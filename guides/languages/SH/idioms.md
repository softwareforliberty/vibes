# POSIX sh Idioms and Principles

How to write POSIX `sh` well. [coding-style.md](coding-style.md) covers how
code looks. This guide covers how it's designed: the idioms and principles that
keep scripts correct, safe and maintainable. Every example follows the style
guide.

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
- **Stay within POSIX.** A script that says `#!/bin/sh` must run under every
  POSIX shell, not just the one on the author's machine.

## Script skeleton

```sh
#!/bin/sh
#
# Archive a directory into a timestamped tarball.

set -eu

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
  if [ "$#" -ne 1 ]; then
    usage
    exit 2
  fi

  src="$1"
  [ -d "${src}" ] || die "not a directory: ${src}"

  stamp="$(date +%Y%m%d%H%M%S)"
  tar -czf "${ARCHIVE_ROOT}/${src##*/}-${stamp}.tar.gz" -- "${src}" \
    || die "archiving failed: ${src}"
}

main "$@"
```

## Error handling

### Strict mode

Start every executable with `set -eu`, straight after the header comment:

- `-e` exits when a command fails.
- `-u` makes expanding an unset variable an error, which catches typos.

`set -e` is a safety net, not error handling. It's ignored for a command in an
`if`, `while` or `until` condition, for any command but the last in an `&&` or
`||` list, and for everything inside a function called from those places.
Check the commands that matter explicitly.

### Pipelines

A pipeline's status is the status of its **last** command, so an earlier
stage can fail unnoticed. Don't rely on `set -o pipefail`: it was only
standardised in POSIX.1-2024, and older shells reject it. When an early
stage's failure matters, write its output to a temporary file and check its
status before the next step:

```sh
list_hosts >"${tmp_dir}/hosts" || die "could not list hosts"
sort -- "${tmp_dir}/hosts"
```

### Checking commands

- Test a command's status directly, and report what failed:

  ```sh
  if ! mv -- "${tmp_file}" "${dest}"; then
    die "could not move file into place: ${dest}"
  fi
  ```

- Use `cmd || die "..."` for one-line checks.
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

```sh
tmp_dir="$(mktemp -d)"
trap 'rm -rf -- "${tmp_dir}"' EXIT
trap 'exit 1' HUP INT TERM
```

The trap runs when the script exits, after `main` has returned. Anything it
uses must still be set at that point.

`mktemp` isn't in POSIX.1-2017, but every mainstream system provides
`mktemp -d`. Use it rather than inventing temporary names.

## Quoting and word splitting

- **Quote every expansion** unless you specifically want it split and
  globbed. That's almost never the case.
- **Build commands in the positional parameters, not strings.** They're the
  one list POSIX sh has, and `"$@"` keeps each argument intact, spaces
  included. Inside a function, `set --` replaces only that function's
  arguments:

  ```sh
  sync_dir() {
    _sync_dir_src="$1"
    _sync_dir_dst="$2"
    set -- --archive --delete
    if [ "${dry_run}" = true ]; then
      set -- "$@" --dry-run
    fi
    rsync "$@" -- "${_sync_dir_src}/" "${_sync_dir_dst}/"
  }
  ```

- **End options with `--`** before passing file names or other operands to a
  command, so a name that starts with `-` isn't read as an option.
- **Glob with `./*`, not `*`**, for the same reason.
- A glob that matches nothing expands to itself. Check each match exists
  before using it:

  ```sh
  for file in ./*.log; do
    [ -e "${file}" ] || continue
    gzip -- "${file}"
  done
  ```

- **Never parse the output of `ls`.** File names can contain spaces and
  newlines. Use a glob, or `find`.
- **Guard destructive commands against empty variables.** `${var:?}` stops the
  script if `var` is unset or empty, so this can never become `rm -rf /*`:

  ```sh
  rm -rf -- "${build_dir:?}"/*
  ```

## Reading input

- Read lines with `IFS= read -r`. `IFS=` keeps leading and trailing
  whitespace, and `-r` keeps backslashes:

  ```sh
  while IFS= read -r line; do
    process_line "${line}"
  done <"${input}"
  ```

- **Don't pipe into a `while` loop** whose variables you need afterwards. Each
  side of a pipeline may run in a subshell, so its changes can be lost. Write
  the command's output to a temporary file and redirect the loop's input from
  it, as above.
- Let `find` run the command on the files it finds, so any character in a
  name is safe:

  ```sh
  find "${src}" -type f -exec chmod 0644 -- {} +
  ```

- Parse options with `getopts`, and print a usage message for unknown ones.
- Quote a here-document's delimiter (`<<'EOF'`) when its text must be used as
  is, with no expansion.

## Commands and builtins

- **Prefer parameter expansion to external programs.** It's faster and has no
  quoting surprises: `${path##*/}` instead of `basename`, `${path%/*}` instead
  of `dirname`, and `${file%.*}` to drop an extension.
- **Use `printf` instead of `echo`** for anything other than a fixed string.
  `echo`'s handling of options like `-n` and `-e`, and of backslashes, varies
  between shells and settings.
- **Never use `eval`.** It runs data as code, which makes quoting bugs into
  injection bugs. The positional parameters, `case` and parameter expansion
  cover the cases people reach for `eval` to solve.
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

- **Test scripts under dash** as well as your usual shell. dash implements
  little beyond POSIX, so it catches features other shells quietly accept.
- **Don't use Bash features.** ShellCheck flags them in `sh` scripts. The
  common ones, and what to use instead:

  | Bash feature | POSIX replacement |
  | --- | --- |
  | `[[ ]]` | `[ ]` with quoted operands, or `case` for patterns |
  | `==` in tests | `=` |
  | `(( ))` | `[ ]` with `-eq`, `-lt` and so on, and `$(( ))` for arithmetic |
  | Arrays | The positional parameters (`set --` and `"$@"`) |
  | `local` | Prefixed variable names, or a subshell function body |
  | `function name` | `name()` |
  | `source file` | `. ./file` |
  | `&>file` | `>file 2>&1` |
  | `<<< "${text}"` | `printf '%s\n' "${text}" \| cmd` |
  | `<(cmd)` | A temporary file |
  | `$'...'` | `printf` |
  | `{a,b}` brace expansion | Write each word out |
  | `${var//old/new}` | `sed` |

- **External tools differ between systems.** GNU and BSD versions of `sed`,
  `date`, `stat` and `readlink` take different options. Use only the options
  POSIX defines, or detect the version and branch. Avoid `sed -i`,
  `grep -P` and `readlink -f`, which POSIX doesn't define.
- Set `LC_ALL=C` for commands whose output you parse, so the locale can't
  change their format or sort order.

## Performance

- **Avoid starting processes in loops.** Each command substitution or external
  program costs a fork. Move the work out of the loop, or use a builtin.
- Hand large amounts of data to a tool built for it, like `awk`, `sort` or
  `grep`, instead of looping over it line by line in the shell.
- Measure with `time` before you optimise.

## Sources

- [POSIX.1-2017 Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) and
  [BashFAQ](https://mywiki.wooledge.org/BashFAQ) on Greg's Wiki (most of their
  advice applies to every shell)
