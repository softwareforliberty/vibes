"""rules-bite's command: check each boundary rule in scripts/check still
fails on the breach that proved it.

    rules-bite [--staged]

When a builder adds a rule to scripts/check, such as that only a
component's entry points may be imported from outside it, it proves the
rule bites by breaking it once, and keeps that breach as a patch in
scripts/breaches/<rule>.patch, committed with the rule. Each patch starts
with two lines, before its diff:

    Rule: the core never imports an edge
    Fails with: Contract "core never imports edges" BROKEN

rules-bite applies each breach to a throwaway worktree of HEAD, or with
--staged, of what's staged, runs scripts/check there, and prints one line
for each:

    BITES <patch>       scripts/check failed, saying what the patch expects
    MISSED <patch>      scripts/check passed: the rule no longer catches it
    ELSEWHERE <patch>   scripts/check failed, but not saying what's expected
    STALE <patch>       the breach no longer applies to the code

Each run's output is kept in .vibes/rules-bite/<patch>.log. A breach that
adds a new file, rather than changing one, stays applicable as the code
changes. Prints NO BREACHES when there are none. Exits 0 when every breach
bites or there are none, 1 when any doesn't, and 2 on an error.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Sequence

BREACHES = Path("scripts") / "breaches"
CHECK = Path("scripts") / "check"
LOGS = Path(".vibes") / "rules-bite"
HEADER = re.compile(r"^(Rule|Fails with):\s*(.*?)\s*$")
TIMEOUT = 3600
# What git sets for a hook, which would point the throwaway worktree's
# commands at the real repository's index and tree.
HOOK_VARIABLES = ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_PREFIX",
                  "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR")


def git(*args: str, cwd: Path) -> str:
    found = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                           text=True, check=False)
    if found.returncode != 0:
        raise RuntimeError(found.stderr.strip() or f"git {args[0]} failed")
    return found.stdout.strip()


def check_header(name: str, text: str) -> tuple[str, str]:
    """The patch's rule and the text scripts/check must print."""
    rule = fails = ""
    for line in text.splitlines():
        if line.startswith("diff --git") or line.startswith("--- "):
            break
        match = HEADER.match(line)
        if match and match.group(1) == "Rule":
            rule = match.group(2)
        elif match:
            fails = match.group(2)
    if not rule or not fails:
        raise ValueError(f"{name}: it needs a Rule: line and a Fails "
                         "with: line before its diff")
    return rule, fails


def expected(patch: Path) -> tuple[str, str]:
    return check_header(str(patch), patch.read_text(encoding="utf-8"))


def staged_commit(root: Path) -> str:
    """A commit holding what's staged, on top of HEAD, that no ref points
    to."""
    tree = git("write-tree", cwd=root)
    return git("commit-tree", tree, "-p", "HEAD", "-m", "Staged", cwd=root)


def check(root: Path, work: Path, commit: str, patch: Path,
          log: Path) -> str:
    git("reset", "--hard", "--quiet", commit, cwd=work)
    git("clean", "-fdq", cwd=work)
    applied = subprocess.run(["git", "apply", "--whitespace=nowarn",
                              str(patch)], cwd=work, capture_output=True,
                             text=True, check=False)
    if applied.returncode != 0:
        log.write_text(applied.stderr, encoding="utf-8")
        return "STALE"
    _, fails = expected(patch)
    try:
        run = subprocess.run([str(work / CHECK)], cwd=work,
                             capture_output=True, text=True, check=False,
                             timeout=TIMEOUT)
        output = run.stdout + run.stderr
        status = run.returncode
    except subprocess.TimeoutExpired:
        output, status = f"timed out after {TIMEOUT}s\n", 1
    log.write_text(output, encoding="utf-8")
    if status == 0:
        return "MISSED"
    return "BITES" if fails in output else "ELSEWHERE"


def main(argv: Sequence[str]) -> int:
    args = list(argv)
    staged = args == ["--staged"]
    if args and not staged:
        print("usage: rules-bite [--staged]", file=sys.stderr)
        return 2
    try:
        root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()))
        # In a pre-commit hook, GIT_INDEX_FILE names the index being
        # committed: read it, then let no git command below see it.
        commit = staged_commit(root) if staged else ""
        for name in HOOK_VARIABLES:
            os.environ.pop(name, None)
        if not staged:
            commit = git("rev-parse", "HEAD", cwd=root)
        patches = sorted(
            path for path in git("ls-tree", "-r", "--name-only", commit,
                                 "--", str(BREACHES), cwd=root).splitlines()
            if path.endswith(".patch"))
        if not patches:
            print("NO BREACHES")
            return 0
        for path in patches:
            text = subprocess.run(["git", "show", f"{commit}:{path}"],
                                  cwd=root, capture_output=True, check=True)
            check_header(path, text.stdout.decode("utf-8", "replace"))
        logs = root / LOGS
        logs.mkdir(parents=True, exist_ok=True)
        ignore = root / ".vibes" / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n", encoding="utf-8")
        failed = 0
        work = Path(tempfile.mkdtemp(prefix="rules-bite-"))
        work.rmdir()
        git("worktree", "add", "--detach", "--quiet", str(work), commit,
            cwd=root)
        try:
            for path in patches:
                name = Path(path).stem
                # The patch as staged, which is what's being committed.
                patch = Path(work.parent) / f"{work.name}-{name}.patch"
                shown = subprocess.run(
                    ["git", "show", f"{commit}:{path}"], cwd=root,
                    capture_output=True, check=True)
                patch.write_bytes(shown.stdout)
                try:
                    verdict = check(root, work, commit, patch,
                                    logs / f"{name}.log")
                finally:
                    patch.unlink()
                print(f"{verdict} {path}")
                failed += verdict != "BITES"
        finally:
            subprocess.run(["git", "worktree", "remove", "--force",
                            str(work)], cwd=root, capture_output=True,
                           check=False)
            shutil.rmtree(work, ignore_errors=True)
    except (RuntimeError, ValueError, OSError) as error:
        print(f"rules-bite: {error}", file=sys.stderr)
        return 2
    return 1 if failed else 0
