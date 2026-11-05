# Kotlin Tools

The free/open source tools that lint, format and check Kotlin code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [kotlinc](https://kotlinlang.org/) (Kotlin compiler) | Apache-2.0 | Linting | Compiling, and linting through its warnings |
| [ktlint](https://pinterest.github.io/ktlint/) | MIT | Formatting, Linting | Formatting and style checks: applies most of [Layout](coding-style.md#layout) automatically |
| [detekt](https://detekt.dev/) | Apache-2.0 | Linting, Code quality | Static analysis for complexity, code smells, unused code and error-prone patterns |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) | Apache-2.0 | Auditing | Checking the resolved build classpath against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Kover](https://github.com/Kotlin/kotlinx-kover) | Apache-2.0 | Code quality | Measuring test coverage, and failing the build below a minimum |

## Recommended setup

Format, then check. Code must build with **no warnings** and no findings.

```sh
# Format every Kotlin file in place, then check what it couldn't fix
ktlint --format
ktlint

# Static analysis, using detekt's defaults plus the project's overrides
detekt --input src --config detekt.yml --build-upon-default-config
```

Configure ktlint through `.editorconfig` at the repository root:

```ini
[*.{kt,kts}]
ktlint_code_style = intellij_idea
max_line_length = 120
ij_kotlin_allow_trailing_comma = true
ij_kotlin_allow_trailing_comma_on_call_site = true
```

- Treat warnings as errors: pass `-Werror` to `kotlinc`, or set
  `allWarningsAsErrors = true` in the Gradle `compilerOptions` block.
- In libraries, turn on **explicit API mode** (`kotlin { explicitApi() }`).
  The compiler then requires a visibility modifier and return type on every
  public declaration (see [Visibility and types](coding-style.md#visibility-and-types)).
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

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads Gradle's `gradle.lockfile` and Maven's
`pom.xml`, and checks every pinned version against the OSV database.

```sh
osv-scanner scan source -r .
```

- In Gradle, turn on dependency locking so there's a lockfile to commit:
  `dependencyLocking { lockAllConfigurations() }` in the build script, then
  `./gradlew dependencies --write-locks` whenever a dependency changes.
- Maven has no lockfile. OSV-Scanner resolves `pom.xml`'s transitive
  dependencies through deps.dev, which needs network access.
- OWASP Dependency-Check's Gradle and Maven plugins check the resolved
  classpath during the build. Use it when the build itself must fail on a
  vulnerable dependency. It needs an NVD API key to download its database.

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
lizard -l kotlin -C 10 -L 60 -w src/
```

detekt's `CyclomaticComplexMethod` and `LongMethod` rules check the same
things inside the build. Set their thresholds in `detekt.yml` to match these
limits, so both tools agree.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format kotlin --min-tokens 50 --exitCode 1 src/
```

### Dead code

detekt's `UnusedPrivateMember`, `UnusedPrivateProperty` and `UnusedParameter`
rules report unused private functions, properties and parameters. The compiler
also warns about unused variables, so `-Werror` makes them build failures.

### Coverage

Measure line and branch coverage with Kover on every test run, and fail the
build when coverage drops below the project's agreed minimum (for example,
80% of lines). Set the minimum with `minBound` in a Kover `verify` rule, then
run `./gradlew koverVerify`.
