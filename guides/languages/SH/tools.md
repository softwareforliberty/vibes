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
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

## Config files

These files are in this directory, ready to copy to the root of a project:

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Editors and IDEs, and shfmt |
| [.shellcheckrc](.shellcheckrc) | ShellCheck |
| [.opengrep/sh.yaml](.opengrep/sh.yaml) | Opengrep |
| [.jscpd.json](.jscpd.json) | jscpd |
| [universalmutator.rules](universalmutator.rules) | universalmutator |

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
jscpd --format bash --min-tokens 50 --exit-code 1 .
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

### Mutation testing

universalmutator makes small changes to the code, such as turning `-ge` into
`-gt`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for POSIX sh. universalmutator works on any language,
because it rewrites the source text with regular expressions, so it's only as
good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for Bash and
POSIX sh. They move each comparison's boundary, flip `=`, `!=`, `-z`, `-n`,
`&&` and `||`, drop `!`, change arithmetic and standalone numbers by one, and
delete commands. They leave comments and the `set` line alone, and never swap a
redirection, so a mutant can't turn a read into a write that empties a file.
Pass it with `--only`: the built-in rules are written for C-like languages, and
add mutants that can't compile or can't change anything.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each script, `mutate` writes the mutants that still
parse, and `analyze_mutants` copies each one over the script in turn and runs
the tests. The last line fails when the tests kill fewer than 80% of the
mutants:

```sh
rm -rf .mutants
mkdir .mutants
files=$(git diff --name-only --diff-filter=d origin/main... \
  -- bin '*.sh' ':!test/')
for f in ${files}; do
  d=.mutants/${f}
  mkdir -p "${d}"
  cp "${f}" "${d}/script.sh"
  mutate "${d}/script.sh" --only universalmutator.rules --noFastCheck \
    --mutantDir "${d}" --cmd "sh -n ${d}/script.sh"
  analyze_mutants "${d}/script.sh" "cp MUTANT ${f} && bats test" \
    --mutantDir "${d}" --prefix "${d}/run"
  cp "${d}/script.sh" "${f}"
done
killed=$(find .mutants -name run.killed.txt -exec cat {} + | wc -l)
total=$(find .mutants -name 'run.*killed.txt' -exec cat {} + | wc -l)
echo "Mutation score: ${killed} of ${total} mutants killed"
[ "$((killed * 100))" -ge "$((total * 80))" ]
```

Install it with pip, pinned to the version this guide was checked with:

```sh
pip install universalmutator==1.14.1
```

- universalmutator names mutants after the file's extension, and executables
  have none. So the loop mutates a copy named `script.sh`, and puts the script
  back when it's done. `cp` keeps the script's mode, so it stays executable.
- `--cmd` drops the mutants that don't parse, so a syntax error isn't counted
  as a kill. Without `--noFastCheck`, `mutate` skips every line that `sh -n`
  still accepts when it's replaced by junk, which is most commands.
- Each mutant runs the script, so run the tests somewhere a wrong command can't
  do harm, such as a container.
- A test run that takes longer than 30 seconds is stopped and counted as a
  kill. If the build and tests take longer, give `analyze_mutants` a larger
  `--timeout`.
- Run it on a clean working tree, and add `.mutants/` to `.gitignore`. If a run
  is interrupted, `git status` shows the script it left mutated.

80% is the same bar as coverage. Some mutants can't change what the code does,
so 100% is rarely reachable; 80% leaves room for them and still fails a change
whose tests check little.

`.mutants/<file>/run.notkilled.txt` lists the survivors of each file. Compare
one with the source to see what changed:

```text
$ diff bin/grade .mutants/bin/grade/script.mutant.15.sh
12c12
< elif [ "${score}" -ge 50 ]; then # the pass mark, 50
---
> elif [ "${score}" -gt 50 ]; then # the pass mark, 50
```

Read it as a missing test: here, no test passes exactly 50, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that just
runs the line. A mutant that can't change behaviour needs no test; the
threshold allows for it.

### Architecture

POSIX sh has no modules and nothing private. `.` runs a file in the current
shell, so every function it defines can be called by any code that runs
after it. ShellCheck follows the files a script sources, but doesn't check
which files may source which. So give the layers a layout and names that
show each breach, and have `scripts/check` search for them, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks.

Give each layer its own directory under `lib`. The names are examples:
replace them with the layers in the project's `design.md`.

```text
lib/core/core.sh              the core's entry point
lib/core/internal/format.sh   the rest of the core
lib/adapters/adapters.sh      an edge's entry point
lib/cli/cli.sh                another edge's entry point
```

- A layer's entry point is its front door. Its functions start with the
  layer's name and `_`, such as `core_greet`, as for any
  [library](coding-style.md#naming).
- Keep the rest of the layer in its `internal` directory. Only the entry
  point sources those files, and their functions start with `_` and the
  layer's name, such as `_core_title`.
- Code outside a layer, and the layer's own tests, source only its entry
  point and call only its public functions.
- The core sources no edge and calls none of an edge's functions. An edge
  may use the core.

A sourced file can't find its own path in POSIX sh, so the executable sets
`APP_LIB` to the `lib` directory, and every `.` line starts from it.
ShellCheck can't follow a path built from a variable, so name the file in a
directive above it. The core's entry point loads its internals like this:

```sh
# shellcheck source=lib/core/internal/format.sh
. "${APP_LIB}/core/internal/format.sh"
```

Add the check to `scripts/check`. It fails on the first rule a change
breaks, and prints the file, line and text of each breach. Comment lines
don't count.

```sh
# The layers, core first. Replace them with the layers in design.md.
core='core'
edges='adapters cli'

# Prints the lines, outside comments, that match $1 in the files $2...
uses() {
  grep -rnE "$@" | grep -vE '^[^:]*:[0-9]+:[[:space:]]*#'
}

for edge in ${edges}; do
  if uses "(^|[^[:alnum:]_])_?${edge}[/_]" "lib/${core}"; then
    echo "the core must not use ${edge}" >&2
    exit 1
  fi
done

for c in ${core} ${edges}; do
  if uses "${c}/internal/|(^|[^[:alnum:]_])_${c}_" bin lib test \
    | grep -v "^lib/${c}/"; then
    echo "use ${c} only through lib/${c}/${c}.sh" >&2
    exit 1
  fi
  if grep -rnE '^[[:space:]]*[[:alnum:]_]+[[:space:]]*\(\)' "lib/${c}" \
    | grep "^lib/${c}/internal/" | grep -vE ":[[:space:]]*_${c}_"; then
    echo "name the functions in lib/${c}/internal _${c}_..." >&2
    exit 1
  fi
done
```

- The first loop fails when the core names an edge's directory, such as
  `adapters/`, or one of its functions, such as `adapters_print`.
- The second fails when code outside a layer, in `bin`, `lib` or `test`,
  names the layer's `internal` directory or one of its `_core_` functions.
- The third fails when a function in an `internal` directory lacks its
  layer's prefix, so that outside code could call it unseen.
- Search only directories that exist: grep reports an error for a missing
  one.
- It's POSIX sh, and uses only grep options that GNU, BSD and BusyBox grep
  all have, so it runs the same under dash, BusyBox and the Bash 3.2 that
  macOS ships.

A breach prints:

```text
lib/core/breach_uses_edge.sh:6:  adapters_print 'breach'
the core must not use adapters
```

The check reads text, so it misses a path or a name built at run time,
such as `. "${APP_LIB}/${layer}/${layer}.sh"`, and anything run through
`eval`. It doesn't check global variables either. Review catches the rest.

Prove the rules bite, as the
[builder](../../../agents/builder.md) does, with a new file that breaks
one. Kept as `scripts/breaches/core-uses-edge.patch`, the breach for the
layer rule is:

```text
Rule: the core never uses an edge
Fails with: the core must not use adapters
diff --git a/lib/core/breach_uses_edge.sh b/lib/core/breach_uses_edge.sh
new file mode 100644
index 0000000..d7d2364
--- /dev/null
+++ b/lib/core/breach_uses_edge.sh
@@ -0,0 +1,7 @@
+# shellcheck shell=sh
+#
+# A breach: the core calls an edge.
+
+core_breach() {
+  adapters_print 'breach'
+}
```

The breach passes `shfmt` and ShellCheck, so `scripts/check` fails on the
layer rule and not on a lint error first. To let one existing breach
through, add a `grep -v` for its file to that rule's pipeline, with a
comment naming the breach and how to fix it.

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
- [POSIX.1-2017: the dot utility](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#dot)
- [ShellCheck directives](https://github.com/koalaman/shellcheck/wiki/Directive)
