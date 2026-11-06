# Make Tools

The free/open source tools that lint, format and check Make code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU Make](https://www.gnu.org/software/make/) 4.3 or later | GPLv3 | Linting | Building, and linting through its own warnings |
| [checkmake](https://github.com/checkmake/checkmake) | MIT | Linting, Code quality | Linting makefiles for phony targets, duplicate targets and long recipes |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`checkmake.ini`](checkmake.ini) | checkmake |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Make warnings

GNU Make's warning for undefined variables is the lint gate. It catches typos
in variable names, which Make otherwise expands silently to nothing. A
makefile must produce **no warnings** when dry-run with the check enabled:

```sh
make --warn-undefined-variables --dry-run all
```

- Newer GNU Make releases also spell this check `--warn=undefined-var`, and
  keep `--warn-undefined-variables` as an alias.
- The check only reports warnings, so CI fails the build when the output
  contains `warning:`.
- Define every variable the makefile reads, even as empty (`LDLIBS ?=`), so
  the check stays quiet for variables that are meant to be empty.
- macOS ships GNU Make 3.81, which is too old. Install a current GNU Make from
  a package manager.

## checkmake

checkmake lints the main makefile, and exits with an error when it finds a
violation:

```sh
checkmake Makefile
```

checkmake reads each file on its own and doesn't follow `include`, so on an
included `.mk` fragment it reports the standard targets as missing. Run it on
the main makefile only, and review fragments against the same rules.

Commit a `checkmake.ini` at the repository root, so it requires the standard
targets from the [naming rules](coding-style.md#naming) instead of its own
defaults:

```ini
[minphony]
required = all,clean,check
```

Its rules check that:

- every required target exists and is declared `.PHONY` (`minphony`)
- every target without a recipe is declared `.PHONY` (`phonydeclared`; see
  [Phony targets](idioms.md#phony-targets))
- no target is defined twice (`uniquetargets`)
- no recipe is longer than 5 lines (`maxbodylength`)
- a variable that holds a timestamp is simply expanded with `:=`, so it
  doesn't change between rules (`timestampexpanded`)

## Auditing

### Security analysis

No maintained FOSS static analyser understands makefiles. The closest check
is a dry run, which prints every command the build would run without running
it, so a change that adds a download or a new tool shows up in review:

```sh
make --dry-run --always-make all
```

### Dependency vulnerabilities

Make has no package manager, so there are no third-party dependencies to
audit.

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

No maintained FOSS tool measures complexity in makefiles, and lizard doesn't
read them. The closest check is checkmake's `maxbodylength` rule (see
[checkmake](#checkmake)), which flags any recipe longer than 5 lines.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format makefile --min-tokens 50 --exitCode 1 .
```

### Coverage

No maintained FOSS tool measures which rules a build runs. The closest check
is to dry-run every standard target in CI, so a target whose prerequisites no
longer resolve fails the build:

```sh
for target in all check clean; do
  make --dry-run --always-make "$target" || exit 1
done
```
