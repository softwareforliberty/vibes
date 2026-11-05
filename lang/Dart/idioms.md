# Dart Idioms and Principles

How to write Dart well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Dart code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Clarity beats cleverness.** Prefer the obvious version unless profiling
  proves it too slow.
- **Let the type system work.** Sound null safety and exhaustive pattern
  matching catch whole classes of bugs at compile time, but only if the code
  doesn't switch them off with `!`, `dynamic` or casts.
- **Immutable by default.** Make fields `final` and values `const`. Data that
  can't change can't be changed by surprise.
- **Fail loudly.** Throw on bugs, and never swallow an exception without
  handling it.
- **Every future is awaited or deliberately left running.** A future nobody
  awaits loses its errors.

## Null safety

- **Make a type nullable only when "no value" is a real state.** Most fields
  and parameters should be non-nullable.
- **Never use the `!` operator to silence the compiler.** Check for `null`
  instead, and let flow analysis promote the variable:

  ```dart
  final customer = order.customer;
  if (customer == null) {
    return null;
  }
  return customer.email;
  ```

- Use `?.` and `??` for short null-aware expressions:
  `final name = user?.name ?? 'guest';`.
- Use `late` only when a field is always set before it's read and can't be
  set in the constructor. Reading an unset `late` field throws at run time.
- Copy a nullable field into a local before testing it. Only private
  `final` fields can be promoted; any other field could be changed by a
  getter, subclass or other method between the check and the use.

## Data and immutability

- **Model data as immutable classes** with `final` fields and a `const`
  constructor, and return a modified copy instead of changing an instance:

  ```dart
  final class Order {
    const Order({required this.id, required this.items, this.paid = false});

    final String id;
    final List<LineItem> items;
    final bool paid;

    Order markPaid() => Order(id: id, items: items, paid: true);
  }
  ```

- `final` stops reassignment, not mutation. Expose lists and maps as
  unmodifiable views (`List.unmodifiable(items)`) when callers mustn't change
  them.
- **Use records for small groups of values** returned together, instead of a
  one-off class or a list:

  ```dart
  (int count, int total) summarise(List<LineItem> items) {
    var total = 0;
    for (final item in items) {
      total += item.priceCents * item.quantity;
    }
    return (items.length, total);
  }
  ```

- **Use `sealed` class hierarchies for values with several shapes.** A
  `switch` over a sealed type must handle every subtype, so adding one breaks
  the build until every `switch` handles it:

  ```dart
  sealed class Payment {}

  final class CardPayment extends Payment {
    CardPayment(this.last4);
    final String last4;
  }

  final class InvoicePayment extends Payment {
    InvoicePayment(this.dueDate);
    final DateTime dueDate;
  }

  String describe(Payment payment) => switch (payment) {
    CardPayment(:final last4) => 'Card ending $last4',
    InvoicePayment(:final dueDate) => 'Invoice due $dueDate',
  };
  ```

- Use `enum` for a fixed set of values, and enhanced enums when each value
  carries data.
- Use class modifiers to state intent: `final` for classes not meant to be
  extended, `interface` for contracts, `base` when subclasses must reuse the
  implementation.

## Errors and exceptions

- **An `Error` is a bug; an `Exception` is a condition the caller can
  handle.** Throw `ArgumentError`, `StateError` and `RangeError` for broken
  preconditions, and never catch them. Throw a class that implements
  `Exception` for expected failures:

  ```dart
  final class OrderNotFoundException implements Exception {
    const OrderNotFoundException(this.id);

    final String id;

    @override
    String toString() => 'OrderNotFoundException: no order $id';
  }
  ```

- **Catch specific types with `on`**, and only where you can do something:
  retry, fall back, or report to the user. A bare `catch (e)` also catches
  bugs.
- Use `rethrow` to pass an exception on after logging or cleanup, so the
  original stack trace is kept.
- Never throw strings or other values that aren't `Error` or `Exception`.
- Release resources in `finally`, or with a helper that takes a callback, so
  they're released on every path.

## Async code

- **Use `async`/`await`**, not `.then()` chains.
- **Never leave a `Future` floating.** Await it, return it, or pass it to
  `unawaited()` from `dart:async` to say explicitly that it runs on its own.
- **Run independent work in parallel** with `Future.wait`, or with
  `.wait` on a record of futures:

  ```dart
  final (user, orders) = await (loadUser(id), loadOrders(id)).wait;
  ```

- Use `Stream` for sequences of values over time, and `await for` to consume
  them. Cancel stream subscriptions you no longer need, so they stop holding
  resources.
- Add a timeout to every network call: `await request.timeout(timeout)`.
- Move long CPU-bound work off the main isolate with `Isolate.run()`, so it
  doesn't block everything else.

## Collections and iteration

- Use `for`-in loops for side effects, and `map`, `where` and `fold` to build
  new values.
- Use collection `if`, `for` and spreads to build collections in one
  expression:

  ```dart
  final lines = [
    header,
    for (final item in items) formatItem(item),
    if (discount > 0) 'Discount: $discount',
  ];
  ```

- Use `whereType<T>()` to filter by type, never a cast inside `map`.
- `map` and `where` return lazy iterables. Call `toList()` when the result is
  iterated more than once or must not change as the source changes.

## Libraries and APIs

- **Keep the public API small.** Export it from the files in `lib/`, and keep
  the implementation in `lib/src/`.
- Pass dependencies in through constructors (a clock, an HTTP client, a
  repository), so tests can supply fakes.
- Use extension methods to add small helpers to types you don't own, not to
  hide complex behaviour.
- Don't use `dart:mirrors`. It's unavailable on most platforms and defeats
  tree shaking.

## Security

- **Validate outside data at the edges.** JSON from `jsonDecode()` is
  `dynamic`. Check each field's type and convert it into a typed class once,
  then pass the typed value inward.
- **Never build shell commands from data.** Use `Process.run()` with the
  executable and an argument list, and don't pass `runInShell: true` with
  outside data.
- Pass values to databases through query parameters, never by string
  concatenation.
- Read secrets from the environment or a secret store at start-up, never
  from source code.
- Commit `pubspec.lock` for applications, so every build uses the same
  dependency versions. Keep dependencies few and audited.

## Testable design

- Write pure functions where you can: same input, same output, no side
  effects.
- Keep I/O at the edges, and test the logic with plain values.
- Test with `package:test`, and group related tests with `group()`.

## Sources

- [Effective Dart: Usage](https://dart.dev/effective-dart/usage)
- [Effective Dart: Design](https://dart.dev/effective-dart/design)
- [Dart language tour](https://dart.dev/language)
- [Sound null safety](https://dart.dev/null-safety)
- [Class modifiers](https://dart.dev/language/class-modifiers)
- [Patterns](https://dart.dev/language/patterns)
