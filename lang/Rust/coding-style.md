# Rust Coding Style

A general-purpose coding style for Rust projects. It builds on the
[Rust Style Guide](https://doc.rust-lang.org/style-guide/) that `rustfmt`
implements, and the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(ownership, errors, `unsafe`, traits and other idioms), see
[idioms.md](idioms.md).

The tools that check Rust code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **Rust 1.85 with the 2024 edition**, the first release that
supports it. Set both in `Cargo.toml`, so Cargo refuses to build with an
older compiler instead of failing with confusing errors:

```toml
[package]
edition = "2024"
rust-version = "1.85"
```

## Layout

### Formatting

- **`rustfmt` owns layout**, using its default settings: 4-space indentation,
  no tabs, and a maximum width of **100 columns**. Don't hand-format code it
  will rewrite, and don't argue with its output in review.
- Keep the defaults. A project-specific `rustfmt.toml` makes code look
  different from every other Rust project for no gain.
- When a call, struct literal or signature doesn't fit on one line, `rustfmt`
  puts one item per line with a trailing comma. Adding an item then changes
  only one line in a diff.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline. `rustfmt`
  removes trailing whitespace.
- File and module names are `snake_case`.
- Put a module in `name.rs`, with its children in a `name/` directory. Don't
  use `name/mod.rs`: an editor full of tabs named `mod.rs` is hard to
  navigate.
- Order a module's contents: inner doc comment (`//!`), `use` declarations,
  constants and statics, types with their `impl` blocks, free functions, then
  the `#[cfg(test)] mod tests` block last.

## Imports

- Group `use` declarations in three blocks separated by blank lines: the
  standard library (`std`, `core`, `alloc`), external crates, then the
  current crate (`crate::`, `super::`). `rustfmt` sorts within each block.

  ```rust
  use std::collections::HashMap;
  use std::io;

  use serde::Deserialize;

  use crate::order::Order;
  ```

- Import types and traits by name. For functions, import the parent module
  and call `module::function()`, so the call site shows where it comes from.
- Don't use glob imports (`use foo::*`), except for a crate's documented
  prelude and `use super::*` in a test module.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Types, traits, enum variants | `UpperCamelCase` | `HttpClient`, `Parse`, `Ready` |
| Functions, methods, variables, modules | `snake_case` | `parse_header`, `retry_count` |
| Constants and statics | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| Type parameters | One capital letter, or short `UpperCamelCase` | `T`, `K`, `Item` |
| Lifetimes | Short and lowercase | `'a`, `'de` |

- **Acronyms are one word**: `Uuid`, `HttpClient`, `parse_json`. Not `UUID`
  or `HTTPClient`.
- **Conversions follow the standard prefixes**: `as_` for a cheap borrowed
  view, `to_` for an expensive conversion, `into_` for one that consumes the
  value.
- **Getters have no `get_` prefix**: a field `name` has the getter `name()`
  and the setter `set_name()`.
- Iterator methods are `iter()`, `iter_mut()` and `into_iter()`, matching
  the standard collections.
- Constructors are `new()`, or `with_` plus what differs:
  `with_capacity(n)`.

## Expressions

- **Use `?` to propagate errors.** Don't write a `match` that only returns
  the error.
- Prefer `if let` and `let ... else` to a `match` with one interesting arm:

  ```rust
  let Some(user) = users.get(&id) else {
      return Err(Error::UnknownUser(id));
  };
  ```

- **Convert numbers with `From` and `TryFrom`, not `as`.** `as` silently
  truncates or wraps; `u32::try_from(n)?` reports the overflow.
- Write long numeric literals with underscores: `1_000_000`.
- Prefer iterator chains to index loops when they read more clearly (see
  [idioms](idioms.md#iterators)).

## Attributes

- Put each attribute on its own line, above the item.
- Derive standard traits in this order, so derive lists look the same
  everywhere: `Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash,
  Default`, then other crates' derives.
- Add `#[must_use]` to functions whose return value is the whole point of
  calling them, such as a pure function or a builder method.

## Comments

- Every public item has a `///` **doc comment**. The first line is a short
  summary sentence; detail follows after a blank line.
- Every crate and public module starts with a `//!` doc comment describing
  what it's for.
- Document failure modes in standard sections:
  - `# Errors` lists when a function returns `Err`.
  - `# Panics` lists when it panics.
  - `# Safety` lists what the caller must uphold to call an `unsafe fn`.

  ```rust
  /// Parses a size such as `"2k"` into a number of bytes.
  ///
  /// # Errors
  ///
  /// Returns [`ParseSizeError`] if `input` isn't a number with an optional
  /// `k`, `m` or `g` suffix.
  pub fn parse_size(input: &str) -> Result<u64, ParseSizeError> {
  ```

- Give public APIs an `# Examples` section. Doc examples run as tests, so
  they stay correct.
- **Every `unsafe` block has a `// SAFETY:` comment** right above it,
  explaining why the code upholds the rules the compiler can't check.
- Use `//` comments for implementation notes. They explain **why**, not
  what.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Rust Style Guide and borrows from:

- [The Rust Style Guide](https://doc.rust-lang.org/style-guide/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
  (naming, documentation)
- [RFC 430: naming conventions](https://rust-lang.github.io/rfcs/0430-finalizing-naming-conventions.html)
- [The rustdoc book](https://doc.rust-lang.org/rustdoc/)
- [The Cargo book: the `rust-version` field](https://doc.rust-lang.org/cargo/reference/rust-version.html)
- [Clippy lint list](https://rust-lang.github.io/rust-clippy/master/)
