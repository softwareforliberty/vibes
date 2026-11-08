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
and a panel of reviewers critiques it once, to find where the spec, the
design and the code fall short. The spec and design are corrected and
approved again, and the spike is set aside. Then the task is **rebuilt
test-first** from them, one atomic, gated commit at a time, and reviewed and
verified against the spec.

That's the full workflow, for large tasks. Smaller tasks skip the parts they
don't need, as [Size the task](#size-the-task) describes, but every task gets
a spec first, a test-first build through the gate, and a review that
verifies it against the spec.

You are the main agent. You coordinate, resolve open questions with the
user, and decide what the subagents can't. Subagents set up the gate,
write the spec and design, build the spike and the task, do the reviews,
and decide on and fix the findings. Each writes its own records, such as
its findings or its report, and replies in a line or two. Leave the code,
the documents and those records to them, and read one only when a
decision needs it, so your context stays small for the whole run: it
carries every phase, and the details belong in theirs.

## The agents

| Agent | Role |
| --- | --- |
| `vibes:designer` | Writes the spec, then the design, decides on their review findings and revises them, and writes the rebuild plan |
| `vibes:spiker` | Builds the spike to the spec and design, and tries out a design change the spike review makes |
| `vibes:builder` | Builds the task test-first, a batch at a time, and decides on and fixes its review findings |
| `vibes:spec-reviewer` | The spec's completeness, then whether the code meets it |
| `vibes:architecture-reviewer` | The design, then module boundaries, coupling, API design |
| `vibes:cleanliness-reviewer` | Readability, naming, size, duplication, dead code, principles |
| `vibes:style-reviewer` | Each guide's `coding-style.md` |
| `vibes:idioms-reviewer` | The most idiomatic approach in each language, format and tool |
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
- **The spike's review corrects the spec and design before the rebuild.**
  Every finding that changes behaviour or structure goes into them, and
  they're approved again, so the rebuild starts from a design the spike has
  tested.
- **The rebuild is accepted only when the spec reviewer verifies it meets
  every requirement.**

## Size the task

| Size | For | Phases |
| --- | --- | --- |
| Small | A fix or one behaviour in existing code, with no new module, interface or dependency | Spec, build, review |
| Medium | A feature across a few modules, or a small new program such as a command-line tool, whose design is clear | Spec, design, build, review |
| Large | A new application or subsystem with several parts, or a task whose design is uncertain | Spec, design, spike, rebuild, review |

- **Pick the size** from the task and the code it touches, and tell the
  user which size and why. If the user names a size, use it. When it's
  between two sizes, pick the larger, unless the only doubt is the size of
  a design that's clear: the spike is for uncertainty, not for size.
- **Move up a size when the work shows the task is bigger,** and tell the
  user. A small task that needs a new module, interface or dependency gets a
  design. A medium task whose design proves uncertain gets a spike.
- **A small task has no designer and no design document.** You write the
  spec yourself, from the template in
  `${CLAUDE_PLUGIN_ROOT}/skills/vibe/templates/spec.md`, writing "None."
  under the sections that don't apply. Its constraints section names the
  code the change touches.
- **The review panel depends on the size.** Medium and large tasks get every
  reviewer. A small task gets `vibes:spec-reviewer`, `vibes:bug-reviewer`,
  `vibes:cleanliness-reviewer` and `vibes:test-reviewer`, and also:
  - `vibes:security-reviewer` when the change handles outside input,
    authentication, secrets, files or commands;
  - `vibes:performance-reviewer` when it's on a hot path or handles large
    data;
  - `vibes:resource-leak-reviewer` when it acquires memory, files,
    connections, locks or threads.
- **Then leave out reviewers whose area the change can't touch,** at every
  size, in the spike and rebuild reviews. Run `guides-for` on the round's
  `files.txt`, and keep each reviewer only when the change has:

  | Reviewer | Kept when the change has |
  | --- | --- |
  | `vibes:spec-reviewer`, `vibes:security-reviewer` | Anything |
  | `vibes:bug-reviewer`, `vibes:cleanliness-reviewer`, `vibes:style-reviewer`, `vibes:idioms-reviewer` | A file that needs a guide |
  | `vibes:test-reviewer` | A file that needs a guide, in a rebuild review |
  | `vibes:architecture-reviewer` | A design, and a file that needs a guide |
  | `vibes:performance-reviewer` | A file that needs a guide in `languages/`, `web/`, `build/` or `tools/`, or a query or schema guide in `data/`: SQL and its dialects, GraphQL or Protocol Buffers |
  | `vibes:resource-leak-reviewer` | A file that needs a guide in `languages/` |

  So a change to only YAML, TOML or XML config gets no performance or
  resource-leak review, and a change to only docs gets only the spec and
  security reviewers. When you're unsure whether a file is in a
  reviewer's area, keep the reviewer. Write the panel to the round's
  `panel.md`, one line per reviewer: the reviewers that run, then each one
  left out and why, in a few words. Check it again each
  round: when the change gains a file in a left-out reviewer's area, that
  reviewer joins, with a full first round.

## Unattended runs

The user can ask for a run that never stops to ask them anything, such as
`/vibes:vibe unattended: <task>` or by saying so in the task. Record it in
`state.md`. Then, wherever this skill says to ask the user:

- **Open questions in the spec:** decide each one yourself. Choose the
  option that does the least the user didn't ask for, and is easiest to
  change later. Record it in the spec's assumptions, marked
  `Unattended decision:`, with the options you didn't choose.
- **A spec change that would alter what the user asked for:** make the
  narrower choice the same way, and record it the same way.
- **An unclear task:** take the narrowest reading that still does something
  useful, and record it as an unattended decision. If no reading makes
  sense, stop and report why.
- **Anything that could lose or overwrite the user's work,** such as
  uncommitted changes, an existing pre-commit hook or another task's
  unfinished run: never act on it. Stop, and report what needs a decision.
- **The round limit:** stop, and report the outstanding findings as the
  limit says.
- **The spike branch at the end:** keep it.

The final report lists every unattended decision first, with the options
not chosen, so the user can check them before anything else.

## Keep the state current

Keep `.vibes/<name>/state.md` current, so an interrupted run can carry on
where it stopped. Update it when a phase starts or ends, after every review
round, and after every commit. It holds:

- the task as the user gave it, their answers to open questions, the
  task's name and size, and whether the run is unattended;
- the base branch, the spec directory and the guides that apply;
- the current phase and round, and the last step finished;
- `status: running` until Phase 8 ends, then `status: done`.

Keep it short: one line for each finished step, naming the commits or the
file that holds the details, such as a round's `responses.md` or a
builder's report. The details live there, not in `state.md`.

## Keep the guides current

A task can need a guide nobody expected at the start, such as a Dockerfile
in a C++ project, or a Python script in a Go one. The guides are for
languages, formats and tools alike. `${CLAUDE_PLUGIN_ROOT}/bin/guides-for`
lists the guides that files need, from
`${CLAUDE_PLUGIN_ROOT}/guides/map.tsv`:

```sh
git diff --name-only <base>...HEAD | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"
```

An entry such as `languages/C|languages/C++` means either will do: use the
one the project uses. Run it on the branch's changes after every spiker
and builder report, and before every review round. For every guide that
isn't in `state.md` yet:

1. **Add it** to `state.md` and to every later brief, so every agent that
   writes or reviews those files reads it.
2. **Have the gate extended** on the rebuild branch, before the commit that
   needs it. Tell the next builder the gate doesn't check the guide yet: it
   adds the checks from the guide's `tools.md` to `scripts/check`, and the
   guide to the `# Guides:` line, in a commit of its own. The builder also
   does this itself when it's the first to write a new kind of file.

For every file listed as `no guide:`, tell the user that no vibes guide
covers it, and add a pattern for it to a `# No guide:` line in
`scripts/check`. In an unattended run, list them in the final report
instead of asking.

Two hooks back this up. The first time an agent writes each kind of file
in a conversation without having read its guide, one refuses the write and
names the guide to read first, and warns if the gate doesn't check that
guide yet. The next write goes ahead. The commit gate blocks a commit whose
files need a guide that the `# Guides:` line doesn't name, or that no guide
covers and no `# No guide:` line lists. The gate doesn't run on the spike
branch, so there the check after the spiker reports is what catches a new
guide.

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
   - when the designer, the spiker or a builder didn't report, run it
     again, and tell it what already exists so it carries on rather than
     starting over;
   - in the build, give a fresh builder the next batch, starting from the
     first entry in the test list that isn't ticked off.

## Phase 0: Set up

1. **Understand the task.** If the task is unclear or missing, ask the user
   before doing anything else. Pick a short kebab-case name for it, such as
   `order-export`. The rebuild branch is `vibe/<name>` and the spike branch
   is `spike/<name>`.
2. **Check the working tree is clean** with `git status`. If it isn't, ask
   the user what to do with the changes. Note the current branch: it's the
   base branch.
3. **Find the guides** that apply: the ones the project already needs,
   from `git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"`, and the
   ones the task will add, such as `tools/Docker` for a task that adds a
   container image. Don't read the guides yourself: the agents that set
   up the gate, and write and review the code, read them.
4. **Size the task,** as [Size the task](#size-the-task) describes, and tell
   the user the size.
5. **Choose the spec directory,** where the task's `spec.md` and
   `design.md` will live in the repository. If the project already keeps
   specs or design documents somewhere, use a directory for the task there.
   Otherwise use `docs/specs/<name>/`.
6. **Create the task's state directory** `.vibes/<name>/` for the
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
7. **Start the commit gate setup.** If the project has no executable
   `scripts/check`, or its `# Guides:` line doesn't name every guide the
   project already needs, spawn a `general-purpose` subagent in the
   background, with `medium` effort, to follow the
   `${CLAUDE_PLUGIN_ROOT}/skills/commit-gate/SKILL.md` skill on the base
   branch, with the guides and any rules the user gave about installing
   tools. It commits the gate setup on the base branch as one commit of its
   own, so the spike and rebuild branches both start with it, and replies
   with the commit and any tool it left out. The setup mostly follows that
   skill's steps, so it needs no more effort. Don't wait for it: go on with
   Phase 1, which drafts the spec where git ignores it, and stay on the
   base branch until the gate is committed. List the gate commit in the
   final report.

## Review rounds

Every review in the workflow runs in rounds, the same way. A round reviews
one phase: `spec`, `design`, `spike` or `rebuild`. The spike phase runs at
most two rounds and fixes no code, as
[Phase 4](#phase-4-review-the-spike) describes, so steps 5 to 7 don't
apply to it.

1. **Prepare the round directory,** `.vibes/<name>/review/<phase>-<round>/`
   (for example `.vibes/<name>/review/spike-1/`). In the spike and rebuild
   phases, save the change in it, and the commit it reviews:

   ```sh
   git diff <base>...HEAD > .vibes/<name>/review/spike-1/diff.patch
   git diff --name-only <base>...HEAD > .vibes/<name>/review/spike-1/files.txt
   git rev-parse HEAD > .vibes/<name>/review/spike-1/head.txt
   ```

   From round 2 on, copy the previous round's findings files and
   `responses.md` into the new directory, without reading them. In the
   spike and rebuild phases, later rounds review only what changed: for
   each round `<k>` that a reviewer in this round last reviewed, save the
   changes since then, for example in `rebuild-3/` for reviewers last run
   in round 2:

   ```sh
   since="$(cat .vibes/<name>/review/rebuild-2/head.txt)"
   git diff "${since}" HEAD \
     > .vibes/<name>/review/rebuild-3/changes-since-2.patch
   git diff --name-only "${since}" HEAD \
     > .vibes/<name>/review/rebuild-3/changed-files-since-2.txt
   ```
2. **Spawn every reviewer for the round in a single message**, so they run in
   parallel. In round 1 every reviewer on the phase's panel runs, as
   [Size the task](#size-the-task) describes. In later rounds, only the
   reviewers that requested changes run again. Give each one a brief:

   ```text
   Task: <the task, and the user's answers to any questions>
   Spec: <absolute path to spec.md>
   Design: <absolute path to design.md, once it exists>
   Review directory: <absolute path to .vibes/<name>/review/spike-1>
   Phase: <spec, design, spike or rebuild>
   Guides: <guides>
   Round: <n>
   Changes: <from round 2, in the spike and rebuild phases: the absolute
     paths of changes-since-<k>.patch and changed-files-since-<k>.txt for
     the round <k> this reviewer last reviewed>
   ```

3. **Each reviewer writes its findings** to `<reviewer>.md` in the round
   directory, such as `security-reviewer.md`, and
   replies with one line: its verdict, and the number of findings at each
   severity. Don't read the findings files: the fixer decides on them.
4. **Have the findings decided on and fixed,** when any reviewer reported
   findings. Spawn a fresh fixer with the round directory: `vibes:designer`
   in `revise` mode in the spec, design and spike phases, with the spec
   directory, the guides and the phase, and asking for change log entries
   when a document was already approved; `vibes:builder` in `fix` mode in
   the rebuild phase. It decides on each finding as its definition says:
   it accepts every BLOCKER and MAJOR finding and the cheap MINOR ones, and
   rejects a wrong one with a reason. It fixes the ones it accepts, putting
   any change in behaviour into the spec first, as
   [The spec comes first](#the-spec-comes-first) says. It writes a line for
   each finding to the round's `responses.md`, and replies with what it
   did and anything it left to you, such as a fix that would change what
   the user asked for. Ask the user about each of those, then give the
   answers to a fresh fixer. For a small task's spec, which you wrote,
   decide on and fix the findings yourself. In the rebuild phase, check
   the fixer's commits are on the right branch and the working tree is
   clean.
5. **Start the next round** with only the reviewers whose verdict was
   `CHANGES REQUESTED`, to check the fixes to their BLOCKER and MAJOR
   findings and any rejections. A fix to a MINOR finding isn't reviewed
   again: the gate checks it, and so does the spec reviewer's last round.
   A reviewer that approved doesn't run again while others are still
   requesting changes, even when their fixes touch its area.
6. **Repeat** until every reviewer's latest verdict is `APPROVED`. Then, in
   the rebuild phase, run one last round to confirm the fixes didn't break
   anything: the spec reviewer, so its final verdict covers the final code,
   and each reviewer that approved before a fix to a BLOCKER or MAJOR
   finding changed code in its area. A change to only tests brings back
   only the test reviewer, and a change to only names, messages or
   comments brings back none. Each one's `Changes:` line covers everything
   since it last ran. A MINOR finding in the last round is fixed without
   another round. A BLOCKER or MAJOR one is fixed and checked once more,
   by its reviewer and the spec reviewer.
7. **Stop at the round limit:** 3 rounds for the spec and design, and 5
   for the rebuild. If any reviewer still requests changes, stop, read the
   outstanding findings and their responses, and show the user them and
   where the reviewers and the fixer disagree. Ask how to proceed.

## Phase 1: Spec

1. Spawn `vibes:designer` in `spec` mode, with the task and the guides.
   Its spec directory is the draft directory `.vibes/<name>/draft/`, which
   git ignores, so the gate setup's commit isn't blocked by the new files.
   For a small task, write the spec there yourself instead.
2. **Resolve every open question.** Ask the user each one in the spec's
   open questions section, then have the designer write their answers into
   the spec as requirements, and empty the section.
3. **Review the spec** in rounds with `vibes:spec-reviewer`, with the
   designer deciding on and fixing its findings, until it approves.
4. **Wait for the gate setup** to finish, if it's still running. Check its
   commit is on the base branch and `scripts/check` passes there.
5. **Commit the approved spec** on the rebuild branch, so the spike and the
   rebuild both start from it: create the branch from the base branch with
   `git switch -c vibe/<name>`, copy the draft into the spec directory, and
   commit it on its own, through the gate. From here on, briefs give the
   spec directory.

## Phase 2: Design

Medium and large tasks only.

1. Spawn `vibes:designer` in `design` mode, with the same brief.
2. **Review the design** in rounds with `vibes:architecture-reviewer`, with
   the designer deciding on and fixing its findings, until it approves. A
   finding that shows the spec is wrong or incomplete goes back into the
   spec first, and the spec reviewer approves the changed spec in a `spec`
   round before the design rounds go on.
3. **Commit the approved design,** together with any spec changes the
   design review made.

## Phase 3: Spike

Large tasks only. Small and medium tasks go straight to
[Phase 6](#phase-6-rebuild-test-first).

1. Create the spike branch from the rebuild branch, so it starts with the
   spec and design: `git switch -c spike/<name>`.
2. Spawn `vibes:spiker` in `build` mode, with a brief giving the task, the
   spike branch, the base branch, the absolute paths of `spec.md` and
   `design.md`, and the guides.
3. It writes its report to `.vibes/<name>/spike-report.md`. Check the
   spike's commits are on `spike/<name>`, and that the working tree is
   clean. If the spiker changed the spec or design, read each change log
   entry, and ask the user about any that alters what they asked for.
4. **Check the guides** on the spike's changes, as
   [Keep the guides current](#keep-the-guides-current) describes. The
   rebuild will extend the gate for any new ones.

## Phase 4: Review the spike

Large tasks only.

The spike exists to test the spec and design, and its code is thrown away.
So its review finds where they fall short and corrects them, and fixes no
code: the rebuild builds every finding right, test-first.

1. **Review the spike once,** in round `spike-1`, with the panel from
   [Size the task](#size-the-task). The panel leaves out
   `vibes:test-reviewer`, `vibes:style-reviewer`, `vibes:idioms-reviewer`
   and `vibes:cleanliness-reviewer`, whose findings would be about code
   that's thrown away. The rebuild review runs them on the code that's
   kept. The spec reviewer lists every requirement the spike doesn't meet.
2. **Correct the spec and design** on the spike branch. Spawn a fresh
   `vibes:designer` in `revise` mode, as step 4 of
   [Review rounds](#review-rounds) says, in the `spike` phase, asking for
   change log entries. It decides on each finding and sorts each one it
   accepts: `spec` or `design` when the spec or the design is at fault,
   which it corrects, and `lesson` for a fault in the spike's code, which
   the rebuild gets right. Ask the user each open question it reports.
   Commit its changes on the spike branch.
3. **Have the corrections approved,** before any rebuild starts: the spec
   reviewer in `spec` rounds, then the architecture reviewer in `design`
   rounds, as Phases 1 and 2 describe. Their findings are fixed in the spec
   and design the same way, and committed on the spike branch.
4. **Try out an uncertain design change,** each one the designer reports
   it can't vouch for without building it, such as a new way to walk a
   directory tree. Spawn `vibes:spiker` in `fix` mode, with the design
   changes to build. Then run round `spike-2`, with the reviewers whose
   findings led to the change and the spec reviewer, on the changes since
   `spike-1`, and correct the spec and design as steps 2 and 3 say.
   There's no third spike round: anything left is a lesson.

## Phase 5: Set the spike aside

Large tasks only.

The spike is a reference implementation, never production code. It stays on
`spike/<name>` and is never merged. The corrected spec and design stay on
the spike branch too, until the rebuild brings each change over with the
commit that implements it. Builders read them there, with
`git show spike/<name>:<path>`, so don't copy them anywhere else.

1. Save the spike phase's spec and design changes:

   ```sh
   git diff vibe/<name> spike/<name> -- <spec directory> \
     > .vibes/<name>/spike-changes.patch
   ```

2. Spawn `vibes:designer` in `plan` mode, still on the spike branch, to
   write `.vibes/<name>/rebuild-plan.md`, as
   [The rebuild plan](#the-rebuild-plan) describes, with the spike's round
   directories and that patch.
3. Switch to the rebuild branch: `git switch vibe/<name>`.

## The rebuild plan

`.vibes/<name>/rebuild-plan.md` is what the builders work from. It opens
with the task's name, the branches and the list of batches, then holds the
batches in order, each in its own section, so a builder reads only the
opening and its own batch. Each batch section holds:

- **The test list entries,** in order from simplest to hardest. Each entry
  is one red, green, refactor cycle ending in a commit: the tests that
  drive one piece of code into being, such as a requirement's normal case
  and its errors together. A test that would pass on code an earlier entry
  wrote goes in that entry, not in one of its own. Each entry names the
  ids it covers. Together, the entries cover every requirement and quality
  id in the spec. An entry covers every requirement its piece of code
  serves, so a plan usually has about half as many entries as the spec has
  ids.
- **The guides** for the files the batch writes.
- **For a large task, the lessons** for the batch: each `lesson` finding
  from the spike review, by its id, with the entry that gets it right.
- **For a large task, the spec changes** the batch brings over: each
  change log entry the spike phase added to the spec or design, with the
  entry whose commit brings it over.

A batch is a group of entries that belong together, such as one
feature's. Make the batches as few and as large as one builder can finish
in a fresh context, because each new builder reads the skills, the guides,
the spec and the design again before it starts: about eight to twelve
entries each. One command-line tool or one library feature is usually two
or three batches, and a small task is one.

## Phase 6: Rebuild test-first

`vibes:builder` builds the task test-first, following the
[test-driven development](../test-driven-development/SKILL.md) and
[atomic commits](../atomic-commits/SKILL.md) skills, through the gate. You
split the work into batches, and give each batch to a fresh builder, so no
context carries more than one batch of code.

For a small or medium task, this is the first build, on the rebuild branch
from Phase 1. Have `vibes:designer` write `.vibes/<name>/rebuild-plan.md`
first, in `plan` mode, as [The rebuild plan](#the-rebuild-plan) describes;
there are no lessons or spec changes from a spike to list. For a small
task, write it yourself. Where there was no spike, the steps
below that mention one don't apply.

1. **The first batch enforces the boundaries.** Where the task has a
   design, it starts by adding the design's boundary rules to
   `scripts/check`, as architecture tests or build structure from each
   guide's `tools.md`, so the gate holds every later commit to them. Where
   the spike needed guides the gate doesn't check yet, it extends the gate
   for them first too.
2. **Spawn a fresh `vibes:builder` in `build` mode for each batch,** one
   at a time, on the rebuild branch. Its brief gives the task, the
   branches, the paths of the spec, design and rebuild plan, the batch's
   section in the plan, its guides and any the gate doesn't check yet,
   whether it's the first batch, and its report's path,
   `.vibes/<name>/build-<batch>.md`. The spec and design are the source of
   truth: for a large task, as the spike phase left them.
3. **Check each batch** before the next: its commits are on the rebuild
   branch, the working tree is clean, the plan's entries are ticked off,
   and `scripts/check` passes. Check the guides on the branch's changes, as
   [Keep the guides current](#keep-the-guides-current) describes, and
   update `state.md`.
4. **Decide what the builder couldn't,** such as a spec change that alters
   what the user asked for, which you ask the user about. Then carry on
   with the next batch.

By the end of the build, every entry is ticked off, and the spec and design
hold every change from the spike phase.

## Phase 7: Review the rebuild

Run review rounds in the `rebuild` phase on the rebuild branch, with the
panel from [Size the task](#size-the-task), including
`vibes:test-reviewer`. A fresh builder in `fix` mode decides on and fixes
the findings the same way as the build: the spec first for any change in
behaviour, then a failing test, then the fix, committed together as atomic
commits through the gate.

Before round 1, run `scripts/check-requirements --all` with the task's spec
and the tests, if the project has it, and have a builder add a test for any
requirement it reports. The spec reviewer's final verdict must be
`APPROVED`, with every requirement met and tested.

## Phase 8: Finish

1. Run `scripts/audit` if the project has one, and have a builder in `fix`
   mode fix what it finds, with the audit's failures in its brief.
2. Check `git status` is clean and `scripts/check` passes.
3. Report to the user:
   - for an unattended run, every unattended decision first, with the
     options not chosen
   - the task's size, and any move to a larger size, with why
   - the guides the task added to the gate, and any files no guide covers
   - the rebuild branch and its commits (`git log --oneline <base>..HEAD`)
   - the spec and design in the spec directory, every change made to the
     spec after it was approved, and the spec reviewer's final coverage
   - every reviewer's final verdict, any reviewer left out of a phase's
     reviews and why, and any deferred MINOR findings
   - for a large task, the spike branch, kept for reference: ask whether to
     delete it
4. Set `status: done` in `state.md`.
5. Don't push, merge or open a pull request unless the user asks.
