"""Files that configure or instruct coding agents and editors.

A CLAUDE.md, a .claude/settings.json hook, an .mcp.json server, a VS Code
task or an .envrc runs commands, or tells an agent what to do, on the
machine of whoever opens the repository: often the maintainer.
"""

from __future__ import annotations

from typing import Iterator

from ..model import HIGH, REVIEW, Context, Finding


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.files:
        if "agent-config" not in change.classes:
            continue
        if change.deleted:
            yield Finding(REVIEW, "agentcfg-deleted", change.path, 0,
                          "agent or editor config deleted: check it didn't "
                          "hold a protection")
        else:
            yield Finding(HIGH, "agentcfg-changed", change.path, 0,
                          "configures or instructs coding agents or editors: "
                          "it can run commands, or steer an agent, on the "
                          "machine of whoever opens the repository")
