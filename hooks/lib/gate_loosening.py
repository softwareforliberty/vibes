"""Finds changes that would loosen a repository's commit gate.

    python3 -I -S gate_loosening.py <directory>

Compares scripts/check and scripts/check-file at HEAD with the index and
the working tree, and prints one line for each loosening: the file deleted,
its executable bit dropped, a line removed whose words no added line in the
same file keeps, or a line added that can end the checks early. Extending
the gate keeps every word, such as adding a guide to the "# Guides:" line
or a file to a lint command, so it passes; dropping a check, an option or a
guide doesn't. A changed line that gains a way to ignore a failure, such as
"|| true" or "--exit-zero", doesn't keep the old one. Blank lines and
comments other than the "# Guides:" line don't count. Any staged change to
.vibes-tracker, the issue tracker's commands, counts too: they run as the
user.

Prints nothing for a file HEAD doesn't have, outside a repository, and on a
spike branch, where the gate doesn't run.
"""

import difflib
import os
import subprocess
import sys
from collections import Counter

FILES = ("scripts/check", "scripts/check-file")
# The issue tracker's commands: any change to them needs confirming.
TRACKER = ".vibes-tracker"
GUIDES = "# Guides:"
SHOWN = 10
# Words that, gained by a changed line, can turn a failure into a pass.
IGNORES_FAILURE = ("||", "true", ":", "exit", "return", "+e", "--exit-zero",
                   "--exit-zero-even-if-changed", "--no-fail")
# First words of an added line that can end the checks early or stop a
# failure from ending them.
ENDS_EARLY = ("exit", "return")


def git(directory, *args):
    """git's output, or None when it fails."""
    found = subprocess.run(["git", "-C", directory, *args],
                           capture_output=True, check=False)
    if found.returncode != 0:
        return None
    return found.stdout.decode("utf-8", "replace")


def counts(line):
    """The line's words, unless it's blank or a comment that doesn't
    matter."""
    text = line.strip()
    if not text or (text.startswith("#") and not text.startswith(GUIDES)):
        return None
    return Counter(text.split())


def keeps(words, kept):
    """Whether a new line keeps every word of an old one, and gains none
    that could ignore a failure."""
    gained = kept - words
    return not words - kept and not any(
        word in IGNORES_FAILURE or "||" in word for word in gained)


def escapes(line):
    """Whether an added line can end the checks early, such as exit 0, or
    stop a failure from ending them, such as set +e."""
    words = line.split()
    return bool(words) and (words[0] in ENDS_EARLY
                            or (words[0] == "set" and "+e" in words[1:]))


def loosened(old, new):
    """Each way the new text loosens the old: a line removed or changed,
    or one added that ends the checks early."""
    old_lines, new_lines = old.splitlines(), new.splitlines()
    gone, added, found = [], [], []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines,
                                      autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("delete", "replace"):
            gone += old_lines[i1:i2]
        if tag in ("insert", "replace"):
            added += [c for c in map(counts, new_lines[j1:j2]) if c]
            found += [f"adds `{line.strip()}`" for line in new_lines[j1:j2]
                      if escapes(line)]
    for line in gone:
        words = counts(line)
        if words and not any(keeps(words, kept) for kept in added):
            found.append(f"removes or changes `{line.strip()}`")
    return found


def loosenings(directory):
    root = git(directory, "rev-parse", "--show-toplevel")
    if root is None:
        return []
    root = root.strip()
    branch = (git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
              or "").strip()
    if branch.startswith("spike/"):
        return []
    found = []
    for path in FILES:
        tree = git(root, "ls-tree", "HEAD", "--", path)
        if not tree:
            continue
        executable = tree.split()[0] == "100755"
        old = git(root, "show", f"HEAD:{path}") or ""
        staged = git(root, "ls-files", "--stage", "--", path) or ""
        full = os.path.join(root, path)
        if not staged or not os.path.isfile(full):
            found.append(f"{path}: deleted")
            continue
        if executable and (staged.split()[0] != "100755"
                           or not os.access(full, os.X_OK)):
            found.append(f"{path}: no longer executable, which turns "
                         "the gate off")
        versions = [git(root, "show", f":{path}") or ""]
        with open(full, encoding="utf-8", errors="replace") as stream:
            versions.append(stream.read())
        lost = []
        for new in versions:
            lost += [item for item in loosened(old, new) if item not in lost]
        found += [f"{path}: {item}" for item in lost]
    if git(root, "rev-parse", "--verify", "--quiet", "HEAD") is None:
        tracker = git(root, "ls-files", "--", TRACKER)
    else:
        tracker = git(root, "diff", "--cached", "--name-only", "HEAD", "--",
                      TRACKER)
    if (tracker or "").strip():
        found.append(f"{TRACKER}: changes the commands vibes runs against "
                     "the issue tracker, as you")
    if len(found) > SHOWN:
        found = found[:SHOWN] + [f"and {len(found) - SHOWN} more"]
    return found


def main():
    if len(sys.argv) != 2:
        print("usage: gate_loosening.py <directory>", file=sys.stderr)
        return 2
    for line in loosenings(sys.argv[1]):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
