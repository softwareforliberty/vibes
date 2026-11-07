# Java Coding Style

A general-purpose coding style for Java projects. It builds on the
[Google Java Style Guide](https://google.github.io/styleguide/javaguide.html),
and fills the gaps from other long-lived FOSS Java projects and the Java
Language Specification (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(immutability, null handling, exceptions, concurrency and other idioms), see
[idioms.md](idioms.md).

The tools that check Java code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Java 17**. Records, sealed types, switch
expressions and text blocks are all available.

## Source files

- Encode source files in **UTF-8**.
- Name each file after the single top-level class it contains: `Order.java`
  holds `class Order`. One top-level class per file keeps classes easy to
  find.
- Lay a file out in this order, with one blank line between each part:
  1. Licence or copyright header, if the project uses one
  2. `package` statement
  3. Imports
  4. The top-level class
- The directory path matches the package: `com/example/billing/Order.java`.

### Imports

- **No wildcard imports**, static or otherwise. Explicit imports show exactly
  where each name comes from and can't silently pick up a new class.
- Put all static imports in one group, then all non-static imports in
  another, with one blank line between them. Sort each group in ASCII order.
- Never wrap `package` or `import` lines, whatever their length.
- Remove unused imports.

## Layout

### Indentation

- Indent with **2 spaces** per block level. Never use tabs.
- Indent continuation lines by **at least 4 spaces** from the start of the
  statement.
- When wrapping, break **before** operators and `.`, `::` and `->` targets,
  so the operator starts the continuation line and the reader sees how it
  joins the line above:

  ```java
  String summary =
      customer.displayName()
          + " ordered "
          + order.items().size()
          + " items worth "
          + order.total();

  List<String> names =
      orders.stream()
          .filter(order -> order.placedAfter(cutoff))
          .map(Order::customerName)
          .distinct()
          .sorted()
          .toList();
  ```

- When a line breaks at an assignment `=`, the break comes after the `=`.

### Line length

- The limit is **100 columns**. Long URLs in comments, and `package` and
  `import` lines, are the only exceptions.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole. Wrap the code around them
  instead, or use a text block.

### Whitespace

- No trailing whitespace. The only whitespace character besides line breaks
  is the ASCII space (no tabs, no non-breaking spaces).
- One blank line between consecutive members of a class. Blank lines between
  fields are optional and can group related fields.
- Never more than one blank line in a row.
- End every file with a newline.

### One thing per line

- One statement per line.
- One variable per declaration: `int a, b;` is never used, except in a `for`
  header.

## Braces

- **Always use braces** with `if`, `else`, `for`, `do` and `while`, even when
  the body is empty or a single statement. A statement added later can't then
  fall outside the block by accident.
- Use K&R ("Egyptian") braces. The opening brace ends the line, and the
  closing brace starts its own line, unless `else`, `catch`, `finally` or a
  do-loop's `while` follows it:

  ```java
  if (order.isPaid()) {
    ship(order);
  } else {
    remind(order.customer());
  }

  try {
    process(order);
  } catch (PaymentException e) {
    log.warn("Payment failed for order {}", order.id(), e);
  }
  ```

- An empty block may be written `{}`, unless it's part of a multi-block
  statement such as `if`/`else` or `try`/`catch`.

## Spacing

- Put a space between a keyword and the `(` or `{` that follows it:
  `if (`, `for (`, `catch (`, `try {`.
- Put a space before every opening `{`, except in annotation arguments
  (`@SomeAnnotation({a, b})`) and between the braces of nested array
  initialisers (`{{"a", "b"}}`).
- Put one space on each side of binary and ternary operators, `->` in
  lambdas, `:` in an enhanced `for`, and `&` in type bounds.
- No space around `.` or `::`, and none just inside parentheses.
- Put a space after `,`, `;` (in a `for` header) and a cast's closing `)`.
- Put a space on both sides of `//` when it follows code:
  `int count = 0; // retries so far`.
- Don't line up code in columns with extra spaces. Alignment breaks every
  time a line changes, so the diff touches lines that didn't change.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Packages | lowercase, words joined with no separator | `com.example.billing` |
| Classes, interfaces, records, enums | `UpperCamelCase` nouns | `Order`, `PaymentGateway` |
| Methods | `lowerCamelCase` verbs | `sendInvoice()`, `isPaid()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Fields, parameters, locals | `lowerCamelCase` | `retryCount`, `customer` |
| Type parameters | One capital letter, optionally with a digit | `T`, `K`, `V`, `T2` |

- A **constant** is a `static final` field whose value is deeply immutable:
  a primitive, a `String`, or an immutable object. A `static final` mutable
  object (such as a `List` you can add to) is not a constant, so it's named in
  `lowerCamelCase`.
- **Treat acronyms as words**: `HttpClient`, `customerId`, `parseXml()`, not
  `HTTPClient` or `customerID`. Word boundaries stay obvious.
- Name booleans and predicate methods as questions: `isEmpty()`,
  `hasChildren()`, `canRetry`.
- Avoid one-letter names, except for loop counters, lambda parameters in
  short lambdas, and type parameters.
- Don't use prefixes or suffixes for kinds of names: no `mName`, `s_count`,
  `IService` or `ServiceImpl` unless the name says something real.
- Test method names may use underscores to separate the parts of a scenario:
  `charge_declinedCard_throwsPaymentException()`.

## Declarations

- Declare local variables **where they're first needed**, and initialise them
  in the declaration. Small scopes mean fewer stale values.
- Use `var` only when the type is obvious from the right-hand side
  (`var orders = new ArrayList<Order>()`). Write the type out when it isn't.
- Put array brackets on the type: `String[] args`, not `String args[]`.
- Write modifiers in the order the Java Language Specification uses:

  ```
  public protected private abstract default static final sealed non-sealed
  transient volatile synchronized native strictfp
  ```

- Use an uppercase `L` on `long` literals: `3000000000L`. A lowercase `l`
  looks too much like `1`.
- Add underscores to long numeric literals to group digits:
  `1_000_000`.

## Classes

- Order members logically, so a reader can follow the class from top to
  bottom. A common order is: constants, fields, constructors, methods,
  nested types.
- **Never split overloads.** Methods with the same name sit together, with
  nothing in between.
- Always add **`@Override`** when a method overrides or implements another.
  The compiler then catches a signature that no longer matches.
- Refer to static members through the class name (`Order.MAX_ITEMS`), never
  through an instance or a subclass.
- Never use finalizers. They're deprecated, unreliable and slow.

### Annotations

- Put class, method and constructor annotations on their own lines, one per
  line, directly after the Javadoc.
- A single annotation without parameters may share the line with a field:
  `@Nullable String middleName;`.
- Type-use annotations go immediately before the type they annotate.

## Statements

### Switch

- Prefer **arrow-form** `case` labels (`case A ->`). They can't fall through,
  so `break` isn't needed.
- Prefer a **switch expression** when the switch produces a value:

  ```java
  int days =
      switch (month) {
        case FEBRUARY -> 28;
        case APRIL, JUNE, SEPTEMBER, NOVEMBER -> 30;
        default -> 31;
      };
  ```

- In an old-style switch, end every group with `break`, `return`, `continue`
  or `throw`, or mark the fall-through with a `// fall through` comment.
- Every switch over a type that isn't exhaustive includes a `default`. A
  switch over an enum or sealed type that covers every case doesn't, so the
  compiler reports any value added later.

### Expressions

- Add grouping parentheses whenever a reader might misread the precedence.
  Only leave them out where the order is obvious, such as `a + b * c`.
- Never ignore a caught exception silently. If doing nothing is genuinely
  right, explain why in a comment inside the `catch` block.

## Comments

- Use `//` for comments inside code, and `/* ... */` for longer explanations.
  Indent a comment to the level of the code it describes.
- Comments explain **why**, not **what**. Rename a variable or extract a
  method before writing a comment that restates the code.
- Don't leave commented-out code. Version control keeps the history.
- Write `TODO` comments as `// TODO: reason`, and track the work somewhere it
  will be seen.

### Javadoc

Write Javadoc for every `public` class, and every `public` or `protected`
member. Simple, obvious members (`getName()`) and methods that override a
documented supertype method may skip it.

```java
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
public Receipt charge(Order order) throws PaymentException {
```

- Start with a **summary fragment**: a short phrase in the third person
  ("Charges the customer's card…"), not "This method charges…". Tools show it
  on its own in summaries.
- Start each new paragraph with `<p>`, directly before its first word.
- Order the block tags `@param`, `@return`, `@throws`, `@deprecated`, and
  never leave one empty.

## Generated and third-party code

Generated sources and vendored third-party code keep their own format and are
excluded from the formatter and linters, so regenerating or updating them
stays a clean replacement.

## Sources

This guide starts from the Google Java Style Guide and borrows from:

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [The Java Language Specification](https://docs.oracle.com/javase/specs/)
  (modifier order)
- [Checkstyle Google checks](https://checkstyle.org/google_style.html)
