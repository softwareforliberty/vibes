---
max_turns: 10
timeout_seconds: 600
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, "Bash(git *)"]
---

Run the `vibes:commit-message-suggester` agent, giving it exactly this
brief, with `<cwd>` replaced by the absolute path of your working
directory:

```text
Repository: <cwd>
Task: charge a late fee on overdue invoices
Commit: the approved spec for late fees, which the rebuild will build to
```

Don't write a message yourself. Reply with the agent's reply, complete and
unchanged, and nothing else.
