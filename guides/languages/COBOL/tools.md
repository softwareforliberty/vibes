# COBOL Tools

The free/open source tools that lint, format and check COBOL code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GnuCOBOL](https://gnucobol.sourceforge.io/) | GPL-3.0-or-later (compiler), LGPL-3.0-or-later (runtime) | Linting, Auditing, Code quality | Compiling, linting through its warnings, runtime checks and coverage |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [gcovr](https://gcovr.com/) | BSD-3-Clause | Code quality | Summarising gcov test coverage |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

COBOL has few FOSS tools beyond the compiler. Where no maintained tool
exists, the section below says so and gives the closest check.

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`gcovr.cfg`](gcovr.cfg) | gcovr |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Compiler warnings

Compiler warnings are the lint gate. Code must build with **no warnings**
using at least these flags:

```sh
cobc -x -std=cobol2014 -Wall -Wextra -Wpossible-truncate -Wunreachable \
    CUSTRPT.cob
```

- `-std=cobol2014` reports anything outside the
  [language baseline](coding-style.md#language-baseline).
- `-Wpossible-truncate` and `-Wunreachable` aren't turned on by `-Wall`.
  They report moves that may cut a value short, and statements that can
  never run.
- CI adds `-Werror`. Leave it out of the default build, so a newer compiler's
  new warnings don't break builds for users.

Build the tests with `-debug`, which turns on every runtime check: out-of-range
subscripts and reference modifications, and invalid numeric data stop the
program instead of continuing with bad values:

```sh
cobc -x -std=cobol2014 -debug -o test-custrpt CUSTRPT.cob
```

## Linting and formatting

No maintained FOSS linter or formatter covers COBOL. The compiler checks the
[reference format](coding-style.md#reference-format), including statements
that run past column 72. Review checks the rest of the style guide.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of COBOL, and Opengrep doesn't
support it. The closest checks are the `-debug` runtime checks in the test
build, and a review of every `CALL`, every embedded SQL statement and every
place input reaches a file name or command.

### Dependency vulnerabilities

COBOL has no package manager, so there are no third-party dependencies to
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

lizard doesn't support COBOL, and no other maintained FOSS tool measures
COBOL complexity. Review paragraphs by hand, and split any paragraph longer
than 60 lines or with deeply nested conditions.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other. Move repeated data layouts into
copybooks, and repeated logic into a called program.

```sh
jscpd --format cobol --min-tokens 50 --exit-code 1 .
```

jscpd reads `.cob` programs and `.cpy` copybooks as its `cobol` format.

### Dead code

`-Wunreachable`, set in the [compiler warnings](#compiler-warnings), reports
statements that can never run. No FOSS tool finds paragraphs that nothing
`PERFORM`s, so check that every paragraph has a caller before keeping it.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

GnuCOBOL compiles COBOL to C. With `--coverage`, it instruments that C code
for gcov and maps it back to the COBOL source lines:

```sh
cobc -x -std=cobol2014 --coverage -o test-custrpt CUSTRPT.cob
./test-custrpt
gcovr --root .
```

gcovr reads the minimum from `gcovr.cfg` in the root directory:

```ini
# gcovr reads this file from the --root directory.
fail-under-line = 80
```
