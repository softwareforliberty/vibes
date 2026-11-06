# Objective-C++ Tools

The free/open source tools that lint, format and check Objective-C++ code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting | Linting modernisation and bug-prone patterns |
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
| [.opengrep/cpp.yaml](.opengrep/cpp.yaml) | Opengrep (pure C++ files) |

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
jscpd --format cpp,objectivec --min-tokens 50 --exitCode 1 src
```

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
