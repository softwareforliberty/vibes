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
| [muttest](https://jakubsob.github.io/muttest/) | MIT | Code quality | Mutation testing |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.lintr`](.lintr) | lintr |
| [`.Rbuildignore`](.Rbuildignore) | `R CMD build` |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/r.yaml`](.opengrep/r.yaml) | Opengrep |

## Configuration

Code must pass all three checks with **no errors, warnings or notes**:

```sh
Rscript -e 'styler::style_pkg(dry = "fail")'
Rscript -e 'if (length(lintr::lint_package())) quit(status = 1)'
out="$(mktemp -d)"
(cd "${out}" && R CMD build "${OLDPWD}" &&
  _R_CHECK_CRAN_INCOMING_=false R CMD check --as-cran --no-manual ./*.tar.gz)
grep -qx 'Status: OK' "${out}"/*.Rcheck/00check.log
```

- **`R CMD check` exits 0 on warnings and notes,** and fails only on
  errors. The last line fails the check unless the log's status is `OK`.
- **Build and check in a temporary directory.** Run in the project, they
  leave a tarball and a `.Rcheck` directory behind, which the commit gate
  refuses as untracked files.
- `_R_CHECK_CRAN_INCOMING_=false` skips CRAN's incoming checks. They need
  the network, and report every package that isn't on CRAN yet as a new
  submission. Run a full `R CMD check --as-cran` before submitting to CRAN.
- `--no-manual` skips building the PDF manual, which needs LaTeX. The
  documentation checks still run.

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

`R CMD check` reports any hidden file in the package as a note, so
`.Rbuildignore` keeps the tool config files out of the built package.
Each line is a regular expression matched against paths from the package
root:

```text
^\.editorconfig$
^\.jscpd\.json$
^\.lintr$
^\.opengrep$
```

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
jscpd --format r --min-tokens 50 --exit-code 1 R
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

### Mutation testing

muttest makes small changes to the package's code, such as turning `>=`
into `>`, and runs the testthat tests against each one. A change the tests
still pass, a surviving mutant, is behaviour no test pins down. A full run
is slow, so `scripts/audit` mutates only the files in `R/` changed since
the base branch, and skips the run when there are none:

```sh
files=$(git diff --name-only --diff-filter=d origin/main... -- 'R/*.R')
[ -z "$files" ] || Rscript -e 'plan <- muttest::muttest_plan(
    c(
      muttest::arithmetic_operators(),
      muttest::comparison_operators(),
      muttest::logical_operators(),
      muttest::condition_mutations()
    ),
    source_files = commandArgs(trailingOnly = TRUE)
  )
  if (nrow(plan) > 0) {
    score <- muttest::muttest(plan)
    if (is.na(score) || score < 0.8) quit(status = 1)
  }' $files
```

- The mutators are operators and conditions, where a missing test most
  often hides. Add others from the
  [mutator reference](https://jakubsob.github.io/muttest/articles/mutators.html)
  as the tests grow.
- A changed file with nothing to mutate makes an empty plan, which passes.

Install it as a development dependency, listed under `Suggests`. This
guide was checked with muttest 0.3.0 and testthat 3.3.2.

`muttest()` returns the mutation score, the share of mutants the tests
kill, and the command exits non-zero when it's under 80%. That's the same
bar as coverage. Some mutants can't be killed, because they don't change
what the code does, so 100% is rarely reachable; 80% leaves room for them
and still fails a change whose tests check little.

Under `Survived Mutants`, the report prints each survivor with its file,
mutator, line and a diff:

```text
price.R  >= → >
  7-   if (total >= 100) {
  7+   if (total > 100) {
```

Read it as a missing test: here, no test passes exactly 100, so the
boundary isn't pinned down. Write the test that fails on the mutant, not
one that just runs the line. muttest has no way to skip a single mutant,
so if one can't change behaviour, leave it to the margin under 80% rather
than writing a test that contorts the code.

## Sources

- [muttest documentation](https://jakubsob.github.io/muttest/)
