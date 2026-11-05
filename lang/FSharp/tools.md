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

## Configuration

Code must build with **no warnings**, Fantomas must have nothing to change,
and FSharpLint must report nothing:

```sh
dotnet fantomas --check .
dotnet build
dotnet fsharplint lint MySolution.sln
```

Install Fantomas, FSharpLint and fsharp-analyzers as local tools, so every
developer and CI run the same versions:

```sh
dotnet new tool-manifest
dotnet tool install fantomas
dotnet tool install dotnet-fsharplint
dotnet tool install fsharp-analyzers
```

Put the shared build settings in `Directory.Build.props` at the repository
root, so every project gets them:

```xml
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
</Project>
```

- `TreatWarningsAsErrors` turns every compiler and NuGet Audit warning into a
  build failure, including incomplete pattern matches (`FS0025`).
- `WarnOn` turns on two warnings that are off by default: unused values
  (`FS1182`) and malformed XML documentation (`FS3390`).
- The compiler doesn't report public functions that lack documentation, so
  reviewers check that rule.

Fantomas reads its settings from `.editorconfig`. The defaults implement this
guide, so only the shared settings are needed:

```ini
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

Put the limits in `fsharplint.json`:

```json
{
  "cyclomaticComplexity": { "enabled": true, "config": { "maxComplexity": 10 } },
  "maxLinesInFunction": { "enabled": true, "config": { "maxLines": 60 } }
}
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format fsharp --min-tokens 50 --exitCode 1 src/
```

### Dead code

`FS1182`, turned on above, reports unused values and parameters, so
`TreatWarningsAsErrors` fails the build on them. Prefix a value that's
deliberately unused with `_`. No FOSS tool finds unused public functions
across a whole solution, because outside code may call them.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Add the `coverlet.msbuild` package to each test project, then:

```sh
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura \
    /p:Threshold=80 /p:ThresholdType=branch /p:ThresholdStat=total
```
