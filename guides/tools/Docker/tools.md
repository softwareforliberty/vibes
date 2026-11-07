# Docker Tools

The free/open source tools that format, lint, audit and test Dockerfiles
and images, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Docker Engine](https://github.com/moby/moby) 25.0 or later, with [Buildx](https://github.com/docker/buildx) 0.15 or later | Apache-2.0 | Linting, Testing | Building and running images, and the build checks (`docker build --check`) |
| [dockerfmt](https://github.com/reteps/dockerfmt) | MIT | Formatting | Formatting Dockerfiles, and the shell in `RUN` through shfmt |
| [hadolint](https://github.com/hadolint/hadolint) | GPL-3.0 | Linting, Auditing | Dockerfile rules, label schema, and ShellCheck on every `RUN` |
| [ShellCheck](https://www.shellcheck.net/) | GPL-3.0 | Linting | Shell scripts that `RUN` steps and entrypoints call |
| [Trivy](https://trivy.dev/) | Apache-2.0 | Auditing | Dockerfile misconfigurations, and vulnerabilities and secrets in built images |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Rules hadolint lacks: digest pins, piped installers, unchecked downloads, heredocs without `set -e` |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code across Dockerfiles |
| [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) | Apache-2.0 | Testing | Checking an image's metadata and files against its spec |

Docker Desktop is not open source. Docker Engine, its CLI and Buildx are,
and they're all the tools here need.

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig, and dockerfmt |
| [`.dockerignore`](.dockerignore) | Docker, when it sends the build context: a template to edit |
| [`.hadolint.yaml`](.hadolint.yaml) | hadolint |
| [`trivy.yaml`](trivy.yaml) | Trivy |
| [`.opengrep/dockerfile.yaml`](.opengrep/dockerfile.yaml) | Opengrep |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`container-structure-test.yaml`](container-structure-test.yaml) | container-structure-test: a template for the example image |

## Versions

This guide was checked with these versions. Run each tool that publishes
an image from that image, pinned by digest like any other, so nothing is
installed on the host:

| Tool | Version | Image |
| --- | --- | --- |
| hadolint | 2.15.1 | `hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d` |
| dockerfmt | 0.5.4 | `ghcr.io/reteps/dockerfmt:v0.5.4@sha256:f7ccef07090dee3318f3521a91b12956a5655bd347f5c6749a3e5a1da5293626` |
| Trivy | 0.76.2 | `aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb` |
| gitleaks | 8.30.1 | `ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` |
| ShellCheck | 0.11.0 | `koalaman/shellcheck:v0.11.0@sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d` |
| Opengrep | 1.33.1 | None: download the release binary |
| jscpd | 5.4.2 | None: install it from npm |
| container-structure-test | 1.22.1 | None: download the release binary |

- Trivy's own images were the target of the supply-chain attack described
  in [idioms.md](idioms.md#unpinned-base-images), and an image pinned by
  digest was safe from it.
- container-structure-test is in maintenance mode, and its project no
  longer updates its container image, so download the binary from its
  [releases](https://github.com/GoogleContainerTools/container-structure-test/releases).

## Formatting

dockerfmt formats Dockerfiles, including the shell in `RUN` steps. It reads
`indent_size` (4) and `insert_final_newline` from the Dockerfile section of
[`.editorconfig`](.editorconfig), so run it with no formatting flags.
Check in CI, and rewrite locally:

```sh
git ls-files -z -- '*Dockerfile' | xargs -0 dockerfmt --check
git ls-files -z -- '*Dockerfile' | xargs -0 dockerfmt --write
```

- The pathspec `'*Dockerfile'` matches `Dockerfile` and `*.Dockerfile` at
  any depth.
- dockerfmt is young (version 0.x). It leaves a `RUN` that uses `;` or
  `{ }` unformatted, and doesn't change `as` to `AS`; the build checks catch
  that. Where its output and this guide disagree on layout, dockerfmt wins.

## Linting

### Build checks

BuildKit's build checks lint a Dockerfile without building it, and exit
non-zero on any warning:

```sh
docker build --check .
docker build --check -f worker.Dockerfile .
```

The `# check=error=true` directive (see
[coding-style.md](coding-style.md#directives-and-header)) makes an ordinary
build fail on the same warnings, so a build can't ship an image that
`--check` would reject. The checks catch shell-form `CMD` and `ENTRYPOINT`,
secret-like names in `ARG` and `ENV`, inconsistent casing, reserved and
duplicate stage names, and undefined variables.

### hadolint

hadolint parses each Dockerfile, checks it against its DL rules, and runs
ShellCheck on every `RUN`. Files must pass with **no findings**:

```sh
git ls-files -z -- '*Dockerfile' | xargs -0 hadolint
```

It reads [`.hadolint.yaml`](.hadolint.yaml) from the current directory:

```yaml
---
# Fail on every finding, down to info and style.
failure-threshold: style
# Every image says what it is, where its source lives, its licence, and the
# version and commit it was built from.
label-schema:
  org.opencontainers.image.title: text
  org.opencontainers.image.source: url
  org.opencontainers.image.licenses: spdx
  org.opencontainers.image.version: text
  org.opencontainers.image.revision: text
```

- `failure-threshold: style` fails the run on every finding. hadolint's
  default, `info`, lets style findings pass.
- `label-schema` requires the
  [OCI labels](coding-style.md#labels) on the final stage, and checks that
  `source` is a URL and `licenses` an SPDX identifier.
- DL3057, a missing `HEALTHCHECK`, stays off. It reports every build stage
  as well as the final one, so it can't pass on a multi-stage build. Trivy
  and the [image test](#testing) check the health check instead.
- hadolint 2.15.1 can't parse an instruction straight after a heredoc's
  closing delimiter, so leave a blank line there.
- To ignore a rule for one instruction, put
  `# hadolint ignore=DL3008` on the line above it, with a comment saying
  why.

### ShellCheck

hadolint runs ShellCheck on inline `RUN` commands. Scripts the image runs,
such as an entrypoint or a build step in its own file, are linted and
formatted as the [SH](../../languages/SH/tools.md) or
[Bash](../../languages/BASH/tools.md) guide says.

## Auditing

### Security analysis

hadolint and the build checks are the main security checks for a
Dockerfile. Trivy's Dockerfile checks add a second opinion, such as a
missing `USER` (DS-0002) or `HEALTHCHECK` (DS-0026), and a split
`apt-get update` (DS-0017). `--skip-check-update` uses the checks built
into Trivy, so the scan needs no network:

```sh
trivy config --skip-check-update .
```

Trivy reads [`trivy.yaml`](trivy.yaml) from the current directory:

```yaml
---
# Fail the run on any finding.
exit-code: 1
vulnerability:
  # Report only vulnerabilities that have a fixed version to upgrade to.
  ignore-unfixed: true
```

- `exit-code: 1` makes any finding fail the run.
- `ignore-unfixed` applies to the image scan below: a vulnerability with no
  fixed version can't be acted on yet, so it doesn't fail the build.

The starter rules in [`.opengrep/dockerfile.yaml`](.opengrep/dockerfile.yaml)
catch traps from [idioms.md](idioms.md) and
[coding-style.md](coding-style.md#heredocs) that no other tool here does: a
`FROM` without a digest, a download piped into a shell, a remote `ADD`
without a checksum, and a heredoc that doesn't start with `set -e`.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

An image's dependencies are its base image's packages and everything the
build installs. Trivy scans the built image: the OS packages, and the
language packages and Go binaries in it. It downloads its vulnerability
database first, so it belongs in `scripts/audit`:

```sh
trivy image hello:dev
```

Rebuild on a newer base digest to fix a finding in the base image. The
language's own guide still audits the project's lock files.

### Secrets

`trivy image` also scans every layer for secrets, so it finds a key that a
`COPY` or `ADD` put in the image, even if a later layer deletes it.

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Duplication

Flag any block of 50 or more tokens that appears twice, such as two
services' Dockerfiles copied from each other. Duplicated code gets fixed in
one place and not the other.

```sh
jscpd --format docker --min-tokens 50 --exit-code 1 .
```

### Testing

Test an image the way the spec describes it, and write the test first:
each requirement in the [spec](idioms.md#writing-the-spec) becomes a check
that fails until the Dockerfile meets it. Two kinds of check cover a spec:

- **container-structure-test** checks what the image is, without starting
  the program: its user, ports, entrypoint, labels, and which files exist,
  with what owner and mode.
- **A script that runs the image** checks what it does: that it becomes
  healthy, which UID its processes run as, its size, and how it stops.

Build the image under a test tag, then run both:

```sh
docker build -t hello:test .
container-structure-test test --image hello:test \
  --config container-structure-test.yaml
scripts/test-image hello:test
```

[`container-structure-test.yaml`](container-structure-test.yaml) is the
test for the [example image](idioms.md#a-complete-example). Replace the
values with the project's own spec:

```yaml
---
schemaVersion: 2.0.0

metadataTest:
  user: 65532:65532
  exposedPorts:
    - "8080"
  entrypoint:
    - /usr/local/bin/hello
  labels:
    - key: org.opencontainers.image.source
      value: https://example.com/hello

fileExistenceTests:
  - name: The service can't change its own binary
    path: /usr/local/bin/hello
    shouldExist: true
    permissions: -rwxr-xr-x
    uid: 0
    gid: 0
  - name: The image has no shell
    path: /bin/sh
    shouldExist: false
```

- Quote the port. The field is a list of strings, and the
  [YAML guide](../../data/YAML/idioms.md#implicit-typing-traps) quotes any
  string that would otherwise read as a number.
- A distroless image has no shell, so `commandTests` can only run the
  program itself. Check files and metadata instead, which need nothing
  inside the image.

`scripts/test-image` runs the image with the least authority the spec
allows, then checks its size, health, user and stop. It follows the
[Bash guide](../../languages/BASH/coding-style.md), and the limits at the
top come from the spec:

```bash
#!/usr/bin/env bash
#
# Check that an image meets its spec: it stays within its size budget,
# becomes healthy, runs as its non-root user, and stops cleanly on SIGTERM.

set -euo pipefail

readonly MAX_BYTES=$((20 * 1000 * 1000))
readonly HEALTHY_WITHIN=10
readonly STOP_WITHIN=5
readonly EXPECTED_UID=65532

container=""

err() {
  printf '%s: %s\n' "${0##*/}" "$*" >&2
}

die() {
  err "$@"
  exit 1
}

cleanup() {
  if [[ -n "${container}" ]]; then
    docker rm --force -- "${container}" >/dev/null
  fi
}

check_size() {
  local image="$1"
  local size
  size="$(docker image inspect --format '{{.Size}}' -- "${image}")"
  if ((size > MAX_BYTES)); then
    die "image is ${size} bytes, over the budget of ${MAX_BYTES}"
  fi
}

wait_healthy() {
  local status=""
  local waited=0
  while ((waited < HEALTHY_WITHIN)); do
    status="$(docker inspect \
      --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' \
      -- "${container}")"
    if [[ "${status}" == "healthy" ]]; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  die "not healthy within ${HEALTHY_WITHIN}s (status: ${status:-none})"
}

check_uid() {
  local top
  local -a lines
  local line
  local uid
  top="$(docker top "${container}" -o pid,uid)"
  mapfile -t lines <<<"${top}"
  for line in "${lines[@]:1}"; do
    read -r _ uid <<<"${line}"
    if ((uid != EXPECTED_UID)); then
      die "a process runs as UID ${uid}, not ${EXPECTED_UID}"
    fi
  done
}

check_stop() {
  local code
  docker stop --timeout "${STOP_WITHIN}" -- "${container}" >/dev/null
  code="$(docker inspect --format '{{.State.ExitCode}}' -- "${container}")"
  if ((code != 0)); then
    die "exited with ${code} when stopped (137: killed after ${STOP_WITHIN}s)"
  fi
}

main() {
  if (($# != 1)); then
    printf 'usage: %s <image>\n' "${0##*/}" >&2
    exit 2
  fi
  local image="$1"

  trap cleanup EXIT
  trap 'exit 1' HUP INT TERM

  check_size "${image}"
  container="$(docker run --detach --read-only --cap-drop ALL \
    --security-opt no-new-privileges -- "${image}")"
  wait_healthy
  check_uid
  check_stop
  printf '%s: %s meets its spec\n' "${0##*/}" "${image}"
}

main "$@"
```

- `docker stop --timeout 5` sends `SIGTERM`, then `SIGKILL` after 5
  seconds. Exit code 137 means the container was killed, so it didn't stop
  in time; 0 means it shut down cleanly.
- `docker image inspect` reports the compressed size with the containerd
  image store and the unpacked size with the older store. Set the budget
  for the store CI uses.
- A program that exits on `SIGTERM` without a handler, as a shell script
  under tini does, exits with 143. Expect that code instead of 0 if the
  spec allows it.

### Reproducibility

Build the same commit twice from scratch, and compare the results byte for
byte. `cmp` exits non-zero when they differ:

```sh
export SOURCE_DATE_EPOCH="$(git log -1 --format=%ct)"
mkdir -p build
docker build --no-cache --output type=oci,dest=build/a.tar,rewrite-timestamp=true .
docker build --no-cache --output type=oci,dest=build/b.tar,rewrite-timestamp=true .
cmp build/a.tar build/b.tar
```

See [Unrepeatable builds](idioms.md#unrepeatable-builds) for what makes a
build differ.

## scripts/check and scripts/audit

`scripts/check` runs what's local and fast:

- `dockerfmt --check` on every Dockerfile.
- `docker build --check` on every Dockerfile.
- hadolint, and ShellCheck on the scripts the image runs.
- `trivy config --skip-check-update .` and Opengrep.
- The tests: build the image, then run container-structure-test and
  `scripts/test-image`. The first build pulls the base images and the
  frontend into the local image store.

`scripts/audit` runs what's slow or needs the network:

- `trivy image` on the built image, which downloads the vulnerability
  database.
- gitleaks over the full history.
- jscpd.
- The reproducibility check, which builds the image twice with no cache.
