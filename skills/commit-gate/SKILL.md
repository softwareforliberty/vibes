---
name: commit-gate
description: >-
  Sets up the vibes commit gate in a project: writes scripts/check (format,
  lint and full tests) and scripts/audit from the guides' tools.md, and
  installs the git hook so no commit lands unless every check passes. Use when
  starting the vibe workflow in a project, or when asked to add a commit gate.
---

# Commit Gate

The commit gate refuses any commit unless the project's checks pass on
exactly what's being committed. It's enforced in two places, which share the
same logic:

- **Claude Code:** the vibes plugin's `PreToolUse` hook runs it before every
  `git commit` the agent makes.
- **Git:** `hooks/git_pre_commit` in this repo, installed as the project's
  pre-commit hook, runs it for every commit, including commits made by people
  and by other agents.

## What the gate does

1. It does nothing in projects without an executable `scripts/check`, so
   installing the plugin never blocks unrelated projects.
2. It does nothing on `spike/*` branches, where the vibe workflow's throwaway
   spikes live.
3. It blocks the commit when there are unstaged changes or untracked files,
   because the checks would then test something other than the commit.
4. It blocks the commit when a staged file needs a guide that the
   `# Guides:` line in `scripts/check` doesn't name, or when no guide
   covers a staged file and no `# No guide:` line lists it. So a project
   that starts using a new language or tool midway, such as a C++ project
   that adds a Python script or a Dockerfile, can't commit those files
   until the gate checks them too.
5. It runs `scripts/check` and blocks the commit if it fails, showing the end
   of its output.
6. In Claude Code it also blocks `git commit -a`, `--all`, `--no-verify` and
   `-n`. Each change is staged deliberately, and the gate is never bypassed.

## Step 1: find the guides

List the guides the project needs, for its languages, formats and tools
alike:

```sh
git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"
```

It reads `${CLAUDE_PLUGIN_ROOT}/guides/map.tsv`. An entry such as
`languages/C|languages/C++` means either guide will do: pick the one the
project uses. A file listed as `no guide:` has no vibes guide: tell the
user, and list a pattern for it on the `# No guide:` line in Step 2.
`scripts/check` is itself a Bash script, so the project always needs
`languages/BASH`.

For each guide, read its `tools.md` in `${CLAUDE_PLUGIN_ROOT}/guides/`. Its
tool table, config files and commands are what the scripts will run.

Install each tool from the source its project publishes, which the tool
table links to, such as its own package registry or releases page. A
package elsewhere under the same name, such as a Python package for a tool
published on npm, may be a stranger's: don't install it unless the tool's
own project links to it. When a tool can't be installed from its own
source, leave it out of the scripts and tell the user.

## Step 2: write scripts/check

`scripts/check` is the gate. It runs on every commit, so it holds everything
that's **local and reasonably fast**:

- **Formatting,** in check mode only. It never rewrites files.
- **Linting and type checking,** with warnings treated as errors.
- **Static security checks that run locally,** such as the guide's
  security linter and Opengrep rules from `tools.md`.
- **The full test suite,** with the coverage minimum from `tools.md`.
- **Architecture tests,** from the Architecture section of `tools.md`, that
  enforce the dependency rules between the project's layers. When the
  project has a design document, such as the `design.md` the vibe workflow
  writes, the rules come from it.
- **Requirement markers,** when the project keeps specs with requirement
  ids, such as the vibe workflow's. Copy
  `${CLAUDE_PLUGIN_ROOT}/skills/commit-gate/templates/check-requirements`
  to `scripts/check-requirements`. In `scripts/check`, it fails when a test's
  `Covers:` comment names a requirement its spec doesn't have, or one the
  spec marks as removed. Requirements without a test yet are allowed here,
  because a test-first build adds them one commit at a time.

Rules for the script:

- It's an executable Bash script that follows
  `${CLAUDE_PLUGIN_ROOT}/guides/languages/BASH/coding-style.md`, runs from
  the repository root, and exits non-zero when any check fails.
- It runs every check even after one fails, then reports them all, so one
  commit attempt shows every problem.
- **Each check prints one line when it passes,** and its full output only
  when it fails. Agents read every line the gate prints, on every commit,
  so a passing check's output is wasted. The skeleton's `check` function
  holds each check's output back until it knows the result.
- It needs no network access, and nothing outside the project's own
  development dependencies.
- **Name the guides it checks** on a `# Guides:` line, and the files no
  guide covers on a `# No guide:` line, as patterns from `map.tsv`'s rules.
  Either line can repeat. The gate reads them, and blocks a commit that
  needs a guide the gate doesn't check.
- Copy each tool's config file from the guide's directory in `guides/` into
  the project, and adjust paths to the project's layout.
- It passes on a project with no tests yet. Some test runners fail when they
  find no tests, such as pytest, which exits with status 5. Treat only that
  status as a pass, with a comment saying why, so the check enforces itself
  from the first test on. Never add a placeholder test that checks nothing.

A skeleton to start from:

```bash
#!/usr/bin/env bash
#
# Run every pre-commit check: formatting, lint, types and the full tests.
#
# Guides: languages/BASH languages/Python
# No guide: *.ipynb

set -euo pipefail

failed=()

# Runs one check, printing its output only when it fails.
check() {
  local name="$1" output
  shift
  if output="$("$@" 2>&1)"; then
    printf 'ok: %s\n' "${name}"
  else
    printf '==> %s failed:\n%s\n' "${name}" "${output}"
    failed+=("${name}")
  fi
}

main() {
  cd -- "$(git rev-parse --show-toplevel)"

  # One line per check, using the commands from each guide's tools.md.
  check 'shell format' shfmt -d scripts/
  check 'shell lint' shellcheck scripts/check scripts/audit \
    scripts/check-requirements
  check 'requirements' scripts/check-requirements docs/specs/*/spec.md \
    -- tests
  check 'format' ruff format --check .
  check 'lint' ruff check .
  check 'types' mypy .
  check 'tests' coverage run -m pytest
  check 'coverage' coverage report

  if ((${#failed[@]} > 0)); then
    printf 'Failed: %s\n' "${failed[*]}" >&2
    exit 1
  fi
}

main "$@"
```

## Step 3: write scripts/audit

`scripts/audit` holds the checks that are **slow or need the network**, such
as dependency vulnerability scans (OSV-Scanner and the guide's own audit
tool), gitleaks over the full history, the complexity and duplication
reports (lizard, jscpd), and mutation testing from the Mutation testing
section of each guide's `tools.md`, which shows whether the tests would
catch small changes to the code. It also runs
`scripts/check-requirements --all`, which fails when any requirement in a
spec has no test that names it. It follows the same rules as
`scripts/check`. The vibe workflow runs it before finishing a task, and CI
should run it too.

## Step 4: install the hooks

1. Make both scripts executable, then run `scripts/check` on the current
   state of the project. Fix or report any failures before going on: a gate
   that already fails can't tell new problems from old ones.
2. Install the git hook, which links to this repo's copy so updates apply
   automatically:

   ```sh
   ln -s "${CLAUDE_PLUGIN_ROOT}/hooks/git_pre_commit" .git/hooks/pre-commit
   ```

   If the project already has a pre-commit hook, ask the user before
   replacing it.
3. Commit `scripts/check`, `scripts/audit`, `scripts/check-requirements`
   if the project has specs, and the tool config files in one commit. The
   gate runs on that commit too.

## When the project needs a new guide

When a change adds a kind of file the gate doesn't check yet, such as the
first Dockerfile, the gate blocks the commit and names the guide. Then:

1. Read the guide's `coding-style.md`, `idioms.md` and `tools.md`, and make
   the new files follow them.
2. Add the checks from its `tools.md` to `scripts/check` (and
   `scripts/audit`), copy its config files, and add the guide to the
   `# Guides:` line.
3. Run `scripts/check`, fix what it finds, and commit the gate change on
   its own, before the files that need it.

## Rules for every commit

- Never bypass the gate with `--no-verify`, `-n` or by deleting the hook.
- When the gate blocks a commit, fix the cause and commit again. Don't weaken
  a check or a test to get past it.
- To commit part of the working tree, stash the rest first, as the
  [atomic commits](../atomic-commits/SKILL.md) skill describes.
