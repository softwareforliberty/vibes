// Template: merge these tool settings into the project's build.gradle.kts.
// Pin every plugin and tool to its latest release when you copy it.

import net.ltgt.gradle.errorprone.errorprone

plugins {
    java
    jacoco
    pmd
    id("com.github.spotbugs") version "6.5.8"
    id("net.ltgt.errorprone") version "5.1.0"
    id("org.owasp.dependencycheck") version "12.2.2"
}

repositories {
    mavenCentral()
}

dependencies {
    errorprone("com.google.errorprone:error_prone_core:2.42.0")
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
