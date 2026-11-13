---
max_turns: 60
timeout_seconds: 2400
runs: 1
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, "Bash(git *)", "Bash(python3 *)", "Bash(*/bin/bench *)", "Bash(*/bench/run *)", "Bash(*/bench/prepare *)", "Bash(command -v *)", "Bash(which *)", "Bash(mkdir *)", "Bash(chmod *)", "Bash(ls *)", "Bash(cat *)", "Bash(head *)", "Bash(tail *)", "Bash(wc *)", "Bash(sort *)", "Bash(cd *)", "Bash(time *)", "Bash(/usr/bin/time *)", "Bash(uname *)", "Bash(sw_vers*)", "Bash(pmset *)", "Bash(sysctl *)", "Bash(diff *)", "Bash(shasum *)", "Bash(sample *)"]
---

Run the `vibes:profiler` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Mode: measure
Task: the dedupe command is slow on large exports
Run directory: <cwd>/.vibes/optimise-dedupe
Guides: languages/Python
Side a: main
Side b: spike/optimise-dedupe-1
Measurement directory: <cwd>/.vibes/optimise-dedupe/profile/candidate-1
Noise directory: <cwd>/.vibes/optimise-dedupe/profile/aa/main
Test command: scripts/check
Guard rails: rss_kib=10
Install nothing.
```

Don't do its work yourself. When it's done, run `git status --porcelain` and
`git branch --show-current` in your working directory, then read this file:

```text
<cwd>/.vibes/optimise-dedupe/profile/candidate-1/report.md
```

Reply with the agent's reply, then `TREE CLEAN` if `git status --porcelain`
printed nothing or `TREE CHANGED` if it printed anything, then the branch,
then the file's contents, all complete and unchanged, and nothing else.
