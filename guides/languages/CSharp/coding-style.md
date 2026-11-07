# C# Coding Style

A general-purpose coding style for C# projects. It builds on the
[.NET runtime coding style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
and Microsoft's
[C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions),
and fills the gaps from the .NET Framework Design Guidelines (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(immutability, nullability, exceptions, async and other idioms), see
[idioms.md](idioms.md).

The tools that check C# code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **.NET 8 or later** and **C# 12**. That version has
file-scoped namespaces, `required` members, primary constructors and
collection expressions, which this guide relies on. **Nullable reference
types are on** in every project.

## Source files

- Encode source files in **UTF-8**. Write any non-ASCII character in a string
  or character literal as an escape (`é`), so tools that mangle encodings
  can't corrupt it.
- Put **one top-level type per file**, and name the file after it:
  `OrderService.cs` holds `OrderService`. Generic types use the plain name
  (`Result.cs` for `Result<T>`).
- Use a **file-scoped namespace** (`namespace Example.Billing;`). It saves a
  level of indentation for the whole file.
- The folder path matches the namespace below the project's root namespace.

### Usings

- Put `using` directives at the **top of the file**, outside the namespace.
- Sort them alphabetically, with `System` namespaces first. Every file then
  lists its dependencies in the same order.
- Remove unused `using` directives.
- Use `global using` only in one dedicated file per project
  (`GlobalUsings.cs`), so there's one place to see them.

## Layout

### Indentation

- Indent with **4 spaces** per level. Never use tabs.
- Indent continuation lines by one level (4 spaces) from the start of the
  statement.
- When a call chain wraps, put each `.` call on its own line, starting with
  the `.`:

  ```csharp
  var names = orders
      .Where(order => order.PlacedAfter(cutoff))
      .Select(order => order.CustomerName)
      .Distinct()
      .ToList();
  ```

### Line length

- Keep lines to **120 columns**. Wide enough for descriptive .NET names,
  narrow enough for side-by-side diffs.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Use a raw string literal for
  long multi-line text.

### Whitespace

- No trailing whitespace, and never more than one blank line in a row.
- One blank line between members of a type.
- End every file with a newline.

### One thing per line

- One statement per line.
- One variable per declaration: `int a, b;` is never used.

## Braces

- Use **Allman braces**: every `{` and `}` goes on its own line, aligned with
  the start of the statement:

  ```csharp
  if (order.IsPaid)
  {
      Ship(order);
  }
  else
  {
      Remind(order.Customer);
  }
  ```

- **Always use braces** with `if`, `else`, `for`, `foreach`, `while`, `do`,
  `using` and `lock`, even for a single statement. A statement added later
  can't then fall outside the block by accident.
- Expression-bodied members (`=>`) don't take braces. Use them only when the
  body is a single, short expression:

  ```csharp
  public decimal Total => _lines.Sum(line => line.Price);
  ```

## Spacing

- Put a space after `if`, `for`, `foreach`, `while`, `switch`, `catch`,
  `using` and `lock`, before the `(`.
- No space between a method name and its `(`, and none just inside
  parentheses.
- Put one space on each side of binary and ternary operators, `=>` and `=`.
- Put a space after `,` and `;` (in a `for` header), and none before them.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

Names follow the .NET Framework Design Guidelines, so code reads like the
base class library it calls.

| Kind | Convention | Example |
| --- | --- | --- |
| Namespaces | `PascalCase`, dot-separated | `Example.Billing` |
| Types (classes, structs, records, enums, delegates) | `PascalCase` nouns | `Order`, `PaymentGateway` |
| Interfaces | `I` + `PascalCase` | `IPaymentGateway` |
| Methods | `PascalCase` verbs | `SendInvoice()` |
| Properties, events, public fields | `PascalCase` | `Total`, `OrderPlaced` |
| Constants (fields and locals) | `PascalCase` | `MaxRetries` |
| Private and internal instance fields | `_camelCase` | `_retryCount` |
| Private and internal static fields | `s_camelCase` | `s_defaultTimeout` |
| Parameters and locals | `camelCase` | `customer`, `retryCount` |
| Type parameters | `T`, or `T` + `PascalCase` | `T`, `TKey`, `TResult` |

- **Acronyms:** two-letter acronyms are all capitals (`IOStream`,
  `UIElement`); longer ones are written as words (`XmlReader`, `HttpClient`).
  In `camelCase`, a leading acronym is all lowercase (`ioStream`,
  `xmlReader`).
- Suffix asynchronous methods with **`Async`**: `SaveAsync()`.
- Name booleans as questions: `IsEmpty`, `HasChildren`, `CanRetry`.
- Name event handlers `On` + event: `OnOrderPlaced`.
- Don't use Hungarian notation or abbreviations nobody would guess.
- Test method names may use underscores between scenario parts:
  `Charge_DeclinedCard_ThrowsPaymentException`.

## Declarations

- **Always write the access modifier**, even when it's the default
  (`private`). Put it first: `public static`, not `static public`.
- Declare local variables **where they're first needed**, and initialise them
  in the declaration.
- Use **`var`** only when the type is obvious from the right-hand side
  (`var orders = new List<Order>();`, a cast, or an `as`). Write the type out
  otherwise, so the reader isn't left guessing.
- Use the **language keywords** for built-in types (`int`, `string`,
  `object`), not the BCL names (`Int32`, `String`), including in member calls
  (`string.IsNullOrEmpty`).
- Use **target-typed `new`** when the type is on the left:
  `List<Order> orders = new();`.
- Use `nameof(x)` instead of the string `"x"`, so renames can't break it.
- Make fields **`readonly`** whenever they're only set in the constructor.
- Don't qualify members with `this.` unless a parameter shadows the member.

## Types and members

- Lay a type out in this order, so readers know where to look: constants,
  fields, constructors, properties, events, methods, nested types. Within
  each group, `public` members come before `private` ones.
- Use a **primary constructor** for simple dependency capture. Assign the
  parameter to a `readonly` field when it's used in several members, so
  nothing reassigns it.
- **Never split overloads.** Overloads of one method sit together.
- Put **attributes** on their own line above the member, one attribute per
  line.

## Statements and expressions

### Pattern matching and null checks

- Compare against `null` with **`is null`** and **`is not null`**. An
  overloaded `==` can't change their meaning.
- Prefer a **switch expression** when a switch produces a value. Put each arm
  on its own line, ending with a comma:

  ```csharp
  var days = month switch
  {
      Month.February => 28,
      Month.April or Month.June or Month.September or Month.November => 30,
      _ => 31,
  };
  ```

- In a switch statement, every `case` section ends with `break`, `return`,
  `throw` or `goto case`. C# forbids implicit fall-through.

### Strings

- Use **string interpolation** (`$"Order {order.Id} shipped"`) instead of
  concatenation or `string.Format`.
- Use a **raw string literal** (`"""…"""`) for multi-line text and text full
  of quotes.

### Expressions

- Add parentheses whenever a reader might misread the precedence.
- Use `??` and `?.` instead of explicit null checks that only pick a default.
- Never ignore a caught exception silently. If doing nothing is genuinely
  right, explain why in a comment inside the `catch` block.

## Comments

- Use `//` for comments, on their own line above the code they describe.
  Leave one space after `//`.
- Comments explain **why**, not **what**. Rename or extract a method before
  writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `// TODO: reason`, and track the work somewhere it
  will be seen.

### XML documentation

Write `///` XML documentation for every `public` and `protected` type and
member. The compiler then reports any that are missing.

```csharp
/// <summary>
/// Charges the customer's card for an order.
/// </summary>
/// <param name="order">The order to charge. Must not be paid already.</param>
/// <param name="cancellationToken">Cancels the charge request.</param>
/// <returns>The receipt for the charge.</returns>
/// <exception cref="PaymentException">The card was declined.</exception>
public async Task<Receipt> ChargeAsync(Order order, CancellationToken cancellationToken)
```

- Start `<summary>` with a third-person verb phrase ("Charges…"), not "This
  method charges…".
- Use `<inheritdoc/>` on overrides and interface implementations instead of
  copying the base documentation.

## Generated and third-party code

Generated sources (`*.g.cs`, designer files) and vendored third-party code
keep their own format and are excluded from the formatter and analyzers, so
regenerating or updating them stays a clean replacement.

## Sources

This guide starts from the .NET runtime coding style and borrows from:

- [.NET runtime coding style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
- [C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [C# identifier naming rules and conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [.NET capitalization conventions](https://learn.microsoft.com/dotnet/standard/design-guidelines/capitalization-conventions)
- [Recommended XML documentation tags](https://learn.microsoft.com/dotnet/csharp/language-reference/xmldoc/recommended-tags)
