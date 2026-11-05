# CMake Idioms and Principles

How to write CMake builds well. [coding-style.md](coding-style.md) covers how
build scripts look. This guide covers how a build is structured: targets and
their usage requirements, dependencies, configuration, installing and
testing. Every example follows the style guide.

## Principles

- **Think in targets, not variables.** Every library and executable is a
  target, and everything it needs (sources, include directories, compile
  options, dependencies) is attached to it. Targets compose; global variables
  leak into everything.
- **Say what each requirement is for.** Mark every requirement `PRIVATE`,
  `PUBLIC` or `INTERFACE`, so CMake passes it exactly to the targets that
  need it.
- **Never touch global state.** Directory-wide and global flags affect every
  target, including dependencies, and can't be undone further down.
- **The build must work as a subproject.** A project pulled in with
  `add_subdirectory()` or FetchContent must not break, slow down or
  reconfigure the project that includes it.
- **Configure once, build anywhere.** Keep build settings in presets and cache
  variables, not in edits to `CMakeLists.txt`.

## Project setup

Start the top-level `CMakeLists.txt` with the version range the project is
tested against, then `project()`:

```cmake
# Builds the buf library, its command-line tool and its tests.
cmake_minimum_required(VERSION 3.24...3.31)

project(buf VERSION 1.2.0 LANGUAGES C)
```

- The first number is the oldest CMake the project supports. The second is
  the newest version you've tested, which tells newer CMake releases to use
  their modern behaviour (policies) up to that version.
- List only the languages the project uses in `LANGUAGES`. CMake checks a
  compiler for each one, so an unused language slows down configuring and can
  fail on machines without that compiler.
- Always build out of source: `cmake -S . -B build`. Add a check that refuses
  an in-source build, because it scatters generated files through the
  source tree:

  ```cmake
  if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
      message(FATAL_ERROR "buf: in-source builds are not supported")
  endif()
  ```

## Targets and usage requirements

- Create every library with `add_library()` and every program with
  `add_executable()`, then attach everything to the target with the
  `target_*` commands.
- Pick the right scope for each requirement:

  | Scope | Used by the target | Passed to targets that link it |
  | --- | --- | --- |
  | `PRIVATE` | Yes | No |
  | `INTERFACE` | No | Yes |
  | `PUBLIC` | Yes | Yes |

  A header directory that the library's public headers live in is `PUBLIC`.
  A library used only inside `.c` files is `PRIVATE`. A header-only library
  is an `INTERFACE` library.
- **List source files explicitly.** Don't collect them with `file(GLOB)`.
  CMake can't tell when a file is added or removed, so a globbed build
  silently misses new files until someone reconfigures.
- Give every library an alias in the form it's exported under, and link to
  the alias:

  ```cmake
  add_library(buf src/buf.c src/pipe.c)
  add_library(buf::buf ALIAS buf)

  target_include_directories(
      buf
      PUBLIC
          "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>"
          "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
  )
  target_compile_features(buf PUBLIC c_std_99)
  ```

  A name with `::` is always a target. If the target doesn't exist,
  `target_link_libraries()` stops with an error, instead of passing an unknown
  name to the linker as a library file.
- Always use the keyword form of `target_link_libraries()`
  (`PUBLIC`/`PRIVATE`/`INTERFACE`). The old plain form can't be mixed with
  the keyword form, and it doesn't say what each dependency is for.

### What not to use

These commands and variables apply to every target in a directory, or to the
whole build. Use the per-target command instead:

| Don't use | Use instead |
| --- | --- |
| `include_directories()` | `target_include_directories()` |
| `add_definitions()`, `add_compile_definitions()` | `target_compile_definitions()` |
| `add_compile_options()` | `target_compile_options()` |
| `link_libraries()`, `link_directories()` | `target_link_libraries()` with imported targets |
| Setting `CMAKE_C_FLAGS` or `CMAKE_EXE_LINKER_FLAGS` | `target_compile_options()`, `target_link_options()` |

The one kind of directory-wide setting allowed is a variable that sets a
default for a target property, such as `CMAKE_C_EXTENSIONS`. Set it at the
top of the project, before any targets, so each target still carries the
value itself:

```cmake
set(CMAKE_C_EXTENSIONS OFF) # -std=c99, not -std=gnu99
```

## Language standards

- Require a language standard with `target_compile_features()`:
  `target_compile_features(buf PUBLIC c_std_99)`. As a `PUBLIC` requirement,
  it reaches every target that includes the library's headers.
- Don't set `CMAKE_C_STANDARD` or add `-std=` flags by hand. A compile feature
  states the minimum the code needs, and lets a consumer that needs a newer
  standard use one.
- Turn off compiler extensions with `CMAKE_C_EXTENSIONS OFF` (or
  `CMAKE_CXX_EXTENSIONS OFF`), so code that relies on an extension fails to
  build instead of only working on one compiler.

## Warnings

Collect the project's warning flags in one `INTERFACE` target and link it
into each of the project's own targets:

```cmake
add_library(buf_warnings INTERFACE)
target_compile_options(
    buf_warnings
    INTERFACE "$<$<C_COMPILER_ID:GNU,Clang,AppleClang>:-Wall;-Wextra;-Wvla>"
)

target_link_libraries(buf PRIVATE $<BUILD_INTERFACE:buf_warnings>)
```

- The generator expression adds the flags only for compilers that understand
  them, so the build still works with other compilers.
- Link the warnings target as `PRIVATE`, so they apply to your code and never
  to code that uses your library.
- Wrap it in `$<BUILD_INTERFACE:...>`. Otherwise installing a static library
  fails, because CMake wants to export `buf_warnings` along with it.
- **Don't turn warnings into errors in `CMakeLists.txt`.** A newer compiler
  adds warnings, and a hard-coded `-Werror` breaks the build for every user
  who has it. Turn them into errors in CI, through the `dev` and `ci` presets,
  with `CMAKE_COMPILE_WARNING_AS_ERROR`.

## Generator expressions

- Use generator expressions (`$<...>`) for anything that depends on the
  build configuration, compiler or platform. They're evaluated per target
  and per configuration at generate time.
- **Never test `CMAKE_BUILD_TYPE` in `if()`.** Multi-config generators (Visual
  Studio, Xcode, Ninja Multi-Config) leave it empty and pick the
  configuration at build time. Write
  `$<$<CONFIG:Debug>:BUF_DEBUG_CHECKS>` instead.
- Keep each generator expression short. When one needs nesting more than two
  levels deep, build it up in named variables first, so it can be read.

## Options and presets

- Declare each user setting with `option()` (for on/off) or a cache variable,
  prefixed with the project name, and give it a sensible default:

  ```cmake
  option(BUF_BUILD_TESTS "Build buf's tests" "${PROJECT_IS_TOP_LEVEL}")
  ```

  Defaulting to `PROJECT_IS_TOP_LEVEL` builds tests when you work on the
  project itself, and skips them when another project includes it.
- **Keep build settings in `CMakePresets.json`**: one preset per way the
  project is built (`dev`, `release`, `ci`, `asan`). A preset records
  the generator, build directory and cache variables, so everyone configures
  the same way with `cmake --preset dev`.
- Put sanitizers, coverage and other tooling options in presets, never in
  `CMakeLists.txt`.

## Dependencies

- **Prefer `find_package()`**, and link the imported targets it provides:
  `ZLIB::ZLIB`, not `${ZLIB_LIBRARIES}`. Imported targets carry their own
  include directories and flags; result variables don't.
- Pass a minimum version: `find_package(ZLIB 1.2.11 REQUIRED)`.
- Use **FetchContent** for dependencies that aren't usually installed, such
  as test frameworks. Pin each one to an exact tag or commit, and let an
  installed copy win when there is one:

  ```cmake
  include(FetchContent)

  FetchContent_Declare(
      unity
      GIT_REPOSITORY https://github.com/ThrowTheSwitch/Unity.git
      GIT_TAG v2.6.0
      FIND_PACKAGE_ARGS 2.6
  )
  FetchContent_MakeAvailable(unity)
  ```

  `FIND_PACKAGE_ARGS` tries `find_package()` first, so packagers and
  developers with the library installed don't download a second copy.
- Never download anything outside FetchContent (for example, with
  `file(DOWNLOAD)` at configure time), so offline and packaged builds can
  provide every dependency themselves.

## Installing and exporting

A library that other projects use installs its targets, headers and a
package config file, so consumers can write `find_package(buf)`:

```cmake
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS buf EXPORT buf_targets)
install(DIRECTORY include/ TYPE INCLUDE)
install(
    EXPORT buf_targets
    NAMESPACE buf::
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/buf"
)

configure_package_config_file(
    cmake/bufConfig.cmake.in
    "${PROJECT_BINARY_DIR}/bufConfig.cmake"
    INSTALL_DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/buf"
)
write_basic_package_version_file(
    "${PROJECT_BINARY_DIR}/bufConfigVersion.cmake"
    COMPATIBILITY SameMajorVersion
)
install(
    FILES
        "${PROJECT_BINARY_DIR}/bufConfig.cmake"
        "${PROJECT_BINARY_DIR}/bufConfigVersion.cmake"
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/buf"
)
```

- Use the `GNUInstallDirs` paths (`CMAKE_INSTALL_LIBDIR` and so on). Never
  hard-code `lib` or `/usr/local`, which differ between platforms and
  distributions.
- Export targets under the same `buf::` namespace as the alias, so code
  that links `buf::buf` works the same whether the library came from
  `add_subdirectory()` or `find_package()`.
- The package config file is named `<Package>Config.cmake`, the name
  `find_package()` searches for. In the config file, call
  `find_dependency()` for each public dependency, so consumers get them too.

## Testing

- Enable testing in the top-level project only, and register each test with
  `add_test()`:

  ```cmake
  if(BUF_BUILD_TESTS)
      enable_testing()
      add_subdirectory(tests)
  endif()
  ```

- Run tests with `ctest --preset dev`, or `ctest --test-dir build
  --output-on-failure` without presets. Show the output of failing tests, so
  CI logs explain the failure.
- Give each test a name that says what it checks: `buf_alloc_rejects_zero`,
  not `test1`.
- Build test programs as ordinary targets, linked to the library under test
  through its `buf::buf` alias, so tests use the library exactly as
  consumers do.

## Code generation and custom commands

- Generate files with `add_custom_command(OUTPUT ...)`, listing every input
  in `DEPENDS`, and add the output to a target's sources. CMake then reruns
  the command only when an input changes.
- Write generated files into the build tree (`${CMAKE_CURRENT_BINARY_DIR}`),
  never into the source tree.
- Run tools through their targets (`COMMAND buf_gen ...`), not hard-coded
  paths, so CMake builds the tool first and uses the right copy.

## Sources

- [CMake documentation](https://cmake.org/cmake/help/latest/), including
  [cmake-buildsystem(7)](https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html)
  and [cmake-packages(7)](https://cmake.org/cmake/help/latest/manual/cmake-packages.7.html)
- [An Introduction to Modern CMake](https://cliutils.gitlab.io/modern-cmake/)
- [Effective Modern CMake](https://gist.github.com/mbinna/c61dbb39bca0e4fb7d1f73b0d66a4fd1)
