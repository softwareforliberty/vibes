"""setup-needs' command.

    setup-needs <base>

Run it in a repository. It reads the lines the branch adds since <base>,
and lists each setting they need that a person must provide and the base
didn't use anywhere: an environment variable the code reads, a key added
to an example env file, or a GitHub Actions secret or variable a workflow
names. One line each, sorted by name, saying where it appears:

    STRIPE_KEY: read in pay.py:3; in .env.example:2; a GitHub secret in .github/workflows/ci.yml:4

It prints "None." when there's nothing. Variables every machine or CI run
has, such as HOME, PATH, CI and GITHUB_TOKEN, are left out. Exits 0, or 2
on an error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

NAME = r"([A-Za-z_][A-Za-z0-9_]*)"
Q = r"""['"]"""

# How code in each language reads an environment variable.
READS = [re.compile(pattern) for pattern in (
    rf"os\.environ\[\s*{Q}{NAME}{Q}",
    rf"os\.environ\.get\(\s*{Q}{NAME}{Q}",
    rf"os\.getenv\(\s*{Q}{NAME}{Q}",
    rf"process\.env\.{NAME}",
    rf"process\.env\[\s*{Q}{NAME}{Q}",
    rf"import\.meta\.env\.{NAME}",
    rf"os\.(?:Getenv|LookupEnv)\(\s*\"{NAME}\"",
    rf"env::var(?:_os)?\(\s*\"{NAME}\"",
    rf"env!\(\s*\"{NAME}\"",
    rf"ENV(?:\.fetch\(\s*|\[\s*){Q}{NAME}{Q}",
    rf"System\.getenv\(\s*\"{NAME}\"",
    rf"System\.get_env\(\s*\"{NAME}\"",
    rf"Environment\.GetEnvironmentVariable\(\s*\"{NAME}\"",
    rf"\$_(?:ENV|SERVER)\[\s*{Q}{NAME}{Q}",
    rf"(?<![\w.])getenv\(\s*{Q}{NAME}{Q}",
)]
EXAMPLE_ENV = re.compile(
    r"(^|/)(\.env\.(example|sample|template|dist)|example\.env|env\.example)$")
ENV_LINE = re.compile(rf"^\s*(?:export\s+)?{NAME}\s*=")
WORKFLOW = re.compile(r"^\.github/workflows/[^/]+\.ya?ml$")
SECRET = re.compile(rf"\bsecrets\.{NAME}")
VARIABLE = re.compile(rf"\bvars\.{NAME}")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

# Set on every machine or CI run, so nobody needs to provide them.
EVERYWHERE = {"PATH", "HOME", "USER", "SHELL", "PWD", "TERM", "LANG",
              "TMPDIR", "TZ", "CI", "GITHUB_TOKEN", "NODE_ENV", "HOSTNAME"}
EVERYWHERE_PREFIXES = ("GITHUB_", "RUNNER_", "LC_")

# What each kind of finding says.
KINDS = ("read in", "in", "a GitHub secret in", "a GitHub variable in")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=False)


def added_lines(base: str) -> List[Tuple[str, int, str]]:
    """Each line the branch adds since base, with its path and number."""
    diff = _git("diff", "-U0", "--no-color", "--no-ext-diff",
                f"{base}...HEAD")
    if diff.returncode:
        raise ValueError(diff.stderr.strip() or f"can't diff from {base}")
    lines: List[Tuple[str, int, str]] = []
    path, number = "", 0
    for line in diff.stdout.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
        elif (hunk := HUNK.match(line)):
            number = int(hunk.group(1))
        elif line.startswith("+") and path:
            lines.append((path, number, line[1:]))
            number += 1
    return lines


def findings(lines: List[Tuple[str, int, str]]) -> Dict[str, List[str]]:
    """Each name the added lines need, with where it appears."""
    found: Dict[str, List[str]] = {}

    def note(name: str, kind: str, path: str, number: int) -> None:
        where = f"{kind} {path}:{number}"
        if where not in found.setdefault(name, []):
            found[name].append(where)

    for path, number, text in lines:
        if EXAMPLE_ENV.search(path):
            match = ENV_LINE.match(text)
            if match:
                note(match.group(1), KINDS[1], path, number)
            continue
        if WORKFLOW.match(path):
            for match in SECRET.finditer(text):
                note(match.group(1), KINDS[2], path, number)
            for match in VARIABLE.finditer(text):
                note(match.group(1), KINDS[3], path, number)
            continue
        for pattern in READS:
            for match in pattern.finditer(text):
                note(match.group(1), KINDS[0], path, number)
    return found


def needed(name: str, base: str) -> bool:
    """Whether a person must provide it: it isn't set everywhere, and the
    base didn't already use it."""
    if name in EVERYWHERE or name.startswith(EVERYWHERE_PREFIXES):
        return False
    return _git("grep", "-q", "-w", "-F", "-e", name, base,
                "--").returncode != 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or [])
    if len(args) != 1:
        print("usage: setup-needs <base>", file=sys.stderr)
        return 2
    base = args[0]
    if _git("rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode:
        print(f"setup-needs: no commit {base}", file=sys.stderr)
        return 2
    try:
        found = findings(added_lines(base))
    except ValueError as error:
        print(f"setup-needs: {error}", file=sys.stderr)
        return 2
    names = sorted(name for name in found if needed(name, base))
    if not names:
        print("None.")
    for name in names:
        order = sorted(found[name],
                       key=lambda where: KINDS.index(where.rsplit(" ", 1)[0]))
        print(f"{name}: " + "; ".join(order))
    return 0
