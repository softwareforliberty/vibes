---
max_turns: 50
timeout_seconds: 1200
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(*/wizard-check *)", "Bash(cat *)", "Bash(ls *)"]
---

Run the `vibes:wizard-writer` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Plan: <cwd>/.vibes/acme-pay/wizard-plan.md
Research notes: <cwd>/.vibes/acme-pay/research/acme-pay-keys.md and
  <cwd>/.vibes/acme-pay/research/acme-pay-account.md
Template: <cwd>/.vibes/acme-pay/tools/skills/wizard/templates/wizard.sh
Wizard: <cwd>/.vibes/acme-pay/wizard.sh
Check command: <cwd>/.vibes/acme-pay/tools/bin/wizard-check
```

Don't do its work yourself. When it's done, run
`<cwd>/.vibes/acme-pay/tools/bin/wizard-check <cwd>/.vibes/acme-pay/wizard.sh` and
`<cwd>/.vibes/acme-pay/tree-check`, then read `<cwd>/.vibes/acme-pay/wizard.sh`.

Reply with only the agent's reply, the lines the two checks printed, and
everything in `wizard.sh` below its `# ── STAGES` line, complete and
unchanged, and nothing else.
