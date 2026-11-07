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

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`PSScriptAnalyzerSettings.psd1`](PSScriptAnalyzerSettings.psd1) | PSScriptAnalyzer and `Invoke-Formatter` |
| [`PesterConfiguration.psd1`](PesterConfiguration.psd1) | Pester |
| [`.jscpd.json`](.jscpd.json) | jscpd |

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
