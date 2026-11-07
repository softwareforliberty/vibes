# PowerShell Idioms and Principles

How to write PowerShell well. [coding-style.md](coding-style.md) covers how
code looks. This guide covers how it's designed: the idioms and principles
that keep PowerShell code correct, safe and maintainable. Every example
follows the style guide.

## Principles

- **Objects, not text.** PowerShell pipes objects. Keep data as objects
  until the very end, and never parse the formatted output of another
  command.
- **Behave like a cmdlet.** A function that takes pipeline input, supports
  common parameters and writes errors properly fits into the rest of the
  shell without surprises.
- **Fail loudly.** Make errors terminating where the script can't continue,
  and report them with context.
- **Keep scope small.** Variables live in the narrowest scope that works,
  and functions never change the caller's state without saying so.
- **Never run text as code.** Build commands from parameters, not from
  strings.

## Functions

- **Write advanced functions.** `[CmdletBinding()]` gives a function the
  common parameters (`-Verbose`, `-ErrorAction`, `-WhatIf` and the rest)
  for free, so it behaves like a built-in cmdlet.
- **Accept pipeline input** where it makes sense, with
  `ValueFromPipeline` or `ValueFromPipelineByPropertyName`, and do the
  per-item work in a `process` block. Setup goes in `begin`, cleanup in
  `end`.
- **Validate parameters with attributes**, not with code in the body:
  `[ValidateNotNullOrEmpty()]`, `[ValidateRange(1, 100)]`,
  `[ValidateSet('Json', 'Csv')]`. PowerShell then rejects bad input before
  the function runs, with a consistent error.
- **Support `-WhatIf` and `-Confirm` on anything that changes state.**
  Declare `SupportsShouldProcess` and wrap each change in a
  `ShouldProcess` check:

  ```powershell
  function Remove-StaleReport {
      [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
      param (
          [Parameter(Mandatory, ValueFromPipelineByPropertyName)]
          [string]
          $Path
      )

      process {
          if ($PSCmdlet.ShouldProcess($Path, 'Remove report')) {
              Remove-Item -LiteralPath $Path
          }
      }
  }
  ```

- **Use `[switch]` for on/off options**, never `[bool]`. A switch reads as
  `-Force` at the call site instead of `-Force $true`.

## Output

- **Return objects, one at a time.** Emit each result to the pipeline as
  it's ready. Build `[pscustomobject]` results with named properties:

  ```powershell
  [pscustomobject]@{
      Name  = $user.Name
      Email = $user.Email
  }
  ```

- **Don't use `return` to emit output.** Everything a function writes to the
  output stream is returned, so `return $x` only adds a misleading sense
  that nothing else is. Use `return` alone to exit early.
- **Silence unwanted output** from calls whose result you don't need with
  `$null = ...`. Stray values otherwise end up in the function's output.
- **Use the right stream.** `Write-Verbose` for progress detail,
  `Write-Warning` for problems that don't stop the work, `Write-Error` for
  failures. Never use `Write-Host` for data; it can't be captured or piped.
- **Format only at the end.** `Format-Table` and `Format-List` turn objects
  into display text, so they belong in the caller, never in a function's
  output.

## Errors

- **Set `$ErrorActionPreference = 'Stop'` at the top of scripts**, so every
  error is terminating and a failed step can't be silently skipped. Also set
  `Set-StrictMode -Version Latest`, which turns uninitialised variables and
  missing properties into errors.
- **Catch errors with `try`/`catch` only where something can be done** about
  them: retry, fall back, or report to the user. Lower levels let them
  propagate.
- **Catch specific exception types** when you handle an error, and rethrow
  (`throw`) the rest:

  ```powershell
  try {
      $content = Get-Content -LiteralPath $path -Raw
  } catch [System.Management.Automation.ItemNotFoundException] {
      Write-Warning "No report at '$path'."
      return
  }
  ```

- **Report failures with `$PSCmdlet.WriteError()` or
  `$PSCmdlet.ThrowTerminatingError()`** in advanced functions. They attach
  the error to the right command, so callers' `-ErrorAction` works.
- **Check `$LASTEXITCODE` after every native command.** Native programs
  don't raise PowerShell errors when they fail.

## Variables and scope

- **Don't use global variables.** Keep module state in `$script:` scope,
  behind the module's functions.
- **Don't change the caller's state.** Avoid `Set-Location` in functions;
  use full paths, or `Push-Location` and `Pop-Location` in a `try`/`finally`.
- **Use `-LiteralPath` for paths that come from data.** `-Path` treats `[`
  and `*` as wildcards, so a file name containing them matches the wrong
  files.

## Modules

- **Ship code as a module** with a manifest (`.psd1`) that lists its
  version, its required PowerShell version and its exported functions.
  Export functions explicitly with `FunctionsToExport`, never with `*`, so
  module loading stays fast and the public API is deliberate.
- **Pin required modules** to an exact version in `RequiredModules`, so
  every machine loads the same code.

## Security

- **Never use `Invoke-Expression`.** It runs whatever string it's given.
  Call commands directly, use the call operator (`&`) with an argument list,
  or use splatting:

  ```powershell
  & git log -- $path
  ```

- **Pass native command arguments as separate values**, never as one string
  built from input.
- **Keep secrets in `[SecureString]` or `[PSCredential]` parameters**, never
  in plain-text strings, and never write them to logs or the console.
  Load them from a secret store, not from files in the repository.
- **Sign scripts** where the execution policy requires it, and never tell
  users to run with `-ExecutionPolicy Bypass` as a fix.
- **Validate input at the boundary** with parameter validation attributes,
  so the rest of the code can trust it.

## Testable design

- **Write tests with Pester** in `.Tests.ps1` files next to the code, or
  under `tests/`.
- **Pass dependencies in, or wrap them in a function.** Pester can mock a
  function you own more easily than a .NET call deep inside your code.
- **Keep I/O at the edges.** Functions that transform objects are easy to
  test; the code that reads and writes stays thin.

## Performance

- **Measure before optimising**, with `Measure-Command`.
- **Don't grow arrays with `+=` in a loop.** Each `+=` copies the whole
  array. Collect loop output directly (`$results = foreach (...) { ... }`)
  or use a `[System.Collections.Generic.List[object]]`.
- **Filter as early as possible.** Use a command's own `-Filter` parameter
  rather than piping everything to `Where-Object`.
- **Read large files with `switch -File` or `[System.IO.File]::ReadLines()`,**
  which stream lines far faster than `Get-Content`. `Get-Content -Raw` reads
  the whole file into memory.

## Sources

- [PowerShell Practice and Style](https://poshcode.gitbook.io/powershell-practice-and-style/)
- [about_Functions_Advanced](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_functions_advanced)
- [about_Preference_Variables](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_preference_variables)
- [Everything you wanted to know about ShouldProcess](https://learn.microsoft.com/powershell/scripting/learn/deep-dives/everything-about-shouldprocess)
- [PSScriptAnalyzer rules](https://learn.microsoft.com/powershell/utility-modules/psscriptanalyzer/rules/readme)
