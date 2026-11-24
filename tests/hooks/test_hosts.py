"""The hooks driven with the JSON Codex, Gemini CLI and Copilot CLI send.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest

from test_check_file import CHECK_FILE
from test_commit_gate import LOOSENING_CHECK, LOOSENING_CHECK_FILE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HOOKS = os.path.join(ROOT, "hooks")
FINDINGS = "/p/.vibes/x/review/spike-1/bug-reviewer.md"


def run(hook: str, event: dict, env: dict | None = None
        ) -> subprocess.CompletedProcess:
    return subprocess.run([os.path.join(HOOKS, hook)],
                          input=json.dumps(event), text=True,
                          capture_output=True, check=False,
                          env={**os.environ, **(env or {})})


def normalise(event: dict, env: dict | None = None) -> list[dict]:
    result = subprocess.run(
        ["python3", "-I", "-S", os.path.join(HOOKS, "lib", "host_input.py")],
        input=json.dumps(event), text=True, capture_output=True, check=True,
        env={**os.environ, **(env or {})})
    return [json.loads(line) for line in result.stdout.splitlines()]


def codex(tool: str, agent: str = "", cwd: str = "/p", **tool_input: str
          ) -> dict:
    event = {"hook_event_name": "PreToolUse", "session_id": "s",
             "turn_id": "t", "cwd": cwd, "tool_name": tool,
             "tool_input": tool_input}
    if agent:
        event["agent_type"] = agent
    return event


def patch(*hunks: str) -> str:
    return "\n".join(("*** Begin Patch", *hunks, "*** End Patch")) + "\n"


class NormaliseTest(unittest.TestCase):
    def test_gemini_becomes_claude_codes_shape(self) -> None:
        for event, tool, name in (("BeforeTool", "run_shell_command", "Bash"),
                                  ("AfterTool", "write_file", "Write"),
                                  ("BeforeTool", "replace", "Edit")):
            with self.subTest(tool=tool):
                [one] = normalise({"hook_event_name": event,
                                   "tool_name": tool, "tool_input": {}})
                self.assertEqual(one["tool_name"], name)
                self.assertEqual(one["vibes_host"], "gemini")
                self.assertIn(one["hook_event_name"],
                              ("PreToolUse", "PostToolUse"))

    def test_before_and_after_share_an_id(self) -> None:
        event = {"session_id": "s", "cwd": "/p",
                 "tool_name": "run_shell_command",
                 "tool_input": {"command": "make"}}
        [before] = normalise(dict(event, hook_event_name="BeforeTool"))
        [after] = normalise(dict(event, hook_event_name="AfterTool"))
        self.assertEqual(before["tool_use_id"], after["tool_use_id"])
        [other] = normalise(dict(event, hook_event_name="BeforeTool",
                                 tool_input={"command": "make test"}))
        self.assertNotEqual(before["tool_use_id"], other["tool_use_id"])

    def test_a_patch_becomes_one_input_per_file(self) -> None:
        events = normalise(codex("apply_patch", command=patch(
            "*** Add File: src/new.py", "+print('hi')", "+x = 1",
            "*** Update File: /abs/old.py", "@@", "-a", "+b",
            "*** Update File: src/from.py", "*** Move to: src/to.py", "@@",
            "-c", "+d",
            "*** Delete File: gone.txt")))
        self.assertEqual(
            [(e["tool_name"], e["tool_input"]["file_path"]) for e in events],
            [("Write", "/p/src/new.py"), ("Edit", "/abs/old.py"),
             ("Delete", "/p/src/from.py"), ("Edit", "/p/src/to.py"),
             ("Delete", "/p/gone.txt")])
        self.assertEqual(events[0]["tool_input"]["content"],
                         "print('hi')\nx = 1\n")
        self.assertEqual({e["vibes_host"] for e in events}, {"codex"})

    def test_copilot_is_told_apart_by_its_environment(self) -> None:
        [one] = normalise({"tool_name": "Bash"},
                          env={"COPILOT_PLUGIN_ROOT": "/plugin"})
        self.assertEqual(one["vibes_host"], "copilot")


class ReadOnlyTest(unittest.TestCase):
    def test_a_patch_is_checked_file_by_file(self) -> None:
        own = patch(f"*** Add File: {FINDINGS}", "+1. MINOR: a")
        self.assertEqual(run("claude_read_only_agents", codex(
            "apply_patch", "vibes:bug-reviewer", command=own)).returncode, 0)
        both = patch(f"*** Add File: {FINDINGS}", "+1. MINOR: a",
                     "*** Update File: src/a.py", "@@", "-a", "+b")
        result = run("claude_read_only_agents", codex(
            "apply_patch", "vibes:bug-reviewer", command=both))
        self.assertEqual(result.returncode, 2)
        self.assertIn("bug-reviewer is read-only", result.stderr)

    def test_deleting_a_file_is_a_write(self) -> None:
        result = run("claude_read_only_agents", codex(
            "apply_patch", "vibes:style-reviewer",
            command=patch("*** Delete File: src/a.py")))
        self.assertEqual(result.returncode, 2)

    def test_an_agent_given_no_shell_may_only_read_with_one(self) -> None:
        for command in ("echo x > src/a.py", "rm src/a.py", "git commit -m x"):
            with self.subTest(command=command):
                self.assertEqual(run("claude_read_only_agents", codex(
                    "Bash", "vibes:bug-reviewer", command=command)
                ).returncode, 2)
        self.assertEqual(run("claude_read_only_agents", codex(
            "Bash", "vibes:bug-reviewer", command="grep -rn x src")
        ).returncode, 0)

    def test_an_agent_given_a_shell_keeps_it(self) -> None:
        for agent in ("vibes:builder", "vibes:spiker", "explorer"):
            with self.subTest(agent=agent):
                self.assertEqual(run("claude_read_only_agents", codex(
                    "Bash", agent, command="echo x > src/a.py")
                ).returncode, 0)

    def test_knows_agents_by_any_hosts_name(self) -> None:
        for agent in ("bug-reviewer", "vibes:bug-reviewer",
                      "vibes-bug-reviewer"):
            with self.subTest(agent=agent):
                event = {"agent_type": agent, "tool_name": "Write",
                         "tool_input": {"file_path": "/p/src/a.py"}}
                self.assertEqual(
                    run("claude_read_only_agents", event).returncode, 2)


class CheckFileTest(unittest.TestCase):
    """A Codex patch, and Gemini CLI's write_file, run scripts/check-file."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        self.write(".gitignore", ".checked\n")
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

    def write(self, path: str, text: str) -> None:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)

    def checked(self) -> list[str]:
        path = os.path.join(self.repo, ".checked")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as stream:
            return stream.read().split()

    def test_checks_each_file_a_patch_wrote(self) -> None:
        self.write("a.txt", "A\n")
        self.write("b.txt", "B\n")
        event = codex("apply_patch", cwd=self.repo, command=patch(
            "*** Add File: a.txt", "+A", "*** Update File: b.txt", "@@",
            "-x", "+B", "*** Delete File: gone.txt"))
        event["hook_event_name"] = "PostToolUse"
        result = run("claude_check_file", event)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(self.checked()), ["a.txt", "b.txt"])

    def test_shows_a_lint_problem_in_a_patch(self) -> None:
        self.write("a.txt", "bad\n")
        event = codex("apply_patch", cwd=self.repo,
                      command=patch("*** Add File: a.txt", "+bad"))
        event["hook_event_name"] = "PostToolUse"
        result = run("claude_check_file", event)
        self.assertEqual(result.returncode, 2)
        self.assertIn("bad word", result.stderr)

    def test_gemini_write_file(self) -> None:
        self.write("a.txt", "A\n")
        result = run("claude_check_file", {
            "hook_event_name": "AfterTool", "session_id": "s",
            "cwd": self.repo, "tool_name": "write_file",
            "tool_input": {"file_path": os.path.join(self.repo, "a.txt"),
                           "content": "A\n"}})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.checked(), ["a.txt"])

    def test_gemini_shell_command(self) -> None:
        event = {"session_id": "s", "cwd": self.repo,
                 "tool_name": "run_shell_command",
                 "tool_input": {"command": "printf A > a.txt"}}
        before = run("claude_check_file",
                     dict(event, hook_event_name="BeforeTool"))
        self.assertEqual(before.returncode, 0, before.stderr)
        self.write("a.txt", "A\n")
        after = run("claude_check_file",
                    dict(event, hook_event_name="AfterTool"))
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(self.checked(), ["a.txt"])


class GuideCheckTest(unittest.TestCase):
    """A Codex patch's files each need their guide read first."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        os.makedirs(os.path.join(self.repo, "scripts"))
        check = os.path.join(self.repo, "scripts", "check")
        with open(check, "w", encoding="utf-8") as stream:
            stream.write("#!/bin/sh\n# Guides: languages/Python\n")
        os.chmod(check, 0o755)
        self.tmp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)
        shutil.rmtree(self.tmp)

    def hook(self, command: str, session: str) -> subprocess.CompletedProcess:
        event = codex("apply_patch", cwd=self.repo, command=command)
        event["session_id"] = session
        return run("claude_guide_check", event, env={"TMPDIR": self.tmp})

    def test_a_new_file_waits_for_its_guide(self) -> None:
        added = patch("*** Add File: src/a.py", "+x = 1")
        result = self.hook(added, "s1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("languages/Python", result.stderr)
        self.assertEqual(self.hook(added, "s1").returncode, 0)

    def test_a_deleted_file_needs_no_guide(self) -> None:
        self.assertEqual(
            self.hook(patch("*** Delete File: src/a.py"), "s2").returncode, 0)


class LooseningTest(unittest.TestCase):
    """Where a hook can't ask the user, a commit loosening the gate is
    refused rather than let through."""

    def setUp(self) -> None:
        self.repo = os.path.realpath(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        for path, text in (("scripts/check", LOOSENING_CHECK),
                           ("scripts/check-file", LOOSENING_CHECK_FILE)):
            full = os.path.join(self.repo, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as stream:
                stream.write(text)
            os.chmod(full, 0o755)
        self.git("add", ".")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "--no-verify", "-m", "Add the checks")
        os.remove(os.path.join(self.repo, "scripts", "check-file"))
        self.git("add", "-A")

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       capture_output=True)

    def test_codex_and_gemini_refuse_it(self) -> None:
        for event in (codex("Bash", cwd=self.repo, command="git commit -m x"),
                      {"hook_event_name": "BeforeTool", "cwd": self.repo,
                       "tool_name": "run_shell_command",
                       "tool_input": {"command": "git commit -m x"}}):
            with self.subTest(host=event.get("turn_id", "gemini")):
                result = run("claude_commit_gate", event)
                self.assertEqual(result.returncode, 2)
                self.assertIn("can't ask for it", result.stderr)
                self.assertIn("scripts/check-file", result.stderr)

    def test_copilot_asks(self) -> None:
        result = run("claude_commit_gate",
                     {"tool_name": "Bash", "cwd": self.repo,
                      "tool_input": {"command": "git commit -m x"}},
                     env={"COPILOT_PLUGIN_ROOT": "/plugin"})
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "ask")


if __name__ == "__main__":
    unittest.main()
