"""pr-prepare --branch and pr-scan report --branch: reviewing the checked-out
branch, with its uncommitted changes, without changing anything."""

from __future__ import annotations

import os
import subprocess
import unittest

from support import ENV, ROOT, Repo

PREPARE = os.path.join(ROOT, "bin", "pr-prepare")
SCAN = os.path.join(ROOT, "bin", "pr-scan")


def state(repo: Repo) -> tuple:
    """Everything a review must leave as it was."""
    return (repo.git("status", "--porcelain", "--untracked-files=all"),
            repo.git("rev-parse", "HEAD"), repo.git("stash", "list"),
            repo.git("diff", "--cached"), repo.git("diff"),
            repo.git("for-each-ref"))


class BranchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo({"src/a.py": "A = 1\n", "src/b.py": "B = 1\n"})
        self.repo.write({"src/a.py": "A = 2\n"})
        self.repo.commit("Change a")
        with open(os.path.join(self.repo.path, "src", "b.py"), "w") as stream:
            stream.write("B = 2\n")
        with open(os.path.join(self.repo.path, "src", "new.py"), "w") as stream:
            stream.write("NEW = 1\n")
        self.out = os.path.join(self.repo.path, ".vibes", "review-pr")

    def tearDown(self) -> None:
        self.repo.cleanup()

    def prepare(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([PREPARE, "--branch", *args], cwd=self.repo.path,
                              env=ENV, capture_output=True, text=True)

    def read(self, name: str) -> str:
        with open(os.path.join(self.out, name), encoding="utf-8") as stream:
            return stream.read()

    def test_reviews_commits_and_uncommitted_changes(self) -> None:
        before = state(self.repo)
        result = self.prepare()
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(state(self.repo), before)
        self.assertEqual(self.read("files.txt").split(),
                         ["src/a.py", "src/b.py"])
        self.assertIn("+B = 2", self.read("diff.patch"))
        self.assertEqual(self.read("untracked.txt"), "src/new.py\n")
        self.assertIn("not reviewed 1", result.stdout)

    def test_takes_the_base_branch_by_name(self) -> None:
        self.repo.git("switch", "-q", "-c", "next", "main")
        self.repo.write({"src/c.py": "C = 1\n"})
        self.repo.commit("Add c")
        self.repo.git("switch", "-q", "pr")
        self.repo.git("stash", "-q")
        result = self.prepare("next")
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(self.read("files.txt").split(), ["src/a.py"])

    def test_refuses_when_there_is_nothing_to_review(self) -> None:
        self.repo.git("stash", "-q")
        self.repo.git("switch", "-q", "main")
        result = self.prepare()
        self.assertEqual(result.returncode, 2)
        self.assertIn("nothing to review", result.stderr)

    def test_report_for_a_branch(self) -> None:
        self.assertIn(self.prepare().returncode, (0, 1))
        with open(os.path.join(self.out, "review", "round-1",
                               "project-docs-reviewer.md"), "w") as stream:
            stream.write("VERDICT: NOT APPLICABLE\n\nDOCS\n"
                         "- README.md: about installing.\n")
        result = subprocess.run([SCAN, "report", "--out", self.out,
                                 "--branch"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("project-docs-reviewer NOT APPLICABLE", result.stdout)
        self.assertNotIn("malformed", result.stdout)
        report = self.read("review.md")
        self.assertTrue(report.startswith("# Branch review"))
        self.assertIn("`src/new.py`", report)
        self.assertNotIn("gh pr merge", report)
        self.assertFalse(os.path.exists(
            os.path.join(self.out, "comment-draft.md")))


if __name__ == "__main__":
    unittest.main()
