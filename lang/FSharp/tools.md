# F# Tools

The free/open source tools that lint, format and check F# code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [.NET SDK](https://github.com/dotnet/sdk) (F# compiler) | MIT | Linting, Code quality | Compiling, and linting through its warnings |
| [Fantomas](https://fsprojects.github.io/fantomas/) | Apache-2.0 | Formatting | Formatting: applies the whole [Layout](coding-style.md#layout) section automatically |
| [FSharpLint](https://fsprojects.github.io/FSharpLint/) | MIT | Linting, Code quality | Lint rules, including complexity and function length limits |
| [fsharp-analyzers](https://github.com/ionide/FSharp.Analyzers.SDK) | MIT | Linting | Running F# analyzers from the command line |
| [G-Research.FSharp.Analyzers](https://github.com/G-Research/fsharp-analyzers) | Apache-2.0 | Linting | Analyzers for common F# bugs and pitfalls |
| [NuGet Audit](https://learn.microsoft.com/nuget/concepts/auditing-packages) (in the .NET SDK) | Apache-2.0 | Auditing | Checking restored packages against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [coverlet](https://github.com/coverlet-coverage/coverlet) | MIT | Code quality | Measuring test coverage, and failing the build below a minimum |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, and Fantomas |
| [`Directory.Build.props`](Directory.Build.props) | MSBuild, for every project in the repository |
| [`.config/dotnet-tools.json`](.config/dotnet-tools.json) | `dotnet tool restore`, which installs Fantomas, FSharpLint and fsharp-analyzers |
| [`fsharplint.json`](fsharplint.json) | FSharpLint |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Configuration

Code must build with **no warnings**, Fantomas must have nothing to change,
and FSharpLint must report nothing:

```sh
dotnet fantomas --check .
dotnet build
dotnet fsharplint lint MySolution.sln
```

Install Fantomas, FSharpLint and fsharp-analyzers as local tools, so every
developer and CI run the same versions. The tool manifest
`.config/dotnet-tools.json` pins them:

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {
    "fantomas": { "version": "8.1.1", "commands": ["fantomas"] },
    "dotnet-fsharplint": {
      "version": "0.27.0",
      "commands": ["dotnet-fsharplint"]
    },
    "fsharp-analyzers": {
      "version": "0.41.0",
      "commands": ["fsharp-analyzers"]
    }
  }
}
```

Restore them once after cloning, and in CI before the checks:

```sh
dotnet tool restore
```

Put the shared build settings in `Directory.Build.props` at the repository
root, so every project gets them:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <WarnOn>1182;3390</WarnOn>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
    <NuGetAudit>true</NuGetAudit>
    <NuGetAuditMode>all</NuGetAuditMode>
    <NuGetAuditLevel>low</NuGetAuditLevel>
  </PropertyGroup>

  <!-- Coverage minimum for projects that reference coverlet.msbuild -->
  <PropertyGroup>
    <CoverletOutputFormat>cobertura</CoverletOutputFormat>
    <Threshold>80</Threshold>
    <ThresholdType>branch</ThresholdType>
    <ThresholdStat>total</ThresholdStat>
  </PropertyGroup>
</Project>
```

- `TreatWarningsAsErrors` turns every compiler and NuGet Audit warning into a
  build failure, including incomplete pattern matches (`FS0025`).
- `WarnOn` turns on two warnings that are off by default: unused values
  (`FS1182`) and malformed XML documentation (`FS3390`).
- The compiler doesn't report public functions that lack documentation, so
  reviewers check that rule.
- The second group sets coverlet's coverage minimum for every test project
  (see [Coverage](#coverage)).

Fantomas reads its settings from `.editorconfig`. Its defaults implement this
guide; the `fsharp_*` values pin the ones the guide relies on, so a new
Fantomas release can't change the layout, and allow at most one blank line in
a row:

```ini
# EditorConfig: https://editorconfig.org
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{fs,fsi,fsx}]
indent_style = space
indent_size = 4
max_line_length = 120

# Fantomas. The values below are Fantomas's defaults, pinned so a new release
# can't change the layout, plus one blank line at most between definitions.
fsharp_space_before_lowercase_invocation = true
fsharp_space_before_uppercase_invocation = false
fsharp_space_before_colon = false
fsharp_space_after_comma = true
fsharp_space_around_delimiter = true
fsharp_keep_max_number_of_blank_lines = 1

# JetBrains Rider, Visual Studio and VS Code (Ionide) format F# with Fantomas,
# which reads the properties above, so no IDE-specific keys are needed.

[*.json]
indent_style = space
indent_size = 2
max_line_length = 80
```

- Leave layout to Fantomas: don't turn on FSharpLint's formatting rules,
  which would fight it.
- Add the `G-Research.FSharp.Analyzers` package and run it with the
  `fsharp-analyzers` tool, as its documentation describes, failing the build
  on any finding.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of F# source: Opengrep doesn't
support F#, and the .NET security analyzers (`CA5xxx`) run only on C# and
Visual Basic. The closest check is reviewing every boundary that touches
input against the [security idioms](idioms.md#security). The G-Research
analyzers catch general bug patterns, but they aren't a security tool.

### Dependency vulnerabilities

NuGet Audit checks every restored package, including transitive ones, on
each restore. With the settings above, any known vulnerability fails the
build. To list the findings without building:

```sh
# .NET 10 SDK and later
dotnet package list --vulnerable --include-transitive

# .NET 9 SDK and earlier
dotnet list package --vulnerable --include-transitive
```

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads NuGet's `packages.lock.json` and checks
every pinned version against the OSV database.

```sh
osv-scanner scan source -r .
```

- `RestorePackagesWithLockFile` writes a `packages.lock.json` for each
  project. In CI, restore with `dotnet restore --locked-mode`, so a build
  fails instead of silently changing a pinned version.

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

lizard doesn't support F#, so FSharpLint enforces the same limits: a
cyclomatic complexity over 10 or more than 60 lines in a function fails the
lint. A function past either limit is hard to test and should be split.

FSharpLint reads `fsharplint.json` from the directory it runs in. A rule
that's missing from the file doesn't run at all, so the file lists every rule:
it's FSharpLint 0.27.0's default configuration with two changes.
`cyclomaticComplexity` is turned on with `maxComplexity` 10, and
`maxLinesInFunction` is turned on with `maxLines` 60. When you upgrade
FSharpLint, start from the new release's default file and make the same two
changes.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format fsharp --min-tokens 50 --exitCode 1 src/
```

`.jscpd.json` holds the same settings, so `jscpd src/` alone runs the same
check.

### Dead code

`FS1182`, turned on above, reports unused values and parameters, so
`TreatWarningsAsErrors` fails the build on them. Prefix a value that's
deliberately unused with `_`. No FOSS tool finds unused public functions
across a whole solution, because outside code may call them.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Add the `coverlet.msbuild` package to each test project.
`Directory.Build.props` sets the 80% branch minimum on the combined total, so
the test run only has to turn coverage on:

```sh
dotnet test /p:CollectCoverage=true
```
