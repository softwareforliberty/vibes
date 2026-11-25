"""The test-first eval: vibes:builder runs only the tests it's changing.

The project is durations, a small Python library with a commit gate whose
scripts/check runs every test, among them an end-to-end one that takes
half a minute, and a scripts/test-one that runs only the tests it's
given. The builder gets a one-batch rebuild plan for parse_duration, on
the vibe/durations branch.

The case passes when the builder ran its tests with scripts/test-one,
never ran scripts/check with no mode itself (even if the test-one hook
refused it), committed its work on the branch with every test passing,
and its report shows a red run before each green one.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from research_cases import dispatched, llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/durations"

PROJECT: Dict[str, str] = {
    "README.md": """# durations

Reads the durations people type, such as `90s` or `1h30m`, as seconds.

Every commit passes `scripts/check`, which runs every test. While you
work, `scripts/test-one <test>` runs only the tests you name.
""",
    "durations/__init__.py": '"""Read typed durations as seconds."""\n',
    "durations/parse.py": '''"""Parse the durations people type."""


def parse_seconds(text: str) -> int:
    """Return the seconds in a duration of whole seconds, such as "90s"."""
    if not text.endswith("s") or not text[:-1].isdigit():
        raise ValueError(f"not a number of seconds: {text!r}")
    return int(text[:-1])
''',
    "tests/__init__.py": "",
    "tests/test_parse.py": '''"""Tests for durations.parse."""

import unittest

from durations.parse import parse_seconds


class ParseSecondsTest(unittest.TestCase):
    def test_reads_whole_seconds(self) -> None:
        self.assertEqual(parse_seconds("90s"), 90)

    def test_rejects_a_missing_unit(self) -> None:
        with self.assertRaises(ValueError):
            parse_seconds("90")
''',
    "tests/test_end_to_end.py": '''"""The end-to-end check, which takes half a minute."""

import time
import unittest

from durations.parse import parse_seconds


class EndToEndTest(unittest.TestCase):
    def test_a_day_of_readings(self) -> None:
        time.sleep(30)
        self.assertEqual(sum(parse_seconds(f"{n}s") for n in range(10)), 45)
''',
    "scripts/check": """#!/usr/bin/env bash
#
# The commit gate: every commit must pass this. It runs every test.
#
# Guides: languages/Python

set -euo pipefail

cd -- "$(dirname -- "$0")/.."
python3 -m unittest discover -s tests -t . -q
""",
    "scripts/test-one": """#!/usr/bin/env bash
#
# Run only the tests given, while you work: test files, such as
# tests/test_parse.py, or single tests, such as
# tests/test_parse.py::ParseSecondsTest::test_reads_whole_seconds. With no
# test, it lists them. The gate runs every test on each commit.

set -euo pipefail

cd -- "$(dirname -- "$0")/.."
if (($# == 0)); then
  python3 -c '
import unittest
def walk(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from walk(item)
        else:
            yield item.id()
for name in walk(unittest.defaultTestLoader.discover("tests", top_level_dir=".")):
    print(name)
'
  exit 0
fi
names=()
for test; do
  test="${test/.py::/::}"
  test="${test%.py}"
  test="${test//\\//.}"
  names+=("${test//::/.}")
done
python3 -m unittest -q "${names[@]}"
""",
    "docs/specs/durations/spec.md": """# Spec: durations

## Summary

People type how long a task took, such as `1h30m`. `parse_duration` reads
such a duration as a number of seconds, so the report can add them up.

## Requirements

- **R1:** `parse_duration(text)` returns the seconds in `text`, which is
  one or more of a whole number of hours (`h`), minutes (`m`) and seconds
  (`s`), in that order, each at most once, such as `1h30m` (5400), `45s`
  (45) or `2h5s` (7205).
- **R2:** Any other text, such as an empty string, an unknown unit (`3d`),
  a repeated unit (`1m2m`) or units out of order (`5s1m`), raises
  `ValueError` naming the text.
""",
}

RECORDS: Dict[str, str] = {
    "rebuild-plan.md": """# Rebuild plan: durations

One batch. Add `parse_duration` to `durations/parse.py`, with its tests in
`tests/test_parse.py`, test-first.

## Batch 1

- [ ] R1: `parse_duration` sums hours, minutes and seconds: `1h30m` is
  5400, `45s` is 45, `2h5s` is 7205.
- [ ] R2: `parse_duration` raises `ValueError` naming the text for an
  empty string, an unknown unit, a repeated unit and units out of order.
""",
    "finish": """#!/usr/bin/env bash
#
# What the builder left: its branch, its commits, whether the tree is
# clean, and whether every test passes.

cd -- "$(dirname -- "$0")/../.."
printf 'BRANCH %s\\n' "$(git branch --show-current)"
printf 'COMMITS %s\\n' "$(git rev-list --count main..HEAD)"
if [ -z "$(git status --porcelain)" ]; then
  echo 'TREE CLEAN'
else
  echo 'TREE CHANGED'
fi
if python3 -m unittest discover -s tests -t . -q >/dev/null 2>&1; then
  echo 'TESTS PASS'
else
  echo 'TESTS FAIL'
fi
""",
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# durations on its main branch, with its gate and test-one, and the
# vibe/durations branch the builder works on, with the plan in the run
# directory.

set -euo pipefail
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
git init -q -b main .
git config user.name evals
git config user.email evals@example.invalid
cp -R "${{fixtures}}/tdd-project/." .
chmod +x scripts/check scripts/test-one
printf '.vibes/\\n__pycache__/\\n' > .gitignore
git add -A
git commit -q -m "durations"
git switch -q -c vibe/durations
mkdir -p {run}
cp -R "${{fixtures}}/tdd-run/." {run}/
chmod +x {run}/finish
"""

BRIEF = f"""Mode: build
Task: add parse_duration, which reads durations such as 1h30m as seconds
Branches: rebuild vibe/durations, base main; no spike
Spec: <cwd>/docs/specs/durations/spec.md
Rebuild plan: <cwd>/{RUN}/rebuild-plan.md
Guides: languages/Python
Batch: Batch 1 of the rebuild plan, its two entries. It's the first and
only batch.
Report: <cwd>/{RUN}/build-1.md"""

PROMPT = f"""---
max_turns: 150
timeout_seconds: 2400
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(git *)", "Bash(scripts/*)", "Bash(./scripts/*)", "Bash(*/scripts/*)", "Bash(python3 *)", "Bash(cd *)", "Bash(cat *)", "Bash(ls *)", "Bash(*/finish)"]
---

Run the `vibes:builder` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
{BRIEF}
```

Don't do its work yourself. When it's done, run `<cwd>/{RUN}/finish`,
then read `<cwd>/{RUN}/build-1.md`.

Reply with only the agent's reply, the lines `finish` printed, and the
report, complete and unchanged, and nothing else.
"""

# A command that runs a project's scripts/check with no mode: after any
# earlier commands, variable settings and wrappers, and not followed by
# --all or --static anywhere in the same command. A JSON string's escaped
# quotes are skipped over.
BARE_CHECK = (
    '"command": ?"(?:(?:[^"\\\\]|\\\\.)*[;&|(] *)?'
    '(?:[A-Za-z_][A-Za-z0-9_]*=[^ "]* +)*'
    '(?:(?:time|bash|sh|command|env|nice|timeout [0-9]+) +)*'
    '(?:[^" ;&|]*/)?scripts/check(?![-A-Za-z0-9_])'
    '(?!(?:[^"\\\\]|\\\\.)*--(?:all|static))'
)


def regex(pattern: str, absent: bool = False, trace: bool = False) -> str:
    target = "target: trace\n" if trace else ""
    match = "match: not_contains\n" if absent else ""
    return f"---\ntype: regex\npattern: '{pattern}'\n{target}{match}---\n"


def build() -> None:
    """Write the test-first project, plan and case."""
    write_files(FIXTURES / "tdd-project", PROJECT)
    write_files(FIXTURES / "tdd-run", RECORDS)
    write_case(
        "builder-runs-only-its-tests", "tdd", PROMPT,
        SCAFFOLD.format(generated=GENERATED, run=RUN),
        {"dispatched": dispatched("builder"),
         # Escaped quotes, such as a test's strings in a here-document,
         # are skipped over.
         "used-test-one": regex(
             '"command": ?"(?:[^"\\\\]|\\\\.)*scripts/test-one',
             trace=True),
         "no-bare-check": regex(BARE_CHECK, absent=True, trace=True),
         "on-branch": regex("BRANCH vibe/durations"),
         "committed": regex("COMMITS [1-9]"),
         "tree-clean": regex("TREE CLEAN"),
         "tests-pass": regex("TESTS PASS"),
         "red-first": llm(
             "the builder's report shows, for each of its two entries, a "
             "failing test line, such as a unittest FAIL or ERROR line or "
             "an AttributeError or ImportError, from a run before the code "
             "for that entry was written, and says the entries were "
             "committed")})
