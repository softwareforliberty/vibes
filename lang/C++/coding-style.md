# C++ Coding Style

A general-purpose coding style for C++ projects. It builds on the
[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html),
and fills the gaps from the
[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
and modern community practice (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(ownership, error handling, const-correctness, templates and other idioms),
see [idioms.md](idioms.md).

The tools that check C++ code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **C++20**.

## Files

- Name files in `snake_case`: `url_parser.h` and `url_parser.cc`. Headers end
  in `.h` and source files in `.cc`.
- Every `.cc` file that implements an interface has a matching `.h` file.
  Small helpers used by only one `.cc` file stay inside it, in an unnamed
  namespace.

### Headers

- Every header is **self-contained**: it compiles on its own, and includes
  everything it needs.
- Every header has an include guard. Don't use `#pragma once`. Build the
  guard from the project name and the file's path, uppercased, with `/` and
  `.` turned into `_`, plus a trailing `_`. For example,
  `myproject/net/url_parser.h` becomes `MYPROJECT_NET_URL_PARSER_H_`. Guards
  are portable, and the full path keeps them unique.
- **Include what you use.** Each file directly includes the headers that
  declare everything it uses. Don't rely on other headers pulling them in.
- Prefer including a header to forward-declaring its types. Forward
  declarations hide dependencies and break when the declared type changes.
- Define functions in a header only when they're short (about 10 lines) or
  must be (templates, `constexpr` functions).

### Include order

Group includes in this order, with a blank line between groups, and sort each
group alphabetically:

1. The `.cc` file's own header. Putting it first proves the header is
   self-contained.
2. C system headers (`<unistd.h>`).
3. C++ standard library headers (`<string>`, `<vector>`).
4. Other libraries' headers.
5. This project's headers.

```cpp
#include "myproject/net/url_parser.h"

#include <sys/types.h>

#include <string>
#include <vector>

#include "absl/strings/str_split.h"

#include "myproject/net/url.h"
```

Use C++ forms of C library headers (`<cstdint>`, `<cstring>`), not the `.h`
forms (`<stdint.h>`).

## Layout

clang-format applies these rules automatically. They're written out here so
reviewers and editors agree with it.

### Indentation and line length

- Indent with **2 spaces**. Never use tabs.
- Continuation lines are indented **4 spaces**, or line up with the open
  parenthesis.
- **80 columns** is the limit. Long URLs and `#include` lines may run over.
- **Never break user-visible strings** across lines, so they stay greppable.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Braces

- Opening braces go **last on the line**, for functions, classes and
  namespaces as well as control statements. The closing brace goes on its own
  line, unless an `else` or a do-loop's `while` follows it.
- **Always use braces** for the bodies of `if`, `else`, `for`, `while` and
  `do`, even when the body is a single statement. A statement added later
  can't silently fall outside the block.

```cpp
if (!parser) {
  ReportError("no parser");
} else if (parser->Count() > kMaxSegments) {
  ReportError("too many segments");
} else {
  Process(*parser);
}
```

### Functions

- Keep the return type on the same line as the function name.
- When the parameters don't fit on one line, wrap them and line them up with
  the first parameter. If even that doesn't fit, put every parameter on its
  own line, indented 4 spaces.

```cpp
std::string JoinPath(std::string_view directory, std::string_view name,
                     char separator) {
  ...
}
```

### Classes

- Order sections as `public`, then `protected`, then `private`, and leave out
  empty sections. Readers of a class want its interface first.
- Indent access specifiers by **1 space**, and members by 2.
- Within each section, declare in this order: types and aliases, constants,
  factory functions, constructors and assignment operators, the destructor,
  other methods, then data members.

```cpp
class UrlParser {
 public:
  explicit UrlParser(std::string_view text);

  UrlParser(const UrlParser &) = delete;
  UrlParser &operator=(const UrlParser &) = delete;

  /// Returns the number of path segments found.
  int Count() const { return count_; }

 private:
  std::string text_;
  int count_ = 0;
};
```

- A constructor initialiser list stays on the signature's line when it all
  fits. Otherwise it starts on its own line, indented 4 spaces:

  ```cpp
  UrlParser::UrlParser(std::string_view text)
      : text_(text), count_(CountSegments(text)) {}
  ```

### Namespaces

- Don't indent the contents of a namespace.
- Close each namespace with a comment naming it.

```cpp
namespace myproject::net {

int CountSegments(std::string_view path);

}  // namespace myproject::net
```

### Switch

Indent `case` labels 2 spaces inside the `switch`, and their statements 2 more.
Mark every intentional fall-through with `[[fallthrough]];`. The compiler then
warns about any fall-through that isn't marked.

```cpp
switch (state) {
  case State::kStarting:
    Prepare();
    [[fallthrough]];
  case State::kRunning:
    Step();
    break;
  case State::kStopped:
    break;
}
```

### Spacing

- Put a space after `if`, `for`, `while`, `switch` and `catch`, and before an
  opening brace.
- No spaces just inside parentheses or angle brackets: `std::vector<int>`.
- Put one space on each side of binary and ternary operators. No space after
  a unary operator.
- The `*` and `&` stick to the name, not the type: `int *count`,
  `const std::string &name`. One declaration per line keeps this unambiguous.
- Put a space after `template`: `template <typename T>`.
- Put two spaces before a trailing `//` comment.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Types: classes, structs, enums, aliases, concepts, template parameters | `PascalCase` | `UrlParser`, `ValueType` |
| Functions and methods | `PascalCase` | `ParseUrl()`, `Count()` |
| Variables and parameters | `snake_case` | `segment_count` |
| Class data members | `snake_case` with a trailing `_` | `count_` |
| Struct data members | `snake_case` | `width` |
| Constants with static storage, and `constexpr` values | `k` + `PascalCase` | `kMaxSegments` |
| Enumerators | `k` + `PascalCase` | `State::kRunning` |
| Namespaces | `snake_case` | `myproject::net` |
| Macros | `UPPER_SNAKE_CASE`, prefixed with the project name | `MYPROJECT_ASSERT` |

- Treat abbreviations as words: `UrlParser` and `HttpClient`, not `URLParser`.
  Word boundaries stay visible.
- Names describe purpose. Use short names (`i`, `n`, `it`) only in small
  scopes where the meaning is obvious.
- The trailing `_` on class members tells them apart from locals and
  parameters at a glance. Struct members don't need it, because structs hold
  plain data that callers access directly.
- Use inclusive terms. Say primary/secondary or leader/follower instead of
  master/slave, and allowlist/denylist instead of whitelist/blacklist.

### Reserved identifiers

- Never declare names that contain `__` anywhere, or that start with `_`
  followed by a capital letter. Never declare global names that start with
  `_`. The C++ standard reserves these for the compiler and standard library.

## Comments

- Use `//` for comments, and `///` for API documentation.
- Comments explain **what** and **why**, not **how**. Good names and small
  functions should make the "how" obvious.
- Start every file with a short comment describing what it contains.
- Write a TODO as `// TODO: <issue link> - <what needs doing>`. The link
  gives the context and an owner.

### API documentation

- Document every public class, function and non-obvious data member with a
  `///` comment on its **declaration in the header**. The header is where
  someone using the API reads its contract.
- Say what the function does, what it returns, which arguments may be null,
  who owns what, and what errors it reports. Don't repeat the signature.
- Comments on a definition in the `.cc` file explain the implementation, and
  only when it's tricky.

```cpp
/// Splits `path` into its non-empty segments.
///
/// The returned views point into `path`, which must outlive them.
std::vector<std::string_view> SplitPath(std::string_view path);
```

## Language usage

### Declarations

- Declare each variable **where it's first needed**, in the narrowest scope
  that works, and initialise it in the declaration. Small scopes and
  initialised variables prevent uninitialised-variable bugs.
- One declaration per line.
- Make a variable `const` (or `constexpr`) unless it needs to change.
- Prefer default member initialisers (`int count_ = 0;`) to repeating the
  value in each constructor.
- Use designated initialisers for aggregates, in declaration order:
  `Options opts{.retries = 3, .verbose = true};`.

### auto

Use `auto` when it makes the code clearer: when the type is obvious from the
right-hand side (`auto parser = std::make_unique<UrlParser>(text);`), or long
and unimportant (iterators). Spell out the type when it carries meaning the
reader needs.

### Casts

- Never use C-style casts (`(int)x`). Use `static_cast`. Named casts say what
  they do, and can be searched for.
- Use `const_cast` and `reinterpret_cast` only when nothing else works, such
  as calling a C API. clang-tidy flags both, so suppress the warning on that
  line with the reason.
- Use `std::bit_cast` to reinterpret an object's bytes as another type.

### Classes and structs

- Use a `struct` only for passive data with all-public members and no
  invariants. Everything else is a `class` with private data.
- Mark single-argument constructors and conversion operators `explicit`, so
  they never run as hidden implicit conversions.
- Mark overriding functions `override` (or `final`), and don't repeat
  `virtual` on them. The compiler then catches signature mismatches.
- Declare copy and move operations explicitly, as `= default` or `= delete`,
  whenever a class doesn't have the default behaviour.

### Types and constants

- Use `nullptr` for null pointers, never `0` or `NULL`.
- Use `enum class`, not plain `enum`. Scoped enums don't leak names, and
  don't convert to integers silently.
- Use `constexpr` constants and functions instead of macros. Define
  constants in headers as `inline constexpr`.
- Use `using` aliases, not `typedef`.
- Use `int` for ordinary integers, and the `<cstdint>` types when the size
  matters. Don't use unsigned types to mean "never negative". Use them for
  bit patterns and modular arithmetic only.
- Prefer brace initialisation (`int x{3};`), which rejects narrowing
  conversions. Use parentheses when braces would pick an
  `std::initializer_list` constructor you don't want:
  `std::vector<int> v(3, 0);`.
- Don't use magic numbers. Give each constant a name, and add a comment
  explaining the size chosen for each limit.

### Statements and expressions

- Test pointers and smart pointers with `if (ptr)` and `if (!ptr)`.
- Never compare a `bool` to `true` or `false`.
- Don't put assignments inside conditions. Use an `if` initialiser instead:
  `if (auto it = map.find(key); it != map.end()) {`.
- Mark functions whose result must not be ignored `[[nodiscard]]`.

### Namespaces and macros

- Put all code in a namespace named after the project. File-local helpers go
  in an unnamed namespace.
- Never write `using namespace`. It pulls in names you didn't ask for, and
  the set changes as libraries grow. Using-declarations
  (`using std::string;`) are fine in `.cc` files and inside functions.
- Avoid macros. When one is unavoidable, name it in `UPPER_SNAKE_CASE` with
  the project prefix, and `#undef` it when it's only needed locally.

### Lambdas

- List captures explicitly (`[this, &total]`) when a lambda outlives the
  current statement. Default captures (`[&]`, `[=]`) are fine for lambdas
  used on the spot.
- Keep lambdas short. A lambda longer than a few lines should be a named
  function.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Google C++ Style Guide and borrows from:

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [clang-format style options](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)
- [clang-tidy checks](https://clang.llvm.org/extra/clang-tidy/checks/list.html)
