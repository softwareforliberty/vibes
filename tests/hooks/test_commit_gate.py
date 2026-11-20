"""The commit gate's choice of checks: a commit of documents only runs
scripts/check --static, and any other commit runs all of it.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks", "git_pre_commit")

# Records the arguments it's run with.
CHECK = """#!/usr/bin/env bash
#
# Guides: languages/BASH
set -euo pipefail
printf '%s\\n' "${*:-<none>}" >>"${ARGS_LOG}"
"""


class DocsOnlyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.log = os.path.join(self.repo, ".git", "args.log")
        self.git("init", "-q", "-b", "main")
        self.write("scripts/check", CHECK)
        os.chmod(os.path.join(self.repo, "scripts", "check"), 0o755)
        self.git("add", ".")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "-m", "Add the checks")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       capture_output=True)

    def write(self, path: str, text: str) -> None:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)

    def gate(self, *paths: str) -> str:
        """Stages the paths, runs the gate, and returns the arguments
        scripts/check was run with."""
        for path in paths:
            self.write(path, "text\n")
        self.git("add", *paths)
        result = subprocess.run(
            [HOOK], cwd=self.repo, capture_output=True, text=True,
            env={**os.environ, "ARGS_LOG": self.log}, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(self.log, encoding="utf-8") as stream:
            return stream.read().strip()

    def test_documents_only_run_the_static_checks(self) -> None:
        self.assertEqual(
            self.gate("docs/specs/x/spec.md", "README.md", "docs/a.rst"),
            "--static")

    def test_code_runs_everything(self) -> None:
        self.assertEqual(self.gate("scripts/build.sh"), "<none>")

    def test_documents_with_code_run_everything(self) -> None:
        self.assertEqual(self.gate("README.md", "scripts/build.sh"),
                         "<none>")

    def test_test_data_runs_everything(self) -> None:
        for path in ("tests/fixtures/input.md", "fixtures/a.md",
                     "pkg/testdata/case.md"):
            with self.subTest(path=path):
                self.assertEqual(self.gate(path), "<none>")
                os.remove(self.log)


class ClaudeHookTest(unittest.TestCase):
    """The Claude Code hook, with a gate that always fails."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        self.write("scripts/check",
                   "#!/bin/sh\n# Guides: languages/BASH\nexit 1\n")
        os.chmod(os.path.join(self.repo, "scripts", "check"), 0o755)
        self.git("add", ".")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "--no-verify", "-m", "Add the checks")
        self.write("scripts/build.sh", "true\n")
        self.git("add", "scripts/build.sh")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    git = DocsOnlyTest.git
    write = DocsOnlyTest.write

    def hook(self, command: str) -> subprocess.CompletedProcess:
        event = {"tool_name": "Bash", "cwd": self.repo,
                 "tool_input": {"command": command}}
        return subprocess.run(
            [os.path.join(ROOT, "hooks", "claude_commit_gate")],
            input=json.dumps(event), text=True, capture_output=True,
            check=False)

    def test_finds_a_commit_behind_a_wrapper(self) -> None:
        for command in ("git commit -q -m 'Add the build'",
                        "time git commit -q -F - <<'EOF' 2>&1 | tail -60\n"
                        "Add the build\nEOF",
                        "time -p git commit -m x",
                        "(time git commit -q -m x) 2>&1 | tail -15",
                        "env GIT_EDITOR=true git commit",
                        "nice -n 5 git commit -m x",
                        "command git commit -m x",
                        "timeout 900 /usr/bin/git commit -m x",
                        "sudo -u git git commit -m x"):
            with self.subTest(command=command):
                self.assertEqual(self.hook(command).returncode, 2)

    def test_leaves_other_commands_alone(self) -> None:
        for command in ("git log --oneline | head", "time make test",
                        "echo 'git commit' > notes.txt", "git status"):
            with self.subTest(command=command):
                self.assertEqual(self.hook(command).returncode, 0)

    def test_refuses_while_a_vibes_hook_link_is_broken(self) -> None:
        hook = os.path.join(self.repo, ".git", "hooks", "pre-commit")
        os.symlink("/gone/vibes/0.3.0/hooks/git_pre_commit", hook)
        result = self.hook("git commit -m x")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no longer exists", result.stderr)
        self.assertIn("install-git-hooks", result.stderr)


if __name__ == "__main__":
    unittest.main()
