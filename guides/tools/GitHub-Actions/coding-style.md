# GitHub Actions Coding Style

A general-purpose style for GitHub Actions workflows, reusable workflows
and composite actions. It builds on the
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and [metadata syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
references, the [YAML guide](../../data/YAML/coding-style.md), and the
checks in [actionlint](https://github.com/rhysd/actionlint) and
[zizmor](https://docs.zizmor.sh/) (see [Sources](#sources)).

This guide covers how workflow files look. For how to write them well (the
traps, permissions, secrets, pinning and how to write the spec), see
[idioms.md](idioms.md).

The tools that check workflows are listed in [tools.md](tools.md).

## Baseline

- **GitHub.com, with GitHub-hosted runners.** Two features this guide
  relies on came in 2026: `$/` in `uses:`, for an action or reusable
  workflow in the same repository (July), and the `cache-mode` key (September).
  Neither is in GitHub Enterprise Server yet, so a project on GHES uses `./`
  with a checkout instead of `$/`, and leaves out `cache-mode`.
- **Self-hosted runners at version 2.336.0 or later.** `$/` needs it.
  GitHub-hosted runners are always up to date.
- **actionlint 1.7.12 predates both features,** and rejects them. The
  [actionlint config](tools.md#actionlint) ignores exactly those errors and
  nothing else.
- **Workflow files are YAML,** and follow the
  [YAML guide](../../data/YAML/coding-style.md) except where this guide says
  otherwise. Each exception is one that the workflow syntax forces.

## Files

- **Put workflows in `.github/workflows/`,** named for what they do, in
  lowercase with hyphens: `ci.yaml`, `release.yaml`. GitHub ignores any
  subdirectory of `.github/workflows/`, so a workflow there never runs.
- **Use the `.yaml` extension,** as the YAML guide says. GitHub reads `.yml`
  and `.yaml` alike, so nothing requires `.yml`.
- **Put reusable workflows in `.github/workflows/` too,** which GitHub
  requires, and give them only the `workflow_call` trigger, so they run only
  when called.
- **Put composite actions in `.github/actions/<name>/action.yaml`.** GitHub
  accepts `action.yml` or `action.yaml`.
- **Name the Dependabot config `.github/dependabot.yml`,** the name its
  documentation gives.
- **Shell scripts that `run:` steps call live in `scripts/`,** and follow the
  [Bash guide](../../languages/BASH/coding-style.md). Developers run the same
  scripts on their own machines (see
  [Long inline scripts](idioms.md#long-inline-scripts)).

## Layout

### YAML rules for workflows

- Start every file with `---`, and indent with 2 spaces, as the YAML guide
  says.
- **Quote the `on` key: `"on":`.** YAML 1.1 parsers read a plain `on` as the
  boolean `true`, and yamllint's `truthy` rule rejects it. GitHub, actionlint
  and zizmor read the quoted key the same way.
- **Write an event with no settings as `{}`:** `workflow_dispatch: {}`. An
  empty value is null, which yamllint's `empty-values` rule rejects.
- **80 columns is the limit,** except for a `uses:` line pinned to a commit
  SHA. The SHA and its version comment can't be split, and often run past 80
  columns. The [Opengrep rule](tools.md#security-analysis)
  `github-actions-line-too-long` checks every other line.
- Break a long expression with `>-`, which folds the lines into one value
  and drops the final newline:

  ```yaml
  concurrency:
    group: >-
      ${{ github.workflow }}-${{ github.event_name == 'pull_request'
      && github.ref || github.run_id }}
    cancel-in-progress: true
  ```

- Separate jobs with one blank line. Steps follow each other with none.

### Key order

GitHub accepts keys in any order, and no tool checks it, so follow one
order everywhere. What a workflow or job is comes first, then when it runs,
then what it may do, then the work. Long blocks, such as `steps` and a
`run:` script, come last, so everything that changes how they run is above
them.

- **In a workflow:** `name`, `run-name`, `"on"`, `permissions`,
  `cache-mode`, `concurrency`, `env`, `defaults`, `jobs`.
- **In a job:** `name`, `needs`, `if`, `runs-on` (or `uses` for a reusable
  workflow), `environment`, `permissions`, `cache-mode`, `concurrency`,
  `timeout-minutes`, `strategy`, `container`, `services`, `outputs`, `env`,
  `defaults`, `with`, `secrets`, `steps`.
- **In a step:** `name`, `id`, `if`, `uses`, `with`, `env`, `shell`,
  `working-directory`, `timeout-minutes`, `continue-on-error`, `run`.
- **In a composite action:** `name`, `description`, `inputs`, `outputs`,
  `runs`.

## Names and ids

- **Give the workflow, every job and every step a `name:`.** The name is
  what the run log, the pull request and the Actions page show. A step with
  no name shows its raw command or action reference instead.
- **Put `name:` first in every step.** It's the step's heading. The
  Opengrep rule `github-actions-step-without-name` rejects a step that
  starts with any other key, and zizmor's pedantic `anonymous-definition`
  audit rejects a workflow or action with no name.
- **Keep job names unique across all workflows.** The job's name is the
  name of its check, which branch protection requires by name, and two jobs
  with the same name give an ambiguous result (see
  [Required checks](idioms.md#required-checks-that-never-report)).
- **Write job ids, step ids and input names in lowercase with hyphens:**
  `build-docs`, `fetch-depth`. It's the form GitHub's own keys and actions
  use. A job id must start with a letter or `_`.
- **Give a step an `id` only when something reads it,** such as
  `steps.version.outputs.tag`. An unused id suggests a reader that doesn't
  exist.
- Write environment variables in `UPPER_SNAKE_CASE`, as the shell does.

## Expressions and quoting

- **Leave a value that is only an expression unquoted:**
  `group: ${{ github.workflow }}`. It's a plain YAML string.
- **Write `if:` without `${{ }}`:** `if: github.event_name == 'push'`.
  GitHub evaluates it as an expression anyway, and text outside a
  `${{ }}` turns it into a non-empty string that is always true.
- **Wrap a condition that starts with `!` in `${{ }}`:**
  `if: ${{ !cancelled() }}`. YAML reads a leading `!` as a tag.
- **Quote strings in expressions with single quotes:** `'pull_request'`.
  Double quotes are an error in an expression.
- **Quote values that would read as another type,** as the YAML guide says:
  `python-version: "3.14"`, not `3.14`, which is the number 3.14 and loses a
  trailing zero in `3.10`.
- **Write multi-line `run:` scripts with `|`,** which keeps each line a
  command. With `>`, the lines fold into one, so the second command becomes
  an argument of the first. The Opengrep rule `github-actions-folded-run`
  catches it.

## run: steps

- **Set the shell for every workflow:**

  ```yaml
  defaults:
    run:
      shell: bash
  ```

  With no `shell:`, GitHub runs `bash -e {0}`, so a failure in the middle
  of a pipeline, as in `curl ... | tar -x`, passes. A named `bash` runs
  `bash --noprofile --norc -eo pipefail {0}`, which fails it.
- **Set `shell: bash` on every `run:` step of a composite action.** A
  composite action has no defaults, and GitHub rejects a `run:` step without
  a shell.
- **`run:` scripts follow the
  [Bash guide](../../languages/BASH/coding-style.md):** quote and brace
  every expansion, `"${TITLE}"`, and write outputs to `"${GITHUB_OUTPUT}"`.
  actionlint runs ShellCheck on the `run:` steps of workflows, though not
  of composite actions.
- **Never put `${{ }}` inside a `run:` script.** Pass the value through
  `env:` and use the variable (see
  [Script injection](idioms.md#script-injection)).
- **Keep a `run:` step to a few lines.** Past 10 lines, move it into a
  script file (see [Long inline scripts](idioms.md#long-inline-scripts)).

## Comments

Comments follow the [YAML guide](../../data/YAML/coding-style.md#comments),
and explain **why**. A workflow has a few comments of its own:

- **Start every workflow and composite action with a comment** that says
  what it's for and when it runs.
- **Follow a SHA pin with its version, two spaces after the value:**
  `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`.
  Write the full version, which Dependabot updates along with the SHA.
  The Opengrep rule `github-actions-sha-without-version-comment` catches a
  pin without one.
- **Say why each permission is granted,** in a comment after it:
  `contents: write  # Create the release and upload its files.` zizmor's
  pedantic `undocumented-permissions` audit rejects a permission without
  one, except `contents: read`, which every checkout needs.
- **Suppress a finding only where it's needed, and say why,** on the line
  above: `# zizmor: ignore[dangerous-triggers]` for zizmor, or
  `# shellcheck disable=SC2086` inside a `run:` script. actionlint has no
  inline comments, so its exceptions go in the
  [config file](tools.md#actionlint), each with a comment.

## Formatting

As in the YAML guide, no formatter rewrites workflow files. yamllint checks
the layout, and the other [linters](tools.md#linting) check the rest.

## Sources

- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Metadata syntax for actions](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [Expressions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions)
- [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Self-repository references](https://github.blog/changelog/2026-07-30-reference-same-repository-actions-with-self-repository-syntax)
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [actionlint checks](https://github.com/rhysd/actionlint/blob/main/docs/checks.md)
- [zizmor audits](https://docs.zizmor.sh/audits/)
- [YAML guide](../../data/YAML/coding-style.md)
