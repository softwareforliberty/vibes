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

## Config files

Copy these files to the same paths in the repository. Every config shown
below is the full contents of one of these files.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor with EditorConfig support, including Xcode |
| [.swift-format](.swift-format) | swift-format |
| [.swiftlint.yml](.swiftlint.yml) | SwiftLint |
| [Tests/.swiftlint.yml](Tests/.swiftlint.yml) | SwiftLint, for the test target |
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

Configure swift-format with `.swift-format` at the repository root:

```json
{
  "version": 1,
  "lineLength": 100,
  "indentation": { "spaces": 2 },
  "respectsExistingLineBreaks": true,
  "rules": {
    "AllPublicDeclarationsHaveDocumentation": true,
    "OrderedImports": true,
    "UseTripleSlashForDocumentationComments": true,
    "ValidateDocumentationComments": true
  }
}
```

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
jscpd --format swift --min-tokens 50 --exitCode 1 Sources
```

### Dead code

Run Periphery to find unused classes, functions, properties and parameters
across the whole project. Unused code still has to be read, compiled and
maintained.

```sh
periphery scan --strict
```

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
