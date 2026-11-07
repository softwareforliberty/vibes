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

## Sources

- [PSMutant](https://github.com/Fortigi/PSMutant/blob/v0.9.1/README.md)
- [PSMutant on the PowerShell Gallery](https://www.powershellgallery.com/packages/PSMutant/0.9.1)
