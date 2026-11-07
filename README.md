# vibes

Guides and tooling for clean vibe coding: letting an AI agent write the code,
while holding it to the standards of careful, experienced developers.

- **`guides/`:** 56 guides, grouped by kind: `languages/` for 40
  programming languages, `web/` for HTML, CSS and Sass, `data/` for SQL,
  database dialects, data formats and schema languages, `build/` for
  CMake, Make and linker scripts, and `tools/` for Docker. Each has a
  `coding-style.md`, an `idioms.md` and a `tools.md` listing FOSS linting,
  auditing and code-quality tools, plus a `.editorconfig` and drop-in config
  files for those tools. [guides/README.md](guides/README.md) says what
  goes in a guide.
- **`skills/`:** agent skills for the workflow, test-driven development,
  atomic commits and setting up the commit gate.
- **`principles.md`:** the programming principles every change is held
  to, such as SOLID, DRY and KISS.
- **`architecture/`:** how to structure software: rules for every kind,
  and a guide each for web, desktop and mobile applications, command-line
  tools, libraries, OS components and embedded systems.
- **`agents/`:** the designer, the spike agent and ten reviewer agents.
- **`hooks/`:** the commit gate, for Claude Code and for git, and a guard
  that keeps the spec reviewer from changing files or git state.
- **`evals/`:** evals that check each reviewer agent finds the defects in
  its area and approves clean code, run with `claude plugin eval`.

## The workflow

Run it in a project with `/vibes:vibe <task>`. The workflow below is for a
large task. The main agent sizes each task and tells you the size, and you
can name one yourself, such as `/vibes:vibe small: fix the date parsing`:

- **Small,** such as a fix in existing code: a spec, a test-first build
  and a focused review, with no design or spike.
- **Medium,** a feature whose design is clear: adds the design, and the full
  review panel.
- **Large,** new or uncertain work: everything below.

Add `unattended` to run it without stopping to ask you anything, such as
`/vibes:vibe unattended: <task>`. The main agent then makes the narrowest
choice for each open question, records it, and lists every such decision
first in its final report. It still stops rather than touch anything that
could lose your work.

1. **Spec.** A designer subagent writes a complete spec: every requirement,
   error and edge case, each testable. You answer any open questions, and a
   spec reviewer checks it until it's complete.
2. **Design.** The designer writes the design to the spec, and the
   architecture reviewer checks it before any code exists. The spec and
   design are committed in your repository, in `docs/specs/<task>/` or
   wherever the project already keeps them.
3. **Spike.** A subagent builds the whole task quickly to the spec and
   design on a `spike/<task>` branch.
4. **Review.** Reviewer subagents critique the spike in parallel, one each
   for architecture, code cleanliness, coding style, idioms, memory and
   resource leaks, performance, bugs and security. The spec reviewer
   verifies it meets every requirement in the spec.
5. **Fix.** The main agent fixes the findings, and the reviewers that asked
   for changes review again, until every reviewer approves (at most five
   rounds before it asks you). A fix that changes behaviour goes into the
   spec first, and so does every other change, all the way through. Each
   spec change is committed together with the code that implements it.
6. **Rebuild.** The spike is set aside, never merged. The task is rebuilt on a
   `vibe/<task>` branch, test-first, one atomic commit at a time.
7. **Gate.** Every commit runs the project's linters and full test suite, and
   is blocked if anything fails.
8. **Review again.** The same reviewers, plus a test-quality reviewer, check
   the rebuild, and their findings are fixed test-first. The spec reviewer
   verifies every requirement is met and tested.

Nothing is pushed or merged unless you ask.

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

The plugin provides:

- **Skills:** `/vibes:vibe`, plus `vibes:test-driven-development`,
  `vibes:atomic-commits` and `vibes:commit-gate`, which agents use on their
  own when they apply.
- **Agents:** `vibes:spiker` and the reviewers, such as
  `vibes:security-reviewer`.
- **The commit gate hook,** which runs before every `git commit` the agent
  makes.

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
formatting, lints and runs the full test suite. The `commit-gate` skill
writes it from the `tools.md` of each language the project uses. Once it
exists, the gate:

- runs `scripts/check` before each commit, and blocks the commit if it fails
- refuses to commit while there are unstaged changes or untracked files, so
  the checks test exactly what's being committed
- skips `spike/*` branches
- in Claude Code, also blocks `git commit -a` and `--no-verify`

Projects without `scripts/check` are never blocked. To enforce the gate for
every commit, including your own, install the git hook:

```sh
ln -s /path/to/vibes/hooks/git_pre_commit .git/hooks/pre-commit
```

The hooks need Bash, git and `realpath`. The Claude Code hook also uses `jq`
or Python 3 to read its input.

## License

[0BSD](LICENSE): use, copy, modify and share any of it, for any purpose, with
no conditions and no need to credit the source. That includes copying the
style guides, skills, agents and config templates into your own projects.
