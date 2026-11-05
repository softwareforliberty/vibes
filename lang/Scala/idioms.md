# Scala Idioms and Principles

How to write Scala well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Scala code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Make illegal states unrepresentable.** Model the domain with enums, case
  classes and opaque types, so the compiler rejects values that can't exist.
- **Prefer immutable values.** A value that can't change can be shared,
  cached and reasoned about without tracing every caller.
- **Keep effects at the edges.** Pure functions in the core, I/O in a thin
  outer layer. Pure code is easy to test and safe to reuse.
- **Make failure visible in the type.** A function that can fail returns
  `Option`, `Either` or an effect type, not a value that might secretly be
  `null` or a thrown exception.
- **Be explicit about context.** Contextual abstractions (`given`/`using`)
  remove boilerplate, but every given should be easy to find by its import.
- **Clarity beats cleverness.** Prefer the version a new teammate can read,
  even when a denser one exists.

## Types and modelling

- **Use `enum` for algebraic data types.** A Scala 3 enum declares a closed
  set of cases, and the compiler checks that every `match` covers them all.

  ```scala
  enum PaymentState:
    case Pending
    case Paid(at: Instant)
    case Failed(reason: String)
  ```

- **Use `sealed trait` hierarchies** only when cases need to live in
  separate files or carry shared behaviour that an enum can't express.
- **Use `final case class` for plain data.** It gives structural equality,
  `copy` and pattern matching for free.
- **Wrap primitive identifiers in opaque types** so an `OrderId` can't be
  passed where a `CustomerId` is expected, with no runtime cost:

  ```scala
  object Ids:
    opaque type OrderId = Long

    object OrderId:
      def apply(value: Long): OrderId = value
  ```

- **Validate in a smart constructor.** Make the case class constructor
  `private` and return `Either` from the companion's factory, so every value
  that exists is valid.

## Immutability

- Use `val`, never `var`. If a measured hot loop needs a local `var`,
  suppress the check on that line with a comment saying why, and never let
  the `var` escape the method.
- Use the immutable collections (`List`, `Vector`, `Map`, `Set`), which are
  the defaults. Reach for `scala.collection.mutable` only inside a method,
  for measured performance, and return an immutable result.
- Update data with `copy`, not by mutating fields.

## Absence and errors

- **Never use `null`** in Scala code. Wrap values that may be null from Java
  APIs at the boundary: `Option(javaMap.get(key))`.
- Use `Option` when a value may be absent and the reason doesn't matter.
- Use `Either[E, A]` when a caller needs to know why something failed. Model
  `E` as an enum of the failures the caller can handle.
- **Throw exceptions only for bugs** and truly unrecoverable conditions.
  Expected failures belong in the return type, where the compiler makes
  callers deal with them.
- Never call `.get` on an `Option` or `Either` outside tests. Use `match`,
  `getOrElse`, `fold` or a `for` comprehension.
- Catch exceptions from Java libraries with `Try` at the boundary, then turn
  the result into your own error type with `.toEither` and `left.map`. Never
  catch `Throwable` directly: `Try` only catches `NonFatal` errors, and lets
  the ones that must propagate through.

## Contextual abstractions

- Declare type class instances with `given`, and take them as `using`
  parameters. Put an instance in the companion object of its type, where the
  compiler finds it without an import.
- Use `extension` methods to add operations to a type you don't own.
- **Avoid implicit conversions.** They change the meaning of code invisibly.
  Scala 3 requires an explicit language import to define one, and that cost
  is a warning sign.
- Don't use givens to pass ordinary configuration or services. Pass those as
  explicit parameters, so the call site shows what a function depends on.

## Effects and side effects

- Keep side effects (I/O, time, randomness, logging) at the edges of the
  program, and pass their results into pure functions.
- Inject a clock and a random source instead of calling `Instant.now()` or
  `Random` inside domain logic. Tests can then control them.
- If the project uses an effect library, use it consistently. Mixing raw
  `Future`, blocking calls and effect types in one layer makes errors and
  cancellation unpredictable.
- Never block a thread inside a `Future` or an effect's compute pool. Run
  blocking calls on a dedicated blocking executor.

## Collections

- Prefer `map`, `filter`, `fold` and `for` comprehensions to manual loops.
- Use `Vector` for indexed access and `List` for prepending and pattern
  matching on the head.
- Use `.view` or `Iterator` for long chains over large collections, so
  intermediate collections aren't built.
- Don't use `head`, `last` or `apply(i)` on collections that might be empty
  or short. Use `headOption`, `lastOption` and `lift(i)`.

## Pattern matching

- Make every match on an enum or sealed type exhaustive, and don't add a
  wildcard `case _` that hides new cases. The compiler then warns when a case
  is added.
- Match on structure, not on runtime types (`case s: String`), unless you're
  at an untyped boundary. Never cast with `asInstanceOf`; a failed cast is a
  runtime crash the compiler can't see.

## Equality

- Compare with `==`, which calls `equals` and is null-safe.
- Turn on **strict equality** (`import scala.language.strictEquality`) in new
  code, so comparing values of unrelated types is a compile error.

## API design

- Return the most specific useful immutable type (`List`, `Map`), and accept
  the most general one the function needs (`Iterable`, `Seq`).
- Keep public signatures free of inferred types (see
  [Types](coding-style.md#types)).
- Avoid `Boolean` parameters. A call like `export(report, true)` hides its
  meaning; use an enum instead.
- Keep companion objects for factories and instances, not for unrelated
  utility functions.

## Concurrency

- Share immutable data between threads instead of guarding mutable state
  with locks.
- When state must be shared, keep it in one place behind a single
  concurrency primitive (an `AtomicReference`, an actor, or the effect
  library's `Ref`), and document what it protects.
- Never use `var` fields from more than one thread.

## Testing

- Test pure functions directly with plain values.
- Use property-based tests for code with laws: parsers, serialisers and
  type class instances.

## Sources

- [Scala 3 reference](https://docs.scala-lang.org/scala3/reference/)
- [Scala Style Guide](https://docs.scala-lang.org/style/)
- [Scala 3 book: domain modelling](https://docs.scala-lang.org/scala3/book/domain-modeling-intro.html)
- [Scala 3 reference: contextual abstractions](https://docs.scala-lang.org/scala3/reference/contextual/)
- [Scala 3 reference: multiversal equality](https://docs.scala-lang.org/scala3/reference/contextual/multiversal-equality.html)
