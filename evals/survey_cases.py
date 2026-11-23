"""The architecture survey evals: a fixture project for vibes:surveyor and
vibes:interface-designer.

The project is orders, a small Python library. Its pricing is shallow:
four one-line modules for the base price, the discount, the tax and the
rounding, and a calculator whose setters must be called in order, while
three callers each run the sequence themselves, one in the wrong order. It
changes in most commits. Its storage is deep, one small interface over
SQLite that a decision record keeps, and changed once.

The survey case checks the surveyor ranks deepening the pricing first,
with a deletion test and diagrams, and leaves the storage alone. The
design case gives three designers the pricing candidate under different
constraints, then has the surveyor compare them, and checks the designs
differ in substance and the comparison recommends one with reasons. Both
check nothing outside .vibes/ changed.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict, List, Tuple

from pr_cases import GENERATED, write_case
from retro_cases import TREE_CHECK, write_files

EVALS = Path(__file__).resolve().parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/survey-eval"

FILES: Dict[str, str] = {
    "orders/__init__.py": '"""Orders, their prices, and where they\'re kept."""\n',
    "orders/model.py": '''"""The things an order is made of."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    price_cents: int


@dataclass(frozen=True)
class Customer:
    name: str
    tier: str  # "standard", "silver" or "gold"
    region: str  # "UK", "EU" or "US"


@dataclass(frozen=True)
class Line:
    product: Product
    quantity: int
''',
    "orders/pricing/__init__.py": "",
    "orders/pricing/base_price.py": '''from orders.model import Line


def base_price(line: Line) -> int:
    """The line's price before discount and tax, in cents."""
    return line.product.price_cents * line.quantity
''',
    "orders/pricing/discount.py": '''RATES = {"standard": 0.0, "silver": 0.05, "gold": 0.10}


def apply_discount(cents: float, tier: str) -> float:
    """The amount after the customer tier's discount."""
    return cents * (1 - RATES[tier])
''',
    "orders/pricing/tax.py": '''RATES = {"UK": 0.20, "EU": 0.21, "US": 0.0}


def apply_tax(cents: float, region: str) -> float:
    """The amount with the region's tax added."""
    return cents * (1 + RATES[region])
''',
    "orders/pricing/rounding.py": '''def round_cents(cents: float) -> int:
    """The amount rounded half up to whole cents."""
    return int(cents + 0.5)
''',
    "orders/pricing/calculator.py": '''from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


class PriceCalculator:
    """Prices lines. Call set_customer, then set_region, before total."""

    def __init__(self) -> None:
        self.tier = None
        self.region = None

    def set_customer(self, customer: Customer) -> None:
        self.tier = customer.tier

    def set_region(self, region: str) -> None:
        self.region = region

    def total(self, lines: list[Line]) -> int:
        cents = sum(base_price(line) for line in lines)
        cents = apply_discount(cents, self.tier)
        cents = apply_tax(cents, self.region)
        return round_cents(cents)
''',
    "orders/checkout.py": '''from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


def checkout_total(customer: Customer, lines: list[Line]) -> int:
    """What the customer pays at checkout, in cents."""
    cents = sum(base_price(line) for line in lines)
    cents = apply_discount(cents, customer.tier)
    cents = apply_tax(cents, customer.region)
    return round_cents(cents)
''',
    "orders/invoice.py": '''from orders.model import Customer, Line
from orders.pricing.base_price import base_price
from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


def invoice_lines(customer: Customer, lines: list[Line]) -> list[int]:
    """Each line's price on the invoice, in cents."""
    prices = []
    for line in lines:
        cents = apply_tax(base_price(line), customer.region)
        cents = apply_discount(cents, customer.tier)
        prices.append(round_cents(cents))
    return prices
''',
    "orders/quote.py": '''from orders.model import Customer, Line
from orders.pricing.calculator import PriceCalculator


def quote(customer: Customer, lines: list[Line]) -> int:
    """A quote for the lines, in cents."""
    calculator = PriceCalculator()
    calculator.set_customer(customer)
    calculator.set_region(customer.region)
    return calculator.total(lines)
''',
    "orders/storage.py": '''"""Where orders are kept: one small interface over SQLite."""

import json
import sqlite3


class OrderStore:
    """Saves and loads orders by number. Callers never see SQL."""

    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS orders "
                         "(number TEXT PRIMARY KEY, body TEXT NOT NULL)")

    def save(self, number: str, order: dict) -> None:
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO orders VALUES (?, ?)",
                             (number, json.dumps(order, sort_keys=True)))

    def load(self, number: str) -> dict:
        row = self._db.execute("SELECT body FROM orders WHERE number = ?",
                               (number,)).fetchone()
        if row is None:
            raise KeyError(number)
        return json.loads(row[0])

    def close(self) -> None:
        self._db.close()
''',
    "tests/__init__.py": "",
    "tests/test_pricing.py": '''import unittest

from orders.pricing.discount import apply_discount
from orders.pricing.rounding import round_cents
from orders.pricing.tax import apply_tax


class PricingTest(unittest.TestCase):
    def test_gold_gets_ten_percent(self) -> None:
        self.assertEqual(apply_discount(1000, "gold"), 900)

    def test_uk_tax_is_twenty_percent(self) -> None:
        self.assertEqual(apply_tax(1000, "UK"), 1200)

    def test_rounds_half_up(self) -> None:
        self.assertEqual(round_cents(10.5), 11)
''',
    "tests/test_storage.py": '''import unittest

from orders.storage import OrderStore


class StorageTest(unittest.TestCase):
    def test_loads_what_it_saved(self) -> None:
        store = OrderStore(":memory:")
        store.save("A-1", {"total": 1200})
        self.assertEqual(store.load("A-1"), {"total": 1200})
        store.close()
''',
    "GLOSSARY.md": '''# Glossary

orders prices customers' orders and keeps them.

## Terms

**Price:**
What a customer pays for a line or an order, in whole cents, after the
discount and the tax.
_Avoid:_ cost, amount

**Discount:**
The share of the price a customer's tier takes off.

**Quote:**
A price given before an order is placed.
''',
    "docs/adr/0001-keep-the-store-behind-one-interface.md": '''# 1. Keep the store behind one interface

Callers save and load orders through `OrderStore` and never see SQL, so the
storage can move off SQLite without touching them.
''',
}

# The history: (message, paths changed). Each change appends a line to a
# comment at the end of each path, so the files stay valid.
HISTORY: List[Tuple[str, Tuple[str, ...]]] = [
    ("Add tax for the EU", ("orders/pricing/tax.py", "orders/checkout.py")),
    ("Add the silver tier", ("orders/pricing/discount.py",
                             "orders/invoice.py")),
    ("Price quotes", ("orders/quote.py", "orders/pricing/calculator.py")),
    ("Round invoice lines", ("orders/invoice.py",
                             "orders/pricing/rounding.py")),
    ("Fix checkout rounding", ("orders/checkout.py",
                               "orders/pricing/rounding.py")),
    ("Discount quotes", ("orders/quote.py", "orders/pricing/calculator.py",
                         "orders/pricing/discount.py")),
    ("US orders pay no tax", ("orders/pricing/tax.py", "orders/checkout.py",
                              "orders/invoice.py")),
    ("Gold tier is ten percent", ("orders/pricing/discount.py",
                                  "orders/checkout.py", "orders/quote.py")),
]

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The orders project with its history, the hotspots bin/hotspots found in
# it, and the files the case needs, as /vibes:survey leaves them.

set -euo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
commit() {{
  git add -A
  git -c user.name=evals -c user.email=evals@example.invalid \\
    commit -q -m "$1"
}}
git init -q -b main .
cp -R "${{fixtures}}/survey-project/." .
mkdir -p .vibes
printf '*\\n' > .vibes/.gitignore
commit "Price and store orders"
while IFS='|' read -r message paths; do
  for path in ${{paths}}; do printf '# %s\\n' "${{message}}" >> "${{path}}"; done
  commit "${{message}}"
done < "${{fixtures}}/survey-history.txt"
mkdir -p {run}/designs
"${{here}}/../../bin/hotspots" > {run}/hotspots.txt
{extra}cp "${{fixtures}}/retro-tools/tree-check" {run}/
chmod +x {run}/tree-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

SURVEY_PROMPT = """---
max_turns: 80
timeout_seconds: 1800
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

Run the `vibes:surveyor` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: survey
Focus: none
Hotspots: <cwd>/{run}/hotspots.txt
Glossary: <cwd>/GLOSSARY.md
Decision records: <cwd>/docs/adr/
Guides: languages/Python
Report: <cwd>/{run}/survey.md
```

Don't do its work yourself. When it's done, run `<cwd>/{run}/tree-check`,
then read `<cwd>/{run}/survey.md`.

Reply with the agent's reply, then the line `tree-check` printed, then the
report's contents, complete and unchanged, and nothing else.
"""

# The pricing candidate, as a survey would give it, for the design case.
SURVEY = """# Survey: orders

Looked at: orders/pricing/ and its callers, the hotspots.

## Top recommendation

C1: pricing changes in most commits, and every change touches its callers.

## C1. Deepen pricing into one Price module: Strong

- **Files:** orders/pricing/base_price.py, discount.py, tax.py,
  rounding.py and calculator.py, and their callers orders/checkout.py,
  orders/invoice.py and orders/quote.py.
- **Problem:** each caller runs the base price, discount, tax and rounding
  steps itself, and orders/invoice.py:11 runs tax before the discount, so
  invoices disagree with checkout. PriceCalculator must have set_customer
  and set_region called before total.
- **Deletion test:** deleting the four step modules would barely change
  the callers, which already hold the sequence: the modules are shallow.
- **Proposal:** one module that prices lines for a customer, holding the
  steps and their order, so callers make one call.
- **Benefits:** the sequence lives in one place; tests drive real prices
  through it instead of each step alone.
- **Cost and risk:** small: three callers and one test file.
- **Decision records:** none.

## Left alone

- orders/storage.py: deep already, and kept by
  docs/adr/0001-keep-the-store-behind-one-interface.md.
"""

CONSTRAINTS = (
    ("a", "the smallest interface: as few entry points, types and concepts "
          "as callers can possibly use"),
    ("b", "the most flexible: callers can see and vary every part that "
          "the code's history shows changing, without a new interface "
          "each time"),
    ("c", "a different seam: the boundary goes somewhere the current code "
          "doesn't put it, such as around the data rather than the steps"),
)

DESIGN_PROMPT = """---
max_turns: 80
timeout_seconds: 2400
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

With `<cwd>` replaced by the absolute path of your working directory:

1. Run three `vibes:interface-designer` agents in a single message, so
   they work at the same time, giving each exactly this brief with its
   letter and constraint from the list below:

   ```text
   Candidate: C1, in <cwd>/{run}/survey.md
   Constraint: <the constraint>
   Design: <cwd>/{run}/designs/<letter>.md
   Glossary: <cwd>/GLOSSARY.md
   Decision records: <cwd>/docs/adr/
   Guides: languages/Python
   ```

{constraints}

2. When all three are done, run the `vibes:surveyor` agent with exactly
   this brief:

   ```text
   Mode: compare
   Candidate: C1, in <cwd>/{run}/survey.md
   Designs: <cwd>/{run}/designs/a.md, b.md and c.md
   Glossary: <cwd>/GLOSSARY.md
   Decision records: <cwd>/docs/adr/
   Guides: languages/Python
   Report: <cwd>/{run}/comparison.md
   ```

   If it replies `CONVERGED`, run one more `vibes:interface-designer` for
   the second design it names, with the same brief and this constraint:
   the caller decides: the module takes what varies, such as rates or
   rules, from its caller, and keeps only what never varies. Then run the
   surveyor again with the same brief.

Don't do their work yourself. When they're done, run
`<cwd>/{run}/tree-check`, then read the comparison and the three designs.

Reply with the line `tree-check` printed, then the comparison, then each
design, complete and unchanged, and nothing else.
"""


def llm(criterion: str) -> str:
    return f"---\ntype: llm\n---\n\nPASS if {criterion}.\nFAIL otherwise.\n"


def dispatched(agent: str) -> str:
    return (f"---\ntype: regex\npattern: 'subagent_type\\W+vibes:{agent}'\n"
            "target: trace\n---\n")


TREE_CLEAN = "---\ntype: regex\npattern: '^TREE CLEAN$'\nflags: m\n---\n"


def build() -> None:
    """Write the survey fixture and cases."""
    write_files(FIXTURES / "survey-project", FILES)
    (FIXTURES / "survey-history.txt").write_text(
        "".join(f"{message}|{' '.join(paths)}\n"
                for message, paths in HISTORY), encoding="utf-8")
    write_files(FIXTURES / "survey-design", {"survey.md": SURVEY})
    write_case(
        "surveyor-finds-shallow-pricing", "survey",
        SURVEY_PROMPT.format(run=RUN),
        SCAFFOLD.format(generated=GENERATED, run=RUN, extra=""),
        {"dispatched": dispatched("surveyor"),
         "tree-clean": TREE_CLEAN,
         "diagrams": "---\ntype: regex\npattern: '```mermaid'\n---\n",
         "top-is-pricing": llm(
             "the top recommendation is to deepen the pricing: the base "
             "price, discount, tax and rounding pieces and the "
             "PriceCalculator become one module that owns the whole "
             "calculation, so the callers stop combining the steps "
             "themselves; and it cites callers such as orders/checkout.py "
             "or orders/invoice.py doing that combining today"),
         "deletion-test": llm(
             "the pricing candidate applies the deletion test and "
             "concludes that some or all of the pricing pieces or the "
             "PriceCalculator are shallow, because the decisions that "
             "matter, such as the order of the steps and the rounding, "
             "sit in the callers"),
         # No candidate's heading names the store; the report may still
         # say, under Left alone, that it's deep.
         "leaves-storage": "---\ntype: regex\n"
                           "pattern: '^## C[0-9][^\\n]*(storage|store)'\n"
                           "flags: im\nmatch: not_contains\n---\n"})
    write_case(
        "interface-designers-design-it-twice", "survey",
        DESIGN_PROMPT.format(run=RUN, constraints="\n".join(
            f"   - `{letter}`: {text}" for letter, text in CONSTRAINTS)),
        SCAFFOLD.format(
            generated=GENERATED, run=RUN,
            extra=f'cp "${{fixtures}}/survey-design/survey.md" {RUN}/\n'),
        {"designers": dispatched("interface-designer"),
         "compared": dispatched("surveyor"),
         "tree-clean": TREE_CLEAN,
         "truly-different": llm(
             "the three designs propose materially different interfaces, "
             "such as different entry points, types or where the boundary "
             "sits, not the same interface with different names"),
         "real-callers": llm(
             "each design shows real call sites from orders/checkout.py, "
             "orders/invoice.py or orders/quote.py rewritten against its "
             "interface"),
         "recommends": llm(
             "the comparison compares the designs on what callers must "
             "know, what each hides, the seam, tests and migration, then "
             "recommends one design or a named combination with its "
             "reasons and what it gives up")})
