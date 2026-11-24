"""The rounds evals: questions asked in rounds, each holding only those
whose prerequisites are answered.

The designer case gives vibes:designer a task whose choices depend on each
other, an export the finance team opens in a spreadsheet, kept for a while
afterwards, and checks some of its open questions wait on others.

The round case gives the main agent the vibe skill and a spec whose open
questions wait on each other, and checks round one researches only the
fact nothing waits on, and asks only the decisions that wait on nothing.

The grill case has the main agent follow /vibes:grill's first two steps
on a plan to add a currency column to the sales CSV, in the project whose
decision record makes the CSV's columns a public format. It checks the
tree cites the record, marks what waits on what, and that nothing outside
.vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path

from pr_cases import GENERATED, write_case
from research_cases import TOOLS, TREE_CLEAN, dispatched, llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/rounds-eval"

SPEC = """# Spec: refunds export

## Summary

A `reports refunds <day>` command writes the day's refunds to a file.

## Requirements

- **R1:** it fetches the day's refunds from the shop's refunds API.

## Open questions

- **Q1 (fact):** How many refunds does the shop's refunds API return per
  page?
- **Q2 (decision):** Write the export as CSV? Recommended: yes, since the
  finance team opens it in a spreadsheet. Otherwise: JSON lines.
- **Q3 (decision, after Q2):** Separate the CSV's fields with commas?
  Recommended: yes. Otherwise: semicolons.
- **Q4 (decision):** Keep each day's export after the next is written?
  Recommended: yes, in `exports/`. Otherwise: overwrite it.
- **Q5 (decision, after Q4):** Delete kept exports after 90 days?
  Recommended: yes. Otherwise: keep them for ever.
- **Q6 (decision, after Q1):** Fetch the pages one at a time? Recommended:
  yes, if a day fits in a few pages. Otherwise: several at once.
"""

DESIGNER_SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project, committed, with a run directory, as the workflow
# leaves them before it spawns the designer.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
git init -q -b main .
cp -R "${{fixtures}}/research-project/." .
mkdir -p .vibes {run}/draft
printf '*\\n' > .vibes/.gitignore
git add -A
git -c user.name=evals -c user.email=evals@example.invalid \\
  commit -q -m "Fetch the day's sales"
cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
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
Task: Add a command that exports the day's refunds to a file for the
  finance team, who open it in a spreadsheet. Their lead also said it
  would help to keep the old exports around for a while.
Spec directory: <cwd>/{run}/draft/
Guides: languages/Python
Glossary: <cwd>/{run}/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/{run}/tree-check`,
then read `<cwd>/{run}/draft/spec.md`.

Reply with only the line `tree-check` printed, then the spec's Open
questions and Assumptions sections, complete and unchanged, and nothing
else.
"""

ROUND_SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The vibe skill, and a spec whose open questions wait on each other.

set -euo pipefail
here="$(cd "$(dirname -- "$0")" && pwd)"
cp "${{here}}/../../skills/vibe/SKILL.md" .
cp "${{here}}/../fixtures/rounds-spec/spec.md" .
"""

ROUND_PROMPT = """---
max_turns: 8
timeout_seconds: 300
runs: 3
allowed_tools: [Read, Glob, Grep]
---

`SKILL.md` in your working directory is the vibes workflow skill. You're
its main agent in Phase 1, step 2, about to resolve the open questions in
`spec.md`, in an attended run. Following the skill's Open questions
section, decide what round one does. Don't spawn anything or ask anything.

Reply with two lines and nothing else: `RESEARCH:` and the numbers of the
facts you'd have researched now, then `ASK:` and the numbers of the
decisions you'd ask the user now, each list in order, separated by ", ",
or `none`.
"""

GRILL_SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project with its sales CSV command and its decision record,
# committed, and the grill skill where its CLAUDE_PLUGIN_ROOT paths find
# it.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
git init -q -b main .
cp -R "${{fixtures}}/research-project/." .
cp -R "${{fixtures}}/prbody-branch/." .
mkdir -p .vibes skills/grill skills/vibe/templates {run}
printf '*\\n' > .vibes/.gitignore
git add -A
git -c user.name=evals -c user.email=evals@example.invalid \\
  commit -q -m "Add the sales CSV command"
cp -R "${{here}}/../../skills/grill/." skills/grill/
cp "${{here}}/../../skills/vibe/templates/spec.md" \\
  "${{here}}/../../skills/vibe/templates/adr.md" skills/vibe/templates/
cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

GRILL_PROMPT = """---
max_turns: 40
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Write, Edit, "Bash(mkdir *)", "Bash(ls *)", "Bash(*/tree-check)"]
---

`skills/grill/SKILL.md` in your working directory is a skill. The user ran
it as `/vibes:grill add a currency column to the daily sales CSV, now we
sell in euros too`. Follow only its steps 1 and 2, with your working
directory standing for `${{CLAUDE_PLUGIN_ROOT}}` and the slug
`currency-column`. Ask the user nothing, and spawn nothing.

Then run `<cwd>/{run}/tree-check`, with `<cwd>` your working directory.

Reply with only the line `tree-check` printed, then the contents of
`.vibes/grill-currency-column/decisions.md`, complete and unchanged, and
nothing else.
"""


def build() -> None:
    """Write the rounds' fixtures and cases."""
    write_files(FIXTURES / "rounds-spec", {"spec.md": SPEC})
    write_case(
        "designer-marks-what-questions-wait-on", "rounds",
        DESIGNER_PROMPT.format(run=RUN, tools=TOOLS),
        DESIGNER_SCAFFOLD.format(generated=GENERATED, run=RUN),
        {"dispatched": dispatched("designer"),
         "tree-clean": TREE_CLEAN,
         "marks-a-wait": "---\ntype: regex\n"
                         "pattern: '\\((fact|decision), after Q\\d+'\n---\n",
         "waits-for-a-reason": llm(
             "at least one open question is marked as asked after another "
             "because the other's answer decides whether it arises or what "
             "its options are, such as a CSV detail after the file format, "
             "or how long to keep old exports after whether to keep them")})
    write_case(
        "main-agent-asks-the-first-round", "rounds", ROUND_PROMPT,
        ROUND_SCAFFOLD.format(generated=GENERATED),
        {"researches-q1": "---\ntype: regex\npattern: '^RESEARCH: Q?1$'\n"
                          "flags: m\n---\n",
         "asks-q2-q4": "---\ntype: regex\n"
                       "pattern: '^ASK: Q?2, Q?4$'\nflags: m\n---\n"})
    write_case(
        "grill-maps-the-tree", "rounds",
        GRILL_PROMPT.format(run=RUN),
        GRILL_SCAFFOLD.format(generated=GENERATED, run=RUN),
        {"tree-clean": TREE_CLEAN,
         "marks-a-wait": "---\ntype: regex\n"
                         "pattern: '\\((fact|decision), after Q\\d+'\n---\n",
         "cites-the-record": "---\ntype: regex\n"
                             "pattern: '0001'\n---\n",
         "record-shapes-the-tree": llm(
             "the document treats the decision record that makes the CSV's "
             "columns a public format as settling or shaping the plan: "
             "for example, it says the existing file's columns can't "
             "simply gain a column, and asks whether to write a new "
             "format or file instead, rather than asking where in the "
             "existing columns to put the currency"),
         "nothing-asked-of-the-code": llm(
             "nothing in Open questions asks the user something the "
             "project's code or records already answer, such as what the "
             "CSV's columns are today")})
