# PowerShell Tools

The free/open source tools that lint, format and check PowerShell code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) | MIT | Formatting, Linting, Auditing | Formatting (`Invoke-Formatter`), linting and security rules |
| [Pester](https://github.com/pester/Pester) | Apache-2.0 | Code quality | Running tests and measuring coverage |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [PSMutant](https://github.com/Fortigi/PSMutant) | MIT | Code quality | Mutation testing |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`PSScriptAnalyzerSettings.psd1`](PSScriptAnalyzerSettings.psd1) | PSScriptAnalyzer and `Invoke-Formatter` |
| [`PesterConfiguration.psd1`](PesterConfiguration.psd1) | Pester |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`psmutant.config.json`](psmutant.config.json) | PSMutant |

## Formatting

PSScriptAnalyzer's `Invoke-Formatter` owns layout, using the same settings
file as the linter. Format a file in place:

```powershell
$path = './src/Get-UserReport.ps1'
$text = Get-Content -LiteralPath $path -Raw
Invoke-Formatter -ScriptDefinition $text -Settings ./PSScriptAnalyzerSettings.psd1 |
    Set-Content -LiteralPath $path -NoNewline
```

Don't hand-format code the formatter will rewrite, and don't argue with its
output in review. The [linting](#linting) gate fails on anything the
formatter would change, because the formatting rules are part of its
settings.

## Linting

Code must pass PSScriptAnalyzer with **no errors, warnings or information
messages**. `-EnableExit` makes the command's exit code the number of
problems found:

```powershell
Invoke-ScriptAnalyzer -Path . -Recurse -Settings ./PSScriptAnalyzerSettings.psd1 -EnableExit
```

Put the settings in `PSScriptAnalyzerSettings.psd1`. The default rules stay
on, and the formatting rules that are off by default are turned on to match
the [style guide](coding-style.md):

```powershell
@{
    Severity            = @('Error', 'Warning', 'Information')
    IncludeDefaultRules = $true
    Rules               = @{
        PSPlaceOpenBrace                          = @{
            Enable             = $true
            OnSameLine         = $true
            NewLineAfter       = $true
            IgnoreOneLineBlock = $true
        }
        PSPlaceCloseBrace                         = @{
            Enable             = $true
            NewLineAfter       = $false
            IgnoreOneLineBlock = $true
            NoEmptyLineBefore  = $false
        }
        PSUseConsistentIndentation                = @{
            Enable          = $true
            Kind            = 'space'
            IndentationSize = 4
        }
        PSUseConsistentWhitespace                 = @{
            Enable                                  = $true
            CheckInnerBrace                         = $true
            CheckOpenBrace                          = $true
            CheckOpenParen                          = $true
            CheckOperator                           = $true
            CheckPipe                               = $true
            CheckSeparator                          = $true
            IgnoreAssignmentOperatorInsideHashTable = $true
        }
        PSAlignAssignmentStatement                = @{
            Enable         = $true
            CheckHashtable = $true
        }
        PSUseCorrectCasing                        = @{ Enable = $true }
        PSAvoidLongLines                          = @{
            Enable            = $true
            MaximumLineLength = 115
        }
        PSAvoidUsingDoubleQuotesForConstantString = @{ Enable = $true }
        PSAvoidSemicolonsAsLineTerminators        = @{ Enable = $true }
    }
}
```

`PSAlignAssignmentStatement` lines up the `=` signs of a multi-line
hashtable, and `IgnoreAssignmentOperatorInsideHashTable` stops
`PSUseConsistentWhitespace` from flagging the extra spaces that alignment
adds, so the two rules don't fight.

Never suppress a rule with `[Diagnostics.CodeAnalysis.SuppressMessageAttribute()]`
without a `Justification` that explains why.

## Auditing

### Security analysis

No Opengrep or other FOSS taint analyser supports PowerShell.
PSScriptAnalyzer's default rules are the closest check, and the
[linting](#linting) gate already runs the ones that catch the unsafe
patterns in [idioms.md](idioms.md#security):

- `PSAvoidUsingInvokeExpression` for running strings as code.
- `PSAvoidUsingPlainTextForPassword`,
  `PSAvoidUsingConvertToSecureStringWithPlainText` and
  `PSAvoidUsingUsernameAndPasswordParams` for secrets in plain text.
- `PSUsePSCredentialType` for credential parameters.
- `PSUseShouldProcessForStateChangingFunctions` for state-changing
  functions without `-WhatIf` support.

### Dependency vulnerabilities

No FOSS tool checks PowerShell Gallery modules against known
vulnerabilities, and the OSV database has no PowerShell Gallery ecosystem.
Pin every required module to an exact version in the module manifest's
`RequiredModules`, and review each module's release notes before upgrading
it.

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

No maintained FOSS tool measures the complexity of PowerShell functions, and
lizard doesn't support the language. Keep functions small instead: a
function that does more than one job, or grows past about 60 lines, should
be split into helper functions.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format powershell --min-tokens 50 --exit-code 1 src
```

### Dead code

PSScriptAnalyzer's `PSUseDeclaredVarsMoreThanAssignments` rule, on by
default, reports variables that are assigned but never used. No tool finds
unused functions, because PowerShell resolves commands by name at run time.

### Coverage

Measure command coverage on every test run, and fail the build when it
falls below 80%. Raise the minimum as coverage grows; never lower it to make
a build pass.

Pester measures which commands the tests run. Its settings are in
`PesterConfiguration.psd1`:

```powershell
@{
    Run          = @{
        Path     = './tests'
        PassThru = $true
    }
    CodeCoverage = @{
        Enabled               = $true
        Path                  = './src'
        CoveragePercentTarget = 80
    }
}
```

`CoveragePercentTarget` only reports against the target, so check the result
in CI:

```powershell
$settings = Import-PowerShellDataFile -Path ./PesterConfiguration.psd1
$config = New-PesterConfiguration -Hashtable $settings

$result = Invoke-Pester -Configuration $config
if ($result.FailedCount -gt 0) {
    exit 1
}
if ($result.CodeCoverage.CoveragePercent -lt 80) {
    exit 1
}
```

### Mutation testing

PSMutant makes small changes to the code, such as turning `-ge` into `-gt`, and
runs the Pester tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. It reads the code with
PowerShell's own parser, and runs each mutant in a copy of `src` and `tests`,
so the source files are never changed.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch, and skips the run when there are none. `ExitCode` is
non-zero when the mutation score is below the minimum:

```powershell
$changed = @(git diff --name-only --diff-filter=d origin/main... -- 'src/*.ps1')
if ($changed.Count -gt 0) {
    $result = Invoke-PSMutation -ConfigFile ./psmutant.config.json -ChangedFile $changed
    exit $result.ExitCode
}
```

Install it from the PowerShell Gallery. It's young, first released in 2026, so
pin the version this guide was checked with, PSMutant 0.9.1 with Pester 5.7.1,
and recheck this page when you upgrade:

```powershell
Install-Module PSMutant -RequiredVersion 0.9.1 -Scope CurrentUser
```

The settings are in [`psmutant.config.json`](psmutant.config.json):

```json
{
  "mutate": ["src/**/*.ps1"],
  "tests": {},
  "testsByConvention": true,
  "operators": [
    "BinaryOperator",
    "BooleanLiteral",
    "NumberLiteral",
    "NegationRemoval",
    "ConditionalBoundary",
    "ConditionForcing",
    "ReturnValue"
  ],
  "thresholds": { "high": 90, "low": 80, "break": 80 },
  "reportPath": "reports/ps-mutation.json"
}
```

- `testsByConvention` runs `tests/Name.Tests.ps1` against `src/Name.ps1`, so
  the map in `tests` can stay empty.
- `operators` adds `ConditionalBoundary`, `ConditionForcing` and `ReturnValue`
  to the four defaults. A boundary mutant, such as `-ge` into `-gt`, finds the
  off-by-one cases tests miss most often, and forcing a condition finds an `if`
  with no comparison in it that no test checks.
- `break` fails the run when the score is under 80%. The `high` and `low` bands
  only colour the score.
- Add `reports/` to `.gitignore`.

80% is the same bar as coverage. Some mutants can't change what the code does,
so 100% is rarely reachable; 80% leaves room for them and still fails a change
whose tests check little.

The summary lists each survivor with its line and the change:

```text
  Mutation score: 69.2%  (9 killed / 13)
  Survivors (add assertions to kill these):
    src/Grade.ps1:13  -ge -> -gt
    src/Grade.ps1:13  90 -> 91
    src/Grade.ps1:16  -ge -> -gt
    src/Grade.ps1:16  50 -> 51
```

Read it as a missing test: here, no test passes exactly 90 or 50, so neither
boundary is pinned down. Write the test that fails on the mutant, not one that
just runs the line. If a mutant can't change behaviour, declare it in
`equivalents` with the reason, rather than writing a test that contorts the
code; the run fails when a declaration goes stale.

### Architecture

PowerShell's modules don't enforce layers. A module can call any command
imported into the session, so the core can call an edge's function without
importing it. And exporting doesn't hide: Microsoft's documentation says it
"does not hide the members", and the call operator, `&`, can run any
function in a module's scope. Pester's `InModuleScope` exists to reach the
functions a module doesn't export. So the manifests declare each layer's
front door, and a script in `scripts/check` enforces the rest, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks.

Make each layer a module, in its own folder under `src`. The names are
examples: replace them with the layers in the project's `design.md`.

```text
src/AppCore/AppCore.psd1                  the core's manifest
src/AppCore/AppCore.psm1                  its root module
src/AppCore/Private/Format-CoreTitle.ps1  a function it doesn't export
src/AppAdapters/AppAdapters.psd1          an edge
src/AppCli/AppCli.psd1                    another edge
tests/AppCore.Tests.ps1                   the core's tests
```

- A module's manifest is its front door. `FunctionsToExport` lists each
  entry point by name. Without it, the module exports every function, and
  a wildcard exports every function that matches.
- Other modules, and the module's own tests, import it only through its
  manifest, and call only what it exports. Importing the `.psm1` itself
  skips the manifest: with no `Export-ModuleMember`, every function is
  exported.
- The core imports no edge and calls none of an edge's functions. An edge
  may use the core.
- Give every function the module's noun prefix, such as `Format-CoreTitle`
  (see [Naming](coding-style.md#naming)), so no two modules share a name.

`src/AppCore/AppCore.psd1`:

```powershell
@{
    RootModule        = 'AppCore.psm1'
    ModuleVersion     = '0.1.0'
    GUID              = '0b9f5a3e-7c1d-4f7e-9a51-3d2c6e8b4f10'
    FunctionsToExport = @('Get-Greeting')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
}
```

Save the check as `scripts/Test-Architecture.ps1`, and run it from
`scripts/check`. It exits 1, and prints the file and line of each breach:

```sh
pwsh -NoProfile -File scripts/Test-Architecture.ps1
```

```powershell
#Requires -Version 7.4
using namespace System.Management.Automation.Language

# Prints the file and line of each breach of a layer or a module's front
# door, and fails if there are any.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# The modules, core first. Replace them with the layers in design.md.
$core = 'AppCore'
$edges = @('AppAdapters', 'AppCli')
$found = [System.Collections.Generic.List[string]]::new()

function Join-Name {
    # A pattern that matches any of the names as a whole word.
    param([string[]]$Name)
    $escaped = $Name | ForEach-Object { [regex]::Escape($_) }
    '(?<![\w-])(' + ($escaped -join '|') + ')(?![\w-])'
}

function Add-Breach {
    # Records each line of code in the files that matches the pattern.
    param([string[]]$Path, [string]$Pattern, [string]$Rule)
    foreach ($file in $Path) {
        $tokens = $null
        $null = [Parser]::ParseFile($file, [ref]$tokens, [ref]$null)
        foreach ($token in $tokens) {
            $comment = $token.Kind -eq 'Comment'
            if ($comment -and $token.Text -notmatch '^#requires') {
                continue
            }
            if ($token.Text -match $Pattern) {
                $where = Resolve-Path -LiteralPath $file -Relative
                $line = $token.Extent.StartLineNumber
                $found.Add("${where}:${line}: $Rule")
            }
        }
    }
}

$all = @(Get-ChildItem -Path 'src', 'tests' -Recurse -File -Include @(
        '*.ps1', '*.psm1', '*.psd1')).FullName
$files = @{}
$exports = @{}
foreach ($name in @($core) + $edges) {
    $files[$name] = @($all -like "*[\/]src[\/]$name[\/]*")
    $manifest = "src/$name/$name.psd1"
    $data = Import-PowerShellDataFile -LiteralPath $manifest
    $exports[$name] = @($data['FunctionsToExport'] |
            Where-Object { $_ -notmatch '^$|\*' })
    $rule = "list what $name exports by name"
    if (-not $data.ContainsKey('FunctionsToExport')) {
        $found.Add("./${manifest}:1: $rule")
    }
    Add-Breach -Path $manifest -Pattern '^[''"].*\*' -Rule $rule
}

# The core never names an edge, or a function an edge exports.
foreach ($edge in $edges) {
    $pattern = Join-Name -Name (@($edge) + $exports[$edge])
    $rule = "the core must not use $edge"
    Add-Breach -Path $files[$core] -Pattern $pattern -Rule $rule
}

# Code outside a module names no file in it but its manifest, and none
# of the functions it doesn't export.
foreach ($name in $files.Keys) {
    $pattern = "(?<![\w-])$name[\\/](?!$name\.psd1)"
    $private = foreach ($file in $files[$name]) {
        $ast = [Parser]::ParseFile($file, [ref]$null, [ref]$null)
        $ast.FindAll({ $args[0] -is [FunctionDefinitionAst] }, $true) |
            Where-Object Name -NotIn $exports[$name] |
            ForEach-Object Name
    }
    if ($private) {
        $pattern += '|' + (Join-Name -Name $private)
    }
    $outside = $all | Where-Object { $_ -notin $files[$name] }
    $rule = "use $name only through its manifest and exports"
    Add-Breach -Path $outside -Pattern $pattern -Rule $rule
}

$rule = 'InModuleScope reaches past a module''s exports'
Add-Breach -Path $all -Pattern '^InModuleScope$' -Rule $rule

$found | Select-Object -Unique
if ($found.Count -gt 0) {
    exit 1
}
```

It reads each file with PowerShell's own parser, so comments don't count,
but `#Requires` lines do. It searches `src` and `tests`; add any other
folder that holds code.

- Each manifest must list `FunctionsToExport`, and no string in it may
  hold a wildcard, so `VariablesToExport = '*'` fails too.
- The core must not name an edge or a function the edge exports. That
  catches `Import-Module`, `using module`, `#Requires -Modules`,
  `RequiredModules` and a call such as `AppAdapters\Write-Console`, or
  just `Write-Console`.
- Code outside a module, its tests included, must not name a file in the
  module's folder other than its manifest, such as its `.psm1` or a
  `Private` file. Nor may it name a function the module doesn't export, so
  `& (Get-Module AppCore) { Format-CoreTitle }` fails too.
- No file may use `InModuleScope`.

A breach prints:

```text
./src/AppCore/Get-CoreBreach.ps1:5: the core must not use AppAdapters
```

The check reads names, so it misses one built at run time, such as
`& ('Format-Core' + 'Title')`, a command found with `Get-Command`, and a
path joined from parts, such as `Join-Path 'AppCore' 'Private'`. Review
catches the rest.

Prove the rules bite, as the
[builder](../../../agents/builder.md) does, with a new file that breaks
one. Kept as `scripts/breaches/core-uses-edge.patch`, the breach for the
layer rule is:

```text
Rule: the core never uses an edge
Fails with: the core must not use AppAdapters
diff --git a/src/AppCore/Get-CoreBreach.ps1 b/src/AppCore/Get-CoreBreach.ps1
new file mode 100644
index 0000000..75123b4
--- /dev/null
+++ b/src/AppCore/Get-CoreBreach.ps1
@@ -0,0 +1,6 @@
+#Requires -Version 7.4
+
+# A breach: the core calls an edge.
+function Get-CoreBreach {
+    Write-Console -Text 'breach'
+}
```

The breach passes PSScriptAnalyzer, so `scripts/check` fails on the layer
rule and not on a lint error first. To let one existing breach through,
leave its file out of that rule's `-Path`, with a comment naming the breach
and how to fix it.

## Sources

- [PSMutant](https://github.com/Fortigi/PSMutant/blob/v0.9.1/README.md)
- [PSMutant on the PowerShell Gallery](https://www.powershellgallery.com/packages/PSMutant/0.9.1)
- [Export-ModuleMember](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/export-modulemember)
- [about_Module_Manifests](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_module_manifests)
- [Pester: InModuleScope](https://pester.dev/docs/commands/InModuleScope)
