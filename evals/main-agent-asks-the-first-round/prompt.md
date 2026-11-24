---
max_turns: 8
timeout_seconds: 300
runs: 3
allowed_tools: [Read, Glob, Grep]
---

`SKILL.md` in your working directory is the vibes workflow skill. You're
its main agent in Phase 1, step 2, about to resolve the open questions in
`spec.md`, in an attended run. Following the skill's Open questions
section, decide what round one does. Don't spawn anything or ask anything.

Reply with two lines and nothing else: `RESEARCH:` and the numbers of the
facts you'd have researched now, then `ASK:` and the numbers of the
decisions you'd ask the user now, each list in order, separated by ", ",
or `none`.
