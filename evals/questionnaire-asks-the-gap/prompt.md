---
max_turns: 30
timeout_seconds: 600
runs: 3
allowed_tools: [Read, Glob, Grep, Write, Edit, "Bash(ls *)", "Bash(mkdir *)"]
---

`skills/questionnaire/SKILL.md` in your working directory is a skill. The
user ran it as `/vibes:questionnaire the three open questions in
docs/specs/nightly-export/spec.md`. Follow it, with your working directory
standing for `${{CLAUDE_PLUGIN_ROOT}}`.

When it says to ask the user, use these answers, which the user gave up
front, rather than asking:

- **Who it's for:** the company's data protection officer, a colleague in
  another department, who knows the data protection rules and the
  company's retention policy, but not this project.
- **What they need back:** 1. how long exported records may be kept in
  the warehouse; 2. whether email addresses and phone numbers may be
  exported, and if so whether they must be masked; 3. whether customers
  who opted out of analytics must be left out.
- **By when:** 5 December 2026. **From:** the platform team.

Reply with only the questionnaire's contents, complete and unchanged, and
nothing else.
