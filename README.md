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
- **`skills/`:** agent skills for the workflow, test-driven development,
  atomic commits and setting up the commit gate.
- **`principles.md`:** the programming principles every change is held
  to, such as SOLID, DRY and KISS.
- **`architecture/`:** how to structure software: rules for every kind,
  and a guide each for web, desktop and mobile applications, command-line
  tools, libraries, OS components and embedded systems.
- **`agents/`:** the designer, the spike agent, the builder and ten
  reviewer agents.
- **`hooks/`:** the commit gate, for Claude Code and for git; a guide
  check that makes the agent read the guide for each kind of file before
  writing it; and a guard that keeps the spec reviewer from changing files
  or git state.
- **`evals/`:** evals that check each reviewer agent finds the defects in
  its area and approves clean code, and that the workflow picks the right
  reviewers for a change, run with `claude plugin eval`.

## The workflow

Run it in a project with `/vibes:vibe <task>`. The workflow below is for a
large task. The main agent sizes each task and tells you the size, and you
can name one yourself, such as `/vibes:vibe small: fix the date parsing`:

- **Small,** such as a fix in existing code: a spec, a test-first build
  and a focused review, with no design or spike.
- **Medium,** a feature whose design is clear: adds the design, and the full
  review panel.
- **Large,** new or uncertain work: everything below.

At every size, a reviewer whose area the change can't touch is left out,
such as the performance and resource-leak reviewers for a change to only
config files.

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
   for architecture, memory and resource leaks, performance, bugs and
   security. The spec reviewer verifies it meets every requirement in the
   spec. Style, idioms and cleanliness wait for the rebuild, since the
   spike's code is thrown away.
5. **Fix.** The main agent decides on the findings and the spike agent fixes
   them, and the reviewers that asked for changes review what changed, until
   every reviewer approves (at most five rounds before it asks you). A fix that
   changes behaviour goes into the spec first, and so does every other change,
   all the way through. Each spec change is committed together with the code
   that implements it.
6. **Rebuild.** The spike is set aside, never merged. Builder subagents
   rebuild the task on a `vibe/<task>` branch, test-first, one atomic
   commit at a time, each starting fresh on its own batch of the work. The
   main agent only coordinates, so its context stays small however long
   the run.
7. **Gate.** Every commit runs the project's linters and full test suite, and
   is blocked if anything fails.
8. **Review again.** The same reviewers, plus reviewers for code
   cleanliness, coding style, idioms and test quality, check the rebuild,
   and their findings are fixed test-first. The spec reviewer
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
- **Agents:** `vibes:designer`, `vibes:spiker`, `vibes:builder` and the
  reviewers, such as `vibes:security-reviewer`.
- **The commit gate hook,** which runs before every `git commit` the agent
  makes.
- **The guide check hook.** The first time an agent, or each subagent,
  writes a kind of file in a conversation without having read its guide,
  it names the guide for it, and warns when the project's gate doesn't
  check that guide yet. In a project
  with the commit gate, it refuses that first write until the agent has
  read the guide, and lets the next one through. Elsewhere it only
  reminds, after the write, because Claude Code shows a hook's message
  alongside the tool's result.

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
- runs `scripts/check` before each commit, and blocks the commit if it fails
- refuses to commit while there are unstaged changes or untracked files, so
  the checks test exactly what's being committed
- skips `spike/*` branches
- in Claude Code, also blocks `git commit -a` and `--no-verify`

For a project with specs, `scripts/check` also checks the tests'
requirement markers. Each test names the requirements it covers, such as
`# Covers: order-export R1, R4`. Every commit fails on a marker naming a
requirement the spec doesn't have, and `scripts/audit`, run before a task
finishes, fails on any requirement no test covers.

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
