---
max_turns: 40
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Write, Edit, "Bash(mkdir *)", "Bash(ls *)", "Bash(*/tree-check)"]
---

`skills/grill/SKILL.md` in your working directory is a skill. The user ran
it as `/vibes:grill add a currency column to the daily sales CSV, now we
sell in euros too`. Follow only its steps 1 and 2, with your working
directory standing for `${CLAUDE_PLUGIN_ROOT}` and the slug
`currency-column`. Ask the user nothing, and spawn nothing.

Then run `<cwd>/.vibes/rounds-eval/tree-check`, with `<cwd>` your working directory.

Reply with only the line `tree-check` printed, then the contents of
`.vibes/grill-currency-column/decisions.md`, complete and unchanged, and
nothing else.
