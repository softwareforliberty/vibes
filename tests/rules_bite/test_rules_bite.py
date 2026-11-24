"""bin/rules-bite, on a project whose check forbids an edge reaching into
the core's internals.

    python3 -I -m unittest discover -s tests/rules_bite -t tests/rules_bite
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "rules-bite")

CHECK = """#!/bin/sh
# Guides: languages/SH
# Edges use only the core's entry points.
if grep -rn 'core/internal' src/edge; then
  echo 'edge reaches into core/internal' >&2
  exit 1
fi
"""

BREACH = """Rule: an edge uses only the core's entry points
Fails with: edge reaches into core/internal

diff --git a/src/edge/breach.sh b/src/edge/breach.sh
new file mode 100644
--- /dev/null
+++ b/src/edge/breach.sh
@@ -0,0 +1 @@
+. ../core/internal/parse.sh
"""


class Project(unittest.TestCase):
    """A project with the rule, and the breach that proved it."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        self.git("init", "-q", "-b", "main")
        self.write("scripts/check", CHECK, executable=True)
        self.write("src/edge/main.sh", ". ../core/entry.sh\n")
        self.write("src/core/entry.sh", "true\n")
        self.write("scripts/breaches/edge-entry-points.patch", BREACH)
        self.git("add", ".")
        self.git("commit", "-q", "-m", "Add the rule and its breach")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c",
                        "user.email=t@example.com", *args], check=True,
                       capture_output=True)

    def write(self, path: str, text: str, executable: bool = False) -> None:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)
        if executable:
            os.chmod(full, 0o755)

    def bite(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([SCRIPT, *args], cwd=self.repo, text=True,
                              capture_output=True, check=False)



class RulesBiteTest(Project):
    def test_a_rule_that_still_bites(self) -> None:
        result = self.bite()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout,
                         "BITES scripts/breaches/edge-entry-points.patch\n")
        with open(os.path.join(self.repo, ".vibes", "rules-bite",
                               "edge-entry-points.log"),
                  encoding="utf-8") as stream:
            self.assertIn("edge reaches into core/internal", stream.read())

    def test_leaves_no_worktree_or_change_behind(self) -> None:
        self.bite()
        worktrees = subprocess.run(
            ["git", "-C", self.repo, "worktree", "list"], text=True,
            capture_output=True, check=True).stdout.splitlines()
        self.assertEqual(len(worktrees), 1)
        self.assertFalse(os.path.exists(
            os.path.join(self.repo, "src", "edge", "breach.sh")))

    def test_a_rule_that_stopped_biting(self) -> None:
        self.write("scripts/check", CHECK.replace("src/edge", "src/edges"),
                   executable=True)
        self.git("commit", "-qam", "Point the check elsewhere")
        result = self.bite()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSED scripts/breaches/edge-entry-points.patch",
                      result.stdout)

    def test_staged_checks_what_is_about_to_be_committed(self) -> None:
        self.write("scripts/check", CHECK.replace("src/edge", "src/edges"),
                   executable=True)
        self.git("add", "scripts/check")
        self.assertEqual(self.bite().returncode, 0)
        result = self.bite("--staged")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSED", result.stdout)

    def test_a_failure_for_another_reason_isnt_proof(self) -> None:
        self.write("scripts/breaches/edge-entry-points.patch",
                   BREACH.replace("Fails with: edge reaches into "
                                  "core/internal",
                                  "Fails with: something else"))
        self.git("commit", "-qam", "Expect another message")
        result = self.bite()
        self.assertEqual(result.returncode, 1)
        self.assertIn("ELSEWHERE", result.stdout)

    def test_quotes_count_as_the_same_in_any_form(self) -> None:
        self.write("scripts/check", CHECK.replace(
            "echo 'edge reaches into core/internal'",
            "echo \"edge reaches into \u2018core/internal\u2019\""),
            executable=True)
        self.write("scripts/breaches/edge-entry-points.patch",
                   BREACH.replace("Fails with: edge reaches into "
                                  "core/internal",
                                  "Fails with: edge reaches into "
                                  "'core/internal'"))
        self.git("commit", "-qam", "Quote the path")
        result = self.bite()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_breach_that_no_longer_applies(self) -> None:
        self.write("src/edge/breach.sh", "already here\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Take the breach's file")
        result = self.bite()
        self.assertEqual(result.returncode, 1)
        self.assertIn("STALE", result.stdout)

    def test_a_breach_needs_its_rule_and_message(self) -> None:
        self.write("scripts/breaches/edge-entry-points.patch",
                   BREACH.split("\n", 2)[2])
        self.git("commit", "-qam", "Drop the header")
        result = self.bite()
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs a Rule: line", result.stderr)

    def test_no_breaches(self) -> None:
        self.git("rm", "-q", "scripts/breaches/edge-entry-points.patch")
        self.git("commit", "-qm", "Drop it")
        self.assertEqual(self.bite().stdout, "NO BREACHES\n")



class GateTest(Project):
    """The commit gate, run by git's own pre-commit hook, which sets
    GIT_INDEX_FILE."""

    def setUp(self) -> None:
        super().setUp()
        hooks = os.path.join(self.repo, ".git", "test-hooks")
        os.makedirs(hooks)
        hook = os.path.join(hooks, "pre-commit")
        with open(hook, "w", encoding="utf-8") as stream:
            stream.write("#!/bin/sh\nexec "
                         f"{os.path.join(ROOT, 'hooks', 'git_pre_commit')}\n")
        os.chmod(hook, 0o755)
        self.git("config", "core.hooksPath", hooks)

    def commit(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", self.repo, "-c", "user.name=t", "-c",
             "user.email=t@example.com", "commit", "-q", *args],
            text=True, capture_output=True, check=False)

    def test_refuses_a_check_that_stops_biting(self) -> None:
        self.write("scripts/check", CHECK.replace("src/edge", "src/edges"),
                   executable=True)
        result = self.commit("-am", "Point the check elsewhere")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no longer fails on the breach", result.stderr)
        self.assertIn("MISSED", result.stderr)
        # The real index still holds only what was committed before.
        staged = subprocess.run(["git", "-C", self.repo, "diff", "--cached",
                                 "--name-only"], text=True,
                                capture_output=True, check=True).stdout
        self.assertEqual(staged, "")

    def test_lets_a_check_that_still_bites_through(self) -> None:
        self.write("scripts/check", CHECK + "# A comment.\n",
                   executable=True)
        result = self.commit("-am", "Comment the check")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_other_commits_dont_run_it(self) -> None:
        self.write("scripts/check", CHECK.replace("src/edge", "src/edges"),
                   executable=True)
        self.git("commit", "-q", "--no-verify", "-am", "Loosen it unchecked")
        self.write("src/core/entry.sh", "true\n# More.\n")
        result = self.commit("-am", "Change the core")
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
