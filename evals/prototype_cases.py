"""The prototype evals: projects for vibes:prototyper.

The logic case is orders, a small Python library whose orders ship in
parcels, asking whether an order can be cancelled once part of it has
shipped. It checks the prototype keeps bin/prototype-check's rules, and
that its scenarios include cancelling after a partial shipment and an
action that's refused, in the business's words.

The UI case is a small web app with a settings page, built from plain
HTML and JavaScript. Three prototypers each build a variant of the page
under a different constraint, and a fourth compares them. It checks the
variants differ in structure and leave the page itself alone.

Both check nothing changed outside .vibes/ and the prototype's own files.
So the agents needn't run git, which in the eval sandbox on macOS needs
lib/eval-path's wrapper, the briefs tell them their branch.

generate.py calls build() after clearing the generated files.
"""

from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case
from research_cases import TREE_CLEAN, dispatched, llm
from retro_cases import write_files

EVALS = Path(__file__).resolve().parent
PLUGIN = EVALS.parent
FIXTURES = EVALS / "fixtures"
RUN = ".vibes/prototype-eval"

# Like retro-tools' tree-check, but the prototype's own files may change.
TREE_CHECK = """#!/bin/sh
here="$(cd "$(dirname -- "$0")" && pwd)"
cd "${here}/../.." || exit 2
find . \\( -path ./.vibes -o -path ./.git -o -path ./prototypes \\
  -o -name 'prototype-*' \\) -prune -o -type f -print \\
  | LC_ALL=C sort | while IFS= read -r path; do cksum "$path"; done \\
  > "${here}/tree-now"
if cmp -s "${here}/tree-before" "${here}/tree-now"; then
  echo 'TREE CLEAN'
else
  echo 'TREE CHANGED'
fi
"""

ORDERS: Dict[str, str] = {
    "README.md": """# orders

Takes orders and ships them in parcels. A large order can ship in several
parcels, on different days.
""",
    "GLOSSARY.md": """# Glossary

- **Order:** what a customer bought in one checkout.
- **Parcel:** one shipment of some of an order's items.
- **Part-shipped:** an order with at least one parcel sent and items
  still to send.
""",
    "orders/__init__.py": "",
    "orders/model.py": '''"""An order and its parcels."""

from dataclasses import dataclass, field


@dataclass
class Order:
    items: list[str]
    shipped: list[str] = field(default_factory=list)
    status: str = "open"  # open, part-shipped, shipped or cancelled

    def ship(self, items: list[str]) -> None:
        self.shipped += items
        self.status = ("shipped" if set(self.shipped) == set(self.items)
                       else "part-shipped")

    def cancel(self) -> None:
        self.status = "cancelled"  # what about the parcels already sent?
''',
}

SETTINGS_APP: Dict[str, str] = {
    "README.md": """# shopfront

The shop's admin pages: plain HTML and JavaScript, no build step. Open
`app/settings.html` in a browser.
""",
    "app/data.js": """// The settings the page shows, as the server would send them.
export const settings = {
  profile: { shopName: "Corner Books", email: "hello@example.invalid" },
  shipping: { freeOver: 4000, regions: ["UK", "EU"] },
  notifications: { newOrder: true, lowStock: true, weeklyReport: false },
  payments: { provider: "Acme Pay", payoutDay: "Friday" },
};
""",
    "app/settings.js": """import { settings } from "./data.js";

// Renders every section of the settings as one long form.
const root = document.querySelector("#settings");
for (const [section, values] of Object.entries(settings)) {
  const block = document.createElement("fieldset");
  block.innerHTML = `<legend>${section}</legend>`;
  for (const [key, value] of Object.entries(values)) {
    const row = document.createElement("label");
    row.textContent = `${key}: ${value}`;
    block.append(row);
  }
  root.append(block);
}
""",
    "app/settings.html": """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Settings</title></head>
<body>
  <h1>Settings</h1>
  <form id="settings"></form>
  <button type="submit" form="settings">Save</button>
  <script type="module" src="settings.js"></script>
</body>
</html>
""",
}

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# The {project} project, with the run directory, prototype-check and a tree
# check that lets the prototype's own files change.

set -euo pipefail
here="$(cd "$(dirname -- "$0")" && pwd)"
fixtures="${{here}}/../fixtures"
cp -R "${{fixtures}}/{project}/." .
mkdir -p {run}/bin {run}/lib/prototype_check {run}/variants
printf '*\\n' > .vibes/.gitignore
cp "${{here}}/../../bin/prototype-check" {run}/bin/
cp "${{here}}/../../lib/prototype_check/"*.py {run}/lib/prototype_check/
cp "${{fixtures}}/prototype-tools/tree-check" {run}/
chmod +x {run}/tree-check {run}/bin/prototype-check
{run}/tree-check >/dev/null
mv {run}/tree-now {run}/tree-before
"""

LOGIC_PROMPT = """---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(*/prototype-check *)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:prototyper` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Mode: logic
Question: Can an order be cancelled once part of it has shipped, and if
  so, what happens to the parcels already sent and the items not yet sent?
Branch: spike/prototype-part-shipped-cancel. Git isn't available here:
  take it that you're on this branch, and skip the check.
Run directory: <cwd>/{run}/
Guides: languages/Python
Glossary: <cwd>/GLOSSARY.md
Prototype: <cwd>/prototypes/part-shipped-cancel/index.html
prototype-check: <cwd>/{run}/bin/prototype-check
```

Don't do its work yourself. When it's done, run
`<cwd>/{run}/bin/prototype-check <cwd>/prototypes/part-shipped-cancel/index.html`
and `<cwd>/{run}/tree-check`, then read `<cwd>/{run}/scenarios.md`.

Reply with only the line prototype-check printed, the line tree-check
printed, then `scenarios.md`'s contents, complete and unchanged, and
nothing else.
"""

UI_PROMPT = """---
max_turns: 80
timeout_seconds: 1800
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(cat *)", "Bash(ls *)"]
---

Run four `vibes:prototyper` agents. First spawn three in one message, each
with this brief, with `<cwd>` replaced by the absolute path of your
working directory, and `<letter>` and `<constraint>` as listed below:

```text
Mode: variant
Question: How should the shop's settings page be laid out?
Branch: spike/prototype-settings-layout. Git isn't available here: take it
  that you're on this branch, and skip the check.
Run directory: <cwd>/{run}/
Guides: web/HTML, languages/JavaScript
Host page: <cwd>/app/settings.html, with app/settings.js and app/data.js
Variant: <letter>
Constraint: <constraint>
```

- **A,** everything at once: the densest view, with all the data and
  actions visible together.
- **B,** one main action: the thing most visits come to do, front and
  centre, and the rest out of the way.
- **C,** in steps: the screen split into sections or steps the user moves
  through.

When all three are done, spawn the fourth with the same brief but
`Mode: compare` and no variant or constraint. Don't do their work
yourself. Then run `<cwd>/{run}/tree-check`, and read every file in
`<cwd>/{run}/variants/`.

Reply with only the three variants' replies, the fourth's reply, the line
tree-check printed, then each `variants/*.md` file's contents, complete and
unchanged, and nothing else.
"""


def build() -> None:
    """Write the prototype projects and cases."""
    write_files(FIXTURES / "prototype-orders", ORDERS)
    write_files(FIXTURES / "prototype-settings", SETTINGS_APP)
    write_files(FIXTURES / "prototype-tools", {"tree-check": TREE_CHECK})
    write_case(
        "prototyper-builds-logic", "prototype",
        LOGIC_PROMPT.format(run=RUN),
        SCAFFOLD.format(generated=GENERATED, project="prototype-orders",
                        run=RUN),
        {"dispatched": dispatched("prototyper"),
         "tree-clean": TREE_CLEAN,
         "keeps-the-rules": "---\ntype: regex\n"
                            "pattern: '^PROTOTYPE OK: [2-9]'\nflags: m\n---\n",
         "cancels-part-shipped": llm(
             "a scenario cancels, or tries to cancel, an order after some "
             "of its parcels have shipped, and says what happens to the "
             "parcels already sent and the items not yet sent"),
         "something-refused": llm(
             "at least one scenario tries an action that the model "
             "refuses, and says it's refused"),
         "business-words": llm(
             "the scenarios speak of orders, parcels, shipping and "
             "cancelling in plain words. Statuses in words, such as "
             "Part-shipped, Cancelled or Part-cancelled, are fine. It "
             "fails only on programming terms, such as reducer, dispatch, "
             "action or state object, or names in code form, such as "
             "part_shipped or cancelOrder")})
    write_case(
        "prototypers-vary-a-screen", "prototype",
        UI_PROMPT.format(run=RUN),
        SCAFFOLD.format(generated=GENERATED, project="prototype-settings",
                        run=RUN),
        {"dispatched": dispatched("prototyper"),
         "tree-clean": TREE_CLEAN,
         "distinct": "---\ntype: regex\npattern: '^DISTINCT'\nflags: m\n"
                     "---\n",
         "beside-the-page": "---\ntype: regex\n"
                            "pattern: 'app/prototype-[^/\"\\s]+/'\n"
                            "target: trace\n---\n",
         "differ-in-structure": llm(
             "the three variants described differ in structure, not just "
             "styling: one shows everything at once, one puts a single "
             "main action first, and one splits the settings into sections "
             "or steps to move through"),
         "say-the-cost": llm(
             "each variant's description says what it's worse at because "
             "of its constraint")})
