---
max_turns: 50
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(*/wizard-check *)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:wizard-writer` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Mode: runbook
Plan: <cwd>/.vibes/runbook-drop-old-price/runbook-plan.md
Research notes: <cwd>/.vibes/runbook-drop-old-price/research/hosting-restart.md
Template: <cwd>/.vibes/runbook-drop-old-price/tools/skills/runbook/templates/runbook.sh
Runbook: <cwd>/.vibes/runbook-drop-old-price/runbook.sh
Check command: <cwd>/.vibes/runbook-drop-old-price/tools/bin/wizard-check
```

Don't do its work yourself, and don't run the runbook. When it's done,
run `<cwd>/.vibes/runbook-drop-old-price/tools/bin/wizard-check <cwd>/.vibes/runbook-drop-old-price/runbook.sh` and
`<cwd>/.vibes/runbook-drop-old-price/tree-check`, then read `<cwd>/.vibes/runbook-drop-old-price/runbook.sh`.

Reply with only the agent's reply, the lines the two checks printed, and
everything in `runbook.sh` below its `# ── STEPS` line, complete and
unchanged, and nothing else.
