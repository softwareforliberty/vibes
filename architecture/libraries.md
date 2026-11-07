# Library Architecture

How to structure a reusable library or SDK, in any language. Read the
[rules for all software](README.md) first: a core of logic with thin edges,
dependencies pointing inward, and one owner for each piece of state. This
guide builds on them.

A library has no `main`. It runs inside other people's programs, on their
threads, beside their other dependencies, and it can't know how it will be
used. Every public name is a promise it keeps across releases. Its natural
shape is a small public interface over hidden internals, with everything it
needs from the outside world passed in by the caller.

A library with a binary interface, such as a C shared library, also follows
the [System libraries](os-components.md#system-libraries) rules: opaque
types, exported symbols and a checked binary interface.

## Scale the structure to the task

- **A small library,** such as a parser or a set of pure functions: one
  public module over private ones.
- **A library that does I/O,** such as a client for a service, a database
  driver or an SDK: everything in this guide.

At every size, choose what's public on purpose. Anything public by accident
becomes part of the interface the day it's released.

## The layers

```text
caller ─▶ public interface ─▶ core ─▶ ports ◀─┬─ default adapters
                                              └─ the caller's own adapters
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Public interface | The types, functions and errors callers use | Core | Internal types in its signatures |
| Core | The library's logic, as plain functions and types | Ports | I/O, the process's environment, global state |
| Ports | Small interfaces the core needs, such as a transport, a clock or a store | Nothing outside the library | Any particular implementation |
| Adapters | Implementations of the ports, such as an HTTP transport | Ports, outside libraries | The public interface, the core's internals |

### Public interface

The public interface is a thin layer of the types and functions the library
promises to keep. It validates what it's given, and calls the core.

- **It exposes only the library's own types.** A dependency's type in a
  public signature ties every caller to that dependency's version, and makes
  replacing it a breaking change.
- **It has one entry point, or a few,** such as a client object or a
  top-level module, so the rest can stay hidden.
- **Types that may grow can't be built field by field.** Use a constructor,
  a builder or an options object, and mark types non-exhaustive where the
  language can, so a new field or variant isn't a breaking change.

### Core, ports and adapters

The core is the library's logic, with no I/O, so callers can use its pure
parts, such as parsing and encoding, with data from any source. Anything it
needs from outside, such as the network, files, the clock or randomness,
goes through a port. The library ships a default adapter for each port where
one makes sense, and the caller can pass in their own.

- **Accept streams and readers,** not only file paths, so callers can pass
  data from memory, the network or a file.
- **Never do I/O as a side effect** of importing the library or building an
  object, such as connecting in a constructor. Connect when asked, so the
  caller controls when it happens and how it fails.

## The smallest public surface

- **Hidden by default.** Use the language's visibility rules, such as
  internal packages, `pub(crate)` or package-private classes, so internals
  can change without breaking anyone.
- **Add to the interface only for a real caller.** Adding a name later is
  cheap, and removing one needs a major version.
- **One way to do each thing.** Two public paths to one result double what
  must be documented, tested and kept compatible.
- **Don't leak details through behaviour,** such as the order of an
  unordered result or the text of an error. Callers depend on anything they
  can observe.

## Versioning and compatibility

Release with [semantic versioning](https://semver.org/): a major version for
an incompatible change, a minor one for new features, and a patch for
compatible fixes. Versions below 1.0.0 promise nothing, so reach 1.0.0 once
callers depend on the library.

A change is breaking when code that worked with the last release stops
working. There are three kinds:

- **Source:** callers' code no longer compiles, such as when a name is
  removed or renamed, or a new overload makes a call ambiguous.
- **Binary:** code compiled against the last release no longer links or
  runs without recompiling, such as when a field is added to a public C
  struct, or a parameter is added in Java or C#. The two kinds don't always
  agree: a change can keep one and break the other.
- **Behaviour:** the code builds and runs, but does something different,
  such as a changed default, a new error from a call that never failed, or a
  stricter check. Even a bug fix can break a caller who relied on the bug.

These are breaking too, and easy to miss: adding a method without a default
to an interface callers implement; adding a variant to an enum or error type
callers match on exhaustively; and raising the minimum language, runtime or
platform version. Follow the ecosystem's policy on the last, and put it in
the changelog either way.

## Deprecation

- **Deprecate in a minor release before removing in a major one,** with the
  language's marker, such as `@Deprecated`, `[Obsolete]`, `#[deprecated]` or
  a `DeprecationWarning`, so callers get a warning and time to move.
- **The warning says what to use instead,** and when it will go.
- **Keep a deprecated name while it's cheap to keep.** Every removal is work
  for every caller.

## Dependencies

Every dependency a library takes becomes a dependency of every program that
uses it, and must agree with every other library in that program.

- **Depend on as little as possible,** and never for something small
  enough to write.
- **Accept the widest version range that works,** and never pin an exact
  version. A pin forces a version on every caller, and can make two
  libraries impossible to use together.
- **Make heavy parts optional,** through the ecosystem's optional features
  or extras, or a separate package, so callers who don't use them don't pay
  for them.

## A good guest

A library shares a process it doesn't own.

- **No global state.** State lives in an object the caller creates, such as
  a client or a context, so two parts of a program can use the library with
  different settings, and tests don't leak into each other.
- **No logging setup.** Log through the ecosystem's logging interface, such
  as Python's `logging`, SLF4J or Rust's `log`, and leave handlers, levels
  and formats to the application. Python's documentation, for example, tells
  a library to add no handler except `NullHandler`.
- **Never exit, print or prompt.** Those decisions belong to the program.
  Report to the caller instead.
- **Never change process-wide settings,** such as signal handlers, the
  locale, the working directory or the environment.
- **Everything it creates can be closed:** threads, connections and files,
  through `close` or the language's disposal pattern.

## Errors

- **Use the language's idiom,** such as exceptions or `Result`, and never a
  sentinel such as `-1` or `null` where the language has better.
- **Error types are public and stable.** Give each failure a caller would
  handle differently its own type or code, so callers never parse messages,
  and treat changing one as a breaking change.
- **Wrap dependencies' errors** in the library's own types, keeping the
  original as the cause, so the dependency doesn't leak into the interface.
- **Misuse fails at once,** such as an invalid argument, while failures the
  caller can't prevent, such as a lost connection, are errors they handle.

## Configuration

Configuration is passed in, as a typed options object or constructor
arguments with safe defaults. A library never reads its own environment
variables or configuration files: the program decides where settings come
from, and passes the values in.

## Threads and concurrency

- **Document each type's thread safety:** safe to share between threads,
  safe from one thread at a time, or confined to the thread that made it.
- **Don't start threads or event loops behind the caller's back.** Take an
  executor, or in an async language, run on the caller's runtime.
- **Blocking calls take a timeout and can be cancelled,** through the
  language's mechanism, such as a context or a cancellation token.

## Extension points

Where callers need to change the library's behaviour, give them a small,
documented interface to implement, such as a transport, a retry policy or a
hook, rather than letting them subclass internal classes. An extension point
is public interface, with the same compatibility promise, so add one only
when a caller needs it.

## Documentation and examples

Documentation is part of the interface. Every public name says what it
does, what it takes and returns, the errors it raises and its thread safety.
Examples run as tests, such as doctests or an `examples/` directory built in
CI, so they never rot. A changelog lists every change a caller might notice,
breaking changes and deprecations first.

## Layout

```text
src/
├── <name>/          the public interface: the only module callers import
└── internal/        the core, ports and adapters, hidden from callers
examples/            small programs that use only the public interface
tests/
├── unit/            the core
└── api/             the public interface, as a caller uses it
CHANGELOG.md
```

## Enforce it

- **Check every change against the last release** in `scripts/check`, with
  a tool for the language, such as
  [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks)
  for Rust, [japicmp](https://github.com/siom79/japicmp) for Java, the
  experimental `gorelease` for Go,
  [API Extractor](https://api-extractor.com/) for TypeScript,
  [Griffe](https://mkdocstrings.github.io/griffe/) for Python, .NET's
  package validation, or `abidiff` for C. A break outside a major version
  fails the gate.
- **Typical rules for architecture tests:** public signatures use only the
  library's own types; the core doesn't do I/O, set up logging or read the
  environment; nothing calls `exit` or writes to standard output.

## Testing

| Part | Test with |
| --- | --- |
| Core | Unit tests, with fake ports |
| Public interface | Tests that import only the public interface, as a caller would |
| Adapters | Integration tests against the real thing, such as a server in a container |
| Compatibility | The last release's tests, run against the new version |

- **Test through the public interface.** Tests of internals break on every
  refactor and prove nothing a caller relies on.
- **Test every supported version** of the language, runtime and key
  dependencies, from the oldest the library supports to the newest.
