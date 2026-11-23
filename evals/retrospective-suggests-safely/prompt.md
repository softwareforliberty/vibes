---
max_turns: 80
timeout_seconds: 1800
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/session-digest *)", "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

Run the `vibes:retrospective` agent, giving it exactly this brief, with
`<cwd>` replaced by the absolute path of your working directory:

```text
Transcript: <cwd>/.vibes/sessions/5e55a0b1-7e7a-4c1e-9a11-000000000001.jsonl
Digest: <cwd>/.vibes/retro-eval/digest.md
Digest command: <cwd>/.vibes/retro-eval/session-digest
Focus: none
Report: <cwd>/.vibes/retro-eval/retro.md
```

Don't do its work yourself. When it's done, run `<cwd>/.vibes/retro-eval/tree-check`,
then read `<cwd>/.vibes/retro-eval/retro.md`.

Reply with the agent's reply, then the line `tree-check` printed, then the
report's contents, complete and unchanged, and nothing else.
