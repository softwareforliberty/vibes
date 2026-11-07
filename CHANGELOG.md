# Changelog

Every release of the vibes plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major
version is 0, a minor release may change how the workflow, the gate or the
guides behave, and says so under **Changed**.

## [Unreleased]

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

[Unreleased]: https://github.com/softwareforliberty/vibes/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/softwareforliberty/vibes/releases/tag/v0.1.0
