# Bash Coding Style

A general-purpose coding style for Bash scripts. It builds on the
[Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html),
and fills the gaps from the Bash manual, ShellCheck and the shell community's
pitfall lists (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (error
handling, quoting, safety and other idioms), see [idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [ShellCheck](https://www.shellcheck.net/) | GPLv3 | Linting: quoting bugs, unsafe constructs and portability problems |
| [shfmt](https://github.com/mvdan/sh) | BSD-3-Clause | Formatting |

### Formatting

shfmt is the formatter. Run it in check mode in CI, and in write mode
locally:

```sh
shfmt -ln bash -i 2 -ci -bn -d .   # show what would change
shfmt -ln bash -i 2 -ci -bn -w .   # rewrite the files
```

- `-i 2` indents with 2 spaces.
- `-ci` indents the branches of a `case`.
- `-bn` lets `|`, `&&` and `||` start a continuation line.
- Given a directory, shfmt also finds scripts with no extension by their
  shebang.

### Linting

Code must pass ShellCheck with **no warnings**. Put this `.shellcheckrc` at the
root of the repository to turn on the optional checks this guide relies on:

```ini
enable=add-default-case
enable=avoid-nullary-conditions
enable=quote-safe-variables
enable=require-double-brackets
enable=require-variable-braces
```

When a warning is a false positive, disable that one check on the line above
the code, and add a comment saying why:

```bash
# Read by the scripts that source this library.
# shellcheck disable=SC2034
readonly LIB_VERSION="1.2.0"
```

### Language baseline

Scripts target **Bash 4.4 or later**. Earlier versions treat an empty array as
unset under `set -u`, and versions before 4.0 lack `mapfile` and associative
arrays.

## Files

- Executables start with `#!/usr/bin/env bash`. It finds Bash on the `PATH`,
  so the script works on systems where Bash isn't installed at `/bin/bash`.
- Executables have **no extension**. They're commands, and callers shouldn't
  have to know what language they're written in.
- Libraries end in `.sh`, aren't executable and have no shebang. Their first
  line is `# shellcheck shell=bash`, so ShellCheck knows the dialect.
- File names are lowercase, with underscores between words.
- Lay out every file in this order:
  1. Shebang (executables only)
  2. Header comment
  3. `set -euo pipefail` (executables only)
  4. `source` lines for libraries
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

  ```bash
  rsync \
    --archive \
    --delete \
    -- "${src}/" "${dst}/"
  ```

### Pipelines and lists

If a pipeline fits on one line, keep it on one line. Otherwise, put each
stage on its own line, start each continuation line with the `|`, and indent
it 2 spaces. Long `&&` and `||` lists follow the same rule:

```bash
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

  ```bash
  for dir in "${dirs[@]}"; do
    if [[ -d "${dir}" ]]; then
      clean_dir "${dir}"
    elif [[ -e "${dir}" ]]; then
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

  ```bash
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

- Put a space inside `[[` and `]]`, around their operators, and around `|`,
  `&&` and `||`.
- Don't put spaces just inside `$(( ))` or `(( ))`. Put one space around
  their operators: `$((count + 1))`, `((count > max))`.
- Don't put a space between a redirection operator and its target:
  `>"${log}"`, `2>&1`, `<"${input}"`.
- Write a function as `name() {`, with no space before `()` and one space
  before `{`.

## Naming

- Functions and variables are lowercase with underscores: `parse_args`,
  `backup_dir`. The shell's own variables and environment variables are
  uppercase, so lowercase names never clobber them.
- Library functions start with the library's name and `::`, as in
  `log::info`. The prefix shows where a function comes from and avoids
  clashes between libraries.
- Constants and exported variables are `UPPER_SNAKE_CASE`. Declare them at
  the top of the file and make them read-only:

  ```bash
  readonly BACKUP_ROOT="/var/backups"
  declare -rx LC_ALL="C"
  ```

- Name loop variables after what they hold: `for host in "${hosts[@]}"`, not
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
- Keep lists in arrays, never in space-separated strings:
  `"${files[@]}"` expands each element as its own word.

### Tests

- Use `[[ ]]` for tests, not `[ ]` or `test`. It doesn't split words or expand
  globs, and it supports `&&`, `||` and pattern matching.
- Test for empty and non-empty strings with `-z` and `-n`:
  `[[ -n "${name}" ]]`, not `[[ "${name}" ]]`.
- Compare strings with `==`, and numbers with `(( ))`:
  `if ((count > max)); then`.
- The right-hand side of `==` is a glob pattern, and the right-hand side of
  `=~` is a regular expression. Quote it to match literally. To match a
  regular expression, keep it in a variable and leave that one expansion
  unquoted: `[[ "${line}" =~ ${version_re} ]]`.

## Functions

- Define functions as `name() {`. Don't use the `function` keyword.
- Declare every variable a function uses with `local`, so it can't leak into
  or clobber the caller's variables.
- Declare and assign separately when the value comes from a command
  substitution. `local` returns its own status, which hides the command's
  failure:

  ```bash
  local dir
  dir="$(dirname -- "${file}")"
  ```

- A script with at least one function other than `main` puts its top-level
  logic in `main`. The script's last line is `main "$@"`.

## Comments

- Start every comment with `#` and a space.
- Every file has a header comment near the top, after the shebang or the
  ShellCheck directive, that says what the file does:

  ```bash
  #!/usr/bin/env bash
  #
  # Back up a directory to a timestamped tarball.
  ```

- Comment every library function, and every function that isn't both short
  and obvious. Describe its behaviour, followed by the sections that apply:
  the globals it uses or changes, its arguments, its output and its return
  status. Leave out sections that don't apply:

  ```bash
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

- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [GNU Bash manual](https://www.gnu.org/software/bash/manual/)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) on Greg's Wiki
- [shfmt](https://github.com/mvdan/sh)
