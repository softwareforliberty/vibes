# Zig Tools

The free/open source tools that lint, format and check Zig code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Zig](https://ziglang.org/) | MIT | Formatting, Linting, Auditing, Code quality | Formatting (`zig fmt`), compile checks, safety-checked tests and fuzzing |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring test coverage of the compiled test binary |

## Config files

Copy this file into the project root. It matches the layout `zig fmt`
produces.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs |

The Zig tools need no other config files: `zig fmt` has no settings, and the
compiler's checks are on by default.

## Formatting

`zig fmt` owns layout. Code must come out of it unchanged:

```sh
zig fmt --check .
```

## Linting

Zig has no separate linter. The compiler is strict on its own: it rejects
unused local variables and parameters, a `var` that's never mutated, and an
ignored error. The lint gate is a build plus the tests, with no errors:

```sh
zig build
zig build test
```

`zig ast-check` checks a single file for these errors without a full build,
which is quick enough for an editor or a pre-commit hook:

```sh
zig ast-check src/main.zig
```

## Auditing

### Security analysis

No maintained FOSS static analyser supports Zig, and Opengrep doesn't parse
it. The closest checks are the compiler's own safety checks: run the tests in
`Debug` and in `ReleaseSafe`, where out-of-bounds access, integer overflow and
null unwraps stop the program instead of corrupting memory:

```sh
zig build test
zig build test -Doptimize=ReleaseSafe
```

Fuzz parsers and decoders with Zig's built-in fuzzer, where your platform
supports it. Fuzzing finds inputs that hit the safety checks:

```sh
zig build test --fuzz
```

### Dependency vulnerabilities

No vulnerability database covers Zig packages, and OSV-Scanner doesn't read
`build.zig.zon`. The closest check is the content hash that `build.zig.zon`
records for every dependency, which stops a changed download from being used.
Review each dependency's changes before updating its hash.

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

No maintained FOSS tool measures complexity for Zig; lizard doesn't support
it. The closest check is review: split any function that no longer fits on
one screen or nests more than three levels deep.

### Duplication

No FOSS duplication detector documents support for Zig, including jscpd. The
closest check is review: when the same logic appears twice, move it into one
function or a `comptime` generic.

### Dead code

The compiler rejects unused locals and parameters. It doesn't report unused
functions, because Zig only compiles what's referenced, so an unused function
is never even checked. Reference every declaration from a test, so the
compiler checks all of them:

```zig
test {
    std.testing.refAllDecls(@This());
}
```

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Build the test binary with debug information, then run it under kcov on
Linux:

```sh
zig test src/main.zig --test-no-exec -femit-bin=zig-out/test
kcov --include-path=src zig-out/coverage zig-out/test
```

kcov has no built-in minimum, so read the total from the `coverage.json` file
it writes, and fail the build when it's under 80%.
