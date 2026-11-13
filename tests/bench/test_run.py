"""bench run, tests and import, end to end on tiny harnesses."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

from support import BENCH

from bench import samples, verdict

HARNESS = """import sys
print(open(sys.argv[1] + "/answer.txt").read().strip())
print("metric items 7")
"""


class RunTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        self.harness = os.path.join(self.root, "harness.py")
        with open(self.harness, "w", encoding="utf-8") as stream:
            stream.write(HARNESS)

    def tree(self, name: str, answer: str) -> str:
        path = os.path.join(self.root, name)
        os.makedirs(path)
        with open(os.path.join(path, "answer.txt"), "w",
                  encoding="utf-8") as stream:
            stream.write(answer)
        return path

    def bench(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([BENCH, *args], capture_output=True, text=True,
                              check=False)

    def run_pairs(self, out: str, a: str, b: str, *extra: str):
        return self.bench("run", "--out", out, "--a", a, "--b", b,
                          "--pairs", "3", "--max-pairs", "3", "--min-time",
                          "0", *extra, "--", sys.executable, self.harness,
                          "{tree}")

    def test_measures_each_side_and_its_metrics(self) -> None:
        a, b = self.tree("a", "42"), self.tree("b", "42")
        out = os.path.join(self.root, "m")
        result = self.run_pairs(out, a, b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 pairs", result.stdout)
        table = samples.by_measure(samples.read_samples(out))
        for measure in ("wall", "user", "sys", "cpu", "rss_kib",
                        "metric.items"):
            self.assertEqual(len(table[measure][0]), 3, measure)
        self.assertEqual(table["metric.items"][1], [7.0, 7.0, 7.0])
        self.assertGreater(table["rss_kib"][0][0], 1000)
        self.assertEqual(verdict.broken(out), [])

    def test_different_output_is_broken_and_not_timed(self) -> None:
        a, b = self.tree("a", "42"), self.tree("b", "41")
        out = os.path.join(self.root, "m")
        self.assertEqual(self.run_pairs(out, a, b).returncode, 0)
        self.assertEqual(verdict.decide(out).word, verdict.BROKEN)
        self.assertEqual(samples.read_samples(out), [])

    def test_a_failing_side_b_is_broken(self) -> None:
        a = self.tree("a", "42")
        b = os.path.join(self.root, "b")
        os.makedirs(b)
        out = os.path.join(self.root, "m")
        self.assertEqual(self.run_pairs(out, a, b).returncode, 0)
        self.assertIn("exited", verdict.decide(out).line)

    def test_a_failing_side_a_is_an_error(self) -> None:
        b = self.tree("b", "42")
        a = os.path.join(self.root, "a")
        os.makedirs(a)
        result = self.run_pairs(os.path.join(self.root, "m"), a, b)
        self.assertEqual(result.returncode, 2)

    def test_the_command_must_name_the_tree(self) -> None:
        a, b = self.tree("a", "42"), self.tree("b", "42")
        result = self.bench("run", "--out", os.path.join(self.root, "m"),
                            "--a", a, "--b", b, "--", sys.executable,
                            self.harness)
        self.assertEqual(result.returncode, 2)
        self.assertIn("{tree}", result.stderr)

    def test_never_overwrites_a_measurement(self) -> None:
        a, b = self.tree("a", "42"), self.tree("b", "42")
        out = os.path.join(self.root, "m")
        self.assertEqual(self.run_pairs(out, a, b).returncode, 0)
        self.assertEqual(self.run_pairs(out, a, b).returncode, 2)

    def test_tests_records_the_result(self) -> None:
        tree = self.tree("t", "42")
        out = os.path.join(self.root, "m")
        result = self.bench("tests", "--out", out, "--tree", tree, "--",
                            sys.executable, "-c", "import sys; sys.exit(3)")
        self.assertEqual(result.returncode, 0)
        self.assertIn("FAILED", result.stdout)
        self.assertEqual(samples.read_json(out, samples.TESTS)["status"], 3)

    def test_import_is_unpaired(self) -> None:
        files = []
        for name, values in (("a.txt", "2\n2\n2\n"), ("b.txt", "1\n1\n")):
            files.append(os.path.join(self.root, name))
            with open(files[-1], "w", encoding="utf-8") as stream:
                stream.write(values)
        out = os.path.join(self.root, "m")
        result = self.bench("import", "--out", out, "--a", files[0],
                            "--b", files[1])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(verdict.interval(out, "wall").ratio, 0.5)


if __name__ == "__main__":
    unittest.main()
