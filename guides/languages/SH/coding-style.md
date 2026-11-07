# POSIX sh Coding Style

A general-purpose coding style for POSIX `sh` scripts: scripts that run under
any POSIX-conforming shell, such as dash, BusyBox ash, ksh, or Bash in POSIX
mode. It builds on the
[POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
and the
[Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html),
and fills the gaps from ShellCheck and the shell community's pitfall lists
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (error
handling, quoting, safety and other idioms), see [idioms.md](idioms.md).

The tools that check POSIX sh code are listed in [tools.md](tools.md).

## Language baseline

Scripts target the **POSIX.1-2017** shell and utilities. Features added in
POSIX.1-2024, such as `set -o pipefail`, aren't yet available in every shell
in use.

## Files

- Executables start with `#!/bin/sh`. Every mainstream Unix-like system
  installs its POSIX shell there.
- Executables have **no extension**. They're commands, and callers shouldn't
  have to know what language they're written in.
- Libraries end in `.sh`, aren't executable and have no shebang. Their first
  line is `# shellcheck shell=sh`, so ShellCheck knows the dialect.
- File names are lowercase, with underscores between words.
- Lay out every file in this order:
  1. Shebang (executables only)
  2. Header comment
  3. `set -eu` (executables only)
  4. `.` lines that load libraries
  5. Constants
  6. Functions
  7. `main "$@"` (executables only)
- Don't put executable code between functions. A reader should find every
  function together, and every top-level command at the end.

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- Don't use `<<-` here-documents. They only strip leading tabs, and this
  style doesn't indent with tabs.

### Line length

- Keep lines to **80 columns**.
- Write a longer string as a here-document, or with embedded newlines. A
  literal that can't sensibly be split, such as a URL or a path, may run
  longer.

### Whitespace

- No trailing whitespace.
- Don't use more than one blank line in a row.
- Use LF line endings, and end every file with a newline.

### One command per line

- Put each command on its own line. Don't join unrelated commands with `;`.
- Break a long command with a trailing `\`. Indent the continuation lines by
  2 spaces, and give each option or argument group its own line:

  ```sh
  rsync \
    --archive \
    --delete \
    -- "${src}/" "${dst}/"
  ```

### Pipelines and lists

If a pipeline fits on one line, keep it on one line. Otherwise, put each
stage on its own line, start each continuation line with the `|`, and indent
it 2 spaces. Long `&&` and `||` lists follow the same rule:

```sh
grep -v '^#' -- "${config}" | sort

grep -v '^#' -- "${config}" \
  | sed -e 's/[[:space:]]*$//' \
  | sort \
  | uniq -c
```

## Control flow

- Put `; then` and `; do` on the same line as the `if`, `while` or `for`.
  `elif`, `else`, `fi` and `done` go on their own lines, lined up with the
  opening keyword:

  ```sh
  for dir in "$@"; do
    if [ -d "${dir}" ]; then
      clean_dir "${dir}"
    elif [ -e "${dir}" ]; then
      err "not a directory: ${dir}"
    else
      mkdir -p -- "${dir}"
    fi
  done
  ```

- Indent `case` branches 2 spaces, and their commands 2 more. `;;` goes on
  its own line, lined up with the commands. A branch with one short command
  may sit on one line, as `pattern) command ;;`.
- Every `case` has a final `*)` branch, so an unexpected value is handled
  instead of silently ignored:

  ```sh
  case "${mode}" in
    fast) level=1 ;;
    best)
      level=9
      check_space
      ;;
    *)
      err "unknown mode: ${mode}"
      exit 2
      ;;
  esac
  ```

## Spacing

- Put a space inside `[` and `]`, around their operators, and around `|`,
  `&&` and `||`.
- Don't put spaces just inside `$(( ))`. Put one space around its operators:
  `$((count + 1))`.
- Don't put a space between a redirection operator and its target:
  `>"${log}"`, `2>&1`, `<"${input}"`.
- Write a function as `name() {`, with no space before `()` and one space
  before `{`.

## Naming

- Functions and variables are lowercase with underscores: `parse_args`,
  `backup_dir`. The shell's own variables and environment variables are
  uppercase, so lowercase names never clobber them.
- Library functions start with the library's name and `_`, as in
  `log_info`. The prefix shows where a function comes from and avoids
  clashes between libraries.
- Constants and exported variables are `UPPER_SNAKE_CASE`. Declare them at
  the top of the file, make constants read-only, and export variables with
  `export`:

  ```sh
  readonly BACKUP_ROOT="/var/backups"
  export LC_ALL="C"
  ```

- Name loop variables after what they hold: `for host in "$@"`, not
  `for i in ...`.

## Variables and expansions

- **Quote every expansion**: `"${file}"`, `"$(cmd)"`, `"$@"`. An unquoted
  expansion is split on whitespace and expanded as a glob.
- **Brace every variable**: `"${name}"`, not `"$name"`. The braces make the
  end of the name explicit. Special parameters (`$?`, `$#`, `$@`, `$*`, `$$`,
  `$!`, `$-`) and positional parameters `$0` to `$9` are the exception, and
  are written without braces.
- Use `$(command)` for command substitution, never backticks. It nests
  without escaping, and it's easier to read.
- Use `"$@"` to pass arguments on, so each one stays a separate word. Use
  `"$*"` only to join them into one string.
- Do arithmetic with `$(( ))`. Refer to variables inside it without `$`, and
  assign the result: `count=$((count + 1))`. Never use `let`, `expr` or
  `$[ ]`.
- There are no arrays. Keep a list in the positional parameters with
  `set --`, and expand it with `"$@"`, which expands each element as its own
  word.

### Tests

- Use `[ ]` for tests, and quote every expansion inside it. Unlike Bash's
  `[[ ]]`, `[` is an ordinary command, so its operands are split and
  globbed.
- Test for empty and non-empty strings with `-z` and `-n`:
  `[ -n "${name}" ]`, not `[ "${name}" ]`.
- Compare strings with `=`, and numbers with `-eq`, `-ne`, `-lt`, `-le`, `-gt`
  and `-ge`: `if [ "${count}" -gt "${max}" ]; then`. `==` isn't POSIX.
- Combine tests with `&&` and `||` between separate `[ ]` commands. Never use
  `-a` or `-o` inside one: they're ambiguous with some operands, and POSIX
  marks them obsolescent.
- Match patterns with `case`, which is the POSIX way to test a string
  against a glob.

## Functions

- Define functions as `name() {`. Don't use the `function` keyword, which
  isn't POSIX.
- POSIX sh has no local variables. Give a function's own variables a prefix
  of `_` and the function's name, such as `_copy_dst` in `copy()`, so they
  can't clobber the caller's variables. `main` is the exception: its
  variables are the script's globals.
- A function that only returns output and a status, without changing any of
  the caller's variables, may run its body in a subshell, `name() (`. Every
  variable it sets then disappears when it returns.
- A script with at least one function other than `main` puts its top-level
  logic in `main`. The script's last line is `main "$@"`.

## Comments

- Start every comment with `#` and a space.
- Every file has a header comment near the top, after the shebang or the
  ShellCheck directive, that says what the file does:

  ```sh
  #!/bin/sh
  #
  # Back up a directory to a timestamped tarball.
  ```

- Comment every library function, and every function that isn't both short
  and obvious. Describe its behaviour, followed by the sections that apply:
  the globals it uses or changes, its arguments, its output and its return
  status. Leave out sections that don't apply:

  ```sh
  #######################################
  # Copy a file into the backup directory.
  # Globals:
  #   BACKUP_ROOT
  # Arguments:
  #   Path of the file to copy.
  # Outputs:
  #   Writes the backup's path to stdout.
  # Returns:
  #   0 on success, non-zero if the copy failed.
  #######################################
  ```

- Inside a function, comment only what's tricky or surprising, and say
  **why**, not **how**.
- Mark unfinished work as `# TODO(owner): what remains to be done.`, so
  someone can ask the owner about it.

## Sources

- [POSIX.1-2017 Shell Command Language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) on Greg's Wiki
  (most of its pitfalls apply to every shell)
- [shfmt](https://github.com/mvdan/sh)
