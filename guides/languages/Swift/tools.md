# Swift Tools

The free/open source tools that lint, format and check Swift code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [swiftc](https://www.swift.org/) (Swift compiler) | Apache-2.0 with Runtime Library Exception | Linting, Auditing, Code quality | Compiling, and linting through its warnings and concurrency checks; sanitizers and coverage through `swift test` |
| [swift-format](https://github.com/swiftlang/swift-format) | Apache-2.0 with Runtime Library Exception | Formatting | Formatting: owns all of [Layout](coding-style.md#layout), [Braces](coding-style.md#braces) and [Spacing](coding-style.md#spacing) |
| [SwiftLint](https://github.com/realm/SwiftLint) | MIT | Linting, Code quality | Linting for unsafe and error-prone patterns that the formatter doesn't check; finding unused imports and declarations |
| [Periphery](https://github.com/peripheryapp/periphery) | MIT | Code quality | Finding unused code across a whole project |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [swift-mutation-testing](https://github.com/ericodx/swift-mutation-testing) | MIT | Code quality | Mutation testing, on macOS |

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support, including Xcode |
| [.swift-format](.swift-format) | swift-format |
| [.swiftlint.yml](.swiftlint.yml) | SwiftLint |
| [Tests/.swiftlint.yml](Tests/.swiftlint.yml) | SwiftLint, for the test target |
| [.periphery.yml](.periphery.yml) | Periphery |
| [.jscpd.json](.jscpd.json) | jscpd |
| [.opengrep/swift.yaml](.opengrep/swift.yaml) | Opengrep |

## Recommended setup

Format, then check. Code must build with **no warnings** and no findings.

```sh
# Format in place, then lint what the formatter couldn't fix
swift-format format --in-place --recursive Sources Tests
swift-format lint --strict --recursive Sources Tests

# Lint for unsafe and error-prone patterns
swiftlint lint --strict
```

Swift 6 toolchains include swift-format but don't always put
`swift-format` on the `PATH`; run it as `swift format` there, with the same
arguments.

Configure swift-format with `.swift-format` at the repository root:

```json
{
  "version": 1,
  "lineLength": 100,
  "indentation": { "spaces": 2 },
  "lineBreakBeforeEachArgument": true,
  "prioritizeKeepingFunctionOutputTogether": true,
  "respectsExistingLineBreaks": true,
  "rules": {
    "AllPublicDeclarationsHaveDocumentation": true,
    "OrderedImports": true,
    "UseTripleSlashForDocumentationComments": true,
    "ValidateDocumentationComments": true
  }
}
```

`lineBreakBeforeEachArgument` and `prioritizeKeepingFunctionOutputTogether`
give the [wrapping](coding-style.md#wrapping) the style guide asks for: one
argument or parameter per line, with the return type kept next to the
closing parenthesis.

Configure SwiftLint with `.swiftlint.yml`. swift-format owns layout, so the
SwiftLint rules that would disagree with it are turned off:

```yaml
---
disabled_rules:
  - opening_brace
  - trailing_comma
opt_in_rules:
  - empty_count
  - fatal_error_message
  - first_where
  - force_unwrapping
  - implicitly_unwrapped_optional
  - unowned_variable_capture
analyzer_rules:
  - unused_declaration
  - unused_import
line_length: 100
excluded:
  - .build
```

- A `Tests/.swiftlint.yml` turns off `force_unwrapping`, `force_try` and
  `force_cast`, because a crash is an acceptable test failure.
- Treat warnings as errors: pass `-warnings-as-errors` to `swiftc`, or set
  `SWIFT_TREAT_WARNINGS_AS_ERRORS` in Xcode.
- Build in the **Swift 6 language mode**. On Swift 5.9 and 5.10, pass
  `-strict-concurrency=complete` instead, so data-race checks are already
  on before the move to Swift 6.
- Because the formatter owns layout, never hand-format code it will rewrite.
  Run it before every commit.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Run the test suite under AddressSanitizer, and again under ThreadSanitizer.
They catch memory errors in unsafe code and
[data races](idioms.md#concurrency) that the compiler's concurrency checks
can't see, such as those behind `@unchecked Sendable`.

```sh
swift test --sanitize=address
swift test --sanitize=thread
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads Swift Package Manager's `Package.resolved`
(OSV-Scanner 2.4 or later) and checks every pinned version against the OSV
database.

```sh
osv-scanner scan source -r .
```

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
lizard -l swift -C 10 -L 60 -w Sources
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format swift --min-tokens 50 --exit-code 1 Sources
```

### Dead code

Run Periphery to find unused classes, functions, properties and parameters
across the whole project. Unused code still has to be read, compiled and
maintained. Periphery reads its settings from `.periphery.yml`, which makes
any finding fail the scan:

```yaml
---
# Periphery settings: fail the scan when it finds unused code.
strict: true
```

```sh
periphery scan
```

In a library, also set `retain_public: true` in `.periphery.yml`, so
Periphery doesn't report the public API as unused.

SwiftLint's analyzer rules, `unused_declaration` and `unused_import` (in the
`.swiftlint.yml` above), need the compiler's log from a clean build:

```sh
swift package clean
swift build -v > build.log 2>&1
swiftlint analyze --strict --compiler-log-path build.log
```

### Coverage

Run the tests with coverage turned on. Coverage shows which lines the tests
never run. Use it to find untested error paths, and question any change that
lowers it.

```sh
swift test --enable-code-coverage
swift test --show-codecov-path
```

The second command prints the path of the JSON coverage report.

### Mutation testing

swift-mutation-testing makes small changes to the code, such as negating
an `if` condition, and runs the tests against each one. A change the tests
still pass, a surviving mutant, is behaviour no test pins down. Muter, the
older tool, has had no release since 2023, so it doesn't qualify.

It runs only on macOS 15 or later: it doesn't build on Linux. This guide
couldn't run it, because its checks run in Linux containers, so the
command below comes from the tool's documentation for version 1.7.1, the
version to pin. Run it from the package root:

```sh
swift-mutation-testing --min-score 80
```

- It exits non-zero (2) when the mutation score, the share of mutants the
  tests kill, is under 80%. That's the same bar as coverage. Some mutants
  can't be killed, because they don't change what the code does, so 100%
  is rarely reachable; 80% leaves room for them and still fails code whose
  tests check little. Code no test reaches counts against the score.
- It can't limit a run to the files changed since the base branch; the
  narrowest scope it takes is one directory or file. It caches each
  verdict in `.swift-mutation-testing-cache/`, keyed by the contents of the
  source and test files, so keep that directory between runs, and a run
  tests only the mutants whose code or tests changed. Don't commit it.
- An Xcode project needs a `.swift-mutation-testing.yml` with its scheme
  and destination, which `swift-mutation-testing init` writes; a package
  needs none.

The report lists each survivor by file, line and the change it made, such
as `NegateConditional`. Read it as a missing test: the code ran, but no
test checked the result of that condition. Write the test that fails on
the mutant, not one that just runs the line;
`swift-mutation-testing reproduce` with the mutant's id reruns it and
shows the mutated line. If a mutant can't change behaviour, put
`// swift-mutation-testing:disable-next-line` above the line, with the
reason, rather than writing a test that contorts the code.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. Make each layer its own target in `Package.swift`. A
target can import only the targets it depends on, so a core that imports an
edge fails to compile, and SwiftPM rejects any dependency cycle between
targets. The target names are examples: replace them with the layers in the
project's `design.md`.

```swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
  name: "App",
  targets: [
    // The core depends on no other layer.
    .target(name: "Core"),
    // Each edge depends only on the core.
    .target(name: "Adapters", dependencies: ["Core"]),
    // The program wires the layers together, so it depends on them all.
    .executableTarget(name: "App", dependencies: ["Core", "Adapters"]),
  ]
)
```

A breach fails with `no such module`, or with a circular dependency between
modules. Build from clean, as CI does: an incremental build can still find a
module left over from an earlier build.

```sh
swift package clean
swift build
```

## Sources

- [swift-mutation-testing: usage and configuration](https://github.com/ericodx/swift-mutation-testing/blob/v1.7.1/Docs/USAGE.MD)
- [swift-mutation-testing: installation](https://github.com/ericodx/swift-mutation-testing/blob/v1.7.1/Docs/INSTALLATION.MD)
- [Muter releases](https://github.com/muter-mutation-testing/muter/releases)
