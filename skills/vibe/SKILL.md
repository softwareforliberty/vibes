---
name: vibe
description: >-
  Runs the clean vibe-coding workflow for a task, scaled to its size: a
  complete spec, and for larger tasks a design, are written and reviewed
  first; large tasks are spiked and critiqued by a panel of reviewer
  subagents; then the task is built test-first in atomic, gated commits,
  reviewed and verified against the spec.
argument-hint: "[task]"
disable-model-invocation: true
---

# Vibe: spec, design, spike, review, rebuild

Task: $ARGUMENTS

Build the task from a complete spec. First the **spec** says everything the
task must do, and the **design** says how the code will be structured, and
each is reviewed until it's approved. Then a fast **spike** builds the design,
and a panel of reviewers critiques it until every reviewer is satisfied and
the spike is verified to meet the whole spec. Then the spike is set aside and
the task is **rebuilt test-first**, one atomic, gated commit at a time, and
reviewed and verified again.

That's the full workflow, for large tasks. Smaller tasks skip the parts they
don't need, as [Size the task](#size-the-task) describes, but every task gets
a spec first, a test-first build through the gate, and a review that
verifies it against the spec.

You are the main agent. You coordinate, resolve open questions with the
user, fix review findings and do the rebuild. Subagents write the spec and
design, build the spike and do the reviews.

## The agents

| Agent | Role |
| --- | --- |
| `vibes:designer` | Writes the spec, then the design |
| `vibes:spiker` | Builds the spike to the spec and design |
| `vibes:spec-reviewer` | The spec's completeness, then whether the code meets it |
| `vibes:architecture-reviewer` | The design, then module boundaries, coupling, API design |
| `vibes:cleanliness-reviewer` | Readability, naming, size, duplication, dead code, principles |
| `vibes:style-reviewer` | Each language's `coding-style.md` |
| `vibes:idioms-reviewer` | The most idiomatic approach in each language |
| `vibes:resource-leak-reviewer` | Memory and resource leaks |
| `vibes:performance-reviewer` | Complexity, I/O and wasted work |
| `vibes:bug-reviewer` | Bugs, edge cases and error handling |
| `vibes:security-reviewer` | Injection, access control, secrets and more |
| `vibes:test-reviewer` | Test quality (final review only) |

Outside the plugin, the same definitions are in this repo's `agents/`
directory, without the `vibes:` prefix.

## The spec comes first

The spec is the single source of truth for what the task does, and the
design for how its code is structured. Both are part of the project: they
live in its repository, in the spec directory, and are committed with the
code.

- **The spec is complete and approved before the design starts,** and the
  design is approved before any code is written.
- **Every change goes into the spec first.** A review finding that changes
  behaviour, an edge case found while building, a change the user asks for:
  each is written into the spec, with a change log entry, before any code
  changes. If it changes the structure, the design is updated next, the
  same way. Only then does the code change.
- **A spec change is committed with its implementation.** The spec and
  design changes go in the same commit as the code and tests that implement
  them, so each commit shows what changed, why, and how it was built. Only
  the first approved spec and design, which nothing implements yet, are
  committed on their own.
- **No code does anything the spec doesn't describe.**
- **If a change would alter what the user asked for,** ask the user before
  writing it into the spec.
- **The spec reviewer checks every spec change** in the next review round,
  along with the code.
- **The spike is accepted only when the spec reviewer verifies it meets
  every requirement,** and so is the rebuild.

## Size the task

| Size | For | Phases |
| --- | --- | --- |
| Small | A fix or one behaviour in existing code, with no new module, interface or dependency | Spec, build, review |
| Medium | A feature across a few modules, whose design is clear | Spec, design, build, review |
| Large | A new application, subsystem or interface, or a task whose design is uncertain | Spec, design, spike, rebuild, review |

- **Pick the size** from the task and the code it touches, and tell the
  user which size and why. If the user names a size, use it. When it's
  between two sizes, pick the larger.
- **Move up a size when the work shows the task is bigger,** and tell the
  user. A small task that needs a new module, interface or dependency gets a
  design. A medium task whose design proves uncertain gets a spike.
- **A small task has no designer and no design document.** You write the
  spec yourself, in the format of the designer's spec mode in
  `${CLAUDE_PLUGIN_ROOT}/agents/designer.md`, with only the sections that
  apply. Its constraints section names the code the change touches.
- **The review panel depends on the size.** Medium and large tasks get every
  reviewer. A small task gets `vibes:spec-reviewer`, `vibes:bug-reviewer`,
  `vibes:cleanliness-reviewer` and `vibes:test-reviewer`, and also:
  - `vibes:security-reviewer` when the change handles outside input,
    authentication, secrets, files or commands;
  - `vibes:performance-reviewer` when it's on a hot path or handles large
    data;
  - `vibes:resource-leak-reviewer` when it acquires memory, files,
    connections, locks or threads.

## Keep the state current

Keep `.vibes/<name>/state.md` current, so an interrupted run can carry on
where it stopped. Update it when a phase starts or ends, after every review
round, and after every commit. It holds:

- the task as the user gave it, their answers to open questions, and the
  task's name and size;
- the base branch, the spec directory and the languages;
- the current phase and round, and the last step finished;
- `status: running` until Phase 8 ends, then `status: done`.

## Resume an unfinished run

Before Phase 0, look for a `.vibes/*/state.md` with `status: running`.

- **There's none:** start at Phase 0.
- **There's one, and the task is empty or the same task:** resume it.
- **There's one, for a different task:** ask the user whether to finish it
  first, or set it aside and start the new one.

To resume:

1. **Read where the run stopped:** `state.md`, the spec and design, the
   rebuild plan and the latest round directory. Tell the user which phase
   and step you're resuming from.
2. **Check git agrees.** The branches exist, the right one is checked out,
   and its latest commits match the state. Where they disagree, git is
   right: update `state.md` to match.
3. **Look at uncommitted changes.** On the rebuild branch they're usually an
   unfinished red, green or refactor step: finish it if the test list shows
   which entry it belongs to, and ask the user otherwise. Never discard
   changes without asking.
4. **Carry on from the first unfinished step:**
   - in a review round with findings files missing, run only the missing
     reviewers, with the same brief;
   - when the designer or the spiker didn't report, run it again, and tell
     it what already exists so it carries on rather than starting over;
   - in the build, carry on with the first entry in the test list that
     isn't ticked off.

## Phase 0: Set up

1. **Understand the task.** If the task is unclear or missing, ask the user
   before doing anything else. Pick a short kebab-case name for it, such as
   `order-export`. The rebuild branch is `vibe/<name>` and the spike branch
   is `spike/<name>`.
2. **Check the working tree is clean** with `git status`. If it isn't, ask
   the user what to do with the changes. Note the current branch: it's the
   base branch.
3. **Find the languages** the task will touch, and read `coding-style.md`,
   `idioms.md` and `tools.md` for each from `${CLAUDE_PLUGIN_ROOT}/lang/`.
4. **Size the task,** as [Size the task](#size-the-task) describes, and tell
   the user the size.
5. **Make sure the commit gate is set up.** If the project has no executable
   `scripts/check`, follow the [commit gate](../commit-gate/SKILL.md) skill
   first. Then run `scripts/check` on the base branch and confirm it passes.
   Commit the gate setup on the base branch as one commit of its own, so the
   spike and rebuild branches both start with it, and list it in the final
   report.
6. **Choose the spec directory,** where the task's `spec.md` and
   `design.md` will live in the repository. If the project already keeps
   specs or design documents somewhere, use a directory for the task there.
   Otherwise use `docs/specs/<name>/`.
7. **Create the task's state directory** `.vibes/<name>/` for the
   workflow's own working files: the run's state, review rounds, the spike
   report and the rebuild plan. A `.gitignore` in `.vibes/` keeps it all out
   of git, without touching the project's own `.gitignore` or anything in
   `.git/`:

   ```sh
   mkdir -p .vibes/<name>
   printf '*\n' > .vibes/.gitignore
   ```

   Then write `.vibes/<name>/state.md`, as
   [Keep the state current](#keep-the-state-current) describes.

## Review rounds

Every review in the workflow runs in rounds, the same way. A round reviews
one phase: `spec`, `design`, `spike` or `rebuild`.

1. **Prepare the round directory,** `.vibes/<name>/review/<phase>-<round>/`
   (for example `.vibes/<name>/review/spike-1/`). In the spike and rebuild
   phases, save the change in it:

   ```sh
   git diff <base>...HEAD > .vibes/<name>/review/spike-1/diff.patch
   git diff --name-only <base>...HEAD > .vibes/<name>/review/spike-1/files.txt
   ```

   From round 2 on, copy the previous round's findings files and
   `responses.md` into the new directory.
2. **Spawn every reviewer for the round in a single message**, so they run in
   parallel. In round 1 every reviewer for the phase runs. In later rounds,
   only the reviewers that requested changes run again. Give each one a
   brief:

   ```text
   Task: <the task, and the user's answers to any questions>
   Spec: <absolute path to spec.md>
   Design: <absolute path to design.md, once it exists>
   Review directory: <absolute path to .vibes/<name>/review/spike-1>
   Phase: <spec, design, spike or rebuild>
   Languages: <languages>
   Round: <n>
   ```

3. **Save each reply** to `findings-<reviewer>.md` in the round directory,
   for example `findings-security-reviewer.md`.
4. **Work through the findings** of every reviewer whose verdict is
   `CHANGES REQUESTED`, most severe first:
   - Fix every BLOCKER and MAJOR finding.
   - Fix MINOR findings when they're cheap and in scope.
   - If a finding is wrong, don't change anything. Reject it, with a reason
     based on the spec, the code or the standards.
   - A fix that changes behaviour goes into the spec first, as
     [The spec comes first](#the-spec-comes-first) says.
5. **Record a response to every finding** in the round's `responses.md`:
   `fixed`, `rejected: <reason>` or `deferred: <reason>` (MINOR only).
6. **Check the fixes.** In the spike and rebuild phases, run the code and
   tests, then commit the fixes, each with the spec and design changes it
   implements.
7. **Start the next round** with only the reviewers that requested changes.
8. **Repeat** until every reviewer's latest verdict is `APPROVED`. Then, if
   anything changed after a reviewer approved it, run that reviewer once
   more to confirm the later changes didn't break its area. The spec
   reviewer always runs in the last round of the spike and rebuild phases,
   so its final verdict covers the final code.
9. **Stop at the round limit:** 3 rounds for the spec and design, and 5 for
   the spike and rebuild. If any reviewer still requests changes, stop and
   show the user the outstanding findings, your responses, and where the
   reviewers and you disagree. Ask how to proceed.

## Phase 1: Spec

1. Create the rebuild branch from the base branch:
   `git switch -c vibe/<name>`. The spec and design are committed here, so
   the spike and the rebuild both start from them.
2. Spawn `vibes:designer` in `spec` mode, with the task, the absolute path
   of the spec directory and the languages. For a small task, write the spec
   yourself instead.
3. **Resolve every open question.** Ask the user each one in the spec's
   open questions section, then write their answers into the spec as
   requirements, and empty the section.
4. **Review the spec** in rounds with `vibes:spec-reviewer`, fixing its
   findings in `spec.md`, until it approves.
5. **Commit the approved spec** on its own, through the gate.

## Phase 2: Design

Medium and large tasks only.

1. Spawn `vibes:designer` in `design` mode, with the same brief.
2. **Review the design** in rounds with `vibes:architecture-reviewer`,
   fixing its findings in `design.md`, until it approves. A finding that
   shows the spec is wrong or incomplete goes back into the spec first, and
   the spec reviewer approves the changed spec in a `spec` round before the
   design rounds go on.
3. **Commit the approved design,** together with any spec changes the
   design review made.

## Phase 3: Spike

Large tasks only. Small and medium tasks go straight to
[Phase 6](#phase-6-rebuild-test-first).

1. Create the spike branch from the rebuild branch, so it starts with the
   spec and design: `git switch -c spike/<name>`.
2. Spawn `vibes:spiker` with a brief giving the task, the spike branch, the
   base branch, the absolute paths of `spec.md` and `design.md`, and the
   languages.
3. Save its report to `.vibes/<name>/spike-report.md`. Check the spike's
   commits are on `spike/<name>`, and that the working tree is clean. If the
   spiker changed the spec or design, read each change log entry, and ask
   the user about any that alters what they asked for.

## Phase 4: Review the spike

Large tasks only.

Run review rounds in the `spike` phase with every reviewer except
`vibes:test-reviewer`, fixing findings on the spike branch, until every
reviewer approves. The spec reviewer's final verdict must be `APPROVED`,
with every requirement met: that's the verification that the spike
satisfies the spec.

## Phase 5: Set the spike aside

Large tasks only.

The approved spike is a reference implementation, never production code. It
stays on `spike/<name>` and is never merged.

1. Write `.vibes/<name>/rebuild-plan.md`:
   - **Test list:** every requirement and quality id in the spec as the
     spike phase left it, broken into behaviours to test, ordered from
     simplest to hardest. Each entry names the ids it covers, and every id
     appears at least once.
   - **Lessons:** what the review rounds changed, so the rebuild gets it right
     first time.
   - **Spec changes:** each change log entry the spike phase added to the
     spec or design, with the test list entry whose commit will bring it
     over. List them from
     `git diff vibe/<name> spike/<name> -- <spec directory>`.
2. Switch to the rebuild branch: `git switch vibe/<name>`.

## Phase 6: Rebuild test-first

Follow the [test-driven development](../test-driven-development/SKILL.md)
skill, using the test list from `.vibes/<name>/rebuild-plan.md`, and the
[atomic commits](../atomic-commits/SKILL.md) skill for every commit.

For a small or medium task, this is the first build, on the rebuild branch
from Phase 1. Write `.vibes/<name>/rebuild-plan.md` first, with the test
list from the spec as Phase 5 describes; there are no lessons or spec
changes from a spike to list. Where there was no spike, the steps below that
mention one don't apply.

- **Build to the spec and design,** which are the source of truth. For a
  large task, that's the spec and design as the spike phase left them, on
  `spike/<name>`, not the spike's code.
- **Rewrite, don't copy.** Write each piece fresh, driven by its test. You may
  read the spike for reference (`git show spike/<name>:<path>`), but never
  paste spike code into the rebuild.
- **Enforce the boundaries first.** Where the task has a design, the first
  commit of the build adds its boundary rules to `scripts/check`, as
  architecture tests or build structure from each language's `tools.md`, so
  the gate holds every later commit to them.
- **Small steps.** One behaviour at a time: red, green, refactor, commit.
- **The gate runs on every commit.** It runs `scripts/check`, and refuses
  unstaged and untracked changes. When it blocks a commit, fix the cause and
  commit again. Never bypass it.
- **Bring the spike's spec changes over with their code.** Each spec and
  design change from the spike phase goes into the commit that implements
  it, as the rebuild plan lists. By the end of the rebuild, the spec and
  design hold every change from the spike phase.
- **Keep the plan current.** Tick off each behaviour in the test list as it's
  committed. A new behaviour goes into the spec first, then the test list,
  then a test, and the spec change is committed with that test and its
  code.

## Phase 7: Review the rebuild

Run review rounds in the `rebuild` phase on the rebuild branch, with the
panel for the task's size from [Size the task](#size-the-task), including
`vibes:test-reviewer`. Fix findings the same way as the
rebuild: the spec first for any change in behaviour, then a failing test,
then the fix, committed together as atomic commits through the gate. The
spec reviewer's final verdict must be `APPROVED`, with every requirement met
and tested.

## Phase 8: Finish

1. Run `scripts/audit` if the project has one, and fix what it finds the same
   way.
2. Check `git status` is clean and `scripts/check` passes.
3. Report to the user:
   - the task's size, and any move to a larger size, with why
   - the rebuild branch and its commits (`git log --oneline <base>..HEAD`)
   - the spec and design in the spec directory, every change made to the
     spec after it was approved, and the spec reviewer's final coverage
   - every reviewer's final verdict, and any deferred MINOR findings
   - for a large task, the spike branch, kept for reference: ask whether to
     delete it
4. Set `status: done` in `state.md`.
5. Don't push, merge or open a pull request unless the user asks.
