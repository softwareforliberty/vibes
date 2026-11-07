# C# Idioms and Principles

How to write C# well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
C# code correct, safe and maintainable. Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. A plain loop beats a LINQ query nobody can follow.
- **Minimise mutability.** Prefer `readonly` fields, `init` properties and
  records. A value that can't change can't be changed wrongly, and can be
  shared between threads.
- **Minimise visibility.** Give every type and member the narrowest access
  that works. Anything `public` is a promise you have to keep.
- **Make illegal states unrepresentable.** Use non-nullable types, `required`
  members and small domain types so invalid objects can't be built.
- **Fail fast.** Validate inputs where they enter, and fail close to the
  cause.

## Types

- **Seal classes that aren't designed for inheritance.** Inheritance is a
  contract; `sealed` says there isn't one, and lets the runtime devirtualise
  calls.
- **Prefer composition to inheritance.** Wrap and delegate instead of
  subclassing to reuse code.
- **Use a `record` for data carriers.** It gives you value equality,
  `ToString()` and non-destructive mutation (`with`) that can't drift out of
  date:

  ```csharp
  public sealed record Address(string Street, string City, string PostCode);
  ```

- **Use a `readonly record struct`** for small values that are copied often,
  such as money or coordinates.
- **Wrap primitive identifiers in their own types**
  (`readonly record struct OrderId(Guid Value)`). The compiler then stops you
  passing a customer ID where an order ID is expected.
- **Use `required` members** for properties that must be set, so object
  initialisers can't leave them out.
- Use `enum` for fixed sets of simple values. Mark flag enums `[Flags]` and
  give them power-of-two values.
- Keep `static` classes for stateless helpers and extension methods only.

## Immutability

- Make fields `readonly` and properties `{ get; }` or `{ get; init; }` unless
  they really change.
- **Don't expose mutable collections.** Return `IReadOnlyList<T>`,
  `IReadOnlyDictionary<TKey, TValue>` or an immutable collection, and keep the
  mutable one `private`.
- Change a record with `with` instead of making its properties settable.

## Nullability

- **Nullable reference types are on.** A type without `?` is never `null`;
  a type with `?` might be, and the compiler makes you check.
- **Treat every nullable warning as a bug**, and fix it instead of
  suppressing it.
- **Don't use the null-forgiving operator `!`** to silence a warning. Check
  the value, or fix the type. It's acceptable only where the compiler can't
  see an invariant you can prove, with a comment saying why.
- **Validate public arguments** with the throw helpers:

  ```csharp
  ArgumentNullException.ThrowIfNull(order);
  ArgumentException.ThrowIfNullOrWhiteSpace(customerName);
  ArgumentOutOfRangeException.ThrowIfNegative(quantity);
  ```

- **Return an empty collection, not `null`**, when there's nothing to return.
- Use the `Try` pattern (`bool TryParse(string s, out Order order)`) when
  absence is a normal outcome, and annotate the `out` parameter with
  `[NotNullWhen(true)]`.

## Exceptions

- **Use exceptions for exceptional failures** (broken invariants, I/O
  failure, bad configuration), not for normal control flow.
- **Throw the most specific built-in type that fits**
  (`ArgumentException`, `InvalidOperationException`), or your own type
  derived from `Exception` when callers need to catch it specifically.
- **Catch specific exceptions.** Catch `Exception` only at the top of a
  request, message handler or thread, where the job is to log and keep
  running.
- **Rethrow with `throw;`**, never `throw ex;`, which loses the original
  stack trace.
- **Wrap with the original as the inner exception** when you translate one
  exception into another.
- **Log or throw, not both.** Logging and rethrowing reports one failure
  several times.
- Use an exception filter (`catch (IOException e) when (IsRetryable(e))`)
  instead of catching, checking and rethrowing. The stack isn't unwound for
  exceptions the filter rejects.

## Resources

- **Dispose every `IDisposable` you create**, with a `using` declaration:

  ```csharp
  using var stream = File.OpenRead(path);
  using var reader = new StreamReader(stream);
  return reader.ReadToEnd();
  ```

- Use `await using` for `IAsyncDisposable` resources.
- A class that owns a disposable field implements `IDisposable` itself, and
  disposes the field. Seal it, so you can skip the full dispose pattern.
- Whoever creates a resource disposes it. A method that receives a stream
  doesn't dispose it unless its documentation says so.

## Async

- **Go async all the way.** Never block on a task with `.Result`, `.Wait()`
  or `.GetAwaiter().GetResult()`. Blocking wastes a thread and can deadlock.
- **Take a `CancellationToken` as the last parameter** of every async method
  that does I/O or long work, and pass it on to everything you call.
- **Never write `async void`**, except for event handlers. An exception in an
  `async void` method can't be caught, and crashes the process.
- In library code, use `ConfigureAwait(false)` on every `await`, so the
  library doesn't depend on the caller's synchronisation context.
- Run independent operations concurrently with `Task.WhenAll`, not one
  `await` after another.
- Return `Task` or `Task<T>`. Use `ValueTask` only when profiling shows the
  allocation matters, and never await a `ValueTask` twice.

## Collections and LINQ

- **Remember LINQ is deferred.** A query runs every time it's enumerated.
  Call `ToList()` or `ToArray()` once when you'll enumerate the result more
  than once.
- Use `Any()` to test for elements, not `Count() > 0`, which may walk the
  whole sequence.
- Keep LINQ free of side effects. Don't change external state inside
  `Select` or `Where`.
- Accept the most general type you need (`IEnumerable<T>`,
  `IReadOnlyCollection<T>`), and return the most specific useful one.

## Equality and strings

- If you override `Equals`, override `GetHashCode` too, from the same members,
  and implement `IEquatable<T>`. A record does all of this for you.
- **Always pass a `StringComparison`** to string comparison, `StartsWith`,
  `EndsWith` and `IndexOf`. Use `Ordinal` (or `OrdinalIgnoreCase`) for
  identifiers, keys and protocols; use the current culture only for text shown
  to people.
- Format and parse machine-readable values with
  `CultureInfo.InvariantCulture`, so a server's locale can't change them.

## Concurrency

- **Prefer immutable data** for anything shared between threads.
- Guard shared mutable state with `lock` on a `private readonly object` (or
  `System.Threading.Lock` on .NET 9 and later). Never lock on `this`, a type
  or a string, which outside code can lock too.
- **Never `await` inside a `lock`.** Use `SemaphoreSlim.WaitAsync` for
  mutual exclusion around async code.
- Use `Interlocked` for single counters and `ConcurrentDictionary` for shared
  maps, instead of hand-rolled locking.

## Security

- **Never build SQL, shell commands or file paths by concatenating input.**
  Use parameterised queries, argument lists and `Path.GetFullPath` with a
  check that the result stays inside the allowed directory.
- **Never deserialise untrusted data into arbitrary types.** Don't use
  `BinaryFormatter` (removed in .NET 9), and don't enable type-name handling
  in JSON serialisers. Use `System.Text.Json` with known target types.
- Use `RandomNumberGenerator` for anything security-related, never
  `Random`.
- Keep secrets out of source and configuration files; load them from the
  environment or a secret store.

## API design

- **Keep public APIs small.** It's easy to add a member later and impossible
  to remove one.
- **Avoid `bool` parameters** in public APIs. An enum says what each option
  means at the call site.
- Use optional parameters for simple defaults, and overloads when the
  parameter lists really differ.
- Use `TimeSpan` for durations and `DateTimeOffset` for points in time, not
  bare numbers or `DateTime` without a kind.

## Performance

- **Measure before you optimise**, with a profiler or BenchmarkDotNet, and
  optimise what the measurement points at.
- Choose the right algorithm and data structure first.
- In hot code, use `Span<T>` and `stackalloc` to avoid allocations, avoid
  boxing value types, and build strings with `StringBuilder` in loops.
- **Stream large input** with `File.ReadLines` or a `StreamReader`, rather than
  `File.ReadAllText` or `File.ReadAllLines`, which read the whole file into
  memory.
- **Memory-map a large file that's read at random positions or many times**
  with `MemoryMappedFile.CreateFromFile` and a view from `CreateViewAccessor`,
  and dispose of both. Don't map a file you read once from start to end, where
  buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.

## Sources

- [C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [.NET Framework Design Guidelines](https://learn.microsoft.com/dotnet/standard/design-guidelines/)
- [Nullable reference types](https://learn.microsoft.com/dotnet/csharp/nullable-references)
- [Best practices for exceptions](https://learn.microsoft.com/dotnet/standard/exceptions/best-practices-for-exceptions)
- [Implement a Dispose method](https://learn.microsoft.com/dotnet/standard/garbage-collection/implementing-dispose)
- [Best practices for comparing strings](https://learn.microsoft.com/dotnet/standard/base-types/best-practices-strings)
- [BinaryFormatter security guide](https://learn.microsoft.com/dotnet/standard/serialization/binaryformatter-security-guide)
