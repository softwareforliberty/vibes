# Scala Tools

The free/open source tools that lint, format and check Scala code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Scala compiler](https://www.scala-lang.org/) (`scalac`) | Apache-2.0 | Linting, Code quality | Compiling, and linting through its warnings, including unused code |
| [scalafmt](https://scalameta.org/scalafmt/) | Apache-2.0 | Formatting | Formatting: applies [Layout](coding-style.md#layout) automatically |
| [scalafix](https://scalacenter.github.io/scalafix/) | BSD-3-Clause | Linting, Code quality | Rewrites and lint rules, including import order and unused code |
| [WartRemover](https://www.wartremover.org/) | Apache-2.0 | Linting | Rejecting unsafe constructs such as `null`, `var` and `Option.get` |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [sbt-dependency-check](https://github.com/nMoncho/sbt-dependency-check) | MIT | Auditing | Checking the resolved classpath against known vulnerabilities, using OWASP Dependency-Check |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [scoverage](https://github.com/scoverage/sbt-scoverage) | Apache-2.0 | Code quality | Measuring statement and branch coverage |

## Recommended setup

Format, then check. Code must build with **no warnings** and no findings.

```sh
sbt scalafmtCheckAll "scalafixAll --check" compile
```

Configure scalafmt in `.scalafmt.conf` at the repository root. Pin the
version, so every machine formats the same way:

```hocon
version = "3.8.3"
runner.dialect = scala3
maxColumn = 100
rewrite.scala3.convertToNewSyntax = true
rewrite.scala3.removeOptionalBraces = true
rewrite.trailingCommas.style = always
```

Turn on the compiler warnings in `build.sbt`, and make them errors:

```scala
scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-Werror",
  "-Wunused:all",
  "-Wvalue-discard",
)
```

Configure scalafix in `.scalafix.conf`:

```hocon
rules = [
  OrganizeImports,
  RemoveUnused,
  DisableSyntax,
]
DisableSyntax.noNulls = true
DisableSyntax.noReturns = true
DisableSyntax.noVars = true
OrganizeImports.removeUnused = true
```

- Add WartRemover's `Null`, `OptionPartial`, `Return`, `Var` and `AsInstanceOf`
  warts as errors (`wartremoverErrors ++= Seq(...)`) to back up the
  [absence and errors](idioms.md#absence-and-errors) idioms. Tests may relax
  `OptionPartial`.
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

OSV-Scanner doesn't read sbt builds, and sbt has no standard lockfile, so it
can't check Scala dependencies directly. Use sbt-dependency-check instead,
which runs OWASP Dependency-Check against the resolved classpath and fails the
build on a known vulnerability:

```scala
// project/plugins.sbt
addSbtPlugin("net.nmoncho" % "sbt-dependency-check" % "1.9.2")
```

```sh
sbt dependencyCheck
```

- Set the failure threshold in `build.sbt` so any vulnerability with a CVSS
  score of 7 or more fails the build.
- Dependency-Check needs an NVD API key to download its database.
- Pin every dependency to an exact version. A version range makes the
  resolved classpath, and so the audit, change between builds.

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
lizard -l scala -C 10 -L 60 -w src/
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format scala --min-tokens 50 --exitCode 1 src/
```

### Dead code

The compiler's `-Wunused:all` warns about unused imports, private members,
local values and parameters, and `-Werror` makes each one a build failure.
scalafix's `RemoveUnused` rule deletes them automatically.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```scala
// build.sbt
coverageMinimumStmtTotal := 80
coverageMinimumBranchTotal := 80
coverageFailOnMinimum := true
```

```sh
sbt clean coverage test coverageReport
```
