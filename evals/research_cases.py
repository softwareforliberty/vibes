"""The research evals: fixtures and cases for vibes:researcher and the
designer's open questions.

The researcher case asks for the default request timeout of tinyhttp, an
HTTP library the project vendors at 2.3.0. Its README still says 30
seconds, but its code and changelog say 10, so the case checks the answer
comes from the code at the pinned version, cites it, and says the README
is out of date.

The designer case asks for a spec that needs a fact the project can't
settle, the page size of an outside payments API, and a choice only the
user can make, the export's file format. It checks the fact is marked
(fact), not asked, and the choice is a (decision) with a recommended
answer. Both check nothing outside .vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/research-eval"

PROJECT: Dict[str, str] = {
    "requirements.txt": "tinyhttp==2.3.0  # vendored in vendor/tinyhttp\n",
    "README.md": """# reports

Fetches sales figures from the shop's HTTP API and writes a daily report.
`vendor/tinyhttp` is the HTTP client, vendored at the version
requirements.txt pins.
""",
    "reports/__init__.py": "",
    "reports/fetch.py": '''"""Fetches the day's sales from the shop."""

from vendor.tinyhttp import client


def daily_sales(base_url: str, day: str) -> dict:
    """The day's sales, as the shop's API returns them."""
    return client.get_json(f"{base_url}/sales/{day}")
''',
    "vendor/__init__.py": "",
    "vendor/tinyhttp/__init__.py": '__version__ = "2.3.0"\n',
    "vendor/tinyhttp/README.md": """# tinyhttp

A tiny HTTP client.

    from tinyhttp import client
    client.get_json(url)

Requests time out after 30 seconds by default; pass `timeout=` to change
it.
""",
    "vendor/tinyhttp/CHANGELOG.md": """# Changelog

## 2.3.0

- The default timeout is now 10 seconds, down from 30, so a hung server
  fails fast.

## 2.2.0

- Add `get_json`.
""",
    "vendor/tinyhttp/client.py": '''"""tinyhttp's client: GET a URL and decode the JSON it returns."""

import json
import urllib.request

# Seconds before a request gives up, unless the caller passes timeout=.
DEFAULT_TIMEOUT = 10


def get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """GET the URL and decode its JSON body."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())
''',
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project, committed, with a run directory, as the workflow
# leaves them before it spawns the agent.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
git init -q -b main .
cp -R "${{fixtures}}/research-project/." .
mkdir -p .vibes {run}/research {run}/draft
printf '*\\n' > .vibes/.gitignore
git add -A
git -c user.name=evals -c user.email=evals@example.invalid \\
  commit -q -m "Fetch the day's sales"
cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

TOOLS = ('[Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", '
         '"Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", '
         '"Bash(head *)", "Bash(sed -n *)", "Bash(pip show *)"]')

RESEARCHER_PROMPT = """---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: {tools}
---

Run the `vibes:researcher` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Question: What is tinyhttp's default request timeout, at the version this
  project uses?
Why: the spec for a --timeout option must say what happens without it.
Project: Python. Dependency versions are pinned in requirements.txt, and
  tinyhttp is vendored in vendor/tinyhttp.
Date: 2026-11-24
Note: <cwd>/{run}/research/tinyhttp-timeout.md
```

Don't do its work yourself. When it's done, run `<cwd>/{run}/tree-check`,
then read the note.

Reply with the agent's reply, then the line `tree-check` printed, then the
note's contents, complete and unchanged, and nothing else.
"""

DESIGNER_PROMPT = """---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: {tools}
---

Run the `vibes:designer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: spec
Task: Add a command that exports the day's refunds to a file. The refunds
  come from Acme Payments' public refunds API, which the project doesn't
  use yet; it pages its results, so the command must fetch every page.
Spec directory: <cwd>/{run}/draft/
Guides: languages/Python
Glossary: <cwd>/{run}/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/{run}/tree-check`,
then read `<cwd>/{run}/draft/spec.md`.

Reply with only the line `tree-check` printed, then the spec's Open
questions and Assumptions sections, complete and unchanged, and nothing
else: not the agent's reply.
"""


def llm(criterion: str) -> str:
    return f"---\ntype: llm\n---\n\nPASS if {criterion}.\nFAIL otherwise.\n"


def dispatched(agent: str) -> str:
    return (f"---\ntype: regex\npattern: 'subagent_type\\W+vibes:{agent}'\n"
            "target: trace\n---\n")


TREE_CLEAN = "---\ntype: regex\npattern: '^TREE CLEAN$'\nflags: m\n---\n"


def build() -> None:
    """Write the research fixture and cases."""
    write_files(FIXTURES / "research-project", PROJECT)
    scaffold = SCAFFOLD.format(generated=GENERATED, run=RUN)
    write_case(
        "researcher-trusts-the-code", "research",
        RESEARCHER_PROMPT.format(run=RUN, tools=TOOLS), scaffold,
        {"dispatched": dispatched("researcher"),
         "tree-clean": TREE_CLEAN,
         "checked-version": "---\ntype: regex\n"
                            "pattern: 'Checked:[^\\n]*2\\.3\\.0'\n---\n",
         "answers-ten": llm(
             "the note's answer is that the default timeout is 10 seconds "
             "at 2.3.0, never 30"),
         "cites-the-code": llm(
             "a finding cites vendor/tinyhttp/client.py, where "
             "DEFAULT_TIMEOUT is 10, as its source"),
         "flags-the-readme": llm(
             "the note says the vendored README's 30 seconds is out of "
             "date or conflicts with the code, rather than repeating it "
             "as the answer")})
    write_case(
        "designer-researches-facts-asks-decisions", "research",
        DESIGNER_PROMPT.format(run=RUN, tools=TOOLS), scaffold,
        {"dispatched": dispatched("designer"),
         "tree-clean": TREE_CLEAN,
         # A paging question marked (fact), not asked as a decision.
         "marks-the-fact": "---\ntype: regex\n"
                           "pattern: '\\(fact\\)[^\\n]*(\\n[^\\n-][^\\n]*)*"
                           "pag(e|ing|inat)'\nflags: i\n---\n",
         # A decision whose recommended answer "yes" accepts.
         "recommends-a-decision": "---\ntype: regex\n"
                                  "pattern: '\\(decision\\)[\\s\\S]{0,400}?"
                                  "Recommended: yes'\nflags: i\n---\n",
         "no-guessed-fact": llm(
             "the Assumptions section states nothing about how Acme "
             "Payments' API behaves, such as its paging, page size, rate "
             "limits, authentication or fields, as if it were settled. "
             "Assumptions about the project's own code, such as the "
             "vendored client's timeout, or about the command itself, "
             "don't count")})
