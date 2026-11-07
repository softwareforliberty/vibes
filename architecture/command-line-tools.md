# Command-Line Tool Architecture

How to structure a command-line tool, in any language. Read the
[rules for all software](README.md) first: a core of logic with thin edges,
dependencies pointing inward, and one owner for each piece of state. This
guide builds on them.

A command-line tool runs once: it reads its arguments, environment and
input, does its work, writes its output and exits with a status. It's used
by people at a terminal and by scripts, pipelines and other programs, and
must serve both. Its natural shape is a parser at one edge that turns the
command line into typed settings, a core of plain functions, and output and
an exit status at the other edge.

A tool built on its own library also follows the
[library guide](libraries.md) for that library. A long-running background
service follows the [system services](os-components.md#system-services)
rules.

## Scale the structure to the task

- **A small tool with one job:** a `main` that parses the arguments, calls
  one core function, writes the result and exits.
- **A tool with subcommands, configuration files or long-running work:**
  everything in this guide.

At every size, keep the argument parser, the terminal and `exit` out of the
core, so it can be tested as plain functions and reused as a library.

## The layers

```text
arguments, environment,  ─▶ entry point ─▶ settings ─▶ command ─▶ core
config files                                              │
                                                          ▼
standard output and error, exit status ◀──────────── output
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Entry point | Parses arguments, resolves configuration, wires the parts and turns the result into an exit status | Settings, commands, output | The core's internals |
| Settings | The typed configuration for one run | Nothing | The argument parser, the environment |
| Command | One subcommand: calls the core and passes its result to output | Core, settings, output | The argument parser, other commands |
| Core | The tool's logic, as plain functions | Its own interfaces for files, the network and the clock | Arguments, the terminal, standard streams, `exit` |
| Output | Formats results for people or programs, and writes them | Result types, the streams it's given | The core's internals |

### Entry point

The entry point is the only code that knows about the command line. It:

1. parses the arguments with the language's standard parser or a common
   library, which also generates `--help`;
2. resolves configuration from every source into settings (see
   [Configuration](#configuration));
3. builds the command with the settings, the streams and the core's
   dependencies;
4. runs it, and turns its result or error into a message on standard error
   and an exit status.

It's the only place that calls `exit`. `--help` and `--version` write to
standard output and exit with success. A usage error prints a short usage
line and the error to standard error, and exits with a usage status.

### Settings

Settings are a plain, validated value: paths, limits, flags as booleans,
choices as enums. They hold no parser types, so a command can be called from
a test, or from another program, by building settings directly.

### Commands

Each subcommand is its own module, with its own settings type for its own
flags. One table registers them all, so adding a subcommand means adding a
module and a line. A command never calls another command: logic both need
belongs in the core.

### Core

The core takes values and returns results or errors. It reads input from a
stream it's given, or through its own interface for files, so a test can
pass data in memory. It never prints, prompts or exits.

### Output

The output layer turns results into text. It decides, once at startup,
whether the stream is a terminal, whether to use colour and which format to
write. Each format has its own formatter, built from the same result values,
so formats can't drift apart.

## Standard streams

- **Data goes to standard output,** and nothing else does, so a pipe gets
  only the data.
- **Everything else goes to standard error:** errors, warnings, progress
  and prompts.
- **`-` as a file name means standard input or output,** so the tool works
  in a pipeline.
- **Check write errors, and flush before exiting.** A full disk must be an
  error, not a silent truncation.
- **A closed pipe ends the run quietly,** such as when the output is piped
  into `head`, without an error message or a stack trace.

## Exit status

The exit status is part of the interface: scripts branch on it.

- **0 for success,** and non-zero for every failure, even a partial one.
- **Separate usage errors from failures.** Many tools follow the shell's
  builtins, which use 2 for incorrect usage, and use 1 for other failures.
- **Give a distinct status only to failures a script would handle
  differently,** such as "not found" for a lookup, and document each one.
  Never change a documented status.
- **Interrupted by a signal,** exit with 128 plus the signal number, which
  is what a shell reports for a process the signal killed: 130 for Ctrl-C.

## Machine-readable output

- **Offer a machine format,** such as `--json`, beside the human one.
  Human output may change in any release, and scripts must never parse it.
- **The machine format is a stable interface,** versioned like a library's:
  fields can be added, but removing or renaming one is a breaking change.
- **Stream records as JSON Lines** when output is long or unbounded, so a
  consumer can start before the tool finishes.
- **Errors stay on standard error,** and the exit status means the same in
  every format.

## Configuration

- **One place resolves configuration,** in a fixed order where each source
  overrides the ones after it: flags, then environment variables, then
  configuration files, then defaults. Where there are several files, a
  project's file overrides the user's, which overrides the system's.
- **Name environment variables after the tool,** such as `MYTOOL_TOKEN`,
  and follow the platform's conventions for where files live, such as the
  XDG base directories on Linux.
- **Validate everything before doing any work,** so a bad setting fails at
  once with a message that names its source.
- **Read secrets from a file, the environment or a credential store,**
  never from a flag, because a process's arguments can be visible to other
  users, and end up in shell history.

## Streaming large input

- **Process input as a stream,** record by record, with memory bounded by
  the size of a record, not the size of the input.
- **Write output as it's produced,** so a pipeline's next stage can start,
  and a consumer that stops early doesn't wait for the whole run.
- **Read the whole input only when the job needs it,** such as for sorting,
  and say so in the help.

## Signals and interruption

- **The signal handler only records the signal,** and the work loop checks
  it, or the core gets a cancellation token or context it checks between
  steps.
- **On Ctrl-C, stop promptly,** clean up within a time limit and exit. A
  second Ctrl-C skips the clean-up.
- **Never leave a half-written result.** Write output files to a temporary
  file in the same directory and rename it into place when it's complete,
  so an interrupted run leaves the old file or none.
- **Make runs safe to repeat** where possible, so a script can retry after
  an interruption.

## Terminals and prompts

- **Prompt only when standard input is a terminal.** Every prompt has a
  flag that answers it, such as `--yes` or a value, and `--no-input` turns
  prompts off, so the tool works in scripts and CI. When input isn't a
  terminal and a needed value is missing, fail with a message naming the
  flag.
- **Use colour only when it helps:** when the stream is a terminal, `TERM`
  isn't `dumb`, and the [`NO_COLOR`](https://no-color.org/) variable isn't
  set to a non-empty value. A flag such as `--color=auto|always|never`
  overrides the detection.
- **Show progress only on a terminal,** on standard error, and never in
  machine output.
- **Check each stream on its own.** Standard output may be piped while
  standard error is still a terminal.

## Layout

```text
src/
├── main         the entry point: parsing, configuration and wiring
├── settings     the settings types
├── commands/    one module per subcommand
├── core/        the logic, with no terminal or process access
└── output/      one formatter per format, and terminal detection
tests/
├── core/        unit tests of the core
└── cli/         end-to-end tests of the built binary
```

## Enforce it

- **Build the core as its own module or library,** without the argument
  parser as a dependency, so it can't reach the command line.
- **Typical rules for architecture tests:** only the entry point imports
  the argument parser or reads the environment; only the entry point calls
  `exit`; the core never writes to standard output or error.

## Testing

| Part | Test with |
| --- | --- |
| Core | Unit tests, with input and output in memory |
| Commands | Unit tests that build settings directly, and capture the streams |
| Output | Golden files for each format, including `--help` |
| The whole tool | End-to-end tests that run the built binary |

End-to-end tests run the real binary with arguments, standard input,
environment variables and a temporary directory, and check standard output,
standard error and the exit status separately. They cover:

- each exit status, including usage errors;
- output when the streams aren't terminals, with no colour, prompts or
  progress;
- `--json` output against its schema;
- configuration precedence, with the same setting in more than one source;
- an interrupted run, which leaves no partial output.
