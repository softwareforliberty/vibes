# Agent Instructions Tools

No free and open source tool checks what makes these files work: whether
a pointer triggers, a step ends on a check, or a rule changes anything.
Review does, against [idioms.md](idioms.md), and running the agent does.

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| None | | | |

## Config files

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors: encoding, line endings and the 79-column wrap |

## Checking

`scripts/check` runs nothing for this guide. A project's Markdown linter,
if it has one, checks these files' layout with the rest of its Markdown.

Check a change by running it. Give an agent a task the file is for, once
with the change and once without, and compare what it read, the steps it
took and where it stopped. For a skill or subagent in a plugin, an eval
case does this on every change; see the plugin's `evals/`.
