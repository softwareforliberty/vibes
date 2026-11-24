---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(*/finish)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)", "Bash(pip show *)"]
---

Run the `vibes:designer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: spec
Task: Add a command that exports the day's refunds to a file. The refunds
  come from Acme Payments' public refunds API, which the project doesn't
  use yet; it pages its results, so the command must fetch every page.
Spec directory: <cwd>/.vibes/research-eval/draft/
Guides: languages/Python
Glossary: <cwd>/.vibes/research-eval/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/research-eval/finish` on
its own, then read `<cwd>/.vibes/research-eval/draft/spec.md`.

Reply with only the line `finish` printed, then the spec's Open
questions and Assumptions sections, complete and unchanged, and nothing
else: not the agent's reply.
