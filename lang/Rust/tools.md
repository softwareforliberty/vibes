# Rust Tools

The free/open source tools that lint, format and check Rust code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [rustfmt](https://github.com/rust-lang/rustfmt) | MIT OR Apache-2.0 | Formatting | Formatting, run as `cargo fmt` |
| [Clippy](https://github.com/rust-lang/rust-clippy) | MIT OR Apache-2.0 | Linting, Code quality | Finding bugs, unidiomatic code and risky casts |
| [Miri](https://github.com/rust-lang/miri) | MIT OR Apache-2.0 | Auditing | Detecting undefined behaviour in `unsafe` code |
| [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit) | Apache-2.0 OR MIT | Auditing | Checking `Cargo.lock` against the RustSec advisory database |
| [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) | MIT OR Apache-2.0 | Auditing | Enforcing allowed licences and dependency sources |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [cargo-machete](https://github.com/bnjbvr/cargo-machete) | MIT | Code quality | Finding unused dependencies |
| [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) | Apache-2.0 OR MIT | Code quality | Measuring test coverage |

## Formatting

`rustfmt` owns layout, with its default settings. Code must come out of it
unchanged:

```sh
cargo fmt --all --check
```

## Linting

Code must pass Clippy with **no warnings**, across tests, examples and every
feature:

```sh
cargo clippy --all-targets --all-features -- -D warnings
```

Set the lints in `Cargo.toml`, so every build and editor applies them:

```toml
[lints.rust]
missing_docs = "warn"
unsafe_op_in_unsafe_fn = "deny"

[lints.clippy]
pedantic = { level = "warn", priority = -1 }
panic = "warn"
undocumented_unsafe_blocks = "warn"
unwrap_used = "warn"
```

- `pedantic` includes the cast lints that enforce
  [converting with `From` and `TryFrom`](coding-style.md#expressions).
- `unwrap_used` and `panic` enforce the rule that
  [library code doesn't panic](idioms.md#errors). Allow `unwrap()` in tests
  with a `clippy.toml` next to `Cargo.toml`:

  ```toml
  allow-unwrap-in-tests = true
  ```

- `undocumented_unsafe_blocks` enforces the
  [`// SAFETY:` comment rule](coding-style.md#comments).
- Disable a lint only on the item it applies to, with a reason:
  `#[allow(clippy::cast_possible_truncation, reason = "value is < 256")]`.

## Auditing

### Security analysis

Run the tests under Miri in any crate that contains `unsafe` code. Miri
interprets the program and stops at undefined behaviour, such as an
out-of-bounds read or a dangling reference, that ordinary tests can miss. It
needs the nightly toolchain:

```sh
cargo +nightly miri test
```

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `Cargo.lock` and checks every pinned version
against the OSV database.

```sh
osv-scanner scan source -r .
```

cargo-audit checks the same lockfile against the RustSec advisory database,
which also tracks unmaintained and yanked crates:

```sh
cargo audit
```

cargo-deny enforces the rules for what may enter the dependency tree: only
allowed licences, and only crates from crates.io. Put the settings in
`deny.toml`:

```toml
[licenses]
allow = ["Apache-2.0", "BSD-3-Clause", "ISC", "MIT", "Unicode-3.0"]

[sources]
unknown-registry = "deny"
unknown-git = "deny"
```

```sh
cargo deny check licenses sources
```

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
lizard -l rust -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format rust --min-tokens 50 --exitCode 1 src
```

### Dead code

The compiler's `dead_code` lint finds unused private items, and the
`-D warnings` in [Linting](#linting) makes it fail the build. Remove dead code
rather than silencing the lint.

cargo-machete finds dependencies listed in `Cargo.toml` that no code uses. It
works by searching the source, so it can be wrong about crates used only
through macros; confirm a finding before removing the dependency:

```sh
cargo machete
```

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
cargo llvm-cov --all-features --fail-under-lines 80
```

Branch coverage needs the nightly toolchain, so line coverage is the gate on
stable Rust.
