"""bin/capacity: its decisions, its cache, and real measurements of small
commands.

    python3 -I -m unittest discover -s tests/capacity -t tests/capacity
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "capacity")
sys.path.insert(0, os.path.join(ROOT, "lib"))

from capacity import cli  # noqa: E402

GIB = 2 ** 30
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
       "GIT_CONFIG_NOSYSTEM": "1"}


def run(wall: float, cpu: float) -> dict:
    return {"tree": "t", "exit": 0, "wall": wall, "cpu": cpu}


def cache(memory: int = GIB, cpus: int = 10, single_memory: int = GIB // 2,
          wall: float = 60, cpu: float = 60, docker=None,
          docker_memory: int = 0, docker_cpu: float = 0,
          pair_wall=None) -> dict:
    data = {"machine": {"cpus": cpus, "memory": memory, "docker": docker},
            "single": {"runs": [run(wall, cpu)], "memory": single_memory,
                       "docker_memory": docker_memory,
                       "docker_cpu": docker_cpu}}
    if pair_wall is not None:
        data["pair"] = {"runs": [run(pair_wall, cpu), run(pair_wall, cpu)]}
    return data


class DecideTest(unittest.TestCase):
    def test_memory_limits_it(self) -> None:
        builders, reasons = cli.decide(cache(memory=8 * GIB,
                                             single_memory=2 * GIB))
        self.assertEqual(builders, 3)
        self.assertIn("limited by memory", reasons[0])

    def test_cpu_limits_it(self) -> None:
        builders, _ = cli.decide(cache(memory=64 * GIB, cpus=8, cpu=240))
        self.assertEqual(builders, 2)

    def test_never_more_than_the_ceiling_or_less_than_one(self) -> None:
        self.assertEqual(cli.decide(cache(memory=512 * GIB,
                                          single_memory=GIB))[0], 4)
        self.assertEqual(cli.decide(cache(memory=GIB,
                                          single_memory=4 * GIB))[0], 1)

    def test_dockers_own_limits_count(self) -> None:
        builders, reasons = cli.decide(cache(
            memory=64 * GIB, docker={"cpus": 10, "memory": 8 * GIB},
            docker_memory=3 * GIB))
        self.assertEqual(builders, 2)
        self.assertIn("Docker's memory", reasons[0])

    def test_two_at_once_must_be_faster(self) -> None:
        roomy = dict(memory=64 * GIB, single_memory=GIB, cpus=32)
        self.assertEqual(cli.decide(cache(**roomy, pair_wall=110))[0], 1)
        self.assertEqual(cli.decide(cache(**roomy, pair_wall=90))[0], 2)
        self.assertEqual(cli.decide(cache(**roomy, pair_wall=62))[0], 4)

    def test_a_lowered_number_holds(self) -> None:
        data = cache(memory=64 * GIB, single_memory=GIB, cpus=32)
        data["lowered"] = {"to": 2, "reason": "ran out of memory"}
        builders, reasons = cli.decide(data)
        self.assertEqual(builders, 2)
        self.assertIn("ran out of memory", reasons[-1])


class SizeTest(unittest.TestCase):
    def test_reads_dockers_sizes(self) -> None:
        self.assertEqual(cli.size("12MiB"), 12 * 2 ** 20)
        self.assertEqual(cli.size("1.5GiB"), int(1.5 * GIB))
        self.assertEqual(cli.size("300kB"), 300_000)
        self.assertEqual(cli.size("0B"), 0)


class StaleTest(unittest.TestCase):
    INFO = {"os": "Darwin arm64", "cpus": 10, "memory": 16 * GIB,
            "docker": None}
    PROJECT = {"gate": "abc", "files": 100, "bytes": 10_000}

    def fresh(self) -> dict:
        data = cache(pair_wall=40)
        data.update({"builders": 2, "fingerprint": cli.fingerprint(self.INFO),
                     "project": dict(self.PROJECT),
                     "measured_at": datetime.datetime.now(
                         datetime.timezone.utc).isoformat()})
        return data

    def test_fresh_when_nothing_changed(self) -> None:
        self.assertIsNone(cli.stale(self.fresh(), self.INFO, self.PROJECT))

    def test_stale_when_something_changed(self) -> None:
        old = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.timedelta(days=31)).isoformat()
        cases = {
            "machine": (self.fresh(), {**self.INFO, "memory": 32 * GIB},
                        self.PROJECT),
            "scripts/check": (self.fresh(), self.INFO,
                              {**self.PROJECT, "gate": "def"}),
            "grew": (self.fresh(), self.INFO,
                     {**self.PROJECT, "files": 130}),
            "days": ({**self.fresh(), "measured_at": old}, self.INFO,
                     self.PROJECT),
            "not measured": ({**self.fresh(), "pair": None}, self.INFO,
                             self.PROJECT),
        }
        for word, (data, info, now) in cases.items():
            with self.subTest(word=word):
                self.assertIn(word, cli.stale(data, info, now))

    def test_small_growth_is_fine(self) -> None:
        self.assertIsNone(cli.stale(self.fresh(), self.INFO,
                                    {**self.PROJECT, "files": 120}))


class CommandTest(unittest.TestCase):
    """The commands, measuring real commands with Docker hidden."""

    def setUp(self) -> None:
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True,
                       env=ENV)
        os.makedirs(os.path.join(self.repo, "scripts"))
        with open(os.path.join(self.repo, "scripts", "check"), "w",
                  encoding="utf-8") as stream:
            stream.write("#!/bin/sh\n")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True,
                       env=ENV)
        self.trees = [os.path.join(self.repo, name) for name in ("a", "b")]
        for tree in self.trees:
            os.mkdir(tree)
        self.cache = os.path.join(self.repo, ".vibes", "capacity.json")
        bin_dir = os.path.join(self.repo, "bin")
        os.mkdir(bin_dir)
        for tool in ("python3", "git", "ps", "sysctl", "vm_stat"):
            found = shutil.which(tool)
            if found:
                os.symlink(found, os.path.join(bin_dir, tool))
        self.env = {**ENV, "PATH": f"{bin_dir}:/usr/bin:/bin:/usr/sbin"}

    def capacity(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([SCRIPT, *args, *([] if "--" in args else [])],
                              cwd=self.repo, text=True, capture_output=True,
                              check=False, env=self.env)

    def test_measures_decides_and_checks(self) -> None:
        hold = [sys.executable, "-c",
                "import time; b = bytearray(80_000_000); time.sleep(2.5)"]
        single = self.capacity("measure", "--cache", self.cache, "--as",
                               "single", "--tree", self.trees[0], "--",
                               *hold)
        self.assertEqual(single.returncode, 0, single.stderr)
        self.assertIn("MEASURED single", single.stdout)
        with open(self.cache, encoding="utf-8") as stream:
            data = json.load(stream)
        self.assertGreater(data["single"]["memory"], 60_000_000)
        self.assertGreaterEqual(data["single"]["runs"][0]["wall"], 2.4)
        self.assertIsNone(data["machine"]["docker"])
        self.assertEqual(self.capacity("check", "--cache",
                                       self.cache).returncode, 3)
        pair = self.capacity("measure", "--cache", self.cache, "--as",
                             "pair", "--tree", self.trees[0], "--tree",
                             self.trees[1], "--", *hold)
        self.assertEqual(pair.returncode, 0, pair.stderr)
        decided = self.capacity("decide", "--cache", self.cache)
        self.assertEqual(decided.returncode, 0, decided.stderr)
        self.assertRegex(decided.stdout, r"^BUILDERS [1-4]\n")
        self.assertIn("two at once ran", decided.stdout)
        checked = self.capacity("check", "--cache", self.cache)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertTrue(checked.stdout.startswith("BUILDERS "))
        lowered = self.capacity("lower", "--cache", self.cache, "--to", "1",
                                "--reason", "a builder ran out of memory")
        self.assertEqual(lowered.stdout, "BUILDERS 1\n")
        self.assertTrue(self.capacity("check", "--cache", self.cache)
                        .stdout.startswith("BUILDERS 1"))

    def test_records_a_failing_command(self) -> None:
        result = self.capacity("measure", "--cache", self.cache, "--as",
                               "single", "--tree", self.trees[0], "--",
                               "sh", "-c", "exit 4")
        self.assertIn("exit 4", result.stdout)

    def test_a_missing_cache_needs_measuring(self) -> None:
        result = self.capacity("check", "--cache", self.cache)
        self.assertEqual((result.returncode, result.stdout),
                         (3, "MEASURE: not measured yet\n"))

    def test_refuses_bad_arguments(self) -> None:
        for args in (["measure", "--cache", self.cache, "--as", "pair",
                      "--tree", self.trees[0], "--", "true"],
                     ["measure", "--cache", self.cache, "--as", "single",
                      "--tree", self.trees[0]],
                     ["decide", "--cache", self.cache], ["nonsense"]):
            with self.subTest(args=args):
                self.assertEqual(self.capacity(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
