# GitHub Actions Tools

The free/open source tools that lint, audit and test GitHub Actions
workflows and composite actions, and how to run them. They enforce the
rules in [coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [actionlint](https://github.com/rhysd/actionlint) | MIT | Linting | Workflow syntax, expressions, contexts and reusable workflow calls, and ShellCheck on every `run:` |
| [zizmor](https://github.com/zizmorcore/zizmor) | MIT | Auditing | Security analysis of workflows, composite actions and the Dependabot config |
| [yamllint](https://github.com/adrienverge/yamllint) | GPL-3.0 | Linting | YAML layout and typing traps, as the [YAML guide](../../data/YAML/tools.md) sets them |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | Apache-2.0 | Linting, Testing | Composite actions and the Dependabot config against their schemas, and the spec test |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Rules the other tools lack: timeouts, `-latest` runners, `continue-on-error`, long scripts, step names |
| [ShellCheck](https://www.shellcheck.net/) | GPL-3.0 | Linting | The scripts that `run:` steps call |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding jobs and steps copied between workflows |
| [Dependabot](https://github.com/dependabot/dependabot-core) | MIT | Auditing | Pull requests that update pinned actions |

GitHub's CodeQL can scan workflows too, but the CodeQL CLI isn't open
source. [act](https://github.com/nektos/act) runs workflows locally; see
[Testing](#testing) for why it's not one of the checks.

## Config files

Copy these files into the repository, at the same paths. Each one matches
the settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.yamllint.yaml`](.yamllint.yaml) | yamllint |
| [`.github/actionlint.yaml`](.github/actionlint.yaml) | actionlint |
| [`.github/zizmor.yaml`](.github/zizmor.yaml) | zizmor: a template to edit |
| [`.github/dependabot.yml`](.github/dependabot.yml) | Dependabot, and zizmor's Dependabot audits |
| [`.opengrep/github-actions.yaml`](.opengrep/github-actions.yaml) | Opengrep |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`tests/workflows/ci.schema.json`](tests/workflows/ci.schema.json) | check-jsonschema: the spec test for the example workflow |

## Versions

This guide was checked with these versions. Run each tool that publishes
an image from that image, pinned by digest, so nothing is installed on the
host:

| Tool | Version | Image |
| --- | --- | --- |
| actionlint | 1.7.12 | `rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667` |
| zizmor | 1.32.0 | `ghcr.io/zizmorcore/zizmor:1.32.0@sha256:3014cc8f68f663935f69b3c3e0e41f5ce102b268d97db13db0f62208747f860d` |
| ShellCheck | 0.11.0 | `koalaman/shellcheck:v0.11.0@sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d` |
| gitleaks | 8.30.1 | `ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` |
| yamllint | 1.38.0 | None: install it from PyPI |
| check-jsonschema | 0.39.0 | None: install it from PyPI |
| Opengrep | 1.33.1 | None: download the release binary |
| jscpd | 5.4.2 | None: install it from npm |

The actionlint image includes ShellCheck 0.11.0 and pyflakes, which
actionlint runs on `run:` steps.

## Formatting

No formatter rewrites workflow files, as in the
[YAML guide](../../data/YAML/tools.md). yamllint checks their layout, and
the Opengrep rules check the parts of the
[style](coding-style.md#layout) that yamllint can't.

## Linting

### yamllint

Workflow files are YAML, and pass yamllint with **no warnings**:

```sh
yamllint --strict .
```

[`.yamllint.yaml`](.yamllint.yaml) is the
[YAML guide's config](../../data/YAML/tools.md#recommended-setup) with one
change, which the workflow syntax forces:

```yaml
  line-length:
    max: 80
    # A uses: line pinned to a commit SHA, with its version comment, can't be
    # split and often runs past 80 columns. The Opengrep rule
    # github-actions-line-too-long checks every other line in these files.
    ignore:
      - .github/workflows/
      - .github/actions/
      - action.yaml
```

- The rest of the YAML guide's rules hold. Workflows quote the `on` key for
  the `truthy` rule, and write an event with no settings as `{}` for the
  `empty-values` rule (see [coding-style.md](coding-style.md#layout)).
- The file replaces the YAML guide's, and checks every other YAML file in
  the project the same way.

### actionlint

actionlint checks what GitHub would reject or misread: unknown keys,
expressions and their types, contexts that don't exist where they're used,
job dependencies, reusable workflow inputs, runner labels, and untrusted
values in scripts. It runs ShellCheck and pyflakes on `run:` steps. Files
must pass with **no errors**:

```sh
actionlint
```

It finds the workflows itself, and reads
[`.github/actionlint.yaml`](.github/actionlint.yaml):

```yaml
---
# Configuration variables the workflows may read. An empty list makes every
# vars.NAME an error, so a misspelt name fails here instead of expanding to
# an empty string at run time. Add each variable the workflows use.
config-variables: []

paths:
  .github/workflows/*.yaml:
    # actionlint 1.7.12 predates two features GitHub added in 2026: the
    # cache-mode key, and $/ in uses: for an action or reusable workflow in
    # the same repository. Delete these once actionlint accepts them.
    ignore:
      - unexpected key "cache-mode"
      - specifying action "\$/
      - reusable workflow call "\$/
```

- Each `ignore` entry is a regular expression matched against the error
  message, so each one silences only that error.
- List a self-hosted runner's labels under `self-hosted-runner.labels`.
  actionlint rejects a label it doesn't know, which catches a typo that
  would leave a job waiting for a runner that never comes.
- What actionlint doesn't check: the steps of a composite action, the
  inputs of an action pinned to a SHA (it knows popular actions' inputs only
  by major version tag), and anything inside a `$/` reference.
- It runs ShellCheck with ShellCheck's defaults, not the project's
  `.shellcheckrc`, so the
  [Bash guide](../../languages/BASH/tools.md#linting)'s optional checks
  apply only to script files. That's one more reason to
  [keep scripts in files](idioms.md#long-inline-scripts).

### Schemas

actionlint can't check a composite action's `action.yaml` on its own, or
the Dependabot config. check-jsonschema checks both against the schemas it
ships from SchemaStore:

```sh
check-jsonschema --builtin-schema vendor.github-actions \
  .github/actions/*/action.yaml
check-jsonschema --builtin-schema vendor.dependabot .github/dependabot.yml
```

### ShellCheck

The scripts that steps call follow the
[Bash guide](../../languages/BASH/tools.md), and its ShellCheck, shfmt and
bats-core run on them.

## Auditing

### Security analysis

zizmor finds the traps in [idioms.md](idioms.md) that make a workflow
unsafe: unpinned actions, template injection, dangerous triggers, broad
permissions, persisted credentials, cache poisoning, inherited secrets and
self-hosted runners. It reads workflows, composite actions and the
Dependabot config. Run it offline in `scripts/check`, with the pedantic
persona:

```sh
zizmor --offline --persona=pedantic .
```

- It exits 11 to 14 when it finds anything, by the highest severity, and 0
  when it finds nothing.
- The pedantic persona adds the audits this guide relies on:
  `concurrency-limits`, `undocumented-permissions`, `anonymous-definition`,
  and every expression in a script.
- The auditor persona, in `scripts/audit`, adds `self-hosted-runner` and
  `secrets-outside-env`. zizmor's documentation lists `self-hosted-runner`
  as pedantic, but 1.32.0 reports it only under the auditor persona.
- When one finding overlaps another, zizmor can report only one of them.
  Fix what it reports and run it again until it's clean.
- To suppress a finding, put `# zizmor: ignore[<audit>]` on the line, with a
  comment above saying why.

It reads [`.github/zizmor.yaml`](.github/zizmor.yaml):

```yaml
---
rules:
  # The actions this project trusts: GitHub's own, and each other action
  # someone has reviewed and added. A uses: of any other action fails until
  # it's reviewed and listed here.
  forbidden-uses:
    config:
      allow:
        - actions/*
```

- Everything else keeps zizmor's defaults, which already require every
  action to be pinned to a SHA, and Dependabot to wait at least 7 days.
- Add an action as `owner/repo`, after reading its code and checking who
  maintains it.

The starter rules in
[`.opengrep/github-actions.yaml`](.opengrep/github-actions.yaml) catch the
traps that neither actionlint nor zizmor does: a job without
`timeout-minutes`, a `-latest` runner label, `continue-on-error: true`, a
`run:` script over 10 lines or written with `>`, a step that doesn't start
with `name:`, a SHA pin without its version, and a line over 80 columns
that isn't a `uses:` line.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

A workflow's dependencies are the actions and reusable workflows it uses.

- **Dependabot** opens a pull request for each new release, moving the SHA
  and the version comment together. [`dependabot.yml`](.github/dependabot.yml)
  covers the workflows and every composite action in `.github/actions/`,
  and waits 7 days before proposing a release.
- **zizmor online** adds the audits that need the GitHub API: actions with
  a published advisory (`known-vulnerable-actions`), SHAs that aren't in the
  named repository (`impostor-commit`), refs that could name a branch or a
  tag (`ref-confusion`), and SHA pins that no tag points to
  (`stale-action-refs`). They need a token in `GH_TOKEN`, so they belong in
  `scripts/audit`, with the auditor persona:

  ```sh
  zizmor --persona=auditor .
  ```

Dependabot's security alerts don't cover actions pinned to a SHA, so the
online audit is what finds a vulnerable pinned action.

### Secrets

Workflows reference secrets by name; the values live in GitHub's secret
store. A value pasted into a workflow, a script or a test fixture is
committed for good.

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Duplication

Flag any block of 100 or more tokens that appears twice, such as setup steps
copied between jobs. Copied steps get fixed in one place and not the other
(see [Copied jobs](idioms.md#copied-jobs)).

```sh
jscpd --format yaml --min-tokens 100 --exit-code 1 .github/
```

- [`.jscpd.json`](.jscpd.json) holds the same settings. The YAML guide uses
  50 tokens, but every workflow repeats about 60 tokens of required
  settings, the triggers, `permissions: {}` and `concurrency`, which are not
  a copy to remove. 100 still catches a copied job: the copied setup steps
  of the [example](idioms.md#a-complete-example) are 116.
- In a project with other YAML, run the YAML guide's check with
  `--ignore "**/.github/**"`, so each file is checked once.

### Testing

A workflow can't be run before it's pushed, so test what can be tested
first, and keep what only a real run proves small.

**Before pushing.** Every check above runs locally in seconds. Add a spec
test, written before the workflow: a JSON Schema that states the
requirements of the [spec](idioms.md#writing-the-spec) that are in the file
itself, such as the triggers, permissions, timeouts and the required job's
name. It fails until the workflow meets them, and fails again if a later
change breaks one:

```sh
check-jsonschema --schemafile tests/workflows/ci.schema.json \
  .github/workflows/ci.yaml
```

[`tests/workflows/ci.schema.json`](tests/workflows/ci.schema.json) is the
spec test for the [example workflow](idioms.md#a-complete-example). Replace
the values with the project's own spec:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$comment": "The spec of .github/workflows/ci.yaml, checked before it runs.",
  "type": "object",
  "required": ["on", "permissions", "concurrency", "jobs"],
  "properties": {
    "on": {
      "$comment": "Pull requests to main, pushes to main, weekly, on demand.",
      "type": "object",
      "required": ["pull_request", "push", "schedule", "workflow_dispatch"],
      "additionalProperties": false,
      "properties": {
        "pull_request": { "const": { "branches": ["main"] } },
        "push": { "const": { "branches": ["main"] } },
        "schedule": { "const": [{ "cron": "0 6 * * 1" }] },
        "workflow_dispatch": { "const": {} }
      }
    },
    "permissions": { "const": {} },
    "concurrency": {
      "type": "object",
      "required": ["group", "cancel-in-progress"],
      "properties": { "cancel-in-progress": { "const": true } }
    },
    "jobs": {
      "type": "object",
      "required": ["check", "audit"],
      "properties": {
        "check": {
          "$comment": "Branch protection requires the check named Check.",
          "not": { "required": ["if"] },
          "properties": {
            "name": { "const": "Check" },
            "timeout-minutes": { "maximum": 15 }
          }
        }
      },
      "patternProperties": {
        "^[A-Za-z_][A-Za-z0-9_-]*$": {
          "$comment": "Every job: a read-only token and a timeout.",
          "type": "object",
          "required": ["permissions", "timeout-minutes"],
          "properties": {
            "permissions": { "const": { "contents": "read" } },
            "timeout-minutes": { "type": "integer", "maximum": 30 }
          }
        }
      }
    }
  }
}
```

- `"not": { "required": ["if"] }` keeps an `if:` off the required job, which
  GitHub would report as a success when it skips the job.
- The `on` key is quoted in the workflow, so the schema sees the string
  `on`, as GitHub does.

**Scripts.** Keep the logic in the scripts that steps call, and test them
with the language's own tests, such as bats-core for Bash. A script that
takes its inputs as arguments and environment variables can be tested with
any value, including a hostile pull request title.

**act.** [act](https://github.com/nektos/act) 0.2.97 (MIT) runs a workflow's
jobs in containers on your machine. It can help debug how a job's steps fit
together, but it proves little about a workflow:

- It ignores `permissions`, `timeout-minutes`, `concurrency`,
  `continue-on-error` and environments, and has no OpenID Connect.
- It runs jobs in images that differ from GitHub's runner images.
- 0.2.97 can't resolve a `$/` reference, so it can't run the example.

The scripts already run on your machine without it.

**On a branch.** Only a real run proves the rest of the spec, so push the
change to a branch of a fork or a scratch repository first, as a
[spike](idioms.md#spikes) does:

- that the triggers fire for the right events and branches, and not for
  others;
- that each job has the permissions it needs, and fails without them;
- that a failing script fails the run, and the required check reports;
- that concurrency cancels a superseded run;
- that the runner image has what the job needs;
- environments, approvals, OpenID Connect and secrets, which use a scratch
  repository's own test values, never production ones.

## scripts/check and scripts/audit

`scripts/check` runs what's local and fast:

- `yamllint --strict .`
- actionlint, with ShellCheck and pyflakes on the `run:` steps.
- check-jsonschema on the composite actions and the Dependabot config, and
  the spec tests.
- `zizmor --offline --persona=pedantic .`
- Opengrep.
- The Bash guide's checks on the scripts the steps call.

`scripts/audit` runs what's slow or needs the network:

- `zizmor --persona=auditor .`, online, with a token in `GH_TOKEN`.
- gitleaks over the full history.
- jscpd.
