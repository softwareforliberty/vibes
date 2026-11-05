# Lua Coding Style

A general-purpose coding style for Lua projects. It builds on the
[Olivine Labs Lua Style Guide](https://github.com/Olivine-Labs/lua-style-guide)
and the [LuaRocks style guide](https://github.com/luarocks/lua-style-guide),
with the layout fixed by [StyLua](https://github.com/JohnnyMorganz/StyLua)
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(scope, modules, errors, tables and other idioms), see [idioms.md](idioms.md).

The tools that check Lua code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Lua 5.4**. It adds integer subtypes, `<const>`
and `<close>` local attributes, and the generational garbage collector.

Code that must also run on **Lua 5.1 or LuaJIT** (common in embedded hosts)
can't use `goto`, integer division (`//`), bitwise operators or local
attributes, and must use `unpack` instead of `table.unpack`. State the
target at the top of the project's README and set the linter's standard
library to match (see [tools.md](tools.md#linting)).

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- When a call or table constructor doesn't fit on one line, put one item per
  line and end with a trailing comma. Adding an item then changes only one
  line in a diff:

  ```lua
  local user = create_user({
    name = name,
    email = email,
    roles = { 'admin' },
  })
  ```

### Line length

- Lines are at most **80 characters**. The formatter enforces it.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- Name files in `snake_case` with the `.lua` extension. A module's file name
  matches the name passed to `require`: `require('app.user_store')` loads
  `app/user_store.lua`.

### One thing per line

- One statement per line. Don't join statements with `;`.
- The body of an `if`, `for`, `while` or `function` goes on its own line,
  even when it's short. A one-line `if` hides the branch in a diff.
- Separate functions with one blank line, and use single blank lines inside
  functions, sparingly, to separate logical steps.

## Strings

- Use **single quotes** for strings: `'hello'`. Use double quotes only when
  the string contains a single quote, so it needs no escaping.
- Use long brackets (`[[ ... ]]`) for multi-line text, and add `=` signs
  (`[==[ ... ]==]`) when the text itself contains `]]`.
- Build strings with `string.format()` or `table.concat()`, not long chains
  of `..`. Each `..` creates a new string, and a format string shows the
  output at a glance.

## Whitespace

- One space around binary operators, including `..`: `a + b`,
  `name .. '!'`.
- No space after unary operators: `-x`, `not done`, `#items`.
- One space inside the braces of a non-empty one-line table:
  `{ 1, 2, 3 }`. No spaces inside parentheses or square brackets:
  `f(x)`, `items[1]`.
- One space after a comma, none before it.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Variables and functions | `snake_case` | `retry_count`, `load_config` |
| Modules | `snake_case` | `user_store` |
| Classes (tables used with a metatable as a type) | `PascalCase` | `UserStore` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Booleans | `is_`, `has_` or `can_` prefix | `is_ready` |
| Ignored values | `_` | `for _, user in ipairs(users) do` |

- Name things for what they are. Single letters are fine only for loop
  counters and very short scopes.
- Don't mark module-internal functions with a prefix. Declare them `local`
  instead, which is what actually makes them private (see
  [idioms.md](idioms.md#scope-and-locals)).
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Variables

- Declare every variable with `local`. A missing `local` creates a global,
  which the linter rejects.
- Declare variables where they're first needed, in the narrowest scope that
  works.
- Mark values that never change as `<const>`:
  `local MAX_RETRIES <const> = 3`. The compiler then rejects reassignment.

## Tables

- Use the constructor syntax: `local user = { name = 'ada', age = 36 }`.
- Use dot access for identifier keys (`user.name`) and brackets only when
  the key isn't a valid identifier or is computed (`headers['Content-Type']`,
  `counts[word]`).
- Don't mix array items and named fields in one table. A table is either a
  sequence or a record, so `#` and `ipairs` behave as expected.

## Functions

- Define named functions with `local function name()`, not
  `local name = function()`. The first form lets the function call itself
  recursively and gives it a name in tracebacks.
- Define methods with a colon and call them with a colon:

  ```lua
  function UserStore:find(id)
    return self.users[id]
  end

  local user = store:find(42)
  ```

- Always use parentheses in calls, even with a single string or table
  argument: `require('json')`, not `require 'json'`. One call style is
  easier to scan and search.
- Return early to handle errors and edge cases, so the main path stays at
  the shallowest indentation.

## Modules

- Put all `require` calls at the top of the file, each assigned to a
  `local`.
- A module builds a local table and returns it as the last statement:

  ```lua
  local json = require('json')

  local M = {}

  function M.load(path)
    ...
  end

  return M
  ```

- Never set globals from a module. Callers get the module only through
  `require`.

## Comments

- Comments start with `-- ` (two dashes and one space). Put a trailing
  comment one space after the code.
- Comments explain **why**, not **what**. The code already says what it
  does.
- Document every public function with a `---` doc comment in the
  [LuaCATS](https://luals.github.io/wiki/annotations/) annotation format.
  Editors and the Lua Language Server read it:

  ```lua
  --- Fetch a user from the store.
  ---@param id integer ID of the user to fetch.
  ---@return User|nil user The matching user, or nil if none matches.
  ---@return string|nil err Why the lookup failed.
  function M.fetch_user(id)
  ```

- Don't leave commented-out code. Version control keeps the history.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Olivine Labs Lua Style Guide and borrows from:

- [Olivine Labs Lua Style Guide](https://github.com/Olivine-Labs/lua-style-guide)
- [LuaRocks style guide](https://github.com/luarocks/lua-style-guide)
- [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/)
- [StyLua documentation](https://github.com/JohnnyMorganz/StyLua)
- [LuaCATS annotations](https://luals.github.io/wiki/annotations/)
