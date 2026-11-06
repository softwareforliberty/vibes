# POSIX sh Tools

The free/open source tools that lint, format and check POSIX sh code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [ShellCheck](https://www.shellcheck.net/) | GPLv3 | Linting, Auditing | Linting: quoting bugs, unsafe constructs and non-POSIX features |
| [shfmt](https://github.com/mvdan/sh) | BSD-3-Clause | Formatting, Linting | Formatting, and rejecting syntax POSIX doesn't have |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [bats-core](https://github.com/bats-core/bats-core) | MIT | Code quality | Testing scripts |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring test coverage |

## Config files

These files are in this directory, ready to copy to the root of a project:

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Editors and IDEs, and shfmt |
| [.shellcheckrc](.shellcheckrc) | ShellCheck |
| [.opengrep/sh.yaml](.opengrep/sh.yaml) | Opengrep |
| [.jscpd.json](.jscpd.json) | jscpd |

## Formatting

shfmt is the formatter. It reads its settings from
[.editorconfig](.editorconfig), so run it with no formatting flags: shfmt
ignores `.editorconfig` entirely when any formatting flag is given. Run it in
check mode in CI, and in write mode locally:

```sh
shfmt -d .   # show what would change
shfmt -w .   # rewrite the files
```

- `shell_variant = posix` parses scripts as POSIX shell, so non-POSIX syntax
  is an error.
- `indent_size = 2` indents with 2 spaces.
- `switch_case_indent = true` indents the branches of a `case`.
- `binary_next_line = true` lets `|`, `&&` and `||` start a continuation line.
- Given a directory, shfmt also finds scripts with no extension by their
  shebang. The `[[shell]]` section gives them the same settings, because they
  have no extension for an editor section to match.
- `*.bats` test files are parsed with `shell_variant = bats`.
- kcov's report in `coverage/` holds its own helper scripts. The
  `[coverage/**]` section sets `ignore = true`, so shfmt skips them.

## Linting

Code must pass ShellCheck with **no warnings**. Put this
[.shellcheckrc](.shellcheckrc) at the root of the repository to turn on the
optional checks this guide relies on:

```ini
enable=add-default-case
enable=avoid-nullary-conditions
enable=quote-safe-variables
enable=require-variable-braces
```

Run it on every script that shfmt finds, including the ones with no
extension:

```sh
shfmt -f . | xargs shellcheck
```

ShellCheck reads the dialect from the `#!/bin/sh` shebang, and warns about
every feature POSIX doesn't define.

When a warning is a false positive, disable that one check on the line above
the code, and add a comment saying why:

```sh
# Read by the scripts that source this library.
# shellcheck disable=SC2034
readonly LIB_VERSION="1.2.0"
```

## Auditing

### Security analysis

ShellCheck is the main security check for shell scripts. Most of its
warnings, such as unquoted expansions (SC2086), are word-splitting and
injection bugs, so the [linting](#linting) gate already covers them.
Opengrep adds checks ShellCheck doesn't have, such as rules for your own
project's dangerous commands.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

The starter rules in [.opengrep/sh.yaml](.opengrep/sh.yaml) catch the
patterns [idioms.md](idioms.md) forbids: `eval`, SUID and SGID modes,
fixed paths in `/tmp`, and `which`.

### Dependency vulnerabilities

POSIX sh has no package manager, so there are no third-party dependencies
to audit.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

No maintained FOSS tool measures the complexity of shell scripts. Keep
scripts small instead: a script that needs complex logic, or grows past
about 100 lines, should be
[rewritten in a general-purpose language](idioms.md#principles).

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format bash --min-tokens 50 --exitCode 1 .
```

### Dead code

ShellCheck reports variables that are set but never used (SC2034) and
commands that can never run (SC2317). Both are on by default, so the
[linting](#linting) gate catches them.

### Coverage

Write tests with bats-core, and measure their coverage with kcov. kcov can
only trace Bash, and its `--bash-handle-sh-invocation` option doesn't help:
it doesn't trace a script run as `sh script`, and it passes the wrong
arguments to a `#!/bin/sh` script run by its path. So each test runs the
script under test with the shell named in `TEST_SHELL`, which defaults to
`sh`, and the coverage run sets it to Bash:

```bash
@test "greet says hello" {
  run "${TEST_SHELL:-sh}" bin/greet Ada
  [[ "${output}" == "Hello, Ada" ]]
}
```

```sh
bats test/
TEST_SHELL=bash kcov --include-path=. coverage/ bats test/
```

Coverage measured under Bash doesn't prove a script works under dash, so
still [test scripts under dash](idioms.md#portability). kcov writes an HTML
report to `coverage/`. It has no coverage threshold of its own, so review
the report for untested branches.
