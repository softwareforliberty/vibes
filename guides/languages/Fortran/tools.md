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
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`fortitude.toml`](fortitude.toml) | Fortitude |
| [`gcovr.cfg`](gcovr.cfg) | gcovr |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`universalmutator.rules`](universalmutator.rules) | universalmutator |

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
jscpd --format fortran --min-tokens 50 --exit-code 1 src
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

### Mutation testing

universalmutator makes small changes to the code, such as turning `>=` into
`>`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for Fortran. universalmutator works on any language,
because it rewrites the source text with regular expressions, so it's only as
good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for Fortran.
They move each comparison's boundary, flip `==`, `/=` and the logical
operators, change arithmetic and numbers by one, and delete statements. They
leave comments and declarations alone, since changing those can't fail a test.
Pass it with `--only`: the built-in rules also add a `continue;` line after
each statement, which is a valid no-op in Fortran, so no test can kill it.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each file, `mutate` writes the mutants that still
compile, and `analyze_mutants` copies each one over the file in turn, runs the
tests, and puts the file back. The last line fails when the tests kill fewer
than 80% of the mutants:

```sh
rm -rf .mutants
mkdir .mutants
files=$(git diff --name-only --diff-filter=d origin/main... -- 'src/*.f90')
for f in $files; do
  d=.mutants/$f
  mkdir -p "$d"
  mutate "$f" --only universalmutator.rules --mutantDir "$d" \
    --cmd "gfortran -std=f2018 -fsyntax-only -Ibuild -J$d $f"
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
- `--cmd` drops the mutants that don't compile, so a build failure isn't
  counted as a kill. `-Ibuild` names the directory that holds the project's
  `.mod` files, and `-J$d` keeps the check's own `.mod` files out of it. Name
  the file in `--cmd`, not the `MUTANT` placeholder, which crashes version
  1.14.1.
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
$ diff src/grading.f90 .mutants/src/grading.f90/grading.mutant.9.f90
16c16
<     else if (score >= 50) then ! the pass mark
---
>     else if (score > 50) then ! the pass mark
```

Read it as a missing test: here, no test passes exactly 50, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that just
runs the line. A mutant that can't change behaviour needs no test; the
threshold allows for it.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks.
gfortran finds the module a `use` names by its `.mod` file, in the directory
`-J` writes to or one that `-I` names. Give each layer its own module
directory, and compile each layer with only the directories of the layers it
may use, so a `use` of any other layer's module fails to compile. fpm can't
do this: it writes every package's `.mod` files to one directory, where any
module finds any other. Build a project with layers with
[CMake](../../build/CMake/idioms.md) instead.

Make each layer its own library target, with its own
`Fortran_MODULE_DIRECTORY`, and add that directory as a `PUBLIC` include
directory, so the targets that link the layer find its modules. Never leave a
target without one: its `.mod` files then go to the build directory of its
source folder, where every target built from that folder finds them.

Each layer's `CMakeLists.txt` declares its target, its sources and the layers
it may use. The target names are examples: replace them with the layers in
the project's `design.md`. `adapters/CMakeLists.txt`:

```cmake
add_library(app_adapters STATIC src/console.f90)
set_target_properties(
    app_adapters
    PROPERTIES Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/mod"
)
target_include_directories(
    app_adapters
    PUBLIC "${CMAKE_CURRENT_BINARY_DIR}/mod"
)
target_link_libraries(app_adapters PUBLIC app_core)
```

The core's target links no other layer, so a core module that uses an edge's
module fails to compile with `Cannot open module file 'console.mod'`. CMake
allows a cycle between static libraries, so nothing stops the core linking
an edge and using its modules. Check for it at the end of the top-level
`CMakeLists.txt`, after the `add_subdirectory()` calls:

```cmake
# CMake allows a cycle between static libraries, so check that the core
# links no edge.
get_target_property(app_core_links app_core LINK_LIBRARIES)
foreach(edge IN ITEMS app_adapters app_cli)
    if(edge IN_LIST app_core_links)
        message(FATAL_ERROR "app_core must not link ${edge}")
    endif()
endforeach()
```

`scripts/check` runs the build, so a breach fails it. The check names the
edge the core links, and the compiler names the module it can't find:

```sh
cmake -S . -B build
cmake --build build
```

Fortran's own rules give each module a front door. Start each module with
`private`, and list its entry points in a `public` statement, as under
[Modules](idioms.md#modules). A `use` of anything else fails to compile,
with `Symbol 'bracket' referenced at (1) not found in module 'greeting'`. A
`use` can't name a submodule at all, so a module's implementation can go in
one.

A layer's modules also use each other, so a layer has modules only it may
use. Keep them under `src/internal`, in a target of their own with its own
module directory, and link that target `PRIVATE`: the layer's own modules
find them, and the targets that link the layer don't. Build the layer's tests
as a separate target that links the layer, so they see only the entry
points, as callers do. `core/CMakeLists.txt`:

```cmake
add_library(app_core_internal OBJECT src/internal/text_format.f90)
set_target_properties(
    app_core_internal
    PROPERTIES Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/internal"
)
target_include_directories(
    app_core_internal
    INTERFACE "${CMAKE_CURRENT_BINARY_DIR}/internal"
)

add_library(app_core STATIC src/greeting.f90)
set_target_properties(
    app_core
    PROPERTIES Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/mod"
)
target_include_directories(
    app_core
    PUBLIC "${CMAKE_CURRENT_BINARY_DIR}/mod"
)
target_link_libraries(app_core PRIVATE app_core_internal)

add_executable(app_core_tests tests/greeting_test.f90)
target_link_libraries(app_core_tests PRIVATE app_core)
add_test(NAME app_core_tests COMMAND app_core_tests)
```

The core's own modules `use text_format`. An edge or a core test that does
fails to compile with `Cannot open module file 'text_format.mod'`.

gfortran looks for an `include` file in the including file's own folder
first, so a test's `include "../src/internal/text_format.f90"` compiles its
own copy of the module, and gets around all of this. Fail `scripts/check` on
any include path that climbs with `..`. A breach prints the file, the line
and the include:

```sh
if grep -rniE '^[[:space:]]*#?[[:space:]]*include[^[:alnum:]_].*\.\./' \
    core adapters cli; then
  echo 'include files through the build, not a relative path' >&2
  exit 1
fi
```

The build hides modules, not procedures. A procedure outside any module,
which the [module rule](idioms.md#modules) forbids, links from anywhere.
`-Wimplicit-interface` reports a call to one, and CI's `-Werror` fails it,
but an `interface` block that declares the procedure silences the warning,
so review must catch that. When existing code needs an internal module, add
the layer's internal module directory to that one target's include
directories, with a comment naming the breach and how to fix it; the build
can't exempt a single `use`.

Keep a breach of each rule as `scripts/breaches/<rule>.patch`, as the
builder does. For the layers, add a new file to the core that uses an edge's
module, `core/src/breach.f90`, and add it to `app_core`'s sources:

```fortran
module core_breach
    use console, only: show
    implicit none
    private
end module core_breach
```

gfortran quotes a module's name with curly quotes in a UTF-8 locale and
straight ones otherwise, so the patch's second line names just the file:

```text
Rule: the core never uses an edge
Fails with: console.mod
```

For the front door, a new core test that uses `text_format`, added as a test
target, breaks it the same way.

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
- [GNU Fortran: options for directory search](https://gcc.gnu.org/onlinedocs/gfortran/Directory-Options.html)
- [CMake: Fortran_MODULE_DIRECTORY](https://cmake.org/cmake/help/latest/prop_tgt/Fortran_MODULE_DIRECTORY.html)
