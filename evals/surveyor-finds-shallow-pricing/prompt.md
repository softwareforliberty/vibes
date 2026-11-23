---
max_turns: 80
timeout_seconds: 1800
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

Run the `vibes:surveyor` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: survey
Focus: none
Hotspots: <cwd>/.vibes/survey-eval/hotspots.txt
Glossary: <cwd>/GLOSSARY.md
Decision records: <cwd>/docs/adr/
Guides: languages/Python
Report: <cwd>/.vibes/survey-eval/survey.md
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/survey-eval/tree-check`,
then read `<cwd>/.vibes/survey-eval/survey.md`.

Reply with the agent's reply, then the line `tree-check` printed, then the
report's contents, complete and unchanged, and nothing else.
