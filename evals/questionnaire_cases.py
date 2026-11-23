"""The questionnaire eval: the questionnaire skill, followed by the eval's
own agent with the user's answers given up front.

The project is warehouse-sync, a small Python program about to export
customer records to a data warehouse each night. Three decisions belong
to the company's data protection officer, not the user: how long exported
records may be kept, whether contact details may go, and whether
customers who opted out of analytics must be left out. The project holds
a token in .env and the export code under warehouse/.

The case checks the questionnaire covers all three needs, one idea per
question, with room to answer, and carries none of the token, the .env
file or the code's paths.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from research_cases import llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
TOKEN = "wh_live_9f3a7c21d4e8b6a0"

PROJECT: Dict[str, str] = {
    "README.md": """# warehouse-sync

Copies the day's customer records from the shop's database to the
analytics warehouse, each night.
""",
    ".env": f"WAREHOUSE_URL=https://warehouse.example.invalid\n"
            f"WAREHOUSE_TOKEN={TOKEN}\n",
    "warehouse/__init__.py": "",
    "warehouse/export.py": '''"""Exports customer records to the warehouse."""

FIELDS = ("id", "name", "email", "phone", "country", "signed_up",
          "analytics_opt_out")


def rows(customers: list[dict]) -> list[tuple]:
    """One row per customer, in FIELDS order."""
    return [tuple(c[f] for f in FIELDS) for c in customers]
''',
    "docs/specs/nightly-export/spec.md": """# Spec: nightly customer export

## Summary

Each night, export every customer record changed that day to the
analytics warehouse, so the analysts can report on sign-ups by country.

## Open questions

1. (decision) How long may exported records stay in the warehouse?
   Recommended: 13 months, enough for a year-on-year report.
2. (decision) May email addresses and phone numbers be exported, and if
   so, masked or as they are? Recommended: leave them out; the reports
   don't use them.
3. (decision) Must customers who opted out of analytics be left out of
   the export? Recommended: yes.
""",
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The warehouse-sync project, and the questionnaire skill with its
# template where the skill's ${{CLAUDE_PLUGIN_ROOT}} paths will find them.

set -euo pipefail
here="$(cd "$(dirname -- "$0")" && pwd)"
cp -R "${{here}}/../fixtures/questionnaire-project/." .
mkdir -p skills/questionnaire .vibes
cp -R "${{here}}/../../skills/questionnaire/." skills/questionnaire/
printf '*\\n' > .vibes/.gitignore
"""

PROMPT = """---
max_turns: 30
timeout_seconds: 600
runs: 3
allowed_tools: [Read, Glob, Grep, Write, Edit, "Bash(ls *)", "Bash(mkdir *)"]
---

`skills/questionnaire/SKILL.md` in your working directory is a skill. The
user ran it as `/vibes:questionnaire the three open questions in
docs/specs/nightly-export/spec.md`. Follow it, with your working directory
standing for `${{CLAUDE_PLUGIN_ROOT}}`.

When it says to ask the user, use these answers, which the user gave up
front, rather than asking:

- **Who it's for:** the company's data protection officer, a colleague in
  another department, who knows the data protection rules and the
  company's retention policy, but not this project.
- **What they need back:** 1. how long exported records may be kept in
  the warehouse; 2. whether email addresses and phone numbers may be
  exported, and if so whether they must be masked; 3. whether customers
  who opted out of analytics must be left out.
- **By when:** 5 December 2026. **From:** the platform team.

Reply with only the questionnaire's contents, complete and unchanged, and
nothing else.
"""


def build() -> None:
    """Write the questionnaire's project and case."""
    write_files(FIXTURES / "questionnaire-project", PROJECT)
    write_case(
        "questionnaire-asks-the-gap", "questionnaire", PROMPT,
        SCAFFOLD.format(generated=GENERATED),
        {"written": "---\ntype: regex\n"
                    "pattern: '\\.vibes/questionnaires/[^\"\\s]+\\.md'\n"
                    "target: trace\n---\n",
         "room-to-answer": "---\ntype: regex\npattern: '^>\\s*$'\n"
                           "flags: m\n---\n",
         "nothing-private": "---\ntype: regex\n"
                            f"pattern: '{TOKEN}|WAREHOUSE_TOKEN|\\.env\\b|"
                            "warehouse/export\\.py|\\.vibes/'\n"
                            "match: not_contains\n---\n",
         "covers-the-needs": llm(
             "the questionnaire has questions that would settle all three: "
             "how long exported records may be kept, whether email "
             "addresses and phone numbers may be exported and whether "
             "masked, and whether customers who opted out of analytics "
             "must be left out"),
         "one-idea-each": llm(
             "each question under a ### heading asks one thing; a "
             "question that bundles two separate decisions, such as "
             "whether contact details may be exported and how long "
             "records are kept, fails. Asking whether contact details may "
             "go and, if so, masked or not, as one question with options, "
             "counts as one idea"),
         "for-an-outsider": llm(
             "the Context section explains what the export is and why "
             "the recipient's knowledge matters, in plain words someone "
             "outside the project would follow")})
