# Groovy Coding Style

A general-purpose coding style for Groovy projects. It builds on the
[Apache Groovy style guide](https://groovy-lang.org/style-guide.html), and
fills the gaps from other long-lived FOSS Groovy projects and the CodeNarc rule
sets (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (typing,
null handling, closures, exceptions and other idioms), see
[idioms.md](idioms.md).

The tools that check Groovy code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Groovy 4**.

## Source files

- Encode source files in **UTF-8**.
- Name each class file after the single top-level class it contains:
  `Order.groovy` holds `class Order`.
- Lay a file out in this order, with one blank line between each part:
  1. Licence or copyright header, if the project uses one
  2. `package` statement
  3. Imports
  4. The top-level class
- The directory path matches the package: `com/example/billing/Order.groovy`.
- Build files and scripts (`build.gradle`, `Jenkinsfile`) follow the naming of
  the tool that runs them.

### Imports

- **No wildcard imports.** Explicit imports show exactly where each name comes
  from and can't silently pick up a new class.
- **Don't import what Groovy imports by default**: `java.lang.*`,
  `java.util.*`, `java.io.*`, `java.net.*`, `groovy.lang.*`, `groovy.util.*`,
  `java.math.BigInteger` and `java.math.BigDecimal`.
- Put all static imports in one group, then all non-static imports in
  another, with one blank line between them. Sort each group in ASCII order.
- Remove unused imports.

## Layout

### Indentation

- Indent with **4 spaces** per block level. Never use tabs.
- Indent continuation lines by **4 spaces**.
- Chained calls that don't fit on one line put each `.` or `?.` at the start of
  the next line, indented once:

  ```groovy
  List<String> names = orders
      .findAll { it.paid && it.placedAfter(cutoff) }
      .collect { it.customerName }
      .unique()
      .sort()
  ```

### Line length

- The limit is **120 columns**.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Wrap the code around them
  instead, or use a multi-line string.

### Whitespace

- No trailing whitespace.
- One blank line between consecutive members of a class, and one after a
  class's opening brace and before its closing brace.
- Never more than one blank line in a row.
- End every file with a newline.

### One thing per line

- One statement per line. **Never use semicolons**: Groovy doesn't need them.
- One variable per declaration.

## Braces

- **Always use braces** with `if`, `else`, `for` and `while`, even when the
  body is a single statement. A statement added later can't then fall outside
  the block by accident.
- Put the opening brace at the **end of the line**, and the closing brace on
  its own line. `else`, `catch` and `finally` go on the same line as the
  closing brace before them:

  ```groovy
  if (order.paid) {
      ship(order)
  } else {
      remind(order.customer)
  }
  ```

## Spacing

- Put a space on each side of binary and ternary operators, including `?:`
  and `->` in closures: `name ?: 'unknown'`, `{ a, b -> a + b }`. The range
  operators `..` and `..<` are the exception: `0..<count`.
- No space after a unary operator: `-x`, `!done`, `count++`.
- Put a space between a keyword and its parenthesis: `if (`, `for (`,
  `while (`, `switch (`, `catch (`.
- No space before the parenthesis of a method declaration or call:
  `void send(`, `send(order)`.
- No spaces just inside `()` or `[]`, and none around `.`, `?.`, `*.` or `::`.
- Put spaces inside closure braces: `{ it.paid }`.
- Put a space after `:` in map literals and named arguments, and none before:
  `[name: 'Ada', port: 8080]`.
- Put a space after `//`: `// retries so far`.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Packages | lowercase, words joined with no separator | `com.example.billing` |
| Classes, interfaces, traits, enums | `UpperCamelCase` nouns | `Order`, `PaymentGateway` |
| Methods | `lowerCamelCase` verbs | `sendInvoice()`, `isPaid()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Enum constants | `UPPER_SNAKE_CASE` | `PENDING`, `PAID` |
| Properties, fields, parameters, locals | `lowerCamelCase` | `retryCount`, `customer` |
| Type parameters | One capital letter, optionally with a digit | `T`, `K`, `V` |

- A **constant** is a `static final` field whose value is deeply immutable:
  a primitive, a `String`, or an immutable object. A `static final` mutable
  object is named in `lowerCamelCase`.
- **Treat acronyms as words**: `HttpClient`, `customerId`, `parseXml()`, not
  `HTTPClient` or `customerID`. Word boundaries stay obvious.
- Name predicate methods as questions: `isEmpty()`, `hasChildren()`,
  `canRetry()`. Name a `boolean` property with the adjective alone (`paid`,
  `active`). Groovy generates the `isPaid()` getter, and callers read it as
  `order.paid`.
- Avoid one-letter names, except for loop counters, type parameters, and the
  implicit `it` in short closures.
- Don't use prefixes or suffixes for kinds of names: no `mName`, `IService`
  or `ServiceImpl` unless the name says something real.
- Test method names may be written as quoted sentences (as in Spock):
  `def 'charging a declined card throws'()`.

## Declarations

### Types and `def`

- **Give methods explicit parameter and return types.** Types document the
  API, let the compiler check calls, and stop a method returning something
  surprising as its last expression. Use `void` for methods that return
  nothing. Test frameworks that declare tests with `def`, such as Spock
  feature methods, are the only exception.
- Use `def` only for local variables whose type is obvious from the
  right-hand side, and in scripts. Never write `def` together with a type
  (`def String name`): it's redundant.
- **Declare fields and properties with types.**
- Declare local variables where they're first needed, and initialise them in
  the declaration.

### Modifiers

- **Leave out `public`.** Classes and methods are public by default, so the
  keyword is noise.
- Declare a property as a field with no access modifier (`String name`).
  Groovy generates the getter and setter. Only write an accessor yourself when
  it does more than return or store the value.
- Write modifiers in the same order as Java:

  ```
  public protected private abstract static final transient volatile
  synchronized native strictfp
  ```

### Classes

- Order members logically, so a reader can follow the class from top to
  bottom. A common order is: constants, properties and fields, constructors,
  methods, nested types.
- **Never split overloads.** Methods with the same name sit together.
- Always add **`@Override`** when a method overrides or implements another.
  The compiler then catches a signature that no longer matches.
- Put class, method and constructor annotations on their own lines, one per
  line, before the declaration.

## Statements and expressions

### Strings

- Use **single quotes** for plain strings: `'Order shipped'`.
- Use **double quotes only for interpolation**: `"Order $id shipped"`. Leave
  out the braces for a simple name or property path, and keep them for any
  other expression: `"Total: ${order.total()}"`.
- Use triple-quoted strings for multi-line text, with `stripIndent()` to keep
  the source indented.

### Calls and closures

- **Omit parentheses only in top-level command statements and DSLs**:
  `println 'Done'`, `implementation 'org.example:lib:1.0'`. Keep them for any
  call whose result is used, any call with no arguments, and any nested call.
- If a closure is the last argument, pass it outside the parentheses:
  `orders.each { ship(it) }`.
- Use `it` in short closures that aren't nested. Name the parameter when the
  closure is longer, or nested inside another closure.

### Returns

- In short methods and closures, **leave out `return`** on the last
  expression: its value is returned anyway.
- Use an explicit `return` for early exits, and in longer methods where the
  returned value isn't obvious.

### Property and collection syntax

- Use property notation, not getter and setter calls: `order.total`, not
  `order.getTotal()`.
- Use Groovy's literal syntax for collections: `[]` for lists, `[:]` for maps,
  `1..10` for ranges.
- Refer to classes without `.class`: `parse(String)`, not
  `parse(String.class)`.

### Switch

- Prefer **arrow-form** `case` labels (`case 'A' ->`). They can't fall
  through, so `break` isn't needed.
- Use a switch expression when the switch produces a value:

  ```groovy
  String label = switch (status) {
      case Status.PENDING -> 'Waiting'
      case Status.PAID -> 'Paid'
      default -> 'Unknown'
  }
  ```

- In an old-style switch, end every group with `break`, `return`, `continue`
  or `throw`, or mark the fall-through with a `// fall through` comment.

## Comments

- Use `//` for comments inside code, and `/* ... */` for longer explanations.
  Indent a comment to the level of the code it describes.
- Comments explain **why**, not **what**. Rename a variable or extract a
  method before writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `// TODO: reason`, and track the work somewhere it
  will be seen.

### Groovydoc

Write Groovydoc (`/** ... */`, the same format as Javadoc) for every public
class, and every public or protected member whose behaviour isn't obvious from
its name and signature.

```groovy
/**
 * Charges the customer's card for an order.
 *
 * <p>The charge is idempotent: calling this again for the same order returns
 * the original receipt.
 *
 * @param order the order to charge; must not be paid already
 * @return the receipt for the charge
 * @throws PaymentException if the card is declined
 */
Receipt charge(Order order) {
```

- Start with a **summary fragment**: a short phrase in the third person
  ("Charges the customer's card…"), not "This method charges…".
- Order the block tags `@param`, `@return`, `@throws`, `@deprecated`, and
  never leave one empty.

## Generated and third-party code

Generated sources and vendored third-party code keep their own format and are
excluded from the formatter and linters, so regenerating or updating them
stays a clean replacement.

## Sources

This guide starts from the Apache Groovy style guide and borrows from:

- [Apache Groovy style guide](https://groovy-lang.org/style-guide.html)
- [Groovy language documentation](https://groovy-lang.org/documentation.html)
  (default imports, switch expressions)
- [CodeNarc rule index](https://codenarc.github.io/CodeNarc/codenarc-rule-index.html)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
  (rules Groovy shares with Java, such as Groovydoc and modifier order)
