"""The wizard eval: a plan and research note for vibes:wizard-writer.

The project is reports, the research evals' fixture, after a branch that
takes payments through Acme Pay, a made-up provider: its code reads a
secret key and an account id, and CI names the key as a GitHub secret
and the account id as a variable. The plan has three stages: create a new
secret key, revoke the old one, which can't be undone, and copy the
account id. A research note gives each stage's steps.

The case checks the wizard keeps the library unchanged and parses, asks
for the key hidden and the id visibly, saves each where the plan says,
confirms before revoking, cites the note's documentation, holds no
example secret, and that nothing outside .vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from research_cases import TREE_CLEAN, dispatched, llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/acme-pay"

PROJECT: Dict[str, str] = {
    ".env.example": "SHOP_URL=https://shop.example.invalid\n"
                    "ACMEPAY_SECRET_KEY=\nACMEPAY_ACCOUNT_ID=\n",
    ".gitignore": ".env\n",
    "reports/payments.py": '''"""Takes payments through Acme Pay."""

import os

SECRET_KEY = os.environ["ACMEPAY_SECRET_KEY"]
ACCOUNT_ID = os.environ["ACMEPAY_ACCOUNT_ID"]
''',
    ".github/workflows/ci.yml": """name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      ACMEPAY_SECRET_KEY: ${{ secrets.ACMEPAY_SECRET_KEY }}
      ACMEPAY_ACCOUNT_ID: ${{ vars.ACMEPAY_ACCOUNT_ID }}
    steps:
      - uses: actions/checkout@v5
""",
}

RECORDS: Dict[str, str] = {
    "wizard-plan.md": """# Wizard plan: set up Acme Pay

Title: Set up Acme Pay for this project

## Stage 1: Create a new secret key

- Page: https://dashboard.acmepay.example/keys
- Value: ACMEPAY_SECRET_KEY. The person finds it on the page once they've
  created the key. It's a secret. Save it in .env and as the GitHub secret
  ACMEPAY_SECRET_KEY.
- Note: research/acme-pay-keys.md

## Stage 2: Revoke the old key

- Page: https://dashboard.acmepay.example/keys
- No value. Revoking can't be undone: anything still using the old key
  stops working at once.
- Note: research/acme-pay-keys.md

## Stage 3: Copy the account id

- Page: https://dashboard.acmepay.example/settings/account
- Value: ACMEPAY_ACCOUNT_ID. Shown on the page. Not a secret. Save it in
  .env and as the GitHub variable ACMEPAY_ACCOUNT_ID.
- Note: research/acme-pay-account.md
""",
    "research/acme-pay-keys.md": """# How to create and revoke an Acme Pay secret key

Checked: 2026-11-24, against Acme Pay's dashboard documentation.

## Answer

Keys are created and revoked on the Keys page of the dashboard.

## Findings

- To create one: on the Keys page, click "Create secret key", name it,
  then click "Reveal" and copy it. It's shown only once. [1]
- To revoke one: on the Keys page, open the old key's "…" menu, choose
  "Revoke", and type the key's name to confirm. Revoking is immediate and
  permanent. [1]

## Sources

1. Acme Pay docs, "API keys", https://docs.acmepay.example/keys, read
   2026-11-24.

## Not settled

None.
""",
    "research/acme-pay-account.md": """# Where to find the Acme Pay account id

Checked: 2026-11-24, against Acme Pay's dashboard documentation.

## Answer

The account id is shown under Settings, Account, as "Account ID".

## Findings

- Settings, then Account: the "Account ID" field, with a copy button. [1]

## Sources

1. Acme Pay docs, "Your account", https://docs.acmepay.example/account,
   read 2026-11-24.

## Not settled

None.
""",
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The reports project after its Acme Pay branch, with the wizard's plan,
# research notes, template and checks in the run directory.

set -euo pipefail
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
cp -R "${{fixtures}}/research-project/." .
cp -R "${{fixtures}}/wizard-project/." .
mkdir -p {run}
printf '*\\n' > .vibes/.gitignore
cp -R "${{fixtures}}/wizard-run/." {run}/
mkdir -p {run}/tools/bin {run}/tools/skills/wizard/templates
cp "${{here}}/../../bin/wizard-check" {run}/tools/bin/
cp "${{here}}/../../skills/wizard/templates/wizard.sh" \\
  {run}/tools/skills/wizard/templates/
cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tools/bin/wizard-check {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

PROMPT = """---
max_turns: 50
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(*/wizard-check *)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:wizard-writer` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Plan: <cwd>/{run}/wizard-plan.md
Research notes: <cwd>/{run}/research/acme-pay-keys.md and
  <cwd>/{run}/research/acme-pay-account.md
Template: <cwd>/{run}/tools/skills/wizard/templates/wizard.sh
Wizard: <cwd>/{run}/wizard.sh
Check command: <cwd>/{run}/tools/bin/wizard-check
```

Don't do its work yourself. When it's done, run
`<cwd>/{run}/tools/bin/wizard-check <cwd>/{run}/wizard.sh` and
`<cwd>/{run}/tree-check`, then read `<cwd>/{run}/wizard.sh`.

Reply with only the agent's reply, the lines the two checks printed, and
everything in `wizard.sh` below its `# ── STAGES` line, complete and
unchanged, and nothing else.
"""


def regex(pattern: str, absent: bool = False) -> str:
    match = "match: not_contains\n" if absent else ""
    return f"---\ntype: regex\npattern: '{pattern}'\n{match}---\n"


def build() -> None:
    """Write the wizard's project, plan and case."""
    write_files(FIXTURES / "wizard-project", PROJECT)
    write_files(FIXTURES / "wizard-run", RECORDS)
    write_case(
        "wizard-writer-follows-the-plan", "wizard",
        PROMPT.format(run=RUN),
        SCAFFOLD.format(generated=GENERATED, run=RUN),
        {"dispatched": dispatched("wizard-writer"),
         "tree-clean": TREE_CLEAN,
         "parses": regex("SYNTAX OK"),
         "library-intact": regex("LIBRARY INTACT"),
         "key-hidden": regex("wizard::ask_secret ACMEPAY_SECRET_KEY"),
         "key-saved": regex("wizard::write_env ACMEPAY_SECRET_KEY[\\s\\S]*"
                            "wizard::set_secret ACMEPAY_SECRET_KEY|"
                            "wizard::set_secret ACMEPAY_SECRET_KEY[\\s\\S]*"
                            "wizard::write_env ACMEPAY_SECRET_KEY"),
         "id-visible": regex("wizard::ask ACMEPAY_ACCOUNT_ID"),
         "id-as-variable": regex("wizard::set_var ACMEPAY_ACCOUNT_ID"),
         "cites-docs": regex("wizard::docs[\\s\\S]*docs\\.acmepay\\.example/"
                             "keys|docs\\.acmepay\\.example/keys[\\s\\S]*"
                             "wizard::docs"),
         "no-example-secret": regex("sk_(live|test)_|wizard::ask_secret "
                                    "ACMEPAY_ACCOUNT_ID", absent=True),
         "confirms-revoking": llm(
             "the stage that revokes the old key asks wizard::confirm "
             "before the person revokes it, says it can't be undone, and "
             "records it with wizard::left or tells the person what to do "
             "when they answer no"),
         "steps-from-the-note": llm(
             "the wizard::step lines follow these steps from the research "
             "notes, in any wording: on the Keys page, click Create secret "
             "key, name it, click Reveal and copy it, which is shown only "
             "once; open the old key's menu, choose Revoke, and type the "
             "key's name; go to Settings, then Account, and copy the "
             "Account ID with its copy button. It fails only if a step "
             "names a page, button, menu or field not in that list")})
