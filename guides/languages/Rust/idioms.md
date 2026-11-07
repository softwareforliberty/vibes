# Rust Idioms and Principles

How to write Rust well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Rust code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **Let the compiler prove it.** Encode rules in types and ownership, so
  mistakes fail to compile instead of failing at run time.
- **Make invalid states unrepresentable.** If two fields can't both be set,
  use an enum, not two `Option`s.
- **Errors are values.** Return `Result`, propagate with `?`, and panic only
  for bugs.
- **`unsafe` is a promise you must keep by hand.** Use as little as
  possible, wrap it in a safe API, and justify every block.
- **Keep scope small.** Make items private by default, and give state the
  narrowest visibility that works.

## Ownership and borrowing

- **Borrow what you only read, and take ownership of what you keep.** A
  function that inspects text takes `&str`; a constructor that stores it
  takes `String` (or `impl Into<String>`).
- **Accept the most general borrowed form**: `&str` instead of `&String`,
  `&[T]` instead of `&Vec<T>`, `&Path` instead of `&PathBuf`. Callers can
  pass more kinds of values, with no extra cost.
- **Clone deliberately.** A `.clone()` added to satisfy the borrow checker
  often hides a design that should pass a reference or move the value.
- Don't reach for `Rc<RefCell<T>>` or `Arc<Mutex<T>>` by default. Shared
  mutable state moves borrow checking to run time, where violations panic.
  First try giving the data one clear owner.

## Errors

- **Return `Result` for anything that can fail** for reasons outside the
  program's control: I/O, parsing, missing data.
- **Libraries define their own error types.** Use an enum with one variant
  per failure the caller might handle, implementing `std::error::Error` and
  `Display`. Callers can then match on the cause:

  ```rust
  #[derive(Debug)]
  pub enum ParseSizeError {
      Empty,
      InvalidNumber(std::num::ParseIntError),
      UnknownSuffix(char),
  }
  ```

  A derive crate such as `thiserror` can write the `Display` and `Error`
  impls for you.
- **Applications can use one general error type** that carries a message
  chain, such as `Box<dyn std::error::Error>` or `anyhow::Error`, and add
  context as errors travel up. Nothing above `main` needs to match on them.
- **Library code never panics for ordinary failures.** Panicking takes the
  decision away from the caller. `unwrap()` is acceptable in tests and
  examples; elsewhere, use `expect()` only for invariants the code
  guarantees, with a message that says why it can't fail:

  ```rust
  let header = lines.next().expect("split always yields one item");
  ```

- Add context when you propagate: say what was being done, not just that
  something failed.

## Types and APIs

- **Use the type system for meaning.** Wrap primitives in newtypes when
  mixing them up would be a bug: `struct UserId(u64)` can't be passed where
  an `OrderId` is expected.
- Model states with enums, and let `match` check that every state is
  handled. Avoid a wildcard `_` arm on your own enums, so adding a variant
  shows every place to update.
- **Implement the common standard traits** on public types whenever they
  make sense: `Debug` always, plus `Clone`, `PartialEq`, `Eq`, `Hash`,
  `Default` and `Display` where they fit. Callers can't add them later.
- Implement `From` for conversions that can't fail and `TryFrom` for ones
  that can, instead of inventing `to_x` functions.
- Mark public enums and structs that may grow `#[non_exhaustive]`, so adding
  a variant or field isn't a breaking change.
- Use a builder when a type has many optional settings, instead of a
  constructor with many parameters.

## Traits and generics

- Prefer generics (`impl Trait` or `<T: Trait>`) when the type is known at
  compile time. Use trait objects (`dyn Trait`) when you need to store
  different types together or keep compile times down.
- Keep trait bounds on the `impl` or function that needs them, not on the
  struct definition.
- **Don't implement `Deref` to fake inheritance.** It's for smart pointers.
  Forward the methods you need, or expose the inner value explicitly.

## Iterators

- **Prefer iterator adaptors to index loops** when the result is clearer.
  They can't index out of bounds, and the compiler optimises them just as
  well:

  ```rust
  let total: u64 = orders
      .iter()
      .filter(|o| o.is_paid())
      .map(|o| o.amount)
      .sum();
  ```

- Return `impl Iterator<Item = T>` instead of collecting into a `Vec`, when
  the caller may not need every item.
- Use a plain `for` loop when the body has side effects or early exits.
  Long adaptor chains with side effects hide control flow.

## Unsafe code

- **Avoid `unsafe` unless you need it** for FFI, a performance gain you've
  measured, or a primitive the standard library doesn't provide. Crates that
  have no reason to use it declare `#![forbid(unsafe_code)]`.
- **Wrap every `unsafe` operation in a safe abstraction** with the smallest
  possible surface, so callers can't break its rules.
- **Justify every `unsafe` block with a `// SAFETY:` comment**, and document
  every `unsafe fn` with a `# Safety` section (see
  [Comments](coding-style.md#comments)).
- Inside an `unsafe fn`, still wrap each unsafe operation in its own
  `unsafe` block, so each one gets its own justification.
- **Test unsafe code under Miri**, which detects undefined behaviour the
  compiler and tests can miss (see [tools](tools.md#security-analysis)).

## Concurrency

- Let `Send` and `Sync` do their job. If the compiler rejects sharing a value
  across threads, fix the design; don't force the trait with `unsafe impl`.
- **Prefer passing ownership** between threads with channels over sharing
  state. When state must be shared, keep the lock's scope short.
- Use scoped threads (`std::thread::scope`) when threads borrow local data,
  so no `Arc` is needed.
- In async code, **never block the executor** with blocking I/O or long
  computation, and **never hold a lock across `.await`**.

## Dependencies

- **Commit `Cargo.lock`** for every crate, so builds and audits see exactly
  the versions you tested.
- Add dependencies sparingly, and enable only the features you use. Every
  crate is code you ship and must keep patched.
- A crate that exposes another crate's types in its API must treat that
  crate's major version as part of its own.

## Testing

- Put unit tests in a `#[cfg(test)] mod tests` block at the end of the
  module, so they can test private items.
- Put tests of the public API in the `tests/` directory. They compile as a
  separate crate, so they see exactly what users see.
- Doc examples are tests too. Keep them short and correct.
- Test error paths, not just success. Assert on the error variant with
  `matches!`.

## Performance

- **Measure before you optimise.** Benchmark and profile in release builds;
  debug builds are much slower and mislead.
- Avoid needless allocation in hot paths: borrow instead of cloning, reuse
  buffers, and preallocate with `with_capacity`.
- **Stream large input** through a `BufReader`, and reuse one `String` with
  `read_line` in hot loops, rather than reading the whole file into memory.
- **Memory-map a large file that's read at random positions or many times**
  with the `memmap2` crate. Mapping is `unsafe`, because another process can
  change or shrink the file under you, so state why that can't happen in a
  `// SAFETY:` comment. Don't map a file you read once from start to end, where
  buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.
- `std::io::copy` between files and sockets already uses the kernel's copy
  calls on Linux, so prefer it to a copy loop of your own.

## Sources

- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/) (unsafe code)
- [Rust standard library: `std::error::Error`](https://doc.rust-lang.org/std/error/trait.Error.html)
- [The Cargo book: Cargo.toml vs Cargo.lock](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html)
- [Clippy lint list](https://rust-lang.github.io/rust-clippy/master/)
