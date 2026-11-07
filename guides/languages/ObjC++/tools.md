# Objective-C++ Tools

The free/open source tools that lint, format and check Objective-C++ code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting | Linting modernisation and bug-prone patterns |
| [Bear](https://github.com/rizsotto/Bear) | GPL-3.0-or-later | Linting | Recording a Make build's compile commands for clang-tidy |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Finding leaks, nil misuse and API misuse along every code path |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Compiling, and linting through its warning flags; sanitizers, and coverage with llvm-cov |
| [Cppcheck](https://cppcheck.sourceforge.io/) | GPL-3.0-or-later | Auditing, Code quality | Finding undefined behaviour, leaks and unused functions in pure C++ files |
| [Flawfinder](https://dwheeler.com/flawfinder/) | GPL-2.0-or-later | Auditing | Flagging calls to risky C library functions in pure C++ files |
| [Infer](https://fbinfer.com/) | MIT | Auditing | Inter-procedural analysis for null dereferences, leaks and retain cycles |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules, in pure C++ files |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Mull](https://mull-project.com/) | Apache-2.0 | Code quality | Mutation testing of the C++ code |

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support, including Xcode; CLion; Visual Studio and VS Code (C/C++ extension) |
| [.clang-format](.clang-format) | clang-format, and CLion and Visual Studio when set to use it |
| [.clang-tidy](.clang-tidy) | clang-tidy |
| [.inferconfig](.inferconfig) | Infer |
| [.jscpd.json](.jscpd.json) | jscpd |
| [.opengrep/objcpp.yaml](.opengrep/objcpp.yaml) | Opengrep (pure C++ files) |
| [mull.yml](mull.yml) | Mull |

## Formatting

Commit this `.clang-format` at the repository root, and run clang-format on
every changed file before committing. A formatter ends layout debates and
keeps diffs free of whitespace noise.

```yaml
---
Language: Cpp
BasedOnStyle: Google
DerivePointerAlignment: false
IncludeBlocks: Preserve
PointerAlignment: Right
---
Language: ObjC
BasedOnStyle: Google
ColumnLimit: 100
DerivePointerAlignment: false
PointerAlignment: Right
```

clang-format formats `.mm` files and Objective-C headers with the `ObjC`
section, and pure C++ files with the `Cpp` section. `IncludeBlocks: Preserve`
keeps the include groups as written, as Google's Objective-C style already
does. clang-format can't tell other libraries' headers from this project's,
so it would otherwise merge those two
[include groups](coding-style.md#include-order).

Check every file in CI. `--dry-run --Werror` prints each change clang-format
would make, and exits non-zero if there is one:

```sh
clang-format --dry-run --Werror $(git ls-files '*.cc' '*.h' '*.m' '*.mm')
```

To format the files in place, run it with `-i`:

```sh
clang-format -i $(git ls-files '*.cc' '*.h' '*.m' '*.mm')
```

## Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
---
Checks: >
  bugprone-*,
  clang-analyzer-*,
  cppcoreguidelines-*,
  google-*,
  misc-*,
  modernize-*,
  objc-*,
  performance-*,
  readability-*,
  -bugprone-easily-swappable-parameters,
  -cppcoreguidelines-use-enum-class,
  -google-readability-todo,
  -misc-const-correctness,
  -modernize-use-trailing-return-type,
  -modernize-use-using,
  -performance-enum-size,
  -readability-identifier-length,
  -readability-identifier-naming,
  -readability-redundant-parentheses
WarningsAsErrors: "*"
CheckOptions:
  readability-implicit-bool-conversion.AllowPointerConditions: true
```

- Identifier naming is checked by review, not clang-tidy. One file holds two
  naming schemes, and the check can't tell which applies where.
- Five more checks are off because they reject Objective-C idioms the style
  guide requires. `cppcoreguidelines-use-enum-class`, `modernize-use-using`
  and `performance-enum-size` reject `typedef NS_ENUM` and block `typedef`s.
  `readability-redundant-parentheses` rejects `__typeof__(self)` in the
  weak-self pattern, and `misc-const-correctness` asks for `NSString *const`
  on every Objective-C local. Reviewers check the `enum class` rule in C++
  code.
- Suppress a warning only on the line that needs it, with
  `// NOLINT(check-name)` and a reason. A bare `NOLINT` hides every check,
  including ones nobody meant to silence.
- Run the static analyzer over the whole build with `scan-build`, for example
  `scan-build --status-bugs make`. It follows paths across functions, and
  finds bugs that per-file checks miss.

clang-tidy reads each file's compile flags from a compilation database,
`compile_commands.json`. CMake writes one into the build directory when
`CMAKE_EXPORT_COMPILE_COMMANDS` is on. Then run clang-tidy on every source
file. `WarningsAsErrors` makes it exit non-zero on any warning:

```sh
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
clang-tidy -p build $(git ls-files '*.cc' '*.m' '*.mm')
```

For a Make build, [Bear](https://github.com/rizsotto/Bear) writes the
database while it runs the build:

```sh
mkdir -p build
bear --output build/compile_commands.json -- make
```

## Compiler warnings

Code must build with **no warnings** using at least these flags:

```sh
clang++ -std=c++20 -fobjc-arc -Wall -Wextra -Wconversion -Wshadow \
    -Wnon-virtual-dtor -Woverloaded-virtual -Wdocumentation \
    -Wimplicit-retain-self -Wnullable-to-nonnull-conversion
```

- `-Wold-style-cast` is left out, because ARC bridging casts
  (`(__bridge T)`) must use C-style cast syntax. In C++ code, reviewers check
  the no C-style casts rule (see [Language usage](coding-style.md#language-usage)).

## Auditing

### Security analysis

The Clang Static Analyzer is the main security check (see
[Linting](#linting)). It fails the build on any finding when run with
`--status-bugs`:

```sh
scan-build --status-bugs make
```

Infer adds deeper inter-procedural analysis for null dereferences, resource
leaks and retain cycles. Run it in CI on large code bases, where bugs cross
many functions and methods. It reads this `.inferconfig` from the repository
root, which makes it fail on any issue it finds:

```json
{
  "fail-on-issue": true
}
```

```sh
infer run -- make
```

Opengrep, Cppcheck and Flawfinder don't read Objective-C++, so run them on
the pure C++ files only, with the same settings as the
[C++ tools](../C++/tools.md#security-analysis):

```sh
cppcheck --std=c++20 --enable=warning,portability --inline-suppr \
    --error-exitcode=1 -I include src/cpp
flawfinder --minlevel=3 --error-level=3 src/cpp
```

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Run the test suite under AddressSanitizer and UndefinedBehaviorSanitizer, and
the concurrent tests under ThreadSanitizer in a separate build. They catch
out-of-bounds access, use after free, undefined behaviour and data races at
the moment they happen, on paths static analysis can miss.

```sh
clang++ -std=c++20 -fobjc-arc -g -fsanitize=address,undefined \
    -fno-sanitize-recover=all -fno-omit-frame-pointer \
    -framework Foundation -o tests tests.mm
clang++ -std=c++20 -fobjc-arc -g -fsanitize=thread \
    -framework Foundation -o tests-tsan tests.mm
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads Swift Package Manager's `Package.resolved`
(OSV-Scanner 2.4 or later) and Conan's `conan.lock`, and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

OSV-Scanner doesn't read vcpkg manifests, and doesn't document support for
CocoaPods' `Podfile.lock`. No other maintained FOSS tool audits them, or
vendored sources. Record the version of every such dependency, and follow its
security advisories.

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
lizard -l cpp -l objectivec -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format cpp,objectivec --formats-exts "cpp:h,hh,hpp" \
    --min-tokens 50 --exit-code 1 src
```

jscpd reads `.mm` and `.m` files as `objectivec`, and `.cc` files as `cpp`,
but no headers. `--formats-exts` reads `.h`, `.hh` and `.hpp` headers as
`cpp`, so they're checked against each other and the C++ files. jscpd
compares files only within one format, so a header isn't compared with `.mm`
files.

### Dead code

`-Wall` and `-Wextra` turn on Clang's `-Wunused-*` warnings for unused
variables, parameters, functions and private fields, and the static analyzer
reports dead stores. They find unused code within one file.

Cppcheck's `unusedFunction` check finds C++ functions that nothing calls. Run
it over the pure C++ files in a single run:

```sh
cppcheck --std=c++20 --enable=unusedFunction --error-exitcode=1 \
    -I include src/cpp
```

No maintained FOSS tool finds unused Objective-C methods across a whole
program. A method can be called by name at run time, so no tool can prove it
unused. Review public headers for methods nothing calls.

### Coverage

Build the tests with Clang's source-based coverage, run them, then report with
llvm-cov. Coverage shows which lines the tests never run. Use it to find
untested error paths, and question any change that lowers it.

```sh
clang++ -std=c++20 -fobjc-arc -fprofile-instr-generate -fcoverage-mapping \
    -framework Foundation -o tests tests.mm
LLVM_PROFILE_FILE=tests.profraw ./tests
llvm-profdata merge -sparse tests.profraw -o tests.profdata
llvm-cov report ./tests -instr-profile=tests.profdata
```

### Mutation testing

Mull makes small changes to the code, such as turning `>` into `>=`, and
runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. Mull mutates the C++
functions in `.mm` files, but not Objective-C methods: checked with Mull
0.37.0, a method in the change gets no mutants. For the methods, rely on
the test reviewer and on [coverage](#coverage).

A full run is slow, so [mull.yml](mull.yml) limits it to the lines changed
since the base branch. Set `gitDiffRef` there to the project's base
branch. Mull runs `git diff origin/main` as it compiles, which also counts
changes made on the base branch since the branch began, so fetch and
rebase first.

Mull is a Clang plugin: install the plugin for the Clang you build with,
such as `mull-19` for `clang++-19`. Compile every file with the plugin,
the tests too, so that templates and inline functions in headers are
mutated where the tests instantiate them; `mull.yml` keeps the tests
themselves from being mutated. Compile one file per command, because
`-grecord-command-line` breaks when one command compiles several. Then
`mull-runner` runs the tests against every mutant. On Linux, with the GNU
Objective-C runtime:

```sh
mkdir -p build-mull
for f in src/*.mm tests.mm; do
    clang++-19 -std=c++20 -fobjc-runtime=gcc -g -grecord-command-line \
        -fpass-plugin=/usr/lib/mull-ir-frontend-19 \
        -c "$f" -o "build-mull/$(basename "$f").o"
done
clang++-19 -o build-mull/tests build-mull/*.o -lobjc
mull-runner --mutation-score-threshold 80 build-mull/tests
```

- `mull-runner` exits non-zero when the mutation score, the share of
  mutants the tests kill, is under 80%. That's the same bar as coverage.
  Some mutants can't be killed, because they don't change what the code
  does, so Mull's default of 100% is rarely reachable; 80% leaves room for
  them and still fails a change whose tests check little.
- With no changed lines there are no mutants, and `mull-runner` exits
  zero.
- On macOS, install Mull with Homebrew (`mull-project/mull/mull@19`) and
  build with that LLVM's `clang++`, using the project's `-fobjc-arc` and
  `-framework Foundation` in place of `-fobjc-runtime=gcc` and `-lobjc`.
  Apple's Clang can't load the plugin. This guide checked the Linux build
  only.
- This guide was checked with Mull 0.37.0, which has plugins for LLVM 16
  to 23.

Mull prints each survivor as a compiler warning at the code it changed:

```text
[info] Survived mutants (1/2):
src/pricing.mm:15:16: warning: Survived: Replaced > with >= [cxx_gt_to_ge]
    if (weight > 5) {
               ^
[info] Mutation score: 50%
```

Read it as a missing test: here, no test passes a weight of exactly 5, so
the boundary isn't pinned down. Write the test that fails on the mutant,
not one that just runs the line. If a mutant can't change behaviour, put
`// mull-ignore-next: cxx_gt_to_ge` above the line, with the reason,
rather than writing a test that contorts the code.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. With [CMake](../../build/CMake/idioms.md), make each layer its
own library target with its own include directory. A source file finds only
the headers of its own target and of the targets it links, so a core file
that includes an edge's header fails to compile. Never include another
layer's header by a relative path, or add include directories with the
directory-wide `include_directories()`: both get around the check.

`project()` must enable the `OBJCXX` language, for example
`project(app LANGUAGES CXX OBJCXX)`.

Each layer's `CMakeLists.txt` declares its target, its headers and the
layers it may use. The target names are examples: replace them with the
layers in the project's `design.md`. `adapters/CMakeLists.txt`:

```cmake
add_library(app_adapters STATIC src/console.mm)
target_include_directories(
    app_adapters
    PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
target_link_libraries(app_adapters PUBLIC app_core)
```

The core's target links no other layer. CMake allows a cycle between static
libraries, so a core that links an edge would still build. Check for it at
the end of the top-level `CMakeLists.txt`, after the `add_subdirectory()`
calls:

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

A breach fails the build. The check names the edge the core links, and the
compiler names the header it can't find:

```sh
cmake -S . -B build
cmake --build build
```

## Sources

- [Mull setup and configuration](https://mull-project.com/getting-started/setup/)
- [Mull: diff-based mutations](https://mull-project.com/guides/diff-based-mutations/)
- [Mull: disable mutants with annotations](https://mull-project.com/guides/annotations/)
- [mull-runner reference](https://mull-project.com/reference/mull-runner/)
