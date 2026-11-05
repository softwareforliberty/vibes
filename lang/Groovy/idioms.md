# Groovy Idioms and Principles

How to write Groovy well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
Groovy code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **Clarity beats cleverness.** Groovy can be very terse. Use that to remove
  noise, not to hide what the code does.
- **Static where you can, dynamic where it pays.** Type-checked code catches
  mistakes at compile time. Keep dynamic features for the places that need
  them, such as DSLs and builders.
- **Minimise mutability.** An object that can't change can't be changed
  wrongly, and can be shared freely between threads.
- **Minimise visibility and magic.** Anything public is a promise you have to
  keep, and every bit of metaprogramming is something a reader has to know
  about to follow the code.
- **Fail fast.** Validate inputs where they enter, and throw as soon as
  something is wrong, close to the cause.

## Static and dynamic typing

- **Annotate application classes with `@CompileStatic`** (or `@TypeChecked`).
  Typos in method and property names, and wrong argument types, become compile
  errors instead of run-time failures. Static compilation also runs faster.
- Turn static checking off only for code that needs dynamic dispatch, such as
  builders, DSL handlers or `methodMissing`. Do it on the smallest scope that
  works, with `@CompileDynamic` on a single method.
- **Give closures used as DSL blocks a `@DelegatesTo` annotation**, so the type
  checker and IDE know what the closure's delegate is:

  ```groovy
  void server(@DelegatesTo(ServerSpec) Closure config) {
      ServerSpec spec = new ServerSpec()
      config.delegate = spec
      config.resolveStrategy = Closure.DELEGATE_FIRST
      config()
  }
  ```

## Classes and types

- **Prefer composition to inheritance.** Use `@Delegate` on a field to forward
  an interface's methods to it, instead of extending a class you don't control.
- **Use traits for reusable behaviour** that several unrelated classes share.
- **Use `record` or `@Immutable` for value types.** They generate the
  constructor, accessors, `equals()`, `hashCode()` and `toString()`, which then
  can't drift out of date:

  ```groovy
  record Money(BigDecimal amount, Currency currency) {}
  ```

- **Use AST transformations instead of boilerplate**:

  | Annotation | Generates |
  | --- | --- |
  | `@ToString` | `toString()` |
  | `@EqualsAndHashCode` | `equals()` and `hashCode()` |
  | `@TupleConstructor` | A constructor with a parameter per property |
  | `@Canonical` | All three of the above |
  | `@Immutable` | An immutable class with all of the above |
  | `@Builder` | A builder for classes with many properties |

- **Use enums, not `int` or `String` constants,** for fixed sets of values.
- Make utility classes `final` with a `private` constructor, so nobody can
  instantiate or extend them.

## Immutability

- Make fields `final` wherever you can, and value types fully immutable.
- **Return unmodifiable collections** with `asImmutable()` or
  `asUnmodifiable()` instead of exposing internal mutable ones.
- **Copy mutable inputs** at the boundary of an immutable class. Otherwise a
  caller who keeps a reference can change the object's state.

## Null handling and Groovy truth

- Use the **safe navigation operator** (`?.`) to call through values that may
  be `null`: `order?.customer?.email`.
- Use the **Elvis operator** (`?:`) for defaults:
  `String name = user.nickname ?: user.fullName`.
- **Use Groovy truth for "is there anything here?" checks.** `null`, `false`,
  `0`, empty strings, empty collections and empty maps all count as false:

  ```groovy
  if (orders) {
      ship(orders)
  }
  ```

- **Compare explicitly when `0` or empty is a valid value.** `if (count)` is
  false for a count of `0`. Write `if (count != null)` when you only mean "has
  a value".
- **Return an empty collection, not `null`,** when there's nothing to return.
- **Check for `null` at the boundary** with `Objects.requireNonNull()`, so a
  bad argument fails immediately with a clear message.

## Errors and exceptions

- **Use exceptions for programming errors and truly exceptional failures.**
  Use the standard ones where they fit: `IllegalArgumentException` for bad
  arguments, `IllegalStateException` for calls made in the wrong state.
- **Catch specific exceptions.** Don't catch `Exception` or `Throwable`
  except at the top level of a thread, request or script, where the job is to
  log the failure and keep running.
- **Never swallow an exception.** Handle it, rethrow it, or wrap it with the
  original as the cause, so the stack trace survives.
- **Log or throw, not both.** Logging and rethrowing the same exception
  reports one failure several times.
- **Document thrown exceptions** with `@throws` in the Groovydoc. Groovy
  doesn't force callers to handle checked exceptions, so the docs are where
  they learn about them.
- Use `assert` for invariants and in tests. Groovy's power assertions are
  always enabled and print every value in the failed expression. Never use
  them to validate input from outside the program; throw an exception
  instead.

## Resources

- **Close every resource with Groovy's `with…` methods**, or with
  try-with-resources. They close the resource on every path, including
  exceptions:

  ```groovy
  path.withReader('UTF-8') { reader ->
      reader.eachLine { line -> process(line) }
  }

  connection.withCloseable {
      it.send(request)
  }
  ```

- A class that holds a resource implements `AutoCloseable`.
- Whoever opens a resource closes it. A method that receives an open stream
  doesn't close it, unless its documentation says it does.

## Collections and closures

- **Use the Groovy Development Kit's collection methods** instead of
  hand-written loops that build collections:

  | Method | Use it to |
  | --- | --- |
  | `collect` | Transform each element |
  | `findAll` / `find` | Filter elements, or find the first match |
  | `any` / `every` | Test whether some or all elements match |
  | `groupBy` / `countBy` | Group or count elements by a key |
  | `collectEntries` | Build a map |
  | `inject` | Fold the elements into one value |
  | `sum` / `max` / `min` | Total or pick an element |

- Use the **spread operator** to call the same property or method on every
  element: `orders*.customerName`.
- **Keep closures free of side effects** when they're passed to `collect`,
  `findAll` and similar methods. Collect the result instead of changing
  external state.
- Don't modify a collection while iterating over it. Use `removeAll { … }`
  or build a new collection.
- Use `each` only for side effects, never to build a collection.

## Strings

- **Don't use a GString as a map key or set element.** A GString's hash code
  differs from the equal `String`'s, so a lookup with one misses entries
  stored with the other. Convert it with `toString()` first.
- Build strings in loops with a `StringBuilder` or `join()`, not with `+`.
- Always pass a charset (usually `'UTF-8'`) when reading or writing text.

## Numbers and equality

- **Decimal literals are `BigDecimal`**, so `0.1 + 0.2 == 0.3` is true. Use
  this for money. Add a `d` suffix only when you need a `double`.
- **Dividing two integers with `/` gives a `BigDecimal`**: `7 / 2` is `3.5`.
  Use `intdiv()` for integer division.
- **`==` calls `equals()`, or `compareTo()` for `Comparable` objects,** and
  handles `null` safely. Use `is()` only for deliberate identity checks.
- Because `==` uses `compareTo()` for `Comparable` objects, keep
  `compareTo()` consistent with `equals()` in your own classes.
- If you override `equals()`, override `hashCode()` too. `@EqualsAndHashCode`
  does both for you.

## Metaprogramming

- **Prefer compile-time techniques** (AST transformations, traits, extension
  modules) to run-time metaprogramming. They're visible to the type checker
  and to readers.
- **Don't change the metaclass of classes you don't own** (`String`,
  `Integer`, …) at run time. The change is global and affects every caller.
- Use `methodMissing` and `propertyMissing` only in DSLs that need open-ended
  method names, and document what they handle.

## Scripts

- **Declare every variable in a script** with `def` or a type. An undeclared
  variable goes into the script's shared binding, where any other code can
  read and change it.
- Use `@Field` for a script-level variable that methods in the script need to
  see.
- **Keep logic in classes, not scripts.** A script should parse arguments and
  call into classes that can be tested on their own.

## Concurrency

- **Prefer immutable objects for shared data.** They need no locking.
- **Use `java.util.concurrent`** (executors, `ConcurrentHashMap`, atomics,
  latches) instead of raw threads and `wait()`/`notify()`.
- Don't let a closure that runs on another thread change local variables
  captured from the enclosing method. Groovy allows it, but nothing makes it
  thread-safe.
- **Document thread safety** on every class shared between threads, and keep
  synchronised sections short.
- Always shut down the executors you create.

## API design

- **Keep APIs small.** It's easy to add a method later and impossible to
  remove one.
- **Give public methods explicit types** (see
  [Types and `def`](coding-style.md#types-and-def)). Callers and tools then
  know what goes in and what comes out.
- **Avoid `boolean` parameters.** Use named arguments, an enum or two methods,
  so each call site says what it means.
- **Use named arguments** for constructors and methods with several optional
  values: `new Server(host: 'localhost', port: 8080)`.
- Validate parameters at the start of every public method, and document what
  it rejects.

## Performance

- **Measure before you optimise**, and optimise what the profiler points at.
- Use `@CompileStatic` on hot code. Dynamic dispatch is far slower than static
  calls.
- Choose the right algorithm and data structure first.

## Sources

- [Apache Groovy style guide](https://groovy-lang.org/style-guide.html)
- [Groovy language documentation](https://groovy-lang.org/documentation.html)
  (semantics, operators, Groovy truth, GStrings)
- [Groovy Development Kit](https://groovy-lang.org/groovy-dev-kit.html)
- [Groovy AST transformations](https://docs.groovy-lang.org/latest/html/documentation/#_available_ast_transformations)
- [Groovy type checking and static compilation](https://docs.groovy-lang.org/latest/html/documentation/#_static_type_checking)
