# Visual Basic Idioms and Principles

How to write Visual Basic well. [coding-style.md](coding-style.md) covers how
code looks. This guide covers how it's designed: the idioms and principles that
keep Visual Basic code correct, safe and maintainable. Every example follows
the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. A plain loop beats a LINQ query nobody can follow.
- **Let the compiler check types.** `Option Strict On` everywhere means no
  late binding and no silent narrowing conversions, so type errors fail the
  build instead of the program.
- **Minimise mutability.** Prefer `ReadOnly` fields and properties. A value
  that can't change can't be changed wrongly, and can be shared between
  threads.
- **Minimise visibility.** Give every type and member the narrowest access
  that works. Anything `Public` is a promise you have to keep.
- **Fail fast.** Validate inputs where they enter, and fail close to the
  cause.

## Types

- **Mark classes `NotInheritable`** unless they're designed for inheritance.
  Inheritance is a contract; `NotInheritable` says there isn't one.
- **Prefer composition to inheritance.** Wrap and delegate instead of
  subclassing to reuse code.
- **Make data carriers immutable**: `ReadOnly` properties set in the
  constructor, with `Equals` and `GetHashCode` overridden together when
  callers compare values. Visual Basic can't declare records, so write these
  by hand, or put shared data types in a C# project.
- Use a `Structure` for small values that are copied often, such as money or
  coordinates, and make it immutable.
- Use `Module` only for extension methods and stateless helpers. Its members
  are shared and visible without qualification, which makes them easy to
  call by accident from anywhere.
- Use `Enum` for fixed sets of simple values. Mark flag enums `<Flags>` and
  give them power-of-two values.

## Nothing handling

- Visual Basic has no nullable reference type annotations, so **document
  which parameters and return values may be `Nothing`**, and validate public
  arguments:

  ```vb
  ArgumentNullException.ThrowIfNull(order)
  ArgumentException.ThrowIfNullOrWhiteSpace(customerName)
  ```

- Use `?.` and `If(value, default)` instead of explicit checks that only pick
  a default.
- **Return an empty collection, not `Nothing`**, when there's nothing to
  return.
- Use the `Try` pattern
  (`Function TryParse(text As String, ByRef order As Order) As Boolean`) when
  absence is a normal outcome.

## Exceptions

- **Use `Try`/`Catch`/`Finally`. Never use `On Error`**, which hides where an
  error came from and is easy to leave switched on by mistake.
- **Use exceptions for exceptional failures** (broken invariants, I/O
  failure, bad configuration), not for normal control flow.
- **Catch specific exceptions.** Catch `Exception` only at the top of a
  request, message handler or thread, where the job is to log and keep
  running.
- **Rethrow with `Throw`** on its own, never `Throw ex`, which loses the
  original stack trace.
- Use an exception filter (`Catch e As IOException When IsRetryable(e)`)
  instead of catching, checking and rethrowing.
- **Log or throw, not both.** Logging and rethrowing reports one failure
  several times.

## Resources

- **Dispose every `IDisposable` you create**, with a `Using` block:

  ```vb
  Using reader As New StreamReader(path)
      Return reader.ReadToEnd()
  End Using
  ```

- Visual Basic has no `Await Using`. Call `DisposeAsync` yourself in a
  `Finally` block for resources that only offer async disposal.
- A class that owns a disposable field implements `IDisposable` itself, and
  disposes the field.
- Whoever creates a resource disposes it.

## Async

- **Go async all the way.** Never block on a task with `.Result` or
  `.Wait()`. Blocking wastes a thread and can deadlock.
- **Take a `CancellationToken` as the last parameter** of every async method
  that does I/O or long work, and pass it on to everything you call.
- **Never write `Async Sub`**, except for event handlers. An exception in an
  `Async Sub` can't be caught, and crashes the process.
- In library code, use `ConfigureAwait(False)` on every `Await`.
- Run independent operations concurrently with `Task.WhenAll`.

## Collections and LINQ

- **Remember LINQ is deferred.** A query runs every time it's enumerated.
  Call `ToList()` once when you'll enumerate the result more than once.
- Use `Any()` to test for elements, not `Count() > 0`.
- Keep queries free of side effects.
- Accept `IEnumerable(Of T)` and return `IReadOnlyList(Of T)`, and don't
  expose a mutable collection.

## Equality and strings

- Keep `Option Compare Binary` (the default), and **pass a
  `StringComparison`** to `String.Equals`, `StartsWith`, `EndsWith` and
  `IndexOf`. Use `Ordinal` for identifiers and keys; use the current culture
  only for text shown to people.
- Format and parse machine-readable values with
  `CultureInfo.InvariantCulture`, so a server's locale can't change them.

## Legacy features

Visual Basic keeps many features from VB6 for compatibility. New code uses
the .NET equivalents, which behave the same in every .NET language:

| Avoid | Use instead | Why |
| --- | --- | --- |
| `On Error`, `Resume` | `Try`/`Catch` | Structured, and shows where errors come from |
| `IIf` | `If(condition, a, b)` | `IIf` evaluates both branches |
| `Left`, `Mid`, `Len`, `InStr` | `String` methods | Zero-based, and consistent with other .NET code |
| `Microsoft.VisualBasic.Collection` | `List(Of T)`, `Dictionary(Of TKey, TValue)` | Typed, zero-based |
| Late binding (`Object` calls) | Typed variables | `Option Strict` forbids it anyway |

## Interop with C# and .NET

- Visual Basic can't use every newer .NET feature. Keep code that needs one
  (for example, heavy `Span(Of T)` work) in a small C# project, and call it
  from Visual Basic.
- Keep `Module` members out of public APIs. Other .NET languages see them as
  members of a static class, so they lose the unqualified calls that make
  them convenient in Visual Basic.

## Concurrency

- **Prefer immutable data** for anything shared between threads.
- Guard shared mutable state with `SyncLock` on a `Private ReadOnly` object.
  Never lock on `Me`, a type or a string, which outside code can lock too.
- Visual Basic forbids `Await` inside `SyncLock`. Use
  `SemaphoreSlim.WaitAsync` for mutual exclusion around async code.
- Use `Interlocked` for single counters and `ConcurrentDictionary` for shared
  maps.

## Security

- **Never build SQL, shell commands or file paths by concatenating input.**
  Use parameterised queries, argument lists, and a check that a resolved path
  stays inside the allowed directory.
- **Never deserialise untrusted data into arbitrary types.** Don't use
  `BinaryFormatter` (removed in .NET 9). Use `System.Text.Json` with known
  target types.
- Use `RandomNumberGenerator` for anything security-related, never `Random`
  or `Rnd`.
- Keep secrets out of source and configuration files; load them from the
  environment or a secret store.

## API design

- **Keep public APIs small.** It's easy to add a member later and impossible
  to remove one.
- **Avoid `Boolean` parameters** in public APIs. An enum says what each
  option means at the call site.
- Use `TimeSpan` for durations and `DateTimeOffset` for points in time.

## Performance

- **Measure before you optimise**, with a profiler or BenchmarkDotNet, and
  optimise what the measurement points at.
- Choose the right algorithm and data structure first.
- In hot code, avoid boxing value types into `Object`, and build strings with
  `StringBuilder` in loops.
- **Stream large input** with `File.ReadLines` or a `StreamReader`, rather than
  `File.ReadAllText` or `File.ReadAllLines`, which read the whole file into
  memory.
- **Memory-map a large file that's read at random positions or many times**
  with `MemoryMappedFile.CreateFromFile` and a view from `CreateViewAccessor`,
  each in a `Using` block. Don't map a file you read once from start to end,
  where buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.

## Sources

- [Visual Basic coding conventions](https://learn.microsoft.com/dotnet/visual-basic/programming-guide/program-structure/coding-conventions)
- [.NET Framework Design Guidelines](https://learn.microsoft.com/dotnet/standard/design-guidelines/)
- [Best practices for exceptions](https://learn.microsoft.com/dotnet/standard/exceptions/best-practices-for-exceptions)
- [Best practices for comparing strings](https://learn.microsoft.com/dotnet/standard/base-types/best-practices-strings)
- [BinaryFormatter security guide](https://learn.microsoft.com/dotnet/standard/serialization/binaryformatter-security-guide)
