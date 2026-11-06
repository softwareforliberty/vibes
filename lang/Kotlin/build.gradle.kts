// Template: merge these tool settings into the project's build.gradle.kts.
// Pin every plugin and tool to its latest release when you copy it.

import kotlinx.kover.gradle.plugin.dsl.CoverageUnit

plugins {
    kotlin("jvm") version "2.4.21"
    id("io.gitlab.arturbosch.detekt") version "1.23.8"
    id("org.jetbrains.kotlinx.kover") version "0.9.11"
    id("org.owasp.dependencycheck") version "13.0.0"
}

repositories {
    mavenCentral()
}

// Lock every configuration, so OSV-Scanner has a gradle.lockfile to read.
dependencyLocking {
    lockAllConfigurations()
}

kotlin {
    // Libraries only: require a visibility modifier and return type on every
    // public declaration.
    explicitApi()

    // Every compiler warning fails the build.
    compilerOptions {
        allWarningsAsErrors = true
    }
}

// detekt 1.23's plugin fails when Gradle runs on JDK 25: run Gradle on JDK 21.
detekt {
    buildUponDefaultConfig = true
    config.setFrom("detekt.yml")
}

// Fail the build on any vulnerability with a CVSS score of 7 or more.
dependencyCheck {
    failBuildOnCVSS = 7.0f
}

// Fail the build when line or branch coverage falls below 80%.
kover {
    reports {
        verify {
            rule {
                minBound(80)
                minBound(80, CoverageUnit.BRANCH)
            }
        }
    }
}
