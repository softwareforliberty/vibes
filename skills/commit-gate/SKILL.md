---
name: commit-gate
description: >-
  Sets up the vibes commit gate in a project: writes scripts/check (format,
  lint and the fast tests, with the slow ones under --all), scripts/check-file (each file's format and lint, as
  it's written), scripts/test-one (only the tests named, while you work) and
  scripts/audit from the guides' tools.md, and installs
  the git hook so no commit lands unless every check passes. Use when
  starting the vibe workflow in a project, or when asked to add a commit gate.
---

# Commit Gate

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

The commit gate refuses any commit unless the project's checks pass on
exactly what's being committed. It's enforced in two places, which share the
same logic:

- **Claude Code:** the vibes plugin's `PreToolUse` hook runs it before every
  `git commit` the agent makes.
- **Git:** `hooks/git_pre_commit` and `hooks/git_commit_msg` in this repo,
  run through the project's pre-commit and commit-msg hooks, run it for
  every commit, including commits made by people and by other agents.

A third hook catches the small mistakes earlier: after each file an agent
writes, the plugin's `PostToolUse` hook runs `scripts/check-file` on it,
which formats the file and shows the agent any lint problems at once,
rather than at the commit. It skips `spike/*` branches and the spiker,
whose code is thrown away, and files git ignores.

## What the gate does

1. It does nothing in projects without an executable `scripts/check`, so
   installing the plugin never blocks unrelated projects.
2. It runs no checks on `spike/*` branches, where the vibe workflow's
   throwaway spikes live, but still checks the subject's length.
3. It blocks the commit when there are unstaged changes or untracked files,
   because the checks would then test something other than the commit.
4. It blocks the commit when a staged file needs a guide that the
   `# Guides:` line in `scripts/check` doesn't name, or when no guide
   covers a staged file and no `# No guide:` line lists it. So a project
   that starts using a new language or tool midway, such as a C++ project
   that adds a Python script or a Dockerfile, can't commit those files
   until the gate checks them too.
5. It runs `scripts/check` and blocks the commit if it fails, showing the end
   of its output. For a commit of documents only, such as a spec, it runs
   `scripts/check --static`, without the tests, since a document can't
   break a test. Test data, such as a Markdown fixture under `tests/`,
   isn't a document. It doesn't run it again for the very commit it just
   passed, on the same parent, with the same staged files, in the same
   mode, as when a retry follows a refused commit message: git runs the
   gate before it reads the message.
6. It blocks a commit whose subject is longer than 50 characters, before
   running anything else.
7. It blocks a commit that adds a line carrying a `/vibes:debug` run's
   debug tag, such as `vibes-debug-month-end`, so no temporary debug log
   reaches a fix.
8. In Claude Code it also blocks `git commit -a`, `--all`, `--no-verify` and
   `-n`. Each change is staged deliberately, and the gate is never bypassed.
9. In Claude Code it tells the agent about a commit that loosens the gate
   itself: one that deletes `scripts/check` or `scripts/check-file`, makes
   either not executable, removes or changes a line of either so that a
   word of it is lost, such as a check, an option or a guide, or lets a
   failure pass, such as with `|| true`, `set +e` or an early `exit`.
   The agent says so in its report. It never asks the user or refuses the
   commit, so an unattended run keeps going. Extending the gate keeps
   every word, and so does rewrapping a command, so neither is mentioned.

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
that's **local and reasonably fast**. It runs the static checks first, then
the tests:

- **Formatting,** in check mode only. It never rewrites files.
- **Linting and type checking,** with warnings treated as errors.
- **Static security checks that run locally,** such as the guide's
  security linter and Opengrep rules from `tools.md`.
- **Architecture tests,** from the Architecture section of `tools.md`, that
  enforce the dependency rules between the project's layers, and each
  component's entry points. When the project has a design document, such
  as the `design.md` the vibe workflow writes, the rules come from it.
- **Requirement markers,** when the project keeps specs with requirement
  ids, such as the vibe workflow's. Copy
  `${CLAUDE_PLUGIN_ROOT}/skills/commit-gate/templates/check-requirements`
  to `scripts/check-requirements`. In `scripts/check`, it fails when a test's
  `Covers:` comment names a requirement its spec doesn't have, or one the
  spec marks as removed. Requirements without a test yet are allowed here,
  because a test-first build adds them one commit at a time.
- **The fast tests,** with the coverage minimum from `tools.md`: every
  test but the slow ones.

**The slow tests** run only with `scripts/check --all`, which the vibe
workflow runs once its batches are built, before each review round and
before it finishes, through vibes' `bin/check-all`, which skips a tree that
already passed; `scripts/audit` runs it too. A test is slow when it takes more than
about ten seconds, or needs a virtual machine, an emulator, a container or
a browser, such as a boot or smoke test. Mark them with the test runner's
own mechanism, such as a pytest marker, an ignored Rust test run with
`--ignored`, Go's `testing.Short`, a ctest label or a directory of their
own. The fast tests should take a few minutes at most, since every commit
waits for them.

`scripts/check` takes one optional argument:

| Run as | Runs | Used by |
| --- | --- | --- |
| `scripts/check` | The static checks, then the fast tests | The gate, on every commit |
| `scripts/check --static` | The static checks | The gate, on a commit of documents only |
| `scripts/check --all` | The static checks, then every test | `bin/check-all`, once the batches are built, before each review round and at the finish; `scripts/audit` |

Architecture rules and requirement markers count as static checks when
they don't run the tests. Put an architecture rule that is itself a test
with the fast tests. If the project's tests read its documents, such as
doctests in `README.md`, run them under `--static` too.

Rules for the script:

- It's an executable Bash script that follows
  `${CLAUDE_PLUGIN_ROOT}/guides/languages/BASH/coding-style.md`, runs from
  the repository root, and exits non-zero when any check fails.
- **It fails fast.** It runs every static check even after one fails, so
  one commit attempt shows every problem, but if any failed it stops
  there, without running the tests: they're the slow part, and the commit
  is blocked anyway.
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
# Run the pre-commit checks: formatting, lint and types, then the tests.
#
# Usage: scripts/check [--static | --all]
#   --static  the static checks only, for a commit of documents
#   --all     the slow tests too
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

# Prints the failed checks and exits, when any failed.
stop_if_failed() {
  if ((${#failed[@]} > 0)); then
    printf 'Failed: %s\n' "${failed[*]}" >&2
    exit 1
  fi
}

main() {
  local mode="${1:-}"
  cd -- "$(git rev-parse --show-toplevel)"

  # The static checks, one line each, using the commands from each guide's
  # tools.md.
  check 'shell format' shfmt -d scripts/
  check 'shell lint' shellcheck scripts/check scripts/check-file \
    scripts/audit scripts/check-requirements
  check 'requirements' scripts/check-requirements docs/specs/*/spec.md \
    -- tests
  check 'format' ruff format --check .
  check 'lint' ruff check .
  check 'types' mypy .
  # The tests are the slow part, so they run only when the rest pass.
  stop_if_failed
  [[ "${mode}" != --static ]] || exit 0

  check 'tests' coverage run -m pytest -m 'not slow'
  check 'coverage' coverage report
  if [[ "${mode}" == --all ]]; then
    check 'slow tests' pytest -m slow
  fi
  stop_if_failed
}

main "$@"
```

## Step 3: write scripts/check-file

`scripts/check-file` runs the **per-file** checks from `scripts/check` on
the files it's given, as paths from the repository root. The plugin's hook
runs it on each file an agent writes, so it must take a second or two:

- **Formatting,** in rewrite mode, such as `ruff format <file>` or
  `shfmt -w <file>`. Unlike `scripts/check`, it fixes the formatting rather
  than reporting it.
- **Linting** of that file, with the same config and the same
  warnings-as-errors as `scripts/check`. It reports problems and never
  rewrites the code to fix them.
- **Nothing that needs the whole project:** no type checker, tests,
  coverage or architecture tests. Changing one file can break another, so
  those stay with `scripts/check`, which runs them on every commit.
- A file no check covers passes. It prints nothing when every check
  passes, and each failing check's output otherwise, and exits non-zero
  when any fails.
- It follows the same rules as `scripts/check`: Bash, run from the
  repository root, no network.

A skeleton to start from:

```bash
#!/usr/bin/env bash
#
# Format and lint the files given, as each one is written. The per-file
# checks from scripts/check; formatting is rewritten, not reported.

set -euo pipefail

failed=0

# Runs one check, printing its output only when it fails.
check() {
  local output
  if ! output="$("$@" 2>&1)"; then
    printf '==> %s failed:\n%s\n' "$*" "${output}"
    failed=1
  fi
}

main() {
  cd -- "$(git rev-parse --show-toplevel)"
  local path
  for path in "$@"; do
    case "${path}" in
      *.py)
        check ruff format --quiet -- "${path}"
        check ruff check --quiet -- "${path}"
        ;;
      *.sh | scripts/*)
        check shfmt -w -- "${path}"
        check shellcheck -- "${path}"
        ;;
      *) ;;
    esac
  done
  exit "${failed}"
}

main "$@"
```

## Step 4: write scripts/test-one

`scripts/test-one` runs **only the tests it's given**, so an agent working
test-first runs the test it's writing in seconds, not the whole suite.
The TDD skill and the builder use it for every red and green run; the
gate still runs every fast test before each commit.

- **Each argument names a test** the way the project's runner does: a test
  file, a test function where the runner can pick one (`pytest`'s
  `path::name`, `cargo test <name>`, `go test -run <name> ./pkg`), a
  module or package, or a test program. Where the runner can, a source
  file of the code under test stands for the tests of that file.
- **It builds only what those tests need,** incrementally, in the same
  environment the gate's tests run in, such as its container and caches.
  It writes nothing the gate reads, such as pass markers or coverage data,
  so a run never changes what the next commit's gate does.
- **It runs them quietly,** a line for a pass and each failure in full,
  and exits non-zero when any fails. A name it can't place fails with
  exit 2 and says why. With no argument, it lists what it can run.
- It follows the same rules as `scripts/check`: Bash, run from the
  repository root, no network.

A skeleton to start from, for a Python project:

```bash
#!/usr/bin/env bash
#
# Run only the tests given, while you work: test files, test functions
# (path::name) or folders. The gate runs every test before each commit.

set -euo pipefail

main() {
  cd -- "$(git rev-parse --show-toplevel)"
  if (($# == 0)); then
    pytest --collect-only -q
    return
  fi
  pytest -q -p no:cacheprovider -- "$@"
}

main "$@"
```

## Step 5: write scripts/audit

`scripts/audit` holds the checks that are **slow or need the network**, such
as dependency vulnerability scans (OSV-Scanner and the guide's own audit
tool), gitleaks over the full history, the complexity and duplication
reports (lizard, jscpd), and mutation testing from the Mutation testing
section of each guide's `tools.md`, which shows whether the tests would
catch small changes to the code. It also runs
`scripts/check-requirements --all`, which fails when any requirement in a
spec has no test that names it, and `scripts/check --all`, for the slow
tests. It follows the same rules as
`scripts/check`. The vibe workflow runs it before finishing a task, and CI
should run it too.

## Step 6: install the hooks

1. Make the scripts executable, then run `scripts/check --all` on the current
   state of the project. Fix or report any failures before going on: a gate
   that already fails can't tell new problems from old ones.
   Then prove each check bites: break it once on purpose, such as with a
   misformatted line, a lint error, a failing test or a forbidden import,
   run `scripts/check`, and see that check fail. Undo each breach before
   the next. A check that can't fail, because its pattern matches no files
   or its tool found nothing to check, looks just like one that passes:
   fix it before you install the hooks. Keep the breach of each
   architecture test, the layers and the entry points, as
   `scripts/breaches/<rule>.patch`, as the builder's instructions
   describe, so `bin/rules-bite` and the gate can prove it again whenever
   the checks change.
2. Install the git hooks:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/install-git-hooks"
   ```

   It writes a small stub for each hook, not a link, that runs the hook
   from the newest vibes installed, so updates apply and removing an old
   version's folder breaks nothing; with no vibes installed, it refuses
   the commit. Never link the hooks into `${CLAUDE_PLUGIN_ROOT}`: that's
   one version's folder, and git skips a hook whose link no longer
   resolves, without a word. It replaces vibes' own hooks, and leaves any
   other hook alone: if it reports one, ask the user before running it
   again with `--replace`. If it reports that `core.hooksPath` is set,
   tell the user that their hook manager needs to run the vibes hooks.
3. Commit `scripts/check`, `scripts/check-file`, `scripts/test-one`,
   `scripts/audit`,
   `scripts/check-requirements` if the project has specs, and the tool
   config files in one commit. The gate runs on that commit too.

## When the gate is older than this skill

A project whose gate has `scripts/check` but no `scripts/check-file` or
no `scripts/test-one` was set up before the steps above. Bring it up to
date in one commit: write whichever is missing, `scripts/check-file` as
Step 3 says and `scripts/test-one` as Step 4 says; make `scripts/check`
fail fast, with its static checks before its tests; add its `--static`
and `--all` modes; and move its slow tests under `--all`, telling the
user which tests moved. Keep every check it already has. Then install
the hooks again as Step 6 says, which turns links to a plugin version's
folder into stubs and adds a missing `commit-msg` hook. A script that
ignores its arguments still works with the gate meanwhile: it runs
everything every time.

## When the project needs a new guide

When a change adds a kind of file the gate doesn't check yet, such as the
first Dockerfile, the gate blocks the commit and names the guide. Then:

1. Read the guide's `coding-style.md`, `idioms.md` and `tools.md`, and make
   the new files follow them.
2. Add the checks from its `tools.md` to `scripts/check` (and
   `scripts/audit`), and its formatter and linter to `scripts/check-file`,
   copy its config files, and add the guide to the `# Guides:` line.
3. Run `scripts/check`, fix what it finds, and commit the gate change on
   its own, before the files that need it.

## Rules for every commit

- Commit through the gate every time: never bypass it with `--no-verify`,
  `-n` or by deleting the hook.
- When the gate blocks a commit, fix the cause and commit again. Don't weaken
  a check or a test to get past it.
- Extend the gate by adding: a new check, a new file to an existing one, a
  guide to the `# Guides:` line. When an existing check truly has to change,
  change it, and say in your report what you changed and why.
- To commit part of the working tree, stash the rest first, as the
  [atomic commits](../atomic-commits/SKILL.md) skill describes.
