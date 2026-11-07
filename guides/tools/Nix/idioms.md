# Nix Idioms and Principles

How to write flakes, packages, development shells and NixOS modules well.
[coding-style.md](coding-style.md) covers how Nix files look. This guide
covers the traps that make a build impure, unrepeatable or unsafe, how the
programming principles apply to Nix, and how to write the spec. Every
example follows the style guide.

## Principles

- **A build is a pure function of its inputs.** Every input is pinned in
  `flake.lock` or by hash, evaluation reads nothing from the machine, and
  the same commit builds the same result anywhere.
- **The store is public and immutable.** Anything that reaches
  `/nix/store` can be read by every user and process on the machine, and
  never changes. Secrets stay out of it.
- **Packages, shells and checks are separate.** A package is what ships, a
  development shell is the tools people use, and a check is what CI
  proves. Each is its own output.
- **flake.nix is wiring.** The logic lives in small files, each a function
  of exactly what it needs.
- **A service gets the least authority that works:** its own dynamic user,
  no capabilities, a read-only system and no network unless it needs one.

## The traps

Each of these looks fine and works in a quick test, and many appear in
quick-start examples and blog posts.

### Impure evaluation

`import <nixpkgs> { }` builds against whatever channel the machine has.
`builtins.fetchTarball` with no hash fetches whatever the URL returns
today, `builtins.currentSystem` is whatever machine runs the build, and
`builtins.getEnv` reads the user's environment. The same file builds
different things on different machines and on different days.

- **Evaluate flakes in pure mode, which is the default.** Pure evaluation
  rejects each of these at once:
  - `<nixpkgs>`: "cannot look up '<nixpkgs>' in pure evaluation mode".
  - `builtins.fetchTarball` or `builtins.fetchurl` without a hash: "in
    pure evaluation mode, 'fetchTarball' requires a 'sha256' argument".
  - `builtins.currentSystem`: "attribute 'currentSystem' missing".
- **`builtins.getEnv` doesn't fail in pure mode:** it returns `""`. Code
  that reads an environment variable silently gets an empty string, so
  never read configuration that way. Pass it as a flake input or an
  option.
- **Take every input from `inputs`,** so it's pinned in `flake.lock`, and
  fetch everything else with a fetcher that takes a hash, such as
  `pkgs.fetchurl` or `pkgs.fetchFromGitHub`.
- **Name the system explicitly.** Build per-system outputs from a list of
  systems (see [Flakes](coding-style.md#flakes)), never from
  `builtins.currentSystem`, and never call `import nixpkgs { }` without
  `system`, which fails for the same reason.
- Never pass `--impure` to make an error go away (see
  [Escape hatches](#escape-hatches-unfree-broken-and-impure)).

### Floating or unsupported nixpkgs

`inputs.nixpkgs.url = "nixpkgs";` isn't a pinned branch: it's looked up in
the user's flake registry, which by default points at
`nixpkgs-unstable`, and on each machine may point somewhere else. `master`
has commits that Hydra hasn't built yet, so nothing comes from the binary
cache, and a release branch past its end of life gets no security fixes.

- **Follow a supported release branch of NixOS/nixpkgs:**
  `github:NixOS/nixpkgs/nixos-26.05`. `flake.lock` pins the exact commit,
  and the branch says which stream of updates `nix flake update` takes.
- **Update the lock in a reviewed change,** on a schedule, with a bot that
  runs `nix flake update` and opens a pull request, so security fixes
  arrive and CI checks each one.
- **Move to the next release before the current one's end of life.**
  Releases come out in May and November, and each has security support
  for about a month after the next one.
- **Use `nixos-unstable` only when you need newer packages,** and accept
  that each update can break the build. Never use `master`.
- `scripts/check` fails unless the root nixpkgs follows a release branch,
  and flake-checker in `scripts/audit` fails when it's unsupported or more
  than 30 days old (see [tools.md](tools.md#pinning)).

### An uncommitted flake.lock

Without `flake.lock` in git, every clone and every CI run resolves each
input again, to whatever its branch points at that day. Nix writes a new
lock file with no more than a warning, and two builds of the same commit
get different nixpkgs.

- **Commit `flake.lock`,** and change it only with `nix flake update` or
  `nix flake lock`, never by hand.
- **Run CI with `--no-update-lock-file`.** It fails when the lock file is
  missing, untracked or out of date with `flake.nix`, instead of writing a
  new one.
- Update one input at a time when you need to, with
  `nix flake update <input>`, so a change to one input doesn't move the
  others.

### Inputs without follows

Most flakes have their own `nixpkgs` input. Without `follows`, each one
locks its own copy: adding `sops-nix` without the `follows` line below
put a second nixpkgs, `nixpkgs_2`, in `flake.lock`. Every copy is another
download, another evaluation of Nixpkgs, and another set of packages that
may differ from yours, with its own unpatched vulnerabilities.

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = _: { };
}
```

- **Add `inputs.<name>.follows` for every input that has its own nixpkgs,**
  as above, so the whole project builds against one.
- Leave out `follows` only when the input is tested against its own pin
  and breaks on yours, and say so in a comment.
- `scripts/check` counts the nixpkgs in `flake.lock` and fails on more
  than one (see [tools.md](tools.md#pinning)). `nix flake metadata`
  shows the tree.

### Secrets in the Nix store

Every file in `/nix/store` is readable by every user and process on the
machine, is copied to every machine and binary cache the closure goes to,
and stays until garbage collection. A path literal copies the file into
the store when it's used: `passwordFile = ./db-password;` puts the
password in a world-readable file named
`/nix/store/<hash>-db-password`. So does `builtins.readFile` of a secret
used in any derivation or configuration, and so does a secret written into
a NixOS option. In a flake, every file tracked by git is copied into the
store when the flake is evaluated.

- **Pass secrets as run-time paths, written as strings:**
  `"/run/secrets/db-password"`. The store then holds only the path, never
  the content. Use the options that take a file, such as
  `users.users.<name>.hashedPasswordFile`, never ones that take the value.
- **Put the secret there at activation,** with sops-nix or agenix, which
  keep it encrypted in git and decrypt it into `/run` on the target
  machine, owned by the service that reads it.
- **Give a service its secret with systemd's `LoadCredential`,** which
  copies it into a directory only that service can read:

  ```nix
  {
    systemd.services.greet.serviceConfig.LoadCredential = [
      "api-token:/run/secrets/greet-api-token"
    ];
  }
  ```

  The program reads `$CREDENTIALS_DIRECTORY/api-token`.
- **Never commit a secret,** even encrypted with a key in the repository.
  Keep `.env` files and keys untracked and out of the flake.
- gitleaks finds secrets committed to the repository (see
  [tools.md](tools.md#secrets)).

### The whole repository as src

`src = ./.;` copies every file in the repository into the store: the
flake, the docs, the CI config, and any file that shouldn't leave the
machine. Every change to any of them gives the source a new hash, so the
package rebuilds after editing the README.

- **Build `src` from a file set** that names what the build reads:

  ```nix
  { lib }:

  lib.fileset.toSource {
    root = ../src;
    fileset = ../src/greet.sh;
  }
  ```

- `lib.fileset.toSource` fails at evaluation if a listed file is missing,
  and `lib.fileset.gitTracked` keeps untracked files out.
- Give checks their own file sets too, such as
  [`nixFiles`](#a-complete-example), so each reruns only when its own
  inputs change.

### Stale and fake hashes

A fixed-output derivation, such as `fetchurl` or `fetchFromGitHub`, is
found by its hash, not its URL. Change the URL or the version but not the
hash, and Nix finds the old download in the store and uses it: the build
succeeds, with the old source. A placeholder such as `lib.fakeHash` fails
the build, and the hash it prints ("got: sha256-...") is only what the
server sent that day, not what upstream released.

- **Change the hash whenever the URL, the version or the revision
  changes.** Set it to `lib.fakeHash`, build, check the new hash against
  upstream's published checksum or signed tag, then commit it.
  `nix-update` changes the version and the hash together, but the check
  against upstream is still yours.
- **Rebuild changed fetchers with `--rebuild`.** `nix build --rebuild`
  downloads again and fails with "hash mismatch" when the hash is stale.
- **Never commit a placeholder.** `scripts/check` fails on `lib.fakeHash`,
  `lib.fakeSha256` and `hash = ""` (see [tools.md](tools.md#pinning)).

### Escape hatches: unfree, broken and impure

`config.allowUnfree = true`, `NIXPKGS_ALLOW_UNFREE=1`, `allowBroken` and
`--impure` all make an error go away. `allowUnfree` accepts every unfree
package, including ones added later by accident. `allowBroken` builds
packages that Nixpkgs knows don't work. `--impure` turns off every check
in [Impure evaluation](#impure-evaluation), and the environment variables
need it.

- **Allow unfree packages by name,** with `allowUnfreePredicate`, in one
  place:

  ```nix
  { nixpkgs, system }:

  import nixpkgs {
    inherit system;
    config.allowUnfreePredicate =
      pkg:
      builtins.elem (nixpkgs.lib.getName pkg) [
        "terraform"
      ];
  }
  ```

- **Don't set `allowBroken`.** Fix the package, pin an older version that
  works, or drop it. To try one build, set
  `problems.handlers.<name>.broken = "warn"` for that one package.
- **Never use `--impure` in a check or a build that ships.** Pass anything
  the build needs as an input.
- **Don't set `accept-flake-config = true`, and don't add users to
  `trusted-users`.** A flake's `nixConfig` can add binary caches and
  their keys, and a trusted user can do the same for every build. The
  Nix manual says a trusted user is essentially root.

### with and rec hide where names come from

`with pkgs;` brings every name in Nixpkgs into scope, so a reader can't
tell whether `curl` is the package, a `let` binding or an argument. A
misspelt name fails only when it's evaluated: nixf-tidy flags an undefined
variable in plain code, but can't flag one inside `with`, where any name
might exist. `rec` does the same to an attribute set, so a name can
silently refer to the set's own attribute instead of the one outside.

- **Write `pkgs.curl`, or `inherit (pkgs) curl;` in a `let`.** A list of
  packages written out is longer, and says exactly where each comes from.
- **Use `let` instead of `rec`** (see
  [let, rec and with](coding-style.md#let-rec-and-with)).
- nixf-tidy flags a `with` or a `rec` that nothing uses. No tool here
  flags one that's used, so `scripts/check` fails on any `with`
  expression (see [tools.md](tools.md#linting)).

### rec and overrides

A package written as `mkDerivation rec { ... }`, with a `src` URL that
uses `${version}`, builds. But `overrideAttrs { version = "2.0"; }`
changes the version and keeps the old URL, because `rec` resolved
`version` before the override.

- **Pass `mkDerivation` a function of `finalAttrs`,** and read other
  attributes through it, as the
  [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/#mkderivation-recursive-attributes)
  describes. An override then changes every attribute that uses the value:

  ```nix
  {
    lib,
    stdenv,
    fetchurl,
  }:

  stdenv.mkDerivation (finalAttrs: {
    pname = "hello";
    version = "2.12.3";

    src = fetchurl {
      url = "mirror://gnu/hello/hello-${finalAttrs.version}.tar.gz";
      hash = "sha256-DV9gFUOC/uELEUocNOeF2LH0kgc64tOm97FHaHs2aqA=";
    };

    meta.license = lib.licenses.gpl3Plus;
  })
  ```

- Changing the version still needs a new hash (see
  [Stale and fake hashes](#stale-and-fake-hashes)). Nixpkgs 26.05 warns
  when an override sets `version` but not `src`: "was overridden with
  `version` but not `src`". Override `src` with its new hash too.

### Overlays that leak

An overlay changes the whole package set it's applied to. A flake that
exports `overlays.default` replacing `openssl` changes `openssl` for every
consumer that applies it, and for every package that depends on it: they
all rebuild, with nothing from the binary cache, and run a build of
openssl that Nixpkgs never tested.

- **Export packages, not overlays,** where you can. A consumer adds
  `inputs.greet.packages.${system}.default` to what it needs, and nothing
  else changes.
- **Change one package for one consumer with `override` or
  `overrideAttrs`,** at the point of use, so only that consumer changes:

  ```nix
  { greet }:

  greet.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ [ ./fix-greeting.patch ];
  })
  ```

- **An overlay a flake exports only adds attributes,** such as the
  project's own packages. It never replaces one that's already there:

  ```nix
  final: _prev: {
    greet = final.callPackage ./nix/package.nix { };
  }
  ```

- **Write overlays as `final: prev:`.** Take the package being changed
  from `prev`, and its dependencies from `final`. `final.openssl` inside
  the overlay that defines `openssl` is infinite recursion.

### Import from derivation

`import (pkgs.runCommand ...)`, or `builtins.readFile` of a build's output,
makes evaluation stop and wait for a build. Evaluation becomes slow and
serial, `nix flake show` and `nix flake check --all-systems` need a
builder for every system just to evaluate, and Nixpkgs and Hydra reject
it.

- **Generate Nix code in a separate step,** commit the output, and check
  in `scripts/check` that it's current.
- **Run checks with `--no-allow-import-from-derivation`,** which fails
  with "cannot build ... during evaluation because the option
  'allow-import-from-derivation' is disabled".
- If a tool such as a language's lock-file converter needs it, keep it out
  of `checks` and the default package, and say why in a comment.

### Packages, dev shells and checks mixed up

A package that lists linters in `nativeBuildInputs` makes every user build
them. A CI job that runs `nix develop --command make test` tests the dev
shell, never the package that ships. And a check that reaches the network
passes on a laptop and fails in the sandbox.

- **`packages` holds what ships,** with only the dependencies its build
  and run time need.
- **`devShells` holds the tools people use,** and takes the package's
  build inputs with `inputsFrom` instead of listing them again.
- **`checks` holds everything CI proves,** built in the sandbox with no
  network: the package itself, tests of what it does, and the lint and
  format gates. `nix flake check` builds checks, but only evaluates
  `packages`, so add each package to `checks` too.
- A program's own test suite runs in the package's `checkPhase`, with
  `doCheck = true`, so a package with failing tests doesn't build.

### One huge flake.nix

A `flake.nix` of hundreds of lines mixes inputs, package builds, shell
scripts, tests and NixOS configuration in one scope, where every name is
visible to every other, and every change touches the same file.

- **Keep `flake.nix` to inputs and wiring.** Each package, check set,
  module and test is its own file, imported with `callPackage` or
  `import`, as the [example](#a-complete-example) does.
- **Give each file only the arguments it uses,** so its dependencies are
  visible at the top and deadnix flags any that aren't.
- Split a large project into several flakes only when the parts are
  released separately. Each flake is another lock file to keep current.

### NixOS services with full authority

`systemd.services.<name>` with only `ExecStart` runs as root, with every
capability, write access to the whole system and the network. A bug in
the program is then a bug with root. `systemd-analyze security` scores
the greet service that way, as the
[style guide's module](coding-style.md#nixos-modules) writes it, 9.4 out
of 10, "UNSAFE". With `DynamicUser = true` added, it scores 8.2.

- **Run each service as a `DynamicUser`,** which systemd creates for the
  service and removes when it stops, and add the hardening options for
  everything it doesn't need. The greet service below scores 0.2:

  ```nix
  # services.greet: prints a greeting at boot, as a dynamic user that can't
  # write to the system, reach the network or gain privileges.
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

      name = lib.mkOption {
        type = lib.types.str;
        default = "world";
        description = "Who to greet.";
      };
    };

    config = lib.mkIf cfg.enable {
      systemd.services.greet = {
        description = "Print a greeting";
        wantedBy = [ "multi-user.target" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = utils.escapeSystemdExecArgs [
            (lib.getExe cfg.package)
            cfg.name
          ];
          DynamicUser = true;
          CapabilityBoundingSet = "";
          DevicePolicy = "closed";
          IPAddressDeny = "any";
          LockPersonality = true;
          MemoryDenyWriteExecute = true;
          PrivateDevices = true;
          PrivateNetwork = true;
          PrivateUsers = true;
          ProcSubset = "pid";
          ProtectClock = true;
          ProtectControlGroups = true;
          ProtectHome = true;
          ProtectHostname = true;
          ProtectKernelLogs = true;
          ProtectKernelModules = true;
          ProtectKernelTunables = true;
          ProtectProc = "invisible";
          RestrictAddressFamilies = "none";
          RestrictNamespaces = true;
          RestrictRealtime = true;
          SystemCallArchitectures = "native";
          SystemCallFilter = [
            "@system-service"
            "~@privileged @resources"
          ];
          UMask = "0077";
        };
      };
    };
  }
  ```

- A service that needs the network drops `PrivateNetwork`, `IPAddressDeny`
  and `RestrictAddressFamilies = "none"`, and lists the address families
  it uses, such as `"AF_INET AF_INET6"`.
- **Keep the firewall closed by default.** A module that opens a port has
  an `openFirewall` option that defaults to `false`.
- The [VM test](tools.md#nixos-vm-tests) fails when the score goes over
  1.0.

### Changing system.stateVersion

`system.stateVersion` looks like the NixOS version, so it's tempting to
bump it on upgrade. It isn't: it records the release the machine was
installed with, and modules use it to choose the default version of
software that can't upgrade its own data, such as a database. Changing it
can switch a service to a version that can't read its existing data, and
the NixOS manual warns of data loss.

- **Set `system.stateVersion` once, at install, and never change it.**
  Upgrade NixOS by changing the nixpkgs input.
- Migrate a service's data first, following the release notes, if you
  ever need the newer default.

## The principles in Nix

How the [programming principles](../../../principles.md) apply to Nix:

- **Immutability:** the store never changes once a path is built; a new
  configuration is a new generation, and a rollback is switching back to
  the old one; `flake.lock` is changed only by `nix flake update`.
- **Single source of truth:** every input pinned once, in `flake.lock`,
  with one nixpkgs for the whole project through `follows`; the tools
  pinned by the same lock, so the dev shell and CI run the same versions;
  each package's build written once, in its own file, and used by
  `packages`, `devShells` and `checks` alike.
- **Fail fast:** pure evaluation; `--no-update-lock-file` and
  `--no-allow-import-from-derivation` in CI; option types; path literals
  and file sets that fail at evaluation when a file is missing; hashes on
  every download; `doCheck = true`; `disallowedRequisites` to keep build
  tools out of the run-time closure.
- **Least authority:** secrets outside the store, read from `/run` and
  given to one service with `LoadCredential`; services as dynamic users,
  hardened, with the firewall closed; no `trusted-users` or
  `accept-flake-config`; builds in the sandbox, with no network unless
  they have a fixed hash.
- **Separation of concerns:** packages, dev shells and checks as separate
  outputs; options apart from their effect in a module; source apart from
  the Nix files that build it.
- **KISS and YAGNI:** `lib.genAttrs` instead of a helper flake; no overlay
  where a package will do; no flake-parts or module system for the flake
  itself until several flakes share structure; no option a user hasn't
  asked for.

## Writing the spec

A spec states what the flake must do in terms a check can prove.
"Reproducible and secure" can't be checked; "builds bit for bit the same
twice, and the service scores at most 1.0" can. For the example:

| Requirement | Checked by |
| --- | --- |
| Builds on aarch64-linux and x86_64-linux, and evaluates on aarch64-darwin | `nix flake check` on each Linux system, and `--all-systems --no-build` |
| `greet Nix` prints `Hello, Nix!`, and `greet` alone greets the world | `checks.greets` |
| Evaluates in pure mode, with no import from derivation | `nix flake check --no-allow-import-from-derivation` |
| Locks one nixpkgs, from a supported release branch less than 30 days old | The lock-file checks, flake-checker |
| Ships no build tool, such as ShellCheck, in its run-time closure | `disallowedRequisites` in the package |
| Has a run-time closure under 60 MiB | `nix path-info --closure-size` |
| Builds bit for bit the same twice | `nix build --rebuild` |
| The service runs as a dynamic user, with exposure at most 1.0 | VM test (`systemd-analyze security --threshold=10`) |
| Has no known vulnerability in its run-time closure | vulnix |
| Contains no unfree package except the ones listed | Evaluation, with `allowUnfreePredicate` |

Write the checks before the Nix that meets them, as
[tools.md](tools.md#testing) describes, so each requirement fails first and
passes once the flake meets it.

## Spikes

A spike builds and runs things locally. `nix build`, `nix develop` and
`nix flake check` only add paths to the store, which garbage collection
removes. They never change the machine's configuration. `nix run` runs the
program, which can do whatever the program does, so point it at test data.

- Try a newer input without touching the lock file:
  `nix build --override-input nixpkgs github:NixOS/nixpkgs/nixos-unstable`.
  Nix reports "not writing modified lock file".
- Try a NixOS configuration in a VM with
  `nixos-rebuild build-vm --flake .#<host>`, or in a
  [VM test](tools.md#nixos-vm-tests).
- **A spike never runs `nixos-rebuild switch`, `boot` or `test`, or a
  deployment tool, against a real machine.** `test` changes the running
  system too, until the next reboot. Never point a spike at production.

## A complete example

A small flake for `greet`, a shell script that prints a greeting. It has
a package, a development shell, and checks that test the package and run
the format and lint gates. Its files:

```text
flake.nix
flake.lock
statix.toml
nix/package.nix
nix/checks.nix
src/greet.sh
```

`flake.nix` only wires the parts together:

```nix
{
  description = "greet: prints a greeting";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  outputs =
    { self, nixpkgs }:
    let
      inherit (nixpkgs) lib;

      # Listed here, so supporting a new system is a reviewed change.
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];

      eachSystem = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      packages = eachSystem (pkgs: {
        default = pkgs.callPackage ./nix/package.nix { };
      });

      devShells = eachSystem (pkgs: {
        default = pkgs.mkShellNoCC {
          inputsFrom = [ self.packages.${pkgs.stdenv.hostPlatform.system}.default ];
          packages = [
            pkgs.deadnix
            pkgs.nixf
            pkgs.nixfmt
            pkgs.statix
          ];
        };
      });

      checks = eachSystem (
        pkgs:
        import ./nix/checks.nix {
          inherit pkgs;
          greet = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
        }
      );

      formatter = eachSystem (pkgs: pkgs.nixfmt-tree);
    };
}
```

`nix/package.nix` builds the package from the script alone:

```nix
# greet: a shell script that prints a greeting.
{
  lib,
  stdenvNoCC,
  shellcheck,
}:

stdenvNoCC.mkDerivation {
  pname = "greet";
  version = "1.0.0";

  # Only the script reaches the store, so an edit anywhere else in the
  # repository doesn't rebuild the package.
  src = lib.fileset.toSource {
    root = ../src;
    fileset = ../src/greet.sh;
  };

  doCheck = true;
  nativeCheckInputs = [ shellcheck ];
  checkPhase = ''
    runHook preCheck
    shellcheck greet.sh
    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall
    install -D --mode=0555 greet.sh "$out/bin/greet"
    runHook postInstall
  '';

  meta = {
    description = "Print a greeting";
    license = lib.licenses.mit;
    mainProgram = "greet";
    platforms = lib.platforms.unix;
  };
}
```

`nix/checks.nix` holds what `nix flake check` builds. It's imported, not
called with `callPackage`, which would add an `override` function to the
set that `nix flake check` rejects as not a derivation:

```nix
# The checks that `nix flake check` builds: the package, what it does, and
# the format and lint gates over the Nix files.
{ pkgs, greet }:

let
  inherit (pkgs) lib;

  # Only the Nix files and the linters' config, so the lint reruns only
  # when one of them changes.
  nixFiles = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      (lib.fileset.fileFilter (file: file.hasExt "nix") ../.)
      ../statix.toml
    ];
  };
in
{
  package = greet;

  greets = pkgs.runCommand "greet-greets" { nativeBuildInputs = [ greet ]; } ''
    [ "$(greet Nix)" = "Hello, Nix!" ]
    [ "$(greet)" = "Hello, world!" ]
    touch "$out"
  '';

  lint =
    pkgs.runCommand "lint"
      {
        nativeBuildInputs = [
          pkgs.deadnix
          pkgs.jq
          pkgs.nixf
          pkgs.nixfmt
          pkgs.statix
        ];
      }
      ''
        cd ${nixFiles}
        find . -name '*.nix' -exec nixfmt --check {} +
        statix check .
        deadnix --fail .
        find . -name '*.nix' -print0 | while IFS= read -r -d "" file; do
          nixf-tidy --variable-lookup < "$file" | jq --exit-status 'length == 0' > /dev/null \
            || { echo "nixf-tidy: findings in $file"; exit 1; }
        done
        touch "$out"
      '';
}
```

`src/greet.sh` follows the [SH guide](../../languages/SH/coding-style.md):

```sh
#!/bin/sh
# Print a greeting to the name given as the first argument, or to the world.
set -eu
printf 'Hello, %s!\n' "${1:-world}"
```

- `nix flake check` builds the three checks for the machine's system:
  the package, with ShellCheck in its `checkPhase`; `greets`, which runs
  it; and `lint`. The linters come from the same locked nixpkgs as
  everything else, so CI and every developer run the same versions.
- `fixupPhase` rewrites the script's `#!/bin/sh` to the store's Bash, so
  the package runs on systems with no `/bin/sh`. Its run-time closure is
  Bash, glibc and their libraries, 51 MiB.
- `nix develop` gives a shell with ShellCheck, from `inputsFrom`, and the
  Nix linters. `nix fmt` formats every Nix file with nixfmt.
- [tools.md](tools.md#nixos-vm-tests) adds the
  [NixOS module](#nixos-services-with-full-authority) and its VM test.

## Sources

- [Nix reference manual](https://nix.dev/manual/nix/2.34/)
- [Flakes](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-flake)
  and [nix flake check](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-flake-check)
- [Pure evaluation](https://nix.dev/manual/nix/2.34/command-ref/conf-file#conf-pure-eval)
  and [allow-import-from-derivation](https://nix.dev/manual/nix/2.34/command-ref/conf-file#conf-allow-import-from-derivation)
- [trusted-users](https://nix.dev/manual/nix/2.34/command-ref/conf-file#conf-trusted-users)
- [Nixpkgs manual](https://nixos.org/manual/nixpkgs/stable/):
  [fixed-point arguments of mkDerivation](https://nixos.org/manual/nixpkgs/stable/#mkderivation-recursive-attributes),
  [overlays](https://nixos.org/manual/nixpkgs/stable/#chap-overlays),
  [file sets](https://nixos.org/manual/nixpkgs/stable/#sec-functions-library-fileset),
  [unfree packages](https://nixos.org/manual/nixpkgs/stable/#sec-allow-unfree)
  and [broken packages](https://nixos.org/manual/nixpkgs/stable/#sec-allow-broken)
- [NixOS manual](https://nixos.org/manual/nixos/stable/):
  [writing modules](https://nixos.org/manual/nixos/stable/#sec-writing-modules)
  and [NixOS tests](https://nixos.org/manual/nixos/stable/#sec-nixos-tests)
- [system.stateVersion](https://nixos.org/manual/nixos/stable/options#opt-system.stateVersion)
- [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
  and [systemd credentials](https://systemd.io/CREDENTIALS/)
- [sops-nix](https://github.com/Mic92/sops-nix) and
  [agenix](https://github.com/ryantm/agenix)
- [NixOS release support](https://endoflife.date/nixos)
