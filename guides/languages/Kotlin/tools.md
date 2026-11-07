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
| [PIT](https://pitest.org/) | Apache-2.0 | Code quality | Mutation testing |
| [ArchUnit](https://www.archunit.org/) | Apache-2.0 | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig; ktlint |
| [`detekt.yml`](detekt.yml) | detekt |
| [`build.gradle.kts`](build.gradle.kts) | Gradle: compiler warnings, explicit API mode, detekt, dependency locking, OWASP Dependency-Check, Kover and PIT |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/kotlin.yaml`](.opengrep/kotlin.yaml) | Opengrep |

`build.gradle.kts` is a template: merge its settings into the project's own
build script.

## Recommended setup

Format, then check. Code must build with **no warnings** and no findings.

```sh
# Format every Kotlin file in place, then check what it couldn't fix
ktlint --format
ktlint

# Static analysis, using detekt's defaults plus the project's overrides
detekt --input src --config detekt.yml --build-upon-default-config
```

Configure ktlint through `.editorconfig` at the repository root. IntelliJ IDEA
reads the same file, so the IDE and ktlint agree:

```ini
# EditorConfig: https://editorconfig.org
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{kt,kts}]
indent_style = space
indent_size = 4
max_line_length = 120
# ktlint
ktlint_code_style = intellij_idea
# JetBrains IDEs (ktlint reads these too)
ij_continuation_indent_size = 4
ij_kotlin_allow_trailing_comma = true
ij_kotlin_allow_trailing_comma_on_call_site = true
ij_kotlin_code_style_defaults = KOTLIN_OFFICIAL
ij_kotlin_imports_layout = *,java.**,javax.**,kotlin.**,^
ij_kotlin_name_count_to_use_star_import = 2147483647
ij_kotlin_name_count_to_use_star_import_for_members = 2147483647
ij_kotlin_packages_to_use_import_on_demand = unset

[*.json]
indent_style = space
indent_size = 2
max_line_length = 80

[*.{yaml,yml}]
indent_style = space
indent_size = 2
max_line_length = 80
# JetBrains IDEs
ij_yaml_align_values_properties = do_not_align
ij_yaml_autoinsert_sequence_marker = true
ij_yaml_block_mapping_on_new_line = false
ij_yaml_indent_sequence_value = true
ij_yaml_keep_indents_on_empty_lines = false
ij_yaml_keep_line_breaks = true
ij_yaml_sequence_on_new_line = false
ij_yaml_space_before_colon = false
ij_yaml_spaces_within_braces = false
ij_yaml_spaces_within_brackets = false

# VS Code, Vim, Emacs and Neovim read only the standard properties above.
```

- Treat warnings as errors: pass `-Werror` to `kotlinc`, or set
  `allWarningsAsErrors = true` in the Gradle `compilerOptions` block.
- In libraries, turn on **explicit API mode** (`kotlin { explicitApi() }`).
  The compiler then requires a visibility modifier and return type on every
  public declaration (see [Visibility and types](coding-style.md#visibility-and-types)).
- detekt 1.23's Gradle plugin fails when Gradle itself runs on JDK 25. Run
  Gradle on JDK 21 until detekt 2 is released. The detekt command line runs
  on either.
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
lizard -l kotlin -C 10 -L 60 -w src/
```

detekt's `CyclomaticComplexMethod` and `LongMethod` rules check the same
things inside the build. detekt reports a function that reaches a threshold,
so [`detekt.yml`](detekt.yml) sets them to 11 and 61, one more than these
limits, and both tools agree.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format kotlin --min-tokens 50 --exit-code 1 src/
```

### Dead code

detekt's `UnusedPrivateMember`, `UnusedPrivateProperty` and `UnusedParameter`
rules report unused private functions, properties and parameters. The compiler
also warns about unused variables, so `-Werror` makes them build failures.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Kover enforces the minimum: the template sets `minBound` to 80% for both
lines and branches in a `verify` rule. Run `./gradlew koverVerify`.

### Mutation testing

PIT makes small changes to the compiled code, such as turning `>=` into
`>`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. A full run is slow, so
`scripts/audit` mutates only the code changed since the base branch, and
skips the run when there is none.

A Kotlin file can declare several classes under any names, and its
top-level functions compile to a class named after the file, such as
`PricingKt`. So the command reads each changed file's `package` line and
mutates that package, which takes in its other files and subpackages too:

```sh
packages=$(git diff --name-only --diff-filter=d origin/main... \
  -- 'src/main/kotlin/*.kt' |
  xargs -r sed -n 's/^package \(.*\)/\1.*/p' | sort -u | paste -sd, -)
[ -z "$packages" ] || ./gradlew pitest -PpitestTargets="$packages"
```

The settings are in the `pitest` block of
[`build.gradle.kts`](build.gradle.kts). This guide was checked with PIT
1.30.2 and its Gradle plugin 1.19.0. PIT runs JUnit 5 and 6 tests,
`kotlin.test` ones included, through its JUnit 5 plugin, which the
template adds.

PIT mutates bytecode, so it sees what the Kotlin compiler generates. It
skips the compiler's null checks and a data class's generated methods,
but it mutates property getters: a property no test reads shows up as
`NO_COVERAGE`.

`mutationThreshold` makes the run fail when the mutation score, the share
of mutants the tests kill, is under 80%. That's the same bar as coverage.
Some mutants can't be killed, because they don't change what the code
does, so 100% is rarely reachable; 80% leaves room for them and still
fails a change whose tests check little. `failWhenNoMutations` is off, so
a change with nothing to mutate, such as a new interface, passes. Run
without `pitestTargets`, PIT mutates every class in the project's `group`.

The CSV report lists every mutant with its class, mutator, method, line
and status. Find the survivors with `grep`:

```text
$ grep SURVIVED build/reports/pitest/mutations.csv
Pricing.kt,com.example.app.PricingKt,org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator,discounted,4,SURVIVED,none
```

Read it as a missing test: here, `ConditionalsBoundaryMutator` turned the
`>=` on line 4 into `>`, and no test passes exactly 100, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that
just runs the line. `NO_COVERAGE` means no test reaches the line at all.
`build/reports/pitest/index.html` shows each mutant on its source line.

PIT can't suppress a single mutant, but it skips any class or method
annotated with an annotation named `DoNotMutate`. If a method's mutants
can't change behaviour, declare that annotation in the project, with
`BINARY` retention, and put it on the method with a comment saying why,
rather than writing a test that contorts the code.

### Architecture

Check the dependency rules between the project's layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks. Where each
layer is its own Gradle subproject, the build already rejects a forbidden
dependency; ArchUnit checks the rest as a test, and also finds cycles.

ArchUnit reads the compiled classes, so it sees every dependency, imported
or not. Konsist checks Kotlin source instead, but it reads only `import`
lines and can't find cycles, so prefer ArchUnit for JVM code.

Add ArchUnit's JUnit 6 support to the test dependencies, and make Gradle
print the whole failure. Put the `import` at the top of `build.gradle.kts`.
With JUnit 5, use `archunit-junit5` instead.

```kotlin
import org.gradle.api.tasks.testing.logging.TestExceptionFormat

dependencies {
    testImplementation("com.tngtech.archunit:archunit-junit6:1.5.1")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
    // Print each broken rule's violations in the build log.
    testLogging.exceptionFormat = TestExceptionFormat.FULL
}
```

Write the rules as a test. This one stops the core depending on the edges,
which may depend on the core, and forbids cycles between the top-level
packages. The package names are examples: replace them with the layers in
the project's `design.md`.

```kotlin
package com.example.app

import com.tngtech.archunit.core.importer.ImportOption
import com.tngtech.archunit.junit.AnalyzeClasses
import com.tngtech.archunit.junit.ArchTest
import com.tngtech.archunit.lang.ArchRule
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices

/** The dependency rules between the layers in design.md. */
@AnalyzeClasses(
    packages = ["com.example.app"],
    importOptions = [ImportOption.DoNotIncludeTests::class],
)
class ArchitectureTest {
    /** The core depends on no edge; the edges may depend on the core. */
    @ArchTest
    val coreDoesNotDependOnEdges: ArchRule =
        noClasses()
            .that()
            .resideInAPackage("com.example.app.core..")
            .should()
            .dependOnClassesThat()
            .resideInAnyPackage("com.example.app.adapters..", "com.example.app.cli..")

    /** No two top-level packages depend on each other. */
    @ArchTest
    val noCycles: ArchRule =
        slices().matching("com.example.app.(*)..").should().beFreeOfCycles()
}
```

`scripts/check` runs it with the other tests. A broken rule fails the build
and lists each dependency that breaks it, with its file and line:

```sh
./gradlew test
```

## Sources

- [PIT quick start](https://pitest.org/quickstart/) and
  [mutators](https://pitest.org/quickstart/mutators/)
- [PIT FAQ](https://pitest.org/faq/)
- [gradle-pitest-plugin](https://gradle-pitest-plugin.solidsoft.info/)
