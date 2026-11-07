# Erlang Coding Style

A general-purpose coding style for Erlang projects. It builds on the
[Inaka Erlang Coding Standards & Guidelines](https://github.com/inaka/erlang_guidelines)
and the layout that [erlfmt](https://github.com/WhatsApp/erlfmt) produces
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(pattern matching, errors, processes, OTP and other idioms), see
[idioms.md](idioms.md).

The tools that check Erlang code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **Erlang/OTP 26** or later, built with **rebar3**. OTP 26
adds map comprehensions, and every tool in [tools.md](tools.md) except the
dependency audit runs on it.

## Layout

The formatter owns layout. Don't fight it with manual alignment; run it and
commit what it produces.

### Indentation

- Indent with **4 spaces**. Never use tabs.
- Indent the body of a function clause, `case`, `receive`, `try` and `fun`
  by one level.

### Line length

- Lines are at most **100 characters**. erlfmt breaks long expressions to
  fit.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- One module per file, named after the module: `queue_server.erl` holds
  `-module(queue_server).`

## Naming

- Modules, functions, atoms and record names are `snake_case`:
  `queue_server`, `parse_config`, `not_found`.
- Variables are `PascalCase`: `UserId`, `Config`. Treat acronyms as words:
  `HttpClient`, not `HTTPClient`.
- Macros are `UPPER_SNAKE_CASE`: `?DEFAULT_TIMEOUT`.
- Prefix modules with the application's name when they could collide with
  another application's: `myapp_config`, not `config`. Erlang has a single,
  flat module namespace.
- Prefix an unused variable with `_` and give it a name that says what it
  is: `_Reason`, not just `_`.
- Name predicates as questions: `is_empty/1`, `has_expired/1`.

## Modules

Order the parts of a module the same way every time, so readers know where
to look:

1. `-module`
2. `-behaviour`
3. `-export`, API functions first, then behaviour callbacks, one attribute
   each
4. `-include`
5. `-define`
6. `-record`
7. `-type`
8. Functions, in the same order as the exports, then private functions

```erlang
-module(queue_server).
-behaviour(gen_server).

%% API
-export([start_link/0, push/1, pop/0]).

%% gen_server callbacks
-export([init/1, handle_call/3, handle_cast/2]).
```

- **Never use `-compile(export_all)`.** It exports every function, so
  nothing is private, and xref can't find unused ones.
- Keep records private to the module that owns them. Put a record in a
  `.hrl` file only when several modules of one application genuinely share
  it.

## Functions

- Prefer several function clauses to a `case` on an argument. Each clause
  handles one shape of input:

  ```erlang
  area({circle, R}) -> math:pi() * R * R;
  area({rect, W, H}) -> W * H.
  ```

- Keep `case` and `receive` expressions at most two levels deep. Move a
  deeper branch into its own function.
- Don't use `if` with a catch-all `true ->` branch. Use a `case`, or guards
  in function clauses.
- Keep guards short. A long guard belongs in a function the body calls.

## Types and specs

- Every exported function has a `-spec`. It documents the contract and lets
  Dialyzer check callers.
- Define a `-type` for every data shape that crosses a module boundary, and
  export it with `-export_type`.

## Strings

- Use binaries (`<<"text">>`) for text, and the `unicode` and `string`
  modules to work on them. A list of characters takes far more memory.
- Build output with iolists instead of concatenating binaries. The VM
  writes an iolist without copying it.

## Comments

- Use `%%%` for module-level comments, `%%` for comments on their own line
  inside a module, and `%` for a short note at the end of a line.
- Document every exported function with an EDoc comment before it:

  ```erlang
  %% @doc Removes the oldest item from the queue.
  %%
  %% Returns `empty' when the queue has no items.
  -spec pop() -> {ok, term()} | empty.
  ```

- Comments explain **why**, not **what**.

## Warnings

Compile with the warning flags in [tools.md](tools.md), and fix every
warning. Don't silence one unless a comment beside it says why.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Inaka guidelines and borrows from:

- [Inaka Erlang Coding Standards & Guidelines](https://github.com/inaka/erlang_guidelines)
- [erlfmt](https://github.com/WhatsApp/erlfmt)
- [Erlang reference manual: expressions](https://www.erlang.org/doc/system/expressions.html)
- [EDoc user's guide](https://www.erlang.org/doc/apps/edoc/chapter.html)
