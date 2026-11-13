---
max_turns: 60
timeout_seconds: 2400
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(git *)"]
---

Run the `vibes:optimiser` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: plan
Task: the dedupe command is slow on large exports
Run directory: <cwd>/.vibes/optimise-dedupe
Spec directory: <cwd>/docs/specs/optimise-dedupe
Guides: languages/Python
Latest profile: <cwd>/.vibes/optimise-dedupe/profile/baseline.md
```

Don't do its work yourself. When it's done, run `git status --porcelain` and
`git branch --show-current` in your working directory, then read this file:

```text
<cwd>/.vibes/optimise-dedupe/optimise-plan.md
```

Reply with the agent's reply, then `TREE CLEAN` if `git status --porcelain`
printed nothing or `TREE CHANGED` if it printed anything, then the branch,
then the file's contents, all complete and unchanged, and nothing else.
