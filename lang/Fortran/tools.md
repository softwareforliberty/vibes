# Fortran Tools

The free/open source tools that lint, format and check Fortran code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU Fortran (gfortran)](https://gcc.gnu.org/fortran/) | GPLv3 | Linting, Auditing | Compiling, linting through its warnings, and runtime checks |
| [Fortitude](https://github.com/PlasmaFAIR/fortitude) | MIT | Linting | Checking style and correctness rules |
| [findent](https://sourceforge.net/projects/findent/) | BSD-3-Clause | Formatting | Indenting source consistently |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [gcovr](https://gcovr.com/) | BSD-3-Clause | Code quality | Summarising gcov test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`fortitude.toml`](fortitude.toml) | Fortitude |
| [`gcovr.cfg`](gcovr.cfg) | gcovr |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Compiler warnings

Compiler warnings are the lint gate. Code must build with **no warnings**
using at least these flags:

```sh
gfortran -std=f2018 -Wall -Wextra -Wimplicit-interface -fimplicit-none \
    -c file.f90
```

- `-std=f2018` rejects non-standard extensions.
- `-Wimplicit-interface` reports calls to procedures without an explicit
  interface, which the [module rule](idioms.md#modules) forbids.
- `-fimplicit-none` makes every file behave as if it had `implicit none`.
- CI adds `-Werror`. Leave it out of the default build, so a newer compiler's
  new warnings don't break builds for users.

Build the tests with runtime checks, so bounds, shape and arithmetic errors
stop the program where they happen:

```sh
gfortran -std=f2018 -g -fcheck=all -fbacktrace \
    -ffpe-trap=invalid,zero,overflow -finit-real=snan -o tests tests.f90
```

## Linting

Fortitude checks style and correctness rules the compiler doesn't, such as
missing `implicit none` and missing `intent`. Run it over the whole source
tree:

```sh
fortitude check
```

Put its settings in `fortitude.toml` at the project root:

```toml
[check]
line-length = 100
# C003 asks for implicit none (type, external). This guide writes plain
# implicit none, and gfortran's -Wimplicit-interface reports the calls
# without an explicit interface that C003 guards against.
ignore = ["C003"]
```

## Formatting

findent re-indents source to the [layout rules](coding-style.md#indentation).
It reads standard input and writes standard output, so CI compares its output
with the file:

```sh
findent -i4 < linalg.f90 | diff -u linalg.f90 -
```

findent only changes indentation. Spacing, case and line length are checked
by review and Fortitude. fprettify isn't listed because it has had no release
since 2020.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of Fortran source, and
Opengrep doesn't support Fortran. The closest check is running the tests
with the [runtime checks](#compiler-warnings) above and with
AddressSanitizer, which catch out-of-bounds access and use of freed memory as
they happen:

```sh
gfortran -std=f2018 -g -fsanitize=address,undefined -o tests tests.f90
```

### Dependency vulnerabilities

fpm writes no lockfile, and no vulnerability database covers Fortran
packages, so OSV-Scanner has nothing to check. Pin every dependency in
`fpm.toml` to a tag or commit (`tag = "v1.2.0"`), and follow the security
advisories of the packages you depend on.

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

Fail the build on any function with a cyclomatic complexity over 10 or more
than 60 lines of code. A function past either limit is hard to test and
should be split.

```sh
lizard -l fortran -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format fortran --min-tokens 50 --exitCode 1 src
```

### Dead code

`-Wall` reports unused variables and dummy arguments, and `-Wextra` adds
unused named constants. No FOSS tool finds public procedures that nothing
calls, so check that every public procedure has a caller before keeping it.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
gfortran -std=f2018 --coverage -o tests tests.f90
./tests
gcovr --root .
```

gcovr reads the minimum from `gcovr.cfg` in the root directory:

```ini
# gcovr reads this file from the --root directory.
fail-under-branch = 80
```
