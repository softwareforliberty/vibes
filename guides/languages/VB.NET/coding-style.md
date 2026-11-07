# Visual Basic Coding Style

A general-purpose coding style for Visual Basic projects on .NET. It builds on
Microsoft's
[Visual Basic coding conventions](https://learn.microsoft.com/dotnet/visual-basic/programming-guide/program-structure/coding-conventions),
and fills the gaps from the .NET Framework Design Guidelines (see
[Sources](#sources)). It covers Visual Basic on the open-source .NET SDK only;
VB6 and VBA are proprietary and out of scope.

This guide covers how code looks. For how to design and structure it
(`Option Strict`, `Nothing` handling, exceptions, async and other idioms), see
[idioms.md](idioms.md).

The tools that check Visual Basic code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **.NET 8 or later** and **Visual Basic 16.9**, the current
language version. Visual Basic no longer gets new syntax, so code uses the
features it has and calls newer .NET APIs as libraries.

Every project sets **`Option Strict On`**, **`Option Explicit On`** and
**`Option Infer On`**. Strict mode turns implicit narrowing conversions and
late binding into compile errors, so mistakes show up at build time instead
of in production.

## Source files

- Encode source files in **UTF-8**.
- Put **one top-level type per file**, and name the file after it:
  `OrderService.vb` holds `OrderService`.
- The folder path matches the namespace below the project's root namespace.

### Imports

- Put `Imports` statements at the top of the file, sorted alphabetically with
  `System` namespaces first. Every file then lists its dependencies in the
  same order.
- Remove unused `Imports` statements.
- Don't import the `Microsoft.VisualBasic` compatibility functions just to
  use them (see [idioms.md](idioms.md#legacy-features)).

## Layout

### Indentation

- Indent with **4 spaces** per level. Never use tabs.
- Write keywords the way the editor writes them, in `PascalCase`: `If`,
  `End If`, `Dim`, `Return`.

### Line length

- Keep lines to **120 columns**. Wide enough for descriptive .NET names,
  narrow enough for side-by-side diffs.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole.

### Line continuation

- **Never use the ` _` line-continuation character.** Visual Basic continues
  a statement implicitly after a comma, an opening parenthesis, an operator or
  a `.`, so break the line there:

  ```vb
  Dim names = orders.
      Where(Function(order) order.PlacedAt > cutoff).
      Select(Function(order) order.CustomerName).
      Distinct().
      ToList()
  ```

- Indent continuation lines by one level (4 spaces).

### Whitespace

- No trailing whitespace, and never more than one blank line in a row.
- One blank line between members of a type.
- End every file with a newline.

### One thing per line

- One statement per line. **Never join statements with `:`.**
- One variable per `Dim`: `Dim a, b As Integer` is never used.

## Blocks

- **Always use the multi-line form** of `If`. Don't write single-line
  `If condition Then statement`. A statement added later can't then fall
  outside the block by accident:

  ```vb
  If order.IsPaid Then
      Ship(order)
  Else
      Remind(order.Customer)
  End If
  ```

- Use `Select Case` instead of long `If`/`ElseIf` chains that test one value.
- Use `Exit Sub` and `Exit Function` sparingly; prefer `Return`.

## Spacing

- Put one space on each side of binary operators and `=`.
- No space between a method name and its `(`, and none just inside
  parentheses.
- Put a space after `,`, and none before it.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

Names follow the .NET Framework Design Guidelines, so code reads like the
.NET libraries it calls. Visual Basic is case-insensitive, so two names that
differ only in case are the same name; the field prefixes below keep fields
apart from the properties and parameters they back.

| Kind | Convention | Example |
| --- | --- | --- |
| Namespaces | `PascalCase`, dot-separated | `Example.Billing` |
| Types (classes, structures, modules, enums, delegates) | `PascalCase` nouns | `Order`, `PaymentGateway` |
| Interfaces | `I` + `PascalCase` | `IPaymentGateway` |
| Methods | `PascalCase` verbs | `SendInvoice()` |
| Properties, events, public fields | `PascalCase` | `Total`, `OrderPlaced` |
| Constants | `PascalCase` | `MaxRetries` |
| Private and friend instance fields | `_camelCase` | `_retryCount` |
| Private and friend `Shared` fields | `s_camelCase` | `s_defaultTimeout` |
| Parameters and locals | `camelCase` | `customer`, `retryCount` |
| Type parameters | `T`, or `T` + `PascalCase` | `T`, `TKey` |

- **Acronyms:** two-letter acronyms are all capitals (`IOStream`,
  `UIElement`); longer ones are written as words (`XmlReader`, `HttpClient`).
  In `camelCase`, a leading acronym is all lowercase (`ioStream`,
  `xmlReader`).
- Suffix asynchronous methods with **`Async`**: `SaveAsync()`.
- Name booleans as questions: `IsEmpty`, `HasChildren`, `CanRetry`.
- Don't use Hungarian notation, type prefixes (`strName`), or the `My`
  prefix for your own names.

## Declarations

- **Always write the access modifier**, even when it's the default. Put it
  first: `Public Shared`, not `Shared Public`.
- Declare local variables **where they're first needed**, and initialise them
  in the declaration.
- Let `Option Infer` choose the type only when it's obvious from the
  right-hand side (`Dim orders = New List(Of Order)()`). Write `As Type`
  otherwise.
- Use the **language keywords** for built-in types (`Integer`, `String`,
  `Object`), not the .NET names (`Int32`, `System.String`).
- Use `NameOf(x)` instead of the string `"x"`, so renames can't break it.
- Make fields **`ReadOnly`** whenever they're only set in the constructor.
- Don't qualify members with `Me.` unless a parameter shadows the member.

## Expressions

- Compare against `Nothing` with **`Is Nothing`** and **`IsNot Nothing`**.
- Use **`AndAlso`** and **`OrElse`**, which short-circuit. Use `And` and `Or`
  only for bitwise operations.
- Join strings with **`&`**, never `+`, which can silently add numbers. Prefer
  string interpolation (`$"Order {order.Id} shipped"`).
- Use the `If(value, default)` operator instead of `IIf`, which evaluates both
  arguments.
- Add parentheses whenever a reader might misread the precedence.
- Never ignore a caught exception silently. If doing nothing is genuinely
  right, explain why in a comment inside the `Catch` block.

## Comments

- Use `'` for comments, on their own line above the code they describe, not
  at the end of a line. Leave one space after `'`. Don't use `REM`.
- Comments explain **why**, not **what**. Rename or extract a method before
  writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `' TODO: reason`, and track the work somewhere it
  will be seen.

### XML documentation

Write `'''` XML documentation for every `Public` and `Protected` type and
member.

```vb
''' <summary>
''' Charges the customer's card for an order.
''' </summary>
''' <param name="order">The order to charge. Must not be paid already.</param>
''' <param name="cancellationToken">Cancels the charge request.</param>
''' <returns>The receipt for the charge.</returns>
''' <exception cref="PaymentException">The card was declined.</exception>
Public Async Function ChargeAsync(order As Order, cancellationToken As CancellationToken) As Task(Of Receipt)
```

- Start `<summary>` with a third-person verb phrase ("Charges…").
- Use `<inheritdoc/>` on overrides and interface implementations instead of
  copying the base documentation.

## Generated and third-party code

Generated sources (designer files) and vendored third-party code keep their
own format and are excluded from the formatter and analyzers, so regenerating
or updating them stays a clean replacement.

## Sources

This guide starts from Microsoft's Visual Basic coding conventions and
borrows from:

- [Visual Basic coding conventions](https://learn.microsoft.com/dotnet/visual-basic/programming-guide/program-structure/coding-conventions)
- [Option Strict statement](https://learn.microsoft.com/dotnet/visual-basic/language-reference/statements/option-strict-statement)
- [Visual Basic line continuation](https://learn.microsoft.com/dotnet/visual-basic/programming-guide/program-structure/statements#continuing-a-statement-over-multiple-lines)
- [.NET capitalization conventions](https://learn.microsoft.com/dotnet/standard/design-guidelines/capitalization-conventions)
- [.NET runtime coding style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
  (field prefixes)
