# Erlang Tools

The free/open source tools that lint, format and check Erlang code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Erlang/OTP](https://www.erlang.org/) compiler, Dialyzer, xref and cover | Apache-2.0 | Linting, Code quality | Compiler warnings, type analysis, cross-reference checks, layer rules and test coverage |
| [rebar3](https://rebar3.org/) | Apache-2.0 | Linting | Building, and running the other tools |
| [erlfmt](https://github.com/WhatsApp/erlfmt) | Apache-2.0 | Formatting | Formatting source files |
| [Elvis](https://github.com/inaka/elvis_core) (through `rebar3_lint`) | Apache-2.0 | Linting, Auditing | Linting style, and banning unsafe calls |
| [rebar3_audit](https://github.com/Taure/rebar3_audit) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [rebar3_mutate](https://github.com/Taure/rebar3_mutate) | MIT | Code quality | Mutation testing |

## Config files

These files are drop-in templates: copy them into the project root.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor and IDE, through EditorConfig |
| [rebar.config](rebar.config) | rebar3: plugins, compiler warnings, erlfmt, Dialyzer, xref, cover and rebar3_mutate (merge into the project's `rebar.config`) |
| [elvis.config](elvis.config) | Elvis, through `rebar3 lint` |
| [.jscpd.json](.jscpd.json) | jscpd |

The `rebar.config` excerpts below are copied from that file.

Add the rebar3 plugins to `rebar.config`:

```erlang
{project_plugins, [erlfmt, rebar3_lint, rebar3_audit, {rebar3_mutate, "0.6.1"}]}.
```

## Formatting

erlfmt owns layout. Check formatting in CI, and fix it locally with
`rebar3 fmt --write`:

```sh
rebar3 fmt --check
```

Tell erlfmt which files to format in `rebar.config`:

```erlang
{erlfmt, [
    {files, ["{src,include,test}/*.{hrl,erl}", "rebar.config"]}
]}.
```

## Compiler warnings

Compiler warnings are the first lint gate. Turn on the extra warnings for
every build, and turn warnings into errors only in a CI profile, so a newer
OTP with new warnings doesn't break a user's build:

```erlang
{erl_opts, [debug_info, warn_export_vars, warn_unused_import, warn_missing_spec]}.

{profiles, [
    {ci, [{erl_opts, [warnings_as_errors]}]}
]}.
```

```sh
rebar3 as ci compile
```

## Linting

Dialyzer checks the `-spec`s against how functions are actually called.
Cache its analysis between CI runs, because building it from scratch is
slow:

```sh
rebar3 dialyzer
```

Turn on the warnings that catch ignored return values and specs that don't
match the code:

```erlang
{dialyzer, [
    {warnings, [error_handling, extra_return, missing_return, unknown, unmatched_returns]}
]}.
```

Elvis checks style rules the formatter doesn't cover:

```sh
rebar3 lint
```

## Auditing

### Security analysis

No maintained FOSS security analyser supports Erlang; Opengrep doesn't parse
it. The closest check is Elvis's `no_call` rule, which bans the calls the
idioms forbid on untrusted input. Add it to `elvis.config`:

```erlang
[
    {config, [
        #{
            files => ["src/*.erl"],
            ruleset => erl_files,
            rules => [
                {elvis_style, no_call, #{
                    no_call_functions => [
                        {erlang, list_to_atom, 1},
                        {erlang, binary_to_atom, 2},
                        {erlang, binary_to_term, 1},
                        {os, cmd, 1}
                    ]
                }}
            ]
        }
    ]}
].
```

### Dependency vulnerabilities

Commit `rebar.lock`, and fail the build when any dependency has a known
vulnerability. rebar3_audit reads the lockfile and checks every pinned
version against the GitHub Advisory Database:

```sh
rebar3 audit
```

rebar3_audit needs OTP 27 or later. It only reads `rebar.lock`, so run it in
a CI job on a newer OTP even when the project itself supports OTP 26.

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
lizard -l erlang -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format erlang --min-tokens 50 --exit-code 1 src
```

### Dead code

The compiler warns about unused functions, variables and imports. xref finds
exported functions nothing calls, and calls to functions that don't exist.
Set its checks in `rebar.config`:

```erlang
{xref_checks, [
    undefined_function_calls,
    undefined_functions,
    locals_not_used,
    exports_not_used,
    deprecated_function_calls
]}.
```

```sh
rebar3 xref
```

A library's API functions are meant to be called from outside, so list them
in `{xref_ignores, [...]}` rather than turning `exports_not_used` off.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Turn coverage on for every test run, and set the minimum, in
`rebar.config`:

```erlang
{cover_enabled, true}.
{cover_opts, [verbose, {min_coverage, 80}]}.
```

```sh
rebar3 do eunit, ct
rebar3 cover
```

### Mutation testing

rebar3_mutate makes small changes to the code, such as turning `>=` into
`=<`, and runs the module's tests against each one. A change the tests
still pass, a surviving mutant, is behaviour no test pins down. A full run
is slow, so `scripts/audit` mutates only the lines changed since the base
branch:

```sh
rebar3 mutate --diff origin/main --min-score 80
```

The plugin is in `project_plugins` in the [template](rebar.config). This
guide was checked with rebar3_mutate 0.6.1.

- `--min-score 80` makes the run exit non-zero when the mutation score,
  the share of mutants the tests kill, is under 80%. That's the same bar
  as coverage. Some mutants can't be killed, because they don't change
  what the code does, so 100% is rarely reachable; 80% leaves room for
  them and still fails a change whose tests check little.
- With nothing to mutate in the diff, the run passes without a score.
- Each module is scored against its own EUnit tests, `<module>_tests`.
  A module tested from another test module is skipped, not scored, until
  you map it under `eunit_tests` in a `mutate` section of `rebar.config`.

The report lists each survivor with its file, line, operator and change:

```text
===> Module: price (12 mutants: 9 killed, 3 survived, 0 timed out)
===> Score:  75.0% (9 killed of 12 testable)
===> 
Surviving mutants:
===>   price.erl:line 5 [op_constant] 100 -> 101
===>   price.erl:line 5 [op_constant] 100 -> 99
```

Read it as a missing test: here, the guard `Total >= 100` can move to 101
or 99 and every test still passes, so no test checks the boundary at 100.
Write the test that fails on the mutant, not one that just runs the line.
A mutant that times out counts against the score, so raise `--timeout`
for slow tests rather than letting them fail.

### Architecture

xref queries enforce the layers as the
[architecture guide](../../../architecture/README.md#enforce-it) asks. Erlang
has one flat module namespace, so name each module after its layer, such as
`myapp_core_greeting` and `myapp_adapters_console`, and write each rule as a
query over the module call graph, `ME`, using the
[query language](https://www.erlang.org/doc/apps/tools/xref.html). rebar3
fails when a query's answer isn't the expected value, and prints the calls
that broke it.

The rules depend on the project's layers, so they aren't in the
[template](rebar.config). Add them to the project's `rebar.config`. The
module prefixes are examples: replace them with the layers in the project's
`design.md`.

```erlang
{xref_queries, [
    %% The core calls no edge module.
    {"(ME | \"myapp_core_.*\" : Mod) || \"myapp_(adapters|cli).*\" : Mod", []},
    %% No modules call each other in a cycle.
    {"components ME", []}
]}.
```

`rebar3 xref`, already under [Dead code](#dead-code), runs these queries
with the other checks:

```sh
rebar3 xref
```

- The first query lists every call from a core module to an edge module, and
  must find none. Edges may call the core.
- The second lists the groups of modules that call each other, directly or
  through others, and must find none.

## Sources

- [rebar3_mutate documentation](https://hexdocs.pm/rebar3_mutate/)
