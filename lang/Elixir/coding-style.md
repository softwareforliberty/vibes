# Elixir Coding Style

A general-purpose coding style for Elixir projects. It builds on the
community [Elixir Style Guide](https://github.com/christopheradams/elixir_style_guide)
and the layout that `mix format` produces (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(pattern matching, errors, processes, OTP and other idioms), see
[idioms.md](idioms.md).

The tools that check Elixir code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **Elixir 1.17** on **Erlang/OTP 26** or later. Elixir 1.17
adds the first set-theoretic type checks, which turn some type mistakes
into compiler warnings.

## Layout

The formatter owns layout. Don't fight it with manual alignment; run it and
commit what it produces.

### Indentation

- Indent with **2 spaces**. Never use tabs.
- Indent the body of `do`/`end` blocks, `fn`, `case`, `cond` and `with` by
  one level.

### Line length

- Lines are at most **98 characters**, the `mix format` default.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Multi-line collections

- When a list, map, keyword list or argument list doesn't fit on one line,
  put one item per line. `mix format` keeps it that way:

  ```elixir
  user = %User{
    name: name,
    email: email,
    roles: [:admin]
  }
  ```

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- One module per file, with the file path matching the module name in
  `snake_case`: `lib/my_app/http_client.ex` holds `MyApp.HTTPClient`.
- Scripts and test files use `.exs`; compiled code uses `.ex`.

## Naming

- Functions, variables, atoms and module attributes are `snake_case`:
  `parse_config`, `max_retries`, `:not_found`, `@default_timeout`.
- Modules are `PascalCase`. Keep acronyms uppercase, as the standard
  library does: `MyApp.HTTPClient`, `JSON`.
- A function that returns a boolean ends in `?`: `empty?`, `expired?`.
  A boolean check that can be used in a guard starts with `is_` instead:
  `is_admin(user)`.
- A function that raises instead of returning an error tuple ends in `!`:
  `fetch!`. Provide it alongside the tuple-returning version, not instead
  of it.
- Prefix an unused variable with `_`, and give it a name that says what it
  is: `_reason`, not just `_`.

## Modules

Order the parts of a module the same way every time, so readers know where
to look:

1. `@moduledoc`
2. `@behaviour`
3. `use`
4. `import`
5. `require`
6. `alias`
7. Module attributes
8. `defstruct`
9. `@type` and `@typep`
10. Callbacks, then public functions, then private functions

- Alias modules you use more than once, one per line. Don't alias a module
  just to save a few characters in a single call.
- Import only the functions you use: `import Ecto.Query, only: [from: 2]`.
  A bare `import` hides where names come from.

## Functions

- Use parentheses on every function call that takes arguments, and on
  zero-arity calls too. Leave them off only in DSLs whose style omits them,
  such as `use`, `defstruct` and test macros.
- **Start a pipeline with a plain value**, not a function call, and use a
  pipe only for two or more steps:

  ```elixir
  emails =
    users
    |> Enum.filter(& &1.active)
    |> Enum.map(& &1.email)
  ```

- Group the clauses of a multi-clause function together, with no blank
  lines between them, and give the group one `@doc` and `@spec`.
- Use the capture operator (`&String.upcase/1`, `& &1.email`) for short
  anonymous functions, and `fn` for anything longer than one expression.
- Keep guards short. Move a complex condition into a `defguard`.

## Typespecs

- Every public function has a `@spec`. It documents the contract and lets
  Dialyzer check callers.
- Define a `@type t` for every struct, and use it in specs:

  ```elixir
  @type t :: %__MODULE__{name: String.t(), email: String.t()}
  ```

## Comments and documentation

- Comment with `#`, followed by one space.
- Every public module has a `@moduledoc`, and every public function a
  `@doc`. Mark an internal module with `@moduledoc false` so it's left out
  of the documentation on purpose, not by accident.
- Write examples in docs as doctests, so they're checked by the test
  suite:

  ```elixir
  @doc """
  Returns the oldest item and the rest of the queue.

      iex> Queue.pop(Queue.new([1, 2]))
      {:ok, 1, Queue.new([2])}
  """
  ```

- Comments explain **why**, not **what**.

## Warnings

Compile with `--warnings-as-errors` in CI (see [tools.md](tools.md)), and fix
every warning. Don't silence one unless a comment beside it says why.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the community Elixir Style Guide and borrows from:

- [Elixir Style Guide](https://github.com/christopheradams/elixir_style_guide)
- [`mix format` documentation](https://hexdocs.pm/mix/Mix.Tasks.Format.html)
- [Elixir naming conventions](https://hexdocs.pm/elixir/naming-conventions.html)
- [Elixir writing documentation guide](https://hexdocs.pm/elixir/writing-documentation.html)
- [Credo](https://hexdocs.pm/credo/)
