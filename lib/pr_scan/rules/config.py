"""Changes to .vibes-review, and to the paths it protects."""

from __future__ import annotations

from typing import Iterator

from ..escape import ascii_only
from ..model import CONFIG_FILE, HIGH, REVIEW, Context, Finding, matches


def check(ctx: Context) -> Iterator[Finding]:
    if ctx.config_changed:
        yield Finding(HIGH, "config-changed", CONFIG_FILE, 0,
                      "the pull request changes the review's own config; "
                      "this scan used the base branch's version")
    for number, line in ctx.config.errors:
        yield Finding(REVIEW, "config-invalid", CONFIG_FILE, number,
                      f"line not understood, so ignored: "
                      f"{ascii_only(line, 80)}")
    for change in ctx.files:
        paths = {change.path, change.change.old_path or change.path}
        if any(matches(path, ctx.config.protected) for path in paths):
            yield Finding(HIGH, "config-protected", change.path, 0,
                          f"a protected path is "
                          f"{'deleted' if change.deleted else 'changed'}")
