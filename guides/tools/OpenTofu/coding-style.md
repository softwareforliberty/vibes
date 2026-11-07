# OpenTofu Coding Style

A general-purpose style for infrastructure code written for
[OpenTofu](https://opentofu.org/), the open-source fork of Terraform, in
HCL. It builds on OpenTofu's
[style conventions](https://opentofu.org/docs/language/syntax/style/),
its [standard module structure](https://opentofu.org/docs/language/modules/develop/structure/)
and `tofu fmt` (see [Sources](#sources)).

This guide covers how the code looks. For how to build infrastructure well
(the traps, state, secrets, modules and how to write the spec), see
[idioms.md](idioms.md).

The tools that check OpenTofu code are listed in [tools.md](tools.md).

## Baseline

- **OpenTofu 1.12 or later.** It's the oldest release series the project
  still supports, until 1 February 2027; 1.13 is supported until
  1 August 2027. The rules rely on S3 lock files (1.10), ephemeral
  variables and write-only arguments (1.11), and state encryption and mock
  providers, which are older. This guide was checked with 1.12.12 and
  1.13.9.
- **Terraform is not open source.** HashiCorp moved it to the Business
  Source Licence (BUSL-1.1) in 2023, so this guide targets OpenTofu, which
  stays under MPL-2.0.
- **Much of the HCL also runs on Terraform.** The
  [example module](idioms.md#a-complete-example) and its tests pass
  `terraform fmt -check`, `terraform validate` and `terraform test` with
  Terraform 1.17.1. A root module with an `encryption` block doesn't:
  Terraform rejects the block. Nothing else here was checked with
  Terraform, so test before relying on it.

## Files

- **Write `.tf` files.** OpenTofu also reads `.tofu` files, but Checkov
  3.4.3 and Opengrep 1.33.1 skip them, so the code in them goes unchecked.
  Use a `.tofu` file only for a module that must also serve Terraform, as
  [Compatibility with Older Versions](https://opentofu.org/docs/language/settings/#compatibility-with-older-versions-and-other-software)
  describes.
- **One module per directory.** OpenTofu loads every `.tf` file in a
  directory as one module, so the directory is the unit of reuse, testing
  and state.
- **Split a module's files by role,** with the names the standard module
  structure uses:

  | File | Holds |
  | --- | --- |
  | `versions.tf` | The `terraform` block: `required_version` and `required_providers` |
  | `variables.tf` | Every `variable` block |
  | `main.tf` | The resources, data sources and module calls |
  | `outputs.tf` | Every `output` block |
  | `providers.tf` | `provider` blocks, in a root module only |
  | `backend.tf` | The `backend` and `encryption` settings, in a root module only |
  | `tests/*.tftest.hcl` | The module's [tests](tools.md#testing) |

  A reader then finds a module's inputs, outputs and versions without
  searching. When `main.tf` grows past a few hundred lines, split it by
  concern, such as `network.tf` and `dns.tf`, never by resource type.
- **Lay out a repository as reusable modules and one root module per
  environment:**

  ```text
  modules/
    private-bucket/
  environments/
    production/
    staging/
  ```

  See [One giant root module](idioms.md#one-giant-root-module) and
  [Workspaces as environments](idioms.md#workspaces-as-environments) for
  why.
- **Commit `.terraform.lock.hcl`** in every directory you run `tofu init`
  in. It records the exact provider versions and their checksums, so every
  machine installs the same providers (see
  [Unpinned versions](idioms.md#unpinned-versions)).
- **Never commit state or saved plans.** The [`.gitignore`](.gitignore)
  template keeps out `.terraform/`, state files and plans, which hold
  secrets in plain text.

## Naming

- **Write every name in lowercase `snake_case`:** resources, data sources,
  modules, variables, outputs and locals. It's how OpenTofu and the
  providers name things, so mixed styles stand out. The Opengrep rule
  `opentofu-name-not-snake-case` checks it.
- **Name a resource for its role, without repeating its type:**
  `aws_s3_bucket.reports`, not `aws_s3_bucket.reports_bucket` or
  `aws_s3_bucket.bucket`. The address already says it's a bucket.
- **Name a module's one main resource of a type `this`,** as in
  `aws_s3_bucket.this`. When a module has several of a type, name each by
  its role.
- **Name variables for what they hold, with the unit:** `retention_days`,
  `kms_key_arn`, not `retention` or `key`. A caller reads only the name
  and the description.
- **Name outputs for the attribute they return:** `arn`, `name`. A caller
  writes `module.reports_bucket.arn`, which already names the module.
- **Name module directories in lowercase with hyphens:**
  `modules/private-bucket`. The module call that uses it is
  `module "reports_bucket"`.
- **Never rename a resource or module call without a `moved` block** (see
  [Refactoring without moved blocks](idioms.md#refactoring-without-moved-blocks)).
  A rename otherwise destroys the old object and creates a new one.

## Blocks and arguments

`tofu fmt` aligns the `=` signs and indents, but doesn't reorder anything.
Order the contents of each block the way OpenTofu's style conventions do,
so every block reads the same way:

1. Meta-arguments: `count`, `for_each`, `provider` and `depends_on`, then
   a blank line.
2. Arguments, in groups of related settings separated by blank lines.
3. Nested blocks, each separated by a blank line.
4. The `lifecycle` block, last.

```hcl
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
```

- **Order a `variable` block** as `description`, `type`, `default`, then
  `sensitive`, `ephemeral` and `nullable`, then the `validation` blocks.
  The first lines then say what the input is.
- **Order an `output` block** as `description`, `value`, then `sensitive`.
- **List required variables first,** then the optional ones, so a caller
  sees what they must pass.
- **Separate top-level blocks with one blank line.**
- **Keep lines under 100 columns.** `tofu fmt` never wraps a line, so the
  limit is a guide; a URL, an ARN or a long string can't be split. Break a
  long expression inside its brackets, one item per line, as the
  [test file](tools.md#testing) does.

## Variables and outputs

- **Give every variable a `description` and a `type`,** and every output a
  `description`. The description is the module's documentation, and the
  type makes a wrong value fail at plan time instead of deep inside a
  provider call. Opengrep's `opentofu-variable-without-description`,
  `opentofu-variable-without-type` and
  `opentofu-output-without-description` rules check them.
- **Use the narrowest type:** `string`, `number`, `bool`,
  `list(string)`, or `object({...})` with `optional()` attributes. Never
  `any` or `map(any)`, which accept a value of the wrong shape and fail
  later.
- **Give a default only when one value is right everywhere.** A value that
  differs by environment, such as a name or a size, has no default, so a
  root module that forgets it fails at plan time.
- **Validate inputs with `validation` blocks,** so a bad value fails with
  a clear message at plan time instead of an error from the cloud API
  halfway through an apply.
- **Set `nullable = false`** on a variable that must never be null. A
  caller passing `null` then gets the default, or an error if there is
  none.
- **Mark a variable or output that holds a secret `sensitive = true`.**
  See [Secrets in state, variables and outputs](idioms.md#secrets-in-state-variables-and-outputs)
  for what that does and doesn't protect.

## Formatting

`tofu fmt` formats `.tf`, `.tofu`, `.tfvars`, `.tftest.hcl` and
`.tofutest.hcl` files. It has no style settings: it indents by 2 spaces
and aligns the `=` signs of consecutive arguments. Where this guide and its
output could disagree, `tofu fmt` wins. See
[tools.md](tools.md#formatting).

The [`.editorconfig`](.editorconfig) sets the same indent for editors, and
tabs for Rego, as `conftest fmt` writes it.

## Comments

- **Write comments with `#`.** HCL also accepts `//` and `/* */`, and
  `tofu fmt` leaves them alone, so a file can mix all three. The Opengrep
  rule `opentofu-comment-style` flags the others.
- **Start each file of a module with a comment that says what the module
  builds,** as the [example](idioms.md#a-complete-example) does.
- **Comments explain why:** why a value is pinned, why a check is skipped,
  why a resource is protected. `# create the bucket` above a bucket says
  nothing.
- **Skip a Checkov check only inside the resource that needs it,** with a
  reason after the check ID:
  `# checkov:skip=CKV2_AWS_57:The payments provider issues it; AWS cannot rotate it.`
  A check skipped in [`.checkov.yaml`](.checkov.yaml) is off for every
  resource.
- **The description is the documentation** for a variable or output. Don't
  repeat it in a comment.

## Sources

- [Style conventions](https://opentofu.org/docs/language/syntax/style/)
- [Command: fmt](https://opentofu.org/docs/cli/commands/fmt/)
- [Standard module structure](https://opentofu.org/docs/language/modules/develop/structure/)
- [Input variables](https://opentofu.org/docs/language/values/variables/)
- [Output values](https://opentofu.org/docs/language/values/outputs/)
- [Files and directories](https://opentofu.org/docs/language/files/)
- [Dependency lock file](https://opentofu.org/docs/language/files/dependency-lock/)
- [Language and compatibility settings](https://opentofu.org/docs/language/settings/)
- [Release support](https://github.com/opentofu/opentofu/blob/v1.13.9/CHANGELOG.md)
- [Terraform licence](https://github.com/hashicorp/terraform/blob/main/LICENSE)
