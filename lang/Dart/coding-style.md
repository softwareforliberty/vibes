# Dart Coding Style

A general-purpose coding style for Dart, on the command line, the server or
the web. It builds on [Effective Dart](https://dart.dev/effective-dart) and
the formatting of [`dart format`](https://dart.dev/tools/dart-format) (see
[Sources](#sources)). Flutter apps follow the same rules for their Dart code;
framework idioms are out of scope.

This guide covers how code looks. For how to design and structure it (null
safety, immutability, errors, async code and security), see
[idioms.md](idioms.md).

The tools that check Dart code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Dart 3.7**, set through the SDK constraint in
`pubspec.yaml`. Dart 3 adds records, patterns, sealed classes and class
modifiers, and Dart 3.7 adds the "tall" formatting style, which manages
trailing commas automatically. The language version decides which style
`dart format` uses, so a single baseline keeps every file formatted the same
way.

```yaml
environment:
  sdk: ^3.7.0
```

## Layout

- **`dart format` owns layout.** Run it on every file, and don't hand-format
  code it will rewrite.
- Indent with **2 spaces**. Never use tabs.
- **80 columns**, the formatter's default page width. Rewrite comments and
  long strings yourself.
- Let the formatter add and remove trailing commas. It adds one when it
  splits an argument or parameter list across lines, and removes it when the
  list fits on one line.
- Always use braces for `if`, `for` and `while` bodies, except for an `if`
  with no `else` that fits entirely on one line:

  ```dart
  if (items.isEmpty) return 0;

  if (order.isPaid) {
    ship(order);
  } else {
    remind(order.customer);
  }
  ```

- Separate top-level declarations, and the members inside a class, with one
  blank line. Never use more than one in a row.

## Files

- Use UTF-8 with LF line endings, and end every file with a newline.
- Name files, directories and packages in `lowercase_with_underscores`:
  `order_summary.dart`. Dart uses file names as library names, and other
  cases break on case-insensitive file systems.
- Put public code in `lib/`, private implementation in `lib/src/`, tests in
  `test/` and executables in `bin/`, following the package layout `dart pub`
  expects.
- Name test files after the library they test: `order_summary_test.dart`.

## Imports

- Order directives in sections, with a blank line between them:
  1. `dart:` imports
  2. `package:` imports
  3. Relative imports
  4. `export` directives
- Sort each section alphabetically.
- Use relative imports for files inside your own `lib/` directory, and never
  reach into another package's `src/` directory. Its contents aren't part of
  that package's API.
- Use `show` to import a few names from a large library, and an `as` prefix,
  in `lowercase_with_underscores`, when names would clash:
  `import 'package:path/path.dart' as p;`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Classes, enums, typedefs, extensions, type parameters | `UpperCamelCase` | `OrderQueue`, `PaymentStatus` |
| Variables, functions, methods, parameters, named constants | `lowerCamelCase` | `orderTotal`, `maxRetries` |
| Files, directories, packages, import prefixes | `lowercase_with_underscores` | `order_queue.dart` |

- Name constants in `lowerCamelCase` too: `const defaultTimeout = ...`. Dart
  doesn't use `UPPER_SNAKE_CASE`.
- Capitalise acronyms and abbreviations longer than two letters like words
  (`HttpRequest`, `Uri`), keep two-letter acronyms in capitals (`IOStream`),
  and treat `Id` as a word, not an acronym (`userId`).
- A leading underscore makes a name private to its library: `_cache`. Use it
  only for that, never as a naming style.
- Name booleans as questions or states: `isOpen`, `hasItems`, `canRetry`.
- Name methods that return a new value with a noun or a `to`/`as` prefix
  (`toJson()`, `asMap()`), and methods with side effects with a verb
  (`save()`, `clear()`).
- Include the unit in names that hold quantities when the type doesn't carry
  it: `timeoutMs`. Prefer `Duration` over a plain number of milliseconds.

## Strings

- Use single quotes: `'text'`.
- Use interpolation, never `+`: `'Hello, $name'` and `'Total: ${order.total}'`.
- Leave out the braces when interpolating a plain identifier: `'$name'`, not
  `'${name}'`.
- Use adjacent string literals, not `+`, to split a long string across lines.

## Declarations and types

- **Annotate public APIs fully**: every public function's parameters and
  return type, and every public field. The signature is the contract.
- **Don't annotate initialised local variables.** Use `final` for locals that
  are never reassigned, and `var` for those that are:
  `final total = orderTotal(order);`.
- Use `const` for values known at compile time, and give classes a `const`
  constructor when every field can be final.
- Never use `dynamic` unless the value really can be anything. Use `Object?`
  for values of unknown type, and check before use.
- Use collection literals (`[]`, `{}`, `<String, int>{}`), never `List()` or
  `Map()` constructors.
- Use `required` named parameters for anything optional or easy to confuse,
  such as booleans: `send(message, retry: true)`.
- Use `=>` for members whose body is a single expression.

## Classes

- Order members: static fields, instance fields, constructors, then methods.
- Initialise fields in the constructor's initialiser list or with
  `this.field` parameters, not in the constructor body.
- Make fields `final` unless they really change.
- Mark overriding members with `@override`.

## Comments

- Document every public declaration with a `///` doc comment. Start with a
  one-sentence summary, and refer to code in square brackets so `dart doc`
  links it:

  ```dart
  /// Returns the total of [order] in cents, including tax.
  ///
  /// Throws an [ArgumentError] if [taxRate] is negative.
  int orderTotal(Order order, double taxRate) {
  ```

- Use `//` for other comments, as full sentences that explain **why**.
- Don't use `/* */` block comments.
- Don't leave commented-out code. Version control keeps the history.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted. Exclude them from analysis with `analyzer: exclude:` in
`analysis_options.yaml`.

## Sources

- [Effective Dart](https://dart.dev/effective-dart)
- [Effective Dart: Style](https://dart.dev/effective-dart/style)
- [Effective Dart: Documentation](https://dart.dev/effective-dart/documentation)
- [Effective Dart: Usage](https://dart.dev/effective-dart/usage)
- [dart format](https://dart.dev/tools/dart-format)
- [Package layout conventions](https://dart.dev/tools/pub/package-layout)
