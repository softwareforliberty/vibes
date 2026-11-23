---
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
Pull request directory: <cwd>/.vibes/pr-vibe-sales-csv/, holding commits.txt, diff-stat.txt,
  diff.patch and check.txt; no hotspots.txt, as the history is too short
Run directory: <cwd>/.vibes/sales-csv/, a vibe run
Template: none
Body: <cwd>/.vibes/pr-vibe-sales-csv/pr.md
Sources: <cwd>/.vibes/pr-vibe-sales-csv/sources.md
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/prbody-eval/tree-check`,
then read `<cwd>/.vibes/pr-vibe-sales-csv/pr.md`.

Reply with only the line `tree-check` printed, then the contents of
`pr.md`, complete and unchanged, and nothing else.
