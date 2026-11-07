---
max_turns: 8
timeout_seconds: 300
runs: 3
allowed_tools: [Read, Glob, Grep]
---

`SKILL.md` in your working directory is the vibes workflow skill. You're its
main agent, about to start round 1 of the `rebuild` review of a medium task,
which has a design. `files.txt` lists the files the change touches, and
`guides.txt` is what `guides-for` printed for them. Following the skill's
rules for the review panel, decide which reviewers run. Don't run any.

Reply with one line: `PANEL:` and then the reviewers' names without the
`vibes:` prefix, in alphabetical order, separated by ", ".
