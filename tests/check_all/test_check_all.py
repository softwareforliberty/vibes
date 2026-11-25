"""check-all: scripts/check --all once for each tree.

    python3 -I -m unittest discover -s tests/check_all -t tests/check_all
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "bin", "check-all")


class CheckAllTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.runs = os.path.join(self.repo, ".git", "check-runs")
        self.git("init", "-q", "-b", "main")
        self.check("exit 0")
        self.write("a.txt", "a\n")
        self.commit("Start")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
             *args], cwd=self.repo, check=True, capture_output=True,
            text=True).stdout

    def write(self, path: str, text: str) -> None:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)

    def check(self, then: str) -> None:
        """A scripts/check that counts its runs and their arguments."""
        self.write("scripts/check",
                   f'#!/bin/sh\necho "$*" >> "{self.runs}"\n{then}\n')
        os.chmod(os.path.join(self.repo, "scripts", "check"), 0o755)

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "--no-verify", "-m", message)

    def run_tool(self, cwd: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([TOOL], cwd=cwd or self.repo, check=False,
                              capture_output=True, text=True)

    def runs_of_check(self) -> list[str]:
        if not os.path.exists(self.runs):
            return []
        with open(self.runs, encoding="utf-8") as stream:
            return stream.read().splitlines()

    def test_a_pass_runs_with_all_and_is_remembered(self) -> None:
        first = self.run_tool()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertRegex(first.stdout, r"PASSED [0-9a-f]{40}\n\Z")
        second = self.run_tool()
        self.assertEqual(second.returncode, 0)
        self.assertIn("(already)", second.stdout)
        self.assertEqual(self.runs_of_check(), ["--all"])

    def test_the_same_files_at_another_commit_count_as_passed(self) -> None:
        self.run_tool()
        self.git("commit", "-q", "--no-verify", "--allow-empty", "-m", "Mark")
        self.assertIn("(already)", self.run_tool().stdout)
        self.assertEqual(len(self.runs_of_check()), 1)

    def test_new_files_run_again(self) -> None:
        self.run_tool()
        self.write("a.txt", "b\n")
        self.commit("Change a")
        result = self.run_tool()
        self.assertNotIn("(already)", result.stdout)
        self.assertEqual(len(self.runs_of_check()), 2)

    def test_a_failure_is_run_again_every_time(self) -> None:
        self.check("exit 1")
        self.commit("Break the check")
        for _ in range(2):
            result = self.run_tool()
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAILED", result.stdout)
        self.assertEqual(len(self.runs_of_check()), 2)

    def test_a_tree_with_changes_is_refused(self) -> None:
        for change in ("modified", "untracked"):
            with self.subTest(change=change):
                path = "a.txt" if change == "modified" else "new.txt"
                self.write(path, "changed\n")
                result = self.run_tool()
                self.assertEqual(result.returncode, 2)
                self.assertIn("has changes", result.stderr)
                os.remove(os.path.join(self.repo, path)) \
                    if change == "untracked" else self.git("checkout", "a.txt")
        self.assertEqual(self.runs_of_check(), [])

    def test_a_change_while_it_runs_records_nothing(self) -> None:
        self.check(f'echo x > "{self.repo}/a.txt"')
        self.commit("A check that writes")
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("CHANGED", result.stdout)
        self.git("checkout", "a.txt")
        self.assertNotIn("(already)", self.run_tool().stdout)

    def test_worktrees_share_what_passed(self) -> None:
        self.run_tool()
        worktree = os.path.join(self.repo, ".git", "wt")
        self.git("worktree", "add", "-q", "--detach", worktree)
        self.assertIn("(already)", self.run_tool(worktree).stdout)

    def test_no_scripts_check_is_an_error(self) -> None:
        os.remove(os.path.join(self.repo, "scripts", "check"))
        self.commit("Drop the check")
        self.assertEqual(self.run_tool().returncode, 2)


if __name__ == "__main__":
    unittest.main()
