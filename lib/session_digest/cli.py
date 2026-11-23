"""session-digest's commands.

    session-digest [--project <dir>] <transcript or session id>
    session-digest --show <ref> [--project <dir>] <transcript or session id>

The first prints the digest; the second prints one call's full input and
result, by the reference the digest gave it. A session id is looked up in
the project's transcript directory, the current directory's by default.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from . import transcript
from .transcript import Call, Session

LARGEST = 10
REFS_SHOWN = 12
USER_WIDTH = 200
SHOW_LIMIT = 50_000


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="session-digest")
    parser.add_argument("--show", metavar="REF",
                        help="print one call's full input and result")
    parser.add_argument("--project", default=".",
                        help="the project a session id belongs to")
    parser.add_argument("session", help="a transcript or a session id")
    args = parser.parse_args(argv)
    try:
        path = transcript.find(args.session, os.path.abspath(args.project))
        session = transcript.read(path)
    except (OSError, ValueError) as error:
        print(f"session-digest: {error}", file=sys.stderr)
        return 2
    if args.show:
        call = session.call(args.show)
        if call is None:
            print(f"session-digest: no call {args.show}", file=sys.stderr)
            return 2
        print(show(call))
    else:
        print(digest(session))
    return 0


def digest(session: Session) -> str:
    calls = session.calls
    main = session.main
    first = min((a.first for a in session.agents if a.first), default="")
    last = max((a.last for a in session.agents), default="")
    skipped = sum(agent.skipped for agent in session.agents)
    lines = [
        "# Session digest",
        "",
        f"Transcript: {session.path}",
        f"From {stamp(first)} to {stamp(last)} ({span(first, last)}): "
        f"{len(main.user_messages)} user messages, "
        f"{sum(len(a.replies) for a in session.agents)} replies, "
        f"{len(calls)} tool calls, {len(session.subagents)} subagents, "
        f"{main.compactions} compactions.",
        "References: m<n> is the main agent's nth call, a<k>.<n> the kth "
        "subagent's, u<n> the nth user message. Run session-digest --show "
        "<ref> for a call's full input and result.",
    ]
    if skipped:
        lines.append(f"Skipped {skipped} lines it couldn't read.")
    lines += ["", "## Agents", "",
              "| Ref | Agent | Replies | Calls | Failed | Wall time | Task |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for agent in session.agents:
        failed = sum(call.failed for call in agent.calls)
        lines.append(f"| {agent.ref} | {agent.kind} | {len(agent.replies)} "
                     f"| {len(agent.calls)} | {failed} "
                     f"| {span(agent.first, agent.last)} "
                     f"| {cell(agent.description)} |")
    lines += _by_tool(calls)
    lines += _reasons(calls, "blocked", "Hook blocks")
    lines += _reasons(calls, "denied", "Denied")
    lines += _repeats(session)
    lines += _largest(calls)
    lines += ["", "## User messages", ""]
    lines += [f"- {m.ref} {stamp(m.timestamp)} "
              f"{transcript.shorten(m.text, USER_WIDTH)}"
              for m in main.user_messages] or ["None."]
    lines += ["", "## Calls"]
    for agent in session.agents:
        title = agent.ref if agent.ref == "main" \
            else f"{agent.ref} {agent.kind}"
        if agent.description:
            title += f": {agent.description}"
        lines += ["", f"### {title}", ""]
        lines += [_line(call) for call in agent.calls] or ["None."]
    return "\n".join(lines)


def show(call: Call) -> str:
    lines = [f"{call.ref} {call.tool} by {call.agent} at {stamp(call.timestamp)}"
             f": {call.status}"]
    if call.subagent:
        lines.append(f"Spawned {call.subagent}.")
    lines += ["", "## Input", "",
              json.dumps(call.input, indent=2, ensure_ascii=False), "",
              "## Result", ""]
    result = call.result if call.result is not None else "(no result)"
    if len(result) > SHOW_LIMIT:
        result = result[:SHOW_LIMIT] + \
            f"\n… cut at {SHOW_LIMIT} of {len(result)} characters."
    lines.append(result)
    return "\n".join(lines)


def _line(call: Call) -> str:
    size = size_text(len(call.result)) if call.result is not None else "-"
    text = f"{call.ref} {stamp(call.timestamp)} {call.tool} {call.status} " \
           f"{size} {call.summary}"
    if call.subagent:
        text += f" → {call.subagent}"
    if call.reason:
        text += f" ⟶ {transcript.shorten(call.reason, 100)}"
    return text


def _by_tool(calls: List[Call]) -> List[str]:
    counts: Counter = Counter()
    failed: Counter = Counter()
    chars: Counter = Counter()
    for call in calls:
        counts[call.tool] += 1
        failed[call.tool] += call.failed
        chars[call.tool] += len(call.result or "")
    lines = ["", "## Calls by tool", "",
             "| Tool | Calls | Failed | Result size |", "| --- | --- | --- | --- |"]
    lines += [f"| {tool} | {count} | {failed[tool]} | {size_text(chars[tool])} |"
              for tool, count in counts.most_common()]
    return lines


def _reasons(calls: List[Call], status: str, title: str) -> List[str]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for call in calls:
        if call.status == status:
            groups[transcript.shorten(call.reason, 120)].append(call.ref)
    if not groups:
        return []
    lines = ["", f"## {title}", ""]
    for reason, refs in sorted(groups.items(), key=lambda g: -len(g[1])):
        lines.append(f"- {len(refs)}× {reason} — {ref_list(refs)}")
    return lines


def _repeats(session: Session) -> List[str]:
    """Identical calls by one agent, and the ones retried unchanged after
    failing, with no Write or Edit in between. A repeated read says whether
    a Write or Edit changed the file between the first read and the last: a
    shell command might have too."""
    groups: Dict[str, List[Call]] = defaultdict(list)
    for call in session.calls:
        groups[call.key].append(call)
    writes = sorted((c.timestamp, c.path) for c in session.calls
                    if c.tool in transcript.WRITERS and c.path)
    retried, repeated = [], []
    for group in groups.values():
        if len(group) < 2:
            continue
        for before, after in zip(group, group[1:]):
            changed = any(before.timestamp <= when <= after.timestamp
                          for when, _ in writes)
            if before.failed and not changed:
                retried.append(f"- {after.tool} {after.summary} — "
                               f"{before.ref} {before.status}, retried "
                               f"unchanged as {after.ref}: {after.status}")
        note = ""
        if group[0].tool == "Read":
            written = any(group[0].timestamp <= when <= group[-1].timestamp
                          and path == group[0].path for when, path in writes)
            note = " (a Write or Edit in between)" if written \
                else " (no Write or Edit in between)"
        repeated.append((len(group), f"- {len(group)}× {group[0].tool} "
                         f"{group[0].summary}{note} — "
                         f"{ref_list([c.ref for c in group])}"))
    lines = []
    if retried:
        lines += ["", "## Retried unchanged after failing", "", *retried]
    if repeated:
        repeated.sort(key=lambda item: -item[0])
        lines += ["", "## Repeated identical calls", "",
                  *[text for _, text in repeated]]
    return lines


def _largest(calls: List[Call]) -> List[str]:
    ranked = sorted((c for c in calls if c.result), key=lambda c:
                    -len(c.result or ""))[:LARGEST]
    if not ranked:
        return []
    return ["", "## Largest results", ""] + [
        f"- {size_text(len(c.result or ''))} {c.ref} {c.tool} {c.summary}"
        for c in ranked]


def ref_list(refs: List[str]) -> str:
    shown = ", ".join(refs[:REFS_SHOWN])
    if len(refs) > REFS_SHOWN:
        shown += f" and {len(refs) - REFS_SHOWN} more"
    return shown


def cell(text: str) -> str:
    return transcript.shorten(text, 60).replace("|", "/")


def stamp(timestamp: str) -> str:
    """An ISO timestamp as month, day and time, such as 11-23 10:31:05."""
    return timestamp[5:19].replace("T", " ") if timestamp else "?"


def span(first: str, last: str) -> str:
    try:
        start = datetime.fromisoformat(first.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return "?"
    seconds = int((end - start).total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        return f"{days}d{hours:02d}h"
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{seconds:02d}s"
    return f"{seconds}s"


def size_text(chars: int) -> str:
    """A number of characters, such as 850, 1.2k or 3.4M."""
    if chars < 1000:
        return str(chars)
    if chars < 10_000:
        return f"{chars / 1000:.1f}k"
    if chars < 1_000_000:
        return f"{chars // 1000}k"
    return f"{chars / 1_000_000:.1f}M"
