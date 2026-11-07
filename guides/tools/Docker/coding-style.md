# Docker Coding Style

A general-purpose style for Dockerfiles and `.dockerignore` files, built
with BuildKit. It builds on the
[Dockerfile reference](https://docs.docker.com/reference/dockerfile/),
Docker's [build checks](https://docs.docker.com/build/checks/) and
[hadolint](https://github.com/hadolint/hadolint) (see [Sources](#sources)).

This guide covers how Dockerfiles look. For how to build images well (the
traps, base images, users, secrets, signals and how to write the spec), see
[idioms.md](idioms.md).

The tools that check Dockerfiles are listed in [tools.md](tools.md).

## Baseline

- **Docker Engine 25.0 or later, with Buildx 0.15 or later.** BuildKit is
  the default builder from Engine 23.0, Engine 25.0 adds the
  `HEALTHCHECK --start-interval` option, and Buildx 0.15 adds
  `docker build --check`.
- **Dockerfile syntax 1, with frontend 1.10 or later.** Version 1.8 added
  the `check` directive and 1.10 added `env=` on secret mounts. Declare the
  frontend on the first line, and pin it by digest like any other image:

  ```dockerfile
  # syntax=docker/dockerfile:1.28.0@sha256:bb22d9815c728170f72750f4e5b0d672e06176142e1d602c7e66c050100b7e5b
  ```

  Docker's documentation suggests `docker/dockerfile:1`, which pulls the
  newest 1.x frontend on every build. The frontend parses and runs the
  build, and sees its secrets, so a pinned one keeps builds repeatable and
  stops a moved tag from changing them. Update the pin like a base image.
- **Buildah 1.43** builds this guide's examples too, and so does
  `podman build`, which uses it. It doesn't run the build checks, and it
  drops `HEALTHCHECK` unless it's given `--format docker`, so in a
  Buildah-only project hadolint is the only lint gate.

## Files

- **Name the main Dockerfile `Dockerfile`,** at the root of its build
  context. Docker finds it without `-f`.
- **Name any other Dockerfile `<purpose>.Dockerfile`,** such as
  `worker.Dockerfile`, so editors, dockerfmt, Trivy and jscpd recognise it.
  Its own ignore file, if it needs one, is `worker.Dockerfile.dockerignore`.
- **Use `Containerfile` only in a project that builds with Podman or
  Buildah alone.** It's their default name, but Docker reads it only when
  given `-f Containerfile`.
- **Every build context has a `.dockerignore`** (see
  [Missing .dockerignore](idioms.md#missing-dockerignore)).
- **Shell scripts that `RUN` calls live in their own files,** and follow the
  [SH](../../languages/SH/coding-style.md) or
  [Bash](../../languages/BASH/coding-style.md) guide.

## Layout

### Directives and header

Start every Dockerfile with the `syntax` and `check` directives, then a
blank line and a comment that says what the image is for:

```dockerfile
# syntax=docker/dockerfile:1.28.0@sha256:bb22d9815c728170f72750f4e5b0d672e06176142e1d602c7e66c050100b7e5b
# check=error=true

# The hello service: a static Go binary on a distroless base, run as a
# non-root user with no shell or package manager in the image.
```

- **Directives must come first.** BuildKit stops looking for them at the
  first comment, blank line or instruction, and silently treats a
  directive after that as a comment.
- `check=error=true` makes a build-check warning fail the build, so a
  plain `docker build` enforces the [build checks](tools.md#linting).

### Order of stages and instructions

- **Order stages from build to runtime.** The last stage is what a plain
  `docker build` produces, so it's the image you ship.
- **Within a stage, put what changes least first.** A change to one
  instruction rebuilds it and everything after it, so a frequent change
  near the top throws away the cache for the whole stage.
- In a build stage: `FROM`, `WORKDIR`, then `COPY` the dependency manifests,
  `RUN` the dependency download, `COPY` the source and `RUN` the build.
- In the final stage: `FROM`, then `RUN` for system packages and users,
  `COPY --from` for the build's output, `USER`, `EXPOSE`, `HEALTHCHECK`,
  `ENTRYPOINT` and `CMD`.
- **Put `ARG` and `LABEL` for per-build values, such as the version and
  commit, last.** A changed `ARG` reruns every `RUN` after its
  declaration, even one that doesn't use it, so declared last it reruns
  nothing.
- Separate stages with one blank line. Inside a stage, leave a blank line
  only after a heredoc's closing delimiter: hadolint 2.15.1 fails to parse
  an instruction that directly follows one.

### Case

- **Write instructions in uppercase,** and `AS` in `FROM ... AS name` too.
  Uppercase is Docker's convention, and the build checks
  `ConsistentInstructionCasing` and `FromAsCasing` reject mixed case.
- **Name stages in lowercase, by their job:** `build`, `test`, `runtime`.
  `StageNameCasing` rejects uppercase, and `ReservedStageName` and hadolint's
  DL3063 reject reserved words such as `scratch`.
- **Name `ARG` and `ENV` variables in `UPPER_SNAKE_CASE`.** They're
  environment variables, which is the convention for them.

### Line length and continuations

- **80 columns** is the limit. A digest-pinned image reference or a URL
  can't be split, and may run longer.
- Break a long instruction with a trailing `\`, and indent each
  continuation line by **4 spaces**, the indent dockerfmt uses.
- Put `&&` at the start of a continuation line, not the end of the line
  before, so each command starts its own line.
- **List packages one per line, sorted,** so a diff shows exactly which
  package changed, and a duplicate stands out.
- Never leave an empty continuation line. `NoEmptyContinuation` warns that
  it will become an error.
- Write `ENV` and `LABEL` as `key=value` pairs. In the old `ENV KEY value`
  form, everything after the key becomes the value, spaces and `=` signs
  included. `LegacyKeyValueFormat` rejects it.

### Exec form

Write `CMD`, `ENTRYPOINT`, `SHELL` and the `HEALTHCHECK` command in exec
form, as a JSON array with double quotes:
`ENTRYPOINT ["/usr/local/bin/hello"]`. The shell form runs the command
through `/bin/sh -c`, which stops it receiving signals (see
[Shell-form CMD](idioms.md#shell-form-cmd-and-entrypoint)). Single quotes
aren't JSON, so Docker runs the whole line, brackets and all, as a shell
command.

## RUN steps

`RUN` commands are shell scripts. They run in `/bin/sh` unless `SHELL`
changes it, so they follow the
[SH guide](../../languages/SH/coding-style.md), or the
[Bash guide](../../languages/BASH/coding-style.md) where `SHELL` selects
Bash. hadolint runs ShellCheck on every `RUN`.

### One step per RUN

- **Give each `RUN` one job,** such as installing packages or building the
  program. Every `RUN` is a layer, and hadolint's DL3059 flags consecutive
  ones that could be merged.
- Split a step only where the cache needs it, such as downloading
  dependencies before the source is copied in.

### Heredocs

When a step needs more than two or three commands, write it as a heredoc
instead of a chain of `&& \`:

```dockerfile
RUN <<EOT
set -eu
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates=20250419+deb13u1 \
    tini=0.19.0-3+b8
rm -rf /var/lib/apt/lists/*
EOT
```

- **Start every heredoc with `set -eu`.** A heredoc runs as one script, and
  without `-e` a failing line doesn't stop it: the build carries on and
  succeeds. The Opengrep rule `dockerfile-heredoc-without-set-e` flags a
  heredoc that doesn't.
- Use `EOT` as the delimiter, so it can't clash with an `EOF` inside the
  script.
- Leave a blank line after the closing delimiter (see
  [Order](#order-of-stages-and-instructions)).

### Long scripts and pipes

- **Move a step past about 10 lines into a script file,** `COPY` it in and
  run it. A file gets the shell guide's formatting, linting and tests;
  inline shell gets only hadolint's ShellCheck pass.
- **Set `pipefail` before any `RUN` with a pipe.** `/bin/sh` reports only
  the last command of a pipeline, so `curl ... | tar -x` passes when the
  download fails. In an image with Bash, set
  `SHELL ["/bin/bash", "-o", "pipefail", "-c"]` first. hadolint's DL4006
  flags a pipe without it.

## Labels

Describe the image with the
[OCI annotation](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
keys, in one `LABEL` instruction with one key per line:

```dockerfile
ARG VERSION=0.0.0-dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="hello" \
    org.opencontainers.image.description="Says hello over HTTP" \
    org.opencontainers.image.source="https://example.com/hello" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.revision="${REVISION}"
```

- `title`, `source`, `licenses`, `version` and `revision` are required.
  The [`.hadolint.yaml`](.hadolint.yaml) label schema enforces them, and
  checks that `source` is a URL and `licenses` an SPDX identifier.
- CI passes the version and commit as build arguments, such as
  `--build-arg REVISION="$(git rev-parse HEAD)"`, so the Dockerfile never
  changes per release. The defaults mark a local build.
- Don't set a `created` label. It changes on every build, so the image can
  never be [reproduced](idioms.md#unrepeatable-builds).
- Use `org.opencontainers.image.authors` instead of `MAINTAINER`, which is
  deprecated (`MaintainerDeprecated`, DL4000).

## Comments

- **Put comments on their own lines.** A `#` after an instruction isn't a
  comment: it's passed on as arguments, so `EXPOSE 8080 # http` fails the
  build.
- Comments explain **why**: why a package is needed, why a version is
  pinned, or why a rule is ignored. `# install curl` above an install of
  curl says nothing.
- Suppress a hadolint rule only on the instruction that needs it, with
  `# hadolint ignore=DL3008` on the line above and a comment saying why.
  Don't skip build checks with `check=skip`, which applies to the whole
  file.

## .dockerignore

- Write one pattern per line, with comments only in column 1. The last
  pattern that matches a path decides whether it's sent.
- Write it as an allowlist: `*` first, then a `!` line for each path the
  build copies. See the [template](.dockerignore).

## Formatting

dockerfmt formats Dockerfiles, and reads `indent_size` and
`insert_final_newline` from the [`.editorconfig`](.editorconfig). Where this
guide and dockerfmt's output could disagree on layout, dockerfmt wins. It
leaves alone a `RUN` that uses `;` or `{ }` grouping, and it doesn't fix
`as` to `AS`; the build checks catch that. See
[tools.md](tools.md#formatting).

## Sources

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Build checks](https://docs.docker.com/build/checks/) and the
  [list of checks](https://docs.docker.com/reference/build-checks/)
- [Building best practices](https://docs.docker.com/build/building/best-practices/)
- [Build context and .dockerignore](https://docs.docker.com/build/concepts/context/)
- [OCI image annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
- [hadolint rules](https://github.com/hadolint/hadolint#rules)
- [dockerfmt](https://github.com/reteps/dockerfmt)
- [Buildah](https://buildah.io/)
