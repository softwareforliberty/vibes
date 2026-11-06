// Template: merge these tool settings into the project's build.gradle.kts.
// Pin every plugin and tool to its latest release when you copy it.

plugins {
    groovy
    codenarc
    jacoco
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
