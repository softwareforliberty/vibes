# Changelog

Every release of the vibes plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major
version is 0, a minor release may change how the workflow, the gate or the
guides behave, and says so under **Changed**.

## [Unreleased]

### Added

- **The designer keeps the project's glossary and decision records.**
  - **The glossary:** the spec uses its terms and none of the words it
    says to avoid, and a clash between the task's words and the glossary
    becomes an open question. Each new term the task brings into the
    project is added, and `GLOSSARY.md` is created when the first one
    needs it.
  - **Decision records:** the design keeps to the existing records, and
    asks before replacing one. Each new decision that is hard to reverse,
    surprising without its reason and a real choice gets a short record
    in `docs/adr/`, or wherever the project keeps them.
  - **Reviews:** the spec reviewer checks the glossary, the architecture
    reviewer checks the new records, and the project docs reviewer treats
    breaking a record as a BLOCKER and using a word the glossary says to
    avoid as MAJOR.
  - **The final report** lists the terms and records the task added.
- **`/vibes:retro` looks back on a session** and suggests changes to the
  project that would make the next one go better, such as a check, a
  coding standard or a pointer to a file, each citing the calls behind
  it. It changes nothing. A change that would loosen a check is listed
  apart and applied only when named on its own, and the review rounds,
  the gate and the tests are never counted as waste.
- **`bin/session-digest`** prints a compact digest of a session's
  transcript and its subagents': every tool call on one line with a
  reference, and the failures, hook blocks, retries, repeated calls and
  largest results.

### Changed

- **The commit gate asks before it's loosened.** In Claude Code, a commit
  that deletes `scripts/check` or `scripts/check-file`, makes either not
  executable, or removes or changes a line of either so that a word is
  lost now needs your confirmation, and is refused where nobody can give
  it. Builders report a check they think must change instead.

## [0.6.1] - 2026-11-20

### Fixed

- **A commit behind `time`, `env`, `nice` or another wrapper skipped the
  gate.** The Claude Code hook looked for `git commit` only at the start of
  a command, so `time git commit …` ran no checks; it now finds it anywhere
  in the command, including in a subshell.
- **The git hooks broke silently when vibes updated.** They were links into
  one plugin version's folder, and git skips a hook whose link no longer
  resolves, so removing an old version turned the gate off. The new
  `bin/install-git-hooks` writes a small stub for each hook that runs the
  newest vibes installed, and refuses the commit when there's none.
  `/vibes:vibe` and `/vibes:optimise` run it at the start of each run,
  which replaces the old links and adds a missing `commit-msg` hook, and
  the Claude Code hook blocks a commit while a vibes hook's link is broken,
  saying how to reinstall.

## [0.6.0] - 2026-11-20

### Added

- **The project docs reviewer** checks the spec, design and code against
  the project's own documents, such as its README, architecture notes,
  decision records and earlier specs, in every review of `/vibes:vibe` and
  `/vibes:optimise`. It decides from their headings which apply, and stops
  at once when none do; a project with no documents never runs it. The
  designer corrects the spec and design to follow a document, and asks you
  when the task seems meant to change what the document says.
- **`bin/project-docs`** lists a project's own documents, skipping release
  notes, licences, templates, vendored code and test data.
- **The commit message suggester** writes the message for each commit the
  workflows' main agent makes itself, with a subject it has counted to 50
  characters or fewer.
- **A `commit-msg` git hook,** `hooks/git_commit_msg`, which holds every
  commit to the same limit.
- **`/vibes:review` reviews the checked-out branch,** uncommitted changes
  included, with the same scan, guides and reviewers as
  `/vibes:review-pr`, as your own work: the spec reviewer joins when the
  branch has a spec, and you can have the findings fixed test-first.
  `pr-prepare --branch` and `pr-scan report --branch` prepare and report
  it, without touching the working tree, index or branches.
- **`/vibes:review-pr`'s panel** gains the project docs reviewer when the
  project has documents.
- **Evals** for the project docs reviewer and the commit message
  suggester.
- **Each file is formatted and linted as it's written.** A new
  `PostToolUse` hook runs the project's `scripts/check-file` on every file
  an agent writes: it fixes the formatting and shows the agent any lint
  problems at once, rather than when the commit gate fails. It skips
  `spike/*` branches, the spiker and files git ignores, and does nothing
  in projects without `scripts/check-file`. The commit-gate skill writes
  it, and the vibe and optimise workflows add it to a gate that lacks it.
  It also checks each file a shell command writes, such as through a
  heredoc or `sed`, by comparing the changed files before and after the
  command; a command that runs git is left alone. Builders were making
  almost every edit through the shell.
- **`scripts/check --static` and `--all`.** The gate runs `--static`, the
  checks without the tests, for a commit of documents only, such as a
  spec. `--all` adds the slow tests, such as boot and smoke tests, which no
  longer run on every commit: builders run them once at the end of each
  batch, and the workflows before they finish. A `scripts/check` that
  ignores its arguments runs everything, as before.
- **A notification when a run needs you.** `/vibes:vibe` and
  `/vibes:optimise` send a push notification, where the session can, before
  they stop to ask you something, and ask everything they have at once.

### Changed

- **Commit subjects are 50 characters at most,** not 50 where you can and
  72 at most. The Claude Code gate hook reads the subject from
  `git commit`'s `-m`, heredoc or `-F` message and blocks a longer one
  before running the checks, on every branch.
- **The builder runs the type checks before each commit,** so the gate's
  full run seldom fails on a small mistake and runs again. Tests and
  coverage stay with the gate. It writes files with Write and Edit rather
  than the shell.
- **`scripts/check` fails fast:** the commit-gate skill now has it run the
  static checks first and stop before the tests if any fail, so a lint
  error no longer costs a full test run. The vibe and optimise workflows
  bring an older gate up to date.
- **The audit runs alongside the rebuild review,** on the rebuild's head
  in a worktree of its own, instead of after it, and runs again at the
  finish only when the dependencies changed.
- **The main agent no longer reruns `scripts/check` after each batch:** the
  gate ran it on every commit, and the builder ran the slow tests.

### Fixed

- **Reviewers write their findings file before they reply.** Some put
  their findings in their reply instead, or held back because Claude Code
  tells subagents not to write report files, so the main agent had to ask
  again. Each reviewer's output section now starts by saying the file is
  the output its brief asks for, and that a review left in the reply is
  lost.

## [0.5.1] - 2026-11-14

### Changed

- **`/vibes:vibe`, `/vibes:optimise` and `/vibes:review-pr` check their
  agents are loaded before they start,** and stop if they aren't, rather
  than stand in for them with general agents, which have none of their
  tool limits and slip past the hooks that keep reviewers read-only. A
  plugin enabled only for the main checkout can load its skills but not
  its agents in a git worktree session; the README says how to avoid it.

## [0.5.0] - 2026-11-13

### Added

- **`/vibes:optimise` makes a program faster where a profile shows the
  time goes.** It profiles a baseline, plans and specs the optimisation,
  tries each idea as a spike measured against the best version so far
  until the ideas stop paying, has the winner reviewed, then rebuilds it
  test-first and measures it again. `/vibes:vibe` never uses it.
- **`bin/bench`** runs a benchmark harness against two trees in
  interleaved pairs, and decides whether the change is better beyond the
  noise an A/A run measured, with guard rails such as peak memory.
- **The profiler and optimiser agents.** The profiler measures and never
  changes the code, which a hook enforces; the optimiser builds and never
  measures.
- **`performance/`:** the method for measuring and profiling, and the
  profilers and benchmark tools for each guide.
- **Evals** for the profiler, the optimiser and the whole command, on a
  small Python tool with a quadratic hot spot.

## [0.4.0] - 2026-11-13

### Added

- **`/vibes:review-pr` reviews a pull request from outside the project,**
  above all for malicious changes like the XZ Utils backdoor. It never runs
  the pull request's code, and never posts to GitHub: it writes a report and
  a draft comment for you.
- **`bin/pr-prepare` and `bin/pr-scan`** fetch a pull request and scan it,
  reading it only from git objects. The scan checks every file and every
  commit for hidden payloads, obfuscation, build-time code, weakened
  checks, pin and key changes, CI and agent-config risks, and text aimed at
  AI reviewers, and its HIGH findings can't be cleared by a reviewer.
- **The supply-chain reviewer,** used only by `/vibes:review-pr`, with its
  standards in `security/malicious-changes.md`.
- **A `.vibes-review` file** lists a project's protected paths, test data,
  allowed binaries and hosts, and is read from the base branch only.
- **Evals** for the supply-chain reviewer, on twelve versions of a pull
  request to a small C library, and for the whole command.

## [0.3.0] - 2026-11-09

### Fixed

- **The reviewer evals' clean change names the requirements its tests
  cover.** Its tests had no `# Covers:` markers, which the
  test-driven-development skill requires, so the test reviewer rightly
  flagged the clean change in every run.
- **pip-audit no longer fails on the project itself.** The Python guide's
  command skips editable packages, so the project, installed with
  `pip install -e .` and never published, isn't looked up on PyPI.

### Changed

- **The designer fixes the review findings in the spec and design,** in a
  new `revise` mode, so the main agent no longer edits them itself.
- **The main agent no longer reads the findings.** Each reviewer writes its
  own findings file and replies in one line, and the fixer, the designer
  or the builder, decides on each finding and records the response. The
  builder and the spiker write their own reports, and the designer writes
  the rebuild plan. A hook lets a reviewer write only its own findings
  file, and the reviewers write it even when they approve with no
  findings.
- **The spec and design stay in proportion to the task:** they specify
  what users would notice, follow the platform's conventions instead of
  restating them, and the reviewers don't hold them up over details that
  don't matter.
- **A fix to a MINOR finding isn't reviewed again,** and the rebuild's last
  round brings back only the reviewers whose area a BLOCKER or MAJOR fix
  changed.
- **The commit gate is set up while the spec is written,** at medium
  effort, with the spec drafted where git ignores it until the gate is
  committed.
- **A small new program whose design is clear is a medium task,** with no
  spike.
- **The builder shows every new test failing before writing its code,**
  with each red run's failure line in its report, since builders in
  trials 3 and 8 wrote some tests and code together.
- **The rebuild plan has fewer entries and batches:** about half as many
  entries as the spec has ids, and two or three batches of eight to twelve
  entries for one tool or feature, since each new builder reads the
  skills, guides, spec and design again.

## [0.2.0] - 2026-11-08

### Fixed

- **The commit gate missed some of the agent's commits.** A commit made
  with `git -C <dir> commit`, a bare `git commit`, or a commit after `cd`
  into another repository skipped the gate. The hook now runs on every
  Bash command, finds the repository each commit is in and checks it
  there, and blocks a commit whose repository it can't work out when the
  session's own repository is gated.

### Changed

- **The gate's tools are installed only from their own projects'
  sources,** never from a package of the same name in another registry.
- **The spike is reviewed once, and its code is never fixed.** Findings that
  change behaviour or structure correct the spec and design, which are
  approved again before the rebuild. An uncertain design change is tried in
  the spike once more, and every other finding becomes a lesson for the
  rebuild.
- **The builder and the spiker run on Sonnet.**
- **The rebuild plan has a section per batch,** with entries that each
  drive one piece of code, and each builder reads only its own section and
  the parts of the spec and design its entries need.
- **A test that passes straight away is checked by reading the code,** not
  by breaking it on purpose.
- **The main agent keeps its records short:** a line per step in
  `state.md`, and a line per reviewer and finding in each round.

## [0.1.0] - 2026-11-07

The first versioned release.

### Added

- **The vibe workflow** (`/vibes:vibe`): a complete spec, then a design,
  spike, review rounds, a test-first rebuild and a final review, scaled to
  the task's size, with unattended runs and resuming an interrupted run.
- **Agents:** the designer, the spiker, the builder, and ten reviewers for
  the spec, architecture, cleanliness, style, idioms, resource leaks,
  performance, bugs, security and tests.
- **Skills** for test-driven development, atomic commits and setting up the
  commit gate.
- **The commit gate,** for Claude Code and for git: every commit passes the
  project's `scripts/check`, the gate checks every guide the commit's files
  need, and requirement markers in tests are checked against the specs.
- **Guides** for 40 programming languages, web formats, data formats and
  database dialects, build systems, and tools (Docker, GitHub Actions,
  OpenTofu and Nix), each with a coding style, idioms, and checking tools,
  including mutation testing, with drop-in configs.
- **Architecture guides** for web, desktop and mobile applications,
  command-line tools, libraries, OS components and embedded systems, and
  the programming principles every change is held to.
- **Hooks** that make an agent read a file's guide before writing it, and
  keep the spec reviewer from changing files or git state.
- **Evals** for each reviewer, and for choosing the review panel.
- **A worked example** of a large, unattended run, in
  [`docs/example/`](docs/example/README.md).

[Unreleased]: https://github.com/softwareforliberty/vibes/compare/v0.6.1...HEAD
[0.6.1]: https://github.com/softwareforliberty/vibes/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/softwareforliberty/vibes/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/softwareforliberty/vibes/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/softwareforliberty/vibes/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/softwareforliberty/vibes/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/softwareforliberty/vibes/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/softwareforliberty/vibes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/softwareforliberty/vibes/releases/tag/v0.1.0
