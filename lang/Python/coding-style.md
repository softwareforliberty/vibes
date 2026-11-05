# Python Coding Style

A general-purpose coding style for Python projects. It builds on
[PEP 8](https://peps.python.org/pep-0008/), the
[PEP 257](https://peps.python.org/pep-0257/) docstring conventions and
[PEP 484](https://peps.python.org/pep-0484/) type hints (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (errors,
resources, typing, security and other idioms), see [idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | MIT | Formatting, import sorting and linting |
| [mypy](https://mypy-lang.org/) | MIT | Static type checking |

### Configuration

Code must pass all three checks with **no errors or warnings**:

```sh
ruff format .
ruff check .
mypy .
```

Put the settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # import sorting
    "N",    # naming
    "D",    # docstrings
    "UP",   # modern syntax
    "B",    # likely bugs
    "SIM",  # simplifications
    "S",    # security
    "RUF",  # Ruff-specific checks
]
ignore = ["W191", "E111", "E114", "E117", "D206", "D300"]  # formatter conflicts

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "D"]  # pytest uses assert; tests need no docstrings

[tool.mypy]
strict = true
```

- The baseline language is **Python 3.10**. That version adds the `X | None`
  union syntax and `zip(strict=True)`, which this guide relies on.
- `ruff format` owns layout. Don't hand-format code it will rewrite, and
  don't argue with its output in review.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs.
- Wrap long lines inside parentheses, brackets or braces, not with a
  backslash. The brackets make the continuation explicit, and a stray space
  after a backslash breaks the code.
- When a call, collection or signature doesn't fit on one line, put one item
  per line and end with a trailing comma. The formatter then keeps it
  exploded, and adding an item changes only one line in a diff:

  ```python
  user = create_user(
      name=name,
      email=email,
      roles=["admin"],
  )
  ```

### Line length

- Code lines are at most **88 characters**. The formatter enforces it.
- Docstrings and comments wrap at **72 characters**, so they stay readable
  in narrow views and diffs.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Blank lines

- Two blank lines around top-level functions and classes.
- One blank line between methods inside a class.
- Use single blank lines inside functions, sparingly, to separate logical
  steps.

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- Every module starts with a docstring (see [Docstrings](#docstrings)).

### One thing per line

- One statement per line. Don't join statements with `;`.
- The body of an `if`, `for`, `while` or `with` always goes on its own line,
  even when it's short.

## Imports

- Put imports at the top of the module, after the module docstring.
- One module per `import` line: `import os` and `import sys` on separate
  lines. Importing several names from one module on one line is fine:
  `from pathlib import Path, PurePath`.
- Group imports in this order, with a blank line between groups:
  standard library, third-party packages, then this project's modules. Sort
  each group alphabetically. Ruff does this for you.
- Use **absolute imports**. They show where a name comes from without
  needing to know the current package.
- Never use wildcard imports (`from module import *`). They hide where names
  come from and can silently shadow existing ones.

## Strings

- Use **double quotes** for strings. The formatter normalises to them, so
  there's one style everywhere.
- Use **f-strings** for formatting: `f"{name} has {count} items"`. They put
  each value where it appears in the output.
- Use triple double quotes (`"""`) for docstrings and multi-line strings.

## Whitespace

- One space around assignment, comparison, arithmetic and boolean operators:
  `x = a + b`, `if a == b`.
- No spaces around `=` for keyword arguments and unannotated defaults:
  `connect(host, port=80)`. Put spaces around it when the parameter has an
  annotation: `def connect(host: str, port: int = 80)`.
- No spaces just inside brackets: `items[1]`, `f(x)`, `{"a": 1}`.
- No space before a comma, colon or semicolon. One space after a comma or a
  colon that isn't a slice.
- Annotations take one space after the colon and none before:
  `count: int`. The return arrow takes a space on each side: `-> int`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Modules and packages | Short `snake_case`; packages one word where possible | `user_store`, `billing` |
| Classes | `CapWords` | `UserStore`, `HTTPClient` |
| Exceptions | `CapWords` ending in `Error` | `UserNotFoundError` |
| Functions, methods, variables | `snake_case` | `load_config`, `retry_count` |
| Constants | `UPPER_SNAKE_CASE` at module level | `MAX_RETRIES` |
| Type variables | Short `CapWords` | `T`, `KeyT` |

- Prefix internal names with a single underscore: `_parse_header()`. The
  underscore marks it as private to the module or class.
- Don't use double leading underscores just to make a name private. Name
  mangling makes subclassing and debugging harder.
- Never use `l`, `O` or `I` as single-character names. They're easily
  confused with `1` and `0`.
- Don't put the type in the name (`user_list`, `str_name`). Type hints carry
  that.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Type hints

- Annotate every function's parameters and return type. mypy runs in strict
  mode, so untyped code fails the check.
- Use the built-in generics and the `|` union syntax: `list[str]`,
  `dict[str, int]`, `str | None`. Don't use `typing.List` or
  `typing.Optional`.
- Import abstract types from `collections.abc`: `Iterable`, `Mapping`,
  `Sequence`, `Callable`.
- Avoid `Any`. It switches off checking for everything it touches. Use a
  precise type, a `Protocol` or `object` instead.
- Annotate a variable only when mypy can't infer its type, such as an empty
  collection: `seen: set[str] = set()`.

## Functions

- Make optional and flag parameters **keyword-only** with a bare `*`:

  ```python
  def fetch_user(user_id: int, *, timeout: float = 5.0) -> User:
  ```

  Callers then have to name them, so `fetch_user(42, timeout=1.0)` reads
  clearly where `fetch_user(42, 1.0)` wouldn't.
- Either every `return` statement returns a value or none do. If any
  returns a value, write `return None` explicitly where nothing is returned.
- Don't assign a `lambda` to a name. Use `def`, which gives the function a
  real name in tracebacks.

## Expressions

- Compare to `None` with `is` and `is not`: `if value is None`.
- Test empty sequences by truthiness: `if not items`, `if items`.
- Never compare a `bool` to `True` or `False` with `==`. Write `if done`.
- Use `isinstance(x, Foo)` to check a type, not `type(x) == Foo`. It works
  with subclasses.
- Use `str.startswith()` and `str.endswith()` instead of slicing:
  `if name.startswith("test_")`.
- Write `if x is not None`, not `if not x is None`.

## Comments

- Comments start with `# ` (hash and one space). Put inline comments at
  least two spaces after the code.
- Comments explain **why**, not **what**. The code already says what it
  does.
- Don't leave commented-out code. Version control keeps the history.
- Keep comments up to date. A wrong comment is worse than none.

## Docstrings

- Every public module, class, function and method has a docstring. It's how
  `help()`, editors and generated docs explain the API.
- Use triple double quotes. The first line is a one-line summary in the
  imperative mood, ending with a period: `"""Fetch a user by ID."""`.
- For anything longer, put a blank line after the summary, then the details.
  Use the `Args:`, `Returns:` and `Raises:` sections for functions:

  ```python
  def fetch_user(user_id: int, *, timeout: float = 5.0) -> User:
      """Fetch a user from the directory service.

      Args:
          user_id: ID of the user to fetch.
          timeout: Seconds to wait for a response.

      Returns:
          The matching user.

      Raises:
          UserNotFoundError: If no user has that ID.
      """
  ```

- Don't repeat types in the docstring. The type hints already state them.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from PEP 8 and borrows from:

- [PEP 8: Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257: Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484: Type Hints](https://peps.python.org/pep-0484/)
- [PEP 604: Union types as `X | Y`](https://peps.python.org/pep-0604/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [mypy documentation](https://mypy.readthedocs.io/)
