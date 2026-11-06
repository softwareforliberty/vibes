# Dart Tools

The free/open source tools that lint, format and check Dart code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Dart SDK](https://dart.dev/tools) (`dart format`, `dart analyze`, `dart pub`) | BSD-3-Clause | Formatting, Linting, Auditing | Formatting, static analysis, and dependency advisories |
| [lints](https://pub.dev/packages/lints) | BSD-3-Clause | Linting | The Dart team's recommended lint rule set |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [dart_code_linter](https://pub.dev/packages/dart_code_linter) | MIT | Code quality | Measuring function complexity, length and nesting |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [coverage](https://pub.dev/packages/coverage) | BSD-3-Clause | Code quality | Measuring test coverage |

## Config files

Copy these files into the project root. Each one matches the settings this
guide describes.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, including IntelliJ IDEA and Android Studio |
| [`analysis_options.yaml`](analysis_options.yaml) | `dart analyze` and dart_code_linter |
| [`.opengrep/dart.yaml`](.opengrep/dart.yaml) | Opengrep: starter rules for the [security idioms](idioms.md#security) |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Configuration

Code must pass both checks with **no errors, warnings or lints**:

```sh
dart format --output=none --set-exit-if-changed .
dart analyze --fatal-infos
```

`--fatal-infos` fails the build on lint findings too, which the analyzer
otherwise reports only as information.

`analysis_options.yaml`:

```yaml
---
include: package:lints/recommended.yaml

analyzer:
  language:
    strict-casts: true
    strict-inference: true
    strict-raw-types: true

linter:
  rules:
    - always_declare_return_types
    - avoid_dynamic_calls
    - directives_ordering
    - only_throw_errors
    - prefer_final_locals
    - prefer_relative_imports
    - prefer_single_quotes
    - public_member_api_docs
    - type_annotate_public_apis
    - unawaited_futures
    - unreachable_from_main

dart_code_linter:
  metrics:
    cyclomatic-complexity: 10
    source-lines-of-code: 60
    maximum-nesting-level: 3
```

- The three `strict-` modes stop implicit casts from `dynamic`, inference
  that falls back to `dynamic`, and generic types used without type
  arguments.
- The extra lint rules enforce the [style guide](coding-style.md): sorted
  imports, single quotes, annotated and documented public APIs, and `final`
  locals. `unawaited_futures` enforces the
  [async rules](idioms.md#async-code).
- The `dart_code_linter` block sets the limits that
  [Complexity](#complexity) checks.
- `dart format` owns layout, and the analyzer checks only for bugs and
  conventions, so the two never conflict. Run `dart fix --apply` to apply
  the analyzer's automatic fixes.

## Auditing

### Security analysis

Opengrep's Dart support is experimental, so treat its findings as a review
list and check the results by hand when you upgrade it.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Write rules for the patterns the [security idioms](idioms.md#security)
forbid, such as `Process.run()` with `runInShell: true` and SQL built by
string interpolation.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `pubspec.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

`dart pub get` also prints a warning for any resolved package with a
security advisory in the GitHub Advisory Database. Don't add an advisory to
`ignored_advisories` in `pubspec.yaml` without a comment saying why it
doesn't apply.

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

lizard doesn't support Dart, so use dart_code_linter, an open-source fork of
Dart Code Metrics. Fail the build on any function with a cyclomatic
complexity over 10 or more than 60 lines of code. A function past either
limit is hard to test and should be split.

The limits are in the `dart_code_linter` block of `analysis_options.yaml`
(see [Configuration](#configuration)). The command only reports a function
past a limit, so `--set-exit-on-violation-level=warning` makes it fail the
build:

```sh
dart run dart_code_linter:metrics analyze lib \
    --set-exit-on-violation-level=warning
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format dart --min-tokens 50 --exitCode 1 lib
```

### Dead code

The analyzer reports unused imports, private declarations, fields and local
variables, and code that can never run, as warnings that
`dart analyze --fatal-infos` already fails on. For applications, the
`unreachable_from_main` lint in the [configuration](#configuration) also
reports public declarations that nothing reachable from `main()` uses.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

The `coverage` package runs the tests and writes an LCOV report to
`coverage/lcov.info`. `--branch-coverage` collects branch data for the
report as well:

```sh
dart run coverage:test_with_coverage --branch-coverage --fail-under=80
```
