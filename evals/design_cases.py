"""The design evals: a case for vibes:designer in design mode.

The project is reports, the research evals' fixture: a small Python
program that fetches the day's sales from a shop's HTTP API. The spec,
already approved, adds a command that writes the day's sales as a CSV with
a total per product, which needs a core to total the sales and edges for
the file and the command line.

The case checks the design gives each component its entry points, and
writes a boundary rule that keeps callers and tests to them, and that
nothing outside .vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path

from pr_cases import GENERATED, write_case
from research_cases import TOOLS, TREE_CLEAN, dispatched, llm

EVALS = Path(__file__).resolve().parent
RUN = ".vibes/design-eval"

SPEC = """# Spec: daily sales CSV

## Summary

A `reports csv <day>` command writes the day's sales to `sales-<day>.csv`,
one row per product with its total.

## Requirements

- **R1:** `reports csv <day>` fetches the day's sales with
  `reports.fetch.daily_sales`.
- **R2:** it writes one row per product: the product's SKU, the number
  sold and the total in pence, sorted by SKU.
- **R3:** the file is `sales-<day>.csv` in the current directory, with a
  header row `sku,quantity,total_pence`.
- **R4:** a day with no sales writes the header row alone.
- **R5:** a day that isn't `YYYY-MM-DD` exits with status 2 and a message
  naming the expected form, and writes nothing.

## Open questions

None.

## Change log

| Date | Change | Why |
| --- | --- | --- |
"""

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project, committed, with the approved spec in the run
# directory, as the workflow leaves them before design mode.

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
cat > {run}/draft/spec.md <<'SPEC'
{spec}SPEC
cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

PROMPT = """---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: {tools}
---

Run the `vibes:designer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: design
Task: Add a command that writes the day's sales as a CSV, with a total
  per product. The spec is approved.
Spec directory: <cwd>/{run}/draft/
Guides: languages/Python
Glossary: <cwd>/{run}/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/{run}/tree-check`,
then read `<cwd>/{run}/draft/design.md`.

Reply with only the line `tree-check` printed, then the design's
Components and Boundary rules sections, complete and unchanged, and
nothing else: not the agent's reply.
"""


def build() -> None:
    """Write the design case."""
    write_case(
        "designer-names-entry-points", "design",
        PROMPT.format(run=RUN, tools=TOOLS),
        SCAFFOLD.format(generated=GENERATED, run=RUN, spec=SPEC),
        {"dispatched": dispatched("designer"),
         "tree-clean": TREE_CLEAN,
         "has-entry-points": "---\ntype: regex\n"
                             "pattern: 'Entry points:\\**[ \\t]*\\S'\n---\n",
         "every-component": llm(
             "every component in the Components section names its entry "
             "points as specific Python modules or packages of the project, "
             "such as `reports/totals.py` or the `reports.export` package, "
             "not left blank or described only in general words"),
         "rule-keeps-to-them": llm(
             "the Boundary rules section has a rule that code outside a "
             "component, and the component's tests, use only its entry "
             "points")})
