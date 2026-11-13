"""Git-level tricks: symlinks, modes, odd paths, large files, heavy renames,
whitespace noise and merge commits."""

from __future__ import annotations

import posixpath
import re
import unicodedata
from typing import Dict, Iterator, List

from ..escape import ascii_only, is_hidden
from ..model import GITLINK, HIGH, INFO, REVIEW, Context, Finding

SCRIPT_EXT = re.compile(r"\.(?:sh|bash|bats|py|pl|rb|js|mjs|php|lua|tcl|"
                        r"awk|zsh|ksh|fish|ps1)\Z|(?:^|/)[^/.]+\Z")
RESERVED = re.compile(r"^(?:con|prn|aux|nul|com\d|lpt\d)(?:\..*)?\Z",
                      re.IGNORECASE)


def check(ctx: Context) -> Iterator[Finding]:
    symlinks = []
    gitlinks = []
    for change in ctx.files:
        if change.deleted:
            continue
        yield from _path(change.path)
        if change.is_symlink:
            symlinks.append(change)
            target = change.new().decode("utf-8", "replace")
            outside = target.startswith("/") or _escapes(change.path, target)
            yield Finding(HIGH if outside else REVIEW, "gitlevel-symlink",
                          change.path, 0,
                          f"a symlink to {ascii_only(target, 100)}"
                          + (", outside the repository" if outside else ""))
        if change.change.new_mode == GITLINK:
            gitlinks.append(change)
        old, new = change.change.old_mode, change.change.new_mode
        if new == "100755" and old != "100755":
            yield Finding(REVIEW if SCRIPT_EXT.search(change.path) else HIGH,
                          "gitlevel-executable", change.path, 0,
                          "made executable")
        size = len(change.new())
        if size > 10_000_000:
            yield Finding(HIGH, "gitlevel-large", change.path, 0,
                          f"{size} bytes: too large to review")
        elif size > 1_000_000:
            yield Finding(REVIEW, "gitlevel-large", change.path, 0,
                          f"{size} bytes")
        if change.status == "R" and change.change.score < 75:
            yield Finding(REVIEW, "gitlevel-rename-modified", change.path, 0,
                          f"renamed from "
                          f"{ascii_only(change.change.old_path or '', 80)} "
                          f"and {100 - change.change.score}% changed: read "
                          f"it as a new file")
    if symlinks and gitlinks:
        yield Finding(HIGH, "gitlevel-symlink-and-submodule",
                      symlinks[0].path, 0,
                      "a symlink and a submodule in one pull request, the "
                      "shape of the CVE-2024-32002 clone exploit")
    yield from _case_collisions(ctx)
    yield from _whitespace_noise(ctx)
    for commit in ctx.commits:
        if len(commit.parents) > 1:
            yield Finding(HIGH, "gitlevel-merge-commit", "(history)", 0,
                          f"merge commit {commit.sha[:12]}: a merge can "
                          f"carry changes neither parent shows; ask for a "
                          f"rebase")


def _escapes(path: str, target: str) -> bool:
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(path),
                                               target))
    return joined == ".." or joined.startswith("../")


def _path(path: str) -> Iterator[Finding]:
    parts = path.split("/")
    reasons: List[str] = []
    if any(is_hidden(ord(char)) and char != "\t" for char in path):
        reasons.append("hidden or control characters")
    for part in parts:
        bare = "".join(char for char in part if not is_hidden(ord(char)))
        bare = unicodedata.normalize("NFKC", bare).rstrip(". ").lower()
        if bare in (".git", "git~1"):
            reasons.append("a component that can pass for .git")
        if part in (".", "..") or part.endswith((" ", ".")):
            reasons.append("a component that ends in a space or dot, or is "
                           ". or ..")
        if part.startswith("-"):
            reasons.append("a component starting with -, read as an option")
        if RESERVED.match(part):
            reasons.append("a name Windows reserves")
    if reasons:
        yield Finding(HIGH, "gitlevel-path", path, 0,
                      "the path has " + "; ".join(sorted(set(reasons))))
    elif not path.isascii():
        yield Finding(REVIEW, "gitlevel-path", path, 0,
                      "a non-ASCII path, which can look like another")
    if len(path) > 255:
        yield Finding(REVIEW, "gitlevel-path", path, 0, "a very long path")


def _case_collisions(ctx: Context) -> Iterator[Finding]:
    folded: Dict[str, List[str]] = {}
    for path in ctx.head_tree():
        key = unicodedata.normalize("NFKC", path).casefold()
        folded.setdefault(key, []).append(path)
    changed = {change.path for change in ctx.files}
    for paths in folded.values():
        if len(paths) > 1 and changed & set(paths):
            yield Finding(HIGH, "gitlevel-case-collision", paths[0], 0,
                          "paths that are the same on case-insensitive file "
                          "systems: " + ", ".join(ascii_only(p, 60)
                                                  for p in paths))


def _whitespace_noise(ctx: Context) -> Iterator[Finding]:
    only_space = []
    real = []
    for change in ctx.text_files():
        if change.status not in "MR":
            continue
        if re.sub(r"\s+", "", change.old_text()) == re.sub(
                r"\s+", "", change.new_text()):
            only_space.append(change.path)
        else:
            real.append(change.path)
    if len(only_space) >= 5 and real:
        yield Finding(INFO if len(real) > 5 else REVIEW,
                      "gitlevel-whitespace-noise", real[0], 0,
                      f"{len(only_space)} files change only whitespace, "
                      f"which can bury the real changes, in: "
                      + ", ".join(ascii_only(p, 60) for p in real[:5]))
