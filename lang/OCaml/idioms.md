# OCaml Idioms and Principles

How to write OCaml well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep OCaml code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Make illegal states unrepresentable.** Use variants and abstract types
  so that wrong programs fail to compile.
- **Immutable by default.** Mutation is a tool for a specific job, kept
  local and visible.
- **Errors the caller should handle are values.** They show up in the
  return type.
- **The interface is the design.** Write the `.mli` first; it decides what
  the rest of the program can see and depend on.
- **Clarity beats cleverness.** A plain function beats a functor, and a
  functor beats a first-class module trick.

## Modules and signatures

- **Keep types abstract** in the `.mli` (`type t`) unless callers need to
  build or match on them. An abstract type lets the module enforce its own
  rules and change its representation later.
- Provide a constructor function that checks the rules for a value with
  constraints:

  ```ocaml
  (* email.mli *)
  type t

  val of_string : string -> (t, string) result
  val to_string : t -> string
  ```

- Use a **functor** when several modules need the same code over different
  types, such as a map over a key type. Don't use one to pass ordinary
  configuration; pass a record or an argument instead.
- Keep modules small and single-purpose. A module that needs a long
  comment to explain what it holds is two modules.

## Types

- **Model alternatives as variants**, not as a record of optional fields.
  `type payment = Card of card | Invoice of invoice` can't be both or
  neither.
- Use polymorphic variants only when several types genuinely share
  constructors. Ordinary variants give clearer errors.
- Wrap primitive values with meaning in their own module with an abstract
  type (`User_id.t`), so two `int`s can't be mixed up.
- Use `Map` and `Set` (via `Map.Make`) for keyed and unique data. A list of
  pairs makes every lookup linear.

## Pattern matching

- **Match every constructor explicitly.** Don't use a catch-all `_` on a
  variant: when a constructor is added, the compiler's exhaustiveness
  warning then points at every match that must change.
- Don't match on a tuple just to get two values out; use `let (a, b) = ...`
  or a record.
- Use `when` guards sparingly. The compiler can't check guards for
  exhaustiveness.

## Errors

- **Return `option`** when there's one obvious way to fail and the caller
  doesn't need to know why: `List.find_opt`.
- **Return `result`** with a variant of errors when the caller needs to
  know why:

  ```ocaml
  type config_error =
    | Missing_field of string
    | Invalid_port of int

  val parse_config : Yojson.Safe.t -> (config, config_error) result
  ```

- Chain results with `Result.bind`, or the `let*` binding operator defined
  in one place, instead of nested `match`.
- Use exceptions for programming errors (`Invalid_argument`) and for
  failures of the outside world that the caller can't sensibly handle. A
  function that raises ends in `_exn`.
- Never write `try ... with _ ->`. It also catches `Out_of_memory`,
  `Stack_overflow` and `Sys.Break`. Catch the specific exception you can
  handle.

## Resources

- **Release resources with `Fun.protect ~finally`**, or a `with_` function
  built on it, so they're released even when an exception is raised:

  ```ocaml
  let read_lines path = In_channel.with_open_text path In_channel.input_lines
  ```

- Never leave a channel or file descriptor for the garbage collector to
  close. It may never run before the process runs out of descriptors.

## Mutability

- Make record fields immutable, and build changed copies with
  `{ r with field = value }`.
- Keep `ref` cells and mutable fields local to the function or module that
  owns them, and never expose them in an `.mli`.
- Prefer `Map` to `Hashtbl` unless profiling shows the hash table is
  needed. A `Map` is immutable, so it's safe to share.
- Don't use polymorphic equality (`=`, `compare`) on abstract types,
  functions or cyclic values. It compares the representation, which can be
  wrong or raise. Give each type an `equal` function and use it.

## Effects and concurrency

- **Use effect handlers sparingly.** They're a low-level control-flow
  feature. Use them through a library (such as an effects-based I/O
  library) rather than writing handlers in application code.
- Run parallel work on **domains** through a pool, such as the one in
  `Domainslib`, and keep the number of domains near the number of cores.
- Share mutable state between domains only through `Atomic` or `Mutex`.
  Unsynchronised access from two domains is a data race.

## Performance

- **Measure before you optimise.** Profile with `perf` or `landmarks`, and
  let the profile point at the cost.
- Build strings in a loop with `Buffer`, not repeated `^`, which copies the
  whole string every time.
- Keep recursion over large inputs tail-recursive. A non-tail-recursive
  function over a long list overflows the stack.

## Testing

- Test with **Alcotest** for example-based tests and **QCheck** for
  property tests. A property such as "decoding an encoded value gives it
  back" checks thousands of inputs.
- Use expect tests (`ppx_expect` or dune's cram tests) for output-heavy
  code, so a reviewer sees the expected output in the diff.

## Sources

- [OCaml.org guidelines](https://ocaml.org/docs/guidelines)
- [OCaml manual: effect handlers](https://ocaml.org/manual/effects.html)
- [OCaml manual: parallelism](https://ocaml.org/manual/parallelism.html)
- [Real World OCaml](https://dev.realworldocaml.org/)
