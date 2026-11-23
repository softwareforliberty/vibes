"""The pull request body eval: a finished vibe run for vibes:pr-writer.

The project is reports, the research evals' fixture, on a branch,
vibe/sales-csv, that adds a command writing the day's sales as a CSV with
a total per product. The run left its records: a builder's report with the
line each new test failed on, the last review round's verdicts with the
spec reviewer's coverage, and a decision record that makes the CSV's
columns a public format. The project has no scripts/audit, so no audit
ran, and nothing shows the command run by hand.

The case gives the writer the pull request's directory as /vibes:pr
leaves it, and checks the body quotes the run's evidence, calls the
column format a one-way door, claims no audit or manual check, names no
.vibes/ path, and that nothing outside .vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from research_cases import TREE_CLEAN, dispatched, llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/sales-csv"
PR = ".vibes/pr-vibe-sales-csv"
TOOLS = ".vibes/prbody-eval"

SPEC_DIR = "docs/specs/sales-csv"

# The branch's files, added on top of the research project in three
# commits.
BRANCH: Dict[str, str] = {
    f"{SPEC_DIR}/spec.md": """# Spec: daily sales CSV

## Summary

A `reports csv <day>` command writes the day's sales to `sales-<day>.csv`,
one row per product with its total.

## Requirements

- **R1:** `reports csv <day>` fetches the day's sales with
  `reports.fetch.daily_sales`.
- **R2:** it writes one row per product: the SKU, the number sold and the
  total in pence, sorted by SKU.
- **R3:** the file is `sales-<day>.csv` in the current directory, with the
  header row `sku,quantity,total_pence`.
- **R4:** a day with no sales writes the header row alone.
- **R5:** a day that isn't `YYYY-MM-DD` exits with status 2 and a message
  naming the expected form, and writes nothing.
""",
    f"{SPEC_DIR}/design.md": """# Design: daily sales CSV

## Components

### Totals: `reports.totals`

- **Job:** sums the day's sales per SKU, sorted by SKU (R2, R4).
- **Entry points:** `product_totals`, `ProductTotal`.

### CSV output: `reports.csv_output`

- **Job:** writes the header and one row per total (R2, R3, R4).
- **Entry points:** `write_totals`.

### Command: `reports.cli`

- **Job:** parses `csv <day>`, validates the day, and wires the rest (R1,
  R3, R5).
- **Entry points:** `main`.

## Boundary rules

- `reports.totals` never imports `reports.cli` or `reports.csv_output`.
- Outside each component, code and the component's tests use only its
  entry points.
""",
    "docs/adr/0001-csv-columns-are-a-public-format.md": """# 1. The CSV's columns are a public format

Date: 2026-11-20

## Context

The finance team's spreadsheets import `sales-<day>.csv` by column name.

## Decision

The columns `sku,quantity,total_pence` and their order are a public
format. Changing them needs a new file name, not an edit.

## Consequences

The finance team's imports keep working; a new column means a new format.
""",
    "reports/totals.py": '''"""Totals the day's sales per product."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductTotal:
    sku: str
    quantity: int
    total_pence: int


def product_totals(sales: Iterable[dict]) -> list[ProductTotal]:
    """One total per SKU, sorted by SKU."""
    sums: dict[str, tuple[int, int]] = {}
    for sale in sales:
        quantity, pence = sums.get(sale["sku"], (0, 0))
        sums[sale["sku"]] = (quantity + sale["quantity"],
                             pence + sale["total_pence"])
    return [ProductTotal(sku, q, p) for sku, (q, p) in sorted(sums.items())]
''',
    "reports/csv_output.py": '''"""Writes product totals as CSV."""

import csv
from collections.abc import Iterable
from typing import TextIO

from reports.totals import ProductTotal

HEADER = ("sku", "quantity", "total_pence")


def write_totals(totals: Iterable[ProductTotal], stream: TextIO) -> None:
    """The header, then one row per total, in the order given."""
    writer = csv.writer(stream)
    writer.writerow(HEADER)
    for total in totals:
        writer.writerow((total.sku, total.quantity, total.total_pence))
''',
    "reports/cli.py": '''"""The reports command line."""

import re
import sys

from reports.csv_output import write_totals
from reports.fetch import daily_sales
from reports.totals import product_totals

BASE_URL = "https://shop.example.invalid/api"
DAY = re.compile(r"\\d{4}-\\d{2}-\\d{2}")


def main(argv: list[str]) -> int:
    """Run `csv <day>`."""
    if len(argv) != 2 or argv[0] != "csv" or not DAY.fullmatch(argv[1]):
        print("usage: reports csv YYYY-MM-DD", file=sys.stderr)
        return 2
    day = argv[1]
    sales = daily_sales(BASE_URL, day)["sales"]
    with open(f"sales-{day}.csv", "w", newline="", encoding="utf-8") as out:
        write_totals(product_totals(sales), out)
    return 0
''',
    "tests/__init__.py": "",
    "tests/test_totals.py": '''# Covers: sales-csv R2, R4
from reports.totals import ProductTotal, product_totals


def test_sums_each_sku_and_sorts_by_sku() -> None:
    sales = [{"sku": "B", "quantity": 1, "total_pence": 250},
             {"sku": "A", "quantity": 2, "total_pence": 400},
             {"sku": "B", "quantity": 3, "total_pence": 750}]
    assert product_totals(sales) == [ProductTotal("A", 2, 400),
                                     ProductTotal("B", 4, 1000)]


def test_no_sales_gives_no_totals() -> None:
    assert product_totals([]) == []
''',
    "tests/test_cli.py": '''# Covers: sales-csv R1, R3, R5
from reports import cli


def test_rejects_a_malformed_day(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["csv", "24-11-2026"]) == 2
    assert "YYYY-MM-DD" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_writes_the_days_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "daily_sales", lambda url, day: {"sales": [
        {"sku": "A", "quantity": 2, "total_pence": 400}]})
    assert cli.main(["csv", "2026-11-24"]) == 0
    assert (tmp_path / "sales-2026-11-24.csv").read_bytes() == (
        b"sku,quantity,total_pence\\r\\nA,2,400\\r\\n")
''',
}

# The run's records, in .vibes/sales-csv/.
RECORDS: Dict[str, str] = {
    "state.md": f"""# State: sales-csv

- task: Add a command that writes the day's sales as a CSV, with a total
  per product.
- size: medium
- unattended: no
- base branch: main
- spec directory: {SPEC_DIR}
- decision records: docs/adr
- guides: languages/Python

## Done

- Phase 1: spec approved, committed.
- Phase 2: design approved; docs/adr/0001 written, committed.
- Phase 6: build-1.md.
- Phase 7: review/rebuild-round-2: every reviewer approved.
- Audit: none; the project has no scripts/audit.

status: done
""",
    "build-1.md": """# Build: batch 1

## Entries

- **R2, R4 totals:** red run:
  `FAILED tests/test_totals.py::test_sums_each_sku_and_sorts_by_sku - ModuleNotFoundError: No module named 'reports.totals'`
- **R5 bad day:** red run:
  `FAILED tests/test_cli.py::test_rejects_a_malformed_day - ModuleNotFoundError: No module named 'reports.cli'`
- **R1, R3 file:** red run:
  `FAILED tests/test_cli.py::test_writes_the_days_file - AttributeError: module 'reports.cli' has no attribute 'main'`

## Rules proved

- `reports.totals` never imports the edges: an import of
  `reports.csv_output` in `reports/totals.py` failed with
  `reports.totals is not allowed to import reports.csv_output`.

## Slow tests

`scripts/check --all` passed at the last commit.
""",
    "review/rebuild-round-2/spec-reviewer.md": """# Spec review: round 2

## Coverage

- R1: met, tests/test_cli.py::test_writes_the_days_file
- R2: met, tests/test_totals.py::test_sums_each_sku_and_sorts_by_sku
- R3: met, tests/test_cli.py::test_writes_the_days_file
- R4: met, tests/test_totals.py::test_no_sales_gives_no_totals
- R5: met, tests/test_cli.py::test_rejects_a_malformed_day

## Findings

None.

VERDICT: APPROVED
""",
    "review/rebuild-round-2/architecture-reviewer.md":
        "# Architecture review: round 2\n\nNone.\n\nVERDICT: APPROVED\n",
    "review/rebuild-round-2/test-reviewer.md":
        "# Test review: round 2\n\nNone.\n\nVERDICT: APPROVED\n",
    "review/rebuild-round-2/bug-reviewer.md":
        "# Bug review: round 2\n\nNone.\n\nVERDICT: APPROVED\n",
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project on main, the vibe/sales-csv branch with the run's
# commits, the run's records, and the pull request's directory as
# /vibes:pr leaves it before it spawns the writer.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
commit() {{
  git -c user.name=evals -c user.email=evals@example.invalid \\
    commit -q -m "$1"
}}
git init -q -b main .
cp -R "${{fixtures}}/research-project/." .
mkdir -p .vibes
printf '*\\n' > .vibes/.gitignore
git add -A
commit "Fetch the day's sales"
git checkout -q -b vibe/sales-csv
branch="${{fixtures}}/prbody-branch"
mkdir -p {spec_dir} docs/adr tests
cp "${{branch}}/{spec_dir}/spec.md" "${{branch}}/{spec_dir}/design.md" {spec_dir}/
cp "${{branch}}/docs/adr/"*.md docs/adr/
git add -A
commit "Add the spec and design for the sales CSV"
cp "${{branch}}/reports/totals.py" reports/
cp "${{branch}}/tests/__init__.py" "${{branch}}/tests/test_totals.py" tests/
git add -A
commit "Total the day's sales per product"
cp "${{branch}}/reports/csv_output.py" "${{branch}}/reports/cli.py" reports/
cp "${{branch}}/tests/test_cli.py" tests/
git add -A
commit "Add the csv command"
mkdir -p {run} {pr} {tools}
cp -R "${{fixtures}}/prbody-run/." {run}/
git log --reverse --format='%h %s%n%n%b' main..HEAD > {pr}/commits.txt
git diff --stat main...HEAD > {pr}/diff-stat.txt
git diff main...HEAD > {pr}/diff.patch
printf 'exit 0 at %s\\n' "$(git rev-parse --short HEAD)" > {pr}/check.txt
cp "${{fixtures}}/retro-tools/tree-check" {tools}/
chmod +x {tools}/tree-check
{tools}/tree-check >/dev/null
mv {tools}/tree-now {tools}/tree-before
"""

PROMPT = """---
max_turns: 40
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:pr-writer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Branch: vibe/sales-csv
Base branch: main
Pull request directory: <cwd>/{pr}/, holding commits.txt, diff-stat.txt,
  diff.patch and check.txt; no hotspots.txt, as the history is too short
Run directory: <cwd>/{run}/, a vibe run
Template: none
Body: <cwd>/{pr}/pr.md
Sources: <cwd>/{pr}/sources.md
```

Don't do its work yourself. When it's done, run `<cwd>/{tools}/tree-check`,
then read `<cwd>/{pr}/pr.md`.

Reply with only the line `tree-check` printed, then the contents of
`pr.md`, complete and unchanged, and nothing else.
"""


def build() -> None:
    """Write the pull request body's fixtures and case."""
    write_files(FIXTURES / "prbody-branch", BRANCH)
    write_files(FIXTURES / "prbody-run", RECORDS)
    write_case(
        "pr-writer-cites-the-run", "pr-body",
        PROMPT.format(pr=PR, run=RUN, tools=TOOLS),
        SCAFFOLD.format(generated=GENERATED, run=RUN, pr=PR, tools=TOOLS,
                        spec_dir=SPEC_DIR),
        {"dispatched": dispatched("pr-writer"),
         "tree-clean": TREE_CLEAN,
         "sections": "---\ntype: regex\n"
                     "pattern: '## Summary[\\s\\S]*## Evidence[\\s\\S]*"
                     "## Merge risk'\n---\n",
         "no-run-paths": "---\ntype: regex\npattern: '\\.vibes/'\n"
                         "match: not_contains\n---\n",
         "quotes-a-red-run": "---\ntype: regex\n"
                             "pattern: 'FAILED tests/test_(totals|cli)\\.py'"
                             "\n---\n",
         "one-way-format": llm(
             "the merge risk calls the change a one-way door because of "
             "the CSV's columns being a public format that the finance "
             "team's spreadsheets read, or the decision record "
             "docs/adr/0001-csv-columns-are-a-public-format.md"),
         "invents-nothing": llm(
             "the body never claims that an audit, a security review or "
             "scan, a dependency check, or a manual run of the command "
             "took place or passed. Saying one of these wasn't done or "
             "isn't verified is fine"),
         "coverage": llm(
             "the evidence says every requirement, R1 to R5, is met with "
             "a test covering it, or lists them with their tests")})
