---
name: vibe
description: >-
  Runs the clean vibe-coding workflow for a task: a complete spec and a design
  are written and reviewed first, a subagent spikes the solution to them, a
  panel of reviewer subagents critiques it until all approve and the spec is
  verified, then the task is rebuilt test-first in atomic, gated commits and
  reviewed again.
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

`.vibes/spec.md` is the single source of truth for what the task does, and
`.vibes/design.md` for how its code is structured.

- **The spec is complete and approved before the design starts,** and the
  design is approved before any code is written.
- **Every change goes into the spec first.** A review finding that changes
  behaviour, an edge case found while building, a change the user asks for:
  each is written into the spec, with a change log entry, before any code
  changes. If it changes the structure, the design is updated next. Only
  then does the code change.
- **No code does anything the spec doesn't describe.**
- **If a change would alter what the user asked for,** ask the user before
  writing it into the spec.
- **The spec reviewer checks every spec change** in the next review round,
  along with the code.
- **The spike is accepted only when the spec reviewer verifies it meets
  every requirement,** and so is the rebuild.

## Phase 0: Set up

1. **Understand the task.** If the task is unclear or missing, ask the user
   before doing anything else. Pick a short kebab-case name for it, such as
   `order-export`. The spike branch is `spike/<name>` and the rebuild branch
   is `vibe/<name>`.
2. **Check the working tree is clean** with `git status`. If it isn't, ask
   the user what to do with the changes. Note the current branch: it's the
   base branch.
3. **Find the languages** the task will touch, and read `coding-style.md`,
   `idioms.md` and `tools.md` for each from `${CLAUDE_PLUGIN_ROOT}/lang/`.
4. **Make sure the commit gate is set up.** If the project has no executable
   `scripts/check`, follow the [commit gate](../commit-gate/SKILL.md) skill
   first. Then run `scripts/check` on the base branch and confirm it passes.
   Commit the gate setup on the base branch as one commit of its own, so the
   spike and rebuild branches both start with it, and list it in the final
   report.
5. **Create the state directory** `.vibes/` for the spec, the design and
   review files. A `.gitignore` inside it keeps the whole directory out of
   git, without touching the project's own `.gitignore` or anything in
   `.git/`:

   ```sh
   mkdir -p .vibes
   printf '*\n' > .vibes/.gitignore
   ```

## Review rounds

Every review in the workflow runs in rounds, the same way. A round reviews
one phase: `spec`, `design`, `spike` or `rebuild`.

1. **Prepare the round directory,** `.vibes/review/<phase>-<round>/` (for
   example `.vibes/review/spike-1/`). Copy in `.vibes/spec.md`, and
   `.vibes/design.md` once it exists. In the spike and rebuild phases, add
   the change:

   ```sh
   git diff <base>...HEAD > .vibes/review/spike-1/diff.patch
   git diff --name-only <base>...HEAD > .vibes/review/spike-1/files.txt
   ```

   From round 2 on, copy the previous round's findings files and
   `responses.md` into the new directory.
2. **Spawn every reviewer for the round in a single message**, so they run in
   parallel. In round 1 every reviewer for the phase runs. In later rounds,
   only the reviewers that requested changes run again. Give each one a
   brief:

   ```text
   Task: <the task, and the user's answers to any questions>
   Review directory: <absolute path to .vibes/review/spike-1>
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
   tests, then commit the fixes.
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

1. Spawn `vibes:designer` in `spec` mode, with the task, the absolute path
   of `.vibes/` and the languages.
2. **Resolve every open question.** Ask the user each one in the spec's
   open questions section, then write their answers into the spec as
   requirements, and empty the section.
3. **Review the spec** in rounds with `vibes:spec-reviewer`, fixing its
   findings in `spec.md`, until it approves.

## Phase 2: Design

1. Spawn `vibes:designer` in `design` mode, with the same brief.
2. **Review the design** in rounds with `vibes:architecture-reviewer`,
   fixing its findings in `design.md`, until it approves. A finding that
   shows the spec is wrong or incomplete goes back into the spec first, and
   the spec reviewer approves the changed spec in a `spec` round before the
   design rounds go on.

## Phase 3: Spike

1. Create the spike branch from the base branch:
   `git switch -c spike/<name>`.
2. Spawn `vibes:spiker` with a brief giving the task, the spike branch, the
   base branch, the absolute paths of `.vibes/spec.md` and `.vibes/design.md`,
   and the languages.
3. Save its report to `.vibes/spike-report.md`. Check the spike's commits are
   on `spike/<name>`, and that the working tree is clean. If the spiker
   changed the spec or design, read each change log entry, and ask the user
   about any that alters what they asked for.

## Phase 4: Review the spike

Run review rounds in the `spike` phase with every reviewer except
`vibes:test-reviewer`, fixing findings on the spike branch, until every
reviewer approves. The spec reviewer's final verdict must be `APPROVED`,
with every requirement met: that's the verification that the spike
satisfies the spec.

## Phase 5: Set the spike aside

The approved spike is a reference implementation, never production code. It
stays on `spike/<name>` and is never merged.

1. Write `.vibes/rebuild-plan.md`:
   - **Test list:** every requirement and quality id in the spec, broken
     into behaviours to test, ordered from simplest to hardest. Each entry
     names the ids it covers, and every id appears at least once.
   - **Lessons:** what the review rounds changed, so the rebuild gets it right
     first time.
2. Switch back to the base branch and create the rebuild branch:
   `git switch <base> && git switch -c vibe/<name>`.

## Phase 6: Rebuild test-first

Follow the [test-driven development](../test-driven-development/SKILL.md)
skill, using the test list from `.vibes/rebuild-plan.md`, and the
[atomic commits](../atomic-commits/SKILL.md) skill for every commit.

- **Build to the spec and design.** They're the source of truth, not the
  spike.
- **Rewrite, don't copy.** Write each piece fresh, driven by its test. You may
  read the spike for reference (`git show spike/<name>:<path>`), but never
  paste spike code into the rebuild.
- **Small steps.** One behaviour at a time: red, green, refactor, commit.
- **The gate runs on every commit.** It runs `scripts/check`, and refuses
  unstaged and untracked changes. When it blocks a commit, fix the cause and
  commit again. Never bypass it.
- **Keep the plan current.** Tick off each behaviour in the test list as it's
  committed. A new behaviour goes into the spec first, then the test list,
  then a test.

## Phase 7: Review the rebuild

Run review rounds in the `rebuild` phase on the rebuild branch, with all
reviewers, including `vibes:test-reviewer`. Fix findings the same way as the
rebuild: the spec first for any change in behaviour, then a failing test,
then the fix, as atomic commits through the gate. The spec reviewer's final
verdict must be `APPROVED`, with every requirement met and tested.

## Phase 8: Finish

1. Run `scripts/audit` if the project has one, and fix what it finds the same
   way.
2. Check `git status` is clean and `scripts/check` passes.
3. Report to the user:
   - the rebuild branch and its commits (`git log --oneline <base>..HEAD`)
   - the spec and design in `.vibes/`, every change made to the spec after
     it was approved, and the spec reviewer's final coverage
   - every reviewer's final verdict, and any deferred MINOR findings
   - the spike branch, kept for reference: ask whether to delete it
4. Don't push, merge or open a pull request unless the user asks.
