# CMake Coding Style

A general-purpose coding style for CMake build scripts (`CMakeLists.txt` and
`.cmake` files), written for modern, target-based CMake 3.24 or later. It
builds on the [CMake documentation](https://cmake.org/cmake/help/latest/) and
widely used community practice (see [Sources](#sources)).

This guide covers how build scripts look. For how to structure a build
(targets, usage requirements, dependencies, installing and testing), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [CMake](https://cmake.org/) 3.24 or later | BSD-3-Clause | Configuring and building, and linting through its own warnings |
| [gersemi](https://github.com/BlankSpruce/gersemi) | MPL-2.0 | Formatting `CMakeLists.txt` and `.cmake` files |

### CMake warnings

CMake's own warnings are the lint gate. A project must configure with **no
warnings** using:

```sh
cmake --preset dev --warn-uninitialized -Werror=dev -Werror=deprecated
```

- `--warn-uninitialized` reports variables that are read before they're
  set, which is almost always a typo.
- `-Werror=dev` turns warnings meant for project authors into errors, such as
  policy warnings and misused commands.
- `-Werror=deprecated` turns uses of deprecated features into errors, so they
  get fixed before a CMake release removes them.

### Formatting

gersemi formats every CMake file. Check formatting in CI with:

```sh
gersemi --check --diff .
```

Commit a `.gersemirc` at the repository root so every editor and CI run uses
the same settings:

```yaml
line_length: 80
indent: 4
```

Formatting is the formatter's job. Where this guide and gersemi's output could
disagree on layout, gersemi wins, so reviews never argue about whitespace.

## Files

- Every directory that defines targets has a `CMakeLists.txt`.
- Helper modules live in a `cmake/` directory at the project root, and are
  added to the search path with
  `list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")`.
- Name a helper module after the function it defines: `cmake/buf_add_test.cmake`
  defines `buf_add_test()`. Find modules follow CMake's required naming,
  `Find<Package>.cmake`.
- Commit `CMakePresets.json`. Never commit `CMakeUserPresets.json`, which
  holds each developer's own presets.

## Layout

### Indentation and line length

- Indent with **4 spaces**. Never use tabs.
- **80 columns** is the limit. gersemi wraps long commands to fit.
- Indent the body of every block (`if()`, `foreach()`, `function()` and so on)
  by one level.

### Commands and arguments

- No space between a command name and its opening parenthesis:
  `if(BUF_BUILD_TESTS)`, not `if (BUF_BUILD_TESTS)`.
- When a command's arguments fit on one line, keep them on one line. When they
  don't, put each keyword section on its own line, with its values indented
  one level below it:

  ```cmake
  target_link_libraries(
      buf
      PUBLIC
          buf_core
      PRIVATE
          ZLIB::ZLIB
          $<BUILD_INTERFACE:buf_warnings>
  )
  ```

- Close block commands with **empty parentheses**: `endif()`, `endforeach()`,
  `endfunction()`. Repeating the condition (`endif(BUF_BUILD_TESTS)`) adds
  nothing and goes stale when the condition changes.
- Write `else()` and `elseif(...)` the same way.

### Whitespace

- No trailing whitespace.
- Don't use more than one blank line in a row.
- Use LF line endings, and end every file with a newline.

## Case

- Write **commands in lowercase**: `add_library`, `target_link_libraries`,
  `if`. CMake ignores the case of command names, and lowercase is what the
  CMake documentation uses.
- Write **keywords in uppercase**: `PUBLIC`, `PRIVATE`, `REQUIRED`, `STATUS`.
  Keywords are case-sensitive, and uppercase makes them stand out from
  values.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Targets | `snake_case`, starting with the project name | `buf`, `buf_core`, `buf_tests` |
| Exported targets | `<project>::<target>` | `buf::buf` |
| Cache variables and options | `UPPER_SNAKE_CASE`, starting with the project name | `BUF_BUILD_TESTS`, `BUF_ENABLE_ASAN` |
| Normal variables | `snake_case` | `buf_sources`, `test_name` |
| Functions | `snake_case`, starting with the project name | `buf_add_test()` |
| Function parameters | `snake_case`, with an `arg_` prefix for parsed arguments | `name`, `arg_SOURCES` |

- **Prefix every global name with the project's name.** Targets, cache
  variables and functions share one namespace across every project in the
  build, including dependencies pulled in with FetchContent.
- Never define names that start with `CMAKE_` or `_`. CMake reserves the
  `CMAKE_` prefix for its own variables, and leading underscores are used by
  CMake's internals.

## Variables

- Reference variables as `${name}`. Inside `if()`, write the bare name
  instead: `if(BUF_BUILD_TESTS)`, not `if(${BUF_BUILD_TESTS})`. `if()`
  expands names itself, and expanding them twice gives the wrong answer when
  a value happens to name another variable.
- **Quote arguments that expand a variable** unless you want a list to split
  into separate arguments: `"${CMAKE_CURRENT_SOURCE_DIR}/include"`. An
  unquoted expansion that contains spaces or semicolons becomes several
  arguments, and an empty one disappears entirely.
- Use `set()` for normal variables and `option()` or `set(... CACHE ...)` for
  settings a user may change. Give every cache entry a help string.
- Don't use `set(... PARENT_SCOPE)` to pass results between directories. Put
  the result on a target, or return it from a function through an output
  variable named by the caller.

## Functions

- Write `function()`, not `macro()`. A function has its own variable scope; a
  macro expands into the caller's scope and can silently overwrite its
  variables.
- Parse keyword arguments with `cmake_parse_arguments()`, using `arg` as the
  prefix, and reject anything it doesn't recognise:

  ```cmake
  function(buf_add_test name)
      cmake_parse_arguments(PARSE_ARGV 1 arg "" "" "SOURCES;LIBRARIES")
      if(arg_UNPARSED_ARGUMENTS)
          message(
              FATAL_ERROR
              "buf_add_test: unknown arguments: ${arg_UNPARSED_ARGUMENTS}"
          )
      endif()

      add_executable("${name}" ${arg_SOURCES})
      target_link_libraries("${name}" PRIVATE ${arg_LIBRARIES})
      add_test(NAME "${name}" COMMAND "${name}")
  endfunction()
  ```

- Document each function with a comment block directly above it, stating its
  arguments and what it creates.

## Messages

- Use `message(STATUS ...)` for progress, `message(WARNING ...)` for problems
  the user should fix, and `message(FATAL_ERROR ...)` to stop. A plain
  `message()` with no mode prints as a notice that looks like an error.
- Start each message with the project or function name, so the user can tell
  which part of a large build printed it.
- **Never break user-visible strings** across lines, so they stay greppable.

## Comments

- Use `#` line comments. Put a space after the `#`.
- Comments explain **why** the build does something, not what the command
  does. `# link zlib` above `target_link_libraries(buf PRIVATE ZLIB::ZLIB)`
  says nothing.
- Explain every workaround, and link to the bug or CMake issue it works
  around, so it can be removed once the fix lands.
- Start every `CMakeLists.txt` with a comment describing what that directory
  builds.

## Third-party code

Vendored third-party build scripts keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide builds on:

- [CMake documentation](https://cmake.org/cmake/help/latest/)
- [An Introduction to Modern CMake](https://cliutils.gitlab.io/modern-cmake/)
- [Effective Modern CMake](https://gist.github.com/mbinna/c61dbb39bca0e4fb7d1f73b0d66a4fd1)
- [gersemi](https://github.com/BlankSpruce/gersemi)
