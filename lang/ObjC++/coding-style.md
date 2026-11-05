# Objective-C++ Coding Style

A general-purpose coding style for Objective-C++ (`.mm`) code, which mixes
Objective-C and C++ in one file. It builds on the Objective-C++ guidance in
the [Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html),
which in turn rests on the
[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
and Apple's
[Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (bridging
the two languages, ownership across them, error handling and other idioms),
see [idioms.md](idioms.md).

## The core rule

**Follow the style of the language you're writing in.** Code inside an
Objective-C method follows the Objective-C rules. Code inside a C++ function
or class follows the C++ rules. Each language's names and idioms then stay
recognisable, even when they sit side by side. Rules that apply to the whole
file (indentation, braces, spacing, comments) are shared by both languages.

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting modernisation and bug-prone patterns |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Finding leaks, nil misuse and API misuse along every code path |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Compiling, and linting through its warning flags |

### Formatting

Commit this `.clang-format` at the repository root, and run clang-format on
every changed file before committing. A formatter ends layout debates and
keeps diffs free of whitespace noise.

```yaml
---
Language: Cpp
BasedOnStyle: Google
DerivePointerAlignment: false
PointerAlignment: Right
---
Language: ObjC
BasedOnStyle: Google
ColumnLimit: 100
DerivePointerAlignment: false
PointerAlignment: Right
```

clang-format formats `.mm` files and Objective-C headers with the `ObjC`
section, and pure C++ files with the `Cpp` section.

### Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
Checks: >
  bugprone-*,
  clang-analyzer-*,
  cppcoreguidelines-*,
  google-*,
  misc-*,
  modernize-*,
  objc-*,
  performance-*,
  readability-*,
  -bugprone-easily-swappable-parameters,
  -google-readability-todo,
  -modernize-use-trailing-return-type,
  -readability-identifier-length,
  -readability-identifier-naming
WarningsAsErrors: '*'
CheckOptions:
  readability-implicit-bool-conversion.AllowPointerConditions: true
```

- Identifier naming is checked by review, not clang-tidy. One file holds two
  naming schemes, and the check can't tell which applies where.
- Suppress a warning only on the line that needs it, with
  `// NOLINT(check-name)` and a reason. A bare `NOLINT` hides every check,
  including ones nobody meant to silence.
- Run the static analyzer over the whole build with `scan-build`, for example
  `scan-build make`. It follows paths across functions, and finds bugs that
  per-file checks miss.

### Compiler warnings

Code must build with **no warnings** using at least these flags:

```sh
clang++ -std=c++20 -fobjc-arc -Wall -Wextra -Wconversion -Wshadow \
    -Wnon-virtual-dtor -Woverloaded-virtual -Wdocumentation \
    -Wimplicit-retain-self -Wnullable-to-nonnull-conversion
```

- The baseline C++ language is **C++20**, and all code uses ARC.
- `-Wold-style-cast` is left out, because ARC bridging casts
  (`(__bridge T)`) must use C-style cast syntax. In C++ code, reviewers check
  the no C-style casts rule (see [Language usage](#language-usage)).

## Files

- Implementation files that mix the languages end in `.mm`. Keep them to the
  code that needs both languages. Pure C++ stays in `.cc` files, and pure
  Objective-C in `.m` files.
- **Keep headers to one language where possible.** A header that `.m` files
  or Swift import contains no C++. A header that pure C++ files include
  contains no Objective-C. Only a header used exclusively by `.mm` files may
  mix them, and it says so in its opening comment.
- Name Objective-C files after their class (`ABCSpellChecker.mm`), and C++
  files in `snake_case` (`spell_checker.cc`).

### Headers

- Use `#import` for Objective-C headers, and `#include` for C and C++ headers.
  `#import` guards against double inclusion by itself.
- Every C or C++ header has an include guard. Don't use `#pragma once`. Build
  the guard from the project name and the file's path, uppercased, with `/`
  and `.` turned into `_`, plus a trailing `_`. For example,
  `myproject/spell/checker.h` becomes `MYPROJECT_SPELL_CHECKER_H_`.
- **Include what you use.** Each file directly includes the headers that
  declare everything it uses. Don't rely on other headers pulling them in.

### Include order

Group includes in this order, with a blank line between groups, and sort each
group alphabetically:

1. The file's own header. Putting it first proves the header is
   self-contained.
2. C system and framework headers (`<Foundation/Foundation.h>`).
3. C++ standard library headers (`<string>`, `<vector>`).
4. Other libraries' headers.
5. This project's headers.

```objc
#import "ABCSpellChecker.h"

#import <Foundation/Foundation.h>

#include <memory>
#include <string>

#include "myproject/spell/checker.h"
```

## Layout

clang-format applies these rules automatically. They're written out here so
reviewers and editors agree with it.

### Indentation and line length

- Indent with **2 spaces**. Never use tabs.
- **100 columns** is the limit in `.mm` files and Objective-C headers, and
  **80 columns** in pure C++ files.
- **Never break user-visible strings** across lines, so they stay greppable.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Braces

- Opening braces go **last on the line**, for functions, methods, classes and
  namespaces as well as control statements. The closing brace goes on its own
  line, unless an `else` or a do-loop's `while` follows it.
- **Always use braces** for the bodies of `if`, `else`, `for`, `while` and
  `do`, even when the body is a single statement. A statement added later
  can't silently fall outside the block.

### Spacing

- Put a space after `if`, `for`, `while`, `switch`, `catch` and `@catch`, and
  before an opening brace.
- Put one space on each side of binary and ternary operators. No space after
  a unary operator.
- The `*` and `&` stick to the name, not the type: `NSString *name`,
  `const std::string &text`.
- Put two spaces before a trailing `//` comment.

## Naming

Name each thing by the rules of the language it belongs to.

### In Objective-C code

| Kind | Convention | Example |
| --- | --- | --- |
| Classes and protocols | Prefix + `PascalCase` | `ABCSpellChecker` |
| Methods | `camelCase`, read as a phrase | `-suggestionsForWord:` |
| Properties and local variables | `camelCase` | `wordCount` |
| Instance variables | `_` + `camelCase` | `_checker` |
| File-local constants | `k` + `PascalCase` | `kMaxSuggestions` |
| Exported constants | Prefix + `PascalCase` | `ABCSpellCheckerErrorDomain` |

- Every exported Objective-C name starts with a prefix of **three or more
  capital letters** (`ABC`). Apple reserves two-letter prefixes.
- Never start a method name with `_`. Apple reserves that for its own private
  methods.

### In C++ code

| Kind | Convention | Example |
| --- | --- | --- |
| Types | `PascalCase` | `SpellChecker` |
| Functions and methods | `PascalCase` | `Suggest()` |
| Variables and parameters | `snake_case` | `word_count` |
| Class data members | `snake_case` with a trailing `_` | `dictionary_` |
| Constants with static storage, and `constexpr` values | `k` + `PascalCase` | `kMaxSuggestions` |
| Namespaces | `snake_case` | `myproject::spell` |

- Never declare names that contain `__` anywhere, or that start with `_`
  followed by a capital letter. The C++ standard reserves these.

### Shared rules

- Macros are `UPPER_SNAKE_CASE`, with the project prefix. Avoid them where a
  constant or function will do.
- Use inclusive terms. Say primary/secondary or leader/follower instead of
  master/slave, and allowlist/denylist instead of whitelist/blacklist.

## Comments

- Use `//` for comments, and `///` for API documentation.
- Comments explain **what** and **why**, not **how**. Good names and small
  functions should make the "how" obvious.
- Start every file with a short comment describing what it contains.
- Write a TODO as `// TODO: <issue link> - <what needs doing>`. The link
  gives the context and an owner.
- Document every public class, function, method and property with a `///`
  comment on its **declaration in the header**. The header is where someone
  using the API reads its contract.

## Language usage

### Shared rules

- Declare each variable **where it's first needed**, in the narrowest scope
  that works, and initialise it in the declaration. Small scopes and
  initialised variables prevent uninitialised-variable bugs.
- One declaration per line.
- Use `nil` for Objective-C object pointers, and `nullptr` for all other
  pointers. `NULL` is an integer in C++, and can pick the wrong overload.
- Test pointers with `if (ptr)` and `if (!ptr)`.
- Don't put assignments inside conditions.
- Don't use magic numbers. Give each constant a name, and add a comment
  explaining the size chosen for each limit.

### In Objective-C code

- Use `BOOL` with `YES` and `NO`. Never compare a `BOOL` to `YES` or `NO`.
- Return `instancetype` from initialisers and convenience constructors.
- Declare enums with `NS_ENUM`, and bit masks with `NS_OPTIONS`.
- Make properties `nonatomic`, and use `copy` for `NSString`, collections and
  blocks.
- Use dot syntax for properties, and brackets for everything else.
- Wrap every Objective-C header in `NS_ASSUME_NONNULL_BEGIN` and
  `NS_ASSUME_NONNULL_END`, and mark the exceptions `nullable`.

### In C++ code

- Use `bool` with `true` and `false`. Never compare a `bool` to `true` or
  `false`.
- Never use C-style casts (`(int)x`). Use `static_cast`. The one exception is
  an ARC bridging cast (`(__bridge T)`), which has no other syntax.
- Use `enum class`, not plain `enum`.
- Use `constexpr` constants and functions instead of macros.
- Mark single-argument constructors `explicit`, and overriding functions
  `override`.
- Never write `using namespace`.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Objective-C++ guidance in the Google Objective-C
Style Guide and borrows from:

- [Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [Apple: Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
- [clang-format style options](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)
- [clang-tidy checks](https://clang.llvm.org/extra/clang-tidy/checks/list.html)
