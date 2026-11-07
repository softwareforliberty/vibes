# Nix Tools

The free/open source tools that format, lint, audit and test Nix files,
and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Nix](https://github.com/NixOS/nix) 2.34 or later | LGPL-2.1 | Linting, Testing | Pure evaluation, `nix flake check`, and `nix build --rebuild` |
| [nixfmt](https://github.com/NixOS/nixfmt) | MPL-2.0 | Formatting | Formatting Nix files in the RFC 166 style |
| [treefmt](https://github.com/numtide/treefmt), as `nixfmt-tree` | MIT | Formatting | Running nixfmt over the whole tree for `nix fmt` |
| [statix](https://github.com/molybdenumsoftware/statix) | MIT | Linting | Anti-patterns, such as a manual `inherit`, a needless `let` or a repeated key |
| [deadnix](https://github.com/astro/deadnix) | GPL-3.0 | Linting, Code quality | Unused `let` bindings and function arguments |
| [nixf-tidy](https://github.com/nix-community/nixd), from nixd | LGPL-3.0 | Linting | Undefined variables, and a `with` or `rec` that nothing uses |
| [jq](https://github.com/jqlang/jq) | MIT | Linting | Checking `flake.lock` |
| [flake-checker](https://github.com/DeterminateSystems/flake-checker) | Apache-2.0 | Auditing | Checking that nixpkgs is upstream, supported and recent |
| [vulnix](https://github.com/nix-community/vulnix) | BSD-3-Clause | Auditing | Known vulnerabilities in a package's run-time closure |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [NixOS test framework](https://nixos.org/manual/nixos/stable/#sec-nixos-tests), with `systemd-analyze` | MIT, LGPL-2.1 | Testing | Booting NixOS modules in VMs and checking them |

The [example](idioms.md#a-complete-example)'s package also runs
ShellCheck on its script, as the [SH guide](../../languages/SH/tools.md)
describes.

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`statix.toml`](statix.toml) | statix |
| [`vulnix-whitelist.toml`](vulnix-whitelist.toml) | vulnix, with `--whitelist`: a template to edit |

nixfmt, deadnix, nixf-tidy and flake-checker have no config files. This
guide runs them with their defaults, or with the flags shown below.

## Versions

This guide was checked with these versions. Every tool except Nix comes
from nixpkgs, from the `nixos-26.05` branch at commit
`c56a87d8e41ce69bd2af57eb35dcc117a9dfca33`, so a project's `flake.lock`
pins its tools along with everything else:

| Tool | Version |
| --- | --- |
| Nix | 2.34.9, from `nixos/nix:2.34.9@sha256:53b5ec518b696373829ea305c3c07a8c870113e44648c88ec484ef078550fd4f`, and 2.35.4, from `nixos/nix:2.35.4@sha256:f159a58f390677f41e8e900a74b6e2f9c7f27b364122ae6acf7a652ce6c551c0` |
| nixfmt | 1.5.0 |
| treefmt (`nixfmt-tree`) | 2.6.0 |
| statix | `0-unstable-2026-05-14` |
| deadnix | 1.3.2 |
| nixf-tidy (`nixf`) | 2.9.1 |
| jq | 1.8.2 |
| flake-checker | 0.2.14 |
| vulnix | 1.12.4 |
| gitleaks | 8.30.1 |
| systemd (in the VM) | 260.5 |

- **statix has had no tagged release since 0.5.8 in September 2023.** Its
  original repository says it has moved, and Nixpkgs builds it from the
  [Molybdenum Software fork](https://github.com/molybdenumsoftware/statix),
  which is maintained, at a commit, so the version is a date. Use the
  Nixpkgs package, and drop statix if the fork stops being maintained:
  nixf-tidy and deadnix cover the most important checks.
- Run each tool from the project's own nixpkgs, with
  `nix shell --inputs-from . nixpkgs#<tool> --command <tool>`, or from the
  dev shell. `--inputs-from .` takes `nixpkgs` from `flake.lock`, so it's
  the same version CI runs. `nix run nixpkgs#<tool>` without it takes
  whatever the user's registry points at.

## Formatting

nixfmt formats Nix files with no options. The flake's `formatter` output
is `nixfmt-tree`, which runs nixfmt over every Nix file in the
repository, so check in CI and rewrite locally with:

```sh
nix fmt -- --ci
nix fmt
```

- `--ci` makes treefmt fail when a file would change, and skip its cache.
- To check files without the flake:
  `git ls-files -z -- '*.nix' | xargs -0 nixfmt --check`.
- The [lint check](#linting) runs `nixfmt --check` too, so
  `nix flake check` fails on an unformatted file.

## Linting

The example's `lint` check, in
[`nix/checks.nix`](idioms.md#a-complete-example), runs nixfmt, statix,
deadnix and nixf-tidy over the Nix files, so `nix flake check` fails on
any finding. The dev shell has all four, to run directly while you work.

### nix flake check

`nix flake check` evaluates every output, checks each has the right type,
and builds every check for the current system. It rejects a `checks` or
`packages` entry that isn't a derivation and a `nixosModules` entry that
isn't a module, and warns about old output names. Run it twice in CI:

```sh
nix flake check --no-update-lock-file --no-allow-import-from-derivation
nix flake check --no-update-lock-file --no-allow-import-from-derivation \
  --all-systems --no-build
```

- `--no-update-lock-file` fails when `flake.lock` is missing, untracked or
  out of date, instead of writing a new one.
- `--no-allow-import-from-derivation` fails on
  [import from derivation](idioms.md#import-from-derivation).
- The second run evaluates the outputs for every system, such as
  `aarch64-darwin` on a Linux runner, without building them. A builder
  for each system builds them.
- `nix flake check` doesn't build `packages` or `devShells`: it only
  evaluates them. Add each package to `checks`, as the example does.

### statix

statix finds anti-patterns: an assignment that should be an `inherit`
(W03, W04), an empty `let` (W02), a repeated key (W20) and more. It reads
[`statix.toml`](statix.toml) from the current directory or a parent:

```toml
# Every lint is on. To turn one off, add its name with a comment saying why.
disabled = []
# direnv's cache holds generated Nix files that aren't ours to lint.
ignore = [".direnv"]
```

```sh
statix check .
```

- `statix list` lists the lints. statix exits 1 on any finding.
- statix doesn't flag `with` or `rec`. nixf-tidy flags the ones nothing
  uses, below.

### deadnix

deadnix finds unused `let` bindings and unused function arguments,
including names in a `{ ... }` pattern, such as a `pkgs` a module never
reads:

```sh
deadnix --fail .
```

- `--fail` exits 1 on any finding. Without it, deadnix only reports.
- It skips function arguments that start with `_`, such as `_final`.
- Don't pass `--no-lambda-pattern-names`. Its help says it avoids breaking
  `callPackage`, but a `callPackage` file that asks for an argument it
  doesn't use only hides its real dependencies.

### nixf-tidy

nixf-tidy, from nixd, parses a file and reports what a reader would miss:
an undefined variable, a `with` or `rec` that nothing uses, and a
deprecated or unknown builtin. It reads one file on standard input, prints
its findings as JSON, and always exits 0, so `jq` turns findings into a
failure:

```sh
nixf-tidy --variable-lookup < flake.nix | jq --exit-status 'length == 0'
```

- `--variable-lookup` turns on the checks for undefined and unused names,
  and for a needless `with` or `rec`. Without it, nixf-tidy reports only
  parse errors and deprecated syntax.
- It can't see through a `with`: any name under one might exist. That's
  one reason this guide
  [bans `with`](idioms.md#with-and-rec-hide-where-names-come-from).

### with expressions

No linter here flags a `with` that's in use, so `scripts/check` fails on
any:

```sh
if git grep -nE '(^|[^[:alnum:]_-])with [[:alnum:]_.]+;' -- '*.nix'; then
  echo 'with expression found: name each value instead' >&2
  exit 1
fi
```

## Pinning

`scripts/check` checks `flake.lock` and the fetchers, so the traps in
[idioms.md](idioms.md#floating-or-unsupported-nixpkgs) fail the build.
Each check exits non-zero on a problem:

```sh
nix shell --inputs-from . nixpkgs#jq --command jq --exit-status \
  '[.nodes[] | select(.locked.repo? == "nixpkgs")] | length == 1' flake.lock
nix shell --inputs-from . nixpkgs#jq --command jq --exit-status \
  '.nodes[.nodes.root.inputs.nixpkgs].original.ref // "" | test("^nixos-[0-9]{2}\\.[0-9]{2}$")' \
  flake.lock
if git grep -nE 'lib\.fake(Hash|Sha256)|hash = ""' -- '*.nix'; then
  echo 'placeholder hash found: set the real one' >&2
  exit 1
fi
```

- The first fails when more than one nixpkgs is locked, which means an
  input is [missing `follows`](idioms.md#inputs-without-follows).
- The second fails unless the root `nixpkgs` input follows a NixOS
  release branch, such as `nixos-26.05`. It fails on `nixos-unstable`,
  `master` and the registry name `nixpkgs`.
- The third fails on a [placeholder hash](idioms.md#stale-and-fake-hashes).

flake-checker checks what changes with time: that the `nixpkgs` input is
from the NixOS organisation, on a branch that's still supported, and
less than 30 days old. It belongs in `scripts/audit`:

```sh
nix shell --inputs-from . nixpkgs#flake-checker --command \
  flake-checker --no-telemetry --fail-mode
```

- `--fail-mode` exits 1 on any issue. Without it, flake-checker only
  reports.
- `--no-telemetry` stops it sending counts of each issue type to
  Determinate Systems, which it does by default.

## Auditing

### Security analysis

Pure evaluation, `--no-allow-import-from-derivation` and the
[pinning checks](#pinning) are the main security checks for Nix files:
they make sure every input is the one that was reviewed. For a NixOS
service, `systemd-analyze security` scores its exposure from 0 to 10, and
the [VM test](#nixos-vm-tests) fails when it's over the spec's limit.

### Dependency vulnerabilities

vulnix matches the name and version of every package in a closure against
the National Vulnerability Database. Scan each package's run-time
closure, which is what ships:

```sh
nix build --out-link result .#default
nix shell --inputs-from . nixpkgs#vulnix --command \
  vulnix --closure --whitelist vulnix-whitelist.toml ./result
```

- vulnix exits 2 when it finds a vulnerability, and 0 when it finds none.
  It downloads every NVD feed on its first run, into a cache of about
  200 MB, so it belongs in `scripts/audit`. It refuses to run without a
  locale: set `LANG=C.UTF-8`.
- Matching is by name and version, so it reports CVEs that Nixpkgs has
  already patched. It skips a CVE whose ID is in the name of one of the
  package's patches. For the rest, check the package's patches in
  Nixpkgs, then add a [`vulnix-whitelist.toml`](vulnix-whitelist.toml)
  entry:

  ```toml
  # Template: vulnix findings that have been triaged. Each entry names one
  # package version and the CVEs it hides, says why, and expires, so a new CVE
  # or the date brings the finding back. Replace the example below with your
  # own entries, or delete it.
  #
  # ["glibc-2.42-103"]
  # cve = ["CVE-2026-5450"]
  # until = "2026-12-01"
  # issue_url = "https://example.com/issues/42"
  # comment = "Fixed by a patch in Nixpkgs that vulnix can't see"
  ```

- **Give every entry a `cve` list and an `until` date.** A new CVE for the
  package, or the date passing, brings the finding back.
- Fix a real finding by updating nixpkgs (`nix flake update nixpkgs`), not
  with an overlay that patches the package (see
  [Overlays that leak](idioms.md#overlays-that-leak)).

### Secrets

A secret in a tracked file reaches the Nix store as soon as the flake is
evaluated (see [Secrets in the store](idioms.md#secrets-in-the-nix-store)).
Scan the working tree and the full git history:

```sh
gitleaks git --redact
gitleaks dir --redact
```

A secret that reaches history stays exposed after it's deleted, and a
secret that reached a store stays there until garbage collection, and in
any binary cache it was pushed to. Rotate any secret gitleaks finds, then
remove it.

## Code quality

### Dead code

deadnix finds unused bindings and arguments (see [deadnix](#deadnix)).
nixf-tidy finds the same, and a `with` or `rec` that does nothing.

### Testing

Test a flake the way the spec describes it, and write the test first: each
requirement in the [spec](idioms.md#writing-the-spec) becomes a check
that fails until the Nix meets it.

- **Add the check to `checks` before the package or option it tests.** For
  the example, `greets` in [`nix/checks.nix`](idioms.md#a-complete-example)
  came first, and failed until the script printed the right greeting:

  ```sh
  nix build -L .#checks.aarch64-linux.greets
  ```

- **A check is a derivation that fails when the requirement doesn't
  hold,** usually `pkgs.runCommand` with a shell script that ends with
  `touch "$out"`. It runs in the sandbox, with no network and nothing but
  its inputs, so it passes or fails the same way on every machine.
- **Put build-time requirements in the package itself:**
  `disallowedRequisites = [ shellcheck ];` fails the build when its output
  refers to ShellCheck, and `doCheck = true` runs the program's own tests.
- `nix flake check` runs every check. A check that fails stops the run
  with "failed to build attribute 'checks.<system>.<name>'".

### NixOS VM tests

A NixOS module is tested by booting it: `pkgs.testers.runNixOSTest` builds
a VM for each node, starts them, and runs a Python test script against
them. A failing command fails the check. The test for the
[greet module](idioms.md#nixos-services-with-full-authority), in
`nix/vm-test.nix`:

```nix
# Boots a VM with services.greet on, then checks the greeting and how
# exposed the service is.
{ self }:

{
  name = "greet";

  nodes.machine = {
    imports = [ self.nixosModules.default ];
    services.greet = {
      enable = true;
      name = "Nix";
    };
  };

  testScript = ''
    machine.wait_for_unit("greet.service")
    machine.succeed("journalctl --unit greet.service | grep --fixed-strings 'Hello, Nix!'")
    machine.succeed("systemd-analyze security --threshold=10 greet.service")
  '';
}
```

In the example's `flake.nix`, `checks` gains the test on Linux, and a new
`nixosModules` output exports the module, with the flake's own package as
the default. These are the two outputs, without the rest:

```nix
{
  checks = eachSystem (
    pkgs:
    import ./nix/checks.nix {
      inherit pkgs;
      greet = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
    }
    // lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
      vm = pkgs.testers.runNixOSTest (import ./nix/vm-test.nix { inherit self; });
    }
  );

  nixosModules.default =
    { pkgs, ... }:
    let
      inherit (pkgs.stdenv.hostPlatform) system;
    in
    {
      imports = [ ./nix/module.nix ];
      services.greet.package = lib.mkDefault self.packages.${system}.default;
    };
}
```

- `--threshold` counts in tenths, so `--threshold=10` fails when the
  exposure is over 1.0. The hardened module scores 0.2. With only
  `DynamicUser`, it scores 8.2 and the test fails.
- **VM tests need KVM.** The test derivation requires the `kvm` and
  `nixos-test` system features, and on a builder without `/dev/kvm`,
  `nix flake check` fails with "missing system features". Run them on a
  Linux CI runner with KVM.
- Without KVM, `nix flake check --no-build` still evaluates the test, and
  `nix build .#checks.<system>.vm.driver` builds the test driver, which
  type-checks the test script: a misspelt `machine.wait_for_unitt` fails
  there.
- QEMU falls back to emulation when KVM is missing, so declaring the
  feature runs the test without it, slowly. The example's test took about
  two minutes that way, in a container on an Apple silicon Mac. Use it to
  try a test, not in CI:

  ```sh
  nix build -L --option system-features 'kvm nixos-test benchmark big-parallel uid-range' \
    .#checks.aarch64-linux.vm
  ```

### Reproducibility

Build a package again and compare it with the first build, byte for byte.
`--rebuild` fails with "may not be deterministic" when they differ:

```sh
nix build .#default
nix build --rebuild .#default
```

- Rebuild every check and fixed-output derivation that changed, too.
  `--rebuild` on a fetcher downloads again, and fails with "hash mismatch"
  when its [hash is stale](idioms.md#stale-and-fake-hashes).
- A difference usually comes from a timestamp, a random value or the build
  directory's path in the output. `--keep-failed` keeps the second build's
  output, with a `.check` suffix, to compare with the first.

## scripts/check and scripts/audit

`scripts/check` runs what's local and fast, and what the lock file
already pins:

- `nix fmt -- --ci`.
- `nix flake check`, with `--no-update-lock-file` and
  `--no-allow-import-from-derivation`. It builds the package, its tests and
  the `lint` check (nixfmt, statix, deadnix and nixf-tidy), and on Linux
  the VM tests, which need KVM.
- The same with `--all-systems --no-build`, to evaluate every system.
- The [`with`](#with-expressions) and [pinning](#pinning) checks: one
  nixpkgs, a release branch, no placeholder hashes.

`scripts/audit` runs what's slow or needs the network, or whose result
changes with time:

- flake-checker, on the age and support of nixpkgs.
- vulnix on each package's run-time closure.
- gitleaks over the full history.
- The reproducibility check, `nix build --rebuild`, on each package.
