# F# Coding Style

A general-purpose coding style for F# projects. It builds on the
[F# style guide](https://learn.microsoft.com/dotnet/fsharp/style-guide/) and
the default settings of the [Fantomas](https://fsprojects.github.io/fantomas/)
formatter, and fills the gaps from the .NET Framework Design Guidelines (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(immutability, types, errors, computation expressions and other idioms), see
[idioms.md](idioms.md).

The tools that check F# code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **.NET 8 or later** and **F# 8**. That version adds the
`_.Property` shorthand for simple lambdas, which this guide relies on.

## Source files

- Encode source files in **UTF-8**.
- Name each file after the main module or type it contains:
  `OrderService.fs` holds `OrderService`.
- **File order matters.** The compiler reads files in the order the project
  lists them, and a file can only use what comes before it. List files from
  the most basic (domain types) to the most dependent (entry point).
- Start each file with a `namespace` or a top-level `module` declaration.
- Use a signature file (`.fsi`) only for a library's public surface, where
  hiding implementation details is worth keeping two files in step.

### Opens

- Put `open` declarations at the top of the file or namespace, never in the
  middle of code.
- Order them `System` namespaces first, then third-party namespaces, then
  your own, so readers see dependencies layer by layer. Keep each group in
  alphabetical order, unless a later `open` must shadow an earlier one.
- Mark modules that must always be qualified with
  `[<RequireQualifiedAccess>]`, so their short function names (`create`,
  `map`) can't clash.

## Layout

### Indentation

- Indent with **4 spaces** per level. F# doesn't allow tabs for indentation.
- F# is whitespace-sensitive: a continuation must be indented further than
  the start of the expression it continues.

### Line length

- Keep lines to **120 columns**, the Fantomas default. Wide enough for
  descriptive .NET names, narrow enough for side-by-side diffs.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Use a triple-quoted string for
  long multi-line text.

### Whitespace

- No trailing whitespace, and never more than one blank line in a row inside
  a function. Separate top-level definitions with one blank line.
- End every file with a newline.

### Pipelines

- Start each step of a multi-line pipeline with `|>` on its own line, at the
  same indentation as the value it starts from:

  ```fsharp
  let names =
      orders
      |> List.filter (fun order -> order.PlacedAt > cutoff)
      |> List.map _.CustomerName
      |> List.distinct
  ```

- A short pipeline (one or two steps) may stay on one line.

### Match expressions

- Line each `|` up with the `match` keyword. Put the body on the same line
  when it's short, and indented on the next line when it's not:

  ```fsharp
  match result with
  | Approved receipt -> sendReceipt receipt
  | Declined reason ->
      log.Warning("Payment declined: {Reason}", reason)
      notifyCustomer reason
  | Pending -> ()
  ```

## Spacing

- Put one space on each side of binary operators, `=`, `->` and `<-`.
- Put a space between a lowercase function and its argument, including a
  parenthesised one: `printfn "%d" count`, `validate (order, customer)`.
- Don't put a space between a .NET-style `PascalCase` method and its
  argument list: `String.Join(", ", names)`, `order.Ship()`.
- Type annotations take no space before the colon and one after:
  `(order: Order)`. A function's return-type annotation has a space on both
  sides: `let total (order: Order) : decimal =`.
- Put spaces just inside the brackets of lists, arrays and records:
  `[ 1; 2; 3 ]`, `[| 1; 2 |]`, `{ Name = "Ada"; Age = 36 }`.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

Names follow the .NET Framework Design Guidelines, so F# code reads naturally
next to the .NET libraries it calls.

| Kind | Convention | Example |
| --- | --- | --- |
| Namespaces, modules | `PascalCase` | `Example.Billing`, `OrderService` |
| Types, union cases, record fields | `PascalCase` | `Order`, `Approved`, `CustomerName` |
| Members (methods, properties) | `PascalCase` | `order.Total`, `client.SendAsync` |
| Exceptions | `PascalCase` + `Exception` | `PaymentException` |
| `let`-bound functions and values | `camelCase` | `calculateTotal`, `retryCount` |
| Parameters and locals | `camelCase` | `customer`, `order` |
| Generic type parameters | `'T`, or `'T` + `PascalCase` | `'T`, `'TKey` |

- **Acronyms:** two-letter acronyms are all capitals (`IOStream`,
  `UIElement`); longer ones are written as words (`XmlReader`, `HttpClient`).
  In `camelCase`, a leading acronym is all lowercase (`ioStream`,
  `xmlReader`).
- Suffix methods that return a .NET `Task` with **`Async`**: `SaveAsync`.
- Name booleans as questions: `isEmpty`, `hasChildren`, `canRetry`.
- Don't use underscores in names, except a leading `_` for a value that's
  deliberately unused.
- Test function names may use double-backtick names that read as sentences:
  ``let ``charging a declined card returns an error`` () =``.

## Declarations

- Prefer **immutable `let` bindings**. Use `let mutable` only for a local
  value that really changes, and keep it inside one function.
- Annotate the parameter and return types of every public function. Type
  inference is great inside a function, but a public signature is a contract
  that shouldn't change by accident.
- Leave out parentheses and type annotations that add nothing.
- Use `_.Property` (`List.map _.Name`) for lambdas that only read one
  property.

## Types

- Write a record or union on one line only if it's short. Otherwise, put each
  field or case on its own line:

  ```fsharp
  type PaymentResult =
      | Approved of receipt: Receipt
      | Declined of reason: string
      | Pending

  type Address =
      { Street: string
        City: string
        PostCode: string }
  ```

- Name the fields of union cases (`Approved of receipt: Receipt`), so pattern
  matches and C# callers see meaningful names.
- Put members after the type's fields or cases, with `member` declarations
  indented one level.

## Comments

- Use `//` for comments, on their own line above the code they describe.
  Leave one space after `//`.
- Comments explain **why**, not **what**. Rename or extract a function
  before writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `// TODO: reason`, and track the work somewhere it
  will be seen.

### XML documentation

Write `///` XML documentation for every public module, type and function.

```fsharp
/// <summary>Charges the customer's card for an order.</summary>
/// <param name="order">The order to charge. Must not be paid already.</param>
/// <returns>The receipt, or the reason the card was declined.</returns>
let charge (order: Order) : Result<Receipt, string> =
```

- Start `<summary>` with a third-person verb phrase ("Charges…").
- A comment with no XML tags is read as the summary, so a one-line
  `/// Charges the order.` needs no `<summary>` tags.

## Generated and third-party code

Generated sources and vendored third-party code keep their own format and are
excluded from the formatter and linters, so regenerating or updating them
stays a clean replacement.

## Sources

This guide starts from the F# style guide and borrows from:

- [F# style guide](https://learn.microsoft.com/dotnet/fsharp/style-guide/)
- [F# code formatting guidelines](https://learn.microsoft.com/dotnet/fsharp/style-guide/formatting)
- [F# coding conventions](https://learn.microsoft.com/dotnet/fsharp/style-guide/conventions)
- [Fantomas documentation](https://fsprojects.github.io/fantomas/docs/)
- [.NET capitalization conventions](https://learn.microsoft.com/dotnet/standard/design-guidelines/capitalization-conventions)
