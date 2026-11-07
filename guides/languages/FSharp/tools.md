# F# Tools

The free/open source tools that lint, format and check F# code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [.NET SDK](https://github.com/dotnet/sdk) (F# compiler) | MIT | Linting, Code quality | Compiling, and linting through its warnings |
| [Fantomas](https://fsprojects.github.io/fantomas/) | Apache-2.0 | Formatting | Formatting: applies the whole [Layout](coding-style.md#layout) section automatically |
| [FSharpLint](https://fsprojects.github.io/FSharpLint/) | MIT | Linting, Code quality | Lint rules, including complexity and function length limits |
| [fsharp-analyzers](https://github.com/ionide/FSharp.Analyzers.SDK) | MIT | Linting | Running F# analyzers after each build, through its `FSharp.Analyzers.Build` package |
| [G-Research.FSharp.Analyzers](https://github.com/G-Research/fsharp-analyzers) | Apache-2.0 | Linting | Analyzers for common F# bugs and pitfalls |
| [NuGet Audit](https://learn.microsoft.com/nuget/concepts/auditing-packages) (in the .NET SDK) | Apache-2.0 | Auditing | Checking restored packages against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [coverlet](https://github.com/coverlet-coverage/coverlet) | MIT | Code quality | Measuring test coverage, and failing the build below a minimum |
| [ArchUnitNET](https://github.com/TNG/ArchUnitNET) | Apache-2.0 | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, and Fantomas |
| [`Directory.Build.props`](Directory.Build.props) | MSBuild, for every project in the repository |
| [`Directory.Build.targets`](Directory.Build.targets) | MSBuild, which runs the F# analyzers after each build |
| [`.config/dotnet-tools.json`](.config/dotnet-tools.json) | `dotnet tool restore`, which installs Fantomas, FSharpLint and fsharp-analyzers |
| [`fsharplint.json`](fsharplint.json) | FSharpLint |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Configuration

Code must build with **no warnings or analyzer findings**, Fantomas must
have nothing to change, and FSharpLint must report nothing:

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

  <!-- F# analyzers, which Directory.Build.targets runs after each build -->
  <ItemGroup>
    <PackageReference Include="FSharp.Analyzers.Build" Version="0.5.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>build</IncludeAssets>
    </PackageReference>
    <PackageReference Include="G-Research.FSharp.Analyzers" Version="0.26.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>analyzers</IncludeAssets>
    </PackageReference>
  </ItemGroup>
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
- The `ItemGroup` adds the G-Research analyzers, and the
  `FSharp.Analyzers.Build` targets that run them, to every project.

The analyzers run in `Directory.Build.targets`, not `Directory.Build.props`,
because the package path property `$(PkgG-Research_FSharp_Analyzers)` is only
set after NuGet's generated props load:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
  <!-- G-Research analyzers: run after each build, every finding an error -->
  <PropertyGroup>
    <RunAnalyzersDuringBuild>true</RunAnalyzersDuringBuild>
    <FSharpAnalyzersContinueOnError>false</FSharpAnalyzersContinueOnError>
    <FSharpAnalyzersOtherFlags>--analyzers-path &quot;$(PkgG-Research_FSharp_Analyzers)/analyzers/dotnet/fs&quot;</FSharpAnalyzersOtherFlags>
    <FSharpAnalyzersOtherFlags>$(FSharpAnalyzersOtherFlags) --treat-as-error &quot;*&quot;</FSharpAnalyzersOtherFlags>
  </PropertyGroup>
</Project>
```

- `RunAnalyzersDuringBuild` runs `fsharp-analyzers` after each project
  compiles, so `dotnet build` runs the analyzers too. Run
  `dotnet tool restore` first, or the build can't find the tool.
- `--treat-as-error "*"` makes every finding an error, and
  `FSharpAnalyzersContinueOnError` set to `false` lets that error fail the
  build.
- An incremental build that doesn't recompile a project doesn't re-run its
  analyzers either; CI builds from a clean checkout, so it always runs them.

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
fsharp_multiline_bracket_style = aligned
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
jscpd --format fsharp --min-tokens 50 --exit-code 1 src/
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

### Mutation testing

No maintained FOSS mutation testing tool supports F#. Stryker.NET, the
.NET mutation tester, mutates only C#: it removed its experimental F#
support in 2024, and 5.0.0 stops with `Language not supported: Fsharp` on
an F# project.

Rely on the [test reviewer](../../../agents/test-reviewer.md) instead,
which checks that each test pins down the behaviour it covers, not just
runs it, and on the coverage minimum in [Coverage](#coverage). When you
write a test, ask what change to the code would still pass it, such as
`>=` turned into `>`, and add the case that catches it.

### Architecture

Make the build and ArchUnitNET enforce the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks. Put each
layer that can stand alone in its own project, with project references only
to the layers it may use, so a forbidden `open` fails to compile. Inside one
project, the compile order only stops a file using the files below it, so a
core file listed after an edge file can still use it. ArchUnitNET checks the
rules the build can't, as tests that read the compiled assemblies.

Add its xUnit package to a test project (it has NUnit and MSTest packages
too):

```sh
dotnet package add TngTech.ArchUnitNET.xUnitV3 --project tests/Example.ArchitectureTests
```

`scripts/check` runs the tests. Any breach fails a test, so `dotnet test`
exits non-zero and names each type that broke the rule:

```sh
dotnet test tests/Example.ArchitectureTests
```

An example test module for a core with two edges. The namespaces are
examples: replace them with the layers in the project's `design.md`.

```fsharp
/// Checks the dependency rules between the layers.
module Example.ArchitectureTests

open ArchUnitNET.Domain
open ArchUnitNET.Loader
open ArchUnitNET.xUnitV3
open Example.Core
open Xunit

open type ArchUnitNET.Fluent.ArchRuleDefinition
open type ArchUnitNET.Fluent.Slices.SliceRuleDefinition

let private architecture =
    ArchLoader().LoadAssemblies(typeof<Order>.Assembly).Build()

let private core: IObjectProvider<IType> =
    Types().That().ResideInNamespaceOrBelow("Example.Core").As("Core")

let private edges: IObjectProvider<IType> =
    Types().That().ResideInNamespaceOrBelow("Example.Adapters").Or().ResideInNamespaceOrBelow("Example.Cli").As("Edges")

/// The core doesn't depend on the adapters or the CLI.
[<Fact>]
let ``the core doesn't depend on the edges`` () =
    Types().That().Are(core).Should().NotDependOnAny(edges).Check(architecture)

/// The namespaces under Example have no dependency cycles.
[<Fact>]
let ``namespaces have no cycles`` () =
    Slices().Matching("Example.(*)").Should().BeFreeOfCycles().Check(architecture)
```

- `open type` brings in ArchUnitNET's static `Types()` and `Slices()`
  methods.
- `ResideInNamespaceOrBelow` takes in the namespaces under a layer's own,
  so `Example.Core.Billing` is part of the core.
- The first test fails if any core type uses an adapter or CLI type. Each
  edge may use the core.
- `Slices().Matching("Example.(*)")` makes one slice for each namespace
  directly under `Example`. The second test fails if any slices depend on
  each other in a loop, directly or through others.
- Run the tests in the Debug configuration, `dotnet test`'s default. A
  Release build can optimise away some dependencies, so the tests would miss
  them.
- `dotnet test` here uses the VSTest runner, as the coverage run does. With
  xUnit v3 4.x, reference `xunit.v3.mtp-off` instead of `xunit.v3`, or the
  .NET 10 SDK refuses to run the tests that way.

## Sources

- [Stryker.NET](https://stryker-mutator.io/docs/stryker-net/introduction/)
- [Stryker.NET: removal of F# support](https://github.com/stryker-mutator/stryker-net/pull/3121)
