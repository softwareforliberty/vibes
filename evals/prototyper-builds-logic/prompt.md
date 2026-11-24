---
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
Run directory: <cwd>/.vibes/prototype-eval/
Guides: languages/Python
Glossary: <cwd>/GLOSSARY.md
Prototype: <cwd>/prototypes/part-shipped-cancel/index.html
prototype-check: <cwd>/.vibes/prototype-eval/bin/prototype-check
```

Don't do its work yourself. When it's done, run
`<cwd>/.vibes/prototype-eval/bin/prototype-check <cwd>/prototypes/part-shipped-cancel/index.html`
and `<cwd>/.vibes/prototype-eval/tree-check`, then read `<cwd>/.vibes/prototype-eval/scenarios.md`.

Reply with only the line prototype-check printed, the line tree-check
printed, then `scenarios.md`'s contents, complete and unchanged, and
nothing else.
