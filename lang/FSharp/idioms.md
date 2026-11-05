# F# Idioms and Principles

How to write F# well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
F# code correct, safe and maintainable. Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. A named function beats a long point-free composition nobody can
  follow.
- **Immutable by default.** Values, records and collections don't change. A
  value that can't change can't be changed wrongly, and can be shared between
  threads.
- **Make illegal states unrepresentable.** Model the domain with records and
  unions so invalid combinations can't be built at all.
- **Keep side effects at the edges.** Pure functions in the core, I/O at the
  boundary. Pure code is easy to test and to reason about.
- **Minimise visibility.** Mark helpers `private` or `internal`. Anything
  public is a promise you have to keep.

## Types

- **Use records for data** and **discriminated unions for choices.** A union
  makes every case explicit, and the compiler checks every match covers them:

  ```fsharp
  type Shipping =
      | Standard
      | Express of deliverBy: DateOnly
      | Collect of storeId: StoreId
  ```

- **Wrap primitive identifiers and constrained values in single-case unions**
  with a private constructor, so only a validating function can build them:

  ```fsharp
  type Email = private Email of string

  module Email =
      let create (text: string) : Result<Email, string> =
          if text.Contains('@') then Ok(Email text) else Error "Email must contain @"

      let value (Email text) = text
  ```

- Use **units of measure** (`decimal<gbp>`, `float<m/s>`) for quantities that
  must not be mixed up.
- Use classes only for .NET interop, for objects that own resources, or for
  stateful services. Put plain functions in modules.

## Option, Result and exceptions

- **Use `Option` for values that may be absent.** Never use `null` in F#
  code. Convert at the boundary with `Option.ofObj` and `Option.ofNullable`
  when a .NET API can return `null`.
- **Use `Result` for expected failures**, such as validation errors or a
  declined payment, so callers can't forget to handle them. Model the error
  as a union when callers need to tell errors apart.
- **Use exceptions for programming errors and truly exceptional failures**
  (broken invariants, I/O failure). Use `invalidArg` and `invalidOp` for bad
  arguments and calls in the wrong state.
- **Don't use `Option.get` or `List.head`** outside tests. They throw on the
  empty case, which is exactly what the type was meant to make you handle.
  Match on the value, or use `Option.defaultValue` and `List.tryHead`.
- **Catch specific exceptions** with `:?` patterns, and only where you can do
  something about them.

## Pattern matching

- **Keep matches complete.** The compiler warns about incomplete matches, and
  the build treats that warning as an error.
- **Don't use a wildcard `_` case on a union you own.** It hides the cases
  you add later. List every case instead, so adding one is a compile error
  until every match handles it.
- Use active patterns to name a complex condition that several matches share.

## Functions and pipelines

- **Write small functions that do one thing**, and compose them with `|>`.
- **Put the "data" parameter last**, so functions work in a pipeline:
  `List.filter isOverdue invoices`.
- Prefer a named function or a short lambda to deep point-free composition
  with `>>`. Readers shouldn't need to rebuild the arguments in their head.
- Use partial application for configuration
  (`let sendWith client = send client`), not for hiding important arguments.

## Collections

- Use **`list`** for small, immutable sequences you build and pattern-match,
  **`array`** for performance-sensitive or indexed data, and **`seq`** for
  lazy or very large sequences.
- **Remember `seq` is lazy.** It runs every time it's enumerated, so
  materialise it with `List.ofSeq` or `Seq.toArray` before enumerating it
  twice, and never let a `seq` outlive the resource it reads from.
- Use `Map` and `Set` for immutable lookups. Use .NET mutable collections
  only inside a function that hides the mutation.

## Computation expressions

- Use **`task { }`** for code that calls or is called by .NET async APIs. It
  produces a `Task` directly, with no conversion.
- Use **`async { }`** for F#-only code that benefits from its cold start and
  built-in cancellation token passing.
- Don't mix them inside one call chain without a reason; convert at the
  boundary with `Async.AwaitTask` or `Async.StartAsTask`.
- **Never block on an async result** with `Async.RunSynchronously` or
  `.Result`, except at the very top of a console program.
- Pass a `CancellationToken` through every `task { }` that does I/O or long
  work.

## Resources

- **Dispose every `IDisposable`** with `use` (or `use!` inside a computation
  expression). It disposes the value when it goes out of scope, on every path:

  ```fsharp
  let readAll (path: string) : string =
      use reader = new StreamReader(path)
      reader.ReadToEnd()
  ```

- Create disposable objects with `new` (`new StreamReader(path)`). The
  compiler warns when a disposable is created without it, so `new` marks
  every place a resource starts its life.
- Whoever creates a resource disposes it.

## Interop with C# and .NET

- **Expose an object-friendly surface to C# callers.** Public APIs meant for
  C# use methods on types with tupled parameters, not curried functions.
- **Don't expose F# types C# handles badly** in a C#-facing API. Convert
  `Option` to a nullable value or a `Try` method, `list` to
  `IReadOnlyList<T>`, and `Async` to `Task`.
- Use `[<CompiledName>]` when a function's F# name and its .NET name should
  differ.
- Check every value coming from a .NET API that may return `null`, at the
  boundary.

## Concurrency

- **Prefer immutable data** for anything shared. Most F# code needs no locks
  at all.
- Run independent work concurrently with `Task.WhenAll` or `Async.Parallel`.
- Use a `MailboxProcessor` (agent) to own mutable state that several threads
  update, instead of locks.
- When a lock is unavoidable, use `lock` on a private object, and keep the
  locked block short and free of `await`.

## Security

- **Never build SQL, shell commands or file paths by concatenating input.**
  Use parameterised queries and argument lists.
- **Never deserialise untrusted data into arbitrary types.** Use a JSON
  library with known target types.
- Use `RandomNumberGenerator` for anything security-related, never
  `System.Random`.
- Keep secrets out of source and configuration files; load them from the
  environment or a secret store.

## Performance

- **Measure before you optimise**, with a profiler or BenchmarkDotNet, and
  optimise what the measurement points at.
- Choose the right algorithm and data structure first.
- In hot code, prefer arrays to lists, avoid `seq` pipelines in tight loops,
  and consider struct tuples (`struct (a, b)`) and `[<Struct>]` unions to
  avoid allocations.

## Sources

- [F# coding conventions](https://learn.microsoft.com/dotnet/fsharp/style-guide/conventions)
- [F# component design guidelines](https://learn.microsoft.com/dotnet/fsharp/style-guide/component-design-guidelines)
- [F# for fun and profit: designing with types](https://fsharpforfunandprofit.com/series/designing-with-types/)
- [Async programming in F#](https://learn.microsoft.com/dotnet/fsharp/tutorials/async)
- [Task expressions](https://learn.microsoft.com/dotnet/fsharp/language-reference/task-expressions)
