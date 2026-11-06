# Kotlin Coding Style

A general-purpose coding style for Kotlin projects. It builds on the official
[Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html),
and fills the gaps from other long-lived FOSS Kotlin projects and their tools
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(immutability, null safety, errors, coroutines and other idioms), see
[idioms.md](idioms.md).

The tools that check Kotlin code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Kotlin 2.0**.

## Source files

- Encode source files in **UTF-8**.
- A file holding a single class (plus closely related top-level
  declarations) is named after the class: `Order.kt`.
- A file holding several declarations, or only top-level functions, is named
  after what it contains, in `UpperCamelCase`: `OrderFormatting.kt`. Avoid
  meaningless names such as `Util.kt`.
- Putting several closely related declarations in one file is fine, as long
  as the file stays a reasonable size and has one clear subject.
- The directory path matches the package. In a pure Kotlin module, the
  common root package may be left out of the path: with root
  `com.example.billing`, the package `com.example.billing.invoice` lives in
  `invoice/`.

### Imports

- **No wildcard imports.** Explicit imports show exactly where each name comes
  from and can't silently pick up a new declaration.
- Sort imports in ASCII order, with `java`, `javax` and `kotlin` imports
  following the rest, and alias imports last. ktlint applies this order.
- Remove unused imports.

## Layout

### Indentation

- Indent with **4 spaces** per block level. Never use tabs.
- Indent continuation lines by **4 spaces**.

### Line length

- The limit is **120 columns**.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Wrap the code around them
  instead, or use a raw string.

### Whitespace

- No trailing whitespace.
- One blank line between consecutive members of a class.
- Never more than one blank line in a row.
- End every file with a newline.

### One thing per line

- One statement per line. Never use semicolons: Kotlin doesn't need them.
- One property per declaration.

### Wrapping

- **Function signatures** that don't fit on one line put each parameter on
  its own line, indented once, with the closing parenthesis on its own line:

  ```kotlin
  fun sendInvoice(
      order: Order,
      recipient: EmailAddress,
      copyTo: List<EmailAddress> = emptyList(),
      attachments: List<Attachment> = emptyList(),
  ): Receipt {
  ```

- **Class headers** follow the same rule. A supertype list that follows the
  closing parenthesis goes on the same line: `) : Account(id) {`.
- **Calls** with long argument lists break after the opening parenthesis and
  indent the arguments once. Put each argument on its own line.
- **Chained calls** that don't fit on one line put each `.` or `?.` at the
  start of the next line, indented once:

  ```kotlin
  val names = orders
      .filter { it.isPaid && it.placedAfter(cutoff) }
      .map { it.customerName }
      .distinct()
      .sorted()
  ```

- **Expression bodies** that don't fit put the body on the next line after
  the `=`, indented once.
- Use **trailing commas** whenever the elements of a list are on separate
  lines, in declarations and in calls. Adding or reordering an element then
  touches only its own line in a diff.

## Braces

- Put the opening brace at the **end of the line**, and the closing brace on
  its own line, aligned with the start of the construct.
- `else`, `catch` and `finally` go on the same line as the closing brace
  before them:

  ```kotlin
  if (order.isPaid) {
      ship(order)
  } else {
      remind(order.customer)
  }
  ```

- An `if` that spans more than one line uses braces on every branch.
- In `when`, put a short branch on one line without braces. A branch longer
  than one line uses braces, and is separated from its neighbours by a blank
  line.

## Spacing

- Put a space on each side of binary operators: `a + b`, `x == y`. The range
  operators `..` and `..<` are the exception: `0..<count`.
- No space after a unary operator: `-x`, `!done`, `count++`.
- Put a space between a control-flow keyword and its parenthesis:
  `if (`, `when (`, `for (`, `while (`.
- No space before the parenthesis of a function declaration or call:
  `fun send(`, `send(order)`.
- No spaces just inside `()` or `[]`, and none around `.`, `?.`, `::` or
  angle brackets.
- No space before the `?` of a nullable type: `String?`.
- **Colons:** no space before a `:` that separates a declaration from its
  type (`val count: Int`, `fun total(): Money`). Put a space before a `:`
  that introduces a supertype or constructor delegation
  (`class Order : Entity`, `constructor(id: Id) : this(id, null)`). Always put
  a space after a colon.
- **Lambdas:** put spaces inside the braces and around `->`:
  `orders.filter { order -> order.isPaid }`.
- Put a space after `//`: `// retries so far`.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Packages | lowercase, words joined with no separator | `com.example.billing` |
| Classes, interfaces, objects | `UpperCamelCase` nouns | `Order`, `PaymentGateway` |
| Functions | `lowerCamelCase` verbs | `sendInvoice()`, `isPaid()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Enum entries | `UPPER_SNAKE_CASE` | `PENDING`, `PAID` |
| Properties, parameters, locals | `lowerCamelCase` | `retryCount`, `customer` |
| Type parameters | One capital letter, optionally with a digit | `T`, `K`, `V` |

- A **constant** is a `const val`, or a top-level or `object` `val` with no
  custom getter that holds deeply immutable data. A `val` that holds a mutable
  object, or an object with behaviour, is named in `lowerCamelCase`.
- **Treat acronyms as words**, including two-letter ones: `HttpClient`,
  `customerId`, `IoStream`, `parseXml()`. Word boundaries stay obvious.
- Name booleans and predicate functions as questions: `isEmpty`,
  `hasChildren`, `canRetry`.
- A function that mutates its receiver is a verb (`sort()`). One that returns
  a new value instead is a participle or adjective (`sorted()`).
- A **backing property** for a public property uses the public name with a
  leading underscore:

  ```kotlin
  private val _events = MutableStateFlow<List<Event>>(emptyList())
  val events: StateFlow<List<Event>> = _events
  ```

- A **factory function** may share the name of the type it returns:
  `fun Money(amount: String): Money`.
- Avoid one-letter names, except for loop counters, type parameters, and the
  implicit `it` in short lambdas.
- Don't use prefixes or suffixes for kinds of names: no `mName`, `IService`
  or `ServiceImpl` unless the name says something real.
- Test function names may be written in backticks as a sentence:
  `` fun `charging a declined card throws`() ``.

## Declarations

### Class layout

Order the contents of a class like this, so a reader can always find things in
the same place:

1. Properties and `init` blocks
2. Secondary constructors
3. Functions
4. The `companion object`

- Keep related members together. Don't sort them alphabetically or by
  visibility.
- **Never split overloads.** Functions with the same name sit together.
- When implementing an interface, keep its members in the interface's order.
- Put a nested class next to the code that uses it. Nested classes meant for
  outside use go at the end, after the companion object.

### Modifiers

Write modifiers in this order:

```
public / protected / private / internal
expect / actual
final / open / abstract / sealed / const
external
override
lateinit
tailrec
vararg
suspend
inner
enum / annotation / fun
companion
inline / value
infix
operator
data
```

Annotations go before modifiers. Leave out modifiers that are already the
default, such as `final` on a member that isn't `override`, and `public`. The
one exception is `public` in a library built in explicit API mode, where the
compiler requires it.

### Visibility and types

- Give every declaration the narrowest visibility that works: `private`,
  then `internal`, then `public`.
- **Write the return type of every public function and property explicitly.**
  It documents the API and stops an implementation change from changing the
  type silently. Private and local declarations may leave it to inference.
- Leave out `: Unit` on functions that return nothing.

### Functions

- Use an **expression body** for a function that's a single expression:
  `fun total(): Money = items.sumOf { it.price }`.
- Use **default parameter values** instead of overloads.
- When a call passes several values of the same type, or any `Boolean`
  literal, **name the arguments**: `send(order, notify = true)`.

### Properties

- Put a simple read-only property on one line:
  `val isEmpty: Boolean get() = size == 0`.
- Put a getter or setter that does more than return a value on its own
  lines, indented under the property.

### Annotations

- Put annotations on their own lines before the declaration, at the same
  indentation.
- Annotations without arguments may share one line:
  `@JvmField @Volatile var counter = 0`.
- File annotations go after the file comment and before the `package`
  statement.

## Statements and expressions

- Use `if` for a choice between two outcomes. Use `when` for three or more.
- Prefer the **expression form** of `if`, `when` and `try`:

  ```kotlin
  val label = when (status) {
      Status.PENDING -> "Waiting"
      Status.PAID -> "Paid"
      Status.REFUNDED -> "Refunded"
  }
  ```

- Leave out `else` in a `when` over an enum or sealed type that covers every
  case. The compiler then reports any value added later.
- Use **string templates** instead of concatenation. Leave out the braces for
  a simple name: `"Order $id"`, but `"Order ${order.id}"`.
- Use raw strings (`"""`) with `trimIndent()` or `trimMargin()` for
  multi-line text.
- For a nullable `Boolean`, compare explicitly: `if (value == true)`.

### Lambdas

- If a lambda is the last argument, pass it outside the parentheses. Leave the
  parentheses out entirely if it's the only argument: `orders.map { … }`.
- Use `it` in short lambdas that aren't nested. Name the parameter when the
  lambda is longer, or nested inside another lambda.
- Don't use more than one labelled `return` in a lambda. Restructure the code,
  or use an anonymous function instead.
- No space between a label and its lambda: `orders.forEach loop@{ … }`.

## Comments

- Use `//` for comments inside code, and `/* ... */` for longer explanations.
  Indent a comment to the level of the code it describes.
- Comments explain **why**, not **what**. Rename a variable or extract a
  function before writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `// TODO: reason`, and track the work somewhere it
  will be seen.

### KDoc

Write KDoc for every public declaration in a library, and for any declaration
whose behaviour isn't obvious from its name and signature.

```kotlin
/**
 * Charges the customer's card for [order] and returns the receipt.
 *
 * The charge is idempotent: calling this again for the same order returns the
 * original receipt.
 *
 * @throws PaymentException if the card is declined.
 */
fun charge(order: Order): Receipt {
```

- Write parameters and the return value into the description, and link them
  with square brackets (`[order]`). Use `@param` and `@return` only when the
  description would be too long to flow naturally.
- Put a short comment on one line: `/** Returns the order's total. */`.
- Document thrown exceptions with `@throws`.

## Generated and third-party code

Generated sources and vendored third-party code keep their own format and are
excluded from the formatter and linters, so regenerating or updating them
stays a clean replacement.

## Sources

This guide starts from the Kotlin coding conventions and borrows from:

- [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- [Kotlin API guidelines](https://kotlinlang.org/docs/api-guidelines-introduction.html)
- [Documenting Kotlin code (KDoc)](https://kotlinlang.org/docs/kotlin-doc.html)
- [ktlint rules](https://pinterest.github.io/ktlint/latest/rules/standard/)
- [detekt rules](https://detekt.dev/docs/rules/style)
