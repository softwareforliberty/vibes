# Erlang Idioms and Principles

How to write Erlang well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Erlang code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Data is immutable.** Functions take data and return new data; nothing
  changes behind your back.
- **Match on the shape you expect.** Pattern matching states the
  assumptions and fails loudly when they don't hold.
- **Errors the caller should handle are values.** They come back as
  `{error, Reason}`.
- **Let it crash.** Don't write defensive code for situations you can't
  handle; let a supervisor restart the process in a known good state.
- **Clarity beats cleverness.** A plain function beats a macro or a parse
  transform.

## Pattern matching

- **Match in function heads** rather than branching inside the body. Each
  clause handles one case.
- Match the specific shape you need and let anything else fail with a
  `function_clause` error, instead of adding a catch-all clause that hides
  bad input.
- **Assert on success by matching**: `{ok, Pid} = supervisor:start_child(Sup,
  Spec)` crashes with a clear `badmatch` if the call fails, which is what you
  want when failure means a bug.

## Errors

- Return `{ok, Value}` or `{error, Reason}` from a function that can fail in
  a way the caller should handle. Make `Reason` an atom or a tagged tuple the
  caller can match on, not a string.
- Use `error/1` for programming errors and broken invariants, and `exit/1`
  to stop the current process. Avoid `throw/1` except as a local non-local
  return inside one module, caught in the same module.
- Don't wrap calls in `try ... catch _:_ -> ok end` to carry on as if nothing
  happened. Catch only at a boundary that can report the failure, and match
  the specific class and reason.

## Data

- **Use maps for data that crosses module boundaries**, and records only
  inside the module that owns them. A record is a compile-time tuple layout,
  so every module that uses it must be recompiled when it changes.
- Use binaries for text and binary data, and lists for sequences of terms.
- Never convert untrusted input to atoms with `list_to_atom/1` or
  `binary_to_atom/2`. Use `list_to_existing_atom/1` or match the value
  explicitly (see [Processes and OTP](#processes-and-otp) for why).
- Never call `binary_to_term/1` on untrusted data. Use
  `binary_to_term(Bin, [safe])`, which refuses to create new atoms.
- Read large files line by line with `file:read_line/1`, on a file opened with
  `[read, raw, binary, read_ahead]`. Send files to sockets with
  `file:sendfile/2`, which uses the kernel's copy call where it can.

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

## Dependencies

- **Pin dependencies through Hex and commit the lockfile** (`mix.lock` or
  `rebar.lock`), so every build uses the same versions.
- Add a dependency only when it saves real work. Every dependency is code
  you ship, update and audit.

## Testing

- Test functions with **EUnit** and whole applications with **Common
  Test**.
- Use property-based tests (PropEr) for functions with clear rules, such as
  "decoding an encoded value gives it back".
- Test a `gen_server` through its API functions, not by sending it raw
  messages.

## Sources

- [Erlang/OTP design principles](https://www.erlang.org/doc/system/design_principles.html)
- [Erlang efficiency guide](https://www.erlang.org/doc/system/efficiency_guide.html)
- [Inaka Erlang Coding Standards & Guidelines](https://github.com/inaka/erlang_guidelines)
- [Erlang reference manual: errors and error handling](https://www.erlang.org/doc/system/errors.html)
