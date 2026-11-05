# Java Idioms and Principles

How to write Java well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
Java code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. Prefer the obvious version unless profiling proves it too slow.
- **Minimise mutability.** An object that can't change can't be changed
  wrongly, and can be shared freely between threads.
- **Minimise accessibility.** Give every class, member and variable the
  narrowest visibility that works. Anything public is a promise you have to
  keep.
- **Fail fast.** Validate inputs where they enter, and throw as soon as
  something is wrong, close to the cause.
- **Let the compiler help.** Prefer designs the type system can check
  (enums, sealed types, generics) over conventions that only reviewers can
  check.

## Classes and encapsulation

- **Make fields `private`.** Expose behaviour through methods, not state
  through fields.
- **Make classes `final` unless they're designed for inheritance.**
  Inheritance couples a subclass to its parent's internals. If a class is
  meant to be extended, document which methods subclasses may override and
  how they're used.
- **Prefer composition to inheritance.** Wrap an object and delegate to it,
  instead of extending a class you don't control.
- **Prefer interfaces to abstract classes** for defining types. A class can
  implement several interfaces, but extend only one class.
- **Use a `record` for plain data carriers.** It gives you a constructor,
  accessors, `equals()`, `hashCode()` and `toString()` that can't drift out
  of date:

  ```java
  public record Money(BigDecimal amount, Currency currency) {
    public Money {
      Objects.requireNonNull(amount);
      Objects.requireNonNull(currency);
    }
  }
  ```

- **Use sealed types for closed hierarchies.** A `sealed interface` with a
  fixed set of implementations lets a `switch` over it be exhaustive.
- **Prefer static factory methods** (`Money.of(…)`, `List.of(…)`) to public
  constructors when a name would help, or when the method may return a cached
  or more specific instance.
- **Use a builder** when a constructor would take many parameters, or
  several of the same type. Callers then name each value as they set it.
- **Use enums, not `int` or `String` constants,** for fixed sets of values.
  Use `EnumSet` and `EnumMap` for sets and maps keyed by them.
- A utility class of static methods is `final` and has a `private`
  constructor, so nobody can instantiate or extend it.

## Immutability

- Make fields **`final`** wherever you can, and make value classes fully
  immutable: `final` class, `private final` fields, no setters.
- **Copy mutable inputs and outputs** at the boundary of an immutable class.
  Otherwise a caller who keeps a reference can change the object's state:

  ```java
  public Order(List<LineItem> items) {
    this.items = List.copyOf(items);
  }
  ```

- **Return unmodifiable collections** (`List.of()`, `List.copyOf()`,
  `Collections.unmodifiableList()`) instead of exposing internal mutable
  ones.
- Prefer `java.time` types (`Instant`, `LocalDate`, `Duration`) for dates and
  times. They're immutable and unambiguous, unlike `Date` and `Calendar`.

## Null handling

- **Don't return `null` for "nothing".** Return an empty collection, an empty
  `Optional`, or a [null object](https://en.wikipedia.org/wiki/Null_object_pattern).
- **Use `Optional` only as a return type** for a value that may be absent.
  Don't use it for fields, parameters or collection elements, where it adds
  allocation and noise without adding safety.
- Never call `Optional.get()` without checking first. Use `orElse()`,
  `orElseThrow()`, `map()` or `ifPresent()`.
- **Check for `null` at the boundary** with `Objects.requireNonNull()`, so a
  bad argument fails immediately with a clear message, not later somewhere
  unrelated.
- Mark values that may be `null` with a `@Nullable` annotation, and treat
  everything else as non-null. Static analysis can then check the rest.

## Exceptions

- **Use checked exceptions for conditions a caller can recover from**, such
  as a declined payment. Use **unchecked exceptions for programming errors**,
  such as a bad argument or a call in the wrong state.
- **Prefer the standard exceptions** when they fit:

  | Exception | Thrown when |
  | --- | --- |
  | `IllegalArgumentException` | An argument has an invalid value |
  | `IllegalStateException` | The object is in the wrong state for the call |
  | `NullPointerException` | A required argument is `null` (via `Objects.requireNonNull()`) |
  | `UnsupportedOperationException` | The object doesn't support the operation |
  | `IndexOutOfBoundsException` | An index is out of range |

- **Catch specific exceptions.** Don't catch `Exception`, `Throwable` or
  `RuntimeException` except at the top level of a thread or request, where
  the job is to log the failure and keep running.
- **Never swallow an exception.** Handle it, rethrow it, or wrap it. When you
  wrap one, pass the original as the cause so the stack trace survives:

  ```java
  } catch (IOException e) {
    throw new StorageException("Could not save order " + order.id(), e);
  }
  ```

- **Log or throw, not both.** Logging and rethrowing the same exception
  reports one failure several times.
- **Put useful detail in the message**: the values involved, not just what
  went wrong.
- Don't use exceptions for ordinary control flow. They're slow, and they hide
  the normal path.
- If `InterruptedException` is caught and not rethrown, restore the flag with
  `Thread.currentThread().interrupt()`, so code higher up still sees it.

## Resources

- **Close every resource with try-with-resources.** It closes the resource on
  every path, including exceptions, and keeps any exception thrown while
  closing as a suppressed exception:

  ```java
  try (BufferedReader reader = Files.newBufferedReader(path)) {
    return reader.lines().toList();
  }
  ```

- A class that holds a resource implements `AutoCloseable`, so callers can use
  try-with-resources with it.
- Whoever opens a resource closes it. A method that receives an open stream
  doesn't close it, unless its documentation says it does.

## Collections and streams

- **Declare variables and parameters as interfaces** (`List`, `Map`, `Set`),
  not implementations (`ArrayList`, `HashMap`). You can then change the
  implementation without changing the callers.
- Use `List.of()`, `Set.of()` and `Map.of()` for small fixed collections.
- **Use streams when they read better than a loop**, typically for a chain of
  filter, map and collect. Use a loop when the logic needs early exits,
  checked exceptions or several pieces of mutable state.
- **Keep stream operations free of side effects.** Don't change external
  state inside `map()` or `filter()`. Collect the result instead.
- Don't modify a collection while iterating over it. Use
  `Iterator.remove()`, `removeIf()` or build a new collection.

## Generics

- **Never use raw types** (`List` instead of `List<String>`). They switch off
  type checking and move errors from compile time to run time.
- Use **bounded wildcards** in API parameters for flexibility. A parameter
  you only read from is `? extends T`, and one you only write to is
  `? super T`:

  ```java
  public static <T> void copy(List<? super T> dst, List<? extends T> src) {
  ```

- Fix every unchecked warning. If one is truly safe, suppress it with
  `@SuppressWarnings("unchecked")` on the smallest possible scope, with a
  comment explaining why.

## Equality and hashing

- Compare objects with `equals()`. Use `==` only for primitives, enums and
  deliberate identity checks.
- **Override `hashCode()` whenever you override `equals()`.** Equal objects
  must have equal hash codes, or hash-based collections break. A `record`
  does this for you.
- Base `equals()` and `hashCode()` only on fields that never change. An
  object whose hash code changes gets lost inside a `HashSet`.
- Use `Objects.equals()` and `Objects.hash()` to handle `null` fields.

## Concurrency

- **Prefer immutable objects for shared data.** They need no locking.
- **Use `java.util.concurrent`** (executors, `ConcurrentHashMap`,
  `CompletableFuture`, latches, atomics) instead of raw `Thread`s and
  `wait()`/`notify()`.
- On Java 21 and later, use **virtual threads** for blocking I/O-bound work,
  instead of sizing a thread pool for it.
- **Document thread safety** on every class shared between threads: say
  whether it's immutable, thread-safe, or must be confined to one thread.
- **Keep synchronised sections short.** Never call unknown code (callbacks,
  overridable methods) while holding a lock. It may block, or take another
  lock and deadlock.
- Always take multiple locks in the same order.
- `volatile` makes single reads and writes visible, but doesn't make compound
  actions like `count++` atomic. Use an `AtomicInteger` or a lock.
- Always shut down the executors you create.

## API design

- **Keep APIs small.** Every public method is something you have to support
  forever. It's easy to add a method later and impossible to remove one.
- **Avoid `boolean` parameters.** `send(order, true)` doesn't say what `true`
  means at the call site. Use an enum or two methods.
- **Avoid long parameter lists**, especially of the same type. Group related
  values into a record, or use a builder.
- **Accept the most general type, return the most specific useful one.**
  Accept `Collection<T>` if any collection will do, return `List<T>` if order
  matters.
- Validate parameters at the start of every public method, and document what
  it rejects in the Javadoc's `@throws` tags.
- Use `Duration` and named units for time, not bare `long` milliseconds.

## Strings and text

- Build strings in loops with a `StringBuilder`. Concatenating with `+` in a
  loop copies the whole string on every pass.
- Use **text blocks** (`"""`) for multi-line text such as SQL or JSON.
- Always pass a `Charset` (usually `StandardCharsets.UTF_8`) when converting
  between bytes and text. The platform default varies between machines.
- Use the logging framework's placeholders
  (`log.info("Shipped order {}", id)`) instead of building the message
  yourself, so the string is only built when the level is enabled.

## Performance

- **Measure before you optimise**, with a profiler or a benchmark harness
  such as JMH, and optimise what the measurement points at.
- Choose the right algorithm and data structure first.
- Avoid unnecessary boxing in hot code: prefer `int` to `Integer`, and
  `IntStream` to `Stream<Integer>`.

## Sources

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [Effective Java](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/),
  3rd edition, by Joshua Bloch
- [Java SE API documentation](https://docs.oracle.com/en/java/javase/21/docs/api/)
  (`Objects`, `Optional`, `java.util.concurrent`, `java.time`)
- [Error Prone bug patterns](https://errorprone.info/bugpatterns)
