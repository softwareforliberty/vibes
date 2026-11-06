# Visual Basic Tools

The free/open source tools that lint, format and check Visual Basic code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

Visual Basic has fewer dedicated FOSS tools than C#. The .NET SDK's compiler
and analyzers do most of the work, and several general-purpose tools don't
support it at all; each section below says where that leaves a gap.

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [.NET SDK](https://github.com/dotnet/sdk) (Visual Basic compiler and .NET code analyzers) | MIT | Linting, Auditing, Code quality | Compiling with `Option Strict`, and code-style, quality and security analysis |
| [dotnet format](https://github.com/dotnet/format) (in the .NET SDK) | MIT | Formatting | Applying the `.editorconfig` formatting and code-style fixes |
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
| [`.editorconfig`](.editorconfig) | Editors and IDEs, `dotnet format` and the .NET analyzers |
| [`Directory.Build.props`](Directory.Build.props) | MSBuild, for every project in the repository |
| [`CodeMetricsConfig.txt`](CodeMetricsConfig.txt) | The `CA1502` complexity analyzer |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Configuration

Code must build with **no warnings**, and the formatter must have nothing to
change:

```sh
dotnet format --verify-no-changes
dotnet build
```

Put the shared build settings in `Directory.Build.props` at the repository
root, so every project gets them:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
  <PropertyGroup>
    <OptionStrict>On</OptionStrict>
    <OptionExplicit>On</OptionExplicit>
    <OptionInfer>On</OptionInfer>
    <OptionCompare>Binary</OptionCompare>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <AnalysisLevel>latest-recommended</AnalysisLevel>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
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

  <!-- Complexity limit read by the CA1502 analyzer -->
  <ItemGroup>
    <AdditionalFiles Include="$(MSBuildThisFileDirectory)CodeMetricsConfig.txt"/>
  </ItemGroup>
</Project>
```

- The four `Option` properties apply the
  [language baseline](coding-style.md#language-baseline) to every file, so
  no file needs its own `Option` statements.
- `TreatWarningsAsErrors` turns every compiler, analyzer and NuGet Audit
  warning into a build failure.
- `AnalysisLevel` turns on the recommended set of .NET code-quality rules
  (`CAxxxx`).
- `EnforceCodeStyleInBuild` makes the code-style rules (`IDExxxx`) run during
  the build, not just in the editor.
- `GenerateDocumentationFile` writes the XML documentation file and lets
  `IDE0005` find unused `Imports` statements.
- The second group sets coverlet's coverage minimum for every test project
  (see [Coverage](#coverage)), and the `ItemGroup` hands
  `CodeMetricsConfig.txt` to the analyzers (see [Complexity](#complexity)).

Put the formatting and code-style rules in `.editorconfig`, which both
`dotnet format` and the build read:

```ini
# EditorConfig: https://editorconfig.org
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.vb]
indent_style = space
indent_size = 4
max_line_length = 120

# .NET code style and analyzers: read by dotnet format, the build
# (EnforceCodeStyleInBuild), Visual Studio and VS Code with C# Dev Kit.
# Each enforced rule sets both the option's severity and the matching
# dotnet_diagnostic severity, so the IDE and the build agree.

# Imports
dotnet_sort_system_directives_first = true
dotnet_separate_import_directive_groups = false
dotnet_diagnostic.IDE0005.severity = warning

# Declarations (IDE0036 checks the default modifier order: Public Shared, not
# Shared Public)
dotnet_style_require_accessibility_modifiers = always:warning
dotnet_diagnostic.IDE0040.severity = warning
dotnet_diagnostic.IDE0036.severity = warning
dotnet_style_predefined_type_for_locals_parameters_members = true:warning
dotnet_style_predefined_type_for_member_access = true:warning
dotnet_diagnostic.IDE0049.severity = warning
dotnet_style_qualification_for_field = false:warning
dotnet_style_qualification_for_property = false:warning
dotnet_style_qualification_for_method = false:warning
dotnet_style_qualification_for_event = false:warning
dotnet_diagnostic.IDE0003.severity = warning
dotnet_style_readonly_field = true:warning
dotnet_diagnostic.IDE0044.severity = warning

# Expressions
dotnet_style_prefer_is_null_check_over_reference_equality_method = true:warning
dotnet_diagnostic.IDE0041.severity = warning
visual_basic_style_prefer_isnot_expression = true:warning
dotnet_diagnostic.IDE0084.severity = warning
dotnet_style_coalesce_expression = true:warning
dotnet_diagnostic.IDE0029.severity = warning
dotnet_diagnostic.IDE0030.severity = warning
dotnet_style_null_propagation = true:warning
dotnet_diagnostic.IDE0031.severity = warning

# Naming: PascalCase constants, I-prefixed interfaces, s_camelCase Shared
# fields, _camelCase instance fields. The build reports a naming rule's
# severity only when IDE1006 has one too.
dotnet_diagnostic.IDE1006.severity = warning

dotnet_naming_rule.constants.symbols = constants
dotnet_naming_rule.constants.style = pascal_case
dotnet_naming_rule.constants.severity = warning
dotnet_naming_symbols.constants.applicable_kinds = field, local
dotnet_naming_symbols.constants.required_modifiers = const
dotnet_naming_style.pascal_case.capitalization = pascal_case

dotnet_naming_rule.interfaces.symbols = interfaces
dotnet_naming_rule.interfaces.style = i_pascal_case
dotnet_naming_rule.interfaces.severity = warning
dotnet_naming_symbols.interfaces.applicable_kinds = interface
dotnet_naming_style.i_pascal_case.required_prefix = I
dotnet_naming_style.i_pascal_case.capitalization = pascal_case

dotnet_naming_rule.static_fields.symbols = static_fields
dotnet_naming_rule.static_fields.style = s_camel_case
dotnet_naming_rule.static_fields.severity = warning
dotnet_naming_symbols.static_fields.applicable_kinds = field
dotnet_naming_symbols.static_fields.applicable_accessibilities = private, friend
dotnet_naming_symbols.static_fields.required_modifiers = shared
dotnet_naming_style.s_camel_case.required_prefix = s_
dotnet_naming_style.s_camel_case.capitalization = camel_case

dotnet_naming_rule.instance_fields.symbols = instance_fields
dotnet_naming_rule.instance_fields.style = underscore_camel_case
dotnet_naming_rule.instance_fields.severity = warning
dotnet_naming_symbols.instance_fields.applicable_kinds = field
dotnet_naming_symbols.instance_fields.applicable_accessibilities = private, friend
dotnet_naming_style.underscore_camel_case.required_prefix = _
dotnet_naming_style.underscore_camel_case.capitalization = camel_case

# Complexity: CA1502 fails any method over the limit in CodeMetricsConfig.txt
dotnet_diagnostic.CA1502.severity = warning

# Unused code: private member never used (IDE0051), never read (IDE0052),
# unused parameter (IDE0060)
dotnet_diagnostic.IDE0051.severity = warning
dotnet_diagnostic.IDE0052.severity = warning
dotnet_diagnostic.IDE0060.severity = warning

# Security rules as build failures
dotnet_analyzer_diagnostic.category-Security.severity = warning

# JetBrains Rider reads the standard and dotnet_* properties above, so it
# needs no resharper_* keys.

[*.json]
indent_style = space
indent_size = 2
max_line_length = 80
```

- Each enforced rule sets both the option's severity (read by the editor)
  and the matching `dotnet_diagnostic` severity (read by the build), so the
  two always agree.
- The constants rule comes first, so `Const` fields get `PascalCase` rather
  than a field prefix.
- The build doesn't run every rule: `Me.` qualification (`IDE0003`), .NET
  type names (`IDE0049`) and whitespace are reported only by
  `dotnet format --verify-no-changes`, so run both commands.
- Never hand-format code the formatter will rewrite. Run `dotnet format`
  before every commit.

## Auditing

### Security analysis

The .NET SDK ships security analyzers (`CA2100`, `CA3xxx`, `CA5xxx`) that
find SQL injection, insecure deserialisation, weak cryptography and similar
bugs, and they run on Visual Basic as well as C#. The `.editorconfig` above
raises the whole Security category to warnings, so `TreatWarningsAsErrors`
fails the build on any finding.

Opengrep doesn't document Visual Basic support, so it isn't listed here. The
.NET analyzers are the only FOSS security analysis for Visual Basic source.

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

lizard doesn't support Visual Basic, so the .NET code-metrics rule `CA1502`
enforces the complexity limit: any method with a cyclomatic complexity over
10 fails the build. A method past the limit is hard to test and should be
split.

The `.editorconfig` above turns the rule on, `CodeMetricsConfig.txt` sets the
threshold with the line `CA1502: 10`, and `Directory.Build.props` adds that
file to every project.

No FOSS tool limits method length for Visual Basic, so reviewers check that
methods stay under 60 lines.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format vbnet --min-tokens 50 --exit-code 1 src/
```

`.jscpd.json` holds the same settings, so `jscpd src/` alone runs the same
check.

### Dead code

The `.editorconfig` above raises the code-style rules for unused code to
warnings, so `EnforceCodeStyleInBuild` and `TreatWarningsAsErrors` fail the
build on them: an unused private member (`IDE0051`), a private member that's
never read (`IDE0052`) and an unused parameter (`IDE0060`).

The compiler already warns about unused local variables, and `IDE0005` above
catches unused `Imports` statements. No FOSS tool finds unused `Public`
members across a whole solution, because outside code may call them.

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
