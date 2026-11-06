# R Tools

The free/open source tools that lint, format and check R code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [styler](https://styler.r-lib.org/) | MIT | Formatting | Formatting code to the tidyverse style |
| [lintr](https://lintr.r-lib.org/) | MIT | Linting, Auditing, Code quality | Style, correctness and complexity checks |
| [cyclocomp](https://github.com/gaborcsardi/cyclocomp) | MIT | Code quality | Measuring function complexity for lintr |
| [R CMD check](https://cran.r-project.org/doc/manuals/r-release/R-exts.html#Checking-packages) | GPL-2 or GPL-3 | Linting | Checking a package's code, documentation and dependencies |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [covr](https://covr.r-lib.org/) | MIT | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.lintr`](.lintr) | lintr |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/r.yaml`](.opengrep/r.yaml) | Opengrep |

## Configuration

Code must pass all three checks with **no errors, warnings or notes**:

```sh
Rscript -e 'styler::style_pkg(dry = "fail")'
Rscript -e 'if (length(lintr::lint_package())) quit(status = 1)'
R CMD build . && R CMD check --as-cran *.tar.gz
```

Put the lintr settings in `.lintr` at the package root:

```
linters: linters_with_defaults(
    line_length_linter(80L),
    cyclocomp_linter(complexity_limit = 10L),
    undesirable_function_linter()
  )
exclusions: list(
    "tests/testthat.R" = list(undesirable_function_linter = Inf)
  )
encoding: "UTF-8"
```

- styler owns layout. Don't hand-format code it will rewrite.
- lintr's default linters check the naming, assignment, spacing and quote
  rules in the style guide. `cyclocomp_linter()` isn't a default, so the
  config adds it.
- `tests/testthat.R` calls `library()` to load the package under test, so
  `undesirable_function_linter()` skips that one file.
- `R CMD check` catches undeclared dependencies, undocumented arguments and
  code that uses undefined variables.

## Auditing

### Security analysis

`undesirable_function_linter()`, enabled in the
[configuration](#configuration), flags functions the idioms ban, such as
`attach()` and `setwd()`.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Opengrep's R support is experimental. The starter rules in
[`.opengrep/r.yaml`](.opengrep/r.yaml) cover the unsafe calls in the
[security idioms](idioms.md#security), such as `eval(parse(...))` and
`readRDS()`; test them against known examples before relying on them.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads renv's `renv.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

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

lizard doesn't support R. `cyclocomp_linter()`, set in the
[configuration](#configuration), fails the lint on any function with a
cyclomatic complexity over 10. No FOSS tool limits function length in R, so
review long functions by hand and split any that do more than one thing.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format r --min-tokens 50 --exitCode 1 R
```

### Dead code

lintr's default `object_usage_linter()` reports local variables that are
assigned but never used. No FOSS tool finds unused functions across a
package, so check that every internal function has a caller before keeping
it.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
Rscript -e 'cov <- covr::package_coverage()
  print(cov)
  if (covr::percent_coverage(cov) < 80) quit(status = 1)'
```
