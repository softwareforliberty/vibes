# Changelog

Every release of the vibes plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major
version is 0, a minor release may change how the workflow, the gate or the
guides behave, and says so under **Changed**.

## [Unreleased]

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

[Unreleased]: https://github.com/softwareforliberty/vibes/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/softwareforliberty/vibes/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/softwareforliberty/vibes/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/softwareforliberty/vibes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/softwareforliberty/vibes/releases/tag/v0.1.0
