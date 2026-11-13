---
name: optimise
description: >-
  Makes a program faster where a profile shows the time goes: measures a
  baseline with real profilers, plans and specs the optimisation, tries
  candidates as spikes measured against the best so far until the gains run
  out, has the winner reviewed, then rebuilds it test-first and verifies
  the gain. Separate from /vibes:vibe, which never uses it.
argument-hint: "[unattended:] [max <n>] [area or problem to optimise]"
disable-model-invocation: true
---

# Optimise: profile, spike, measure, review, rebuild

Task: $ARGUMENTS

Make the program faster where the time really goes. A **profile** of a
representative workload shows where that is. A **plan** ranks the ideas by
how much time each can save, and a **spec** sets the targets. Each idea is
tried as a **spike** on its own branch and **measured** against the best
version so far, until the ideas stop paying. The reviewers check the
winning spike against every standard, the spec is corrected, and the spike
is set aside. Then the optimisation is **rebuilt test-first** from the spec,
and measured once more to show the gain survived.

Without a task, optimise the whole program's usual workload. With one, such
as `the CSV import` or `startup takes 4 seconds`, focus the workload and the
profile there. `max <n>` changes how many candidates are tried at most, and
`unattended:` runs without stopping to ask.

You are the main agent. You coordinate, ask the user what only they can
decide, and run `bench verdict`. Subagents measure, plan, build and review,
each writing its own records and replying in a line or two. Never read the
profiles, flame graphs, samples, harness, worktrees, candidate diffs,
reviewers' findings or the plan: read the agents' replies, `bench`'s
one-line output, your state file, and a change log row only when a decision
needs it.

## The agents

| Agent | Role |
| --- | --- |
| `vibes:profiler` | Agrees the workload, builds the harness, profiles, and measures each candidate. Never changes the code |
| `vibes:optimiser` | Plans the candidates, writes the spec, and builds each candidate spec first. Never measures |
| `vibes:designer` | Decides on review findings and corrects the spec and design, and writes the rebuild plan |
| `vibes:builder` | Rebuilds the optimisation test-first, and fixes review findings |
| The reviewers | As in `/vibes:vibe`, in the spike review and the rebuild review |

## Names

Pick a short kebab-case slug for the task, such as `csv-import`. Everything
this run makes is prefixed so it never meets a `/vibes:vibe` run's:

- **Run directory:** `.vibes/optimise-<slug>/`, which git ignores. Its state
  file is `optimise-state.md`, never `state.md`, which is vibe's.
- **Rebuild branch:** `optimise/<slug>`.
- **Candidate branches:** `spike/optimise-<slug>-<i>` for attempt `<i>`. The
  commit gate doesn't run on `spike/` branches.
- **Spec directory:** `optimise-<slug>/` in the project's spec directory,
  or in `docs/specs/` if it has none. It holds only what this run adds;
  the behaviour that must not change is referred to, not copied.
- **Worktrees:** `wt/best` and `wt/candidate` in the run directory, where
  the profiler builds and runs code.

## Rules

- **The spec comes first.** Every change in behaviour or structure goes
  into the spec, then the design if there is one, with a change log row,
  and is committed with the code that implements it. A change that would
  alter what the user asked for goes to the user first.
- **The one who optimises never measures.** The optimiser builds; the
  profiler measures; you decide with `bench verdict`.
- **No worktree exists during a gated commit,** because the project's checks
  might lint or test the copies in it. Remove them before every commit off
  a `spike/` branch:

  ```sh
  git worktree remove --force .vibes/optimise-<slug>/wt/best
  git worktree remove --force .vibes/optimise-<slug>/wt/candidate
  git worktree prune
  ```

- **One measurement at a time,** and nothing else running while the
  profiler measures: never run another agent alongside it.
- **Check the main tree after every profiler run:** `git status --porcelain`
  is as it was, and `HEAD` hasn't moved. If not, stop and tell the user.
- **Installing tools:** when the profiler reports a missing tool, ask the
  user whether to install it, with what it would show. Tell the next
  profiler the ones they allow, with the commands. Never use `sudo`.

### Unattended runs

Record an unattended run in the state file. Then, wherever this skill says
to ask the user:

- **The workload and tools:** take the profiler's choice, install nothing,
  and record each as an `Unattended decision:` in the state file, with the
  options not chosen.
- **Open questions in the spec, or a change that would alter what the user
  asked for:** choose the option that does the least the user didn't ask
  for and is easiest to change later, and record it in the spec's
  assumptions the same way.
- **A trade-off,** such as a candidate that fails a guard rail: reject it.
- **Anything that could lose the user's work:** stop, and report it.
- **A round limit:** stop, and report the outstanding findings.

The final report lists every unattended decision first.

### Keep the guides current

After every optimiser or builder report, and before every review round,
run:

```sh
git diff --name-only <base>...HEAD | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"
```

Add each new guide to the state file and every later brief. On the rebuild
branch, the next builder extends the gate for it, in a commit of its own.
For each `no guide:` file, tell the user, and have a `# No guide:` line
added to `scripts/check`; in an unattended run, list them in the report.

## The state file

Keep `.vibes/optimise-<slug>/optimise-state.md` current, from
`${CLAUDE_PLUGIN_ROOT}/skills/optimise/templates/optimise-state.md`: the
task, the user's answers, unattended or not, the base branch and its commit
(the baseline), the spec directory, the guides, the noise floor, the guard
rails, the candidates table, the phase and last step, and
`status: running` until the end, then `status: done`. Update it after every
step.

## Resume an unfinished run

Before Phase 0, look for `.vibes/optimise-*/optimise-state.md` with
`status: running`. If there's one for this task, or the task is empty,
resume it; for another task, ask the user whether to finish it first. If a
`.vibes/*/state.md` says `status: running`, a vibe run is unfinished: tell
the user, since both would use the working tree.

To resume, read the state file, check the branches and commits agree with
it (git wins), run `git worktree prune`, and carry on from the first
unfinished step. A candidate with commits but no measurement is measured
again. If the machine, its power state or the toolchain has changed, have
the profiler run aa mode again first, and measure the best version against
the baseline again before trusting old gains.

## Phase 0: Set up

1. **Understand the task,** pick the slug, and parse `unattended:` and
   `max <n>` (8 by default).
2. **Check the working tree is clean.** If it isn't, ask the user what to
   do. The current branch is the base branch, and its commit the baseline.
3. **Find the guides:** `git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"`.
4. **Create the run directory** and the state file:

   ```sh
   mkdir -p .vibes/optimise-<slug>
   printf '*\n' > .vibes/.gitignore
   ```

5. **Set up the commit gate,** if the project has no executable
   `scripts/check` or its `# Guides:` line misses a guide: spawn a
   `general-purpose` subagent with `medium` effort to follow
   `${CLAUDE_PLUGIN_ROOT}/skills/commit-gate/SKILL.md` on the base branch,
   committing the setup on its own. **Wait for it,** so nothing else runs
   while the baseline is measured. Its commit is then the baseline.

## Phase 1: Baseline

1. **Ask about the workload,** unless the task or an unattended run settles
   it: how the program is used, with what sizes of input, and what "slow"
   means to the user. Give the profiler their answers.
2. **Spawn `vibes:profiler` in `baseline` mode,** with the task, the run
   directory, the guides, the baseline commit and the answers. It builds
   the harness in `bench/`, profiles, and runs the A/A measurement.
3. **Check the main tree,** then remove the worktrees.
4. **Tell the user** the top hot spots and the noise floor in a few lines,
   and record the noise floor in the state file. If the task named an area
   and the profiler reports that most of the time is elsewhere, ask
   whether to optimise where the time is instead. Ask about any missing
   tool; if the user installs one, run baseline mode again.

## Phase 2: Plan and spec

1. **Spawn `vibes:optimiser` in `plan` mode** with the baseline profile.
2. **Create the rebuild branch:** `git switch -c optimise/<slug>`.
3. **Spawn `vibes:optimiser` in `spec` mode,** to write the goal. Ask the
   user each open question it reports, and have it write the answers in.
4. **Review the spec** in `spec` rounds with `vibes:spec-reviewer`, as
   [Review rounds](#review-rounds) describes, with `vibes:designer` in
   `revise` mode fixing the findings, until it approves.
5. **Commit the spec** on its own, through the gate. Record the guard rails
   from its quality requirements in the state file, as `bench` guards such
   as `rss_kib=10`.

## Phase 3: The spike loop

The best version starts as the head of `optimise/<slug>`. For each attempt
`<i>`, from 1:

1. **Pick the candidate:** the plan's top `proposed` one. If it needs the
   user, as the optimiser reported, ask first.
2. **Branch from the best version:**
   `git switch -c spike/optimise-<slug>-<i> <best>`.
3. **Spawn `vibes:optimiser` in `try` mode,** with the candidate, the
   attempt, the branch, the spec directory and the guides. Check its
   commits are on the branch and the tree is clean, and check the guides.
   If it reports the idea can't work, mark it so and go to step 7.
4. **Spawn `vibes:profiler` in `measure` mode:** side a the best version,
   side b the candidate's head, into `profile/candidate-<i>/`, with the
   noise directory `profile/aa/main`, the test command and the guard rails.
   Then check the main tree.
5. **Decide,** yourself, running each command on its own, with no shell
   variables, so a permission rule for `bench` matches:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/bench" verdict \
     --out .vibes/optimise-<slug>/profile/candidate-<i>/main \
     --noise .vibes/optimise-<slug>/profile/aa/main --guard <each guard rail>
   "${CLAUDE_PLUGIN_ROOT}/bin/bench" verdict \
     --out .vibes/optimise-<slug>/profile/candidate-<i>/holdout \
     --noise .vibes/optimise-<slug>/profile/aa/main
   ```

   - **Accept** it when the main verdict is `IMPROVED` with its guards ok,
     and the holdout's isn't `REGRESSED` or `BROKEN`: it becomes the best
     version.
   - **A failed guard** is a trade-off: ask the user whether to accept it,
     and if they do, the spec's guard rail changes in the next attempt.
   - **Anything else is rejected.** Its branch stays, for the record.
6. **Record the attempt** in the candidates table: attempt, candidate,
   branch, commit, the verdict line, and accepted or not.
7. **Update the plan:** spawn `vibes:optimiser` in `plan` mode with the
   candidate's `measured.md`, or the latest profile of the best version if
   it was rejected.
8. **Stop** at the first of:
   - the plan's top candidate has a bound under 5%, or there's none;
   - three attempts in a row with nothing accepted;
   - `max <n>` attempts.

   Otherwise go on with the next attempt.

When the loop stops:

1. **Measure the best version against the baseline:** spawn the profiler in
   `measure` mode, with side a the head of `optimise/<slug>` and side b the
   best version, into `profile/best/`.
2. **Settle the targets:** on the best version's branch, spawn the
   optimiser in `spec` mode to settle them from `profile/best/measured.md`
   and the noise floor. Commit the change there.

If nothing was accepted, tell the user what was tried and why it didn't
pay, and stop: there's nothing to rebuild.

## Phase 4: Review the winning spike

The best version's branch is the spike. Its code is thrown away, but its
review corrects the spec and design and gathers the lessons the rebuild
needs.

1. **Review it once,** in round `spike-1`, with `vibes:spec-reviewer`,
   `vibes:architecture-reviewer`, `vibes:bug-reviewer`,
   `vibes:security-reviewer`, `vibes:performance-reviewer`,
   `vibes:resource-leak-reviewer`, `vibes:style-reviewer`,
   `vibes:idioms-reviewer` and `vibes:cleanliness-reviewer`, less any whose
   area the change can't touch, as [Review rounds](#review-rounds) says.
   Their findings about the code become lessons for the rebuild.
2. **Correct the spec and design** on the spike branch: spawn
   `vibes:designer` in `revise` mode, in the `spike` phase, asking for
   change log entries. It sorts each finding it accepts as `spec`, `design`
   or `lesson`. Tell it a finding that would undo a measured gain is
   rejected, with the measurement as the reason, unless the gain is small
   beside what the finding costs; then it's an open question for the user.
   Commit its changes on the spike branch.
3. **Have the corrections approved:** the spec reviewer in `spec` rounds,
   then, if there's a design, the architecture reviewer in `design` rounds.
4. **Try an uncertain design change,** each one the designer can't vouch
   for without building it: a new attempt from the spike, with the
   optimiser in `try` mode given the change and its findings, then a
   measurement. It becomes the spike unless it's `BROKEN` or `REGRESSED`.
   Then run round `spike-2` with the reviewers whose findings led to it and
   the spec reviewer. There's no third round.

## Phase 5: Set the spike aside

1. **Remove the worktrees.**
2. **Save the spike's spec and design changes:**

   ```sh
   git diff optimise/<slug> <spike branch> -- <spec directory> \
     > .vibes/optimise-<slug>/spike-changes.patch
   ```

3. **Spawn `vibes:designer` in `plan` mode,** on the spike branch, to write
   `.vibes/optimise-<slug>/rebuild-plan.md`, with the spike's round
   directories, that patch, and each accepted candidate's
   `candidates/<i>.md`: what makes each one fast is a lesson for the batch
   that builds it, so the rebuild keeps the technique that measured fast.
4. **Switch to the rebuild branch:** `git switch optimise/<slug>`.

## Phase 6: Rebuild test-first

Spawn a fresh `vibes:builder` in `build` mode for each batch of the plan,
one at a time, on `optimise/<slug>`. Its brief gives the task, the branches
(the rebuild branch, the base branch, and the spike branch to read the spec
and design from with `git show`), the paths of the spec, the design and the
plan, the batch's section, its guides and any the gate doesn't check yet,
whether it's the first batch, and its report's path,
`.vibes/optimise-<slug>/build-<batch>.md`.

The first batch extends the gate for any new guide, and adds the design's
boundary rules to `scripts/check` if there's a design. The committed
benchmark is built like any other entry, with the language's own benchmark
tool, never `bin/bench`, and the gate runs it only at its small size.

After each batch, check its commits are on the rebuild branch, the tree is
clean, the plan's entries are ticked off, and `scripts/check` passes, and
check the guides.

## Phase 7: Verify the rebuild

1. **Measure it:** spawn the profiler in `aa` mode on the baseline, for a
   fresh noise floor, then in `measure` mode twice: side a the baseline and
   side b the rebuild's head, into `profile/verify-<n>-baseline/`, and side
   a the spike and side b the rebuild, into `profile/verify-<n>-spike/`.
   Remove the worktrees.
2. **Check it,** with `bench verdict` on each main size: against the
   baseline it's `IMPROVED` and its median change meets each target in the
   spec;
   against the spike it isn't `REGRESSED`. If either fails, spawn a builder
   in `fix` mode with both reports, and measure again.
3. **Review it** in `rebuild` rounds, with the panel from step 1 of Phase 4
   plus `vibes:test-reviewer`. Before round 1, run
   `scripts/check-requirements --all` if the project has it, and have a
   builder add a test for any id it reports. The brief's `Measurements:`
   line gives the latest verify reports: the spec reviewer reads the
   targets' results there rather than timing anything, and the performance
   reviewer also checks the committed benchmark's method.
4. **Measure again** after the last round that changed code, as step 1
   says, and fix the same way if it fails.

## Phase 8: Finish

1. Run `scripts/audit` if the project has one, and have a builder in `fix`
   mode fix what it finds.
2. Check `git status` is clean and `scripts/check` passes.
3. Report to the user:
   - for an unattended run, every unattended decision first;
   - the workload, and a table of the baseline against the final rebuild:
     wall time, CPU time and peak memory for each size, with the change and
     its interval, and each target met;
   - every attempt: the candidate, its verdict, and accepted or not;
   - the rebuild branch's commits (`git log --oneline <base>..HEAD`), the
     spec directory, and each change to the spec after it was approved;
   - every reviewer's final verdict, and any deferred findings;
   - the spike branches and the run directory, kept for reference: ask
     whether to delete the branches.
4. Set `status: done`.
5. Don't push, merge or open a pull request unless the user asks.

## Review rounds

A round reviews one phase, `spec`, `design`, `spike` or `rebuild`, in
`.vibes/optimise-<slug>/review/<phase>-<round>/`.

1. **Prepare the round directory.** For the spike and rebuild phases, save
   the change, against `optimise/<slug>` for the spike and the base branch
   for the rebuild:

   ```sh
   git diff <base>...HEAD > <round directory>/diff.patch
   git diff --name-only <base>...HEAD > <round directory>/files.txt
   git rev-parse HEAD > <round directory>/head.txt
   ```

   From round 2, copy the previous round's findings files and
   `responses.md` in without reading them, and for each round `<k>` a
   reviewer last ran in, save `changes-since-<k>.patch` and
   `changed-files-since-<k>.txt` from that round's `head.txt` to `HEAD`.
2. **Choose the panel** by area, from `guides-for` on `files.txt`: the spec
   and security reviewers always; the bug, cleanliness, style, idioms and
   test reviewers for a file that needs a guide; the architecture and
   resource-leak reviewers for a file that needs a guide in `languages/`;
   the performance reviewer for one in `languages/`, `web/`, `build/` or
   `tools/`, or a query or schema guide in `data/`. Write the panel to
   `panel.md`, with each reviewer left out and why.
3. **Spawn the panel in a single message,** each with this brief:

   ```text
   Task: <the task, and the user's answers>
   Spec: <absolute path to spec.md>
   Design: <absolute path to design.md, or none>
   Review directory: <absolute path to the round directory>
   Phase: <spec, design, spike or rebuild>
   Guides: <guides>
   Round: <n>
   Changes: <from round 2: the changes-since files for this reviewer>
   Measurements: <for the spike: each accepted candidate's candidates/<i>.md
     and profile report; for the rebuild: the latest verify reports>
   Rules:
   - This is a performance optimisation. A change that measured faster is
     intended: weigh what it costs in clarity against the measured gain,
     and never ask to undo a gain without saying what that would cost.
   ```

4. **Each reviewer writes** `<reviewer>.md` in the round directory and
   replies with its verdict and counts. Don't read the findings.
5. **Have them decided on and fixed:** a fresh `vibes:designer` in `revise`
   mode for the spec, design and spike phases, or `vibes:builder` in `fix`
   mode for the rebuild. Ask the user about anything it leaves to you, and
   give the answers to a fresh fixer.
6. **The next round** runs only the reviewers that requested changes, until
   all approve. In the rebuild, a last round then runs the spec reviewer
   and each reviewer that approved before a fix to a BLOCKER or MAJOR
   finding changed code in its area.
7. **Round limits:** 3 for the spec and design, 5 for the rebuild, and the
   spike's two. At a limit, show the user the outstanding findings and
   where the reviewers and the fixer disagree, and ask how to go on.
