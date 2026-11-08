---
max_turns: 12
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent]
---

Run the `vibes:resource-leak-reviewer` agent on a change, giving it exactly this brief,
with `<cwd>` replaced by the absolute path of your working directory:

```text
Task: Add a low-stock report to the stock library, as docs/spec.md describes.
Spec: <cwd>/docs/spec.md
Design: <cwd>/docs/design.md
Review directory: <cwd>/.vibes/stock/review/round-1
Phase: spike
Guides: languages/Python
Round: 1
```

Don't review the change yourself. When the agent is done, read the file it
writes its review to:

```text
<cwd>/.vibes/stock/review/round-1/resource-leak-reviewer.md
```

Reply with the agent's reply, then the file's contents, both complete and
unchanged, and nothing else.
