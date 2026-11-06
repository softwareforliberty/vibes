# Java Tools

The free/open source tools that lint, format and check Java code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [javac](https://openjdk.org/) (OpenJDK) | GPLv2 with Classpath Exception | Linting | Compiling, and linting through its warning flags |
| [google-java-format](https://github.com/google/google-java-format) | Apache-2.0 | Formatting | Formatting: applies the whole [Layout](coding-style.md#layout) section automatically |
| [Checkstyle](https://checkstyle.org/) | LGPL-2.1+ | Linting | Checking naming, Javadoc and the style rules the formatter can't fix |
| [Error Prone](https://errorprone.info/) | Apache-2.0 | Linting, Code quality | Compile-time bug detection, including unused code |
| [PMD](https://pmd.github.io/) | BSD-style | Linting, Code quality | Static analysis for unused code, error-prone patterns and complexity |
| [SpotBugs](https://spotbugs.github.io/) | LGPL-2.1+ | Auditing | Bytecode analysis for bugs, and the host for Find Security Bugs |
| [Find Security Bugs](https://find-sec-bugs.github.io/) | LGPL-3.0 | Auditing | SpotBugs plugin that finds injection, crypto and other security bugs |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) | Apache-2.0 | Auditing | Checking the resolved build classpath against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [JaCoCo](https://www.jacoco.org/jacoco/) | EPL-2.0 | Code quality | Measuring test coverage, and failing the build below a minimum |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`build.gradle.kts`](build.gradle.kts) | Gradle: javac warnings, Error Prone, PMD, SpotBugs, Find Security Bugs, dependency locking, OWASP Dependency-Check and JaCoCo |
| [`pmd-ruleset.xml`](pmd-ruleset.xml) | PMD |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/java.yaml`](.opengrep/java.yaml) | Opengrep |

`build.gradle.kts` is a template: merge its settings into the project's own
build script. Checkstyle uses the `google_checks.xml` configuration bundled
in its jar, which matches this guide, so there's no Checkstyle file to copy.

## Recommended setup

Format, then check. Code must build with **no warnings** and no findings.

```sh
# Format every Java file in place
java -jar google-java-format-<version>-all-deps.jar --replace $(git ls-files '*.java')

# Style checks, using the Google configuration that ships with Checkstyle.
# It reports warnings by default; the property makes each one an error.
java -Dorg.checkstyle.google.severity=error \
  -jar checkstyle-<version>-all.jar -c /google_checks.xml src/

# Static analysis with the project rule set, which builds on PMD's quickstart rules
pmd check --no-progress --no-cache -d src -R pmd-ruleset.xml -f text
```

- Compile with `-Xlint:all -Werror`, so every compiler warning fails the
  build.
- Run Error Prone as a compiler plugin (`-Xplugin:ErrorProne`). Its install
  guide lists the extra flags each build tool needs.
- Because the formatter owns layout, never hand-format code it will rewrite.
  Run it before every commit.

## Auditing

### Security analysis

Run SpotBugs with the Find Security Bugs plugin on every build. It analyses
the compiled bytecode, so it also sees code that generated sources and
annotation processors produce. Apply it through the SpotBugs Gradle or Maven
plugin, add Find Security Bugs as a SpotBugs plugin dependency, and fail the
build on any finding.

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
  vulnerable dependency. The template fails the build on any vulnerability
  with a CVSS score of 7 or more. It needs an NVD API key to download its
  database.

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
lizard -l java -C 10 -L 60 -w src/
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format java --min-tokens 50 --exitCode 1 src/
```

### Dead code

Error Prone's `UnusedVariable` and `UnusedMethod` checks report unused locals,
parameters, fields and private methods as compiler warnings, so
`-Xlint:all -Werror` turns them into build failures. PMD's quickstart rule set
also reports unused private fields, methods and local variables.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

In Gradle, the `jacoco` plugin's `jacocoTestCoverageVerification` task
enforces the minimum; the template sets 80% for both lines and branches and
runs it as part of `check`. In Maven, run the `jacoco-maven-plugin` `check`
goal with the same limits.
