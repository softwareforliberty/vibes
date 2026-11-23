---
max_turns: 12
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent]
---

Run the `vibes:project-docs-reviewer` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
Task: Charge a late fee on overdue invoices, as the spec describes.
Spec: <cwd>/docs/specs/late-fees/spec.md
Review directory: <cwd>/.vibes/late-fees/review/spec-1
Phase: spec
Guides: languages/Python
Round: 1
Project docs: README.md, GLOSSARY.md, docs/adr/0001-overdue-on-read.md, docs/release.md
```

Don't review anything yourself. When the agent is done, read the file it
writes its review to:

```text
<cwd>/.vibes/late-fees/review/spec-1/project-docs-reviewer.md
```

Reply with the agent's reply, then the file's contents, both complete and
unchanged, and nothing else.
