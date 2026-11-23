"""Reads a session's transcript, and its subagents', into calls and messages.

Claude Code writes a session as JSON lines in
<config>/projects/<project>/<session>.jsonl, and each subagent's as
<session>/subagents/agent-<id>.jsonl, beside a .meta.json naming its type.
The format isn't a documented contract, so a line this can't read is
skipped and counted, never guessed at.
"""

from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# How a hook's refusal starts, such as "PreToolUse:Bash hook error: [cmd]: ".
HOOK_ERROR = re.compile(r"\A(?:Pre|Post)ToolUse:\S+ hook error: \[.*?\]: ")
DENIALS = ("Permission for this action was denied",
           "The user doesn't want to proceed")
TASK_NOTIFICATION = "<task-notification>"
SESSION_ID = re.compile(r"\A[A-Za-z0-9-]+\Z")
SUMMARY_WIDTH = 100
# Tools whose input names one file.
FILE_TOOLS = ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit")
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


@dataclass
class Call:
    """One tool call and its result."""

    ref: str
    agent: str
    tool: str
    input: Dict[str, Any]
    timestamp: str
    tool_use_id: str
    result: Optional[str] = None
    is_error: bool = False
    subagent: Optional[str] = None

    @property
    def status(self) -> str:
        """ok, error, blocked (by a hook), denied (by a permission check or
        the user), or no result."""
        if self.result is None:
            return "no result"
        if not self.is_error:
            return "ok"
        if HOOK_ERROR.match(self.result):
            return "blocked"
        if any(denial in self.result for denial in DENIALS):
            return "denied"
        return "error"

    @property
    def failed(self) -> bool:
        return self.status in ("error", "blocked", "denied")

    @property
    def reason(self) -> str:
        """The first line of a hook's refusal or a denial, or nothing."""
        if self.result is None or self.status not in ("blocked", "denied"):
            return ""
        return HOOK_ERROR.sub("", self.result).strip().splitlines()[0]

    @property
    def path(self) -> str:
        """The file a file tool reads or writes, or nothing."""
        if self.tool in FILE_TOOLS:
            return str(self.input.get("file_path")
                       or self.input.get("notebook_path") or "")
        return ""

    @property
    def summary(self) -> str:
        """The input in a few words, on one line."""
        get = self.input.get
        if self.tool == "Bash":
            text = str(get("command", ""))
        elif self.tool == "Read":
            text = self.path
            if get("offset") or get("limit"):
                text += f" from {get('offset', 1)}, {get('limit', '')} lines"
        elif self.tool in FILE_TOOLS:
            text = self.path
        elif self.tool == "Grep":
            text = f"{get('pattern', '')} in {get('path') or get('glob') or '.'}"
        elif self.tool == "Glob":
            text = f"{get('pattern', '')} in {get('path') or '.'}"
        elif self.tool in ("Agent", "Task"):
            text = f"{get('subagent_type', 'general-purpose')}: " \
                   f"{get('description', '')}"
        elif self.tool == "Skill":
            text = f"{get('skill', '')} {get('args', '')}"
        elif self.tool == "WebFetch":
            text = str(get("url", ""))
        elif self.tool == "WebSearch":
            text = str(get("query", ""))
        else:
            text = json.dumps(self.input, sort_keys=True)
        return shorten(text, SUMMARY_WIDTH)

    @property
    def key(self) -> str:
        """What makes two calls identical."""
        return f"{self.agent}\t{self.tool}\t" \
               f"{json.dumps(self.input, sort_keys=True)}"


@dataclass
class UserMessage:
    ref: str
    timestamp: str
    text: str


@dataclass
class Agent:
    """The main agent or one subagent, with everything it did."""

    ref: str
    kind: str
    description: str
    path: str
    tool_use_id: str = ""
    calls: List[Call] = field(default_factory=list)
    replies: Set[str] = field(default_factory=set)
    first: str = ""
    last: str = ""
    user_messages: List[UserMessage] = field(default_factory=list)
    compactions: int = 0
    skipped: int = 0


@dataclass
class Session:
    path: str
    main: Agent
    subagents: List[Agent]

    @property
    def agents(self) -> List[Agent]:
        return [self.main, *self.subagents]

    @property
    def calls(self) -> List[Call]:
        return [call for agent in self.agents for call in agent.calls]

    def call(self, ref: str) -> Optional[Call]:
        return next((call for call in self.calls if call.ref == ref), None)


def shorten(text: str, width: int) -> str:
    """The text on one line, cut to the width."""
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width - 1] + "…"


def project_dir(path: str) -> str:
    """The name Claude Code gives a project's transcript directory: its path
    with every character but a letter or a digit as a hyphen."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def find(session: str, project: str) -> str:
    """The transcript for a path or a session id. Raises ValueError when
    there's none."""
    if os.path.isfile(session):
        return session
    if not SESSION_ID.match(session):
        raise ValueError(f"no transcript at {session}")
    root = os.environ.get("CLAUDE_CONFIG_DIR") \
        or os.path.join(os.path.expanduser("~"), ".claude")
    projects = os.path.join(root, "projects")
    path = os.path.join(projects, project_dir(project), f"{session}.jsonl")
    if os.path.isfile(path):
        return path
    # A long project path is cut short and given a hash, so look for the
    # session id in every project.
    found = glob.glob(os.path.join(glob.escape(projects), "*",
                                   f"{session}.jsonl"))
    if len(found) == 1:
        return found[0]
    raise ValueError(f"no transcript for session {session} in {projects}")


def read(path: str) -> Session:
    """The session in a transcript, with its subagents' transcripts."""
    main = Agent("main", "main", "", path)
    _read_agent(main, "m")
    subagents = []
    directory = os.path.join(os.path.splitext(path)[0], "subagents")
    for file in sorted(glob.glob(os.path.join(glob.escape(directory),
                                              "agent-*.jsonl"))):
        meta = _meta(os.path.splitext(file)[0] + ".meta.json")
        agent = Agent("", str(meta.get("agentType") or "unknown"),
                      str(meta.get("description") or ""), file,
                      str(meta.get("toolUseId") or ""))
        subagents.append(agent)
    for agent in subagents:
        _read_agent(agent, "?")
    subagents.sort(key=lambda agent: (agent.first or "~", agent.path))
    for number, agent in enumerate(subagents, 1):
        agent.ref = f"a{number}"
        for index, call in enumerate(agent.calls, 1):
            call.ref = f"{agent.ref}.{index}"
            call.agent = agent.ref
    spawned = {agent.tool_use_id: agent.ref for agent in subagents
               if agent.tool_use_id}
    for call in main.calls + [c for a in subagents for c in a.calls]:
        call.subagent = spawned.get(call.tool_use_id)
    return Session(path, main, subagents)


def _meta(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as stream:
            meta = json.load(stream)
    except (OSError, ValueError):
        return {}
    return meta if isinstance(meta, dict) else {}


def _read_agent(agent: Agent, prefix: str) -> None:
    pending: Dict[str, Call] = {}
    with open(agent.path, encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                agent.skipped += 1
                continue
            if not isinstance(entry, dict) or "type" not in entry:
                agent.skipped += 1
                continue
            _read_entry(agent, prefix, entry, pending)


def _read_entry(agent: Agent, prefix: str, entry: Dict[str, Any],
                pending: Dict[str, Call]) -> None:
    timestamp = str(entry.get("timestamp") or "")
    if timestamp:
        agent.first = min(agent.first or timestamp, timestamp)
        agent.last = max(agent.last, timestamp)
    kind = entry["type"]
    if kind == "system" and entry.get("subtype") == "compact_boundary":
        agent.compactions += 1
        return
    message = entry.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if kind == "assistant":
        if message.get("id"):
            agent.replies.add(str(message["id"]))
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                call = Call(f"{prefix}{len(agent.calls) + 1}", agent.ref,
                            str(block.get("name", "")),
                            block.get("input") if isinstance(
                                block.get("input"), dict) else {},
                            timestamp, str(block.get("id", "")))
                agent.calls.append(call)
                pending[call.tool_use_id] = call
    elif kind == "user":
        if isinstance(content, str):
            _user_message(agent, entry, content, timestamp)
            return
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                call = pending.pop(str(block.get("tool_use_id", "")), None)
                if call is not None:
                    call.result = _text(block.get("content"))
                    call.is_error = bool(block.get("is_error"))
            elif block.get("type") == "text":
                _user_message(agent, entry, str(block.get("text", "")),
                              timestamp)


def _user_message(agent: Agent, entry: Dict[str, Any], text: str,
                  timestamp: str) -> None:
    """Records a message the user typed, but not a subagent's brief, a
    notification, a summary or anything else Claude Code added."""
    origin = entry.get("origin")
    origin_kind = origin.get("kind") if isinstance(origin, dict) else None
    if agent.ref != "main" or entry.get("isMeta") \
            or entry.get("isCompactSummary") \
            or origin_kind not in (None, "human") \
            or text.lstrip().startswith(TASK_NOTIFICATION):
        return
    ref = f"u{len(agent.user_messages) + 1}"
    agent.user_messages.append(UserMessage(ref, timestamp, text))


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content if isinstance(content, list) else []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif isinstance(block, dict):
            parts.append(f"[{block.get('type', 'block')}]")
    return "\n".join(parts)
