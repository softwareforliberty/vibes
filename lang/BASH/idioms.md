# Bash Idioms and Principles

How to write Bash well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that keep
scripts correct, safe and maintainable. Every example follows the style guide.

## Principles

- **Shell is glue.** Use it to run other programs and move data between them.
  When a script needs complex logic or data structures, or grows past about
  100 lines, rewrite it in a general-purpose language.
- **Fail early and loudly.** Stop at the first unexpected failure, and say
  what went wrong, instead of carrying on with bad state.
- **Quote by default.** Most shell bugs come from unquoted expansions being
  split into words or expanded as globs.
- **Data goes to stdout, messages go to stderr.** A script's output can then
  be piped into another program without its diagnostics mixed in.
- **Make scripts safe to re-run.** A script that's interrupted halfway should
  be able to run again and finish the job, without failing on what it
  already did.
- **Keep scope small.** Use `local` in functions, and make constants
  read-only.

## Script skeleton

```bash
#!/usr/bin/env bash
#
# Archive a directory into a timestamped tarball.

set -euo pipefail

readonly ARCHIVE_ROOT="/var/archives"

err() {
  printf '%s: %s\n' "${0##*/}" "$*" >&2
}

die() {
  err "$@"
  exit 1
}

usage() {
  printf 'usage: %s <directory>\n' "${0##*/}" >&2
}

main() {
  if (($# != 1)); then
    usage
    exit 2
  fi

  local src="$1"
  [[ -d "${src}" ]] || die "not a directory: ${src}"

  local stamp
  stamp="$(date +%Y%m%d%H%M%S)"
  tar -czf "${ARCHIVE_ROOT}/${src##*/}-${stamp}.tar.gz" -- "${src}" \
    || die "archiving failed: ${src}"
}

main "$@"
```

## Error handling

### Strict mode

Start every executable with `set -euo pipefail`, straight after the header
comment:

- `-e` exits when a command fails.
- `-u` makes expanding an unset variable an error, which catches typos.
- `-o pipefail` makes a pipeline fail when **any** stage fails, not just the
  last one.

`set -e` is a safety net, not error handling. It's ignored for a command in an
`if`, `while` or `until` condition, for any command but the last in an `&&` or
`||` list, and for everything inside a function called from those places.
Check the commands that matter explicitly.

### Checking commands

- Test a command's status directly, and report what failed:

  ```bash
  if ! mv -- "${tmp_file}" "${dest}"; then
    die "could not move file into place: ${dest}"
  fi
  ```

- Use `cmd || die "..."` for one-line checks.
- When you need the status of every stage in a pipeline, read `PIPESTATUS`
  straight after it, before any other command replaces it.
- **Report each error once.** A function either prints an error or returns
  it, not both, so one failure doesn't produce a cascade of messages.

### Exit status

- Exit with `0` for success, `1` for a general failure, and `2` for a usage
  error, such as a missing or unknown argument.
- Functions report failure with `return 1` (or another non-zero status), and
  return data on stdout.

### Cleaning up

Remove temporary files with an `EXIT` trap. Make every signal that should
stop the script call `exit` too, because not every shell runs the `EXIT`
trap when it's killed by a signal:

```bash
tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "${tmp_dir}"' EXIT
trap 'exit 1' HUP INT TERM
```

The trap runs when the script exits, after `main` has returned. Anything it
uses must be a global, not a `local` in a function.

## Quoting and word splitting

- **Quote every expansion** unless you specifically want it split and
  globbed. That's almost never the case.
- **Build commands in arrays, not strings.** An array keeps each argument
  intact, spaces included:

  ```bash
  local -a args=(--archive --delete)
  if ((dry_run)); then
    args+=(--dry-run)
  fi
  rsync "${args[@]}" -- "${src}/" "${dst}/"
  ```

- **End options with `--`** before passing file names or other operands to a
  command, so a name that starts with `-` isn't read as an option.
- **Glob with `./*`, not `*`**, for the same reason.
- A glob that matches nothing expands to itself. Check each match exists
  before using it:

  ```bash
  for file in ./*.log; do
    [[ -e "${file}" ]] || continue
    gzip -- "${file}"
  done
  ```

- **Never parse the output of `ls`.** File names can contain spaces and
  newlines. Use a glob, or `find`.
- **Guard destructive commands against empty variables.** `${var:?}` stops the
  script if `var` is unset or empty, so this can never become `rm -rf /*`:

  ```bash
  rm -rf -- "${build_dir:?}"/*
  ```

## Reading input

- Read lines with `IFS= read -r`. `IFS=` keeps leading and trailing
  whitespace, and `-r` keeps backslashes:

  ```bash
  while IFS= read -r line; do
    process_line "${line}"
  done <"${input}"
  ```

- **Don't pipe into a `while` loop** whose variables you need afterwards. Each
  side of a pipeline runs in a subshell, so its changes are lost. Read from a
  process substitution instead, or load the lines into an array:

  ```bash
  mapfile -t hosts < <(list_hosts)
  ```

- Handle file names from `find` with null separators, so any character is
  safe:

  ```bash
  while IFS= read -r -d '' file; do
    check_file "${file}"
  done < <(find "${src}" -type f -print0)
  ```

- Parse options with `getopts`, and print a usage message for unknown ones.
- Quote a here-document's delimiter (`<<'EOF'`) when its text must be used as
  is, with no expansion.

## Commands and builtins

- **Prefer parameter expansion to external programs.** It's faster and has no
  quoting surprises: `${path##*/}` instead of `basename`, `${path%/*}` instead
  of `dirname`, `${file%.*}` to drop an extension, and `${text//old/new}` to
  replace text.
- **Use `printf` instead of `echo`** for anything other than a fixed string.
  `echo`'s handling of options like `-n` and `-e`, and of backslashes, varies
  between shells and settings.
- **Never use `eval`.** It runs data as code, which makes quoting bugs into
  injection bugs. Arrays, `printf -v` and indirect expansion cover the cases
  people reach for `eval` to solve.
- **Use functions, not aliases.** Functions can take arguments, and they
  behave the same in every shell and mode.
- **Check that a program exists with `command -v`**, not `which`.
  `command -v` is defined by POSIX and built into the shell; `which` is
  neither.

## Safety and security

- **Never make a script SUID or SGID.** Shell scripts can't be made safe to
  run with raised privileges. Use `sudo` to run them as another user.
- **Keep secrets off the command line.** Other users can see every process's
  arguments. Pass secrets on stdin, or in a file only the owner can read.
- Set `umask 077` before creating files that hold secrets, so no one else
  can read them.
- **Create temporary files and directories with `mktemp`.** Fixed names in
  `/tmp` can be predicted, and attackers can race to create them first.
- Set `PATH` explicitly in scripts that run with elevated privileges, so they
  can't be tricked into running the wrong program.
- Validate every input before using it, especially in paths passed to `rm`,
  `chmod` or `chown`.

## Portability

- Scripts need Bash 4.4 or later. Check `BASH_VERSINFO` and fail with a clear
  message if a script may meet an older Bash, such as the 3.2 that ships with
  macOS.
- **External tools differ between systems.** GNU and BSD versions of `sed`,
  `date`, `stat` and `readlink` take different options. Use only the options
  POSIX defines, or detect the version and branch.
- Set `LC_ALL=C` for commands whose output you parse, so the locale can't
  change their format or sort order.

## Performance

- **Avoid starting processes in loops.** Each command substitution or external
  program costs a fork. Move the work out of the loop, or use a builtin.
- Hand large amounts of data to a tool built for it, like `awk`, `sort` or
  `grep`, instead of looping over it line by line in the shell.
- Measure with `time` before you optimise.

## Sources

- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [GNU Bash manual](https://www.gnu.org/software/bash/manual/)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) and
  [BashFAQ](https://mywiki.wooledge.org/BashFAQ) on Greg's Wiki
