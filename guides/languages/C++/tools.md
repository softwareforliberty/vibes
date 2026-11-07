# C++ Tools

The free/open source tools that lint, format and check C++ code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting | Linting naming, modernisation and bug-prone patterns |
| [Bear](https://github.com/rizsotto/Bear) | GPL-3.0-or-later | Linting | Recording a Make build's compile commands for clang-tidy |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Compiling, and linting through its warning flags; sanitizers, and coverage with llvm-cov |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Auditing | Finding leaks, null dereferences and API misuse along every code path |
| [Cppcheck](https://cppcheck.sourceforge.io/) | GPL-3.0-or-later | Auditing, Code quality | Finding undefined behaviour, leaks and unused functions |
| [Flawfinder](https://dwheeler.com/flawfinder/) | GPL-2.0-or-later | Auditing | Flagging calls to risky C library functions |
| [Infer](https://fbinfer.com/) | MIT | Auditing | Inter-procedural analysis for null dereferences, leaks and data races |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support; CLion; Visual Studio and VS Code (C/C++ extension) |
| [.clang-format](.clang-format) | clang-format, and CLion and Visual Studio when set to use it |
| [.clang-tidy](.clang-tidy) | clang-tidy |
| [.inferconfig](.inferconfig) | Infer |
| [.jscpd.json](.jscpd.json) | jscpd |
| [.opengrep/cpp.yaml](.opengrep/cpp.yaml) | Opengrep |

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
```

`IncludeBlocks: Preserve` sorts includes within each group and keeps the
groups as written. clang-format can't tell other libraries' headers from this
project's, so it would merge those two
[include groups](coding-style.md#include-order).

Check every file in CI. `--dry-run --Werror` prints each change clang-format
would make, and exits non-zero if there is one:

```sh
clang-format --dry-run --Werror $(git ls-files '*.cc' '*.h')
```

To format the files in place, run it with `-i`:

```sh
clang-format -i $(git ls-files '*.cc' '*.h')
```

## Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
---
Checks: >
  bugprone-*,
  cppcoreguidelines-*,
  google-*,
  misc-*,
  modernize-*,
  performance-*,
  readability-*,
  -bugprone-easily-swappable-parameters,
  -google-readability-todo,
  -modernize-use-trailing-return-type,
  -performance-enum-size,
  -readability-identifier-length
WarningsAsErrors: "*"
CheckOptions:
  readability-identifier-naming.ClassCase: CamelCase
  readability-identifier-naming.StructCase: CamelCase
  readability-identifier-naming.EnumCase: CamelCase
  readability-identifier-naming.FunctionCase: CamelCase
  readability-identifier-naming.MethodCase: CamelCase
  readability-identifier-naming.VariableCase: lower_case
  readability-identifier-naming.ParameterCase: lower_case
  readability-identifier-naming.PrivateMemberSuffix: _
  readability-identifier-naming.ProtectedMemberSuffix: _
  readability-identifier-naming.NamespaceCase: lower_case
  readability-identifier-naming.ConstexprVariableCase: CamelCase
  readability-identifier-naming.ConstexprVariablePrefix: k
  readability-identifier-naming.GlobalConstantCase: CamelCase
  readability-identifier-naming.GlobalConstantPrefix: k
  readability-identifier-naming.StaticConstantCase: CamelCase
  readability-identifier-naming.StaticConstantPrefix: k
  readability-identifier-naming.EnumConstantCase: CamelCase
  readability-identifier-naming.EnumConstantPrefix: k
  readability-identifier-naming.MacroDefinitionCase: UPPER_CASE
  readability-identifier-naming.MacroDefinitionIgnoredRegexp: ^[A-Z0-9_]+_$
  readability-implicit-bool-conversion.AllowPointerConditions: true
```

- The disabled checks conflict with rules in this guide: TODO format,
  ordinary return types, short local names and `int` as the default integer.
  `MacroDefinitionIgnoredRegexp` lets include guards end in `_`.
  `AllowPointerConditions` permits the
  [`if (ptr)`](coding-style.md#statements-and-expressions) form.
- Suppress a warning only on the line that needs it, with
  `// NOLINT(check-name)` and a reason. A bare `NOLINT` hides every check,
  including ones nobody meant to silence.

clang-tidy reads each file's compile flags from a compilation database,
`compile_commands.json`. CMake writes one into the build directory when
`CMAKE_EXPORT_COMPILE_COMMANDS` is on. Then run clang-tidy on every source
file. `WarningsAsErrors` makes it exit non-zero on any warning:

```sh
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
clang-tidy -p build $(git ls-files '*.cc')
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
clang++ -std=c++20 -Wall -Wextra -Wpedantic -Wconversion -Wshadow \
    -Wold-style-cast -Wnon-virtual-dtor -Woverloaded-virtual -Wdocumentation
```

- `-Wold-style-cast` enforces the [no C-style casts](coding-style.md#casts) rule.
- `-Wdocumentation` checks [API comments](coding-style.md#api-documentation) against the
  declarations they describe.

## Auditing

### Security analysis

Run the Clang Static Analyzer over the whole build with `scan-build`. It
follows paths across functions, and finds leaks, null dereferences and
use-after-move bugs that per-file checks miss.

```sh
scan-build --status-bugs make
```

Run Cppcheck over the whole source tree. It finds undefined behaviour,
out-of-bounds access and leaks that the compiler doesn't warn about.

```sh
cppcheck --std=c++20 --enable=warning,portability --inline-suppr \
    --error-exitcode=1 -I include src
```

Run Flawfinder to flag calls to C library functions with a history of misuse,
such as `strcpy()` and `sprintf()`. Review every hit at level 3 or above.

```sh
flawfinder --minlevel=3 --error-level=3 src
```

Infer adds deeper inter-procedural analysis for null dereferences, resource
leaks and data races. Run it in CI on large code bases, where bugs cross many
functions. It reads this `.inferconfig` from the repository root, which makes
it fail on any issue it finds:

```json
{
  "fail-on-issue": true
}
```

```sh
infer run -- make
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
out-of-bounds access, use after free,
[undefined behaviour](idioms.md#integers-and-undefined-behaviour) and data
races at the moment they happen, on paths static analysis can miss.

```sh
clang++ -std=c++20 -g -fsanitize=address,undefined -fno-sanitize-recover=all \
    -fno-omit-frame-pointer -o tests tests.cpp
clang++ -std=c++20 -g -fsanitize=thread -o tests-tsan tests.cpp
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads Conan's `conan.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

OSV-Scanner doesn't read vcpkg manifests, and no maintained FOSS tool maps
vendored sources to known vulnerabilities. Record the version of every
vendored library, and follow its security advisories.

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
lizard -l cpp -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format cpp --formats-exts "cpp:h,hh,hpp" --min-tokens 50 \
    --exit-code 1 src
```

jscpd's `cpp` format reads `.cc`, `.cpp` and `.cxx` files, but no headers.
`--formats-exts` adds `.h`, `.hh` and `.hpp`, so headers are checked
against each other and the source files.

### Dead code

`-Wall` and `-Wextra` turn on Clang's `-Wunused-*` warnings for unused
variables, parameters, functions and private fields. Add
`-Wunused-member-function` and `-Wunused-template`, which `-Wall` leaves out.
They find unused code within one file.

Cppcheck's `unusedFunction` check finds functions that nothing calls across
the whole program. It needs every source file in a single run:

```sh
cppcheck --std=c++20 --enable=unusedFunction --error-exitcode=1 \
    -I include src
```

### Coverage

Build the tests with Clang's source-based coverage, run them, then report with
llvm-cov. Coverage shows which lines the tests never run. Use it to find
untested error paths, and question any change that lowers it.

```sh
clang++ -std=c++20 -fprofile-instr-generate -fcoverage-mapping \
    -o tests tests.cpp
LLVM_PROFILE_FILE=tests.profraw ./tests
llvm-profdata merge -sparse tests.profraw -o tests.profdata
llvm-cov report ./tests -instr-profile=tests.profdata
```

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. With [CMake](../../build/CMake/idioms.md), make each layer its
own library target with its own include directory. A source file finds only
the headers of its own target and of the targets it links, so a core file
that includes an edge's header fails to compile. Never include another
layer's header by a relative path, or add include directories with the
directory-wide `include_directories()`: both get around the check.

Each layer's `CMakeLists.txt` declares its target, its headers and the
layers it may use. The target names are examples: replace them with the
layers in the project's `design.md`. `adapters/CMakeLists.txt`:

```cmake
add_library(app_adapters STATIC src/console.cc)
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
