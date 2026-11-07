// Template: merge these tool settings into the project's build.gradle.kts.
// Pin every plugin and tool to its latest release when you copy it.

import net.ltgt.gradle.errorprone.errorprone

plugins {
    java
    jacoco
    pmd
    id("com.github.spotbugs") version "6.5.13"
    id("net.ltgt.errorprone") version "5.2.0"
    id("info.solidsoft.pitest") version "1.19.0"
    id("org.owasp.dependencycheck") version "13.0.0"
}

repositories {
    mavenCentral()
}

dependencies {
    errorprone("com.google.errorprone:error_prone_core:2.52.0")
    spotbugsPlugins("com.h3xstream.findsecbugs:findsecbugs-plugin:1.14.0")
}

// Lock every configuration, so OSV-Scanner has a gradle.lockfile to read.
dependencyLocking {
    lockAllConfigurations()
}

// Every compiler and Error Prone warning fails the build.
tasks.withType<JavaCompile>().configureEach {
    options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror"))
    options.errorprone.disableWarningsInGeneratedCode = true
}

pmd {
    isConsoleOutput = true
    ruleSetFiles = files("pmd-ruleset.xml")
    ruleSets = emptyList()
}

spotbugs {
    ignoreFailures = false
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
    mutationThreshold = 80
    timestampedReports = false
    outputFormats = listOf("HTML", "CSV")
}
