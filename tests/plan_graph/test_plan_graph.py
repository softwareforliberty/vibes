"""bin/plan-graph, on rebuild plans' batch lists.

    python3 -I -m unittest discover -s tests/plan_graph -t tests/plan_graph
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "plan-graph")

DIAMOND = """# Rebuild plan: display

Branches: vibe/display from main.

## Batches

1. [Gate and parser](#batch-1-gate-and-parser) (9 entries)
   After: none
   Touches: scripts/check, src/parser/, docs/specs/display/spec.md
2. [The core](#batch-2-the-core) (8 entries)
   After: 1
   Touches: src/core/
3. [Renderer](#batch-3-renderer) (7 entries)
   After: 2
   Touches: src/render/, tests/render/
4. [Init edges](#batch-4-init-edges) (9 entries)
   After: 2
   Touches: src/init/, tests/init/
5. [Smoke test and documents](#batch-5-smoke-test-and-documents) (6 entries)
   After: 3, 4
   Touches: scripts/smoke.sh, README.md

## Batch 1: Gate and parser

After: 7 should be ignored here, in the batch's own section.
"""


def plan_graph(text: str, *args: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as stream:
        stream.write(text)
    try:
        return subprocess.run([SCRIPT, stream.name, *args], text=True,
                              capture_output=True, check=False)
    finally:
        os.remove(stream.name)


class PlanGraphTest(unittest.TestCase):
    def test_follows_the_graph(self) -> None:
        cases = [((), "READY: 1"), (("--done", "1"), "READY: 2"),
                 (("--done", "1,2"), "READY: 3, 4"),
                 (("--done", "1,2", "--running", "3"), "READY: 4"),
                 (("--done", "1,2,3"), "READY: 4"),
                 (("--done", "1,2,3,4"), "READY: 5"),
                 (("--done", "1,2,3,4,5"), "READY: none")]
        for args, ready in cases:
            with self.subTest(args=args):
                result = plan_graph(DIAMOND, *args)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual(result.stdout, f"{ready}\nWIDTH: 2\n")

    def test_finds_two_batches_that_touch_the_same_path(self) -> None:
        text = DIAMOND.replace("Touches: src/init/, tests/init/",
                               "Touches: src/init/, src/render/fonts.cc")
        result = plan_graph(text, "--done", "1,2")
        self.assertEqual(result.returncode, 1)
        self.assertIn("batches 3 and 4 both touch src/render/fonts.cc, and "
                      "neither waits for the other", result.stdout)

    def test_batches_in_order_may_share(self) -> None:
        text = DIAMOND.replace("Touches: src/core/",
                               "Touches: src/core/, scripts/check")
        self.assertEqual(plan_graph(text).returncode, 0)

    def test_missing_lines_are_safe(self) -> None:
        text = DIAMOND.replace("   After: 2\n   Touches: src/init/, "
                               "tests/init/\n", "")
        result = plan_graph(text, "--done", "1,2")
        self.assertEqual(result.stdout, "READY: 3\nWIDTH: 1\n")
        text = DIAMOND.replace("   Touches: src/init/, tests/init/\n", "")
        result = plan_graph(text, "--done", "1,2")
        self.assertEqual(result.returncode, 1)
        self.assertIn("batches 3 and 4 both touch", result.stdout)

    def test_a_running_batch_holds_back_one_that_shares_a_path(self) -> None:
        text = DIAMOND.replace("Touches: src/init/, tests/init/",
                               "Touches: src/init/, tests/render/x.cc")
        result = plan_graph(text, "--done", "1,2", "--running", "3")
        self.assertIn("READY: none", result.stdout)

    def test_reports_cycles_and_unknown_batches(self) -> None:
        cycle = DIAMOND.replace("   After: 1\n", "   After: 5\n")
        self.assertIn("a cycle", plan_graph(cycle).stdout)
        unknown = DIAMOND.replace("After: 3, 4", "After: 3, 9")
        self.assertIn("batch 9, which isn't listed",
                      plan_graph(unknown).stdout)

    def test_refuses_bad_input(self) -> None:
        self.assertEqual(plan_graph("# No batches\n").returncode, 2)
        self.assertEqual(plan_graph(DIAMOND, "--later", "1").returncode, 2)
        self.assertEqual(subprocess.run([SCRIPT], capture_output=True,
                                        check=False).returncode, 2)


if __name__ == "__main__":
    unittest.main()
