---
name: vibe
description: >-
  Runs the clean vibe-coding workflow for a task: a subagent spikes the whole
  solution, a panel of reviewer subagents critiques it until all approve, then
  the task is rebuilt test-first in atomic, gated commits and reviewed again.
argument-hint: "[task]"
disable-model-invocation: true
---

# Vibe: spike, review, rebuild

Task: $ARGUMENTS

Build the task in two passes. First a fast **spike** finds the design, and a
panel of reviewers critiques it until every reviewer is satisfied. Then the
spike is set aside and the task is **rebuilt test-first**, one atomic, gated
commit at a time, and reviewed again.

You are the main agent. You coordinate, fix review findings and do the
rebuild. Subagents do the spike and the reviews.

## The agents

| Agent | Role |
| --- | --- |
| `vibes:spiker` | Builds the spike |
| `vibes:architecture-reviewer` | Module boundaries, coupling, API design |
| `vibes:cleanliness-reviewer` | Readability, naming, size, duplication, dead code |
| `vibes:style-reviewer` | Each language's `coding-style.md` |
| `vibes:idioms-reviewer` | The most idiomatic approach in each language |
| `vibes:resource-leak-reviewer` | Memory and resource leaks |
| `vibes:performance-reviewer` | Complexity, I/O and wasted work |
| `vibes:bug-reviewer` | Bugs, edge cases and error handling |
| `vibes:security-reviewer` | Injection, access control, secrets and more |
| `vibes:test-reviewer` | Test quality (final review only) |

Outside the plugin, the same definitions are in this repo's `agents/`
directory, without the `vibes:` prefix.

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
5. **Create the state directory** `.vibes/` for review files. A
   `.gitignore` inside it keeps the whole directory out of git, without
   touching the project's own `.gitignore` or anything in `.git/`:

   ```sh
   mkdir -p .vibes
   printf '*\n' > .vibes/.gitignore
   ```

## Phase 1: Spike

1. Create the spike branch from the base branch:
   `git switch -c spike/<name>`.
2. Spawn `vibes:spiker` with a brief giving the task, the spike branch, the
   base branch and the languages.
3. Save its report to `.vibes/spike-report.md`. Check the spike's commits are
   on `spike/<name>`, and that the working tree is clean.

## Phase 2: Review the spike

Each round of reviews works the same way, in both this phase and the final
review.

1. **Prepare the round directory**, `.vibes/review/<phase>-<round>/` (for
   example `.vibes/review/spike-1/`):

   ```sh
   git diff <base>...HEAD > .vibes/review/spike-1/diff.patch
   git diff --name-only <base>...HEAD > .vibes/review/spike-1/files.txt
   ```

   From round 2 on, copy the previous round's findings files and
   `responses.md` into the new directory.
2. **Spawn every reviewer for the round in a single message**, so they run in
   parallel. The spike review uses all reviewers except
   `vibes:test-reviewer`. In round 1 every reviewer runs. In later rounds,
   only the reviewers that requested changes run again. Give each one a
   brief:

   ```text
   Task: <the task>
   Review directory: <absolute path to .vibes/review/spike-1>
   Languages: <languages>
   Round: <n>
   ```

3. **Save each reply** to `findings-<reviewer>.md` in the round directory,
   for example `findings-security-reviewer.md`.

## Phase 3: Fix until every reviewer approves

1. **Work through the findings** of every reviewer whose verdict is
   `CHANGES REQUESTED`, most severe first:
   - Fix every BLOCKER and MAJOR finding.
   - Fix MINOR findings when they're cheap and in scope.
   - If a finding is wrong, don't change the code. Reject it, with a reason
     based on the code or the standards.
2. **Record a response to every finding** in the round's `responses.md`:
   `fixed`, `rejected: <reason>` or `deferred: <reason>` (MINOR only).
3. **Run the code and tests** to check the fixes, then commit them to the
   spike branch.
4. **Start the next review round** (Phase 2) with only the reviewers that
   requested changes.
5. **Repeat** until every reviewer's latest verdict is `APPROVED`. Then, if
   the code changed after a reviewer approved it, run that reviewer once more
   to confirm the later fixes didn't break its area.
6. **Stop after 5 rounds.** If any reviewer still requests changes, stop and
   show the user the outstanding findings, your responses, and where the
   reviewers and you disagree. Ask how to proceed.

## Phase 4: Set the spike aside

The approved spike is a reference design, never production code. It stays on
`spike/<name>` and is never merged.

1. Write `.vibes/rebuild-plan.md`:
   - **Design:** the approved design, in a few sentences.
   - **Test list:** every behaviour to build, ordered from simplest to
     hardest. Start from the spiker's behaviour list, and add every edge case
     and error case the reviewers raised.
   - **Lessons:** what the review rounds changed, so the rebuild gets it right
     first time.
2. Switch back to the base branch and create the rebuild branch:
   `git switch <base> && git switch -c vibe/<name>`.

## Phase 5: Rebuild test-first

Follow the [test-driven development](../test-driven-development/SKILL.md)
skill, using the test list from `.vibes/rebuild-plan.md`, and the
[atomic commits](../atomic-commits/SKILL.md) skill for every commit.

- **Rewrite, don't copy.** Write each piece fresh, driven by its test. You may
  read the spike for design reference (`git show spike/<name>:<path>`), but
  never paste spike code into the rebuild.
- **Small steps.** One behaviour at a time: red, green, refactor, commit.
- **The gate runs on every commit.** It runs `scripts/check`, and refuses
  unstaged and untracked changes. When it blocks a commit, fix the cause and
  commit again. Never bypass it.
- **Keep the plan current.** Tick off each behaviour in the test list as it's
  committed, and add any new behaviour you discover.

## Phase 6: Review the rebuild

Run the review rounds again (Phases 2 and 3) on the rebuild branch, with the
round directories named `rebuild-<round>`, and all reviewers, including
`vibes:test-reviewer`.

Fix findings the same way as the rebuild: a failing test first for any
change in behaviour, then the fix, as atomic commits through the gate. The
5-round limit applies again.

## Phase 7: Finish

1. Run `scripts/audit` if the project has one, and fix what it finds the same
   way.
2. Check `git status` is clean and `scripts/check` passes.
3. Report to the user:
   - the rebuild branch and its commits (`git log --oneline <base>..HEAD`)
   - every reviewer's final verdict, and any deferred MINOR findings
   - the spike branch, kept for reference: ask whether to delete it
4. Don't push, merge or open a pull request unless the user asks.
