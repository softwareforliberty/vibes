# Docker Idioms and Principles

How to build container images well. [coding-style.md](coding-style.md)
covers how Dockerfiles look. This guide covers the traps that make an image
unsafe, slow or impossible to reproduce, how the programming principles
apply to images, and how to write an image's spec. Every example follows
the style guide.

## Principles

- **An image is a release.** Build it once, from pinned inputs, give it a
  tag that never moves, and promote the same image from test to production.
- **Build and run are separate.** Compilers, package caches and source
  belong in a build stage. The runtime image holds the program and what it
  needs to run, nothing else.
- **Run with the least authority that works:** a non-root user, no Linux
  capabilities, a read-only file system and no shell.
- **One process, one concern.** A container runs one program, which handles
  its own signals and reports its own health.
- **Configuration and secrets come from outside.** The image holds code.
  Settings arrive when the container starts, and build secrets never reach
  a layer.

## The traps

Each of these looks fine and works in a quick test, and many appear in
quick-start examples.

### Unpinned base images

`FROM python:3` or `FROM node:lts` builds from whatever the tag points to
today. Anyone who can push to the repository can point a tag at a
different image: in March 2026, attackers with stolen credentials pushed
malicious Trivy images to Docker Hub as 0.69.5 and 0.69.6, and the
[advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
lists images referenced by digest as safe.

- **Pin every image by tag and digest:**
  `FROM golang:1.27.3-alpine3.24@sha256:fa3d...`. The digest decides what's
  pulled; the tag tells the reader which version it is.
- Pin the digest of the multi-platform index, which is the first `Digest`
  that `docker buildx imagetools inspect <image>` prints, so the same line
  builds on every platform.
- Pin the `syntax` frontend the same way (see the
  [baseline](coding-style.md#baseline)), and every image a `COPY --from`
  names.
- Update the pins in reviewed changes, with a bot that opens a pull request
  for each new digest, so you still get security fixes.
- The Opengrep rule `dockerfile-from-without-digest` flags a `FROM` without
  a digest. hadolint's DL3006 and DL3007 flag a missing tag and `latest`.

### Running as root

With no `USER`, the process runs as root. A bug in the program then gives
an attacker root inside the container, and root on the host if the
container also escapes.

- **End the final stage with a non-root `USER`, as a numeric UID and GID:**
  `USER 65532:65532`. A name only means something inside the image's
  `/etc/passwd`, so a runtime or policy that checks from outside can't
  verify it (DL3066).
- Distroless `nonroot` images already have UID 65532. On other bases,
  create a system user with a fixed UID in the same `RUN` that installs the
  packages, as in the [Debian example](#package-manager-hygiene).
- Never install or use `sudo` (DL3004). Do the root work in the build, and
  switch user once at the end.
- **Drop the rest at run time:**
  `docker run --read-only --cap-drop ALL --security-opt no-new-privileges`.
  The example below runs that way, and the
  [image test](tools.md#testing) runs every image that way.
- **Publish ports on localhost unless they must be public:**
  `-p 127.0.0.1:8080:8080`. Without an address, Docker publishes the port
  on every interface of the host.
- Trivy's DS-0002 flags a Dockerfile with no `USER`, hadolint's DL3002 one
  that ends as root, and the image test checks the UID of every process.

### Secrets in ARG, ENV or layers

`ARG` values are recorded in the image history, `ENV` values are in the
image config, and every file a layer adds stays in that layer, even if a
later `RUN rm` deletes it. Anyone who can pull the image can read them.

- **Pass build secrets with a secret mount.** The secret is mounted only
  while that one `RUN` runs, and never written to a layer:

  ```dockerfile
  RUN --mount=type=secret,id=netrc,target=/root/.netrc,required=true \
      --mount=type=cache,target=/go/pkg/mod \
      go mod download
  ```

  Build with `docker build --secret id=netrc,src="${HOME}/.netrc" .`.
  `required=true` fails the build when the secret is missing, instead of
  running the step without it.
- Use `--mount=type=ssh` for an SSH agent, such as for cloning private
  repositories, instead of copying a key in.
- **Pass run-time secrets when the container starts,** as files mounted by
  the orchestrator or a secret store. Never bake them into the image.
- The build check `SecretsUsedInArgOrEnv`, hadolint's DL3064 and Trivy's
  DS-0031 flag secret-like names in `ARG` and `ENV`. Trivy's image scan
  finds secrets that reached a layer, and gitleaks finds them in the
  repository before they get that far.

### Missing .dockerignore

Without a `.dockerignore`, `COPY . .` copies everything in the build
context: `.git`, `.env` files, local credentials and build output. They end
up in the image, and every change to any of them invalidates the cache.

- **Write `.dockerignore` as an allowlist:** exclude everything with `*`,
  then re-include each path the build needs with `!`. A file added later,
  such as a new secret, stays out until someone lists it. The
  [template](.dockerignore) is the one the example below uses:

  ```text
  # Template: an allowlist. Exclude everything, then re-include only what the
  # build reads, so a new file, such as a secret or a local build output,
  # never reaches the build context by accident. Replace the entries below
  # with the files your own build copies.
  *
  !go.mod
  !go.sum
  !**/*.go
  ```

- `**` matches any number of directories, so `!**/*.go` re-includes Go
  files at any depth.
- Trivy's image scan finds secrets that slipped through.

### Cache-busting order

Copying the whole source before installing dependencies means every source
change downloads every dependency again, and a slow build tempts people to
skip it.

- **Copy the dependency manifests first, install, then copy the source**,
  as the [example](#a-complete-example) does with `go.mod`. The download
  layer is reused until the manifests change.
- Keep package caches in a cache mount, such as
  `--mount=type=cache,target=/go/pkg/mod`. BuildKit keeps it between
  builds, and it never becomes part of the image.
- Declare per-build `ARG`s last (see the
  [order](coding-style.md#order-of-stages-and-instructions)).

### Compilers in the runtime image

A single-stage build ships the compiler, headers, package caches and
source in the runtime image. It's larger, has more packages for scanners to
report, and hands an attacker the tools to build their own.

- **Build in one stage and copy only the output into the final one** with
  `COPY --from=build`.
- Copy named files, never a stage's whole file system (DL3067).
- The [structure test](tools.md#testing) can check that a build tool or a
  shell is absent from the final image.

### Large base images

Every package in the base image is something to patch and something an
attacker can use. A full language image, such as `python:3`, holds a
compiler toolchain and many packages the program never uses.

- **Pick the smallest base the program runs on.** A static binary runs on
  a distroless `static` image, or on `scratch`. An interpreted program runs
  on a `-slim` official image or a distroless language image.
- Distroless images have no shell and no package manager, so a compromised
  process has nothing to run. The program must then provide its own
  health check, as the example does.
- Alpine uses musl instead of glibc. Programs and prebuilt packages linked
  against glibc may fail or behave differently, so test on the base you
  ship.

### Package-manager hygiene

Package managers leave caches behind, install recommended extras and pick
whatever version is newest on the day of the build.

- **Update and install in the same `RUN`.** A separate `apt-get update`
  layer is cached, so a later install uses a stale index and fails, or
  installs old packages (Trivy's DS-0017).
- Install with `--no-install-recommends` (DL3015), pin each version
  (DL3008), and delete the package lists in the same `RUN` (DL3009). For
  pip, use `--no-cache-dir` (DL3042) and a lock file; for apk, `--no-cache`
  (DL3019).
- When Debian publishes a newer version, the pinned one leaves the mirror
  and the build fails. Bump the pin then, as a reviewed change.
- A Debian-based runtime stage that installs packages and creates its user
  in one step:

  ```dockerfile
  RUN <<EOT
  set -eu
  apt-get update
  apt-get install -y --no-install-recommends \
      ca-certificates=20250419+deb13u1 \
      tini=0.19.0-3+b8
  rm -rf /var/lib/apt/lists/*
  groupadd --system --gid 10001 worker
  useradd --system --uid 10001 --gid worker --no-log-init \
      --no-create-home --shell /usr/sbin/nologin worker
  install --directory --owner=worker --group=worker --mode=0700 /var/lib/worker
  EOT

  COPY --chmod=0755 worker.sh /usr/local/bin/worker
  USER 10001:10001
  ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/worker"]
  ```

- `--no-log-init` stops `useradd` writing a large, sparse log file for a
  high UID (DL3046).

### ADD instead of COPY

`ADD` unpacks local archives and downloads URLs, so the same instruction
does different things depending on the file name.

- **Use `COPY` for local files** (DL3020, Trivy's DS-0005).
- Use `ADD` only to download, and always with a checksum:
  `ADD --checksum=sha256:<digest> <url> <dest>`. The build fails if the file
  changes. The Opengrep rule `dockerfile-add-url-without-checksum` flags a
  remote `ADD` without one.

### Piping a download into a shell

`RUN curl -fsSL https://example.com/install.sh | sh` runs whatever the
server returns that day, with root in the build, and nothing records what
it was.

- Install from the distribution's packages, with a pinned version.
- Or download a release file with `ADD --checksum` and unpack it in a build
  stage.
- Or copy the tool from its official image, pinned by digest:
  `COPY --from=<image>@sha256:<digest> <path> <dest>`.
- The Opengrep rule `dockerfile-no-pipe-to-shell` flags the pipe, and
  hadolint's DL4006 flags a pipe without `pipefail`.

### Shell-form CMD and ENTRYPOINT

`CMD python app.py` runs as `/bin/sh -c "python app.py"`. The shell is
process 1 and doesn't pass on signals, so `docker stop` waits 10 seconds
and then kills the program, mid-request, with exit code 137.

- **Use exec form:** `ENTRYPOINT ["/usr/local/bin/hello"]`. The build check
  `JSONArgsRecommended` and hadolint's DL3025 flag the shell form.
- **Exec form isn't enough on its own.** The kernel gives process 1 no
  default signal actions, so a program that doesn't install a `SIGTERM`
  handler ignores it, and is killed after the timeout too.
- **Handle `SIGTERM` in the program:** stop accepting work, finish what's in
  flight, and exit 0 within the stop timeout. The example's service drains
  its connections and exits in well under a second.
- **When the program can't, run it under an init.** `docker run --init`, or
  tini as the entrypoint as in the
  [Debian example](#package-manager-hygiene), forwards signals and reaps
  zombie child processes. Use one for any image that runs a shell script or
  starts child processes.
- An entrypoint script ends with `exec "$@"` or `exec <program>`, so the
  program replaces the shell instead of running under it.
- Set `STOPSIGNAL` only when the program shuts down gracefully on a signal
  other than `SIGTERM`.
- The [image test](tools.md#testing) stops the container and fails unless
  it exits 0 within the time the spec allows.

### No health check

Without `HEALTHCHECK`, Docker reports a container as running even when the
program has hung or lost its database.

- **Add a `HEALTHCHECK` in exec form** that asks the program itself whether
  it's healthy. In an image with no shell or curl, the program's own binary
  does the probe, as the example's `-healthcheck` flag does.
- Set `--start-period` for slow starts, and `--start-interval` (Engine
  25.0) to check often while starting, so the container turns healthy in
  seconds rather than after the first 30-second interval.
- Orchestrators such as Kubernetes define their own probes. Point them at
  the same endpoint.
- Trivy's DS-0026 flags a missing `HEALTHCHECK`. hadolint's DL3057 would
  too, but flags every build stage, so it's off.

### Configuration baked into the image

`ENV DATABASE_URL=postgres://prod-db/...` or a copied `config.prod.yaml`
builds a different image for each environment. The image you tested is then
not the one you ship.

- **Read configuration from the environment or mounted files when the
  container starts.** Build one image and promote it unchanged.
- Use `ENV` only for defaults that hold everywhere, such as a port.
- Validate the configuration at startup and exit non-zero on a bad value,
  so a broken deployment fails at once instead of on the first request.

### Unrepeatable builds

Building the same commit twice gives different images: base tags have
moved, packages have new versions, and every file and history entry carries
the build's timestamp. Nobody can check that an image came from the source
it claims.

- Pin every input: base images and the frontend by digest, packages by
  version, and dependencies in lock files.
- Don't run `apt-get upgrade` in the Dockerfile. Rebuild on a newer base
  digest instead, so the result depends on the pins, not the day.
- **Set `SOURCE_DATE_EPOCH` to the commit's time, and export with
  `rewrite-timestamp=true`.** BuildKit then uses it for every timestamp in
  the image, so two builds of the same commit give the same image:

  ```sh
  export SOURCE_DATE_EPOCH="$(git log -1 --format=%ct)"
  docker build \
    --output type=image,name=registry.example.com/hello:1.4.2,push=true,unpack=false,rewrite-timestamp=true \
    .
  ```

- `unpack=false` is needed with Docker's default builder, which otherwise
  rejects `rewrite-timestamp`.
- The provenance attestation that BuildKit attaches by default records
  when the build ran, so the pushed index still gets a new digest each
  time; the image manifest inside it doesn't change. Add
  `--provenance=false` when the pushed digest itself must match.
- The [reproducibility check](tools.md#reproducibility) builds twice and
  compares.

### Moving tags

Pushing every build as `latest`, or re-pushing `1.4`, means nobody can tell
which image is running, and a rollback can pull a different image from the
one that ran before.

- **Treat each tag as a release that never changes:** tag with the version,
  `1.4.2`, and the commit, such as `git-3f9c2ab`. Never push the same tag
  twice.
- **Deploy by digest**, `registry.example.com/hello@sha256:...`, so what runs
  is exactly what was tested.
- Turn on tag immutability in the registry where it has the setting.

### Wrong file ownership

Files that `COPY` adds belong to root, which is right for code: the
program's user can run it but not change it. The usual fix for a
permission error, `RUN chown -R app /app`, lets a compromised process
rewrite its own code, and copies every file into a new layer.

- **Keep code and config owned by root and not writable by the runtime
  user.** Set modes as files are copied: `COPY --chmod=0755`.
- Give the runtime user only the directories it writes to, such as
  `/var/lib/worker` in the [Debian example](#package-manager-hygiene), and
  give them `0700`.
- With `--read-only`, mount a volume or a tmpfs on each directory the
  program writes to.
- The [structure test](tools.md#testing) checks the owner and mode of the
  files that matter.

### Several concerns in one container

A container that runs the web server, a database and cron under
supervisord can't be scaled, restarted or updated one part at a time, and
one part's crash leaves the others running in a broken whole.

- **Run one program per container,** and connect containers over the
  network or shared volumes.
- Write logs to stdout and stderr, where `docker logs` and log collectors
  read them, not to files inside the container.

## The principles in Docker

How the [programming principles](../../../principles.md) apply to images:

- **Least authority:** a non-root numeric `USER`; `--cap-drop ALL`,
  `--security-opt no-new-privileges` and `--read-only` at run time; a base
  image with no shell; secrets mounted only into the `RUN` that needs them;
  an allowlist `.dockerignore`; ports published on localhost unless they
  must be public.
- **Single source of truth:** each version pinned once, in the `FROM` line
  or the lock file; the version and commit labels passed in from git; one
  image for every environment, with configuration from the environment.
- **Immutability:** a tag never moves once pushed, deployments name a
  digest, the root file system is read-only, and a container is replaced,
  never patched with `docker exec`.
- **Fail fast:** `check=error=true`; `set -eu` in heredocs and `pipefail`
  for pipes; `required=true` on secret mounts; checksums on downloads; a
  `HEALTHCHECK`; and a program that validates its configuration at startup.
- **Separation of concerns:** build stages apart from the runtime stage,
  one concern per container, and configuration apart from the image.
- **KISS and YAGNI:** one Dockerfile per image, without build arguments
  that switch between environments; no shared base image or `ONBUILD`
  triggers until several images need them; the plainest base that works.

## Writing the spec

A spec states what the image must do in terms a test can check. "Small and
secure" can't be checked; "under 20 MB and runs as UID 65532" can. For the
example service:

| Requirement | Checked by |
| --- | --- |
| Runs as UID 65532 and GID 65532, never root | Structure test (`user`), image test (UID of every process) |
| Exposes only port 8080/tcp | Structure test (`exposedPorts`) |
| Starts with `--read-only`, `--cap-drop ALL` and `no-new-privileges` | Image test (runs it that way) |
| Reports healthy within 10 seconds of starting | Image test |
| Exits 0 within 5 seconds of `SIGTERM` | Image test (`docker stop --timeout 5`) |
| Is at most 20 MB, as `docker image inspect` reports it | Image test |
| Contains no shell, and its binary is owned by root and not writable by the service | Structure test (`fileExistenceTests`) |
| Has no known vulnerability with a fixed version | `trivy image` |
| Carries the source URL and commit in OCI labels | hadolint label schema, structure test |
| Builds byte for byte the same twice from the same commit | Reproducibility check |

Write the checks before the Dockerfile, as [tools.md](tools.md#testing)
describes, so each requirement fails first and passes once the image meets
it.

## Spikes

A spike builds and runs images locally, under a throwaway name such as
`spike/hello:dev`. It never pushes to a shared registry, and never reuses a
release tag, which would overwrite a real release.

## A complete example

A small Go web service. The Go program answers on port 8080, handles
`SIGTERM` by draining its connections with `http.Server.Shutdown`, and has a
`-healthcheck` flag that requests `/healthz` and exits 0 or 1. The image
is 3.4 MB compressed, which is what `docker image inspect` reports with the
containerd image store, and its layers unpack to about 12 MB.

```dockerfile
# syntax=docker/dockerfile:1.28.0@sha256:bb22d9815c728170f72750f4e5b0d672e06176142e1d602c7e66c050100b7e5b
# check=error=true

# The hello service: a static Go binary on a distroless base, run as a
# non-root user with no shell or package manager in the image.

FROM golang:1.27.3-alpine3.24@sha256:fa3d596898d9f126af7c01d14ee7597bab3f39cccf392ef36b69fe77cd681f18 AS build
WORKDIR /src
COPY go.mod ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download
COPY . ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/hello .

FROM gcr.io/distroless/static-debian13:nonroot@sha256:25ac8f0c3b2334a9eb05452266bd4697864a8c8ef0ef71e5e6480d7f92868329 AS runtime
COPY --from=build /out/hello /usr/local/bin/hello
USER 65532:65532
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --start-interval=1s \
    CMD ["/usr/local/bin/hello", "-healthcheck"]
ENTRYPOINT ["/usr/local/bin/hello"]

ARG VERSION=0.0.0-dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="hello" \
    org.opencontainers.image.description="Says hello over HTTP" \
    org.opencontainers.image.source="https://example.com/hello" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.revision="${REVISION}"
```

- Both base images are pinned by digest, and the build runs in its own
  stage. The runtime stage gets one file from it.
- `CGO_ENABLED=0` builds a static binary, which needs no C library, so it
  runs on distroless `static`. `-trimpath` keeps the build machine's paths
  out of the binary, so builds on different machines match.
- The binary keeps the owner and mode the build gave it: root, `0755`.
- The module has no dependencies, so it has no `go.sum` yet. A module with
  dependencies copies `go.sum` with `go.mod`.
- Run it with the least authority it needs:

  ```sh
  docker run --rm --read-only --cap-drop ALL \
    --security-opt no-new-privileges -p 127.0.0.1:8080:8080 hello:dev
  ```

## Sources

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Building best practices](https://docs.docker.com/build/building/best-practices/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Build secrets](https://docs.docker.com/build/building/secrets/)
- [Build context and .dockerignore](https://docs.docker.com/build/concepts/context/)
- [Build checks](https://docs.docker.com/reference/build-checks/)
- [Reproducible builds with BuildKit](https://github.com/moby/buildkit/blob/master/docs/build-repro.md)
- [docker container run](https://docs.docker.com/reference/cli/docker/container/run/)
- [Port publishing](https://docs.docker.com/engine/network/port-publishing/)
- [Distroless images](https://github.com/GoogleContainerTools/distroless)
- [Trivy advisory GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
