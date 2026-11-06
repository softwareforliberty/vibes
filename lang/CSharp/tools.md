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

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, `dotnet format` and the .NET analyzers |
| [`Directory.Build.props`](Directory.Build.props) | MSBuild, for every project in the repository |
| [`.opengrep/csharp.yaml`](.opengrep/csharp.yaml) | Opengrep: starter rules for the [security idioms](idioms.md#security) |
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

  <!-- Coverage minimum for projects that reference coverlet.msbuild -->
  <PropertyGroup>
    <CoverletOutputFormat>cobertura</CoverletOutputFormat>
    <Threshold>80</Threshold>
    <ThresholdType>branch</ThresholdType>
    <ThresholdStat>total</ThresholdStat>
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
- The second group sets coverlet's coverage minimum for every test project
  (see [Coverage](#coverage)).

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

[*.cs]
indent_style = space
indent_size = 4
max_line_length = 120

# .NET code style and analyzers: read by dotnet format, the build
# (EnforceCodeStyleInBuild), Visual Studio and VS Code with C# Dev Kit.
# Each enforced rule sets both the option's severity and the matching
# dotnet_diagnostic severity, so the IDE and the build agree.

# Usings
dotnet_sort_system_directives_first = true
dotnet_separate_import_directive_groups = false
csharp_using_directive_placement = outside_namespace:warning
dotnet_diagnostic.IDE0065.severity = warning
dotnet_diagnostic.IDE0005.severity = warning

# Layout and braces
csharp_new_line_before_open_brace = all
csharp_new_line_before_else = true
csharp_new_line_before_catch = true
csharp_new_line_before_finally = true
csharp_indent_case_contents = true
csharp_indent_switch_labels = true
csharp_preserve_single_line_statements = false
csharp_preserve_single_line_blocks = true
csharp_prefer_braces = true:warning
dotnet_diagnostic.IDE0011.severity = warning
csharp_style_namespace_declarations = file_scoped:warning
dotnet_diagnostic.IDE0161.severity = warning

# Spacing
csharp_space_after_keywords_in_control_flow_statements = true
csharp_space_between_method_call_name_and_opening_parenthesis = false
csharp_space_between_method_declaration_name_and_open_parenthesis = false
csharp_space_between_parentheses = false
csharp_space_around_binary_operators = before_and_after
csharp_space_after_comma = true
csharp_space_before_comma = false
csharp_space_after_semicolon_in_for_statement = true
csharp_space_before_semicolon_in_for_statement = false
csharp_space_after_cast = false

# Declarations (IDE0036 checks the default modifier order: public static, not
# static public)
dotnet_style_require_accessibility_modifiers = always:warning
dotnet_diagnostic.IDE0040.severity = warning
dotnet_diagnostic.IDE0036.severity = warning
csharp_style_var_for_built_in_types = false:warning
csharp_style_var_when_type_is_apparent = true:warning
csharp_style_var_elsewhere = false:warning
dotnet_diagnostic.IDE0007.severity = warning
dotnet_diagnostic.IDE0008.severity = warning
csharp_style_implicit_object_creation_when_type_is_apparent = true:warning
dotnet_diagnostic.IDE0090.severity = warning
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
csharp_style_prefer_primary_constructors = true:suggestion
csharp_style_expression_bodied_methods = when_on_single_line:silent
csharp_style_expression_bodied_properties = true:silent
csharp_style_expression_bodied_accessors = true:silent
csharp_style_expression_bodied_constructors = false:silent

# Expressions
dotnet_style_prefer_is_null_check_over_reference_equality_method = true:warning
dotnet_diagnostic.IDE0041.severity = warning
csharp_style_prefer_not_pattern = true:warning
dotnet_diagnostic.IDE0083.severity = warning
dotnet_style_coalesce_expression = true:warning
dotnet_diagnostic.IDE0029.severity = warning
dotnet_diagnostic.IDE0030.severity = warning
dotnet_style_null_propagation = true:warning
dotnet_diagnostic.IDE0031.severity = warning
csharp_style_prefer_switch_expression = true:suggestion

# Naming: PascalCase constants, I-prefixed interfaces, s_camelCase static
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

# Unused code: private member never used (IDE0051), never read (IDE0052),
# unused parameter (IDE0060)
dotnet_diagnostic.IDE0051.severity = warning
dotnet_diagnostic.IDE0052.severity = warning
dotnet_diagnostic.IDE0060.severity = warning

# Security rules as build failures
dotnet_analyzer_diagnostic.category-Security.severity = warning

# JetBrains Rider reads the standard, dotnet_* and csharp_* properties above,
# so it needs no resharper_* keys.

# Test method names may use underscores between scenario parts, so CA1707 is
# off in test classes, which are named *Tests.
[*Tests.cs]
dotnet_diagnostic.CA1707.severity = none

[*.json]
indent_style = space
indent_size = 2
max_line_length = 80

[*.{yaml,yml}]
indent_style = space
indent_size = 2
max_line_length = 80
# JetBrains IDEs
ij_yaml_align_values_properties = do_not_align
ij_yaml_autoinsert_sequence_marker = true
ij_yaml_block_mapping_on_new_line = false
ij_yaml_indent_sequence_value = true
ij_yaml_keep_indents_on_empty_lines = false
ij_yaml_keep_line_breaks = true
ij_yaml_sequence_on_new_line = false
ij_yaml_space_before_colon = false
ij_yaml_spaces_within_braces = false
ij_yaml_spaces_within_brackets = false
```

- Each enforced rule sets both the option's severity (read by the editor)
  and the matching `dotnet_diagnostic` severity (read by the build), so the
  two always agree.
- The constants rule comes first, so `const` fields get `PascalCase` rather
  than a field prefix.
- The build doesn't run every rule: `this.` qualification (`IDE0003`), BCL
  type names (`IDE0049`) and whitespace are reported only by
  `dotnet format --verify-no-changes`, so run both commands.
- The `[*Tests.cs]` section turns off `CA1707`, so test method names can use
  underscores, as [coding-style.md](coding-style.md#naming) allows.
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

`.jscpd.json` holds the same settings, so `jscpd src/` alone runs the same
check.

### Dead code

The `.editorconfig` above raises the code-style rules for unused code to
warnings, so `EnforceCodeStyleInBuild` and `TreatWarningsAsErrors` fail the
build on them: an unused private member (`IDE0051`), a private member that's
never read (`IDE0052`) and an unused parameter (`IDE0060`).

The compiler already warns about unused local variables (`CS0168`,
`CS0219`), and `IDE0005` above catches unused `using` directives. No FOSS
tool finds unused `public` members across a whole solution, because outside
code may call them.

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
