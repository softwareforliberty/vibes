# Objective-C Tools

The free/open source tools that lint, format and check Objective-C code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting | Linting naming and bug-prone patterns |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Finding leaks, nil misuse and API misuse along every code path |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Linting, Auditing, Code quality | Compiling, and linting through its warning flags; sanitizers, and coverage with llvm-cov |
| [Infer](https://fbinfer.com/) | MIT | Auditing | Inter-procedural analysis for nil dereferences, leaks and retain cycles |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Formatting

Commit this `.clang-format` at the repository root, and run clang-format on
every changed file before committing. A formatter ends layout debates and
keeps diffs free of whitespace noise.

```yaml
---
Language: ObjC
BasedOnStyle: Google
ColumnLimit: 100
DerivePointerAlignment: false
PointerAlignment: Right
```

## Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
Checks: >
  bugprone-*,
  clang-analyzer-*,
  google-objc-*,
  objc-*,
  readability-braces-around-statements,
  -bugprone-easily-swappable-parameters
WarningsAsErrors: '*'
```

- Suppress a warning only on the line that needs it, with
  `// NOLINT(check-name)` and a reason. A bare `NOLINT` hides every check,
  including ones nobody meant to silence.
- Run the static analyzer over the whole build with `scan-build`, for example
  `scan-build --status-bugs make`. It follows paths across functions, and finds bugs that
  per-file checks miss.

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
many methods.

```sh
infer run --fail-on-issue -- make
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
jscpd --format objectivec --min-tokens 50 --exitCode 1 src
```

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
