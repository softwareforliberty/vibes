# Scala Coding Style

A general-purpose coding style for Scala 3 projects. It builds on the official
[Scala Style Guide](https://docs.scala-lang.org/style/) and the defaults of
the [scalafmt](https://scalameta.org/scalafmt/) formatter, and fills the gaps
from other long-lived FOSS Scala projects (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(immutability, algebraic data types, errors, contextual abstractions and
other idioms), see [idioms.md](idioms.md).

The tools that check Scala code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Scala 3.3**, the first long-term support release
of Scala 3. It adds the `-Wunused` warnings this guide relies on to keep code
free of unused imports and values.

## Source files

- Encode source files in **UTF-8**.
- A file holding a single top-level class, trait, object or enum is named
  after it: `Order.scala`. A companion object lives in the same file as its
  class.
- A file holding several closely related declarations, or only top-level
  definitions, is named after what it contains, in `UpperCamelCase`:
  `OrderFormatting.scala`. Avoid meaningless names such as `Utils.scala`.
- The directory path matches the package: `com.example.billing.invoice`
  lives in `com/example/billing/invoice/`. Tools and readers find files by
  their package.

### Packages and imports

- Package names are all lowercase, with no underscores:
  `com.example.billing`.
- Put one `package` clause at the top of the file. Don't use chained or
  nested package clauses; one clause shows the package at a glance.
- **No wildcard imports**, except for a package of givens or extension
  methods meant to be imported together (`import cats.syntax.all.*`).
  Explicit imports show where each name comes from and can't silently pick
  up a new declaration.
- Write the Scala 3 forms: `*` for wildcards and `as` for renames
  (`import java.util.List as JList`). The old `_` and `=>` forms are
  deprecated.
- Import givens explicitly with `given` (`import com.example.json.given`),
  so contextual instances are visible at the import.
- Sort imports in ASCII order and remove unused ones. scalafix's
  `OrganizeImports` rule applies both.

## Layout

### Indentation

- Indent with **2 spaces** per level. Never use tabs. Two spaces is the
  convention across the Scala ecosystem and keeps nested expressions inside
  the line limit.
- Use **significant indentation** (the braceless Scala 3 syntax) for
  definitions and control structures. One syntax across a codebase keeps it
  readable, and scalafmt converts to it automatically.

  ```scala
  def total(items: List[Item]): BigDecimal =
    items.map(_.price).sum

  if order.isPaid then ship(order)
  else remind(order)
  ```

- Close any definition longer than about 15 lines, or containing blank lines,
  with an **`end` marker** (`end OrderService`). Without braces, the marker
  shows where a long block stops.

### Line length

- The limit is **100 columns**.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Wrap the code around them
  instead.

### Whitespace

- No trailing whitespace.
- One blank line between members of a class or object.
- Never more than one blank line in a row.
- End every file with a newline.

### Wrapping

- Break long parameter and argument lists with **one item per line**,
  indented once, and keep a **trailing comma** after the last item. Adding an
  item then changes one line in a diff.

  ```scala
  final case class Invoice(
    id: InvoiceId,
    customer: CustomerId,
    lines: List[InvoiceLine],
  )
  ```

- Break a long method chain before each `.`, one call per line.
- Break long infix expressions after the operator, never before it.

## Spacing

- One space after `:` in type annotations, and none before it:
  `count: Int`.
- One space on each side of `=`, `=>`, `<-` and infix operators.
- No space between a method name and its argument list: `total(items)`.
- One space inside the braces of a single-line lambda block or import
  selector: `{ x => x + 1 }`, `import a.{ B, C }`.

## Naming

Scala treats acronyms as words in all names: `HttpClient`, `XmlParser`, not
`HTTPClient`. Word boundaries stay visible, and every JVM language in these
guides follows the same rule.

| Kind | Convention | Example |
| --- | --- | --- |
| Classes, traits, objects, enums, type aliases | `UpperCamelCase` | `OrderService`, `PaymentState` |
| Methods, values, variables, parameters | `lowerCamelCase` | `totalPrice`, `isPaid` |
| Constants (`final val` in an object, enum cases) | `UpperCamelCase` | `MaxRetries`, `Pending` |
| Type parameters | One uppercase letter, or `UpperCamelCase` when one letter is unclear | `A`, `F[_]`, `Key` |
| Packages | All lowercase, no underscores | `com.example.billing` |

- **Accessors don't start with `get`.** Write `order.total`, not
  `order.getTotal`. Scala properties read like fields.
- A method with no side effects and no parameters is declared **without
  parentheses** (`def size: Int`). A method with side effects keeps empty
  parentheses (`def close(): Unit`), so callers can see the difference.
- Boolean values and predicates read as a question: `isEmpty`, `hasNext`,
  `canRetry`.
- Name a symbolic operator only when it already has a well-known meaning
  (`+` on a numeric type, `::` on a list), and give it a named alias.

## Declarations

### Class layout

Order the members of a class or object the same way everywhere:

1. Type members and constants.
2. Values and variables.
3. Public methods.
4. Private methods.

### Modifiers

- Write modifiers in this order: annotations, then `override`, access
  (`private`/`protected`), `final`, `sealed`, `abstract`, `implicit`, `lazy`,
  `inline`, `opaque`, `open`.
- Mark every **case class `final`**. Extending a case class breaks its
  generated `equals` and `copy`.
- Mark classes and traits that are designed for extension `open`, and leave
  everything else closed.

### Types

- **Annotate the type of every public and protected member.** The signature
  is the API; an inferred type can change silently when the body changes.
- Leave types off local values when the right-hand side makes them obvious.

### Functions

- Prefer an expression body with `=` to a block that ends in the result.
- Put each parameter list's implicit-style parameters in a `using` clause
  last: `def render(page: Page)(using Theme): Html`.

## Statements and expressions

- Don't write `return`. The last expression is the result, and `return`
  inside a lambda throws a control exception.
- Don't write semicolons at the end of lines.
- Write `if ... then ... else` and `while ... do` in the Scala 3 form, and
  use `match` for anything with more than two branches.
- Use `_` for a lambda parameter only when the lambda is short and uses the
  parameter once: `items.map(_.price)`. Otherwise name it.

## Comments

- Use `//` for comments on their own line and at the end of a line.
- Comments explain **why**, not **what**. The code already says what.

### Scaladoc

- Document every public type and member with a `/** ... */` Scaladoc
  comment. Start with a one-sentence summary.
- Describe parameters with `@param` and the result with `@return` only when
  the summary doesn't already make them clear.
- Don't repeat the signature in prose.

```scala
/** Returns the invoice total, including tax, rounded to the nearest cent.
  *
  * @param rate the tax rate as a fraction, for example `0.2` for 20%
  */
def totalWithTax(rate: BigDecimal): BigDecimal
```

## Generated and third-party code

Generated sources and vendored third-party code keep their own style. Exclude
them from scalafmt and scalafix, so updates stay easy to merge.

## Sources

- [Scala Style Guide](https://docs.scala-lang.org/style/)
- [Scala 3 reference: new control syntax and optional braces](https://docs.scala-lang.org/scala3/reference/other-new-features/indentation.html)
- [scalafmt documentation](https://scalameta.org/scalafmt/docs/configuration.html)
- [scalafix documentation](https://scalacenter.github.io/scalafix/)
