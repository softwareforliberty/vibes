# Elixir Idioms and Principles

How to write Elixir well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Elixir code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Data is immutable.** Functions take data and return new data; nothing
  changes behind your back.
- **Match on the shape you expect.** Pattern matching states the
  assumptions and fails loudly when they don't hold.
- **Errors the caller should handle are values.** They come back as
  `{:error, reason}`.
- **Let it crash.** Don't write defensive code for situations you can't
  handle; let a supervisor restart the process in a known good state.
- **Clarity beats cleverness.** A plain function beats a macro, and a
  macro is a last resort.

## Pattern matching

- **Match in function heads** rather than branching inside the body. Each
  clause handles one case:

  ```elixir
  def area({:circle, r}), do: :math.pi() * r * r
  def area({:rect, w, h}), do: w * h
  ```

- Match the specific shape you need and let anything else fail with a
  `FunctionClauseError`, instead of adding a catch-all clause that hides
  bad input.
- Use `case` to branch on a value and `cond` for unrelated conditions.
  Avoid nested `if`; it usually wants to be a `case` or separate clauses.
- Pin (`^value`) an existing variable to match against it, rather than
  rebinding it by accident.

## Errors

- Return `{:ok, value}` or `{:error, reason}` from a function that can fail
  in a way the caller should handle. Make `reason` an atom or a struct the
  caller can match on, not a string.
- **Chain fallible steps with `with`**, so the happy path reads top to
  bottom and the first error falls through:

  ```elixir
  with {:ok, body} <- File.read(path),
       {:ok, data} <- Jason.decode(body),
       {:ok, config} <- Config.validate(data) do
    {:ok, config}
  end
  ```

- Provide a `!` version that raises only where callers commonly want to
  crash on failure, and build it on the tuple-returning version.
- Raise exceptions for programming errors and broken invariants, not for
  expected failures.
- Don't `rescue` exceptions to carry on as if nothing happened. Rescue only
  at a boundary that can report the failure, such as a request handler.

## Data

- **Use structs for records** with known fields. A struct gives compile-time
  field checks; a plain map with atom keys gives none.
- Use maps for dynamic keys and keyword lists for options passed to a
  function.
- Never convert untrusted strings to atoms with `String.to_atom/1`. Use
  `String.to_existing_atom/1` or match the string explicitly (see
  [Processes and OTP](#processes-and-otp) for why).
- Use `Enum` for finite collections and `Stream` for large or infinite
  ones, so a long pipeline doesn't build every intermediate list.
- Stream large files with `File.stream!/1`, and process them with `Stream`
  before the final `Enum` call. `File.read!/1` reads the whole file into
  memory.

## Processes and OTP

- **Let it crash.** Handle only the errors you expect and can act on. For
  anything else, let the process crash and its supervisor restart it in a
  known good state. Defensive code that keeps a broken process running is
  worse than a clean restart.
- **Run every long-lived process under a supervisor**, started from the
  application's supervision tree. A process started outside the tree can
  die unnoticed, or outlive the code that started it.
- **Use the OTP behaviours** (`gen_server`/`GenServer`, `gen_statem`,
  `supervisor`/`Supervisor`) instead of hand-written receive loops. They
  handle system messages, code upgrades and tracing for you.
- **Use a process for state, concurrency or fault isolation, not to
  organise code.** Every call to a process is handled one at a time, so a
  process wrapped around plain functions becomes a bottleneck.
- **Set a timeout on every synchronous call** and decide what happens when
  it expires. A call that waits forever stalls its caller with it.
- **Handle every message a process can receive.** A message that no
  `receive` clause matches stays in the mailbox and slows every later
  receive.
- **Never create atoms from external input.** Atoms are never
  garbage-collected and the atom table has a fixed size, so converting
  untrusted strings to atoms can crash the whole node.
- Keep the state in a `GenServer` small. Copying a large state into every
  message and reply wastes memory and time.

## Dependencies

- **Pin dependencies through Hex and commit the lockfile** (`mix.lock` or
  `rebar.lock`), so every build uses the same versions.
- Add a dependency only when it saves real work. Every dependency is code
  you ship, update and audit.

## Macros

- Write a macro only when a function can't do the job, such as generating
  code at compile time or building a DSL. Macros are harder to read, debug
  and type-check.
- Keep `use` hooks small: inject a few imports and attributes, not hidden
  behaviour.

## Testing

- Test with **ExUnit**, and run tests with `async: true` unless they share
  global state.
- Write examples in `@doc` as doctests, so documentation can't drift from
  the code.
- Test a `GenServer` through its public API, not by sending it raw
  messages.

## Sources

- [Elixir documentation: anti-patterns](https://hexdocs.pm/elixir/what-anti-patterns.html)
- [Elixir documentation: GenServer](https://hexdocs.pm/elixir/GenServer.html)
- [Erlang/OTP design principles](https://www.erlang.org/doc/system/design_principles.html)
- [Elixir Style Guide](https://github.com/christopheradams/elixir_style_guide)
