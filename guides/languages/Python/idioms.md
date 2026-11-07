# Python Idioms and Principles

How to write Python well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Python code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Readability counts.** Code is read far more often than it's written.
  Prefer the plain, obvious version over the clever one.
- **Explicit is better than implicit.** Pass values in rather than reaching
  for globals, and name things for what they are.
- **Errors should never pass silently.** Raise them, handle them where
  something can be done, and never swallow them without a reason.
- **Keep scope small.** Give names, state and imports the narrowest
  visibility that works.
- **Types are documentation the computer checks.** Keep the type hints
  precise, and let mypy catch mistakes before they run.

## Modules and packages

- A module does one job. Every name it exports is part of its contract, so
  prefix internal names with `_`.
- **Importing a module must have no side effects.** Don't open connections,
  read files or start threads at import time. Do that work in a function
  that the caller runs.
- Give scripts an entry point, so the module can also be imported and
  tested:

  ```python
  def main() -> int:
      ...
      return 0


  if __name__ == "__main__":
      raise SystemExit(main())
  ```

- **Avoid global mutable state.** Pass objects to the functions that need
  them. A module-level constant is fine; a module-level variable that
  changes at run time is not.
- Group related settings into one object, such as a dataclass, instead of
  threading many parameters through every call.

## Data and mutability

- **Use dataclasses for records.** They generate `__init__`, `__repr__` and
  `__eq__`, and declare the fields in one place. Make them immutable by
  default:

  ```python
  @dataclass(frozen=True, slots=True)
  class Point:
      x: float
      y: float
  ```

- Use `enum.Enum` for a fixed set of values, instead of bare strings or
  integers. A typo then fails at once instead of matching nothing.
- Describe the shape of a dictionary that comes from outside (JSON, an API)
  with a `TypedDict`. Turn it into a dataclass once it's validated.
- **Never use a mutable default argument.** The default is created once and
  shared by every call. Default to `None` and create the value inside:

  ```python
  def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
      if tags is None:
          tags = []
      tags.append(tag)
      return tags
  ```

- Prefer tuples and `frozenset` for collections that shouldn't change. Code
  that can't mutate a value can't corrupt it.
- Don't modify a function's arguments unless that's its stated job. Return
  a new value instead.

## Errors and exceptions

- **Raise exceptions for errors.** Don't return `None`, `-1` or `False` to
  signal failure. A caller can forget to check a return value, but an
  exception can't be ignored by accident.
- Return `None` only when "no result" is a normal outcome, such as a lookup
  that may find nothing, and say so in the return type.
- **Catch the most specific exception you can handle.** Never write a bare
  `except:`. It also catches `KeyboardInterrupt` and `SystemExit`.
- Keep `try` blocks small, so you only catch exceptions from the line you
  expect to fail.
- **Chain exceptions** when you translate one into another, so the original
  cause stays in the traceback:

  ```python
  try:
      raw = path.read_text(encoding="utf-8")
  except FileNotFoundError as err:
      raise ConfigError(f"missing config file: {path}") from err
  ```

- Give each package a base exception, and derive its specific errors from
  it. Callers can then catch everything from your package in one place:

  ```python
  class BillingError(Exception):
      """Base class for billing errors."""


  class PaymentDeclinedError(BillingError):
      """The payment provider declined the charge."""
  ```

- **Handle each error at the level that can do something about it**: retry,
  fall back, or report to the user. Lower levels let it propagate.
- **Report each error once.** Code either logs an exception or raises it,
  not both, so one failure doesn't produce a cascade of messages.
- Don't use `assert` to validate input or enforce behaviour. Running Python
  with `-O` removes every `assert`. Raise an explicit exception instead.

## Resources

- **Use `with` for everything that must be released**: files, locks,
  sockets, database connections and transactions. The `with` block releases
  the resource even when an exception is raised.
- Always pass an encoding when opening text files: `open(path,
  encoding="utf-8")`. The default depends on the platform.
- Use `pathlib.Path` for file paths. It handles joining and separators
  correctly on every platform.
- Write your own context managers with `contextlib.contextmanager`, and use
  `contextlib.ExitStack` when the number of resources is only known at run
  time.

## Iteration

- **Loop over items, not indexes.** Use `for item in items`, `enumerate()`
  when you need the index too, and `dict.items()` for keys and values.
- Use `zip(a, b, strict=True)` to walk sequences in step. `strict=True`
  raises an error if their lengths differ, instead of silently dropping the
  extra items.
- Use a comprehension to build a list, set or dictionary from another
  iterable. Use a plain loop when the body has side effects or needs more
  than one condition.
- Use a **generator** for large or endless sequences, so items are produced
  one at a time instead of all held in memory.
- Use `any()`, `all()`, `sum()`, `min()` and `max()` instead of writing the
  loop yourself.
- Never add or remove items in a collection while looping over it. Loop over
  a copy, or build a new collection.
- Build strings from many parts with `"".join(parts)`, not repeated `+=`.

## Typing

- **Accept abstract types, return concrete ones.** Parameters take
  `Iterable`, `Sequence` or `Mapping` so callers can pass any suitable
  collection. Return values are `list`, `dict` and so on, so callers know
  exactly what they get.
- Use a `Protocol` for duck typing. It states the methods an argument needs
  without forcing it to inherit from anything.
- Mark constants with `Final`, so mypy reports any reassignment.
- Use `typing.cast()` only when you know something mypy can't work out, and
  add a comment saying why.
- Validate data at the boundary where it enters the program. Inside, rely on
  the types.

## Concurrency

- Use **threads for I/O-bound work** and **processes for CPU-bound work**.
  The global interpreter lock lets only one thread run Python code at a
  time, so threads don't speed up computation.
- Use `concurrent.futures` instead of managing threads or processes by hand.
- In `asyncio` code, **never block the event loop.** Call `await` on every
  I/O operation, and run blocking calls with `asyncio.to_thread()`.
- **Document what protects shared data**, and guard it with a lock held in a
  `with` block. Prefer handing data between threads with a `queue.Queue`
  over sharing it.

## Security

- **Never build SQL by string formatting.** Pass values as query parameters,
  so the driver escapes them:

  ```python
  cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
  ```

- **Run commands with an argument list, not a shell.** Use
  `subprocess.run(["git", "log", path], check=True)`. Never pass
  `shell=True` with values you don't control.
- **Never unpickle data you don't trust.** `pickle` and `marshal` can run
  arbitrary code while loading. Use JSON for data from outside the program,
  and `yaml.safe_load()`, never `yaml.load()`, for YAML.
- Never call `eval()` or `exec()` on input. Use `ast.literal_eval()` to read
  Python literals safely.
- Use the `secrets` module for tokens and passwords, never `random`.
  Compare secrets with `hmac.compare_digest()`, which takes the same time
  however much of the value matches.
- Resolve file paths built from input, and check they stay inside the
  intended directory before you open them.
- Create temporary files with the `tempfile` module, never with a
  predictable name.

## Testable design

- **Pass dependencies in.** A function that takes a client, a clock or a
  random generator as a parameter can be tested with a fake. One that
  creates them itself can't.
- Keep the core logic in **pure functions** that take values and return
  values. Push I/O to the edges of the program.
- Don't call `datetime.now()` or `time.time()` deep in your logic. Pass the
  current time in, or inject a clock.
- Write tests with `pytest`. Tests use plain `assert`.

## Performance

- **Measure before you optimise.** Use `cProfile` to find the slow part, and
  optimise only that.
- Choose the right data structure first. A `set` or `dict` lookup takes the
  same time however large it grows, while a `list` lookup gets slower as the
  list grows.
- Prefer built-in functions and the standard library. They run in C and are
  well tested.
- Pass arguments to logging calls instead of formatting them yourself:
  `logger.debug("loaded %d rows", count)`. The message is only built if it's
  actually logged.
- **Stream large input** by iterating over the file object, line by line,
  rather than calling `read()` or `readlines()`, which read the whole file into
  memory.
- **Memory-map a large file that's read at random positions or many times**
  with `mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)`. Searching it with
  `re` doesn't copy the file into memory first. For arrays of numbers, use
  `numpy.memmap`. Don't map a file you read once from start to end, where
  buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.
- Copy files with `shutil.copyfile`, which uses the operating system's fast
  copy calls where it can.

## Sources

- [PEP 20: The Zen of Python](https://peps.python.org/pep-0020/)
- [PEP 8: Style Guide for Python Code](https://peps.python.org/pep-0008/)
  (programming recommendations)
- [Python documentation: `pickle` security warning](https://docs.python.org/3/library/pickle.html)
- [Python documentation: `subprocess` security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [mypy documentation](https://mypy.readthedocs.io/)
