"""check-all's command: run the slow tests, once for each tree.

    check-all [--tree <dir>]

Runs the project's `scripts/check --all` in the repository holding <dir>
(the current directory by default), unless it already passed on the same
files: the tree of HEAD. Each tree that passed is kept, one a line, in
vibes-check-all-passed in the repository's shared git folder, so every
worktree of it shares them, such as a builder's worktree and the main
checkout after it joins. A tree that failed is run again every time.

The working tree must be clean, so that the tree that's run is the one
that's recorded; check-all refuses one with changes, staged or not, or
with untracked files. It prints the run's output, then one line:

    PASSED <tree>             it ran and passed
    PASSED <tree> (already)   it passed on this tree before, so didn't run
    FAILED <tree>             it ran and failed
    CHANGED <tree>            it passed, but the files changed while it ran,
                              so nothing is recorded

Exits 0 for PASSED, 1 for FAILED or CHANGED, and 2 on an error, such as no
repository, no executable scripts/check or a working tree with changes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RECORD = "vibes-check-all-passed"
# The most trees kept; the oldest go first.
KEEP = 200


def git(root: Path, *args: str) -> str:
    """The output of a git command in the repository, without its newline."""
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def state(root: Path) -> tuple[str, str]:
    """HEAD's tree, and git's short status of the working tree."""
    return (git(root, "rev-parse", "HEAD^{tree}"),
            git(root, "status", "--porcelain", "--untracked-files=normal"))


def record_path(root: Path) -> Path:
    common = Path(git(root, "rev-parse", "--git-common-dir"))
    return (common if common.is_absolute() else root / common) / RECORD


def passed(record: Path) -> list[str]:
    try:
        return record.read_text(encoding="utf-8").split()
    except OSError:
        return []


def main(argv: list[str]) -> int:
    if argv and not (len(argv) == 2 and argv[0] == "--tree"):
        print("usage: check-all [--tree <dir>]", file=sys.stderr)
        return 2
    start = Path(argv[1] if argv else os.getcwd())
    try:
        root = Path(git(start, "rev-parse", "--show-toplevel"))
        tree, status = state(root)
    except (subprocess.CalledProcessError, OSError):
        print(f"check-all: {start} isn't in a git repository with a commit",
              file=sys.stderr)
        return 2
    check = root / "scripts" / "check"
    if not os.access(check, os.X_OK):
        print(f"check-all: {root} has no executable scripts/check",
              file=sys.stderr)
        return 2
    if status:
        print("check-all: the working tree has changes; commit or stash "
              "them first, so the files run are the ones recorded:\n"
              + status, file=sys.stderr)
        return 2
    record = record_path(root)
    trees = passed(record)
    if tree in trees:
        print(f"PASSED {tree} (already)")
        return 0
    status_code = subprocess.run([str(check), "--all"], cwd=root,
                                 check=False).returncode
    if status_code != 0:
        print(f"FAILED {tree}")
        return 1
    if state(root) != (tree, ""):
        print(f"CHANGED {tree}")
        return 1
    trees = [t for t in passed(record) if t != tree] + [tree]
    record.write_text("\n".join(trees[-KEEP:]) + "\n", encoding="utf-8")
    print(f"PASSED {tree}")
    return 0
