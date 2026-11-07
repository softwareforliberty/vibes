# Zig Tools

The free/open source tools that lint, format and check Zig code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Zig](https://ziglang.org/) | MIT | Formatting, Linting, Auditing, Code quality | Formatting (`zig fmt`), compile checks, safety-checked tests and fuzzing |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring test coverage of the compiled test binary |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the project root. The `.editorconfig` matches the
layout `zig fmt` produces.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs |
| [`.jscpd.json`](.jscpd.json) | jscpd |

The other Zig tools need no config files: `zig fmt` has no settings, and the
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

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other. Move logic that appears twice into one
function or a `comptime` generic.

```sh
jscpd --format zig --min-tokens 50 --exit-code 1 src
```

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

### Architecture

The build enforces the layers, as the
[architecture guide](../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. Make each layer its own module in `build.zig`. A file
can `@import` only the modules its module's `.imports` lists, and no file
that belongs to another module, so a core that imports an edge fails to
compile.

Zig analyses only the code that's referenced, so `zig build` misses a
forbidden import in a function nothing calls yet. Give each layer a test, and
reference every declaration from it as under [Dead code](#dead-code), so
`zig build test` analyses all of it. The module names are examples: replace
them with the layers in the project's `design.md`.

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // The core imports no other layer.
    const core = b.createModule(.{
        .root_source_file = b.path("src/core/root.zig"),
        .target = target,
        .optimize = optimize,
    });
    // Each edge imports only the core.
    const adapters = b.createModule(.{
        .root_source_file = b.path("src/adapters/root.zig"),
        .target = target,
        .optimize = optimize,
        .imports = &.{.{ .name = "core", .module = core }},
    });
    // The program wires the layers together, so it imports them all.
    const exe = b.addExecutable(.{
        .name = "app",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/cli/main.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "core", .module = core },
                .{ .name = "adapters", .module = adapters },
            },
        }),
    });
    b.installArtifact(exe);

    // Zig analyses only referenced code, so test every layer.
    const test_step = b.step("test", "Run the tests");
    for ([_]*std.Build.Module{ core, adapters }) |module| {
        const tests = b.addTest(.{ .root_module = module });
        test_step.dependOn(&b.addRunArtifact(tests).step);
    }
}
```

A breach fails the tests with `no module named 'adapters' available`:

```sh
zig build test
```
