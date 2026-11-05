---
name: commit-gate
description: >-
  Sets up the vibes commit gate in a project: writes scripts/check (format,
  lint and full tests) and scripts/audit from the languages' tools.md, and
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
4. It runs `scripts/check` and blocks the commit if it fails, showing the end
   of its output.
5. In Claude Code it also blocks `git commit -a`, `--all`, `--no-verify` and
   `-n`. Each change is staged deliberately, and the gate is never bypassed.

## Step 1: find the languages

List the languages the project uses (source, tests, build files, config).
For each one, find its directory under `${CLAUDE_PLUGIN_ROOT}/lang/` and read
its `tools.md`. Its tool table, config files and commands are what the
scripts will run.

## Step 2: write scripts/check

`scripts/check` is the gate. It runs on every commit, so it holds everything
that's **local and reasonably fast**:

- **Formatting,** in check mode only. It never rewrites files.
- **Linting and type checking,** with warnings treated as errors.
- **Static security checks that run locally,** such as the language's
  security linter and Opengrep rules from `tools.md`.
- **The full test suite,** with the coverage minimum from `tools.md`.

Rules for the script:

- It's an executable Bash script that follows
  `${CLAUDE_PLUGIN_ROOT}/lang/BASH/coding-style.md`, runs from the repository
  root, and exits non-zero when any check fails.
- It runs every check even after one fails, then reports them all, so one
  commit attempt shows every problem.
- Each check prints its name, and only prints details when it fails.
- It needs no network access, and nothing outside the project's own
  development dependencies.
- Copy each tool's config file from the language's directory in `lang/` into
  the project, and adjust paths to the project's layout.

A skeleton to start from:

```bash
#!/usr/bin/env bash
#
# Run every pre-commit check: formatting, lint, types and the full tests.

set -euo pipefail

failed=()

check() {
  local name="$1"
  shift
  printf '==> %s\n' "${name}"
  if ! "$@"; then
    failed+=("${name}")
  fi
}

main() {
  cd -- "$(git rev-parse --show-toplevel)"

  # One line per check, using the commands from each language's tools.md.
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
as dependency vulnerability scans (OSV-Scanner and the language's own audit
tool), gitleaks over the full history, and the complexity and duplication
reports (lizard, jscpd). It follows the same rules as `scripts/check`. The
vibe workflow runs it before finishing a task, and CI should run it too.

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
3. Commit `scripts/check`, `scripts/audit` and the tool config files in one
   commit. The gate runs on that commit too.

## Rules for every commit

- Never bypass the gate with `--no-verify`, `-n` or by deleting the hook.
- When the gate blocks a commit, fix the cause and commit again. Don't weaken
  a check or a test to get past it.
- To commit part of the working tree, stash the rest first, as the
  [atomic commits](../atomic-commits/SKILL.md) skill describes.
