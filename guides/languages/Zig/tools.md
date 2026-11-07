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
| [zentinel](https://github.com/oly-wan-kenobi/zentinel) | MIT | Code quality | Mutation testing |

## Config files

Copy these files into the project root. The `.editorconfig` matches the
layout `zig fmt` produces.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`zentinel.toml`](zentinel.toml) | zentinel |

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

### Mutation testing

zentinel makes small changes to the code, such as turning `>` into `>=`,
and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. It's the only free
maintained tool for Zig, and it's young: 0.1.0, from June 2026, is its
only release, and it needs Zig 0.16.0 exactly.

Each mutant builds from a cold cache, which can take a minute, so
`scripts/audit` mutates only the files changed since the base branch.
zentinel 0.1.0 can't read a diff, so the command writes a copy of
[`zentinel.toml`](zentinel.toml) whose `include` lists those files:

```sh
files=$(git diff --name-only --diff-filter=d --merge-base origin/main \
  -- 'src/*.zig')
if [ -n "$files" ]; then
  mkdir -p zig-out
  list=$(printf '"%s", ' $files)
  sed "s|^include = .*|include = [${list%, }]|" zentinel.toml \
    > zig-out/zentinel-diff.toml
  zentinel --config zig-out/zentinel-diff.toml --root . run \
    --output zig-out/zentinel.json || exit
  count() {
    sed -n "s/^ *\"$1\": \([0-9]*\),\$/\1/p" zig-out/zentinel.json
  }
  killed=$(($(count killed) + $(count timeout)))
  tested=$((killed + $(count survived)))
  echo "Mutation score: $killed of $tested mutants killed"
  [ $((100 * killed)) -ge $((80 * tested)) ]
fi
```

- zentinel has no minimum score of its own: `--fail-on-survivors` fails on
  any survivor, and there's no way to mark a mutant that can't change
  behaviour. So the command reads the counts from the JSON report and
  fails when the mutation score, the share of mutants the tests kill, is
  under 80%. That's the same bar as coverage. Some mutants can't be
  killed, because they don't change what the code does, so 100% is rarely
  reachable; 80% leaves room for them and still fails a change whose tests
  check little.
- It mutates whole files, not just the changed lines, so a survivor
  elsewhere in a changed file counts too.
- A mutant that times out counts as killed: the 10-minute timeout in
  `zentinel.toml` leaves room for the cold build, so a timeout means the
  mutant hangs. `|| exit` stops when the unmutated tests fail.
- `--merge-base` compares with the point the branch left `origin/main`.
  Replace it with the project's base branch, and fetch that first.
- Build it from the `v0.1.0` tag with `zig build -Doptimize=ReleaseSafe`;
  this guide was checked with that version.

zentinel prints each survivor with the change it made:

```text
survived 3 comparison_boundary src/price.zig:11
  -     if (weight > 5) return 10;
  +     if (weight >= 5) return 10;
  selected tests passed: zig test src/price.zig
  likely focus: missing exact-boundary inputs
```

Read it as a missing test: here, no test passes a weight of exactly 5, so
the boundary isn't pinned down. Write the test that fails on the mutant,
not one that just runs the line.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
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

## Sources

- [zentinel README](https://github.com/oly-wan-kenobi/zentinel/blob/v0.1.0/README.md)
- [zentinel configuration](https://github.com/oly-wan-kenobi/zentinel/blob/v0.1.0/docs/CONFIG_SPEC.md)
- [zentinel report format](https://github.com/oly-wan-kenobi/zentinel/blob/v0.1.0/docs/REPORT_FORMAT.md)
