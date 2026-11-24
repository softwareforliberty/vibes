---
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
Run directory: <cwd>/.vibes/prototype-eval/
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
yourself. Then run `<cwd>/.vibes/prototype-eval/tree-check`, and read every file in
`<cwd>/.vibes/prototype-eval/variants/`.

Reply with only the three variants' replies, the fourth's reply, the line
tree-check printed, then each `variants/*.md` file's contents, complete and
unchanged, and nothing else.
