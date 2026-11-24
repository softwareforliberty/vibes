---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(*/finish)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)", "Bash(pip show *)"]
---

Run the `vibes:designer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: design
Task: Add a command that writes the day's sales as a CSV, with a total
  per product. The spec is approved.
Spec directory: <cwd>/.vibes/design-eval/draft/
Guides: languages/Python
Glossary: <cwd>/.vibes/design-eval/draft/glossary.md, which doesn't exist yet
Decision records: <cwd>/docs/adr/, which doesn't exist yet
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/design-eval/tree-check`,
then read `<cwd>/.vibes/design-eval/draft/design.md`.

Reply with only the line `tree-check` printed, then the design's
Components and Boundary rules sections, complete and unchanged, and
nothing else: not the agent's reply.
