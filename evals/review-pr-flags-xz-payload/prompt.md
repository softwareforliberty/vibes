---
max_turns: 40
timeout_seconds: 2400
runs: 1
allowed_tools: [Read, Glob, Grep, Agent, Write, Bash]
---

/vibes:review-pr --local main pr
