# OpenTofu Idioms and Principles

How to build infrastructure with OpenTofu well.
[coding-style.md](coding-style.md) covers how the code looks. This guide
covers the traps that make infrastructure unsafe, lose data or drift from
its code, how the programming principles apply to OpenTofu, and how to
write the spec. Every example follows the style guide.

## Principles

- **The code is the source of truth.** Every change reaches the
  infrastructure through a reviewed commit and a reviewed plan, never
  through the console or a one-off command.
- **State is a secret and a single point of failure.** It holds every
  attribute of every resource, secrets included, in plain text. Keep it
  remote, locked, encrypted, versioned and readable by as few people as
  possible.
- **Small blast radius.** Each environment, and each large component,
  has its own root module, state and credentials, so a mistake in one
  can't touch the others.
- **Least authority.** Grant each resource, role and pipeline only the
  access it uses; make nothing public unless the spec says so.
- **Data outlives the code.** Databases, buckets and keys are protected
  from deletion in the code, in the provider and in the plan review, so no
  single mistake can destroy them.

## The traps

Each of these looks fine and works in a quick test, and many appear in
quick-start examples.

### State stored locally or committed

With no `backend` block, OpenTofu writes `terraform.tfstate` next to the
code. It's lost with the laptop, two people applying from their own
copies each overwrite the other's changes, and once it's committed, every
secret in it is in the git history for good.

- **Store state in a remote backend,** such as S3 or Google Cloud Storage,
  in a bucket with versioning on, so a corrupted or deleted state can be
  restored. The [example root module](#a-complete-example) uses S3.
- **Keep the state bucket in its own account or project,** readable only
  by the pipeline that applies and the few people who repair state.
- **Give each root module its own state key,** such as
  `production/terraform.tfstate`.
- The [`.gitignore`](.gitignore) template keeps state files out of git, and
  gitleaks finds AWS keys and tokens in a state file that slips through.

### No state locking

Two applies running at once against the same state both read it, both
change the infrastructure, and the last to finish overwrites the other's
record of what it built. OpenTofu then plans to create resources that
already exist, or loses track of ones it made.

- **Use a backend that locks.** For S3, set `use_lockfile = true`
  (OpenTofu 1.10 or later), which locks with a file in the state bucket and
  needs no DynamoDB table:

  ```hcl
  # State lives in a versioned S3 bucket, locked with a lock file in the same
  # bucket, and is encrypted by OpenTofu before it leaves this machine.

  terraform {
    backend "s3" {
      bucket       = "example-opentofu-state"
      key          = "production/terraform.tfstate"
      region       = "eu-west-2"
      encrypt      = true
      use_lockfile = true
    }

    encryption {
      key_provider "aws_kms" "state" {
        kms_key_id = "arn:aws:kms:eu-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
        region     = "eu-west-2"
        key_spec   = "AES_256"
      }

      method "aes_gcm" "state" {
        keys = key_provider.aws_kms.state
      }

      state {
        method   = method.aes_gcm.state
        enforced = true
      }

      plan {
        method   = method.aes_gcm.state
        enforced = true
      }
    }
  }
  ```

- **Never run with `-lock=false`,** and use `tofu force-unlock` only after
  checking that the run holding the lock has died.
- **Apply from one pipeline,** one run at a time per root module, so
  locking is a backstop rather than the only guard.

### Secrets in state, variables and outputs

`sensitive = true` hides a value in plan output and the terminal, nothing
more. Every attribute of every resource, including a generated password or
a key, is written to state in plain text, and a saved plan file and
`tofu show -json` both contain sensitive values in plain text too. A
`.tfvars` file with a password in it, or a variable with a secret default,
puts the secret in git.

- **Let the service create and keep the secret where it can,** such as
  `manage_master_user_password = true` on an RDS database, which stores
  the password in Secrets Manager and never in state.
- **Pass a secret you must supply as an ephemeral variable into a
  write-only argument** (OpenTofu 1.11 or later). Neither is ever written
  to state or a plan, and the `_version` argument tells OpenTofu when to
  send a new value:

  ```hcl
  variable "api_token" {
    description = "Token the service uses to call the payments API."
    type        = string
    sensitive   = true
    ephemeral   = true
  }

  variable "api_token_version" {
    description = "Increase by one to store a new api_token."
    type        = number
  }

  resource "aws_secretsmanager_secret" "api_token" {
    # checkov:skip=CKV2_AWS_57:The payments provider issues it; AWS cannot rotate it.
    name       = "payments-api-token"
    kms_key_id = "arn:aws:kms:eu-west-2:111122223333:key/0987dcba-09fe-87dc-65ba-ab0987654321"
  }

  resource "aws_secretsmanager_secret_version" "api_token" {
    secret_id                = aws_secretsmanager_secret.api_token.id
    secret_string_wo         = var.api_token
    secret_string_wo_version = var.api_token_version
  }
  ```

- **Pass secrets in from the environment** (`TF_VAR_api_token`) or a
  secret store in the pipeline. Never put them in a `.tfvars` file or a
  `default`.
- **Mark every secret variable and output `sensitive = true`,** so it
  isn't printed in plans and logs. OpenTofu refuses an output that returns
  a sensitive value without it.
- **Encrypt state and plans,** as the next trap describes, and treat a
  saved plan like state: keep it in the pipeline that made it, never as a
  downloadable artifact.
- Opengrep's `opentofu-secret-variable-not-sensitive` and
  `opentofu-secret-variable-with-default` flag secret-like variable names;
  Checkov's CKV_AWS_41 flags AWS keys in a `provider` block; gitleaks finds
  keys and tokens in any committed file. None of them recognise a plain
  password in a `.tfvars` file, so keep secrets out of those files.

### Unencrypted state

A backend's own encryption, such as `encrypt = true` on S3, protects the
stored object, but anyone who can read the bucket, and every backup of it,
still reads every secret.

- **Turn on OpenTofu's state and plan encryption,** as the backend example
  above does. OpenTofu encrypts the state before it leaves the machine, so
  the backend never holds plain text. Use a key management service, such
  as AWS KMS, GCP KMS, Azure Key Vault or OpenBao, with a key for each
  state, so access to one key opens one state.
- **Set `enforced = true`** on `state` and `plan`, so OpenTofu refuses to
  write either unencrypted if the encryption settings go missing.
- **Back up the state and test the key before enabling it on an existing
  project.** Encrypted state can't be read without the key, and an
  existing project needs an `unencrypted` fallback method for the
  migration; see the
  [state encryption](https://opentofu.org/docs/language/state/encryption/)
  documentation.
- Don't rename a key provider or method once state is encrypted: the name
  is stored with the data. Use a `fallback` block to change it.
- Encryption doesn't protect values from whoever runs `tofu`, so apply
  from a pipeline, not laptops.

### Unpinned versions

A module with no `required_version` runs on any OpenTofu, including one it
was never tested with. A provider with no `version` constraint takes the
newest release, so a new major version can change behaviour between two
runs of the same commit. A module sourced from a git branch, or a tag,
runs whatever the branch or tag points to that day.

- **Set `required_version` and a `version` for every provider in
  `versions.tf`.** In a reusable module, allow the range it's tested with,
  so callers can choose; in a root module, allow only newer patch and minor
  releases:

  ```hcl
  terraform {
    required_version = ">= 1.12.0, < 2.0.0"

    required_providers {
      aws = {
        source  = "hashicorp/aws"
        version = "~> 6.72"
      }
    }
  }
  ```

- **Commit `.terraform.lock.hcl`** and run `tofu init -lockfile=readonly`
  in CI. The lock file records the exact provider version and its
  checksums; read-only mode fails if they'd change. Upgrade providers with
  `tofu init -upgrade`, as a reviewed change.
- **Pin a third-party module to a commit,** with a comment naming the
  release. The lock file doesn't record module versions, and a tag can be
  moved:

  ```hcl
  module "assets_bucket" {
    # v5.17.0
    source = "git::https://github.com/terraform-aws-modules/terraform-aws-s3-bucket.git?ref=9afa4fc8c8f1e0b3fd913474c1bef8d0c454b235"

    bucket = "example-assets"
  }
  ```

- **Update pins in reviewed changes,** with a bot that opens a pull request
  for each new release, so you still get fixes.
- Opengrep's `opentofu-required-version-missing` and
  `opentofu-provider-without-version` flag missing constraints, and
  Checkov's CKV_TF_1 flags a module source that isn't a commit. CKV_TF_1
  also flags a registry module with a `version`, since the code can't
  name its commit, so source third-party modules from git.

### count over a list

`count = length(var.names)` gives each instance an index. Remove the first
name and every later instance shifts down one: OpenTofu plans to change or
replace each of them, and to destroy the last. With three queues, removing
`billing` from the front of the list plans to destroy all three and create
`orders` and `emails` again, where the intent was to delete one queue.

- **Use `for_each` over a set or map,** so each instance is keyed by
  something stable, and removing one removes only that one:

  ```hcl
  variable "queue_names" {
    description = "Names of the queues to create."
    type        = set(string)
  }

  resource "aws_sqs_queue" "this" {
    for_each = var.queue_names

    name                    = each.key
    sqs_managed_sse_enabled = true
  }
  ```

- Use `count` only for a number of identical, interchangeable instances.
  For one optional instance, OpenTofu 1.11 adds
  `lifecycle { enabled = var.create_queue }`, which avoids the `[0]` index.
- Keys must be known at plan time, so key on names from variables, never
  on IDs that a resource returns.

### Refactoring without moved blocks

Renaming a resource, moving it into a module, or switching it from `count`
to `for_each` changes its address. OpenTofu then sees one resource removed
and another added, and plans to destroy the old object and create a new
one: a new, empty database.

- **Add a `moved` block for each changed address,** in the same change.
  The plan then shows the move and no destroy:

  ```hcl
  moved {
    from = aws_sqs_queue.this[0]
    to   = aws_sqs_queue.this["billing"]
  }

  moved {
    from = aws_sqs_queue.this[1]
    to   = aws_sqs_queue.this["orders"]
  }
  ```

- Keep `moved` blocks in a shared module until every caller has applied
  the change; in a root module, remove them once every environment has.
- To stop managing a resource without destroying it, use a `removed` block
  with `lifecycle { destroy = false }` instead of `tofu state rm`, so the
  change is reviewed like any other.
- Read the plan for `must be replaced` and `will be destroyed` after any
  refactor. A refactor that's correct plans no changes at all.

### Data stores without protection

A changed argument that forces replacement, a renamed resource or a
`tofu destroy` in the wrong directory deletes a database or a bucket along
with its data.

- **Protect data in three layers:** the provider's own setting, such as
  `deletion_protection_enabled` on a DynamoDB table or
  `deletion_protection` on an RDS database; `prevent_destroy` in the
  `lifecycle` block; and the [plan policy](tools.md#policy-checks), which
  fails any plan that deletes a protected type:

  ```hcl
  resource "aws_dynamodb_table" "orders" {
    name                        = "orders"
    billing_mode                = "PAY_PER_REQUEST"
    hash_key                    = "order_id"
    deletion_protection_enabled = true

    attribute {
      name = "order_id"
      type = "S"
    }

    point_in_time_recovery {
      enabled = true
    }

    server_side_encryption {
      enabled     = true
      kms_key_arn = "arn:aws:kms:eu-west-2:111122223333:key/0987dcba-09fe-87dc-65ba-ab0987654321"
    }

    lifecycle {
      prevent_destroy = true
    }
  }
  ```

- `prevent_destroy` only works while the block is in the code: deleting
  the resource block deletes the protection with it. The provider setting
  and the plan policy still catch that.
- Turn on backups and recovery: point-in-time recovery, bucket versioning,
  final snapshots. Protection stops an accident; a backup undoes one.
- OpenTofu 1.12 adds `lifecycle { destroy = false }`, which removes an
  object from state instead of destroying it, for a resource that must
  outlive the code that made it.
- Checkov flags missing deletion protection and backups on many data
  stores, such as CKV_AWS_293 on RDS.

### Applying a plan nobody reviewed

`tofu apply` without a saved plan makes a new plan and applies it. If the
code, the state or the infrastructure changed since someone read the
plan, what runs isn't what they approved. `-auto-approve` on a fresh plan
skips the review entirely.

- **Save the plan, review it, then apply exactly that plan:**

  ```sh
  tofu plan -input=false -out=production.tfplan
  tofu show production.tfplan
  tofu show -json production.tfplan > production.json
  conftest test --policy policy/opentofu production.json
  tofu apply -input=false production.tfplan
  ```

- OpenTofu refuses a saved plan whose state has changed since
  (`Saved plan is stale`), so a plan can't be applied over someone else's
  change.
- **Read every `destroy` and `must be replaced`** in the plan, and the
  reason OpenTofu gives for it. The [plan policy](tools.md#policy-checks)
  fails a plan that deletes a protected type or misses required tags.
- The JSON plan holds sensitive values in plain text: delete it with the
  plan file when the run ends.

### Targeting and manual drift

`-target` and `-exclude` plan only part of the configuration, so the rest
silently diverges from the code. A change made in the console, or with
the cloud CLI, is drift: the next plan reverts it, or worse, plans around
it.

- **Plan the whole root module every time.** Use `-target` only to recover
  from a failure, as OpenTofu's documentation says, and follow it at once
  with a full plan and apply.
- **Make every change through the code.** For an emergency console change,
  write the matching code change the same day.
- **Detect drift on a schedule:** `tofu plan -detailed-exitcode` exits 2
  when the infrastructure differs from the code, 0 when it matches and 1
  on error.
- Use `ignore_changes` only for an attribute that another system owns by
  design, such as a desired count that an autoscaler changes, with a
  comment saying which system.

### One giant root module

One root module for everything means every plan reads and refreshes every
resource, takes minutes, and holds one lock; a typo in one service can
plan a change to the network; and the pipeline that applies it needs
permission to change everything.

- **Write reusable modules for things you build more than once,** such as
  a private bucket or a service, each in its own directory with its own
  tests.
- **Give each environment its own small root module,** under
  `environments/`, holding only the backend, the providers and a few
  module calls with that environment's values.
- **Split large systems by component as well,** such as `network`, `data`
  and `services`, each with its own state, so a change to one can't plan
  a change to another. Pass values between them with data sources or
  outputs read through `terraform_remote_state`.
- **Keep `provider` blocks out of reusable modules.** A module declares
  `required_providers` and receives its providers from the root. A module
  with its own `provider` block can't be called with `count`, `for_each`
  or `depends_on`, and can't be removed in one change, since OpenTofu
  needs the provider to destroy the module's resources.

### Workspaces as environments

CLI workspaces run one configuration against several states in the same
backend. Production and staging then share the backend's credentials and
access controls, the code can't differ between them without conditionals
on `terraform.workspace`, and nothing on screen says which workspace a
`tofu apply` will hit.

- **Use a separate root module per environment,** each with its own state
  key, as the [layout](coding-style.md#files) shows, so the directory
  names the environment and each can have its own credentials. OpenTofu's
  documentation says workspaces are not suitable for this.
- **Give each environment its own account or project,** and set
  `allowed_account_ids` (or the provider's equivalent) in its provider
  block, so the production root refuses to run with credentials for any
  other account.
- Workspaces suit short-lived copies of one environment, such as a copy
  per pull request.

### Hard-coded values in modules

A module with a bucket name, a region or a size written into it can be
used once. Copying it for the next use creates two copies that drift.
Variables with no checks move the problem: a wrong value fails halfway
through an apply with an error from the cloud API.

- **Make every value that differs between uses a variable,** and keep the
  values themselves in the root modules.
- **Validate each variable,** so a bad value fails at plan time with a
  message that says what's wrong, as the
  [example module](#a-complete-example) does for the bucket name and key.
- **Keep secure settings out of the variables.** A module that always
  blocks public access and always encrypts has no `public` or `encrypt`
  input to get wrong.

### Over-broad IAM and public resources

`"Action": "*"`, `"Resource": "*"`, a security group open to `0.0.0.0/0`
or a bucket with a public ACL is quick to write and works in every test.
It also means one stolen credential or one leaked URL exposes everything.

- **Grant the actions and resources the code uses, nothing more,** with
  `aws_iam_policy_document` or its equivalent, so the policy is checked as
  code:

  ```hcl
  data "aws_iam_policy_document" "read_reports" {
    statement {
      sid       = "ReadReports"
      actions   = ["s3:GetObject"]
      resources = ["arn:aws:s3:::example-reports-production/*"]
    }
  }

  resource "aws_iam_policy" "read_reports" {
    name        = "read-reports"
    description = "Read the objects in the reports bucket, and nothing else."
    policy      = data.aws_iam_policy_document.read_reports.json
  }
  ```

- **Block public access on every bucket,** and disable ACLs, as the
  example module does, even when the bucket policy is private.
- **Open network access to known ranges and ports only.** Reach private
  hosts through a bastion service or VPN, never SSH open to the internet.
- Checkov flags wildcard IAM policies (CKV_AWS_62, CKV_AWS_63 and
  others), ingress from anywhere on admin ports (CKV_AWS_24), and public
  or unblocked buckets (CKV_AWS_20, CKV_AWS_53 to CKV_AWS_56).

### local-exec provisioners

A `local-exec` provisioner runs a command on whatever machine runs the
apply. It isn't shown in the plan, doesn't run again when it fails or
when someone changes the infrastructure, and isn't undone by destroy. A
script that works on a laptop fails in CI, or runs with the pipeline's
credentials.

- **Use a provider resource for the job,** such as a database user from a
  PostgreSQL provider instead of `psql` in a provisioner.
- Configure servers with images or cloud-init (`user_data`), not
  `remote-exec`.
- Where no provider exists, run the step as its own pipeline job after the
  apply, where it's visible, retried and reviewed.
- The Opengrep rule `opentofu-local-exec` flags every `local-exec`.

## The principles in OpenTofu

How the [programming principles](../../../principles.md) apply to
infrastructure code:

- **Least authority:** IAM policies with named actions and resources; no
  public access unless the spec requires it; a pipeline role per root
  module that can change only that module's resources; state readable by
  the pipeline alone; `allowed_account_ids` on every provider.
- **Single source of truth:** the code describes the infrastructure, and
  nothing changes it any other way; each version pinned once, in
  `versions.tf` and the lock file; each value set once, in the root module
  that owns it; shared tags set once, in the provider's `default_tags`.
- **Immutability:** a reviewed plan file is what's applied; module and
  provider pins never move; replace servers from a new image rather than
  changing them in place.
- **Fail fast:** `required_version`; variable types and `validation`
  blocks; `enforced = true` on encryption; `prevent_destroy`; and
  `tofu test` and the scanners before any plan reaches a real account.
- **Separation of concerns:** reusable modules apart from the root
  modules that use them; one root per environment and per component;
  provider configuration only in roots.
- **KISS and YAGNI:** a module for something built twice, not before; no
  input for a setting that never changes; plain `for_each` over a map
  before nested `dynamic` blocks and conditional expressions.

## Writing the spec

A spec states what the infrastructure must be in terms a check can prove.
"Secure storage for reports" can't be checked; "no public access, every
object encrypted with key X, versioning on" can. For the example module
and its production root:

| Requirement | Checked by |
| --- | --- |
| All four public access settings are blocked, and ACLs are disabled | `tofu test` (`blocks_all_public_access`), Checkov CKV_AWS_53 to CKV_AWS_56, CKV2_AWS_6, CKV2_AWS_65 |
| Every object is encrypted with the customer-managed KMS key given | `tofu test` (`encrypts_with_the_given_key`), Checkov CKV_AWS_145 |
| Versioning is on | `tofu test` (`keeps_old_versions`), Checkov CKV_AWS_21 |
| Access is logged to the given log bucket | `tofu test` (`logs_access`), Checkov CKV_AWS_18 |
| A bucket name that breaks S3's naming rules fails at plan time | `tofu test` (`rejects_a_name_with_capitals`) |
| Every taggable resource carries `owner` and `environment` tags | Conftest plan policy |
| No plan deletes or replaces the bucket | `prevent_destroy`, Conftest plan policy |
| OpenTofu and provider versions are pinned, and the lock file is committed | Opengrep, `tofu init -lockfile=readonly` |
| Third-party modules are pinned to a commit | Checkov CKV_TF_1 |
| State and plans are encrypted, and state is locked | Review of `backend.tf`; with `enforced = true`, OpenTofu refuses to write either unencrypted |
| The production root applies only to account 111122223333 | The AWS provider, through `allowed_account_ids` |
| No secret is committed | gitleaks, Opengrep secret-variable rules |

Write the tests before the code, as [tools.md](tools.md#testing) describes,
so each requirement fails first and passes once the module meets it.

## Spikes

OpenTofu changes real systems, so a spike never touches a shared or
production account, not even with `tofu plan`, which reads the real
infrastructure with the credentials it's given.

- **Start with `tofu test` and a mock provider.** It plans, and even
  applies, against generated values, with no account or credentials, so
  most design questions can be answered offline.
- **When a spike must create real resources, use a throwaway sandbox
  account** that holds nothing else, with a budget alert. Give the spike
  its own root module, under a name such as `spikes/queue-design/`, and
  set `allowed_account_ids` to the sandbox account, so it fails to run
  with any other credentials.
- **Destroy everything when the spike ends** with `tofu destroy`, then
  check the account is empty. Spike state is thrown away with the
  account.
- Never point a spike at a shared state bucket or reuse a real root
  module's state key, which would overwrite that environment's state.

## A complete example

A module that builds a private S3 bucket: no public access, ACLs disabled,
every object encrypted with a customer-managed KMS key, versioned and
logged. Its tests are in [tools.md](tools.md#testing).

`modules/private-bucket/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.12.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0, < 7.0.0"
    }
  }
}
```

`modules/private-bucket/variables.tf`:

```hcl
variable "name" {
  description = "Globally unique name of the bucket."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.name))
    error_message = "The name must be 3 to 63 lowercase letters, digits and hyphens."
  }
}

variable "kms_key_arn" {
  description = "ARN of the KMS key that encrypts every object in the bucket."
  type        = string

  validation {
    condition     = startswith(var.kms_key_arn, "arn:aws:kms:")
    error_message = "The kms_key_arn must be the ARN of a KMS key."
  }
}

variable "log_bucket" {
  description = "Name of the bucket that receives this bucket's access logs."
  type        = string
}
```

`modules/private-bucket/main.tf`:

```hcl
# A private S3 bucket: no public access, no ACLs, every object encrypted
# with a customer-managed KMS key, versioned, and logged.

resource "aws_s3_bucket" "this" {
  bucket = var.name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    bucket_key_enabled = true

    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "this" {
  bucket = aws_s3_bucket.this.id

  target_bucket = var.log_bucket
  target_prefix = "${var.name}/"
}
```

`modules/private-bucket/outputs.tf`:

```hcl
output "name" {
  description = "Name of the bucket."
  value       = aws_s3_bucket.this.id
}

output "arn" {
  description = "ARN of the bucket, for IAM policies that grant access to it."
  value       = aws_s3_bucket.this.arn
}
```

- The module has no `public` or `encrypt` input: every bucket it builds is
  private and encrypted.
- It has no `provider` block and no tags. The root module configures the
  provider, and its `default_tags` tag every resource.
- `prevent_destroy` stops a plan that would delete the bucket and its
  objects; deleting one needs a reviewed change that removes the line
  first.

The production root module calls it. Its `versions.tf` is the one in
[Unpinned versions](#unpinned-versions), and its `backend.tf` the one in
[No state locking](#no-state-locking).

`environments/production/providers.tf`:

```hcl
provider "aws" {
  region              = "eu-west-2"
  allowed_account_ids = ["111122223333"]

  default_tags {
    tags = {
      environment = "production"
      owner       = "reports-team"
    }
  }
}
```

`environments/production/main.tf`:

```hcl
module "reports_bucket" {
  source = "../../modules/private-bucket"

  name        = "example-reports-production"
  kms_key_arn = "arn:aws:kms:eu-west-2:111122223333:key/0987dcba-09fe-87dc-65ba-ab0987654321"
  log_bucket  = "example-access-logs-production"
}
```

`environments/production/outputs.tf`:

```hcl
output "reports_bucket_name" {
  description = "Name of the reports bucket, for the services that write to it."
  value       = module.reports_bucket.name
}
```

## Sources

- [OpenTofu language](https://opentofu.org/docs/language/)
- [State](https://opentofu.org/docs/language/state/) and
  [sensitive data in state](https://opentofu.org/docs/language/state/sensitive-data/)
- [State locking](https://opentofu.org/docs/language/state/locking/)
- [State and plan encryption](https://opentofu.org/docs/language/state/encryption/)
- [S3 backend](https://opentofu.org/docs/language/settings/backends/s3/)
- [Ephemeral values](https://opentofu.org/docs/language/ephemerality/)
  and [write-only attributes](https://opentofu.org/docs/language/ephemerality/write-only-attributes/)
- [Provider requirements](https://opentofu.org/docs/language/providers/requirements/)
- [Dependency lock file](https://opentofu.org/docs/language/files/dependency-lock/)
- [Module sources](https://opentofu.org/docs/language/modules/sources/)
- [The `count` meta-argument](https://opentofu.org/docs/language/meta-arguments/count/)
  and [`for_each`](https://opentofu.org/docs/language/meta-arguments/for_each/)
- [Refactoring with `moved` blocks](https://opentofu.org/docs/language/modules/develop/refactoring/)
- [Resource lifecycle](https://opentofu.org/docs/language/resources/behavior/#lifecycle-customizations)
- [Command: plan](https://opentofu.org/docs/cli/commands/plan/) and
  [Command: apply](https://opentofu.org/docs/cli/commands/apply/)
- [Providers within modules](https://opentofu.org/docs/language/modules/develop/providers/)
- [Workspaces](https://opentofu.org/docs/cli/workspaces/)
- [Provisioners](https://opentofu.org/docs/language/resources/provisioners/syntax/)
- [JSON output format](https://opentofu.org/docs/internals/json-format/)
- [AWS provider](https://search.opentofu.org/provider/hashicorp/aws/latest)
