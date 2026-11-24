# vibes

Guides and tooling for clean vibe coding: letting an AI agent write the code,
while holding it to the standards of careful, experienced developers.

- **`guides/`:** 60 guides, grouped by kind: `languages/` for 40
  programming languages, `web/` for HTML, CSS and Sass, `data/` for SQL,
  database dialects, data formats and schema languages, `build/` for
  CMake, Make and linker scripts, and `tools/` for Docker, GitHub Actions,
  OpenTofu, Nix, and the instructions agents read: `CLAUDE.md`,
  `AGENTS.md`, skills and subagents. Each has a `coding-style.md`, an `idioms.md` and a
  `tools.md` listing FOSS linting, auditing and code-quality tools, plus a
  `.editorconfig` and drop-in config files for those tools.
  [guides/README.md](guides/README.md) says what goes in a guide, and
  [guides/map.tsv](guides/map.tsv) says which guide each kind of file
  needs.
- **`bin/guides-for`:** lists the guides a set of files needs, such as
  `git ls-files | bin/guides-for`.
- **`bin/project-docs`:** lists a project's own documents, such as its
  README, architecture notes and earlier specs, for the project docs
  reviewer: `git ls-files | bin/project-docs`.
- **`bin/pr-prepare` and `bin/pr-scan`:** fetch an untrusted pull request
  and scan it for malicious changes, without running anything in it. The
  scanner is in `lib/pr_scan/`, and its tests in `tests/pr_scan/`.
- **`bin/bench`:** measures whether a change made a program faster, in
  interleaved A/B runs with a verdict beyond the noise. It's in
  `lib/bench/`, and its tests in `tests/bench/`.
- **`bin/repro`:** runs a bug's reproduction several times and says
  whether it fails reliably and fast. It's in `lib/repro/`, and its tests
  in `tests/repro/`.
- **`bin/hotspots`:** ranks the files and directories recent commits
  changed most, for the architecture survey.
- **`bin/report-page`:** turns a Markdown report with Mermaid diagrams
  into one page to open in a browser. It's in `lib/report_page/`.
- **`bin/issue-digest`:** prints a digest of what other people wrote in
  an issue, so an issue changed after you approved it is never picked up.
- **`bin/prototype-check`:** checks a logic prototype loads nothing from
  outside, keeps its logic apart from the page, and has its question and
  scenarios. It's in `lib/prototype_check/`, and its tests in
  `tests/prototype_check/`.
- **`bin/setup-needs`:** lists the settings a branch needs a person to
  provide, such as an API key the code now reads or a secret a workflow
  now names. It's in `lib/setup_needs/`, and its tests in
  `tests/setup_needs/`.
- **`bin/wizard-check`:** checks a wizard parses, keeps the wizard
  library unchanged and passes ShellCheck, without running it.
- **`bin/tracker`:** reaches the project's issue tracker through the
  commands it names in `.vibes-tracker`, only as you approved them, as
  [Your issue tracker](#your-issue-tracker) says. It's in `lib/tracker/`,
  and its tests in `tests/tracker/`.
- **`bin/capacity`:** measures how many builders the machine can run at
  once for the project, from runs of its gate, and caches the answer. It's
  in `lib/capacity/`, and its tests in `tests/capacity/`.
- **`bin/plan-graph`:** reads the task graph in a rebuild plan: which
  batches can start, how many could run at once, and any two that could
  run at once but touch the same files. It's in `lib/plan_graph/`, and its
  tests in `tests/plan_graph/`.
- **`bin/session-digest`:** prints a compact digest of a Claude Code
  session's transcript, for a retrospective. It's in
  `lib/session_digest/`, and its tests in `tests/session_digest/`.
- **`skills/`:** agent skills for the workflow, optimising performance,
  debugging, surveying the architecture, reviewing your own branch or an
  outside pull request, writing a pull request, triaging issues and
  picking up approved ones, setting up the issue tracker, asking someone
  else through a questionnaire,
  prototyping a decision, writing a wizard for steps only you can do and a
  runbook for changes that can't be undone,
  grilling a plan before it's built, measuring how many builders the
  machine can run,
  looking back on a session, test-driven development, atomic commits and setting up the
  commit gate.
- **`principles.md`:** the programming principles every change is held
  to, such as SOLID, DRY and KISS.
- **`architecture/`:** how to structure software: rules for every kind,
  a guide each for web, desktop and mobile applications, command-line
  tools, libraries, OS components and embedded systems, and how to judge
  whether a module is deep enough to pay for itself.
- **`security/`:** how malicious changes hide, for the supply-chain
  reviewer.
- **`performance/`:** how to measure and profile a program, and the
  profilers and benchmark tools for each guide, for the profiler and the
  optimiser.
- **`agents/`:** the designer, the spike agent, the builder, twelve
  reviewer agents, the profiler and optimiser, the diagnoser, the
  researcher, the surveyor
  and interface designer, the commit message suggester, the
  retrospective, the pull request writer, the issue reader, the
  prototyper and the wizard writer.
- **`bin/host-files`:** writes vibes' agents for Codex, and a whole
  extension for Gemini CLI, as [Other agents](#other-agents) says. It's in
  `lib/host_files/`, and its tests in `tests/host_files/`.
- **`hooks/`:** the commit gate, for Claude Code, Copilot CLI, Codex,
  Gemini CLI and git; a guide
  check that makes the agent read the guide for each kind of file before
  writing it; and a guard that keeps the reviewers, the commit message
  suggester, the retrospective, the survey's agents, the pull request
  writer, the issue reader and the wizard writer from changing anything
  but their own findings files and reports,
  and the
  profiler from changing the code. The commit gate also refuses a subject
  longer than 50 characters, and asks you before a commit that loosens
  the gate itself.
- **`evals/`:** evals that check each reviewer agent finds the defects in
  its area and approves clean code, that the workflow picks the right
  reviewers for a change, that a pull request review catches malicious
  changes, that the profiler and optimiser find and measure the hot spot,
  that the project docs reviewer finds a contradiction and skips documents
  that don't apply, that suggested commit subjects fit in 50 characters,
  that a retrospective suggests a check without loosening one, and that
  the survey finds the shallow module and designs it three different
  ways, run with `claude plugin eval`.

## The workflow

Run it in a project with `/vibes:vibe <task>`. The workflow below is for a
large task. The main agent sizes each task and tells you the size, and you
can name one yourself, such as `/vibes:vibe small: fix the date parsing`:

- **Small,** such as a fix in existing code: a spec, a test-first build
  and a focused review, with no design or spike.
- **Medium,** a feature or a small new program whose design is clear: adds
  the design, and the full review panel.
- **Large,** a new application with several parts, or uncertain work:
  everything below.

At every size, a reviewer whose area the change can't touch is left out,
such as the performance and resource-leak reviewers for a change to only
config files.

When the project has documents of its own, such as architecture notes,
conventions or the specs of earlier tasks, the project docs reviewer joins
every review, the spec and design ones too. It first decides which of them
apply to the task, and stops at once when none do. Where one does, it
reports each place the work contradicts it, and the spec and design are
corrected to follow the document. If the task seems meant to change what a
document says, you're asked, and if it is, the task updates the document
too. A project with no documents never runs it.

You're asked only for decisions, never for facts. Each open question is
marked one or the other. A fact, such as what an outside API allows or
how a library behaves at the version the project pins, goes to a
researcher subagent. It answers from primary sources, the dependency's
own code at that version first, and writes a dated note citing a source
for each claim, which is committed with the spec that relies on it. Each
decision comes with a recommended answer worded so "yes" accepts it, so
you can answer by number, or reply "yes" to accept them all.

Add `unattended` to run it without stopping to ask you anything, such as
`/vibes:vibe unattended: <task>`. The main agent then takes each
decision's recommended answer, or the narrowest choice when the
recommendation does more than you asked, records it, and lists every
such decision first in its final report. It still stops rather than touch anything that
could lose your work.

1. **Spec.** A designer subagent writes a complete spec: every requirement,
   error and edge case, each testable, in proportion to the task. Its factual
   questions are researched, you answer the decisions in rounds, and a spec
   reviewer checks it until it's complete. The spec uses the project's
   glossary, and each new term the task brings is added to it. Meanwhile,
   another subagent sets up the commit gate.
2. **Design.** The designer writes the design to the spec, and the
   architecture reviewer checks it before any code exists. The design
   keeps to the project's decision records, and each new decision that's
   hard to reverse, surprising and a real choice gets a short record of
   its own, in `docs/adr/` or wherever the project keeps them. Each
   component gets entry points, its front door, which other components and
   its own tests must go through. The spec
   and design are committed in your repository, in `docs/specs/<task>/` or
   wherever the project already keeps them.
3. **Spike.** A subagent builds the whole task quickly to the spec and
   design on a `spike/<task>` branch.
4. **Review.** Reviewer subagents critique the spike in parallel, one each
   for architecture, memory and resource leaks, performance, bugs and
   security, and the spec reviewer lists any requirement it doesn't meet.
   Style, idioms and cleanliness wait for the rebuild, since the spike's
   code is thrown away.
5. **Correct.** The spike's code isn't fixed. Each finding that changes
   behaviour goes into the spec, and each that changes the structure into
   the design, and the spec and architecture reviewers approve them again
   before anything is rebuilt. A design change the spike can't vouch for is
   tried out in the spike once more. Every other finding becomes a lesson
   for the rebuild. Each change to the spec, here and later, is committed
   together with the code that implements it.
6. **Rebuild.** The spike is set aside, never merged. Builder subagents
   rebuild the task on a `vibe/<task>` branch, test-first, one atomic
   commit at a time, each starting fresh on its own batch of the work. The
   main agent only coordinates: subagents keep their own records, decide
   on and fix the findings, and reply in a line or two, so its context
   stays small however long the run.
7. **Gate.** Every commit runs the project's linters and fast tests, and is
   blocked if anything fails. Each batch ends with the slow tests too. The
   first batch adds the design's boundary rules to the gate, the layers
   and each component's entry points, and proves each one bites by
   breaking it once on purpose.
8. **Review again.** The same reviewers, plus reviewers for code
   cleanliness, coding style, idioms and test quality, check the rebuild,
   and their findings are fixed test-first. The spec reviewer verifies
   every requirement is met and tested.

Nothing is pushed or merged unless you ask.

To see what a run looks like, from the spec to the first rebuild batches,
read the [worked example](docs/example/README.md).

## Optimise performance

`/vibes:optimise [area or problem]` makes a program faster where a profile
shows the time goes, such as `/vibes:optimise the CSV import is slow`.
Without an area, it optimises the program's usual workload. It's separate
from `/vibes:vibe`, which never uses it.

1. **Baseline.** The profiler agrees a workload with you, at two sizes and
   with a holdout input, and builds a harness for it outside the code. It
   profiles with real tools, such as `perf`, samply, `sample`, cProfile or
   pprof, and measures how noisy this machine is with an A/A run.
2. **Plan and spec.** The optimiser ranks ideas by the share of time each
   can save. It writes the optimisation's own spec, with targets relative
   to the baseline and guard rails such as peak memory, which the spec
   reviewer approves.
3. **The spike loop.** Each idea is built, spec first, on its own
   `spike/optimise-<slug>-<i>` branch from the best version so far. The
   profiler runs the tests, then measures it against the best version in
   interleaved pairs, and `bin/bench verdict` decides: `IMPROVED`,
   `NO CHANGE`, `REGRESSED`, `INCONCLUSIVE` or `BROKEN`. An improvement
   becomes the best version. The loop stops when the next idea could save
   under 5%, after three attempts in a row without a gain, or at eight
   attempts; `max <n>` changes the last.
4. **Review the spike.** The reviewers check the best version for
   architecture and every standard, knowing what each change measured.
   The spec and design are corrected, and their findings about the code
   become lessons for the rebuild.
5. **Rebuild test-first** on `optimise/<slug>`, as the vibe workflow does,
   with a benchmark committed in the language's own benchmark tool.
6. **Verify.** The rebuild is measured against the baseline and the spike,
   must meet the spec's targets, and is reviewed in rounds.

`/vibes:optimise unattended: <area>` runs without stopping to ask: it
takes the profiler's workload, installs nothing, and rejects any trade-off
outside the spec. Otherwise it asks before installing a profiler. Measure
on mains power with nothing else running: `bench` warns when the machine is
on battery, in Low Power Mode or busy.
[performance/README.md](performance/README.md) describes the method.

## Review a pull request from outside

`/vibes:review-pr <number or URL>` reviews a pull request from someone
outside the project, above all for malicious changes, such as the XZ Utils
backdoor (CVE-2024-3094), which hid its payload in test data and pulled it
into the build. It's separate from `/vibes:vibe`, which never uses it.
`/vibes:review-pr --local <base> <head>` reviews a local branch instead.

On GitHub it fetches the pull request and its metadata with `gh`. On
another forge, fetch the merge request yourself into a ref that isn't a
branch, so it's never checked out by mistake, and review it with
`--local` from where it left the base branch. GitLab keeps a merge request
at `refs/merge-requests/<n>/head`, for 14 days after it's closed or
merged, and Forgejo and Gitea keep a pull request at `refs/pull/<n>/head`:

```sh
git fetch --no-tags origin +refs/merge-requests/12/head:refs/vibes/mr/12
/vibes:review-pr --local $(git merge-base main refs/vibes/mr/12) refs/vibes/mr/12
```

That review has everything but the forge's own record of the pull
request, such as its description, which only GitHub's gives the
reviewers.

1. **Prepare.** `bin/pr-prepare` fetches the pull request and its metadata
   with `gh` and git, and reads it only from git objects, with hooks,
   filters, textconv, LFS and submodules turned off. Nothing from the pull
   request is checked out, built, tested or run.
2. **Scan.** `bin/pr-scan` checks every changed file, and every commit on
   its own, against about twenty families of rules: binaries and what they
   hide, encoded payloads, hidden Unicode, build-time code, code that runs
   before `main`, weakened checks, pins and keys, dependencies, CI, agent
   config, git tricks, privilege and kernel settings, network use,
   behaviour that depends on where it runs, text aimed at AI reviewers, and
   who the commits come from. It writes the pull request's files under
   hashed names with hidden characters shown, so no `CLAUDE.md` or
   `.claude/settings.json` in it is ever loaded, and describes binaries
   instead of showing them.
3. **Review.** The supply-chain, security and bug reviewers always run, and
   the quality reviewers join when the change is in their area, as does the
   project docs reviewer when the project has documents. The spec reviewer
   never does, since it runs code. The supply-chain reviewer must
   account for every HIGH scan finding.
4. **Report.** `pr-review.md` lists the scan's findings first, then each
   reviewer's, then the files a person must inspect. `comment-draft.md` is a
   comment for you to edit and post. Nothing is posted to GitHub, approved
   or merged.

No reviewer can clear a HIGH scan finding: each needs a person.

## Review your own branch

`/vibes:review` reviews the checked-out branch since it left its base
branch, the remote's default branch unless you name one, such as
`/vibes:review develop`. Uncommitted changes to tracked files are included,
without touching your working tree, index or branches; new files you
haven't added to git are listed but not reviewed.

It runs the same scan, guides and reviewers as `/vibes:review-pr`, but as
your own work: the reviewers read the working tree, and with a spec, such
as `/vibes:review spec docs/specs/order-export` or a `vibe/<name>` branch's
own, the spec reviewer joins and may run the tests. Say what the change is
for, such as `/vibes:review adds CSV export`, and the reviewers judge it
against that and the commit messages.

The report, `review.md`, lists the scan's findings, each reviewer's, and
the files a person must inspect. Then it offers to fix the findings: a
builder fixes them test-first, committing on your branch through the gate,
and the reviewers who asked for changes check the fixes, for up to three
rounds. Your uncommitted changes are never mixed in: commit or stash them
first. Nothing is pushed.

### Protected paths

A `.vibes-review` file in the repository adds project-specific rules, one
per line, a kind and a glob separated by a tab:

```text
protected	vendor/*/get.sh
test-data	tests/smoke/references/**
binary-allowed	tests/smoke/references/*.png
allowed-host	cdn.kernel.org
```

- **`protected`:** any change is HIGH.
- **`test-data`:** treated as test data, which build code mustn't read.
- **`binary-allowed`:** a well-formed image or font here is REVIEW, not HIGH.
  Archives and executables are always HIGH.
- **`allowed-host`:** not reported as a new host.

The scan reads `.vibes-review` from the base branch only, so a pull request
can't weaken it, and a pull request that changes it is HIGH.

### Limits

- An attacker who knows these checks may write a change that passes all of
  them.
- Nothing here can tell whether an upstream release a pin points at is
  itself malicious, so every pin, hash and key change needs checking by
  hand.
- Nothing here detects social engineering: pressure to merge, or trust
  built up over years.
- CI may already have run the pull request's code on GitHub.
- A reviewer can be misled by text in the pull request, which is why the
  scan's HIGH findings and the list of files to inspect always stand.
- Merge with `gh pr merge --squash --match-head-commit <head>`, so what you
  merge is what was reviewed, and no commit's history comes with it.

## Debug a bug

`/vibes:debug <symptom>` finds and fixes a bug whose cause isn't known,
such as `/vibes:debug invoices issued on the 31st show as overdue a day
early`. It's separate from `/vibes:vibe`, which builds what's already
understood, and `/vibes:optimise`, which takes a symptom that's only
slowness.

1. **Reproduce.** The diagnoser builds `repro.sh`, one command that fails
   on the exact symptom, and shrinks it into `minimal.sh`. Nobody guesses
   at the cause until `bin/repro` runs each several times and says `RED`
   every time, in seconds. When it can't be reproduced, you're asked for
   what would make it possible, such as a log or access.
2. **Diagnose.** It ranks three to five hypotheses, each with a prediction
   that could prove it wrong, and you can re-rank or rule any out. It
   tests them one change at a time on a throwaway `spike/debug-<slug>`
   branch, tagging every debug log `vibes-debug-<slug>`, until one holds
   and a quick change makes both commands pass.
3. **Fix.** A short bug spec, the symptom, the cause and the correct
   behaviour, is reviewed and committed on `debug/<slug>`. A builder then
   rebuilds the fix test-first, starting from a regression test that fails
   on the bug, and the fix commit says what the cause was. The reviewers
   check it, and the original `repro.sh` must pass on the fix.

The gate refuses any commit carrying the debug tag, so no debug log
reaches the fix. When no test can reach the bug the way it really
happens, the report says so, as a finding about the code's structure.
`/vibes:debug unattended: <symptom>` runs without stopping to ask, and
stops and reports when it needs something only you can give.

## Survey the architecture

`/vibes:survey` looks across the existing codebase, not one change, for
shallow modules worth deepening: places where an interface is nearly as
complex as the code behind it, so callers repeat work, call things in the
right order, or can't test the real behaviour. Name a focus, such as
`/vibes:survey the order pipeline`, or let the history decide:
`bin/hotspots` ranks the files recent commits changed most, since a better
structure pays off where change keeps landing. It judges by
[deep modules](architecture/deep-modules.md): depth, seams, locality, and
whether deleting a module would concentrate its complexity or only move
it.

1. **The survey.** The surveyor writes ranked candidates, each with the
   code that shows the friction, the deletion test, what would change, its
   cost, and before and after diagrams, rated strong, worth exploring or
   speculative, with a top recommendation and the areas it left alone.
   `bin/report-page` shows it as a page. It respects the project's
   decision records, raising one only when the friction is worth
   reopening it.
2. **Design it twice.** For the candidate you pick, three interface
   designers each design it under a different constraint, the smallest
   interface, the most flexible and a different seam, without seeing each
   other's. The surveyor checks they really differ, having one redesigned
   if two came out the same, then compares them and recommends one, or a
   combination, and what it gives up.
3. **Build it,** if you choose, with `/vibes:vibe`, from the chosen
   design: a spec, a test-first rebuild through the gate, and every
   review. The gate then holds callers and tests to the deepened module's
   entry points, so it can't turn shallow again.

The survey changes nothing: its agents may write only their own reports.
When you turn a candidate down for a lasting reason, it offers to record a
decision record so later surveys don't suggest it again.

## Look back on a session

`/vibes:retro` looks back on a session, this one unless you name another by
its id or transcript, and suggests what in the project would have made it
go better: a check that would have caught a mistake, a coding standard a
reviewer needed, a pointer to a file an agent hunted for, or a fix for
wasted calls. Give it a focus, such as
`/vibes:retro the commit gate blocks`, to look there first.

A read-only agent works from a digest of the transcript that
`bin/session-digest` writes, which numbers every tool call, such as `a3.7`
for the third subagent's seventh. Each suggestion cites the calls and
messages behind it, and says when it rests on a single moment. The report,
`.vibes/retro-<date>-<n>/retro.md`, is shown to you.

It changes nothing, and it only ever tightens:

- **A change that would loosen a check,** such as dropping a lint rule,
  excluding files or skipping a review round, is never a suggestion. It's
  listed apart, under **Would loosen a check**, with what it would stop
  catching, and is applied only when you name it on its own.
- **Tool economy looks only for waste,** such as the same file read again
  unchanged or a failing command retried as it was. The review rounds, the
  gate and the tests cost a lot on purpose, and are never counted.
- **The commit gate asks you** before any commit that loosens it, whoever
  made the change.

Name the suggestions you want, and each is applied as a commit of its own.

## Write a pull request

`/vibes:pr` writes the body of a pull request for the checked-out branch,
for a reviewer who hasn't seen the work. It runs only when you ask: a
vibes run never opens or writes a pull request by itself.

- **The summary** is the smallest view that makes the change clear, such
  as a short diagram, a file tree or a few lines of pseudocode.
- **The evidence** is before and after, quoted from the records: a
  reproduction that went from `RED` to `GREEN`, measurements from an
  optimise run, the line each new test failed on before its code existed,
  each requirement with the test that covers it, and the reviewers'
  verdicts. Without a vibes run, it uses the branch's commits and diff,
  and runs `scripts/check --all` at the branch's head.
- **The merge risk** says whether the change is a one-way door, such as
  a decision record, a migration, a public format or a new dependency, or
  a two-way door undone by a revert, and what calls the changed code.

Every claim comes from a record, listed in `sources.md` beside the body,
and what no record shows is marked unverified. It fills the repository's
own pull request template when there is one, and leaves out anything
private, such as `.vibes/` paths. You read it first: it pushes the branch
and opens the pull request, as a draft or ready for review, or replaces
an existing one's body, only when you say so, and never forces a push. It
opens it through [your issue tracker's](#your-issue-tracker) commands.

## Work from issues

vibes reads issues through [your issue tracker's](#your-issue-tracker)
commands. Anyone can write an issue, so **its text is untrusted:** only the issue
reader, which can write nothing but its brief, ever reads it. It turns the
issue into a brief, the task in the project's words, what the reporter
saw and what would close it, and lists anything in the issue that tries
to direct an agent, such as a hidden request to run a script or reveal a
token. Runs start from the brief, never the issue.

- **Start a run from an issue:** `/vibes:vibe #123`, `/vibes:debug #45` or
  `/vibes:optimise #67`. You confirm the brief before the run starts, even
  an unattended one, and `/vibes:pr` links the pull request with the
  tracker's closing line, such as `Closes #123`.
- **Triage:** `/vibes:triage` takes the open issues without a triage
  label, or the ones you name. For each, it checks whether the code
  already does it and whether a decision record ruled it out, reproduces
  a bug with `bin/repro`, and proposes `ready-for-agent`,
  `ready-for-human`, `needs-info` or `wontfix`, with a short reply to the
  reporter. Nothing is posted until you approve the batch. An issue with
  anything suspicious in it is never `ready-for-agent`. A `wontfix`
  issue is closed, keeps its label, and its reply says it's closed as
  not planned, and why, since not every tracker records a reason for
  closing: GitLab's Free tier doesn't.
- **Pick up approved issues unattended:** `/vibes:pickup` takes the
  oldest issue you approved as `ready-for-agent` and runs the workflow its
  brief names, unattended, on a local branch. It takes an issue only if
  nobody has edited it or commented on it since you approved it, works
  from the brief you approved, and never posts, labels, pushes or opens
  a pull request. It takes one issue a run; `/loop /vibes:pickup` works
  through them.

Approvals are kept in `.vibes/issues/` on the machine you triaged on.

## Your issue tracker

vibes knows no tracker itself. The project names the commands for its
own in `.vibes-tracker`, at the repository's root, and vibes runs those,
through `bin/tracker`. `/vibes:tracker` sets it up: it drafts one for a
GitHub or GitLab remote, or writes one for another tracker, such as
Forgejo, SourceHut or Jira, from its CLI's documentation, and has you
check it before it's committed. Each line is a kind, a tab, and its value:

```text
issue-id	[0-9]+
closes	Closes #{id}
state-open	OPEN
read	gh issue view {id} --json title,body,comments,labels,state,url
read.title	.title
comment	gh issue comment {id} --body-file {body-file}
```

[skills/tracker/templates/](skills/tracker/templates/) has the drafts,
and the top of [lib/tracker/cli.py](lib/tracker/cli.py) every kind.

The file holds commands that run as you, with your tracker's
credentials, so a change to it is an attack on you. vibes defends against
one in layers:

- **You approve the commands, not the repository.** Nothing runs until
  you run `bin/tracker approve` in your own terminal. It shows every
  command, and keeps your approval in the repository's git directory,
  never in the checkout, so nothing committed can approve itself. Any
  change needs approving again, and an unattended `/vibes:pickup`
  stops rather than run a changed file.
- **It's read from the default branch,** never the checkout, so a branch,
  or a contributor's pull request you've checked out, can't change it.
- **No shell.** Each command is one program and its arguments, run
  directly, so nothing can be piped, redirected or substituted. Only
  trackers' own tools run, unless you allow another when approving, and
  `curl` reaches only the hosts the file names, over https.
- **Issue text never becomes a command.** Each value is checked before
  it fills its placeholder: an issue id must match the file's pattern, no
  value may begin with `-`, and only `{body-file}` may name a file, one
  in `.vibes/`.
- **Reading and posting are kept apart.** Comments, labels, closing an
  issue and pull requests run only from a batch, which you confirm before
  it runs, and which no subagent may run. `/vibes:pickup` never posts.
- **Your other secrets stay out.** The commands get only the tokens the
  file names, besides what any program needs, such as `PATH` and `HOME`.
- **It's guarded like the gate.** No agent may approve it or touch the
  approval, no subagent may write the file, the commit gate asks you
  before a commit that changes it, and `/vibes:review-pr` marks a change
  to it HIGH.

What's left: a command you approve yourself runs as you, so read them
before you approve. Agents have no terminal, but a program can fake one,
so the hook that stops agents approving guards against mistakes and
instructions picked up from an issue, not a determined attacker. And
`/vibes:review-pr` still fetches GitHub pull requests with `gh` directly,
as [Review a pull request from outside](#review-a-pull-request-from-outside)
says, since its commands are fixed and part of vibes, not the project's.

## Build in parallel

A rebuild plan is also a task graph: each batch says which batches it
needs first, and which files it changes. Batches that don't need each
other, such as two edges built on the same core, are built at once, each
by its own builder in its own git worktree, `.vibes/workers/<n>`, on its
own branch, through the gate as usual. As each finishes, it's brought up
to date with the rebuild branch, checked again with `scripts/check --all`
if anything moved under it, and joined, so the rebuild branch ends with
every commit in a line, as if one builder had built them all.
`bin/plan-graph` says which batches are ready, and catches two that could
run at once but would change the same file.

How many at once depends on the machine and the project, so it's
measured, not guessed. `/vibes:capacity` runs the project's gate alone
and then twice at the same time, sampling memory and CPU, Docker's too,
and settles on a number: what memory and CPU allow, never more than 4,
and 1 when two at once ran little faster than one after the other. It
caches the answer in `.vibes/capacity.json`, and a run measures again by
itself when the machine, the gate or the project's size has changed, or
after 30 days, or uses fewer builders when memory is already in use. A
builder that runs out of memory lowers the number for later runs. Run
`/vibes:capacity` yourself after the project grows, or when you give
Docker more or less. The worktrees are reused from run to run, so what
they've built stays warm.

## Grill a plan

Before you start a task, `/vibes:grill <the plan or idea>` stress-tests
it. It maps every decision the plan leaves open and every fact it rests
on, settles what the code and the decision records already answer, has
the researcher look up the facts, and asks you the decisions **in
rounds**: each round holds only the questions whose prerequisites you've
answered, so you're never asked the CSV's delimiter before you've chosen
CSV, and each answer can make some questions moot and raise new ones. It
ends when nothing is open and you agree it's what you mean, with a
decisions document `/vibes:vibe` can start from, and offers to record the
lasting decisions and new terms.

A vibes run asks its spec's open questions the same way: the designer
marks what each waits on, the first round asks everything that waits on
nothing, and the facts are researched while you answer.

## Steps only you can do

Some steps need a person: signing in to a provider's dashboard, creating
an API key, setting a CI secret. Instead of a list in the report,
`/vibes:wizard <the procedure>` writes a **wizard**, a bash script you run
in your own terminal. It walks you through one stage at a time: it opens
each page, says exactly what to click, and saves what you paste back in
`.env`, created readable only by you, or as a GitHub secret or variable.
Secrets go into hidden prompts, straight to where they're saved, so they
never pass through the conversation. It asks before anything that can't
be undone, and you can stop and run it again: it keeps what it saved.

Each step comes from the provider's own documentation, found by the
researcher, and the wizard names its source and the date it was checked;
a step the documentation doesn't settle is marked for you to check. The
stages are written onto a small wizard library, tested on Bash 3.2 and
later, and the script is checked with `bash -n` and ShellCheck, but never
run by an agent.

A run writes one for you at its end when `bin/setup-needs` finds the
branch needs settings nobody has provided, such as a key the code now
reads, and the report gives the command. Keep a wizard you'll need again,
such as for each new developer, as `scripts/setup-<thing>`.

### Changes that can't be undone

`/vibes:runbook <the change>` writes a **runbook** for a change that can't
simply be undone, such as a production migration, a DNS cutover or
rotating a signing key. It's a script you run in your own terminal, like
a wizard, and it builds on the wizard library, with fences around each
change:

- **Checks first:** each step checks what it needs before it changes
  anything, such as that a fresh backup exists, and stops if one fails.
- **One-way steps wait for you:** before each, it says what changes for
  good and how to recover, and runs it only once you type the step's
  name.
- **Verification after:** each step checks its change worked before the
  next starts, and stops with the recovery if it didn't, as it does when
  any command fails.
- **A log, and resuming:** each step is logged beside the script, and a
  second run starts from the step that stopped, never repeating one that
  finished.

Read it first with `bash <runbook> --plan`, which shows every step, each
one-way step with its recovery, and changes nothing. It refuses to run
without a person at a terminal. Each command comes from the project's own
scripts or the provider's documentation, found by the researcher, and the
steps are confirmed with you before it's written. `/vibes:pr` offers one
when it judges a change a one-way door someone must deploy, such as a
migration. Keep one you'll need again, such as a yearly key rotation, as
`scripts/runbook-<thing>`.

## Prototype a decision

Some decisions you can only judge once you can click them: whether an
order can be cancelled after part of it ships, or how a settings page
should be laid out. `/vibes:prototype <the question>` builds a throwaway
prototype that answers one, on a `spike/prototype-<slug>` branch that's
never merged.

- **A logic prototype,** for how something should behave, is one HTML
  file anyone can open: free-play buttons, the state after every click,
  and scenarios that walk through the awkward cases, in the business's
  words. You confirm or correct what each scenario does, and the
  confirmed scenarios become examples in the spec, which the build turns
  into its first tests. Send it to someone who knows the domain with a
  questionnaire, if they're the one to judge. `bin/prototype-check`
  checks it loads nothing from outside and keeps its logic apart from
  the page.
- **A UI prototype,** for how a screen should look, builds three variants
  of the real page, each under a different constraint: everything at
  once, one main action, or in steps. A check makes sure they differ in
  structure, and a bar on the page, hidden in production builds, flips
  between them. You pick one, or parts of each.

The answer goes into `answer.md`, which a vibes run's designer writes
into the spec. A run offers a prototype for a decision that's hard to
judge in words; an unattended run never builds one.

## Ask someone else

Some questions only someone else can answer, such as a client, a domain
expert or another team. `/vibes:questionnaire` writes a questionnaire for
them to fill in on their own or with you in a meeting. It asks you only
who it's for and what you need back, then writes one question per idea,
most important first, with the options known so far and room to answer,
and nothing the recipient shouldn't see, such as secrets or file paths.

A vibes run offers one when a decision in its spec needs someone else:
it waits for the answers as it would for yours, and the spec records who
gave them. An unattended run takes its recommended answers instead.

## Install as a Claude Code plugin

This repository is its own plugin marketplace. In Claude Code 2.1.275 or
later:

```text
/plugin install vibes --marketplace softwareforliberty/vibes
```

Or in two steps:

```text
/plugin marketplace add softwareforliberty/vibes
/plugin install vibes@vibes
```

To try a local checkout without installing it, start Claude Code with
`claude --plugin-dir /path/to/vibes`.

If you run sessions in git worktrees, install it at user scope, the
default for `claude plugin install vibes@vibes` in a shell, or enable it in
each worktree. A plugin enabled only for the main checkout can load its
skills in a worktree session but not its agents. `/vibes:vibe`,
`/vibes:optimise`, `/vibes:debug`, `/vibes:survey`, `/vibes:review`,
`/vibes:review-pr` and `/vibes:retro` then stop and say so, rather than run
without them.

The plugin provides:

- **Skills:** `/vibes:vibe`, `/vibes:optimise`, `/vibes:debug`,
  `/vibes:survey`, `/vibes:review`, `/vibes:review-pr` and `/vibes:retro`,
  plus `vibes:test-driven-development`, `vibes:atomic-commits` and
  `vibes:commit-gate`, which agents use on their own when they apply.
- **Agents:** `vibes:designer`, `vibes:spiker`, `vibes:builder`,
  `vibes:profiler`, `vibes:optimiser`, `vibes:diagnoser`, `vibes:researcher`,
  `vibes:surveyor`,
  `vibes:interface-designer`, `vibes:commit-message-suggester`,
  `vibes:retrospective` and the reviewers, such as `vibes:security-reviewer` and
  `vibes:project-docs-reviewer`.
- **The commit gate hook,** which runs before every `git commit` the agent
  makes, and asks you before one that loosens the gate.
- **The check-file hook,** which formats and lints each file an agent
  writes, as soon as it's written, in projects with `scripts/check-file`.
  It also checks the files a shell command changes, except a command that
  runs git.
- **The guide check hook.** The first time an agent, or each subagent, writes a
  kind of file in a conversation without having read its guide, it names the
  guide for it, and warns when the project's gate doesn't check that guide yet.
  In a project with the commit gate, it refuses that first write until the
  agent has read the guide, and lets the next one through. Elsewhere it only
  reminds, after the write, because Claude Code shows a hook's message
  alongside the tool's result.

### Updates

Each release has a version, and [CHANGELOG.md](CHANGELOG.md) says what
changed in it. An installed plugin stays on its version until a new release,
so work in progress on `master` never reaches you. To update, run
`claude plugin update vibes@vibes` in a shell, or
`/plugin marketplace update vibes` and then `/reload-plugins` in a session.
To update automatically, turn on auto-update for the marketplace under
`/plugin` > **Marketplaces**.

To release, move the changelog's Unreleased entries under a new version
and date, set the same version in `.claude-plugin/plugin.json`, commit
both, and tag the commit `v<version>`. Until 1.0, a minor version marks any
change in how the workflow, the gate or the guides behave.

## Other agents

vibes is built for Claude Code, and also runs in GitHub Copilot CLI, Codex
and Gemini CLI, with as much of its enforcement as each allows. Each needs
Bash, git and Python 3. Each loads vibes, and the hooks are tested with the
input each sends them, but no workflow has yet run end to end in any of
them.

### Copilot CLI

Copilot CLI reads the plugin as Claude Code does, skills, agents and hooks:

```sh
copilot plugin marketplace add softwareforliberty/vibes
copilot plugin install vibes@vibes
```

Its commands have no prefix: `/vibe`, `/optimise`, `/debug`.

### Codex

Codex reads the plugin's skills and hooks, but a plugin can't carry agents,
so `bin/host-files` writes them as Codex's custom agents:

```sh
codex plugin marketplace add softwareforliberty/vibes
codex plugin add vibes@vibes
"$(ls -d ~/.codex/plugins/cache/vibes/vibes/* | sort -V | tail -n 1)/bin/host-files" codex ~/.codex/agents
```

Then run `/hooks` in a session, and trust vibes' hooks: Codex skips a
plugin's hooks until you do. Start a workflow by naming its skill, such as
`$vibes:vibe add CSV export`. Run `host-files` again after each update.

### Gemini CLI

Gemini CLI reads only its own extensions, so `bin/host-files` writes one,
from a checkout of this repository:

```sh
bin/host-files gemini ~/.vibes-gemini
gemini extensions link ~/.vibes-gemini
```

The commands are as in Claude Code: `/vibes:vibe`, `/vibes:optimise`. The
extension uses the checkout for everything else, so keep it where it is,
and run `host-files` again after updating it.

### What each enforces

| | Claude Code | Copilot CLI | Codex | Gemini CLI |
|---|---|---|---|---|
| The commit gate on the agent's commits | Yes | Yes | Once you trust the hooks | Yes |
| A commit that loosens the gate | Asks you | Asks you | Refused | Refused |
| Posting to the issue tracker | Asks you | Asks you | You run the batch | You run the batch |
| Formatting and linting each file written | Yes | Yes | Yes | Yes |
| The guide check | Yes | Yes | Yes | Yes |
| Reviewers write only their findings | Yes | Yes | Yes | No |
| Each agent's tools | As listed | As listed | All, but an agent listed without Bash may only run commands that read | As listed |
| Each agent's model | As listed | Not checked | The session's | The session's |

Elsewhere, the guide check counts a guide as read if the session's
transcript names its files, even before the conversation was compacted.
Gemini CLI doesn't say which agent is calling a tool, so a reviewer there
has no shell, but could write any file. Codex can't ask you questions
outside Plan mode, so vibes asks in its reply, and waits for yours.

The rest is plain Markdown and Bash, for any agent or person: read the
guides in `guides/`, copy a guide's `.editorconfig` and tool configs into
your project, and install the commit gate as a git hook, below, which
holds whatever makes the commit.

## The commit gate

A project opts in by adding an executable `scripts/check` that checks
formatting, lints and runs the tests. The `commit-gate` skill
writes it from the `tools.md` of each guide the project needs, and names
those guides on a `# Guides:` line in it:

```bash
# Guides: languages/BASH languages/C++ tools/Docker
# No guide: *.ipynb
```

Once it exists, the gate:

- blocks a commit with a file that needs a guide the `# Guides:` line
  doesn't name, such as the project's first Python file or Dockerfile,
  until `scripts/check` runs that guide's checks too
- blocks a commit with a file no guide covers, until a `# No guide:` line
  lists it, so a file is never quietly left unchecked
- runs `scripts/check` before each commit, and blocks the commit if it fails;
  for a commit of documents only, such as a spec, it runs
  `scripts/check --static`, without the tests
- refuses to commit while there are unstaged changes or untracked files, so
  the checks test exactly what's being committed
- blocks a commit whose subject is longer than 50 characters
- blocks a commit that adds a line carrying a `/vibes:debug` run's debug
  tag, such as `vibes-debug-month-end`
- runs no checks on `spike/*` branches, apart from the subject's length
- in an agent's session, also blocks `git commit -a` and `--no-verify`
- in an agent's session, asks you to confirm a commit that loosens the gate
  itself: one that deletes `scripts/check` or `scripts/check-file`, makes
  either not executable, removes or changes a line so that a word of it is
  lost, such as a check, an option or a guide, or lets a failure pass, such
  as with `|| true` or an early `exit`. Extending the gate keeps every word,
  so it goes through without asking. Where nobody can answer,
  as in `claude -p`, or the host can't ask from a hook, as in Codex and
  Gemini CLI, the commit is refused

`scripts/check` runs its static checks first, and stops before the tests
if any fail, since the tests are the slow part. It runs only the fast
tests; the slow ones, such as boot or smoke tests, run with
`scripts/check --all`, once at the end of each batch of work and before a
task finishes.

Alongside it, `scripts/check-file` runs the per-file checks, formatting in
rewrite mode and linting, on the files it's given. The plugin runs it on
each file an agent writes, with the Write and Edit tools or a shell
command, except on `spike/*` branches and for the spiker, so a format or
lint error is fixed straight away rather than at the commit. Type checks
and tests need the whole project, so they stay in `scripts/check`.

For a project with specs, `scripts/check` also checks the tests'
requirement markers. Each test names the requirements it covers, such as
`# Covers: order-export R1, R4`. Every commit fails on a marker naming a
requirement the spec doesn't have, and `scripts/audit`, run before a task
finishes, fails on any requirement no test covers.

Projects without `scripts/check` are never blocked. To enforce the gate for
every commit, including your own, install the git hooks from the
repository's root:

```sh
~/.claude/plugins/cache/vibes/vibes/<version>/bin/install-git-hooks
```

or the same script in another agent's copy of vibes, such as
`~/.codex/plugins/cache/vibes/vibes/<version>/bin/install-git-hooks`.

It writes a small stub for each hook, not a link: the stub runs the hook
from the newest vibes installed, so updates apply and removing an old
version breaks nothing, and refuses the commit if vibes is gone. It leaves
a hook that isn't vibes' alone unless you add `--replace`. `/vibes:vibe`
and `/vibes:optimise` run it at the start of each run, which also mends
hooks installed as links by earlier versions.

The hooks need Bash, git and `realpath`. The agents' hooks also use `jq`
or Python 3 to read their input, and Python 3 for Codex's and Gemini
CLI's.

## License

[0BSD](LICENSE): use, copy, modify and share any of it, for any purpose, with
no conditions and no need to credit the source. That includes copying the
style guides, skills, agents and config templates into your own projects.
