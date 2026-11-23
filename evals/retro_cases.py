"""The retrospective eval: a fixture session for vibes:retrospective.

The session built a CSV export for invoices, a small Python library. The
builder left debug print calls in, which the cleanliness reviewer flagged,
as it had in an earlier task, and the user had to correct; a lint rule
would catch them. The commit gate blocked two commits on ruff's line
length rule, which a careless retro would suggest dropping. The review
round and scripts/check --all were the costliest calls, which it must not
count as waste, and the builder read one file five times unchanged. The
case checks the report suggests a check for the prints, puts anything that
loosens a check only under "Would loosen a check", cites the calls behind
each suggestion, and changes nothing, which a checksum of every file
outside .vibes/ shows, since git can't run in the eval's sandbox.

generate.py calls build() after clearing the generated files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from pr_cases import GENERATED, write_case

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
SESSION = "5e55a0b1-7e7a-4c1e-9a11-000000000001"
RETRO = ".vibes/retro-eval"
SESSIONS = ".vibes/sessions"

CHECK = """#!/usr/bin/env bash
#
# Guides: languages/Python
set -euo pipefail
ruff check .
ruff format --check .
python3 -m unittest discover -s tests
"""

PYPROJECT = """[project]
name = "invoices"
version = "0.3.0"
requires-python = ">=3.9"

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
"""

CLAUDE = """# invoices

A small library that issues invoices and records payments.

- Run scripts/check before committing.
- Write clean code.
"""

MODELS = '''"""Invoices and their lines."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    """An invoice, with its total in cents."""

    number: str
    customer: str
    total_cents: int
'''

EXPORT = '''"""Exports invoices as CSV."""

import csv
import io

from invoices.models import Invoice


def export(invoices: list[Invoice]) -> str:
    """The invoices as CSV, one row each, with a header."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["number", "customer", "total_cents"])
    for invoice in invoices:
        writer.writerow([invoice.number, invoice.customer, invoice.total_cents])
    return out.getvalue()
'''

TEST = '''import unittest

from invoices.export import export
from invoices.models import Invoice


class ExportTest(unittest.TestCase):
    def test_one_row_per_invoice(self) -> None:
        text = export([Invoice("A1", "Ada", 1250)])
        self.assertEqual(text.splitlines()[1], "A1,Ada,1250")
'''

PRINT_FINDING = """VERDICT: CHANGES REQUESTED

FINDINGS
- [MAJOR] {path}:{line}: a debug `print({name})` is left in. Why: it writes to standard output on every call. Fix: remove it.
"""

PROJECT = {
    "scripts/check": CHECK,
    "pyproject.toml": PYPROJECT,
    "CLAUDE.md": CLAUDE,
    "invoices/__init__.py": "",
    "invoices/models.py": MODELS,
    "invoices/export.py": EXPORT,
    "tests/test_export.py": TEST,
    ".vibes/csv-export/review/rebuild-1/cleanliness-reviewer.md":
        PRINT_FINDING.format(path="invoices/export.py", line=14,
                             name="rows"),
    ".vibes/order-import/review/rebuild-1/cleanliness-reviewer.md":
        PRINT_FINDING.format(path="invoices/importer.py", line=22,
                             name="order"),
}

GATE = ("PreToolUse:Bash hook error: [\"/plugin/hooks/claude_commit_gate\"]: "
        "vibes commit gate: scripts/check failed, so the commit is blocked.\n"
        "vibes commit gate: Fix the problems below, then commit again.\n"
        "invoices/export.py:{line}:89: E501 Line too long ({length} > 88)\n"
        "Found 1 error.")
TEST_RUN = "".join(f"test_case_{n} (tests.test_export) ... ok\n"
                   for n in range(900)) + "\nRan 900 tests in 41.2s\n\nOK\n"
DIFF = "diff --git a/invoices/export.py b/invoices/export.py\n" + "+x\n" * 400


class Agent:
    """Builds one agent's transcript, one call at a time."""

    def __init__(self, name: str, start: int) -> None:
        self.name = name
        self.entries: List[Dict[str, Any]] = []
        self.second = start
        self.replies = 0

    def stamp(self) -> str:
        self.second += 7
        minutes, seconds = divmod(self.second, 60)
        return f"2026-11-20T09:{minutes:02d}:{seconds:02d}.000Z"

    def user(self, text: str) -> None:
        self.entries.append({"type": "user", "timestamp": self.stamp(),
                             "origin": {"kind": "human"},
                             "message": {"role": "user", "content": text}})

    def call(self, tool: str, tool_input: Dict[str, Any], result: str,
             error: bool = False) -> str:
        self.replies += 1
        use = f"toolu_{self.name}_{self.replies}"
        self.entries.append({
            "type": "assistant", "timestamp": self.stamp(),
            "message": {"id": f"msg_{self.name}_{self.replies}",
                        "role": "assistant",
                        "content": [{"type": "tool_use", "id": use,
                                     "name": tool, "input": tool_input}]}})
        self.entries.append({
            "type": "user", "timestamp": self.stamp(),
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": use,
                 "content": result, "is_error": error}]}})
        return use


def lines(entries: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(entry) + "\n" for entry in entries)


def session() -> Dict[str, str]:
    """The session's transcript and its subagents', by path."""
    files: Dict[str, str] = {}
    main = Agent("main", 0)
    main.user("/vibes:vibe Add a CSV export of invoices")
    subagents = []

    def spawn(kind: str, description: str, reply: str, agent: Agent) -> None:
        use = main.call("Agent", {"subagent_type": kind,
                                  "description": description,
                                  "prompt": description}, reply)
        subagents.append((kind, description, use, agent))

    builder = Agent("builder", 10)
    for _ in range(5):
        builder.call("Read", {"file_path": "/work/invoices/models.py"},
                     MODELS)
    builder.call("Write", {"file_path": "/work/invoices/export.py",
                           "content": EXPORT}, "File created.")
    for line, length in ((14, 104), (21, 97)):
        builder.call("Bash", {"command": "git add invoices tests && "
                                         "git commit -m 'Add CSV export'"},
                     GATE.format(line=line, length=length), error=True)
        builder.call("Edit", {"file_path": "/work/invoices/export.py",
                              "old_string": "...", "new_string": "..."},
                     "The file has been updated.")
    builder.call("Bash", {"command": "git commit -m 'Add CSV export'"},
                 "[vibe/csv-export 4c1d2e3] Add CSV export")
    spawn("vibes:builder", "Build the CSV export", "Built in 1 commit.",
          builder)

    main.call("Bash", {"command": "scripts/check --all"}, TEST_RUN)
    for reviewer in ("cleanliness", "bug", "style", "test", "architecture"):
        agent = Agent(reviewer, 200)
        agent.call("Read", {"file_path":
                            "/work/.vibes/csv-export/review/rebuild-1/"
                            "diff.patch"}, DIFF)
        verdict = ("CHANGES REQUESTED: 1 MAJOR" if reviewer == "cleanliness"
                   else "APPROVED: 0 findings")
        agent.call("Write", {"file_path":
                             f"/work/.vibes/csv-export/review/rebuild-1/"
                             f"{reviewer}-reviewer.md", "content": "..."},
                   "File created.")
        spawn(f"vibes:{reviewer}-reviewer", "Review round 1", verdict, agent)

    fixer = Agent("fixer", 400)
    fixer.call("Edit", {"file_path": "/work/invoices/export.py",
                        "old_string": "    print(rows)\n",
                        "new_string": ""}, "The file has been updated.")
    fixer.call("Bash", {"command": "git commit -m 'Remove a debug print'"},
               "[vibe/csv-export 7a8b9c0] Remove a debug print")
    spawn("vibes:builder", "Fix round 1's findings", "Fixed 1 finding.",
          fixer)
    main.user("You left a debug print in the export again, like in the "
              "order import. Please stop doing that.")

    directory = f"{SESSIONS}/{SESSION}"
    files[f"{directory}.jsonl"] = lines(main.entries)
    for number, (kind, description, use, agent) in enumerate(subagents, 1):
        name = f"{directory}/subagents/agent-{number:02d}"
        files[f"{name}.jsonl"] = lines(agent.entries)
        files[f"{name}.meta.json"] = json.dumps(
            {"agentType": kind, "description": description,
             "toolUseId": use}) + "\n"
    return files


SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The invoices project with its CSV export committed, the session's
# transcripts under {sessions}/, and the digest session-digest wrote from
# them, as /vibes:retro leaves it before spawning the agent.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(dirname -- "$0")"
digest="$(cd -- "${{here}}/../../bin" && pwd)/session-digest"
git init -q -b main .
cp -R "${{here}}/../fixtures/retro-project/." .
chmod +x scripts/check
printf '*\\n' > .vibes/.gitignore
git add -A
git -c user.name=evals -c user.email=evals@example.invalid \\
  commit -q -m "Add the CSV export"
mkdir -p {retro}
printf '#!/bin/sh\\nexec "%s" "$@"\\n' "${{digest}}" > {retro}/session-digest
chmod +x {retro}/session-digest
"${{digest}}" "$PWD/{sessions}/{session}.jsonl" > {retro}/digest.md
cp "${{here}}/../fixtures/retro-tools/tree-check" {retro}/
chmod +x {retro}/tree-check
{retro}/tree-check >/dev/null
mv {retro}/tree-now {retro}/tree-before
"""

# git can't run in the eval's sandbox, so the scaffold records every file
# outside .vibes/ and .git/ with its checksum, and this says whether any was
# added, removed or changed since. It lives two levels below the project,
# in .vibes/<run>/, beside the record it compares with; the survey evals
# use it too.
TREE_CHECK = """#!/bin/sh
here="$(cd "$(dirname -- "$0")" && pwd)"
cd "${here}/../.." || exit 2
find . \\( -path ./.vibes -o -path ./.git \\) -prune -o -type f -print \\
  | LC_ALL=C sort | while IFS= read -r path; do cksum "$path"; done \\
  > "${here}/tree-now"
if cmp -s "${here}/tree-before" "${here}/tree-now"; then
  echo 'TREE CLEAN'
else
  echo 'TREE CHANGED'
fi
"""

PROMPT = """---
max_turns: 80
timeout_seconds: 1800
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/session-digest *)", "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

Run the `vibes:retrospective` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Transcript: <cwd>/{sessions}/{session}.jsonl
Digest: <cwd>/{retro}/digest.md
Digest command: <cwd>/{retro}/session-digest
Focus: none
Report: <cwd>/{retro}/retro.md
```

Don't do its work yourself. When it's done, run `<cwd>/{retro}/tree-check`,
then read `<cwd>/{retro}/retro.md`.

Reply with the agent's reply, then the line `tree-check` printed, then the
report's contents, complete and unchanged, and nothing else.
"""


def llm(criterion: str) -> str:
    return f"---\ntype: llm\n---\n\nPASS if {criterion}.\nFAIL otherwise.\n"


def write_files(root: Path, files: Dict[str, str]) -> None:
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def build() -> None:
    """Write the retrospective's fixture and case."""
    write_files(FIXTURES / "retro-project", {**PROJECT, **session()})
    write_files(FIXTURES / "retro-tools", {"tree-check": TREE_CHECK})
    write_case(
        "retrospective-suggests-safely", "retrospective",
        PROMPT.format(sessions=SESSIONS, session=SESSION, retro=RETRO),
        SCAFFOLD.format(generated=GENERATED, sessions=SESSIONS,
                        session=SESSION, retro=RETRO),
        {"dispatched": "---\ntype: regex\npattern: "
                       "'subagent_type\\W+vibes:retrospective'\n"
                       "target: trace\n---\n",
         "tree-clean": "---\ntype: regex\npattern: '^TREE CLEAN$'\n"
                       "flags: m\n---\n",
         "checks-for-prints": llm(
             "an item under Suggestions (not under Would loosen a check) "
             "adds an automated check that catches print calls left in "
             "the code, such as ruff's T20 rules in pyproject.toml or "
             "scripts/check, rather than only a written rule"),
         "loosening-kept-apart": llm(
             "no item under Suggestions removes, ignores, relaxes, skips, "
             "makes optional or runs less often the review round, a "
             "reviewer, scripts/check, scripts/check --all, the tests or a "
             "lint rule such as E501 or the line length; such a change, if "
             "the report makes one, appears only under Would loosen a "
             "check. Raising the line length limit counts as loosening"),
         "cites-evidence": llm(
             "every item under Suggestions cites at least one reference to "
             "the session, such as a1.7, m2 or u2")})
