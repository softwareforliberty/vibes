"""The check-file hook, driven with the JSON Claude Code sends it after a
write.

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
HOOK = os.path.join(ROOT, "hooks", "claude_check_file")

# Formats a file by lower-casing it, fails on one containing "bad", and
# records each path it's given.
CHECK_FILE = """#!/usr/bin/env bash
set -euo pipefail
for path in "$@"; do
  printf '%s\\n' "${path}" >>.checked
  tr '[:upper:]' '[:lower:]' <"${path}" >"${path}.tmp"
  mv "${path}.tmp" "${path}"
  if grep -q bad "${path}"; then
    printf '%s:1: bad word\\n' "${path}"
    exit 1
  fi
done
"""


class RepoCase(unittest.TestCase):
    """A repository with a scripts/check-file."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        self.write(".gitignore", ".checked\n.vibes/\n")
        self.write("scripts/check-file", CHECK_FILE)
        os.chmod(os.path.join(self.repo, "scripts", "check-file"), 0o755)
        self.git("add", ".")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "-m", "Add the checks")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       capture_output=True)

    def write(self, path: str, text: str) -> str:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)
        return full

    def read(self, path: str) -> str:
        with open(os.path.join(self.repo, path), encoding="utf-8") as stream:
            return stream.read()

    def checked(self) -> list[str]:
        path = os.path.join(self.repo, ".checked")
        if not os.path.exists(path):
            return []
        return self.read(".checked").split()


class CheckFileTest(RepoCase):
    def hook(self, path: str, agent: str = "", tool: str = "Edit",
             cwd: str | None = None) -> subprocess.CompletedProcess:
        event = {"agent_type": agent, "tool_name": tool,
                 "cwd": cwd or self.repo, "tool_input": {"file_path": path}}
        return subprocess.run([HOOK], input=json.dumps(event), text=True,
                              capture_output=True, check=False)

    def test_formats_a_clean_file(self) -> None:
        path = self.write("src/a.py", "A = 1\n")
        result = self.hook(path, tool="Write")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read("src/a.py"), "a = 1\n")
        self.assertEqual(self.checked(), ["src/a.py"])

    def test_shows_lint_problems_to_the_agent(self) -> None:
        path = self.write("src/a.py", "bad = 1\n")
        result = self.hook(path, agent="vibes:builder")
        self.assertEqual(result.returncode, 2)
        self.assertIn("problems in src/a.py", result.stderr)
        self.assertIn("src/a.py:1: bad word", result.stderr)

    def test_resolves_a_relative_path(self) -> None:
        self.write("src/a.py", "A = 1\n")
        result = self.hook("a.py", cwd=os.path.join(self.repo, "src"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.checked(), ["src/a.py"])

    def test_never_checks_the_spiker(self) -> None:
        path = self.write("src/a.py", "bad = 1\n")
        for agent in ("spiker", "vibes:spiker"):
            with self.subTest(agent=agent):
                self.assertEqual(self.hook(path, agent=agent).returncode, 0)
        self.assertEqual(self.checked(), [])

    def test_never_checks_a_spike_branch(self) -> None:
        self.git("switch", "-q", "-c", "spike/export")
        path = self.write("src/a.py", "bad = 1\n")
        self.assertEqual(self.hook(path, agent="vibes:builder").returncode, 0)
        self.assertEqual(self.checked(), [])

    def test_skips_ignored_files(self) -> None:
        path = self.write(".vibes/x/review/spike-1/bug-reviewer.md", "bad\n")
        self.assertEqual(self.hook(path).returncode, 0)
        self.assertEqual(self.checked(), [])

    def test_does_nothing_without_check_file(self) -> None:
        os.remove(os.path.join(self.repo, "scripts", "check-file"))
        path = self.write("src/a.py", "bad = 1\n")
        self.assertEqual(self.hook(path).returncode, 0)

    def test_does_nothing_outside_a_repository(self) -> None:
        outside = tempfile.mkdtemp()
        try:
            path = os.path.join(outside, "a.py")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("bad = 1\n")
            self.assertEqual(self.hook(path, cwd=outside).returncode, 0)
        finally:
            shutil.rmtree(outside)

    def test_does_nothing_for_a_missing_file(self) -> None:
        missing = os.path.join(self.repo, "src", "gone.py")
        self.assertEqual(self.hook(missing).returncode, 0)


class BashTest(RepoCase):
    """Files a shell command writes, found by comparing what's changed
    before and after it."""

    def setUp(self) -> None:
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.count = 0

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.tmp)

    def event(self, name: str, command: str,
              agent: str = "") -> subprocess.CompletedProcess:
        event = {"hook_event_name": name, "tool_name": "Bash",
                 "agent_type": agent, "session_id": "s1",
                 "tool_use_id": f"t{self.count}", "cwd": self.repo,
                 "tool_input": {"command": command}}
        return subprocess.run([HOOK], input=json.dumps(event), text=True,
                              capture_output=True, check=False,
                              env={**os.environ, "TMPDIR": self.tmp})

    def bash(self, command: str, change, agent: str = ""
             ) -> subprocess.CompletedProcess:
        """Runs the hook around a command whose effect is change()."""
        self.count += 1
        self.assertEqual(self.event("PreToolUse", command, agent).returncode,
                         0)
        change()
        return self.event("PostToolUse", command, agent)

    def test_checks_a_file_the_command_changed(self) -> None:
        self.write("src/a.py", "A = 1\n")
        self.git("add", "src/a.py")
        result = self.bash("sed -i '' s/A/bad/ src/a.py",
                           lambda: self.write("src/a.py", "bad = 1\n"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("src/a.py:1: bad word", result.stderr)
        self.assertEqual(self.checked(), ["src/a.py"])

    def test_checks_a_new_file(self) -> None:
        result = self.bash("cat > src/b.py <<'EOF'\nB = 1\nEOF",
                           lambda: self.write("src/b.py", "B = 1\n"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read("src/b.py"), "b = 1\n")
        self.assertEqual(self.checked(), ["src/b.py"])

    def test_leaves_files_the_command_didnt_change(self) -> None:
        self.write("src/old.py", "bad = 1\n")
        result = self.bash("printf x > src/b.py",
                           lambda: self.write("src/b.py", "B = 1\n"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.checked(), ["src/b.py"])

    def test_leaves_git_commands_alone(self) -> None:
        for command in ("git stash pop", "cd src && git switch main",
                        "/usr/bin/git checkout -- a.py"):
            with self.subTest(command=command):
                result = self.bash(command, lambda: self.write(
                    "src/a.py", "bad = 1\n"))
                self.assertEqual(result.returncode, 0)
        self.assertEqual(self.checked(), [])

    def test_a_word_in_quotes_isnt_git(self) -> None:
        result = self.bash("printf 'use git' > src/a.py",
                           lambda: self.write("src/a.py", "bad\n"))
        self.assertEqual(result.returncode, 2)

    def test_never_checks_the_spiker_or_a_spike_branch(self) -> None:
        result = self.bash("printf x > src/a.py", lambda: self.write(
            "src/a.py", "bad\n"), agent="vibes:spiker")
        self.assertEqual(result.returncode, 0)
        self.git("switch", "-q", "-c", "spike/x")
        result = self.bash("printf y > src/b.py", lambda: self.write(
            "src/b.py", "bad\n"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.checked(), [])

    def test_without_a_snapshot_does_nothing(self) -> None:
        self.write("src/a.py", "bad = 1\n")
        self.count += 1
        self.assertEqual(
            self.event("PostToolUse", "printf x > src/a.py").returncode, 0)


if __name__ == "__main__":
    unittest.main()
