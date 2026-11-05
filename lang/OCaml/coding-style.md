# OCaml Coding Style

A general-purpose coding style for OCaml projects. It builds on the
[OCaml.org guidelines](https://ocaml.org/docs/guidelines) and the layout
that [ocamlformat](https://github.com/ocaml-ppx/ocamlformat) produces with
its default profile (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(modules, variants, errors, mutability and other idioms), see
[idioms.md](idioms.md).

The tools that check OCaml code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **OCaml 5.1** built with **dune 3**. OCaml 5.1 makes
`List.map` and similar functions tail-recursive and adds the
`In_channel`/`Out_channel` modules this guide relies on, and OCaml 5 brings
domains and effect handlers.

## Layout

The formatter owns layout. Don't fight it with manual alignment; run it and
commit what it produces.

### Indentation

- Indent with **2 spaces**, the ocamlformat default. Never use tabs.
- Put each `match` case on its own line, starting with `|`, including the
  first one:

  ```ocaml
  let describe = function
    | Circle r -> Printf.sprintf "circle of radius %g" r
    | Rect (w, h) -> Printf.sprintf "%g by %g rectangle" w h
  ```

### Line length

- Lines are at most **80 characters**. ocamlformat breaks long expressions
  to fit.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- File names are lowercase `snake_case`: `http_client.ml` defines module
  `Http_client`.

### One thing per line

- One top-level definition per `let`. Separate top-level definitions with
  one blank line.
- Don't join independent statements with `;` on one line.

## Naming

- Values, functions, types and record fields are `snake_case`:
  `parse_config`, `max_retries`, `user_id`.
- Modules and constructors start with a capital, then use `snake_case`:
  `Http_client`, `Invalid_port`. This matches the standard library
  (`Not_found`, `Out_channel`).
- Module types are capitalised too; a functor's argument signature is
  usually `S`.
- **The main type of a module is called `t`**: `User.t`, `Queue.t`. Callers
  read the module name as part of the type.
- Type variables are short: `'a`, `'b`, `'key`.
- A function that raises instead of returning an option or result ends in
  `_exn`: `find_exn`. A function that returns an option where a raising
  version is the norm ends in `_opt`: `find_opt`. The name warns the caller.
- Name predicates as questions: `is_empty`, `has_expired`.

## Modules and interfaces

- **Every module has an `.mli` file.** The interface is the module's
  contract: it hides helpers, keeps types abstract, and lets the compiler
  warn about unused definitions.
- Document the API in the `.mli`, not the `.ml`.
- Order an `.mli` as: the main type, constructors, accessors, operations,
  then conversions (`to_string`, `pp`).

### Opening modules

- Don't `open` a module at the top of a file, except a project-wide
  standard library replacement. A top-level `open` hides where names come
  from and can shadow existing ones.
- Use a qualified name (`List.map`), or a local open for a short
  expression that uses a module heavily:

  ```ocaml
  let offset = Int64.(add base (mul step (of_int n)))
  ```

## Declarations

### Type annotations

- Every exported value has its type in the `.mli`. Annotate a definition in
  the `.ml` only where it makes a type error clearer.

### Records and variants

- Put each field and each constructor of a multi-line type on its own line:

  ```ocaml
  type t = {
    name : string;
    email : string;
    roles : role list;
  }
  ```

- Construct and pattern-match records with field punning when the variable
  name matches the field: `{ name; email; roles }`.

### Functions

- Use **labelled arguments** (`~len`, `~timeout`) when a function takes two
  or more arguments of the same type, so callers can't swap them.
- Put optional arguments (`?timeout`) before positional ones, and follow them
  with at least one positional argument, so the function can be applied
  fully.
- Use `|>` to chain transformations, reading top to bottom:

  ```ocaml
  let active_emails users =
    users
    |> List.filter (fun u -> u.active)
    |> List.map (fun u -> u.email)
  ```

- Use `function` for a function that only matches on its last argument.

## Comments

- Comment with `(* ... *)`. Document with `(** ... *)`, which odoc turns
  into API docs.
- Document every value in an `.mli`. Say what it does, what it returns,
  and what it raises:

  ```ocaml
  (** [pop q] removes the oldest item from [q].

      Returns [None] when [q] is empty. *)
  val pop : 'a t -> ('a * 'a t) option
  ```

- Comments explain **why**, not **what**. The types already say what.

## Warnings

Build with dune's default development profile, which turns the standard
warnings into errors, plus the extra warnings in [tools.md](tools.md). Don't
silence a warning with an attribute unless a comment beside it says why.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the OCaml.org guidelines and borrows from:

- [OCaml.org guidelines](https://ocaml.org/docs/guidelines)
- [ocamlformat](https://github.com/ocaml-ppx/ocamlformat)
- [OCaml manual](https://ocaml.org/manual/)
- [odoc documentation](https://ocaml.github.io/odoc/)
- [dune documentation](https://dune.readthedocs.io/)
