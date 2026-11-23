"""bin/repro's verdicts, on commands with known exit statuses.

    python3 -I -m unittest discover -s tests/repro -t tests/repro
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "repro")
sys.path.insert(0, os.path.join(ROOT, "lib"))

from repro import cli  # noqa: E402

# Fails on the runs whose number is in FAIL_ON, counting in a file.
FLAKY = """count=$(( $(cat count 2>/dev/null || echo 0) + 1 ))
echo "$count" > count
case " $FAIL_ON " in *" $count "*) exit 1 ;; esac
exit 0
"""


class VerdictTest(unittest.TestCase):
    def test_counts_exits_as_git_bisect_run_does(self) -> None:
        for code, expected in ((0, "passed"), (1, "failed"), (2, "failed"),
                               (124, "failed"), (126, "failed"),
                               (127, "failed"), (125, "can't tell"),
                               (128, "can't tell"), (-9, "can't tell"),
                               (None, "can't tell")):
            with self.subTest(code=code):
                self.assertEqual(cli.outcome(code), expected)

    def test_any_run_it_cannot_tell_makes_the_verdict(self) -> None:
        self.assertEqual(cli.verdict(["failed", "can't tell"]), "CAN'T TELL")
        self.assertEqual(cli.verdict(["failed", "failed"]), "RED")
        self.assertEqual(cli.verdict(["passed", "passed"]), "GREEN")
        self.assertEqual(cli.verdict(["failed", "passed"]), "FLAKY")


class RunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.out = os.path.join(self.directory, "out")

    def tearDown(self) -> None:
        shutil.rmtree(self.directory)

    def repro(self, *args: str, env: dict = None
              ) -> subprocess.CompletedProcess:
        return subprocess.run([SCRIPT, "run", "--out", self.out, *args],
                              capture_output=True, text=True, check=False,
                              env={**os.environ, **(env or {})})

    def test_a_command_that_always_fails_is_red(self) -> None:
        found = self.repro("--runs", "3", "--", "sh", "-c",
                           "echo boom; exit 1")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertRegex(found.stdout, r"^RED 3/3 failed, median \d+\.\ds\n$")
        with open(os.path.join(self.out, "run-2.log"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "boom\n")
        with open(os.path.join(self.out, "summary.json"),
                  encoding="utf-8") as stream:
            summary = json.load(stream)
        self.assertEqual(summary["verdict"], "RED")
        self.assertEqual([run["exit"] for run in summary["runs"]], [1, 1, 1])

    def test_a_command_that_fails_sometimes_is_flaky(self) -> None:
        found = self.repro("--tree", self.directory, "--", "sh", "-c", FLAKY,
                           env={"FAIL_ON": "2 4"})
        self.assertTrue(found.stdout.startswith("FLAKY 2/5 failed"),
                        found.stdout)

    def test_a_timeout_cannot_tell(self) -> None:
        found = self.repro("--runs", "1", "--timeout", "0.2", "--",
                           "sleep", "5")
        self.assertTrue(found.stdout.startswith("CAN'T TELL 1/1 couldn't "
                                                "tell"), found.stdout)

    def test_runs_in_the_tree(self) -> None:
        found = self.repro("--runs", "1", "--tree", self.directory, "--",
                           "sh", "-c", "test -d out && exit 1; exit 0")
        self.assertTrue(found.stdout.startswith("RED"), found.stdout)

    def test_says_when_the_loop_is_too_slow(self) -> None:
        cli.SLOW_SECONDS, slow = 0.1, cli.SLOW_SECONDS
        try:
            line = cli._run(self.out, 1, 5, ".", ["sleep", "0.3"])
        finally:
            cli.SLOW_SECONDS = slow
        self.assertTrue(line.endswith(" SLOW"), line)

    def test_errors_exit_2(self) -> None:
        for args in (("--",), ("--runs", "0", "--", "true"),
                     ("--tree", "/no/such", "--", "true"),
                     ("--", "/no/such/command")):
            with self.subTest(args=args):
                self.assertEqual(self.repro(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
