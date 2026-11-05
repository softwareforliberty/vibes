# Kotlin Idioms and Principles

How to write Kotlin well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
Kotlin code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. A plain `if` beats a chain of scope functions that does the same
  thing.
- **Minimise mutability.** Prefer `val` to `var`, and read-only types to
  mutable ones. A value that can't change can't be changed wrongly, and can be
  shared freely between threads and coroutines.
- **Minimise visibility.** Give every declaration the narrowest visibility
  that works. Anything public is a promise you have to keep.
- **Make illegal states unrepresentable.** Model data so that invalid
  combinations can't be built, using non-null types, sealed hierarchies and
  value classes.
- **Fail fast.** Validate inputs where they enter, and fail as soon as
  something is wrong, close to the cause.

## Classes and types

- Classes are `final` by default. **Only mark a class `open` when it's
  designed for inheritance**, and document which members subclasses may
  override.
- **Prefer composition to inheritance.** Kotlin's class delegation
  (`class LoggingStore(store: Store) : Store by store`) makes wrapping as
  short as extending.
- **Use a `data class` for plain data carriers.** It gives you `equals()`,
  `hashCode()`, `toString()` and `copy()` that can't drift out of date. Make
  its properties `val`.
- **Use sealed classes and interfaces for closed hierarchies**, such as the
  states of a screen or the results of an operation. A `when` over them is
  exhaustive, so adding a case is a compile error until every `when` handles
  it:

  ```kotlin
  sealed interface PaymentResult {
      data class Approved(val receipt: Receipt) : PaymentResult
      data class Declined(val reason: String) : PaymentResult
      data object Pending : PaymentResult
  }
  ```

- **Use enums for fixed sets of simple values**, and sealed types when each
  case carries different data.
- **Wrap primitive identifiers and units in value classes**
  (`@JvmInline value class OrderId(val value: String)`). The compiler then
  stops you passing a customer ID where an order ID is expected, at no
  run-time cost.
- **Use `object` for true singletons** that have no state, or state that's
  genuinely global. Anything with dependencies should be a class that's
  passed in.
- **Prefer top-level functions to utility objects.** A function that belongs
  to no class can live at the top level of a file, without wrapping it in an
  `object`.

## Immutability

- Use **`val`** unless the variable really has to be reassigned.
- **Declare collections with read-only types** (`List`, `Set`, `Map`) and
  create them with `listOf()`, `setOf()` and `mapOf()`. Use the mutable types
  only for local variables that are being built up.
- **Don't expose a mutable collection.** Keep the mutable version `private`
  and expose a read-only view through a [backing property](coding-style.md#naming).
- To change a data class, **make a modified copy** with `copy()` instead of
  making its properties `var`.

## Null safety

- **Prefer non-null types.** Make a type nullable only when "absent" is a real,
  meaningful state.
- **Don't use `!!`.** It throws a bare `NullPointerException` far from the
  cause. Use `?.`, `?:`, or a check that explains itself:

  ```kotlin
  val customer = order.customer ?: return Result.NotFound
  val email = requireNotNull(customer.email) { "Customer ${customer.id} has no email" }
  ```

- Use `?.let { … }` to run code only when a value isn't `null`. For more than
  a few lines, a plain `if (x != null)` reads better and smart-casts `x`.
- **Return an empty collection, not `null`,** when there's nothing to return.
- **Give Java platform types an explicit type** at the boundary. A value
  coming from Java code has an unknown nullability, so declare it as `String`
  or `String?` where it enters your code.
- Use `lateinit` only for properties a framework sets after construction
  (dependency injection, test setup). Never use it to dodge thinking about
  initialisation order.

## Errors and exceptions

- **Use exceptions for programming errors and truly exceptional failures**,
  such as broken invariants, I/O failure or a misconfigured system.
- **Model expected failures in the return type**, with a sealed result type
  or a nullable return, so callers can't forget to handle them. A declined
  payment is an expected outcome, not an exception.
- **Check preconditions with the standard functions**, which throw the right
  exception with your message:

  | Function | Throws | Use for |
  | --- | --- | --- |
  | `require(cond) { msg }` | `IllegalArgumentException` | Bad arguments |
  | `requireNotNull(x) { msg }` | `IllegalArgumentException` | A required argument that's `null` |
  | `check(cond) { msg }` | `IllegalStateException` | Calls made in the wrong state |
  | `checkNotNull(x) { msg }` | `IllegalStateException` | State that should never be `null` |
  | `error(msg)` | `IllegalStateException` | Code paths that should be unreachable |

- **Catch specific exceptions.** Don't catch `Exception` or `Throwable` except
  at the top level of a thread, request or coroutine, where the job is to log
  the failure and keep running.
- **Never swallow an exception.** Handle it, rethrow it, or wrap it with the
  original as the cause.
- **Never catch `CancellationException` without rethrowing it.** Swallowing it
  breaks coroutine cancellation. This also rules out `runCatching` around a
  call that suspends, because it catches everything.
- **Log or throw, not both.** Logging and rethrowing the same exception
  reports one failure several times.
- Document the exceptions a public function throws with `@throws` in its
  KDoc. Kotlin has no checked exceptions, so the docs are the only place
  callers learn about them.

## Resources

- **Close every resource with `use`.** It closes the resource on every path,
  including exceptions:

  ```kotlin
  val lines = Files.newBufferedReader(path).use { it.readLines() }
  ```

- A class that holds a resource implements `AutoCloseable`, so callers can use
  `use` with it.
- Whoever opens a resource closes it. A function that receives an open stream
  doesn't close it, unless its documentation says it does.

## Collections and sequences

- **Use the standard library's higher-order functions** (`filter`, `map`,
  `associateBy`, `groupBy`, `sumOf`, …) instead of hand-written loops that
  build collections.
- Prefer a plain `for` loop to `forEach`, unless the receiver is nullable or
  `forEach` ends a longer chain. A loop supports `break` and `continue`, and
  its `return` means what it looks like.
- **Use a `Sequence`** (`asSequence()`) for long chains over large collections,
  or when you only need the first few results. Each step then runs lazily,
  instead of building a full intermediate list.
- Keep collection operations free of side effects. Don't change external
  state inside `map` or `filter`.
- Use ranges for counting: `for (i in 0..<count)`, `repeat(n) { … }`.

## Functions and lambdas

- **Make a function an extension** when it reads naturally as an operation on
  its receiver. Give extensions the narrowest visibility that works, and keep
  them near the code that uses them.
- **Prefer a property to a function** when the value takes no parameters,
  is cheap to compute, doesn't throw, and returns the same result each time.
- **Use scope functions for their intended job, and don't nest them:**

  | Function | Use it to |
  | --- | --- |
  | `let` | Run code on a non-null value: `email?.let { send(it) }` |
  | `apply` | Configure an object and return it |
  | `also` | Add a side effect, such as logging, without changing a chain |
  | `run` | Compute a value from an object's members |
  | `with` | Call several members of an object without repeating its name |

- Mark a function `infix` only when its two operands play similar roles and
  it reads like an operator: `a to b`, `x shl 2`.
- Use `inline` for higher-order functions whose lambdas are called in place,
  and for `reified` type parameters. Don't inline anything else.

## Concurrency and coroutines

- **Use structured concurrency.** Launch coroutines in a scope tied to a
  lifecycle (a request, a screen, a service), never in `GlobalScope`. When the
  scope ends, its coroutines are cancelled, so none of them leak.
- **Make suspending functions main-safe.** A `suspend` function that blocks
  or does heavy work switches dispatcher itself with
  `withContext(Dispatchers.IO)`, so callers never need to know.
- **Never block inside a coroutine.** Don't call `Thread.sleep()` or blocking
  I/O on a coroutine dispatcher without `withContext`. Use `delay()` to wait.
- **Keep coroutines cancellable.** Long loops check `isActive` or call
  `ensureActive()`, and cleanup code runs in `finally`.
- Expose streams of values as `Flow`, and observable state as `StateFlow`.
  Hold a `MutableStateFlow` privately and expose it read-only.
- **Prefer immutable data for anything shared** between coroutines or threads.
  When shared mutable state is unavoidable, guard it with a `Mutex` or keep it
  confined to one coroutine, and say so in a comment.
- `@Volatile` makes single reads and writes visible, but doesn't make
  compound actions like `count++` atomic. Use an atomic type or a `Mutex`.

## API design

- **Keep APIs small.** It's easy to add a function later and impossible to
  remove one.
- **Use default arguments instead of overloads**, and annotate with
  `@JvmOverloads` when Java callers need the overloads.
- **Avoid `Boolean` parameters** in public APIs. A named enum or a sealed
  type says what each option means.
- **Accept the most general type, return the most specific useful one.**
- Validate arguments at the start of every public function with `require`,
  and document what's rejected.
- Use `Duration` (`5.seconds`) for time, not bare `Long` milliseconds.
- When Java callers matter, check how the API looks from Java, and use
  `@JvmStatic`, `@JvmName` and `@JvmField` where they make it read naturally.

## Equality

- Use `==` for structural equality (it calls `equals()`, and handles `null`).
  Use `===` only for deliberate identity checks.
- If you override `equals()`, override `hashCode()` too, based on the same
  properties. A data class does both for you.
- Base equality only on properties that never change. An object whose hash
  code changes gets lost inside a `HashSet`.

## Performance

- **Measure before you optimise**, with a profiler or a benchmark harness such
  as kotlinx-benchmark, and optimise what the measurement points at.
- Choose the right algorithm and data structure first.
- In hot code, avoid needless boxing (`IntArray` over `Array<Int>`) and needless
  intermediate collections (use a `Sequence`).

## Sources

- [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
  (idiomatic use of language features)
- [Kotlin idioms](https://kotlinlang.org/docs/idioms.html)
- [Kotlin API guidelines](https://kotlinlang.org/docs/api-guidelines-introduction.html)
- [Coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [Kotlin null safety](https://kotlinlang.org/docs/null-safety.html)
