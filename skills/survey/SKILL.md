---
name: survey
description: >-
  Surveys the codebase's architecture for shallow modules worth deepening,
  starting where recent commits keep landing, and shows ranked candidates
  with before and after diagrams on a page. For the one the user picks,
  several designers each design a very different interface, and they're
  compared with a recommendation that can become a /vibes:vibe task.
  Suggests and changes nothing.
argument-hint: "[area or pain point to survey]"
disable-model-invocation: true
---

# Survey: find what's worth deepening, then design it twice

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Focus: $ARGUMENTS

Look across the existing codebase, not one change, for **deepening
opportunities**: shallow modules, whose interface is nearly as complex as
the code behind it, where a deeper module would make the next change
easier and the code easier to test. The surveyor starts where recent
commits keep landing, since that's where a better structure pays off, and
writes ranked candidates with before and after diagrams. The user picks
one, or none.

For the one they pick, **design it twice:** several interface designers
each design it under a different constraint, without seeing each other's
work, and the surveyor compares them and recommends one. The chosen
design becomes a task for `/vibes:vibe`, which builds it test-first like
any other.

**The survey changes nothing.** Its agents may write only their own
reports, which a hook enforces, and you only write the pages and, when the
user agrees, a decision record.

## The agents

`vibes:surveyor`, `vibes:interface-designer` and
`vibes:commit-message-suggester`.

**Check they're loaded before anything else:** each must be among the agent
types you can spawn. If any is missing, stop and tell the user the vibes
agents aren't loaded in this session. In Claude Code, this happens when
vibes is enabled only for one checkout and the session runs in a git
worktree or another checkout; enabling it at user scope, or running from
the checkout it's enabled in, then starting a new session, fixes it. Never
stand in for one with `general-purpose` or any other agent told to read its
definition: a stand-in has none of its tool limits, and the hook that keeps
them read-only knows them only by their agent type.

## Steps

1. **Read the focus,** if the user gave one, such as `the order pipeline`
   or `adding a payment method touches eight files`. Without one, the
   hotspots decide.
2. **Find the glossary and the decision records,** as the vibe skill's
   [Phase 0](../vibe/SKILL.md#phase-0-set-up) does, and the guides:
   `git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"`.
3. **Make the survey's directory** from the repository root,
   `.vibes/survey-<date>-<n>`, such as `.vibes/survey-2026-11-24-1`, with
   the next free number, kept out of git:

   ```sh
   mkdir -p .vibes/survey-<date>-<n>/designs
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

4. **Find the hotspots,** as a command of its own:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/hotspots" > .vibes/survey-<date>-<n>/hotspots.txt
   ```

   If it exits 2, the project has no history yet: the focus decides
   where to look, or the whole codebase if there's none.
5. **Spawn `vibes:surveyor` in `survey` mode,** with the focus or that
   there's none, the hotspots file, the glossary and decision records
   directory, the guides, and the report path, `survey.md` in the
   directory, as absolute paths.
6. **Show the survey.** Turn it into a page and open it:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/report-page" .vibes/survey-<date>-<n>/survey.md \
     .vibes/survey-<date>-<n>/survey.html
   ```

   Open the page with `open` on macOS or `xdg-open` on Linux, and give
   its path. Read `survey.md`, and give the user, in the terminal: the top
   recommendation, then a line for each candidate with its id, what it
   would deepen and its strength. Ask which to explore, or none.
7. **When the user picks none, stop.** When they turn a candidate down
   for a reason that will still hold, such as a decision they've made
   about how that part works, offer to record it as a decision record, so
   later surveys don't suggest it again. With their yes, write it from
   `${CLAUDE_PLUGIN_ROOT}/skills/vibe/templates/adr.md`, numbered after
   the project's last, in its decision records directory, and commit it
   on its own, as the vibe skill's
   [agents section](../vibe/SKILL.md#the-agents) says for your own
   commits. Skip it for a passing reason, such as "not now".

## Design it twice

For the candidate the user picks:

1. **Spawn three `vibes:interface-designer`s in a single message,** so
   they work at once and apart. Each brief gives the candidate's id, the
   path of `survey.md`, the glossary, the decision records directory, the
   guides, its design path, `designs/<letter>.md`, and its constraint:
   - **A, the smallest interface:** as few entry points, types and
     concepts as callers can possibly use;
   - **B, the most flexible:** callers can see and vary every part that
     the code's history shows changing, without a new interface each
     time;
   - **C, a different seam:** the boundary goes somewhere the current code
     doesn't put it, such as around the data rather than the steps.

   When the user names a constraint of their own, add a designer D for
   it.
2. **Spawn `vibes:surveyor` in `compare` mode,** with the candidate's id,
   the design files and the report path, `comparison.md`. If it replies
   `CONVERGED`, two designs came out the same: spawn a fresh designer for
   the second of them, under a constraint no design has had yet, such as
   **the caller decides:** the module takes what varies, such as rates or
   rules, from its caller, and keeps only what never varies. Then compare
   again. Do this at most twice.
3. **Show the comparison.** Put it and the designs on one page:

   ```sh
   cat .vibes/survey-<date>-<n>/comparison.md \
     .vibes/survey-<date>-<n>/designs/*.md \
     > .vibes/survey-<date>-<n>/designs.md
   "${CLAUDE_PLUGIN_ROOT}/bin/report-page" .vibes/survey-<date>-<n>/designs.md \
     .vibes/survey-<date>-<n>/designs.html
   ```

   Open it, and give the user the recommendation and what it gives up,
   in a few lines. Ask whether to build it, build another design, have a
   design reworked under a constraint they name, or stop.
4. **To build it,** give the user the command to run, from the
   comparison's task: `/vibes:vibe <the task>, from the design in
   <design path>`. The designer reads that design as its starting point,
   and the refactor gets a spec, a test-first rebuild through the gate,
   and every review. Don't start it yourself: it's the user's call, and
   it runs in a fresh session or this one as they choose.

Keep the survey's directory: it records what was considered.
