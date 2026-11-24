---
max_turns: 60
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(*/tree-check)", "Bash(*/finish)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)", "Bash(pip show *)"]
---

Run the `vibes:researcher` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Question: What is tinyhttp's default request timeout, at the version this
  project uses?
Why: the spec for a --timeout option must say what happens without it.
Project: Python. Dependency versions are pinned in requirements.txt, and
  tinyhttp is vendored in vendor/tinyhttp.
Date: 2026-11-24
Note: <cwd>/.vibes/research-eval/research/tinyhttp-timeout.md
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/research-eval/tree-check`,
then read the note.

Reply with the agent's reply, then the line `tree-check` printed, then the
note's contents, complete and unchanged, and nothing else.
