# Swift Idioms and Principles

How to write Swift well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
Swift code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. A plain `if` beats a chain of operators that does the same thing.
- **Prefer value types.** A `struct` or `enum` can't be changed behind your
  back, and can be shared freely between threads.
- **Minimise mutability.** Prefer `let` to `var`. A value that can't change
  can't be changed wrongly.
- **Minimise visibility.** Give every declaration the narrowest access level
  that works. Anything `public` is a promise you have to keep.
- **Make illegal states unrepresentable.** Model data so that invalid
  combinations can't be built, using non-optional types and enums with
  associated values.
- **Let the compiler prove it.** Strict concurrency checking, exhaustive
  `switch`es and non-optional types catch whole classes of bugs before the
  code runs.

## Value and reference types

- **Default to `struct`.** Use a `class` only when you need identity (two
  references to the same object), inheritance, or Objective-C interop.
- Use an **`enum` with associated values** for a value that is exactly one
  of several shapes:

  ```swift
  enum LoadState {
    case idle
    case loading(progress: Double)
    case loaded(Data)
    case failed(any Error)
  }
  ```

- Use an **`actor`** for shared mutable state that several tasks touch (see
  [Concurrency](#concurrency)).
- Mark classes `final` unless they're designed to be subclassed. Subclassing
  is part of a class's public contract, and `final` lets the compiler
  dispatch statically.
- Large value types are cheap to copy when their storage is copy-on-write,
  as the standard collections are. Keep stored properties to types that
  already behave this way, instead of writing your own copy-on-write.

## Optionals

- **Never force-unwrap (`!`) outside tests.** A force unwrap turns a missing
  value into a crash. Unwrap with `if let`, `guard let`, `??` or optional
  chaining, and decide what a missing value means.
- **Never declare implicitly unwrapped optionals (`Type!`)** outside tests.
  They're force unwraps waiting to happen. The one exception is an
  `@IBOutlet`, which the framework fills in before you use it.
- Use `guard let` to unwrap values the rest of the function needs, and exit
  early when they're missing:

  ```swift
  guard let data = cache[key] else {
    return nil
  }
  ```

- Don't use an optional when there's a natural empty value. An empty array or
  string is clearer than `nil`, and callers don't have to unwrap it.
- Don't nest optionals (`Int??`). Flatten them, or use an enum that says what
  each case means.
- Never use `try!` or `as!` outside tests, for the same reason as `!`. Use
  `try` with error handling, and `as?` with a fallback.

## Errors

- **Report recoverable errors by throwing.** A function that can fail is
  marked `throws`, and its documentation lists what it throws.
- Define errors as an **enum conforming to `Error`**, with a case for each
  failure a caller might handle differently:

  ```swift
  enum CacheError: Error {
    case tooLarge(bytes: Int)
    case corrupted(key: String)
  }
  ```

- **Handle each error at the level that can do something about it**: retry,
  fall back, or report to the user. Lower levels let it propagate.
- Don't catch an error just to ignore it. If ignoring it is right, say why
  in a comment.
- Use **`Result`** only where a thrown error can't travel: storing an outcome
  to inspect later, or bridging to a completion-handler API. In `async` code,
  throw instead.
- **Bugs are not errors.** A broken internal assumption is checked with
  `precondition()` (kept in release builds) or `assert()` (debug only), or
  stopped with `fatalError("why")`. Never throw for a programming mistake.
- Never use `try?` to silently turn a meaningful failure into `nil`. Use it
  only where "failed" and "absent" really mean the same thing.

## Protocols and extensions

- **Design around protocols.** Depend on what a type can do (`ImageLoading`),
  not what it is (`URLSessionImageLoader`). Callers and tests can then supply
  any conforming type.
- Keep protocols small and focused. A protocol with one or two requirements
  is easy to conform to and easy to fake in tests.
- Give a requirement a default implementation in a protocol extension only
  when the default is right for nearly every conforming type.
- Use **`some Protocol`** when one concrete type is used throughout, and
  **`any Protocol`** only when the concrete type really varies at run time.
  `some` keeps static dispatch and full type information.
- Use **extensions** to group a type's conformances and to add helpers.
  Don't add `public` extensions to types you don't own: another module could
  add the same member and the two would clash.

## Access control

- Leave declarations `internal` by default, and make them `public` only as
  part of a deliberate API.
- Mark everything that's used only inside a type or file `private`.
- Make a property's setter narrower than its getter where callers should
  only read it: `public private(set) var count = 0`.
- Don't make something `open` unless you've designed it to be overridden
  from other modules.

## Memory

Swift manages memory with automatic reference counting (ARC). A reference
cycle between objects means none of them is ever freed.

- **Capture `self` weakly in escaping closures that an object keeps**, such
  as stored callbacks and observation handlers. A strong capture there forms
  a cycle:

  ```swift
  subscription = store.observe { [weak self] change in
    guard let self else {
      return
    }
    apply(change)
  }
  ```

- Delegates and other back-references are `weak var`.
- Avoid `unowned`. It crashes if the object is gone, so it only saves an
  unwrap at the cost of safety. Use it only when the captured object
  provably outlives the closure.
- A non-escaping closure, such as the one passed to `map`, can't form a
  cycle, so it needs no capture list.

## Concurrency

Use Swift's structured concurrency (`async`/`await`, tasks and actors) for
all new concurrent code.

- **Mark functions `async`** instead of taking completion handlers. The
  compiler then checks that every path returns exactly once.
- **Prefer structured tasks.** Use `async let` for a fixed number of
  concurrent operations, and a `TaskGroup` for a variable number. Their
  child tasks are cancelled and awaited automatically when the scope ends.
- Use an unstructured `Task { }` only to start async work from synchronous
  code. Avoid `Task.detached`: it drops the caller's actor, priority and
  task-local values.
- **Protect shared mutable state with an actor.** Only one task runs on an
  actor at a time, so its state can't race.
- **Run UI code on the `@MainActor`.** Mark view models and other UI types
  `@MainActor` instead of dispatching to the main queue by hand.
- **Make values that cross concurrency boundaries `Sendable`.** Value types
  made of `Sendable` parts already are. Never use `@unchecked Sendable` to
  silence a warning. Use it only when you've made the type thread-safe some
  other way, and say how in a comment.
- **Remember that `await` is a suspension point.** An actor's state can
  change while a method is suspended, so re-check anything you read before
  the `await`.
- **Support cancellation.** Long-running work checks
  `Task.checkCancellation()` or `Task.isCancelled` and stops early.
- Don't block a task: no semaphores, `sleep()` or synchronous waits. Use
  `try await Task.sleep(for:)` and other async APIs.

## Codable

- Conform data-transfer types to `Codable`, and keep them separate from
  domain types when the wire format and the domain model differ. Each can
  then change without breaking the other.
- Map differently named keys with a `CodingKeys` enum, or with a decoder's
  `keyDecodingStrategy` when the whole format uses a consistent convention
  (such as `snake_case`).
- **Validate after decoding.** Decoding proves the shape is right, not that
  the values make sense. Check invariants in the initialiser or a separate
  validation step.
- Decode dates, URLs and other structured values into their real types, not
  into `String`. Configure the decoder's `dateDecodingStrategy` explicitly.

## Interop with Objective-C

- Expose only what Objective-C callers need, with `@objc`. Give each exposed
  type a prefixed Objective-C name (`@objc(ABCImageCache)`), following the
  [Objective-C naming rules](../ObjC/coding-style.md#naming).
- Objective-C headers must carry **nullability annotations**. A `nullable`
  pointer imports as an optional, and an unannotated one imports as an
  implicitly unwrapped optional, which this guide forbids. See
  [Objective-C nullability](../ObjC/idioms.md#nullability).
- Use `NS_SWIFT_NAME` in Objective-C headers to give imported APIs names that
  follow the [Swift naming rules](coding-style.md#naming).
- Bridge `NSError **` methods by letting Swift import them as `throws`. Don't
  wrap them in your own error-pointer handling.

## API design

- **Use default arguments instead of overloads** that differ only in which
  parameters they take. One function is easier to document and to find.
- Mark functions whose result may reasonably be ignored with
  `@discardableResult`. The compiler warns about every other unused result.
- Take the most general type that works: a `some Sequence<Element>` instead
  of an `[Element]`, or a protocol instead of a concrete class.
- Inject dependencies through initialisers instead of reaching for
  singletons. Tests can then pass fakes, and dependencies are visible in the
  type's signature.
- Avoid `Bool` parameters. `load(url, true)` doesn't say what `true` means at
  the call site. Use an enum, or an argument label that makes it read
  clearly.

## Performance

- **Measure before you optimise**, with Instruments or another profiler.
- Choose the right data structure first. A `Set` or `Dictionary` lookup
  beats a linear search through an array.
- Use `lazy` sequences when you chain several transformations and only need
  part of the result.
- Mark classes `final` and members `private` where you can. Both let the
  compiler dispatch statically and optimise across calls.
- **Stream large input** with `FileHandle`'s `read(upToCount:)` in a loop,
  rather than reading the whole file into memory.
- **Memory-map a large file that's read at random positions or many times**
  with `Data(contentsOf: url, options: .mappedIfSafe)`, which maps the file
  only where that's safe and reads it otherwise. Don't map a file you read once
  from start to end, where buffered reads are as fast and simpler, or one that
  another process may shrink while it's mapped, which can crash the program.

## Sources

- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
- [Google Swift Style Guide](https://google.github.io/swift/)
- [The Swift Programming Language](https://docs.swift.org/swift-book/)
- [Swift concurrency migration guide](https://www.swift.org/migration/documentation/migrationguide/)
