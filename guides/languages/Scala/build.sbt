// Template: merge these tool settings into the project's build.sbt.

ThisBuild / scalaVersion := "3.3.9"

// scalafix's semantic rules (OrganizeImports, RemoveUnused) need SemanticDB.
ThisBuild / semanticdbEnabled := true

// Every compiler warning, including unused code, fails the build.
scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-Werror",
  "-Wunused:all",
  "-Wvalue-discard",
)

// Reject the unsafe constructs the idioms forbid. Tests may call Option.get.
wartremoverErrors ++= Seq(
  Wart.AsInstanceOf,
  Wart.Null,
  Wart.OptionPartial,
  Wart.Return,
  Wart.Var,
)
Test / compile / wartremoverErrors -= Wart.OptionPartial

// Fail the build when statement or branch coverage falls below 80%.
coverageMinimumStmtTotal := 80
coverageMinimumBranchTotal := 80
coverageFailOnMinimum := true

// Fail the build on any vulnerability with a CVSS score of 7 or more. The
// dependencyCheck task reads the key dynamically, which sbt's unused-key check
// can't see, so exclude it from that check.
dependencyCheckFailBuildOnCVSS := 7
Global / excludeLintKeys += dependencyCheckFailBuildOnCVSS
