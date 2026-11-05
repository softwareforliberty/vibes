# Groovy Tools

The free/open source tools that lint, format and check Groovy code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [CodeNarc](https://codenarc.github.io/CodeNarc/) | Apache-2.0 | Linting, Auditing, Code quality | Static analysis: style, naming, formatting, security, size and unused code |
| [npm-groovy-lint](https://nvuillam.github.io/npm-groovy-lint/) | MIT | Formatting, Linting | Runs CodeNarc from the command line, and formats and auto-fixes code |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) | Apache-2.0 | Auditing | Checking the resolved build classpath against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [JaCoCo](https://www.jacoco.org/jacoco/) | EPL-2.0 | Code quality | Measuring test coverage, and failing the build below a minimum |

## Recommended setup

Format, then check. Code must have no findings.

```sh
# Format and auto-fix every Groovy file, then report what's left
npm-groovy-lint --format
npm-groovy-lint
```

- In a Gradle build, also run CodeNarc through Gradle's built-in `codenarc`
  plugin, so the build fails on any finding.
- Set CodeNarc's formatting rules to match this guide: `Indentation` with 4
  spaces per level, and `LineLength` at 120.
- Because the formatter owns layout, never hand-format code it will rewrite.
  Run it before every commit.

Add CodeNarc's security, size and unused-code rule sets to the project's
rule set file, so the checks in [Auditing](#auditing) and
[Code quality](#code-quality) run with the rest of the build:

```xml
<ruleset xmlns="http://codenarc.org/ruleset/1.0">
    <ruleset-ref path="rulesets/security.xml"/>
    <ruleset-ref path="rulesets/size.xml">
        <rule-config name="CyclomaticComplexity">
            <property name="maxMethodComplexity" value="10"/>
        </rule-config>
        <rule-config name="MethodSize">
            <property name="maxLines" value="60"/>
        </rule-config>
    </ruleset-ref>
    <ruleset-ref path="rulesets/unused.xml"/>
</ruleset>
```

## Auditing

### Security analysis

No maintained FOSS pattern or taint analyser supports Groovy source, and
Opengrep doesn't parse it. Run CodeNarc's `security` rule set instead, which
catches the unsafe patterns it knows about, and review any code that builds
shell commands, SQL or file paths from input by hand.

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
- Scripts that fetch dependencies with Grape (`@Grab`) have no lockfile, so
  no scanner can see them. Declare dependencies in the build instead.

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

lizard doesn't support Groovy, so CodeNarc's `size` rule set checks
complexity instead. Fail the build on any method with a cyclomatic complexity
over 10 or more than 60 lines, using the `CyclomaticComplexity` and
`MethodSize` settings above. A method past either limit is hard to test and
should be split. `CyclomaticComplexity` needs the GMetrics library on
CodeNarc's classpath.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format groovy --min-tokens 50 --exitCode 1 src/
```

### Dead code

CodeNarc's `unused` rule set reports unused private methods, fields,
variables and parameters.

### Coverage

Measure line and branch coverage with JaCoCo on every test run, and fail the
build when coverage drops below the project's agreed minimum (for example,
80% of lines). In Gradle, apply the `jacoco` plugin and run
`jacocoTestCoverageVerification`. In Maven, run the `jacoco-maven-plugin`
`check` goal.
