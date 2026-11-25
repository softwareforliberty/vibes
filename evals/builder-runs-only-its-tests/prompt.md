---
max_turns: 150
timeout_seconds: 2400
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(git *)", "Bash(scripts/*)", "Bash(./scripts/*)", "Bash(*/scripts/*)", "Bash(python3 *)", "Bash(cd *)", "Bash(cat *)", "Bash(ls *)", "Bash(*/finish)"]
---

Run the `vibes:builder` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: build
Task: add parse_duration, which reads durations such as 1h30m as seconds
Branches: rebuild vibe/durations, base main; no spike
Spec: <cwd>/docs/specs/durations/spec.md
Rebuild plan: <cwd>/.vibes/durations/rebuild-plan.md
Guides: languages/Python
Batch: Batch 1 of the rebuild plan, its two entries. It's the first and
only batch.
Report: <cwd>/.vibes/durations/build-1.md
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/durations/finish`,
then read `<cwd>/.vibes/durations/build-1.md`.

Reply with only the agent's reply, the lines `finish` printed, and the
report, complete and unchanged, and nothing else.
