"""Turns a tool hook's JSON input from Codex or Gemini CLI into Claude Code's.

The vibes hooks read Claude Code's input: tool_name Bash, Write or Edit,
tool_input.command or tool_input.file_path, and hook_event_name PreToolUse
or PostToolUse. Copilot CLI sends that shape already. Gemini CLI names its
events BeforeTool and AfterTool, and its tools run_shell_command, write_file
and replace. Codex sends Claude Code's shape, but its file edits are one
apply_patch call whose patch may add, change, move and delete several files.

Reads the input on stdin and prints one JSON object per line: the input in
Claude Code's shape, or for a patch, one object for each file it touches,
as tool Write for a file it adds, Edit for one it changes or moves to, and
Delete for one it deletes or moves away. Each object gets vibes_host, the
host that sent it, and a tool_use_id when the host gave none, the same
before and after the tool runs, so the two can be matched.

    python3 host_input.py < input.json
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

GEMINI_EVENTS = {"BeforeTool": "PreToolUse", "AfterTool": "PostToolUse"}
GEMINI_TOOLS = {
    "run_shell_command": "Bash",
    "write_file": "Write",
    "replace": "Edit",
}
PATCH_HEADERS = {
    "*** Add File: ": "Write",
    "*** Update File: ": "Edit",
    "*** Delete File: ": "Delete",
}
MOVE_HEADER = "*** Move to: "


def host_of(event: dict[str, Any]) -> str:
    """Names the host that sent an input."""
    if event.get("vibes_host"):
        return str(event["vibes_host"])
    if event.get("hook_event_name") in GEMINI_EVENTS:
        return "gemini"
    if "turn_id" in event:
        return "codex"
    if os.environ.get("COPILOT_PLUGIN_ROOT"):
        return "copilot"
    return "claude"


def patch_files(patch: str) -> list[tuple[str, str, str]]:
    """Lists the files a patch touches: (tool, path, content), where content
    is what an added file holds."""
    files: list[tuple[str, str, str]] = []
    added: list[str] | None = None
    for line in patch.splitlines():
        if added is not None:
            if line.startswith("+"):
                added.append(line[1:])
                continue
            tool, path, _ = files[-1]
            files[-1] = (tool, path, "\n".join(added) + "\n")
            added = None
        if line.startswith(MOVE_HEADER) and files:
            tool, path, content = files[-1]
            files[-1] = ("Delete", path, content)
            files.append(("Edit", line[len(MOVE_HEADER):].strip(), ""))
            continue
        for header, tool in PATCH_HEADERS.items():
            if line.startswith(header):
                files.append((tool, line[len(header):].strip(), ""))
                if tool == "Write":
                    added = []
    if added is not None and files:
        tool, path, _ = files[-1]
        files[-1] = (tool, path, "\n".join(added) + "\n")
    return files


def normalise(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Returns the input in Claude Code's shape, one object per file."""
    host = host_of(event)
    event["vibes_host"] = host
    if host == "gemini":
        event["hook_event_name"] = GEMINI_EVENTS[event["hook_event_name"]]
        tool = event.get("tool_name", "")
        event["tool_name"] = GEMINI_TOOLS.get(tool, tool)
    if not event.get("tool_use_id"):
        key = json.dumps([event.get("session_id"), event.get("turn_id"),
                          event.get("cwd"), event.get("tool_name"),
                          event.get("tool_input")], sort_keys=True)
        event["tool_use_id"] = hashlib.sha256(key.encode()).hexdigest()[:16]
    if event.get("tool_name") != "apply_patch":
        return [event]
    tool_input = event.get("tool_input") or {}
    patch = tool_input.get("command") or tool_input.get("input") or ""
    cwd = event.get("cwd") or ""
    events = []
    for tool, path, content in patch_files(patch):
        full = os.path.join(cwd, path) if cwd else path
        one = dict(event, tool_name=tool,
                   tool_input={"file_path": full, "content": content})
        events.append(one)
    return events or [event]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 1
    if not isinstance(event, dict):
        return 1
    for one in normalise(event):
        print(json.dumps(one, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
