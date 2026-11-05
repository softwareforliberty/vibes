# Zig Idioms and Principles

How to write Zig well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Zig code correct, safe and maintainable. Every example follows the style
guide.

## Principles

- **No hidden control flow, no hidden allocation.** A function that
  allocates takes an allocator; a function that does I/O takes the I/O
  interface. A reader can see every cost at the call site.
- **Every resource has exactly one owner.** Pair each `init` with a `deinit`
  and each allocation with a `free`, and make clear who calls them.
- **Errors are values.** Return them, handle them where something can be
  done, and never discard them silently.
- **Let the safe build modes catch mistakes.** Bounds, overflow and null
  checks are on in `Debug` and `ReleaseSafe`. Don't write code that only works
  because they're off.
- **Keep scope small.** Make declarations private unless other files need
  them.

## Allocators

- **Functions that allocate take a `std.mem.Allocator` parameter.** Never
  reach for a global allocator inside a library. The caller decides where
  memory comes from, and tests can pass one that detects leaks.
- **Name the parameter for the memory's lifetime**: `gpa` when the caller
  frees each allocation, `arena` when everything is freed at once.
- **Free with the same allocator you allocated with**, and document who owns
  returned memory:

  ```zig
  /// Returns `dir` and `name` joined with a slash. The caller owns the
  /// returned memory and frees it with `gpa`.
  pub fn joinPath(gpa: Allocator, dir: []const u8, name: []const u8) ![]u8 {
      return std.fmt.allocPrint(gpa, "{s}/{s}", .{ dir, name });
  }
  ```

- Use an arena (`std.heap.ArenaAllocator`) for many short-lived allocations
  with one lifetime, such as handling one request. Freeing the arena frees
  them all.
- Use a fixed buffer (`std.heap.FixedBufferAllocator`) when the maximum size
  is known and small. It can't leak and needs no heap.
- Containers take the allocator in each call that may allocate, and in
  `deinit`. Pass the same one every time.

## Errors

- **Return an error union (`!T`) for anything that can fail**, and propagate
  with `try`.
- **Clean up with `errdefer`** when a function acquires several resources.
  It runs only if the function returns an error, so the success path keeps
  what it built:

  ```zig
  pub fn init(gpa: Allocator, capacity: usize) !Buffer {
      const bytes = try gpa.alloc(u8, capacity);
      errdefer gpa.free(bytes);

      try validateCapacity(capacity);
      return .{ .bytes = bytes, .len = 0 };
  }
  ```

- **Give public functions explicit error sets** when callers need to handle
  specific errors. An inferred set (`!T`) changes whenever the
  implementation does.
- Handle specific errors with `catch |err| switch (err) { ... }`, listing
  each error you handle.
- **Never write `catch unreachable` for an error that can happen.** Use it
  only when the code proves the error impossible, with a comment saying
  why. In unsafe build modes it's undefined behaviour if you're wrong.
- Don't discard errors with `catch {}`. If you really mean to ignore one,
  say why in a comment.

## Optionals and pointers

- Use `?T` for a value that may be absent, and unwrap it with `orelse` or
  `if (value) |v|`. Don't use sentinel values like `-1` for "none".
- **Prefer slices (`[]T`) to many-item pointers (`[*]T`).** A slice carries
  its length, so the safe build modes can check every index.
- Use sentinel-terminated slices (`[:0]const u8`) only where a terminator is
  needed, such as strings passed to C.

## Safety

- **Ship in `ReleaseSafe`** unless measurement shows a hot path needs
  `ReleaseFast`. Safety checks turn silent memory corruption into a clear
  crash.
- When a narrowing conversion can fail, check it: `std.math.cast(u8, n)`
  returns `null` instead of hitting illegal behaviour like `@intCast` would.
- Use wrapping (`+%`) or saturating (`+|`) operators only when that's the
  intended arithmetic, never to silence an overflow check.
- Turn safety off for a block (`@setRuntimeSafety(false)`) only in measured
  hot code, with a comment saying what guarantees the code stays in bounds.

## Data types

- Model states with **tagged unions** and switch on them exhaustively, so
  adding a state shows every place to update.
- Give struct fields default values only when the default is correct for
  every caller. A wrong default is worse than a required field.
- **`deinit` invalidates the value**: end it with `self.* = undefined`, so a
  use after `deinit` is caught in safe builds.

## Comptime

- **Use `comptime` parameters for generics**: a function taking
  `comptime T: type` and returning a `type` is how Zig writes generic
  containers.
- Use `anytype` sparingly. It accepts anything, so the error for a wrong
  argument appears deep inside the function. Prefer a concrete type or an
  explicit `comptime T: type`.
- Report misuse at compile time with `@compileError` and a clear message.
- Keep comptime logic simple. Code that runs at compile time is still code
  someone has to read.

## C interop

- **Expose functions to C with `export fn`**, named as C would name them,
  with the module prefix: `export fn buf_flush(b: *Buf) c_int`. Follow the
  [C idioms](../C/idioms.md#error-handling) at the boundary: return `0` for
  success or a negative errno code, never a Zig error.
- **Translate C headers instead of hand-writing `extern` declarations**, so
  the Zig side can't drift from the header.
- Keep C pointer types (`[*c]T`) at the boundary. Convert to slices and
  optional pointers as soon as values enter Zig code.
- Memory allocated by C is freed by C. Memory allocated by Zig is freed by
  Zig, with the same allocator.

## Build and dependencies

- Describe the build in `build.zig`, with the standard target and optimize
  options, so every project builds the same way:
  `zig build -Doptimize=ReleaseSafe`.
- Add dependencies with `zig fetch --save`. `build.zig.zon` pins each one by
  content hash, so a changed download fails the build.
- Add dependencies sparingly. Every package is code you ship and must keep
  updated, and there's no advisory database to warn you about vulnerable
  versions (see [tools](tools.md#dependency-vulnerabilities)).

## Testing

- **Use `std.testing.allocator` in tests.** It fails the test on any leak or
  double free.

  ```zig
  test "joinPath joins with a slash" {
      const gpa = std.testing.allocator;
      const path = try joinPath(gpa, "etc", "hosts");
      defer gpa.free(path);
      try std.testing.expectEqualStrings("etc/hosts", path);
  }
  ```

- **Zig only compiles what's referenced.** A function nothing calls isn't
  even type-checked, so it can hide errors. Reference every declaration from
  a test with `std.testing.refAllDecls(@This())`.
- Run the tests in both `Debug` and `ReleaseSafe`, since optimisation can
  expose different bugs.
- Test the error paths: `try std.testing.expectError(error.Empty, parse(""))`.

## Performance

- **Measure before you optimise.** Benchmark in a release mode; `Debug` is
  much slower and misleads.
- Prefer contiguous memory (slices, `std.ArrayList`) and struct-of-arrays
  layouts (`std.MultiArrayList`) in hot paths. They keep the cache warm.

## Sources

- [Zig language reference](https://ziglang.org/documentation/0.16.0/)
  (allocators, errors, illegal behaviour, comptime, C interop)
- [Zig build system documentation](https://ziglang.org/learn/build-system/)
- [Zig 0.16.0 release notes](https://ziglang.org/download/0.16.0/release-notes.html)
- [Zig standard library documentation](https://ziglang.org/documentation/0.16.0/std/)
