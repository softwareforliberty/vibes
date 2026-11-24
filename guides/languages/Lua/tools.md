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
| [`.busted`](.busted) | busted |
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
jscpd --format lua --min-tokens 50 --exit-code 1 src
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
busted
luacov
```

`.busted` turns on coverage for every busted run, so `busted` needs no
flags:

```lua
return {
  _all = {
    coverage = true,
  },
}
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

### Mutation testing

No maintained free mutation testing tool supports Lua, so there's no
mutation check in `scripts/audit`. luamut, the only one written for Lua,
has never had a release: LuaRocks has only a development version from
2023. Generic tools such as universalmutator change text with rules for
C-like languages; they don't know `~=`, `and`, `or` or `--` comments, so
most of their mutants are broken code rather than changed behaviour.

Rely on two checks instead:

- The test reviewer asks of each changed comparison, branch and return
  value whether a test would fail if it changed, such as `>=` turned into
  `>`, and asks for a test at each boundary.
- [Coverage](#coverage) shows the code no test runs at all. It can't show
  a line that runs but whose result no test checks, which is why the
  review matters.

### Architecture

No maintained FOSS tool checks the dependencies between a Lua project's
own modules. selene's `restricted_module_paths` lint skips a `require` that
takes a string, which is how modules are loaded. So a search in
`scripts/check`
[enforces the layers](../../../architecture/README.md#enforce-it).

`require` turns each dot in a module's name into a directory, and returns
what the module's file returns. busted's default path holds `src/?.lua`
and `src/?/init.lua`, so `src/app/core/init.lua` is the module `app.core`.
Make each layer a directory under `src/app/`. The names are examples:
replace them with the layers in the project's `design.md`.

Only what a module returns can be used, and its `local` functions stay
private. Lua can't hide a whole module, though: any code can `require` it
by name. So keep each layer's entry points directly in its directory, such
as `app.core` and `app.adapters.console`, and the rest under an `internal`
folder, such as `src/app/core/internal/format.lua`. The layer's own modules
may require those, and its entry points return only what callers need.
`src/app/core/init.lua`:

```lua
local format = require('app.core.internal.format')

local M = {}

function M.greet(name)
  return format.title('hello, ' .. name)
end

return M
```

Fail `scripts/check` when the core requires an edge, or when code outside a
layer requires one of its internal modules. That covers every spec, so a
layer's own specs use only its entry points too. A breach prints the file,
the line and the `require`:

```sh
if find src/app/core -name '*.lua' -exec grep -nE \
    'require[^[:alnum:]_]*app\.(adapters|cli)([^[:alnum:]_]|$)' \
    /dev/null {} + | grep .; then
  echo 'the core must not require an edge' >&2
  exit 1
fi

for c in core adapters cli; do
  if find src spec -name '*.lua' ! -path "src/app/${c}/*" -exec grep -nE \
      "require[^[:alnum:]_]*app\.${c}\.internal([^[:alnum:]_]|\$)" \
      /dev/null {} + | grep .; then
    echo "require app.${c} only through its entry points" >&2
    exit 1
  fi
done
```

```text
spec/core/breach_spec.lua:1:local format = require('app.core.internal.format')
require app.core only through its entry points
```

- `/dev/null` makes grep name the file even when `find` passes it only one.
  `find` doesn't pass on grep's exit status, so the final `grep .` decides:
  it succeeds only when a line matched.
- The search sees only a `require` of a literal name, in any of its forms,
  such as `require 'app.cli'` or `require [[app.cli]]`. Review must catch a
  `require` of a variable, a module taken from `package.loaded`, and a file
  run with `dofile` or `loadfile`.

To let one existing breach through, skip its file with another `! -path`,
with a comment naming the breach and how to fix it.

Prove each check bites. For the first, the builder keeps a new core module
that requires an edge as `scripts/breaches/core-requires-edge.patch`:

```text
Rule: the core never requires an edge
Fails with: the core must not require an edge

diff --git a/src/app/core/breach.lua b/src/app/core/breach.lua
new file mode 100644
index 0000000..3d57ecf
--- /dev/null
+++ b/src/app/core/breach.lua
@@ -0,0 +1,4 @@
+-- Breach: the core requires an edge.
+local cli = require('app.cli')
+
+return cli
```

## Sources

- [luamut on LuaRocks](https://luarocks.org/modules/ligurio/luamut)
- [universalmutator](https://github.com/agroce/universalmutator)
- [Lua 5.4 manual: modules](https://www.lua.org/manual/5.4/manual.html#6.3)
- [selene: `restricted_module_paths`](https://kampfkarren.github.io/selene/lints/restricted_module_paths.html)
