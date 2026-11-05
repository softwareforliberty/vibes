# Zig Coding Style

A general-purpose coding style for Zig projects. It builds on the style guide
in the [Zig language reference](https://ziglang.org/documentation/0.16.0/#Style-Guide)
and the layout that `zig fmt` produces (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(allocators, errors, safety, comptime, C interop and other idioms), see
[idioms.md](idioms.md).

The tools that check Zig code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **Zig 0.16.0**. Zig hasn't reached 1.0, and each release
changes the language and standard library, so pin the exact version rather
than a minimum range. Record it in `build.zig.zon`, so an older compiler
refuses the build with a clear message:

```zig
.minimum_zig_version = "0.16.0",
```

Upgrade Zig deliberately, in its own change, and fix everything the new
release breaks at once.

## Layout

### Formatting

- **`zig fmt` owns layout**: 4-space indentation, no tabs, and opening braces
  on the same line. Don't hand-format code it will rewrite, and don't argue
  with its output in review.
- **A trailing comma tells `zig fmt` to put one item per line.** Use it when
  a list has more than two items or doesn't fit on one line. Adding an item
  then changes only one line in a diff:

  ```zig
  const server = try Server.init(gpa, .{
      .port = 8080,
      .max_connections = 64,
      .timeout_ms = 5_000,
  });
  ```

### Line length

- Aim for **100 columns**. `zig fmt` doesn't wrap lines, so break long ones
  yourself with trailing commas, or by naming intermediate values.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline. `zig fmt`
  removes trailing whitespace.
- A file is a struct. **A file with top-level fields is a type, so its name is
  `TitleCase`** (`Server.zig`). Every other file is a namespace, named in
  `snake_case` (`http_parser.zig`). Directory names are `snake_case`.
- Order a file's contents: top-level doc comment (`//!`), imports, then
  public declarations, then private ones, then tests.

## Imports

- Import the standard library once, as `std`, at the top of the file. Alias
  the parts you use often:

  ```zig
  const std = @import("std");
  const mem = std.mem;
  const Allocator = std.mem.Allocator;

  const Order = @import("Order.zig");
  ```

- Name an import after what it is: a type import is `TitleCase`, a namespace
  import is `snake_case`, following the [naming rules](#naming).

## Naming

The rule is decided by what a name refers to:

| Kind | Convention | Example |
| --- | --- | --- |
| Types, and functions that return a type | `TitleCase` | `Server`, `ArrayList` |
| Other functions | `camelCase` | `parseHeader`, `readU32Be` |
| Variables, constants, fields, parameters | `snake_case` | `max_retries`, `buf_len` |
| Namespaces (structs with no fields that are never instantiated) | `snake_case` | `http_parser` |
| Enum fields | `snake_case` | `.little`, `.big` |
| Error names | `TitleCase` | `error.OutOfMemory` |

- **Acronyms and initialisms are ordinary words**, even two-letter ones:
  `XmlParser`, `HttpClient`, `readU32Be`. Not `XMLParser`.
- **Don't repeat the namespace.** Callers write `json.Parser`, not
  `json.JsonParser`.
- Avoid empty words in type names: `Value`, `Data`, `Context`, `Manager`,
  `utils`. Name what the thing is.
- Name allocator parameters for their lifetime: `gpa` for a general-purpose
  allocator whose memory the caller frees, `arena` for one freed all at once
  (see [allocators](idioms.md#allocators)).

## Declarations

- **Use `const` unless the value changes.** The compiler rejects a `var`
  that is never mutated.
- Give integer literals underscores when they're long: `1_000_000`.
- Prefer decl literals and result-location syntax to repeating the type:
  `const config: Config = .{ .port = 8080 };`.
- Use `undefined` only for memory you'll fully write before reading. Reading
  `undefined` is illegal behaviour.

## Control flow

- Handle errors and edge cases first, and return early, so the main path
  stays at the left margin.
- **Switch on your own enums and tagged unions without an `else` prong.** The
  compiler then reports every switch that needs updating when a value is
  added.
- Use labelled blocks (`blk: { ... break :blk value; }`) to compute a value
  with several steps, instead of a mutable variable assigned in branches.

## Comments

- Every public declaration has a `///` **doc comment**. Every file that's
  part of an API starts with a `//!` comment describing what it's for.
- Leave out what the name already says. Document behaviour, ownership of
  returned memory, and the errors a function can return.
- Use the word **assert** for an invariant whose violation is caught as
  safety-checked illegal behaviour, and **assume** for one that isn't
  checked. Readers then know which mistakes the safe build modes will
  catch.

  ```zig
  /// Returns the bytes up to the first newline. The caller owns the returned
  /// slice and frees it with `gpa`.
  /// Asserts that `input` is not empty.
  pub fn firstLine(gpa: Allocator, input: []const u8) ![]u8 {
  ```

- Use `//` comments for implementation notes. They explain **why**, not
  what. Zig has no block comments.

## Tests

- Name each test with a sentence describing the behaviour:
  `test "parseSize rejects an unknown suffix" { ... }`.
- Put tests at the end of the file they test, so they can reach private
  declarations.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting checks, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Zig language reference's style guide and borrows
from:

- [Zig language reference: Style Guide](https://ziglang.org/documentation/0.16.0/#Style-Guide)
- [Zig language reference: Comments](https://ziglang.org/documentation/0.16.0/#Comments)
- [Zig language reference: Illegal Behavior](https://ziglang.org/documentation/0.16.0/#Illegal-Behavior)
- [Zig build system documentation](https://ziglang.org/learn/build-system/)
- [Zig 0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html)
