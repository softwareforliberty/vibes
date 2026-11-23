---
max_turns: 80
timeout_seconds: 2400
runs: 3
allowed_tools: [Read, Glob, Grep, Agent, Write, "Bash(*/tree-check)", "Bash(git *)", "Bash(cat *)", "Bash(ls *)", "Bash(grep *)", "Bash(head *)", "Bash(sed -n *)"]
---

With `<cwd>` replaced by the absolute path of your working directory:

1. Run three `vibes:interface-designer` agents in a single message, so
   they work at the same time, giving each exactly this brief with its
   letter and constraint from the list below:

   ```text
   Candidate: C1, in <cwd>/.vibes/survey-eval/survey.md
   Constraint: <the constraint>
   Design: <cwd>/.vibes/survey-eval/designs/<letter>.md
   Glossary: <cwd>/GLOSSARY.md
   Decision records: <cwd>/docs/adr/
   Guides: languages/Python
   ```

   - `a`: the smallest interface: as few entry points, types and concepts as callers can possibly use
   - `b`: the most flexible: callers can see and vary every part that the code's history shows changing, without a new interface each time
   - `c`: a different seam: the boundary goes somewhere the current code doesn't put it, such as around the data rather than the steps

2. When all three are done, run the `vibes:surveyor` agent with exactly
   this brief:

   ```text
   Mode: compare
   Candidate: C1, in <cwd>/.vibes/survey-eval/survey.md
   Designs: <cwd>/.vibes/survey-eval/designs/a.md, b.md and c.md
   Glossary: <cwd>/GLOSSARY.md
   Decision records: <cwd>/docs/adr/
   Guides: languages/Python
   Report: <cwd>/.vibes/survey-eval/comparison.md
   ```

   If it replies `CONVERGED`, run one more `vibes:interface-designer` for
   the second design it names, with the same brief and this constraint:
   the caller decides: the module takes what varies, such as rates or
   rules, from its caller, and keeps only what never varies. Then run the
   surveyor again with the same brief.

Don't do their work yourself. When they're done, run
`<cwd>/.vibes/survey-eval/tree-check`, then read the comparison and the three designs.

Reply with the line `tree-check` printed, then the comparison, then each
design, complete and unchanged, and nothing else.
