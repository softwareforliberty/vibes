# Lua Tools

The free/open source tools that lint, format and check Lua code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [StyLua](https://github.com/JohnnyMorganz/StyLua) | MPL-2.0 | Formatting | Formatting |
| [selene](https://github.com/Kampfkarren/selene) | MPL-2.0 | Linting | Linting, including undefined globals and unused variables |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [busted](https://github.com/lunarmodules/busted) | MIT | Code quality | Running tests |
| [LuaCov](https://github.com/lunarmodules/luacov) | MIT | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.stylua.toml`](.stylua.toml) | StyLua |
| [`selene.toml`](selene.toml) | selene |
| [`lua54.yml`](lua54.yml) | selene, as the Lua 5.4 standard library |
| [`busted.yml`](busted.yml) | selene, as busted's standard library |
| [`.luacov`](.luacov) | LuaCov |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/lua.yaml`](.opengrep/lua.yaml) | Opengrep |

## Formatting

StyLua owns layout. Code must be formatted with no changes left:

```sh
stylua --check .
```

Put the settings in `.stylua.toml`:

```toml
column_width = 80
line_endings = "Unix"
indent_type = "Spaces"
indent_width = 2
quote_style = "AutoPreferSingle"
call_parentheses = "Always"
```

Don't hand-format code StyLua will rewrite, and don't argue with its output
in review.

## Linting

Code must pass selene with **no errors or warnings**:

```sh
selene .
```

Put the settings in `selene.toml`. Set `std` to the Lua version the project
targets (see [coding-style.md](coding-style.md#language-baseline)), so
selene rejects library functions that version doesn't have:

```toml
std = "lua53+lua54+busted"
```

selene ships standard libraries only up to Lua 5.3, so `lua54` and `busted`
are project standard-library files next to `selene.toml`. Each library in
`std` extends the one before it. `lua54.yml` adds the Lua 5.4 syntax
(`<const>` and `<close>`) and the 5.4 globals:

```yaml
---
# Lua 5.4 syntax and globals for selene, which ships libraries only up to
# Lua 5.3. selene.toml loads it after lua53, so its lua_versions entry
# turns on the 5.4 syntax.
lua_versions:
  - lua54
globals:
  coroutine.close:
    args:
      - type:
          display: coroutine
  warn:
    args:
      - type: string
      - required: false
        type: ...
```

`busted.yml` adds the globals busted gives spec files, so the tests are
linted too:

```yaml
---
# The globals busted gives spec files, for selene. selene.toml loads it
# so the tests are linted with the rest of the code.
globals:
  after_each:
    any: true
  # Keep Lua's assert() and allow busted's assert.* fields.
  assert.*:
    any: true
  before_each:
    any: true
  context:
    any: true
  describe:
    any: true
  expose:
    any: true
  finally:
    any: true
  insulate:
    any: true
  it:
    any: true
  lazy_setup:
    any: true
  lazy_teardown:
    any: true
  match:
    any: true
  mock:
    any: true
  pending:
    any: true
  randomize:
    any: true
  setup:
    any: true
  spec:
    any: true
  spy:
    any: true
  strict_setup:
    any: true
  strict_teardown:
    any: true
  stub:
    any: true
  teardown:
    any: true
  test:
    any: true
```

For code that targets LuaJIT, use `std = "lua51+busted"`. selene has no
LuaJIT library, so declare the LuaJIT globals the code uses, such as `bit`
and `jit`, in a project standard-library file. Any global the host provides
goes in a project standard-library file too, never in an inline
`-- selene: allow` comment, so the full list lives in one place.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Opengrep's Lua support is experimental, so keep rules simple: flag calls to
`load`, `loadstring`, `os.execute` and `io.popen` for review, as
[idioms.md](idioms.md#security) requires.

### Dependency vulnerabilities

No FOSS tool checks LuaRocks dependencies against known vulnerabilities,
and the OSV database has no LuaRocks ecosystem. Pin every dependency to an
exact version in the rockspec, and review each dependency's changelog before
upgrading it.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

Fail the build on any function with a cyclomatic complexity over 10 or more
than 60 lines of code. A function past either limit is hard to test and
should be split.

```sh
lizard -l lua -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format lua --min-tokens 50 --exitCode 1 src
```

### Dead code

selene's `unused_variable` lint, on by default, reports unused locals,
parameters and functions. No tool finds unused public functions across
modules, because `require` and table access hide them from static analysis.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Run the tests with busted and collect coverage with LuaCov, then generate
the report:

```sh
busted --coverage
luacov
```

LuaCov has no minimum of its own. Its report, `luacov.report.out`, ends with
a `Total` line giving the overall percentage; check it in CI:

```sh
awk '/^Total/ { sub("%", "", $NF); if ($NF + 0 < 80) exit 1 }' \
  luacov.report.out
```

Put the settings in `.luacov`, so only the project's own code is measured:

```lua
return {
  include = { 'src/' },
  exclude = { 'spec/' },
}
```
