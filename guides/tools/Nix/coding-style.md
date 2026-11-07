# Nix Coding Style

A general-purpose style for Nix files: flakes, packages, development shells
and NixOS modules. It follows the
[Nix language reference](https://nix.dev/manual/nix/2.34/language/), the
[Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/) and the
[RFC 166 format](https://github.com/NixOS/rfcs/blob/master/rfcs/0166-nix-formatting.md)
that nixfmt implements (see [Sources](#sources)).

This guide covers how Nix files look. For how to write them well (the
traps, pinning, purity, secrets and how to write the spec), see
[idioms.md](idioms.md).

The tools that check Nix files are listed in [tools.md](tools.md).

## Baseline

- **Nix 2.34 or later.** It's the version NixOS 26.05 ships as
  `nixVersions.stable`, and the Nix team supports only the latest release
  and the one in the stable NixOS release. This guide was checked with Nix
  2.34.9 and 2.35.4.
- **Flakes, with the `nix-command` and `flakes` features turned on:**

  ```text
  experimental-features = nix-command flakes
  ```

  Both are still marked experimental in Nix 2.35, so their commands and
  lock file may change between releases. This guide uses them anyway,
  because they give each project a lock file that pins every input, pure
  evaluation by default, and a standard set of outputs that
  `nix flake check` checks. Without flakes, each of those is a convention
  to build and enforce by hand.
- **Keep the experimental part thin.** `flake.nix` only wires things
  together. Packages, modules and checks live in plain Nix files that know
  nothing about flakes, so a change to the flake interface, or a move to
  another pinning tool, touches one file.
- **Nixpkgs 26.05,** from the `nixos-26.05` branch, which has security
  support until 31 December 2026. Move to the next release before then
  (see [Floating nixpkgs](idioms.md#floating-or-unsupported-nixpkgs)).

## Files

A small project keeps its Nix files together, apart from its source:

```text
flake.nix         inputs and outputs only: the wiring
flake.lock        the pinned inputs, committed
statix.toml       linter config
nix/package.nix   one file per package, called with callPackage
nix/checks.nix    the checks that nix flake check builds
nix/module.nix    a NixOS module, if the project ships one
nix/vm-test.nix   its NixOS VM test
src/              the program
```

- **One package per file,** written as a function of its dependencies and
  called with `callPackage`, as Nixpkgs does. The file can then be built,
  overridden and tested on its own.
- **Name files in kebab-case,** by what they hold: `package.nix`,
  `vm-test.nix`. Several packages go in `nix/packages/<name>.nix`.
- **Start every file with a comment** that says what it is, as the
  [example](idioms.md#a-complete-example) does.

## Formatting

nixfmt formats every Nix file, in the RFC 166 style that Nixpkgs uses. Run
it with no options: 2-space indents and a 100-column limit are its
defaults, and a project that changes them formats differently from every
other Nix project. Where this guide and nixfmt's output could disagree on
layout, nixfmt wins. See [tools.md](tools.md#formatting).

- nixfmt doesn't break long strings, URLs or comments. Keep them within 100
  columns by hand where you can.
- It keeps blank lines you write between bindings, and removes extra ones.
  Use one blank line to group related bindings.

## Naming

- **Variables, attributes and options are lowerCamelCase:** `nixFiles`,
  `eachSystem`, `services.greet.enable`. It's the convention throughout
  Nixpkgs and NixOS, so names read the same as the ones they sit beside.
- **Package names are lowercase with hyphens,** as upstream spells them:
  `greet`, `my-tool`. The attribute name, the `pname` and the file or
  directory name are the same, so each can be found from the others.
- **A package's version goes in `version`,** never in `pname`, so
  `lib.getName` and update tools can tell them apart.
- **Feature flags are `withX` or `enableX`** with a default, such as
  `withJson ? true`, as in Nixpkgs.
- **Prefix a deliberately unused function argument with `_`,** such as
  `_final` in an overlay. deadnix and nixf-tidy skip it, and flag every
  other unused name. They still flag `_name` inside a `{ ... }` pattern:
  remove that name instead.

## let, rec and with

- **Bind local names with `let ... in`.** Every name has one visible
  binding, and nothing outside sees it.
- **Don't use `rec`.** It makes every attribute visible to every other, so
  a name can refer to itself by mistake and loop forever, and an attribute
  can't be overridden from outside (see
  [rec and overrides](idioms.md#rec-and-overrides)). In `mkDerivation`,
  pass a function of `finalAttrs` instead. nixf-tidy flags a `rec` that
  nothing uses.
- **Don't use `with`.** `with pkgs;` makes every name in Nixpkgs visible,
  so a reader can't tell where a name comes from, and nixf-tidy can't flag
  a misspelt one (see
  [with and rec](idioms.md#with-and-rec-hide-where-names-come-from)).
  Write `pkgs.jq`, or `inherit (pkgs) jq;` in a `let`.
- **Use `inherit`** instead of `x = x;` or `jq = pkgs.jq;`. statix flags
  both (W03, W04).

## Functions and arguments

- **Take an attribute set pattern,** with each argument named, so a caller
  that passes the wrong one gets an error.
- **Don't add `...` to a package file.** Without it, a misspelt argument,
  such as `.override { shelcheck = ...; }`, fails with "called with
  unexpected argument". With it, the typo is silently ignored.
- **NixOS modules do take `...`.** The module system passes every module
  more arguments than it uses, and a module without `...` fails to
  evaluate.
- **Ask only for what the function uses.** deadnix flags an unused
  argument, such as a `pkgs` that a module never reads.
- Give defaults (`withJson ? true`) only to options a caller is meant to
  change. A dependency never has a default: `callPackage` supplies it.

## Strings and paths

- **Refer to files in the repository with path literals:** `./src`,
  `../statix.toml`, never the string `"./src"`. Nix checks the path exists
  when it evaluates, and copies the file into the store when it's used.
- **Refer to files that exist only at run time with strings:**
  `"/run/secrets/db-password"`. A path literal would copy the file into
  the store (see [Secrets in the store](idioms.md#secrets-in-the-nix-store)).
- **Name a package's program with `lib.getExe pkg`,** not
  `"${pkg}/bin/name"`. It reads `meta.mainProgram`, so the program's name
  is written once, in the package, and a rename changes one line.
- **Escape every value that reaches a shell** with `lib.escapeShellArg`,
  and every value in a systemd `ExecStart` with
  `utils.escapeSystemdExecArgs`. Shell and systemd quote differently, and
  a name with a space or a `$` otherwise breaks the command or runs part
  of it.
- Write shell in indented strings, `'' ... ''`, and follow the
  [SH guide](../../languages/SH/coding-style.md). Move anything longer
  than a few lines into a script file in `src/`, where ShellCheck can
  check it.

## Comments

- **Comments start with `#`,** on their own line above what they explain.
- **Say why:** why a package is pinned, why a check is off, why an
  override exists. `# build greet` above a build of greet says nothing.
- Document functions that others call, such as a project's own library,
  with RFC 145 doc comments, `/** ... */`, which `nixdoc` and the Nix
  REPL read.

## Flakes

Lay out `flake.nix` in this order:

1. `description`, one line.
2. `inputs`, each pinned to a branch or tag, with `follows` where an input
   has its own nixpkgs (see [follows](idioms.md#inputs-without-follows)).
3. `outputs`, as a function of exactly the inputs it uses.

In `outputs`:

- **List the supported systems once,** and build per-system outputs with
  `lib.genAttrs`, as the [example](idioms.md#a-complete-example) does. A
  new system is then a reviewed one-line change. A helper flake such as
  flake-utils is one more input to pin and update, for one line of code.
- **Take packages from `nixpkgs.legacyPackages.${system}`.** Each
  `import nixpkgs { ... }` evaluates Nixpkgs again, so do it once, and
  only when you need `config` or overlays.
- **Order the outputs:** `packages`, `devShells`, `checks`, `formatter`,
  then `overlays`, `nixosModules` and `nixosConfigurations`.
- **Name the main entry `default`,** as in `packages.<system>.default`.
  The old names, such as `defaultPackage` and `devShell`, still work but
  make `nix flake check` warn.

## NixOS modules

Write a module in one shape, so every reader finds its options and their
effect in the same place:

```nix
# services.greet: prints a greeting at boot.
{
  config,
  lib,
  utils,
  ...
}:

let
  cfg = config.services.greet;
in
{
  options.services.greet = {
    enable = lib.mkEnableOption "greet, which prints a greeting at boot";

    package = lib.mkOption {
      type = lib.types.package;
      description = "The greet package to run.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.greet = {
      wantedBy = [ "multi-user.target" ];
      serviceConfig.ExecStart = utils.escapeSystemdExecArgs [ (lib.getExe cfg.package) ];
    };
  };
}
```

- **Options under `options`, their effect under `config`,** with the
  whole `config` behind `lib.mkIf cfg.enable`, so importing a module
  changes nothing until it's turned on.
- **Bind `cfg` once** to the module's own options, so every use reads
  `cfg.x`.
- **Give every option a `type` and a `description`.** The type makes a
  wrong value fail at evaluation, with the file that set it.
- **Use `lib.mkDefault` for values a user may change,** and keep
  `lib.mkForce` for overriding another module, with a comment saying why.
  Two modules that both force a value can't be combined.
- This module shows the shape only: its service runs as root. The
  [complete module](idioms.md#nixos-services-with-full-authority) adds the
  systemd hardening that a real one needs.

## Sources

- [Nix language reference](https://nix.dev/manual/nix/2.34/language/)
- [Nix experimental features](https://nix.dev/manual/nix/2.34/development/experimental-features)
- [RFC 166: Nix formatting](https://github.com/NixOS/rfcs/blob/master/rfcs/0166-nix-formatting.md)
  and the [Nix format standard](https://github.com/NixOS/nixfmt/blob/master/standard.md)
- [RFC 145: doc comments](https://github.com/NixOS/rfcs/blob/master/rfcs/0145-doc-strings.md)
- [Nixpkgs package naming](https://github.com/NixOS/nixpkgs/blob/master/pkgs/README.md#package-naming)
- [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/)
- [Writing NixOS modules](https://nixos.org/manual/nixos/stable/#sec-writing-modules)
  and [option declarations](https://nixos.org/manual/nixos/stable/#sec-option-declarations)
- [nix flake check](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-flake-check)
- [NixOS release support](https://endoflife.date/nixos)
