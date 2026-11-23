"""bin/session-digest, given small transcripts in Claude Code's format.

    python3 -I -m unittest discover -s tests/session_digest -t tests/session_digest
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "session-digest")
SESSION = "1b2c3d4e-0000-4000-8000-000000000001"
PROJECT = "/work/shop"


def stamp(second: int) -> str:
    return f"2026-11-23T10:{second // 60:02d}:{second % 60:02d}.000Z"


def human(text: str, second: int, **extra: Any) -> Dict[str, Any]:
    return {"type": "user", "timestamp": stamp(second),
            "message": {"role": "user", "content": text},
            "origin": {"kind": "human"}, **extra}


def call(message: str, use: str, name: str, tool_input: Dict[str, Any],
         second: int) -> Dict[str, Any]:
    return {"type": "assistant", "timestamp": stamp(second),
            "message": {"id": message, "role": "assistant", "content": [
                {"type": "tool_use", "id": use, "name": name,
                 "input": tool_input}]}}


def result(use: str, text: str, second: int,
           error: bool = False) -> Dict[str, Any]:
    return {"type": "user", "timestamp": stamp(second),
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": use, "content": text,
                 "is_error": error}]}}


GATE = ("PreToolUse:Bash hook error: [\"/p/hooks/claude_commit_gate\"]: "
        "vibes commit gate: scripts/check failed, so the commit is blocked."
        "\nvibes commit gate: Fix the problems below.")
DENIED = ("Permission for this action was denied by the Claude Code auto "
          "mode classifier.")

MAIN: List[Any] = [
    {"type": "mode", "mode": "normal"},
    human("Add a CSV export.", 0),
    call("msg_1", "t1", "Read", {"file_path": "/work/shop/app.py"}, 1),
    result("t1", "x" * 1500, 2),
    # A second entry of the same reply: one reply, two calls.
    call("msg_1", "t2", "Agent", {"subagent_type": "vibes:builder",
                                  "description": "Build the export"}, 3),
    result("t2", "Built it.", 90),
    call("msg_2", "t3", "Read", {"file_path": "/work/shop/app.py"}, 91),
    result("t3", "x" * 1500, 92),
    call("msg_3", "t4", "Bash", {"command": "git commit -m 'Add export'"}, 93),
    result("t4", GATE, 94, error=True),
    call("msg_4", "t5", "Bash", {"command": "git commit -m 'Add export'"}, 95),
    result("t5", GATE, 96, error=True),
    call("msg_5", "t6", "Bash", {"command": "rm -rf build"}, 97),
    result("t6", DENIED, 98, error=True),
    call("msg_6", "t7", "Bash", {"command": "false"}, 99),
    result("t7", "Exit code 1", 100, error=True),
    call("msg_7", "t8", "Bash", {"command": "sleep 1000"}, 101),
    human("<task-notification>done</task-notification>", 102,
          origin={"kind": "task-notification"}),
    human("A note Claude Code added.", 103, isMeta=True),
    human("The summary of an earlier conversation.", 104,
          isCompactSummary=True),
    {"type": "system", "subtype": "compact_boundary",
     "timestamp": stamp(105)},
    human("No, use semicolons.", 106),
    "not an entry",
]
BUILDER: List[Any] = [
    {"type": "user", "timestamp": stamp(4),
     "message": {"role": "user", "content": "Build the export."}},
    call("msg_b1", "b1", "Write", {"file_path": "/work/shop/export.py",
                                   "content": "..."}, 5),
    result("b1", "File created.", 6),
]
EARLIER: List[Any] = [
    call("msg_e1", "e1", "Grep", {"pattern": "csv", "path": "src"}, 0),
    result("e1", "No matches", 1),
]


def write_lines(path: str, entries: List[Any]) -> None:
    with open(path, "w", encoding="utf-8") as stream:
        for entry in entries:
            if isinstance(entry, str):
                stream.write(entry + "\n")
            else:
                stream.write(json.dumps(entry) + "\n")


class SessionDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = tempfile.mkdtemp()
        self.directory = os.path.join(self.config, "projects", "-work-shop")
        os.makedirs(os.path.join(self.directory, SESSION, "subagents"))
        self.path = os.path.join(self.directory, f"{SESSION}.jsonl")
        write_lines(self.path, MAIN)
        agents = os.path.join(self.directory, SESSION, "subagents")
        write_lines(os.path.join(agents, "agent-b.jsonl"), BUILDER)
        with open(os.path.join(agents, "agent-b.meta.json"), "w",
                  encoding="utf-8") as stream:
            json.dump({"agentType": "vibes:builder", "toolUseId": "t2",
                       "description": "Build the export"}, stream)
        # Started first, so it's a1, though its file sorts second.
        write_lines(os.path.join(agents, "agent-z.jsonl"), EARLIER)

    def tearDown(self) -> None:
        shutil.rmtree(self.config)

    def run_digest(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "CLAUDE_CONFIG_DIR": self.config}
        return subprocess.run([SCRIPT, *args], capture_output=True,
                              text=True, env=env, check=False)

    def digest(self) -> str:
        found = self.run_digest(self.path)
        self.assertEqual(found.returncode, 0, found.stderr)
        return found.stdout

    def test_counts_replies_by_message_id_and_calls(self) -> None:
        text = self.digest()
        self.assertIn("2 user messages, 9 replies, 10 tool calls, "
                      "2 subagents, 1 compactions.", text)
        self.assertIn("| main | main | 7 | 8 | 4 |", text)
        self.assertIn("Skipped 1 lines it couldn't read.", text)

    def test_numbers_subagents_in_the_order_they_started(self) -> None:
        text = self.digest()
        self.assertIn("| a1 | unknown | 1 | 1 | 0 |", text)
        self.assertIn("| a2 | vibes:builder | 1 | 1 | 0 | 2s "
                      "| Build the export |", text)
        self.assertIn("a2.1 11-23 10:00:05 Write ok 13 "
                      "/work/shop/export.py", text)

    def test_links_a_spawn_to_its_subagent(self) -> None:
        self.assertIn("Agent ok 9 vibes:builder: Build the export → a2",
                      self.digest())

    def test_tells_hook_blocks_denials_and_errors_apart(self) -> None:
        text = self.digest()
        self.assertIn("## Hook blocks\n\n- 2× vibes commit gate: "
                      "scripts/check failed, so the commit is blocked. "
                      "— m4, m5", text)
        self.assertIn("## Denied\n\n- 1× Permission for this action was "
                      "denied", text)
        self.assertIn("m6 11-23 10:01:37 Bash denied", text)
        self.assertIn("m7 11-23 10:01:39 Bash error 11 false", text)
        self.assertIn("m8 11-23 10:01:41 Bash no result - sleep 1000", text)

    def test_finds_retries_and_repeated_reads(self) -> None:
        text = self.digest()
        self.assertIn("- Bash git commit -m 'Add export' — m4 blocked, "
                      "retried unchanged as m5: blocked", text)
        self.assertIn("- 2× Read /work/shop/app.py (no Write or Edit in "
                      "between) — m1, m3", text)

    def test_lists_only_what_the_user_typed(self) -> None:
        text = self.digest()
        self.assertIn("- u1 11-23 10:00:00 Add a CSV export.\n"
                      "- u2 11-23 10:01:46 No, use semicolons.", text)
        for added in ("task-notification", "Claude Code added",
                      "earlier conversation", "Build the export."):
            self.assertNotIn(added, text.split("## User messages")[1]
                             .split("## Calls")[0])

    def test_ranks_the_largest_results(self) -> None:
        self.assertIn("## Largest results\n\n- 1.5k m1 Read", self.digest())

    def test_shows_one_call_in_full(self) -> None:
        found = self.run_digest("--show", "m4", self.path)
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertIn("m4 Bash by main at 11-23 10:01:33: blocked",
                      found.stdout)
        self.assertIn('"command": "git commit -m \'Add export\'"',
                      found.stdout)
        self.assertIn("Fix the problems below.", found.stdout)

    def test_refuses_an_unknown_reference(self) -> None:
        found = self.run_digest("--show", "m99", self.path)
        self.assertEqual(found.returncode, 2)
        self.assertIn("no call m99", found.stderr)

    def test_finds_a_session_by_id_in_the_project(self) -> None:
        found = self.run_digest("--project", PROJECT, SESSION)
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertIn(f"Transcript: {self.path}", found.stdout)

    def test_finds_a_session_by_id_in_any_project(self) -> None:
        found = self.run_digest("--project", "/somewhere/else", SESSION)
        self.assertEqual(found.returncode, 0, found.stderr)

    def test_says_when_there_is_no_transcript(self) -> None:
        found = self.run_digest("--project", PROJECT,
                                "00000000-0000-0000-0000-000000000000")
        self.assertEqual(found.returncode, 2)
        self.assertIn("no transcript for session", found.stderr)


if __name__ == "__main__":
    unittest.main()
