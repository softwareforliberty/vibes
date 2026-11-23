"""The project docs reviewer's and the commit message suggester's evals.

The reviewer cases give it a small invoicing library's spec for a late fee.
In one, the project's architecture notes say money is whole cents and the
spec stores the fee as a float of dollars, a contradiction it must find. In
the other, the project's only documents are about releases and branding,
which a late fee doesn't touch, so it must stop early and say they don't
apply. In the third, the spec charges the fee from a nightly job, which a
decision record rules out, and calls the customer a client, a word the
glossary says to avoid; it must find both. The suggester case stages a
change and checks the subject it suggests fits in 50 characters.

generate.py calls build() after clearing the generated files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from pr_cases import GENERATED, write_case

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
REVIEWER = "project-docs-reviewer"
SPEC_DIR = "docs/specs/late-fees"
REVIEW = ".vibes/late-fees/review/spec-1"
TASK = "Charge a late fee on overdue invoices, as the spec describes."

README = """# invoices

A small library that issues invoices and records payments. See
`docs/` for how it's built and released.
"""

ARCHITECTURE = """# Architecture

## Money

Every amount of money is an `int` number of cents, in every layer: models,
storage and the public API. Never use `float` or `Decimal` for money, and
never store or return dollars. Round only when converting a rate to cents,
half up, to the nearest cent.

## Storage

Only `invoices/repository.py` runs SQL. Services call the repository.
"""

RELEASE = """# Releasing

## Cutting a release

1. Update `CHANGELOG.md`.
2. Tag the commit `v<version>` and push the tag.

## Version numbers

We follow semantic versioning.
"""

BRANDING = """# Branding

## Logo

Use the blue logo on light backgrounds and the white one on dark.

## Colours

Primary `#1d4ed8`, accent `#f59e0b`.
"""

SPEC = """# Late fees

## Summary

Charge a late fee on invoices that are overdue, so customers who pay late
pay for the cost of chasing them.

## Requirements

- **R1:** An invoice is overdue once 30 days have passed since its issue
  date and it isn't fully paid.
- **R2:** The late fee is 1.5% of the invoice's unpaid total, stored on the
  invoice as `late_fee`, a `float` number of dollars rounded to two
  decimal places.
- **R3:** The fee is charged once per invoice, the first time it's found
  overdue.

## Open questions

None.
"""

GLOSSARY = """# Glossary

An invoicing library that issues invoices and records payments.

## Terms

**Customer:**
A person or company that is sent invoices.
_Avoid:_ client, account holder

**Invoice:**
A request for payment for one sale, with a total in cents.
_Avoid:_ bill

**Payment:**
Money a Customer pays against one Invoice.
_Avoid:_ remittance
"""

DECISION = """# 1. Work out overdue state when an invoice is read

The library is embedded in hosts that have no scheduler, so nothing in it
runs on a timer: whether an invoice is overdue, and any charge that follows
from it, is worked out from the dates when the invoice is read.
"""

SCHEDULED_SPEC = """# Late fees

## Summary

Charge a late fee on invoices that are overdue, so clients who pay late
pay for the cost of chasing them.

## Requirements

- **R1:** A job runs every night at 02:00 and marks each invoice overdue
  once 30 days have passed since its issue date and it isn't fully paid.
- **R2:** When the job marks an invoice overdue, it adds a late fee of
  1.5% of the unpaid total, in whole cents rounded half up, to the
  invoice's `late_fee_cents`, and emails the client.
- **R3:** The fee is charged once per invoice.

## Open questions

None.
"""

CODE = """\"\"\"Invoices and their payments.\"\"\"

from dataclasses import dataclass


@dataclass
class Invoice:
    number: str
    total_cents: int
    paid_cents: int = 0
"""


@dataclass(frozen=True)
class Variant:
    """The project's documents, and what the reviewer must say about them."""

    name: str
    docs: Tuple[Tuple[str, str], ...]
    verdict: str
    graders: Dict[str, str]
    spec: str = SPEC


def llm(criterion: str) -> str:
    return f"---\ntype: llm\n---\n\nPASS if {criterion}.\nFAIL otherwise.\n"


VARIANTS = (
    Variant(
        "contradiction",
        (("README.md", README), ("docs/architecture.md", ARCHITECTURE),
         ("docs/release.md", RELEASE)),
        "CHANGES REQUESTED",
        {"finds-contradiction": llm(
            "a BLOCKER or MAJOR finding says R2 in the spec contradicts "
            "docs/architecture.md, because money must be an int number of "
            "cents, not a float of dollars, and asks for the fee in cents")},
    ),
    Variant(
        "not-applicable",
        (("docs/release.md", RELEASE), ("docs/branding.md", BRANDING)),
        "NOT APPLICABLE",
        {"exits-early": "---\ntype: regex\n"
                        "pattern: 'file_path\\W+[^\"]*docs/(release|branding)\\.md'\n"
                        "target: trace\nmatch: not_contains\n---\n"},
    ),
    Variant(
        "glossary-and-decision",
        (("README.md", README), ("GLOSSARY.md", GLOSSARY),
         ("docs/adr/0001-overdue-on-read.md", DECISION),
         ("docs/release.md", RELEASE)),
        "CHANGES REQUESTED",
        {"finds-decision": llm(
            "a BLOCKER or MAJOR finding says the spec's nightly job (R1 or "
            "R2) goes against docs/adr/0001-overdue-on-read.md, because "
            "overdue state and fees must be worked out when the invoice is "
            "read, not on a schedule"),
         "finds-avoided-term": llm(
            "a finding says the spec calls the customer a client, a word "
            "GLOSSARY.md says to avoid, and asks for Customer instead")},
        SCHEDULED_SPEC,
    ),
)

PROMPT = """---
max_turns: 12
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent]
---

Run the `vibes:{reviewer}` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Task: {task}
Spec: <cwd>/{spec_dir}/spec.md
Review directory: <cwd>/{review}
Phase: spec
Guides: languages/Python
Round: 1
Project docs: {docs}
```

Don't review anything yourself. When the agent is done, read the file it
writes its review to:

```text
<cwd>/{review}/{reviewer}.md
```

Reply with the agent's reply, then the file's contents, both complete and
unchanged, and nothing else.
"""

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# Copy this case's project into the run's working directory.

set -euo pipefail

cp -R "$(dirname -- "$0")/../fixtures/docs-{variant}/." .
mkdir -p {review}
"""

SUGGESTER_PROMPT = """---
max_turns: 10
timeout_seconds: 600
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, "Bash(git *)"]
---

Run the `vibes:commit-message-suggester` agent, giving it exactly this
brief, with `<cwd>` replaced by the absolute path of your working
directory:

```text
Repository: <cwd>
Task: charge a late fee on overdue invoices
Commit: the approved spec for late fees, which the rebuild will build to
```

Don't write a message yourself. Reply with the agent's reply, complete and
unchanged, and nothing else.
"""

SUGGESTER_SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# A repository with the late-fees spec staged on top of the library.

set -euo pipefail

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
cp -R "$(dirname -- "$0")/../fixtures/docs-contradiction/." .
git init -q -b main .
git add -A -- . ':!{spec_dir}'
git -c user.name=evals -c user.email=evals@example.invalid \\
  commit -q -m "Add the invoice model"
git add {spec_dir}
"""


def write(root: Path, files: Tuple[Tuple[str, str], ...]) -> None:
    for path, text in files:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")


def build_fixture(variant: Variant) -> None:
    write(FIXTURES / f"docs-{variant.name}",
          variant.docs + ((f"{SPEC_DIR}/spec.md", variant.spec),
                          ("invoices/models.py", CODE)))


def reviewer_case(variant: Variant) -> None:
    docs = ", ".join(path for path, _ in variant.docs)
    graders = {
        "dispatched": "---\ntype: regex\n"
                      f"pattern: 'subagent_type\\W+vibes:{REVIEWER}'\n"
                      "target: trace\n---\n",
        "verdict": f"---\ntype: regex\npattern: 'VERDICT:\\s*{variant.verdict}'\n---\n",
        **variant.graders,
    }
    kind = "precision" if variant.verdict == "NOT APPLICABLE" else "recall"
    write_case(
        f"{REVIEWER}-{'skips' if kind == 'precision' else 'finds'}-{variant.name}",
        f"{kind}, {REVIEWER}",
        PROMPT.format(reviewer=REVIEWER, task=TASK, spec_dir=SPEC_DIR,
                      review=REVIEW, docs=docs),
        SCAFFOLD.format(generated=GENERATED, variant=variant.name,
                        review=REVIEW),
        graders)


def build() -> None:
    """Write every project docs and commit message fixture and case."""
    for variant in VARIANTS:
        build_fixture(variant)
        reviewer_case(variant)
    write_case(
        "commit-message-suggester-fits-subject", "commit-message",
        SUGGESTER_PROMPT,
        SUGGESTER_SCAFFOLD.format(generated=GENERATED, spec_dir=SPEC_DIR),
        {"dispatched": "---\ntype: regex\npattern: "
                       "'subagent_type\\W+vibes:commit-message-suggester'\n"
                       "target: trace\n---\n",
         "short-subject": "---\ntype: regex\n"
                          "pattern: '^[^\\n]{1,50}(\\n|$)'\n---\n",
         "imperative": llm("the message's first line describes adding the "
                           "late fees spec, in the imperative mood, such as "
                           "'Add the late fees spec', with no full stop")})
