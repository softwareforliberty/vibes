# C Tools

The free/open source tools that lint, format and check C code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GCC](https://gcc.gnu.org/) | GPLv3 | Linting, Auditing, Code quality | Compiling C, and linting through its warning flags; static analysis with `-fanalyzer`, sanitizers, and coverage with gcov |
| [Cppcheck](https://cppcheck.sourceforge.io/) | GPL-3.0-or-later | Auditing, Code quality | Finding undefined behaviour, leaks and unused functions |
| [Flawfinder](https://dwheeler.com/flawfinder/) | GPL-2.0-or-later | Auditing | Flagging calls to risky C library functions |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [gcovr](https://gcovr.com/) | BSD-3-Clause | Code quality | Summarising gcov coverage |

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support; CLion; Visual Studio and VS Code (C/C++ extension) |
| [.jscpd.json](.jscpd.json) | jscpd |
| [.opengrep/c.yaml](.opengrep/c.yaml) | Opengrep |
| [gcovr.cfg](gcovr.cfg) | gcovr |

## Compiler warnings

Compiler warnings are the lint gate. Code must build with **no warnings**
using at least these flags:

```sh
gcc -std=c99 -Wall -Wextra -Wvla
```

- `-Wextra` turns on `-Wimplicit-fallthrough`, which enforces the
  [`fallthrough` rule](coding-style.md#switch).
- `-Wvla` enforces the [no variable-length arrays](coding-style.md#language-usage) rule.

## Auditing

### Security analysis

Build with GCC's static analyzer in a separate CI job. It follows paths
within and between functions, and reports leaks, double frees, use after free
and NULL dereferences. It's slower than a normal build, so it doesn't run on
every local compile.

```sh
gcc -std=c99 -Wall -Wextra -Wvla -fanalyzer -c file.c
```

Run Cppcheck over the whole source tree. It finds undefined behaviour,
out-of-bounds access and leaks that the compiler doesn't warn about.

```sh
cppcheck --std=c99 --enable=warning,portability --inline-suppr \
    --error-exitcode=1 -I include src
```

Run Flawfinder to flag calls to C library functions with a history of misuse,
such as `strcpy()` and `sprintf()` (see the
[buffer and string rules](idioms.md#buffers-and-strings)). Review every hit at
level 3 or above.

```sh
flawfinder --minlevel=3 --error-level=3 src
```

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Run the test suite under AddressSanitizer and UndefinedBehaviorSanitizer. They
catch out-of-bounds access, use after free and
[undefined behaviour](idioms.md#undefined-behaviour) at the moment it happens,
on paths static analysis can miss.

```sh
gcc -std=c99 -g -fsanitize=address,undefined -fno-sanitize-recover=all \
    -fno-omit-frame-pointer -o tests tests.c
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
jscpd --format c --formats-exts "c:h" --min-tokens 50 --exit-code 1 src
```

jscpd's `c` format reads only `.c` files. `--formats-exts` adds `.h`
headers to it, so they're checked against each other and the `.c` files.

### Dead code

`-Wall` turns on `-Wunused-function`, `-Wunused-variable` and
`-Wunused-but-set-variable`, and `-Wextra` adds `-Wunused-parameter`. They
find unused code within one file.

Cppcheck's `unusedFunction` check finds non-static functions that nothing
calls. It needs the whole program in a single run:

```sh
cppcheck --std=c99 --enable=unusedFunction --error-exitcode=1 -I include src
```

### Coverage

Build the tests with `--coverage`, run them, then summarise the result with
gcovr. Coverage shows which lines the tests never run. Use it to find
untested error paths, and question any change that lowers it. Run gcovr from
the repository root, where it reads [gcovr.cfg](gcovr.cfg).

```sh
gcc -std=c99 --coverage -o tests tests.c
./tests
gcovr
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

Each layer's `CMakeLists.txt` declares its target, its headers and the
layers it may use. The target names are examples: replace them with the
layers in the project's `design.md`. `adapters/CMakeLists.txt`:

```cmake
add_library(app_adapters STATIC src/console.c)
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
