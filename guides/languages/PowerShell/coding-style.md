# PowerShell Coding Style

A general-purpose coding style for PowerShell projects. It builds on the
[PowerShell Practice and Style guide](https://poshcode.gitbook.io/powershell-practice-and-style/)
from PoshCode, with the layout checked by
[PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(functions, the pipeline, errors, security and other idioms), see
[idioms.md](idioms.md).

The tools that check PowerShell code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **PowerShell 7.4**, the cross-platform,
MIT-licensed edition. It's a long-term-support release, and it adds the
ternary (`? :`), pipeline chain (`&&`, `||`) and null-coalescing (`??`)
operators that this guide relies on.

Every script and module states the requirement on its first line, so older
hosts fail with a clear message:

```powershell
#Requires -Version 7.4
```

Windows PowerShell 5.1 is out of scope. Code that must also run there can't
use the operators above.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs.
- When a command has more than a few parameters, use splatting instead of a
  long line or backtick continuations (see [Commands](#commands)).
- Never end a line with a backtick (`` ` ``) to continue it. A trailing
  space after the backtick silently breaks the continuation. Break lines
  after a pipe, an operator or an opening bracket instead.

### Line length

- Lines are at most **115 characters**. PSScriptAnalyzer enforces it.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8 without a byte-order mark, LF line endings, and end every file
  with a newline.
- No trailing whitespace.
- Scripts use `.ps1`, modules `.psm1`, module manifests `.psd1` and Pester
  tests `.Tests.ps1`.
- Name script and module files in `PascalCase`, matching the function or
  module they contain: `Get-UserReport.ps1`, `UserTools.psm1`.

### One thing per line

- One statement per line. Don't join statements with `;`.
- The body of an `if`, `foreach` or `while` goes on its own line, even when
  it's short.

## Braces

Use the "one true brace style": the opening brace goes at the end of the
line, and `else`, `elseif`, `catch` and `finally` follow the closing brace
on the same line:

```powershell
if ($user) {
    Send-Greeting -User $user
} else {
    Register-User
}
```

## Whitespace

- One space around operators, including comparison operators:
  `$total = $price * $count`, `if ($count -gt 0)`.
- One space after a comma, none before it.
- One space between a keyword and its parenthesis: `if ($x)`,
  `foreach ($item in $items)`.
- One space inside the braces of a one-line script block:
  `{ $_.Name }`. No spaces just inside parentheses.
- Line up the `=` signs of a multi-line hashtable, as in the splatting
  example under [Commands](#commands). The formatter does it for you.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Functions and cmdlets | `Verb-Noun`, approved verb, singular `PascalCase` noun | `Get-UserReport` |
| Parameters | `PascalCase` | `-UserName`, `-TimeoutSeconds` |
| Modules, classes and enums | `PascalCase` | `UserTools`, `ReportFormat` |
| Local variables | `camelCase` | `$retryCount` |
| Script- and module-scope variables | `PascalCase` with the `script:` scope | `$script:Cache` |

- Use only the approved verbs that `Get-Verb` lists. Users discover commands
  by verb, and PowerShell warns on import when a module uses others.
- Use singular nouns: `Get-User`, not `Get-Users`. The command may still
  return many objects.
- Prefix the nouns in a module with a short module-specific prefix when they
  could clash with other modules: `Get-ContosoUser`.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Commands

- Write the **full command name**, never an alias: `Get-ChildItem`, not
  `gci` or `ls`. Aliases differ between platforms and hosts, and they hide
  what the command is.
- Write **parameter names in full**, never positional or abbreviated:
  `Get-ChildItem -Path $dir -Filter '*.log'`. The call then reads the same
  to everyone and survives new parameters.
- Use **splatting** when a call needs more than three or four parameters:

  ```powershell
  $params = @{
      Uri         = $url
      Method      = 'Post'
      Body        = $body
      ContentType = 'application/json'
  }
  Invoke-RestMethod @params
  ```

- Write keywords and operators in lowercase: `if`, `foreach`, `function`,
  `-eq`, `-and`.
- Use the case-sensitive operators (`-ceq`, `-cmatch`) only when case
  matters, and say so in a comment.

## Strings

- Use **single quotes** for strings that don't interpolate, and double
  quotes only when they do. The quote then tells the reader whether to look
  for variables.
- Use the format operator or a subexpression for anything more than a plain
  variable: `"Found $($users.Count) users"`.
- Use a here-string (`@' ... '@` or `@" ... "@`) for multi-line text.

## Functions

- Write every function as an **advanced function**, with
  `[CmdletBinding()]` and a `param()` block (see
  [idioms.md](idioms.md#functions)).
- Put each parameter on its own line, with its attributes above it and its
  type in brackets:

  ```powershell
  function Get-UserReport {
      [CmdletBinding()]
      [OutputType([pscustomobject])]
      param (
          [Parameter(Mandatory, ValueFromPipeline)]
          [string]
          $UserName,

          [int]
          $TimeoutSeconds = 30
      )

      process {
          ...
      }
  }
  ```

- Declare the output type with `[OutputType()]`, so tab completion and
  readers know what the function returns.

## Comments and help

- Comments start with `# ` (hash and one space).
- Comments explain **why**, not **what**. The code already says what it
  does.
- Give every exported function **comment-based help** inside the function,
  above `[CmdletBinding()]`, with at least `.SYNOPSIS`, `.DESCRIPTION`, one
  `.PARAMETER` per parameter and an `.EXAMPLE`. `Get-Help` then documents
  it like any built-in cmdlet.
- Don't leave commented-out code. Version control keeps the history.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the PowerShell Practice and Style guide and borrows
from:

- [PowerShell Practice and Style](https://poshcode.gitbook.io/powershell-practice-and-style/)
- [Approved verbs for PowerShell commands](https://learn.microsoft.com/powershell/scripting/developer/cmdlet/approved-verbs-for-windows-powershell-commands)
- [about_Comment_Based_Help](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_comment_based_help)
- [PSScriptAnalyzer rules](https://learn.microsoft.com/powershell/utility-modules/psscriptanalyzer/rules/readme)
