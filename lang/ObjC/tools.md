# Objective-C Tools

The free/open source tools that lint, format and check Objective-C code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting | Linting naming and bug-prone patterns |
| [Bear](https://github.com/rizsotto/Bear) | GPL-3.0-or-later | Linting | Recording a Make build's compile commands for clang-tidy |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Finding leaks, nil misuse and API misuse along every code path |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Compiling, and linting through its warning flags; sanitizers, and coverage with llvm-cov |
| [Infer](https://fbinfer.com/) | MIT | Auditing | Inter-procedural analysis for nil dereferences, leaks and retain cycles |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support, including Xcode; CLion |
| [.clang-format](.clang-format) | clang-format, and CLion when set to use it |
| [.clang-tidy](.clang-tidy) | clang-tidy |
| [.inferconfig](.inferconfig) | Infer |
| [.jscpd.json](.jscpd.json) | jscpd |

## Formatting

Commit this `.clang-format` at the repository root, and run clang-format on
every changed file before committing. A formatter ends layout debates and
keeps diffs free of whitespace noise.

```yaml
---
Language: Cpp
BasedOnStyle: Google
ColumnLimit: 100
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

clang-format formats `.m` files and Objective-C headers with the `ObjC`
section, and plain C headers with the `Cpp` section. Without a `Cpp`
section, it refuses to format a header that holds only C.
`IncludeBlocks: Preserve` keeps the import groups as written, as Google's
Objective-C style already does.

Check every file in CI. `--dry-run --Werror` prints each change clang-format
would make, and exits non-zero if there is one:

```sh
clang-format --dry-run --Werror $(git ls-files '*.h' '*.m')
```

To format the files in place, run it with `-i`:

```sh
clang-format -i $(git ls-files '*.h' '*.m')
```

## Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
---
Checks: >
  bugprone-*,
  clang-analyzer-*,
  google-objc-*,
  objc-*,
  readability-braces-around-statements,
  -bugprone-easily-swappable-parameters
WarningsAsErrors: "*"
```

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
clang-tidy -p build $(git ls-files '*.m')
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
clang -fobjc-arc -Wall -Wextra -Wdocumentation -Wimplicit-retain-self \
    -Wnullable-to-nonnull-conversion
```

- `-fobjc-arc` turns on Automatic Reference Counting. All code uses ARC.
- `-Wimplicit-retain-self` flags blocks that capture `self` through an
  instance variable without saying so (see [idioms.md](idioms.md#blocks)).
- `-Wnullable-to-nonnull-conversion` enforces the
  [nullability annotations](coding-style.md#nullability).
- `-Wdocumentation` checks [API comments](coding-style.md#api-documentation) against the
  declarations they describe.

## Auditing

### Security analysis

The Clang Static Analyzer is the main security check (see
[Linting](#linting)). It fails the build on any finding when run with
`--status-bugs`:

```sh
scan-build --status-bugs make
```

Infer adds deeper inter-procedural analysis for nil dereferences, resource
leaks and retain cycles. Run it in CI on large code bases, where bugs cross
many methods. It reads this `.inferconfig` from the repository root, which
makes it fail on any issue it finds:

```json
{
  "fail-on-issue": true
}
```

```sh
infer run -- make
```

Opengrep doesn't support Objective-C, so the Clang Static Analyzer and Infer
are the security analysis for Objective-C code.

Run the test suite under AddressSanitizer and UndefinedBehaviorSanitizer, and
the concurrent tests under ThreadSanitizer in a separate build. They catch
out-of-bounds access, use after free, undefined behaviour and data races at
the moment they happen, on paths static analysis can miss.

```sh
clang -fobjc-arc -g -fsanitize=address,undefined -fno-sanitize-recover=all \
    -fno-omit-frame-pointer -framework Foundation -o tests tests.m
clang -fobjc-arc -g -fsanitize=thread -framework Foundation \
    -o tests-tsan tests.m
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads Swift Package Manager's `Package.resolved`
(OSV-Scanner 2.4 or later) and checks every pinned version against the OSV
database.

```sh
osv-scanner scan source -r .
```

OSV-Scanner doesn't document support for CocoaPods' `Podfile.lock`, and no
other maintained FOSS tool audits it. Prefer Swift Package Manager for new
dependencies. For each pod you keep, record its version and follow its
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
lizard -l objectivec -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format objectivec --formats-exts "objectivec:h" --min-tokens 50 \
    --exit-code 1 src
```

jscpd's `objectivec` format reads only `.m` and `.mm` files.
`--formats-exts` adds `.h` headers to it, so they're checked against each
other and the `.m` files.

### Dead code

`-Wall` and `-Wextra` turn on Clang's `-Wunused-*` warnings for unused
variables, parameters and functions, and the static analyzer reports dead
stores. They find unused code within one file.

No maintained FOSS tool finds unused Objective-C methods across a whole
program. A method can be called by name at run time, so no tool can prove it
unused. Review public headers for methods nothing calls.

### Coverage

Build the tests with Clang's source-based coverage, run them, then report with
llvm-cov. Coverage shows which lines the tests never run. Use it to find
untested error paths, and question any change that lowers it.

```sh
clang -fobjc-arc -fprofile-instr-generate -fcoverage-mapping \
    -framework Foundation -o tests tests.m
LLVM_PROFILE_FILE=tests.profraw ./tests
llvm-profdata merge -sparse tests.profraw -o tests.profdata
llvm-cov report ./tests -instr-profile=tests.profdata
```

### Architecture

The build enforces the layers, as the
[architecture guide](../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. With [CMake](../CMake/idioms.md), make each layer its
own library target with its own include directory. A source file finds only
the headers of its own target and of the targets it links, so a core file
that includes an edge's header fails to compile. Never include another
layer's header by a relative path, or add include directories with the
directory-wide `include_directories()`: both get around the check.

`project()` must enable the `OBJC` language, for example
`project(app LANGUAGES C OBJC)`.

Each layer's `CMakeLists.txt` declares its target, its headers and the
layers it may use. The target names are examples: replace them with the
layers in the project's `design.md`. `adapters/CMakeLists.txt`:

```cmake
add_library(app_adapters STATIC src/console.m)
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
