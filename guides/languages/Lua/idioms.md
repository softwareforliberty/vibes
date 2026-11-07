# Lua Idioms and Principles

How to write Lua well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Lua code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Simple beats clever.** Lua gives you a few powerful mechanisms
  (tables, closures, metatables). Use the plainest one that does the job.
- **Keep scope small.** Every name is `local`, and lives in the narrowest
  block that works.
- **Fail loudly and early.** Check inputs where they arrive, and report
  failures to a caller who can act on them.
- **One way to signal each kind of failure.** Programming mistakes raise
  errors; expected failures return `nil` plus a message. Mixing the two
  makes callers guess.
- **Know your host.** Lua is usually embedded. The host decides which
  libraries exist and which Lua version runs, so write to that, not to an
  assumed standard library.

## Scope and locals

- **Everything is `local`.** Globals are shared by every chunk in the
  program, so a typo or a name clash silently changes someone else's state.
  The linter rejects any global that isn't declared in its config.
- **Cache library functions in locals in hot code.** A local lookup is
  faster than a table lookup on every call:

  ```lua
  local insert = table.insert
  ```

  Do this only where profiling shows it matters; elsewhere, the full name
  reads better.
- **Use `<close>` for resources** in Lua 5.4. The value's `__close`
  metamethod runs when the variable goes out of scope, even on error:

  ```lua
  local file <close> = assert(io.open(path, 'r'))
  ```

## Modules

- **A module returns one table** and changes nothing else. Requiring it has
  no side effects beyond defining that table.
- **Don't do work at load time.** Opening files, connecting or reading
  configuration at `require` time makes the module hard to test. Expose an
  `init` or `new` function and let the caller run it.
- **Keep state in objects, not in the module.** `require` caches the module,
  so state stored on it is shared by every caller. Return a constructor
  instead when callers need separate state.

## Errors

- **Expected failures return `nil` plus a message.** This is the
  convention the standard library uses (`io.open` returns
  `nil, err, code`):

  ```lua
  local function load_config(path)
    local file, err = io.open(path, 'r')
    if not file then
      return nil, 'cannot open config: ' .. err
    end
    ...
  end
  ```

- **Programming mistakes raise errors** with `error()`. Pass a level of `2`
  when the mistake is the caller's, so the message points at the call site:

  ```lua
  if type(id) ~= 'number' then
    error('id must be a number', 2)
  end
  ```

- **Use `assert()` to turn a `nil, err` result into an error** when the
  caller can't continue anyway: `local file = assert(io.open(path))`.
- **Catch errors with `pcall` or `xpcall` only at boundaries** (a request
  handler, a plugin call, the main loop) where something can be done about
  them. Use `xpcall` with `debug.traceback` so the stack trace survives.
- **Raise tables, not strings, when callers need to tell errors apart.** A
  table with a `code` field can be inspected; a string can only be matched
  with patterns.

## Tables

- **Arrays start at 1.** `ipairs`, `#` and the `table` library all assume
  it. Don't start an array at 0 to match another language.
- **Never put `nil` in an array.** The length operator `#` is undefined on
  arrays with holes. Use a sentinel value, or keep an explicit count.
- **Use `ipairs` for arrays and `pairs` for records.** `pairs` visits keys
  in no particular order, so never rely on its order.
- **Don't modify a table while iterating over it with `pairs`.** Assigning
  to an existing field is allowed; adding a new field is undefined.
- **Copy tables explicitly** when a caller must not see later changes.
  Assignment shares the same table.

## Metatables and objects

- **Use metatables sparingly.** They make ordinary-looking code behave in
  surprising ways. Reach for them for objects with methods, and for
  `__close` and `__gc` resource handling, not for clever syntax.
- **Write classes with one metatable and a constructor:**

  ```lua
  local UserStore = {}
  UserStore.__index = UserStore

  function UserStore.new()
    return setmetatable({ users = {} }, UserStore)
  end

  function UserStore:add(user)
    self.users[user.id] = user
  end
  ```

- **Prefer composition to inheritance chains.** Each extra `__index` level
  is another place a lookup can go wrong, and another lookup at run time.
- **Don't change the metatables of built-in types** (the shared string
  metatable, for example). Every module in the program sees the change.

## Strings

- **Use `table.concat` to build a string in a loop.** Repeated `..` copies
  the whole string each time, which is quadratic.
- **Lua patterns aren't regular expressions.** They have no alternation
  (`|`), and `%` is the escape character, not `\`. Escape user input with
  `%` before putting it in a pattern, or pass `true` as the plain-text flag
  to `string.find`.

## Security

- **Never run untrusted code with `load`.** If you must evaluate data as
  Lua, give it an empty environment (the `env` argument of `load`) and
  allow only text chunks (`'t'` mode). Bytecode can crash the interpreter.
- **Don't build shell commands from input** for `os.execute` or
  `io.popen`. Validate arguments against an allowlist, or avoid the shell.
- **Validate data at the boundary.** Check types and ranges where external
  data (files, network, host calls) enters, so the rest of the code can
  trust it.

## Testable design

- **Pass dependencies in.** A function that takes its clock, file system or
  network client as an argument can be tested with a stub.
- **Keep I/O at the edges.** Pure functions that transform tables are easy
  to test with busted; the code that reads and writes stays thin.

## Performance

- **Measure before optimising.** Lua is fast enough for most work; the
  profiler shows where it isn't.
- **Avoid creating tables and closures in hot loops.** Each one is garbage
  the collector must clean up later.
- **Stream large input** with `io.lines`, or `file:read(n)` in blocks, rather
  than `file:read("a")`, which reads the whole file into memory.

## Sources

- [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/)
- [Programming in Lua](https://www.lua.org/pil/)
- [Olivine Labs Lua Style Guide](https://github.com/Olivine-Labs/lua-style-guide)
- [LuaRocks style guide](https://github.com/luarocks/lua-style-guide)
