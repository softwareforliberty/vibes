---
max_turns: 40
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:issue-reader` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Mode: brief
Issue: <cwd>/.vibes/issues/41/issue.json
Your login on the tracker: project-owner
Decision records: <cwd>/docs/adr/
Glossary: none
Brief: <cwd>/.vibes/issues/41/brief.md
```

Don't do its work yourself, and don't read the issue. When it's done, run
`<cwd>/.vibes/issue-eval/tree-check`, then read `<cwd>/.vibes/issues/41/brief.md`.

Reply with only the line `tree-check` printed, then the brief's contents, complete and
unchanged, and nothing else.
