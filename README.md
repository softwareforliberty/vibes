# vibes

Guides and tooling for clean vibe coding: letting an AI agent write the code,
while holding it to the standards of careful, experienced developers.

- **`lang/`:** per-language guides for 55 languages. Each has a
  `coding-style.md`, an `idioms.md` and a `tools.md` listing FOSS linting,
  auditing and code-quality tools, plus a `.editorconfig` and drop-in config
  files for those tools.
- **`skills/`:** agent skills for the workflow, test-driven development,
  atomic commits and setting up the commit gate.
- **`agents/`:** the spike agent and nine reviewer agents.
- **`hooks/`:** the commit gate, for Claude Code and for git.

## The workflow

Run it in a project with `/vibes:vibe <task>`:

1. **Spike.** A subagent builds the whole task quickly on a `spike/<task>`
   branch, to find the design.
2. **Review.** Reviewer subagents critique the spike in parallel, one each
   for architecture, code cleanliness, coding style, idioms, memory and
   resource leaks, performance, bugs and security.
3. **Fix.** The main agent fixes the findings, and the reviewers that asked
   for changes review again, until every reviewer approves (at most five
   rounds before it asks you).
4. **Rebuild.** The spike is set aside, never merged. The task is rebuilt on a
   `vibe/<task>` branch, test-first, one atomic commit at a time.
5. **Gate.** Every commit runs the project's linters and full test suite, and
   is blocked if anything fails.
6. **Review again.** The same reviewers, plus a test-quality reviewer, check
   the rebuild, and their findings are fixed test-first.

Nothing is pushed or merged unless you ask.

## Install as a Claude Code plugin

This repository is its own plugin marketplace. In Claude Code 2.1.275 or
later:

```text
/plugin install vibes --marketplace <owner>/vibes
```

Or in two steps:

```text
/plugin marketplace add <owner>/vibes
/plugin install vibes@vibes
```

Replace `<owner>` with the GitHub account that hosts this repository. To try
a local checkout without installing it, start Claude Code with
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
- Read the guides in `lang/` directly, and copy a language's `.editorconfig`
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
