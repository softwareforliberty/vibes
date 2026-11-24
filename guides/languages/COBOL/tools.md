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
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

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
| [`universalmutator.rules`](universalmutator.rules) | universalmutator |

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

### Mutation testing

universalmutator makes small changes to the code, such as turning `>=` into
`>`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for GnuCOBOL. universalmutator works on any language,
because it rewrites the source text with regular expressions, so it's only as
good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for COBOL.
They move each comparison's boundary, flip `=`, `NOT =`, `AND` and `OR`, change
arithmetic and numbers by one, and delete statements by making them comment
lines. They leave comments, `PIC` clauses and scope terminators alone, since
changing those can't fail a test or can't compile. Pass it with `--only`: the
built-in rules are written for C-like languages, and add mutants that can't
compile or can't change anything.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each file, `mutate` writes the mutants that still
compile, and `analyze_mutants` copies each one over the file in turn, runs the
tests, and puts the file back. The last line fails when the tests kill fewer
than 80% of the mutants:

```sh
rm -rf .mutants
mkdir .mutants
files=$(git diff --name-only --diff-filter=d origin/main... \
  -- '*.cob' ':!test/')
for f in $files; do
  d=.mutants/$f
  mkdir -p "$d"
  mutate "$f" --only universalmutator.rules --mutantDir "$d" \
    --cmd "cobc -std=cobol2014 -fsyntax-only $f"
  analyze_mutants "$f" 'make test' --mutantDir "$d" --prefix "$d/run"
done
killed=$(find .mutants -name run.killed.txt -exec cat {} + | wc -l)
total=$(find .mutants -name 'run.*killed.txt' -exec cat {} + | wc -l)
echo "Mutation score: $killed of $total mutants killed"
[ "$((killed * 100))" -ge "$((total * 80))" ]
```

Install it with pip, pinned to the version this guide was checked with:

```sh
pip install universalmutator==1.14.1
```

- Replace `make test` with the project's test command. It must rebuild from
  source, since each mutant replaces the file on disk.
- `':!test/'` leaves out the test programs, since mutating a test proves
  nothing. Change it to wherever the project keeps them.
- `--cmd` drops the mutants that don't compile, so a build failure isn't
  counted as a kill. Name the file in `--cmd`, not the `MUTANT` placeholder,
  which crashes version 1.14.1.
- A test run that takes longer than 30 seconds is stopped and counted as a
  kill. If the build and tests take longer, give `analyze_mutants` a larger
  `--timeout`.
- Run it on a clean working tree, and add `.mutants/` to `.gitignore`. If a run
  is interrupted, `git status` shows a file it left mutated.

80% is the same bar as coverage. Some mutants can't change what the code does,
so 100% is rarely reachable; 80% leaves room for them and still fails a change
whose tests check little.

`.mutants/<file>/run.notkilled.txt` lists the survivors of each file. Compare
one with the source to see what changed:

```text
$ diff src/GRADE.cob .mutants/src/GRADE.cob/GRADE.mutant.5.cob
15c15
<                IF LS-SCORE >= 50 *> the pass mark, 50
---
>                IF LS-SCORE > 50 *> the pass mark, 50
```

Read it as a missing test: here, no test passes exactly 50, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that just
runs the line. A mutant that can't change behaviour needs no test; the
threshold allows for it.

### Architecture

COBOL has no modules, so the build enforces what it can of the layers, as
the [architecture guide](../../../architecture/README.md#enforce-it) asks,
and `scripts/check` checks the rest. Give each layer its own directory, with
its entry points at the top: the programs other layers may `CALL`, and, in
`copy`, the copybooks they may `COPY`, such as the records those programs
take. Everything else goes under `internal`. The names are examples: replace
them with the layers in the project's `design.md`.

```text
core/GREET.cob              an entry point
core/copy/GREETREC.cpy      the record GREET takes
core/internal/FMTNAME.cob   a program only the core calls
core/internal/FMTREC.cpy    a copybook only the core copies
core/tests/TGREET.cob       the core's tests
adapters/SHOW.cob           an edge, which calls GREET
adapters/copy/SHOWREC.cpy   the record SHOW takes
```

The build enforces the copybooks. `cobc -I` adds a directory to the ones a
`COPY` searches. Compile each layer with its own `copy` directory, its
`internal` one if it has one, and the `copy` directory of each layer it may
use. Compile its tests with only its own `copy`. `scripts/check` runs the
build, with the [compiler warnings](#compiler-warnings) flags too:

```sh
rm -rf build
mkdir -p build/core build/adapters build/tests
for f in core/*.cob core/internal/*.cob; do
  cobc -c -std=cobol2014 -I core/copy -I core/internal \
    -o "build/core/$(basename "$f" .cob).o" "$f"
done
for f in adapters/*.cob; do
  cobc -c -std=cobol2014 -I adapters/copy -I core/copy \
    -o "build/adapters/$(basename "$f" .cob).o" "$f"
done
for f in core/tests/*.cob; do
  cobc -x -std=cobol2014 -I core/copy \
    -o "build/tests/$(basename "$f" .cob)" "$f" build/core/*.o
done
```

A `COPY` of an edge's copybook in the core, or of an internal copybook in an
edge or a test, fails to compile with `SHOWREC: No such file or directory`.
cobc also searches the directory it runs in, so a `COPY` that names a path,
such as `COPY "core/internal/FMTREC.cpy"`, or a library, such as
`COPY FMTREC IN "core/internal"`, gets around the copy path. Fail
`scripts/check` on either. A breach prints the file, the line and the
`COPY`:

```sh
if grep -rniE -e "COPY[[:space:]]+[\"'][^\"']*/" \
    -e 'COPY[[:space:]]+[A-Z0-9-]+[[:space:]]+(IN|OF)[[:space:]]' \
    core adapters cli; then
  echo 'COPY a copybook by its name alone' >&2
  exit 1
fi
```

Nothing limits a `CALL`: a program can call any other by name, wherever it's
compiled. Only a nested program is hidden. Without `COMMON`, only the
program that contains it can call it, so a helper that one program calls can
be nested inside it. For the rest, `scripts/check` matches each literal
`CALL` against the programs its caller may not call. The
[file rules](coding-style.md#files) give each program its file's name, so
the check finds them by file. The core calls no edge. Only the core's own
programs call its internal ones, so its tests, like the edges, go through
its entry points. A breach prints the file, the line and the `CALL`:

```sh
# Prints a pattern that matches a literal CALL of each program in the
# given directories. Each program is named after its file.
call_patterns() {
  find "$@" -name '*.cob' |
    sed -E "s|.*/||; s|\.cob$||; s|.*|CALL[[:space:]]+[\"']&[\"']|"
}

if grep -rniE -f <(call_patterns adapters cli) core; then
  echo 'the core calls an edge program' >&2
  exit 1
fi
if grep -rniE -f <(call_patterns core/internal) adapters cli core/tests
then
  echo 'call the core through its entry points' >&2
  exit 1
fi
```

Repeat the second check for each layer with an `internal` directory.

A `CALL` of a data name, such as `CALL WS-PROGRAM`, picks its program at run
time, so no check can see where it goes. Review must catch any that can
reach an edge from the core, or an internal program from outside its layer.
When existing code breaks a rule, leave that one file out of the check with
`--exclude=OLDRPT.cob`, or give that one program the internal directory,
with a comment naming the breach and how to fix it.

Keep a breach of each rule as `scripts/breaches/<rule>.patch`, as the
builder does. The build compiles every program in a layer's directory, so a
breach needs only a new file. For the layers, `core/BREACH.cob`:

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. BREACH.
      * Breaks a boundary rule on purpose: the core calls an edge.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NAME                     PIC X(20) VALUE "Ada".
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL "SHOW" USING WS-NAME
           END-CALL
           GOBACK.
```

Its patch starts with:

```text
Rule: the core never calls an edge
Fails with: the core calls an edge program
```

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
- [GnuCOBOL manual: compiler options](https://gnucobol.sourceforge.io/doc/gnucobol.html)
- [GnuCOBOL Programmer's Guide: nested programs and COMMON](https://gnucobol.sourceforge.io/HTML/gnucobpg.html)
