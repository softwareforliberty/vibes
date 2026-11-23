# vibes

Guides and tooling for clean vibe coding: letting an AI agent write the code,
while holding it to the standards of careful, experienced developers.

- **`guides/`:** 59 guides, grouped by kind: `languages/` for 40
  programming languages, `web/` for HTML, CSS and Sass, `data/` for SQL,
  database dialects, data formats and schema languages, `build/` for
  CMake, Make and linker scripts, and `tools/` for Docker, GitHub Actions,
  OpenTofu and Nix. Each has a `coding-style.md`, an `idioms.md` and a
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
- **`bin/session-digest`:** prints a compact digest of a Claude Code
  session's transcript, for a retrospective. It's in
  `lib/session_digest/`, and its tests in `tests/session_digest/`.
- **`skills/`:** agent skills for the workflow, optimising performance,
  reviewing your own branch or an outside pull request, looking back on a
  session, test-driven development, atomic commits and setting up the
  commit gate.
- **`principles.md`:** the programming principles every change is held
  to, such as SOLID, DRY and KISS.
- **`architecture/`:** how to structure software: rules for every kind,
  and a guide each for web, desktop and mobile applications, command-line
  tools, libraries, OS components and embedded systems.
- **`security/`:** how malicious changes hide, for the supply-chain
  reviewer.
- **`performance/`:** how to measure and profile a program, and the
  profilers and benchmark tools for each guide, for the profiler and the
  optimiser.
- **`agents/`:** the designer, the spike agent, the builder, twelve
  reviewer agents, the profiler and optimiser, the commit message
  suggester and the retrospective.
- **`hooks/`:** the commit gate, for Claude Code and for git; a guide
  check that makes the agent read the guide for each kind of file before
  writing it; and a guard that keeps the reviewers, the commit message
  suggester and the retrospective from changing anything but the
  reviewers' own findings files and the retrospective's report, and the
  profiler from changing the code. The commit gate also refuses a subject
  longer than 50 characters, and asks you before a commit that loosens
  the gate itself.
- **`evals/`:** evals that check each reviewer agent finds the defects in
  its area and approves clean code, that the workflow picks the right
  reviewers for a change, that a pull request review catches malicious
  changes, that the profiler and optimiser find and measure the hot spot,
  that the project docs reviewer finds a contradiction and skips documents
  that don't apply, that suggested commit subjects fit in 50 characters,
  and that a retrospective suggests a check without loosening one, run
  with `claude plugin eval`.

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

Add `unattended` to run it without stopping to ask you anything, such as
`/vibes:vibe unattended: <task>`. The main agent then makes the narrowest
choice for each open question, records it, and lists every such decision
first in its final report. It still stops rather than touch anything that
could lose your work.

1. **Spec.** A designer subagent writes a complete spec: every requirement,
   error and edge case, each testable, in proportion to the task. You
   answer any open questions, and a spec reviewer checks it until it's
   complete. The spec uses the project's glossary, and each new term the
   task brings is added to it. Meanwhile, another subagent sets up the
   commit gate.
2. **Design.** The designer writes the design to the spec, and the
   architecture reviewer checks it before any code exists. The design
   keeps to the project's decision records, and each new decision that's
   hard to reverse, surprising and a real choice gets a short record of
   its own, in `docs/adr/` or wherever the project keeps them. The spec
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
   blocked if anything fails. Each batch ends with the slow tests too.
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
`/vibes:optimise`, `/vibes:review`, `/vibes:review-pr` and `/vibes:retro`
then stop and say so, rather than run without them.

The plugin provides:

- **Skills:** `/vibes:vibe`, `/vibes:optimise`, `/vibes:review`,
  `/vibes:review-pr` and `/vibes:retro`, plus `vibes:test-driven-development`, `vibes:atomic-commits` and
  `vibes:commit-gate`, which agents use on their own when they apply.
- **Agents:** `vibes:designer`, `vibes:spiker`, `vibes:builder`,
  `vibes:profiler`, `vibes:optimiser`, `vibes:commit-message-suggester`,
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

## Use without Claude Code

Everything is plain Markdown and Bash, so other agents and people can use it
too:

- Point the agent at a skill's `SKILL.md` or an agent definition in
  `agents/`, and replace `${CLAUDE_PLUGIN_ROOT}` with the path to your
  checkout of this repository.
- Read the guides in `guides/` directly, and copy a guide's `.editorconfig`
  and tool configs into your project.
- Install the commit gate as a git hook (see below).

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
- runs no checks on `spike/*` branches, apart from the subject's length
- in Claude Code, also blocks `git commit -a` and `--no-verify`
- in Claude Code, asks you to confirm a commit that loosens the gate
  itself: one that deletes `scripts/check` or `scripts/check-file`, makes
  either not executable, removes or changes a line so that a word of it is
  lost, such as a check, an option or a guide, or lets a failure pass, such
  as with `|| true` or an early `exit`. Extending the gate keeps every word,
  so it goes through without asking. Where nobody can answer,
  as in `claude -p`, the commit is refused

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

It writes a small stub for each hook, not a link: the stub runs the hook
from the newest vibes installed, so updates apply and removing an old
version breaks nothing, and refuses the commit if vibes is gone. It leaves
a hook that isn't vibes' alone unless you add `--replace`. `/vibes:vibe`
and `/vibes:optimise` run it at the start of each run, which also mends
hooks installed as links by earlier versions.

The hooks need Bash, git and `realpath`. The Claude Code hook also uses `jq`
or Python 3 to read its input.

## License

[0BSD](LICENSE): use, copy, modify and share any of it, for any purpose, with
no conditions and no need to credit the source. That includes copying the
style guides, skills, agents and config templates into your own projects.
