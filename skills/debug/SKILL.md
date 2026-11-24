---
name: debug
description: >-
  Finds and fixes a bug whose cause isn't known: builds a command that fails
  on the exact symptom, reliably and in seconds, shrinks it, ranks
  hypotheses that could be proved wrong and tests them one change at a
  time on a throwaway branch, then fixes the proved cause test-first from a
  short bug spec, through the gate, and has it reviewed. Separate from
  /vibes:vibe, which builds what's already understood.
argument-hint: "[unattended:] <the symptom or #issue>"
disable-model-invocation: true
---

# Debug: reproduce, diagnose, fix test-first

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Symptom: $ARGUMENTS

Find out why something is broken, then fix it properly. First the
diagnoser builds a **reproduction**: one command that fails on the exact
symptom, every time, in seconds, which `bin/repro` checks. Nobody guesses
at the cause before it exists. It's **shrunk** until every part is needed,
then the diagnoser ranks **hypotheses**, each with a prediction that could
prove it wrong, and **probes** them one change at a time on a throwaway
spike branch, until one is confirmed and a quick change makes the command
pass. Then a short **bug spec** is written and reviewed, and the fix is
**rebuilt test-first** on its own branch, through the gate, starting from
a regression test that fails on the bug. The reviewers check it, and the
original reproduction must pass at the end.

With `unattended:`, the run never stops to ask, as
[Unattended runs](#unattended-runs) describes. Otherwise it asks when only
the user can decide.

You are the main agent. You coordinate, ask the user what only they can
decide, and run `bin/repro` yourself: the diagnoser builds the
reproduction, but you judge it. The diagnoser keeps its findings in the
run directory and replies in a line or two. Read `diagnosis.md` when you
write the bug spec, and `hypotheses.md` when you show the user the
hypotheses; leave the probes and the code to the agents.

## The agents

| Agent | Role |
| --- | --- |
| `vibes:diagnoser` | Builds and shrinks the reproduction, ranks the hypotheses, probes them and proves the cause, on the spike branch. Never fixes the bug for real |
| `vibes:builder` | Rebuilds the fix test-first, and fixes review findings |
| `vibes:researcher` | Answers a factual question the bug spec needs, from primary sources, in a dated, cited note |
| `vibes:issue-reader` | Turns an issue, which anyone may have written, into a brief the run starts from, once the user confirms it |
| `vibes:wizard-writer` | Writes a wizard for settings only the user can provide, at the end of a run |
| `vibes:spec-reviewer`, `vibes:project-docs-reviewer` | Review the bug spec, and the fix |
| `vibes:bug-reviewer`, `vibes:cleanliness-reviewer`, `vibes:test-reviewer`, and `vibes:security-reviewer`, `vibes:performance-reviewer`, `vibes:resource-leak-reviewer` when they apply | Review the fix |
| `vibes:commit-message-suggester` | Suggests the message for each commit you make yourself |

**Check they're loaded before anything else,** even before resuming: each
agent above, the conditional ones too, must be among the agent types you
can spawn. If any is missing, stop and tell the user, as the vibe skill's
[agents section](../vibe/SKILL.md#the-agents) says, which gives the cause
and the fix, and why no other agent may stand in for one.

**Your own commits,** such as the bug spec, are made as the vibe skill's
[agents section](../vibe/SKILL.md#the-agents) says: stage, have
`vibes:commit-message-suggester` suggest the message, and commit through
the gate. Every subject is 50 characters at most.

## Names

Pick a short kebab-case slug for the bug, such as `month-end-due-date`.
Everything this run makes is prefixed so it never meets a vibe or
optimise run's:

- **Run directory:** `.vibes/debug-<slug>/`, which git ignores, so its
  files survive switching branches. Its state file is `debug-state.md`.
- **Spike branch:** `spike/debug-<slug>`, from the base branch, where the
  diagnoser works. The gate and the check-file hook don't run on `spike/`
  branches, so probes and debug logs aren't blocked. It's never merged.
- **Debug tag:** `vibes-debug-<slug>`, on every temporary debug log. The
  gate refuses any commit that adds a line carrying it, so none reaches
  the fix.
- **Fix branch:** `debug/<slug>`, from the base branch.
- **Spec directory:** `debug-<slug>/` in the project's spec directory, or
  in `docs/specs/` if it has none.

## Rules

- **Hypothesise only from a red reproduction.** The diagnoser's
  `hypothesise` mode runs only once `bin/repro` says `RED` for both
  `repro.sh` and `minimal.sh`.
- **You judge with `bin/repro`,** never the diagnoser's word, running each
  command on its own so a permission rule for it matches:

  ```sh
  "${CLAUDE_PLUGIN_ROOT}/bin/repro" run \
    --out .vibes/debug-<slug>/repro/<name> -- .vibes/debug-<slug>/repro.sh
  ```

  `RED` means every run failed on the bug. `FLAKY` and `CAN'T TELL` aren't
  good enough: give the line back to the diagnoser to tighten. `SLOW`
  means over 30 seconds a run: have it made faster before going on.
- **Check the branches after every diagnoser run:** the base branch
  hasn't moved, the spike branch is checked out, and nothing outside the
  run directory is left uncommitted. If not, stop and tell the user.
- **The spike's code is never merged.** The fix is rebuilt test-first on
  the fix branch.
- **The spec comes first** on the fix branch, as the vibe skill's
  [The spec comes first](../vibe/SKILL.md#the-spec-comes-first) says.
- **Keep the guides current** on both branches, as the vibe skill's
  [Keep the guides current](../vibe/SKILL.md#keep-the-guides-current)
  says, with `debug-state.md` in place of `state.md`.

### Unattended runs

Record an unattended run in the state file. Then, wherever this skill says
to ask the user:

- **The hypotheses:** keep the diagnoser's ranking.
- **Open questions in the bug spec, or a fix that would alter what the
  user expects:** research the facts as usual, then decide and record each
  decision as the vibe skill's
  [Unattended runs](../vibe/SKILL.md#unattended-runs) says.
- **No reproduction, every hypothesis refuted three rounds running, a fix
  that needs a design, a symptom that's only slowness, or a round
  limit:** stop, and report what was found and what's needed.
- **Anything that could lose the user's work:** stop, and report it.

The final report lists every unattended decision first.

## When you need the user

Whenever the run stops to wait for the user, notify them first and ask
everything at once, as the vibe skill's
[When you need the user](../vibe/SKILL.md#when-you-need-the-user) says.

## The state file

Keep `.vibes/debug-<slug>/debug-state.md` current, from
`${CLAUDE_PLUGIN_ROOT}/skills/debug/templates/debug-state.md`: the
symptom, the user's answers, the issue if it came from one, unattended
or not, the branches, the base
commit, the guides, the diagnosis so far, the phase and last step, and
`status: running` until the end, then `status: done`. Update it after
every step.

## Resume an unfinished run

Before Phase 0, look for `.vibes/debug-*/debug-state.md` with
`status: running`. If there's one for this symptom, or the symptom is
empty, resume it; for another, ask the user whether to finish it first.
If a vibe or optimise run's state file says `status: running`, tell the
user, since both would use the working tree.

To resume, read the state file, check the branches and commits agree with
it (git wins), and carry on from the first unfinished step. A diagnoser
that didn't reply runs again in the same mode, told what already exists.

## Phase 0: Set up

1. **Understand the symptom.** If it's an issue, such as `#123`, take it
   as the vibe skill's
   [From an issue](../vibe/SKILL.md#from-an-issue) says, and use the
   brief's task as the symptom. If it's unclear what's wrong, or how to see
   it, ask the user (unattended: take the narrowest reading, and record
   it). If it's only that something is slow, tell the user that
   `/vibes:optimise` is for that, and stop. Pick the slug.
2. **Check the working tree is clean.** If it isn't, ask the user what to
   do. The current branch is the base branch, and its commit the base
   commit.
3. **Find the guides:** `git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"`.
4. **Create the run directory** and the state file:

   ```sh
   mkdir -p .vibes/debug-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

5. **Check the git hooks,** as the vibe skill's
   [Phase 0](../vibe/SKILL.md#phase-0-set-up) says, with
   `bin/install-git-hooks`.
6. **Set up the commit gate,** if the project has no executable
   `scripts/check` or `scripts/check-file`, or the `# Guides:` line misses
   a guide: spawn a `general-purpose` subagent with `medium` effort to
   follow `${CLAUDE_PLUGIN_ROOT}/skills/commit-gate/SKILL.md` on the base
   branch, committing the setup on its own. Wait for it: both branches
   start from its commit, which becomes the base commit.
7. **Create the spike branch:** `git switch -c spike/debug-<slug>`.

## Phase 1: Reproduce and shrink

1. **Spawn `vibes:diagnoser` in `reproduce` mode,** with the symptom and
   the user's answers, the spike and base branches, the run directory, the
   debug tag, the guides, the path of `bin/repro`, and the template
   `${CLAUDE_PLUGIN_ROOT}/skills/debug/templates/diagnosis.md`.
2. **On `NO REPRO`,** read the reproduction section of `diagnosis.md`, and
   ask the user for what it needs: access to an environment, a captured
   log or request, or leave to add logging. Give the answers to a fresh
   diagnoser in `reproduce` mode. On `NEEDS:`, ask whether to install the
   tool, and tell the next diagnoser. On `PERFORMANCE:`, tell the user
   `/vibes:optimise` is for that, and stop.
3. **On `RED`,** check the branches, then run `bin/repro` on `repro.sh`
   and on `minimal.sh` yourself, into `repro/phase-1` and
   `repro/phase-1-minimal`. Both must be `RED` and not `SLOW`. If not,
   give the lines to a fresh diagnoser in `reproduce` mode to tighten.
   Record both lines in the state file.

## Phase 2: Hypothesise

1. **Spawn the diagnoser in `hypothesise` mode,** with the same brief and
   the template `${CLAUDE_PLUGIN_ROOT}/skills/debug/templates/hypotheses.md`.
2. **Show the user the hypotheses,** a line each, from `hypotheses.md`:
   the claim and the prediction, in rank order. Ask, as one question,
   whether they'd re-rank them or rule any out: they often know what
   changed recently, or what they've already checked. If they do, have the
   diagnoser revise `hypotheses.md` in `hypothesise` mode with their
   answer. Unattended, keep the ranking.

## Phase 3: Probe and prove

1. **Spawn the diagnoser in `probe` mode,** with the same brief.
2. **Check the branches.**
3. **On `CONFIRMED`,** run `bin/repro` yourself on `minimal.sh` and
   `repro.sh` at the spike branch's head, into `repro/proved-minimal` and
   `repro/proved`. Both must be `GREEN`. If not, give the lines to a fresh
   diagnoser in `probe` mode. Record the cause, the proving commit and the
   seam in the state file.
4. **On `ALL REFUTED`,** go back to Phase 2 with a fresh diagnoser, which
   reads what the probes showed. After three rounds with nothing
   confirmed, show the user every hypothesis and its result, and ask how
   to go on (unattended: stop and report).

## Phase 4: The bug spec

1. **Read `diagnosis.md`.** If the proving change needed a new module,
   interface or dependency, the fix needs a design: tell the user to run
   `/vibes:vibe` with the diagnosis, and stop (unattended: report it).
2. **Create the fix branch** from the base commit:
   `git switch -c debug/<slug> <base commit>`.
3. **Write the bug spec** yourself, in the spec directory, from
   `${CLAUDE_PLUGIN_ROOT}/skills/vibe/templates/spec.md`, as the vibe skill
   writes a small task's. Its summary gives the symptom and the confirmed
   cause. Its requirements say what the correct behaviour is, for the
   minimal scenario and for every case the cause also reaches, never how
   the fix works. Its constraints name the code the fix touches. Use the
   glossary's terms, if the project has one. Resolve its open questions
   as the vibe skill's [Open questions](../vibe/SKILL.md#open-questions)
   describes, with notes in `.vibes/debug-<slug>/research/`.
4. **Review it** in `spec` rounds with `vibes:spec-reviewer` and, when
   `bin/project-docs` lists a document, `vibes:project-docs-reviewer`, as
   the vibe skill's [Review rounds](../vibe/SKILL.md#review-rounds)
   describe, in `.vibes/debug-<slug>/review/`. Decide on and fix their
   findings yourself, as for a small task's spec. Ask the user about a
   requirement that would change what they expect.
5. **Commit the approved spec** on the fix branch, with the research notes
   it cites in its `research/` directory, on its own, through the gate.

## Phase 5: Fix test-first

1. **Write the rebuild plan** yourself,
   `.vibes/debug-<slug>/rebuild-plan.md`, as the vibe skill's
   [The rebuild plan](../vibe/SKILL.md#the-rebuild-plan) describes, with
   one batch. Its first entry turns the minimal scenario into a regression
   test at the seam `diagnosis.md` names, which fails on the bug before
   the fix. Then an entry for each other requirement. Lessons: the
   proving change, as the spike's lesson, which the builder may read with
   `git show <proving commit>` but must rebuild test-first, not copy.
2. **Spawn one `vibes:builder` in `build` mode,** on the fix branch, with
   the brief the vibe skill's
   [Phase 6](../vibe/SKILL.md#phase-6-rebuild-test-first) gives, and a
   `Cause:` line: the confirmed hypothesis in a sentence, for the fix
   commit's body. Give the spike branch only for the proving change: the
   spec is the fix branch's, so the builder reads it there.
3. **When there's no seam** that reaches the bug the way it really
   happens, the plan's first entry tests at the closest one, and the final
   report flags it as a finding about the code's structure.
4. **Check the batch,** as the vibe skill's Phase 6 says.

## Phase 6: Review the fix

Run `rebuild` rounds on the fix branch, as the vibe skill's
[Review rounds](../vibe/SKILL.md#review-rounds) describe, in
`.vibes/debug-<slug>/review/`, with a fresh `vibes:builder` in `fix` mode
fixing the findings. The panel is the vibe skill's small-task panel, as
[Size the task](../vibe/SKILL.md#size-the-task) gives it: the spec, bug,
cleanliness and test reviewers, the security, performance and
resource-leak reviewers when the fix's area needs them, and the project
docs reviewer when `bin/project-docs` lists a document, less any whose
area the change can't touch. Add a line to each brief:

```text
Diagnosis: <absolute path to diagnosis.md>. This is a bug fix: the spec's
  summary gives the confirmed cause, and the first test reproduces the bug.
```

Before round 1, run `scripts/check-requirements --all` if the project has
it, and have a builder add a test for any requirement it reports. The
round limit is 5.

## Phase 7: Verify

1. **The original reproduction passes on the fix:**

   ```sh
   git worktree add --detach .vibes/debug-<slug>/wt/fix debug/<slug>
   "${CLAUDE_PLUGIN_ROOT}/bin/repro" run --tree .vibes/debug-<slug>/wt/fix \
     --out .vibes/debug-<slug>/repro/fixed -- \
     "$PWD/.vibes/debug-<slug>/repro.sh"
   git worktree remove --force .vibes/debug-<slug>/wt/fix
   ```

   It must be `GREEN`. If it isn't, give the line to a builder in `fix` mode, then review its
   change in one more `rebuild` round with the spec and bug reviewers.
2. **No debug tag is left:** `git diff <base commit>...HEAD` has no
   `vibes-debug-<slug>`. The gate refuses one, so this should hold.
3. **Check `git status` is clean** and `scripts/check --all` passes.
4. **Write a wizard for what only the user can set up:** if
   `"${CLAUDE_PLUGIN_ROOT}/bin/setup-needs" <base commit>` lists anything,
   such as an API key the fix now reads, write
   `.vibes/debug-<slug>/wizard.sh` as the wizard skill's
   [At the end of a run](../wizard/SKILL.md#at-the-end-of-a-run) says.

## Phase 8: Finish

1. Report to the user:
   - for an unattended run, every unattended decision first;
   - the wizard, if there is one, and the command to run it;
   - the symptom, and the `bin/repro` lines before and after;
   - each hypothesis, in a line: its claim, and confirmed or refuted with
     the evidence;
   - the cause, and the seam, or that there's none and why: a finding
     about the code's structure;
   - the fix branch's commits (`git log --oneline <base>..HEAD`), the spec
     directory, and every reviewer's final verdict;
   - the spike branch and the run directory, kept for reference: ask
     whether to delete the branch.
2. Set `status: done`.
3. Leave the branches where they are: push, merge or open a pull request
   only when the user asks.
