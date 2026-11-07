// Template: merge these plugins into the project's project/plugins.sbt.
// Pin every plugin to its latest release when you copy it.

addSbtPlugin("org.scalameta" % "sbt-scalafmt" % "2.6.2")
addSbtPlugin("ch.epfl.scala" % "sbt-scalafix" % "0.14.9")
addSbtPlugin("org.wartremover" % "sbt-wartremover" % "3.6.3")
addSbtPlugin("org.scoverage" % "sbt-scoverage" % "2.4.4")
addSbtPlugin("net.nmoncho" % "sbt-dependency-check" % "2.0.0")
addSbtPlugin("io.stryker-mutator" % "sbt-stryker4s" % "1.1.1")
