"""The tracker guard, and the commit gate on a change to .vibes-tracker.

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
HOOK = os.path.join(ROOT, "hooks", "claude_tracker_guard")
TRACKER = '"/plugins/vibes/bin/tracker"'


def guard(event: dict, env: dict | None = None
          ) -> subprocess.CompletedProcess:
    return subprocess.run([HOOK], input=json.dumps(event), text=True,
                          capture_output=True, check=False,
                          env={**os.environ, **(env or {})})


def bash(command: str, agent: str = "", cwd: str = "/p", **extra: str
         ) -> dict:
    event = {"tool_name": "Bash", "cwd": cwd,
             "tool_input": {"command": command}, **extra}
    if agent:
        event["agent_type"] = agent
    return event


class ApproveTest(unittest.TestCase):
    def test_no_agent_approves(self) -> None:
        for command in (f"{TRACKER} approve", "bin/tracker approve",
                        f"{TRACKER} approve --allow-program x",
                        "cd /p && tracker approve"):
            for agent in ("", "vibes:builder"):
                with self.subTest(command=command, agent=agent):
                    result = guard(bash(command, agent))
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("own terminal", result.stderr)

    def test_no_agent_touches_the_approval(self) -> None:
        for path in ("/home/u/.config/vibes/tracker-approvals/p-1.json",
                     "/p/.git/vibes-tracker-approved.json"):
            with self.subTest(path=path):
                self.assertEqual(
                    guard(bash(f"echo '{{}}' > {path}")).returncode, 2)
                self.assertEqual(guard({"tool_name": "Write", "tool_input": {
                    "file_path": path, "content": "{}"}}).returncode, 2)

    def test_reading_leaves_it_alone(self) -> None:
        for command in (f"{TRACKER} check", f"{TRACKER} list",
                        f"{TRACKER} read 12 --out .vibes/issues/12/i.json",
                        "grep -rn approve docs", "git log"):
            with self.subTest(command=command):
                result = guard(bash(command))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")


class PostTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, ".vibes", "issues"))
        with open(os.path.join(self.dir, ".vibes", "issues", "batch.tsv"),
                  "w", encoding="utf-8") as stream:
            stream.write("label\tid=12\tlabel=ready-for-agent\n"
                         "comment\tid=12\tbody-file=.vibes/issues/12/r.md\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir)

    def command(self) -> str:
        return f"{TRACKER} post .vibes/issues/batch.tsv"

    def test_the_user_confirms_the_batch(self) -> None:
        result = guard(bash(self.command(), cwd=self.dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "ask")
        reason = output["permissionDecisionReason"]
        self.assertIn("- label id=12 label=ready-for-agent", reason)
        self.assertIn("- comment id=12", reason)

    def test_no_subagent_posts(self) -> None:
        result = guard(bash(self.command(), "vibes:issue-reader",
                            cwd=self.dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn("may not post", result.stderr)

    def test_refused_where_the_host_cant_ask(self) -> None:
        result = guard(bash(self.command(), cwd=self.dir, turn_id="t"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("can't ask", result.stderr)


class FileTest(unittest.TestCase):
    def test_no_subagent_writes_the_tracker_file(self) -> None:
        for tool in ("Write", "Edit"):
            with self.subTest(tool=tool):
                result = guard({"tool_name": tool,
                                "agent_type": "vibes:builder",
                                "tool_input": {
                                    "file_path": "/p/.vibes-tracker"}})
                self.assertEqual(result.returncode, 2)

    def test_the_main_agent_drafts_it(self) -> None:
        self.assertEqual(guard({"tool_name": "Write", "tool_input": {
            "file_path": "/p/.vibes-tracker"}}).returncode, 0)


class GateTest(unittest.TestCase):
    """The commit gate has the user confirm a change to .vibes-tracker."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        check = os.path.join(self.repo, "scripts", "check")
        os.makedirs(os.path.dirname(check))
        with open(check, "w", encoding="utf-8") as stream:
            stream.write("#!/bin/sh\n# Guides: languages/BASH\n")
        os.chmod(check, 0o755)
        self.write(".vibes-tracker", "issue-id\t[0-9]+\n")
        self.git("add", ".")
        self.git("commit", "-q", "--no-verify", "-m", "Add the checks")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t",
                        "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)

    def write(self, path: str, text: str) -> None:
        with open(os.path.join(self.repo, path), "w",
                  encoding="utf-8") as stream:
            stream.write(text)

    def gate(self) -> subprocess.CompletedProcess:
        event = {"tool_name": "Bash", "cwd": self.repo,
                 "tool_input": {"command": "git commit -m x"}}
        return subprocess.run(
            [os.path.join(ROOT, "hooks", "claude_commit_gate")],
            input=json.dumps(event), text=True, capture_output=True,
            check=False)

    def test_a_change_asks(self) -> None:
        self.write(".vibes-tracker", "issue-id\t.*\n")
        self.git("add", ".vibes-tracker")
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        reason = json.loads(result.stdout)["hookSpecificOutput"][
            "permissionDecisionReason"]
        self.assertIn(".vibes-tracker: changes the commands", reason)

    def test_other_changes_dont(self) -> None:
        self.write("notes.txt", "x\n")
        self.git("add", "notes.txt")
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
