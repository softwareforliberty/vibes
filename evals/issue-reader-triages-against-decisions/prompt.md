---
max_turns: 40
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:issue-reader` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Mode: triage
Issue: <cwd>/.vibes/issues/52/issue.json
Your login on the tracker: project-owner
Decision records: <cwd>/docs/adr/
Glossary: none
Brief: <cwd>/.vibes/issues/52/brief.md
Triage: <cwd>/.vibes/issues/52/triage.md
```

Don't do its work yourself, and don't read the issue. When it's done, run
`<cwd>/.vibes/issue-eval/tree-check`, then read `<cwd>/.vibes/issues/52/brief.md` and `<cwd>/.vibes/issues/52/triage.md`.

Reply with only the line `tree-check` printed, then the two files' contents, brief first, complete and
unchanged, and nothing else.
