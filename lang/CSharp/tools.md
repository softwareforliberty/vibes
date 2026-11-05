# C# Tools

The free/open source tools that lint, format and check C# code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [.NET SDK](https://github.com/dotnet/sdk) (C# compiler and .NET code analyzers) | MIT | Linting, Auditing, Code quality | Compiling, nullable checks, and code-style, quality and security analysis |
| [dotnet format](https://github.com/dotnet/format) (in the .NET SDK) | MIT | Formatting | Applying the `.editorconfig` formatting and code-style fixes |
| [NuGet Audit](https://learn.microsoft.com/nuget/concepts/auditing-packages) (in the .NET SDK) | Apache-2.0 | Auditing | Checking restored packages against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [coverlet](https://github.com/coverlet-coverage/coverlet) | MIT | Code quality | Measuring test coverage, and failing the build below a minimum |

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
<Project>
  <PropertyGroup>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <AnalysisLevel>latest-recommended</AnalysisLevel>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
    <NuGetAudit>true</NuGetAudit>
    <NuGetAuditMode>all</NuGetAuditMode>
    <NuGetAuditLevel>low</NuGetAuditLevel>
  </PropertyGroup>
</Project>
```

- `TreatWarningsAsErrors` turns every compiler, nullable, analyzer and NuGet
  Audit warning into a build failure.
- `AnalysisLevel` turns on the recommended set of .NET code-quality rules
  (`CAxxxx`).
- `EnforceCodeStyleInBuild` makes the code-style rules (`IDExxxx`) run during
  the build, not just in the editor.
- `GenerateDocumentationFile` makes the compiler report public members with
  no XML documentation, and lets `IDE0005` find unused `using` directives.

Put the formatting and code-style rules in `.editorconfig`, which both
`dotnet format` and the build read:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.cs]
indent_style = space
indent_size = 4

# Usings
dotnet_sort_system_directives_first = true
dotnet_diagnostic.IDE0005.severity = warning

# Layout and braces
csharp_new_line_before_open_brace = all
csharp_prefer_braces = true:warning
csharp_style_namespace_declarations = file_scoped:warning

# Declarations
dotnet_style_qualification_for_field = false:warning
dotnet_style_qualification_for_property = false:warning
dotnet_style_qualification_for_method = false:warning
dotnet_style_predefined_type_for_locals_parameters_members = true:warning
dotnet_style_require_accessibility_modifiers = always:warning
csharp_style_var_for_built_in_types = false:warning
csharp_style_var_when_type_is_apparent = true:warning
csharp_style_var_elsewhere = false:warning

# Naming: PascalCase constants, s_camelCase static fields,
# _camelCase instance fields
dotnet_naming_rule.constants.symbols = constants
dotnet_naming_rule.constants.style = pascal_case
dotnet_naming_rule.constants.severity = warning
dotnet_naming_symbols.constants.applicable_kinds = field, local
dotnet_naming_symbols.constants.required_modifiers = const
dotnet_naming_style.pascal_case.capitalization = pascal_case

dotnet_naming_rule.static_fields.symbols = static_fields
dotnet_naming_rule.static_fields.style = s_camel_case
dotnet_naming_rule.static_fields.severity = warning
dotnet_naming_symbols.static_fields.applicable_kinds = field
dotnet_naming_symbols.static_fields.applicable_accessibilities = private, internal
dotnet_naming_symbols.static_fields.required_modifiers = static
dotnet_naming_style.s_camel_case.required_prefix = s_
dotnet_naming_style.s_camel_case.capitalization = camel_case

dotnet_naming_rule.instance_fields.symbols = instance_fields
dotnet_naming_rule.instance_fields.style = underscore_camel_case
dotnet_naming_rule.instance_fields.severity = warning
dotnet_naming_symbols.instance_fields.applicable_kinds = field
dotnet_naming_symbols.instance_fields.applicable_accessibilities = private, internal
dotnet_naming_style.underscore_camel_case.required_prefix = _
dotnet_naming_style.underscore_camel_case.capitalization = camel_case

# Security rules as build failures
dotnet_analyzer_diagnostic.category-Security.severity = warning
```

- The constants rule comes first, so `const` fields get `PascalCase` rather
  than a field prefix.
- Never hand-format code the formatter will rewrite. Run
  `dotnet format` before every commit.

## Auditing

### Security analysis

The .NET SDK ships security analyzers (`CA2100`, `CA3xxx`, `CA5xxx`) that
find SQL injection, insecure deserialisation, weak cryptography and similar
bugs. The `.editorconfig` above raises the whole Security category to
warnings, so `TreatWarningsAsErrors` fails the build on any finding.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

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

Fail the build on any function with a cyclomatic complexity over 10 or more
than 60 lines of code. A function past either limit is hard to test and
should be split.

```sh
lizard -l csharp -C 10 -L 60 -w src/
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format csharp --min-tokens 50 --exitCode 1 src/
```

### Dead code

Turn on the code-style rules for unused code, so `EnforceCodeStyleInBuild`
and `TreatWarningsAsErrors` fail the build on them:

```ini
[*.cs]
# Unused private member
dotnet_diagnostic.IDE0051.severity = warning
# Private member never read
dotnet_diagnostic.IDE0052.severity = warning
# Unused parameter
dotnet_diagnostic.IDE0060.severity = warning
```

The compiler already warns about unused local variables (`CS0168`,
`CS0219`), and `IDE0005` above catches unused `using` directives. No FOSS
tool finds unused `public` members across a whole solution, because outside
code may call them.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Add the `coverlet.msbuild` package to each test project, then:

```sh
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura \
    /p:Threshold=80 /p:ThresholdType=branch /p:ThresholdStat=total
```
