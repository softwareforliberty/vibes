# OpenTofu Tools

The free/open source tools that format, lint, audit and test OpenTofu
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [OpenTofu](https://github.com/opentofu/opentofu) 1.12 or later | MPL-2.0 | Formatting, Linting, Testing | `tofu fmt`, `tofu validate`, and `tofu test` with mock providers |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Linting | The project's own rules: descriptions, types, version pins, secret variables, names, `local-exec` |
| [Checkov](https://github.com/bridgecrewio/checkov) | Apache-2.0 | Auditing | Security misconfigurations: public access, encryption, IAM, deletion protection, module pins |
| [Conftest](https://github.com/open-policy-agent/conftest) | Apache-2.0 | Auditing | Policies on the saved plan: no protected data store deleted, required tags present |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding keys and tokens committed in code, `.tfvars` and state files |

Other tools were considered and left out:

- **TFLint** is the usual linter, but its release binaries include files
  from Terraform under the Business Source Licence 1.1, so its own README
  says they're bound by both MPL-2.0 and BUSL-1.1. BUSL isn't an open
  source licence. The Opengrep rules here cover its checks this guide
  needs, and `tofu validate` catches invalid code.
- **Terraform** itself is under BUSL-1.1.
- **Trivy** (Apache-2.0) also scans Terraform code, and unlike Checkov it
  reads `.tofu` files. Trivy 0.76.2 passed the example and caught public
  and unencrypted buckets, but missed a wildcard IAM policy and unpinned
  module sources that Checkov 3.4.3 caught, so Checkov is the scanner here.
  A project that runs Trivy for its images, as the
  [Docker guide](../Docker/tools.md) does, can keep both.
- **Terrascan** was archived in November 2025, and **tfsec** has been
  folded into Trivy.
- **`tofu validate -lint`**, new in OpenTofu 1.13, is experimental, checks
  only the root module and reports warnings without failing, so it can't
  gate a commit yet.

## Config files

Copy these files into the repository root. Each one matches the settings
on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.gitignore`](.gitignore) | git: keeps state, plans and `.terraform/` out of the repository |
| [`.opengrep/opentofu.yaml`](.opengrep/opentofu.yaml) | Opengrep |
| [`.checkov.yaml`](.checkov.yaml) | Checkov |
| [`policy/opentofu/plan.rego`](policy/opentofu/plan.rego) | Conftest: a template to edit |

## Versions

This guide was checked with these versions. Run each tool that publishes
an image from that image, pinned by digest, so nothing is installed on the
host:

| Tool | Version | Image |
| --- | --- | --- |
| OpenTofu | 1.13.9 and 1.12.12 | `ghcr.io/opentofu/opentofu:1.13.9-minimal@sha256:84af0049634b7a7c455ab79c485818a8ef7f775cad3b2d42ce1c98ade720b5d1`: copy the binary into your own image |
| Checkov | 3.4.3 | `bridgecrew/checkov:3.4.3@sha256:bfe9d70bb7f044aba49bd99675813445f106dee6072da583f51008cb667f3a63` |
| Conftest | 0.71.1, with OPA 1.21.1 | `openpolicyagent/conftest:v0.71.1@sha256:0e77cdf7c1fcde035f3c579e4aaa6664ee2a8be5777eaa9af9f520cdd02280c0` |
| gitleaks | 8.30.1 | `ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` |
| Opengrep | 1.33.1 | None: download the release binary |
| AWS provider | 6.72.0 | None: `tofu init` installs it, and the lock file pins it |

- Since OpenTofu 1.10, the official image can't be run directly. The
  `-minimal` image holds only `/usr/local/bin/tofu`, to copy into an image
  of your own with `COPY --from`, as OpenTofu's
  [Docker instructions](https://opentofu.org/docs/intro/install/docker/)
  show. That image is code too: follow the
  [Docker guide](../Docker/coding-style.md).
- The Checkov image is large, about 850 MB.

## Formatting

`tofu fmt` formats every OpenTofu file, including variable files and
tests. Check in CI, and rewrite locally:

```sh
tofu fmt -check -recursive
tofu fmt -recursive
```

`-check` lists the files that need formatting and exits non-zero.
`-recursive` includes the subdirectories, which `tofu fmt` skips by
default. Format Rego with `conftest fmt policy`, and check it with
`conftest fmt --check policy`.

## Linting

### tofu validate

`tofu validate` checks a module's syntax, references, types and every
argument against the provider's schema, without touching any account. It
needs the providers, so initialise each module first, without a backend:

```sh
tofu -chdir=modules/private-bucket init -backend=false -input=false -lockfile=readonly
tofu -chdir=modules/private-bucket validate
```

- `-backend=false` skips the backend, so validation needs no credentials.
- `-lockfile=readonly` fails if the providers would differ from the
  committed lock file, instead of quietly updating it.
- Run it in every module and every root module. It checks one directory
  at a time.

### Opengrep

The rules in [`.opengrep/opentofu.yaml`](.opengrep/opentofu.yaml) check
what neither OpenTofu nor Checkov does: every variable has a description
and a type, every output a description, secret-like variables are
sensitive and have no default, `required_version` and provider versions
are set, names are `snake_case`, comments use `#`, and nothing runs
`local-exec`.

```sh
opengrep scan --config .opengrep/ --error
```

- In a git repository, Opengrep scans only the files git tracks, so it
  skips the modules that `tofu init` downloads into `.terraform/`.
  Outside one, it scans them too.
- It doesn't read `.tofu` files, so [write `.tf`](coding-style.md#files).
- Run Opengrep with rules you write, or with rule sets under a FOSS
  licence. The Semgrep Registry rules are under the Semgrep Rules License,
  which isn't a free/open source licence, so don't use them.

## Auditing

### Security analysis

Checkov reads the code, resolves module calls and variables, and checks
the result against its built-in policies: public buckets and ACLs,
missing encryption, wildcard IAM policies, open security groups, missing
deletion protection and backups, hard-coded credentials, and module
sources not pinned to a commit. It needs no credentials and no provider
plugins:

```sh
checkov --directory .
```

Checkov reads [`.checkov.yaml`](.checkov.yaml) from the directory it scans:

```yaml
---
# Scan only the OpenTofu code, with the checks built into Checkov, and never
# contact Prisma Cloud, so the scan runs offline and sends nothing out.
framework:
  - terraform
skip-download: true
compact: true
quiet: true
skip-check:
  # Cross-region replication is a disaster-recovery choice for each bucket,
  # not a default; the spec says which buckets need it.
  - CKV_AWS_144
  # Lifecycle rules and event notifications are features a bucket may need,
  # not security controls.
  - CKV2_AWS_61
  - CKV2_AWS_62
```

- `skip-download: true` stops Checkov contacting Prisma Cloud for
  guidelines and severities. The checks themselves are built in, so the
  scan works offline.
- Any failed check fails the run. Skip a check for one resource with a
  `# checkov:skip=<id>:<reason>` comment inside it (see
  [Comments](coding-style.md#comments)). Skip one everywhere only when it
  never applies, as above, with a comment saying why.
- Checkov skips `.tofu` files.

### Policy checks

Some rules can only be checked on the plan, after OpenTofu has worked out
every module, `for_each` and default: that a plan deletes no data store,
and that every resource ends up with the required tags. Conftest checks
the plan's JSON against Rego policies:

```sh
tofu plan -input=false -out=production.tfplan
tofu show -json production.tfplan > production.json
conftest test --policy policy/opentofu production.json
```

[`policy/opentofu/plan.rego`](policy/opentofu/plan.rego) fails a plan that
deletes or replaces a protected data store, which catches the deletion
that `prevent_destroy` can't (see
[Data stores without protection](idioms.md#data-stores-without-protection)),
and one that creates or updates an AWS resource without the required
tags:

```rego
# Rules for an OpenTofu plan, read from the JSON that
# `tofu show -json <planfile>` prints.
package main

# Types whose objects hold data that a delete would lose. Add the project's
# own data stores.
protected_types := {
	"aws_db_instance",
	"aws_dynamodb_table",
	"aws_efs_file_system",
	"aws_kms_key",
	"aws_rds_cluster",
	"aws_s3_bucket",
}

# Tags every taggable resource must carry, set by the provider's
# default_tags or by the resource itself.
required_tags := {"environment", "owner"}

deny contains msg if {
	some resource in input.resource_changes
	resource.type in protected_types
	"delete" in resource.change.actions
	msg := sprintf("%s would be deleted or replaced, losing its data", [resource.address])
}

deny contains msg if {
	some resource in input.resource_changes
	some action in resource.change.actions
	action in {"create", "update"}
	taggable(resource.change)
	missing := required_tags - object.keys(planned_tags(resource.change))
	count(missing) > 0
	msg := sprintf("%s is missing the tags %v", [resource.address, sort(missing)])
}

# AWS resources that take tags have a tags_all attribute.
taggable(change) if "tags_all" in object.keys(change.after)

taggable(change) if change.after_unknown.tags_all

# tags_all is unknown until apply when no tags are set at all, so fall back
# to the resource's own tags.
planned_tags(change) := tags if {
	tags := change.after.tags_all
	is_object(tags)
} else := tags if {
	tags := change.after.tags
	is_object(tags)
} else := {}
```

- A plan reads the real infrastructure, so it needs the environment's
  credentials. The policy check runs in the deployment pipeline, between
  plan and apply, not in `scripts/check`.
- Deleting a protected data store on purpose is a change of its own,
  whose failed policy check someone with the authority to lose that data
  overrides, after reading the plan.
- The plan JSON holds sensitive values in plain text, so delete it with
  the plan file when the run ends.

### Dependency vulnerabilities

There's no vulnerability database for providers or modules to audit
against. Pin them (see [Unpinned versions](idioms.md#unpinned-versions)),
read their release notes, and update them in reviewed changes, so a
security fix arrives as a diff that someone reads.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

gitleaks 8.30.1 finds AWS keys in a `provider` block or a committed state
file, and tokens with a known format in `.tfvars` files. It doesn't find a
plain password, so keep secrets out of variable files altogether (see
[Secrets in state, variables and outputs](idioms.md#secrets-in-state-variables-and-outputs)).

## Code quality

### Testing

Test a module the way its [spec](idioms.md#writing-the-spec) describes it,
and write the test first: each requirement becomes an `assert` that fails
until the module meets it. `tofu test` runs every `.tftest.hcl` file in
the module directory and its `tests/` directory:

```sh
tofu -chdir=modules/private-bucket test
```

- **Plan, don't apply:** `command = plan` checks what the module would
  build without creating it. An apply run must destroy what it made
  afterwards, which `prevent_destroy` stops, even with a mock provider.
- **Mock the cloud provider:** `mock_provider "aws" {}` replaces every AWS
  resource and data source with generated values, so the tests need no
  account and no credentials. `tofu init` still downloads the provider for
  its schema.
- **Test the validation too:** a run with a bad input and
  `expect_failures = [var.name]` passes only when the validation rejects
  it. `expect_failures` works only for the module's own conditions, not
  for errors the provider would report.
- **Mocks check the module, not the cloud.** They can't tell whether AWS
  accepts a setting, so try new resources in a [spike](idioms.md#spikes)
  in a sandbox account, then keep the mocked test as the regression check.

`modules/private-bucket/tests/private_bucket.tftest.hcl` is the test for
the [example module](idioms.md#a-complete-example):

```hcl
# The spec for the private-bucket module. Every run plans against a mocked
# AWS provider, so the tests need no account and no credentials.

mock_provider "aws" {}

variables {
  name        = "example-reports"
  kms_key_arn = "arn:aws:kms:eu-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
  log_bucket  = "example-access-logs"
}

run "blocks_all_public_access" {
  command = plan

  assert {
    condition = alltrue([
      aws_s3_bucket_public_access_block.this.block_public_acls,
      aws_s3_bucket_public_access_block.this.block_public_policy,
      aws_s3_bucket_public_access_block.this.ignore_public_acls,
      aws_s3_bucket_public_access_block.this.restrict_public_buckets,
    ])
    error_message = "Every public access setting must be blocked."
  }

  assert {
    condition = (
      one(aws_s3_bucket_ownership_controls.this.rule).object_ownership == "BucketOwnerEnforced"
    )
    error_message = "ACLs must be disabled, so no ACL can make an object public."
  }
}

run "encrypts_with_the_given_key" {
  command = plan

  assert {
    condition = alltrue([
      for rule in aws_s3_bucket_server_side_encryption_configuration.this.rule :
      one(rule.apply_server_side_encryption_by_default).kms_master_key_id == var.kms_key_arn
    ])
    error_message = "Objects must be encrypted with the given KMS key."
  }
}

run "keeps_old_versions" {
  command = plan

  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "Versioning must be on, so a deleted or overwritten object can be recovered."
  }
}

run "logs_access" {
  command = plan

  assert {
    condition     = aws_s3_bucket_logging.this.target_bucket == var.log_bucket
    error_message = "Access must be logged to the given bucket."
  }
}

run "rejects_a_name_with_capitals" {
  command = plan

  variables {
    name = "Example-Reports"
  }

  expect_failures = [var.name]
}
```

- Nested blocks such as `rule` are sets or lists, so read them with
  `one()` or a `for` expression, as above.
- The `variables` block at the top gives every run valid inputs; a run
  overrides only the one it tests.
- With the module's versioning set to `Suspended`, a public access setting
  turned off, or a different key, the matching run fails and
  `tofu test` exits 1.

## scripts/check and scripts/audit

`scripts/check` runs what's local and fast, and needs no cloud
credentials:

```sh
tofu fmt -check -recursive
for dir in modules/*/ environments/*/; do
  tofu -chdir="$dir" init -backend=false -input=false -lockfile=readonly
  tofu -chdir="$dir" validate
done
for dir in modules/*/; do
  tofu -chdir="$dir" test
done
opengrep scan --config .opengrep/ --error
checkov --directory .
conftest fmt --check policy
```

- The first `tofu init` downloads the providers. Set
  `TF_PLUGIN_CACHE_DIR` so later runs, and other modules, reuse them.
- The root modules are validated, not tested: their tests would need the
  backend and the encryption key.

`scripts/audit` runs what's slow or reads the whole history:

- gitleaks over the full history.

The deployment pipeline runs the rest, with each environment's
credentials: `tofu plan -out`, the Conftest policy check on the plan,
a person's review, then `tofu apply` of that plan file. A scheduled
`tofu plan -detailed-exitcode` in each environment reports drift.

## Sources

- [Command: fmt](https://opentofu.org/docs/cli/commands/fmt/)
- [Command: validate](https://opentofu.org/docs/cli/commands/validate/)
- [Command: test](https://opentofu.org/docs/cli/commands/test/)
- [Command: init](https://opentofu.org/docs/cli/commands/init/)
- [Linting (experimental)](https://opentofu.org/docs/language/linting/)
- [OpenTofu with Docker](https://opentofu.org/docs/intro/install/docker/)
- [Provider plugin cache](https://opentofu.org/docs/cli/config/config-file/#provider-plugin-cache)
- [Checkov CLI reference](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html)
  and [suppressions](https://www.checkov.io/2.Basics/Suppressing%20and%20Skipping%20Policies.html)
- [Conftest](https://www.conftest.dev/) and
  [Rego](https://www.openpolicyagent.org/docs/policy-language)
- [Opengrep rule syntax](https://github.com/opengrep/opengrep)
- [gitleaks](https://github.com/gitleaks/gitleaks)
- [TFLint licence](https://github.com/terraform-linters/tflint#license)
