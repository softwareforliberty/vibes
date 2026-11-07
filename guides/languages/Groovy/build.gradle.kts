// Template: merge these tool settings into the project's build.gradle.kts.
// Pin every plugin and tool to its latest release when you copy it.

plugins {
    groovy
    codenarc
    jacoco
    id("info.solidsoft.pitest") version "1.19.0"
    id("org.owasp.dependencycheck") version "13.0.0"
}

repositories {
    mavenCentral()
}

// Use the CodeNarc build for Groovy 4. Declaring any codenarc dependency
// replaces Gradle's default, so CodeNarc itself is listed too. Its
// CyclomaticComplexity rule needs GMetrics on the same classpath.
dependencies {
    codenarc("org.codenarc:CodeNarc:3.7.0-groovy-4.0")
    codenarc("org.gmetrics:GMetrics-Groovy4:2.1.0")
}

// Lock every configuration, so OSV-Scanner has a gradle.lockfile to read.
dependencyLocking {
    lockAllConfigurations()
}

// Fail the build on any finding.
codenarc {
    configFile = file("codenarc.xml")
    maxPriority1Violations = 0
    maxPriority2Violations = 0
    maxPriority3Violations = 0
}

// Fail the build on any vulnerability with a CVSS score of 7 or more.
dependencyCheck {
    failBuildOnCVSS = 7.0f
}

// Fail the build when line or branch coverage falls below 80%.
tasks.jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                counter = "LINE"
                minimum = "0.80".toBigDecimal()
            }
            limit {
                counter = "BRANCH"
                minimum = "0.80".toBigDecimal()
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}

// Mutation testing: fail when PIT's mutation score falls below 80%.
// scripts/audit passes the code the branch changed in the pitestTargets
// property; without it, PIT mutates every class in the project's group.
pitest {
    pitestVersion = "1.30.2"
    junit5PluginVersion = "1.2.3"
    targetClasses = providers.gradleProperty("pitestTargets")
        .map { it.split(",") }
        .orElse(provider { listOf("${project.group}.*") })
    // A change with nothing to mutate, such as a new interface, isn't an error.
    failWhenNoMutations = false
    // PIT skips Groovy classes unless its Groovy filter is off.
    features = listOf("-FGROOVY")
    mutationThreshold = 80
    timestampedReports = false
    outputFormats = listOf("HTML", "CSV")
}
