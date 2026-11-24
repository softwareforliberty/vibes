---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)", "Bash(pip show *)"]
---

Run the `vibes:designer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: spec
Task: Add a command that exports the day's refunds to a file for the
  finance team, who open it in a spreadsheet. Their lead also said it
  would help to keep the old exports around for a while.
Spec directory: <cwd>/.vibes/rounds-eval/draft/
Guides: languages/Python
Glossary: <cwd>/.vibes/rounds-eval/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/rounds-eval/tree-check`,
then read `<cwd>/.vibes/rounds-eval/draft/spec.md`.

Reply with only the line `tree-check` printed, then the spec's Open
questions and Assumptions sections, complete and unchanged, and nothing
else.
