# Objective-C Coding Style

A general-purpose coding style for Objective-C projects. It builds on the
[Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html)
and Apple's
[Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (memory
management, nullability, error handling and other idioms), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [clang-format](https://clang.llvm.org/docs/ClangFormat.html) | Apache-2.0 with LLVM exception | Formatting, applied automatically |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/) | Apache-2.0 with LLVM exception | Linting naming and bug-prone patterns |
| [Clang Static Analyzer](https://clang-analyzer.llvm.org/) | Apache-2.0 with LLVM exception | Finding leaks, nil misuse and API misuse along every code path |
| [Clang](https://clang.llvm.org/) | Apache-2.0 with LLVM exception | Compiling, and linting through its warning flags |

### Formatting

Commit this `.clang-format` at the repository root, and run clang-format on
every changed file before committing. A formatter ends layout debates and
keeps diffs free of whitespace noise.

```yaml
---
Language: ObjC
BasedOnStyle: Google
ColumnLimit: 100
DerivePointerAlignment: false
PointerAlignment: Right
```

### Linting

Commit this `.clang-tidy` at the repository root. Code must pass it with no
warnings.

```yaml
Checks: >
  bugprone-*,
  clang-analyzer-*,
  google-objc-*,
  objc-*,
  readability-braces-around-statements,
  -bugprone-easily-swappable-parameters
WarningsAsErrors: '*'
```

- Suppress a warning only on the line that needs it, with
  `// NOLINT(check-name)` and a reason. A bare `NOLINT` hides every check,
  including ones nobody meant to silence.
- Run the static analyzer over the whole build with `scan-build`, for example
  `scan-build make`. It follows paths across functions, and finds bugs that
  per-file checks miss.

### Compiler warnings

Code must build with **no warnings** using at least these flags:

```sh
clang -fobjc-arc -Wall -Wextra -Wdocumentation -Wimplicit-retain-self \
    -Wnullable-to-nonnull-conversion
```

- `-fobjc-arc` turns on Automatic Reference Counting. All code uses ARC.
- `-Wimplicit-retain-self` flags blocks that capture `self` through an
  instance variable without saying so (see [idioms.md](idioms.md#blocks)).
- `-Wnullable-to-nonnull-conversion` enforces the
  [nullability annotations](#nullability).
- `-Wdocumentation` checks [API comments](#api-documentation) against the
  declarations they describe.

## Files

- Name each file after the class it defines: `ABCImageCache.h` and
  `ABCImageCache.m`.
- Name a category's files after the class and the category:
  `NSString+ABCTrimming.h`.
- Each `.h` file holds the public interface. Private properties, methods and
  instance variables go in the `.m` file.

### Headers

- Use `#import` for Objective-C headers, and `#include` for C and C++ headers.
  `#import` guards against double inclusion by itself. A plain C header keeps
  its own include guard.
- **Import what you use.** Each file directly imports the headers that
  declare everything it uses. Don't rely on other headers pulling them in.
- In headers, forward-declare classes and protocols with `@class` and
  `@protocol` instead of importing their headers, when the header only uses
  them as pointer types. Fewer imports mean faster builds and fewer
  dependency cycles.

### Import order

Group imports in this order, with a blank line between groups, and sort each
group alphabetically:

1. The `.m` file's own header. Putting it first proves the header is
   self-contained.
2. System and framework headers (`<Foundation/Foundation.h>`).
3. Other libraries' headers.
4. This project's headers.

```objc
#import "ABCImageCache.h"

#import <Foundation/Foundation.h>

#import "ABCDiskStore.h"
```

## Layout

clang-format applies these rules automatically. They're written out here so
reviewers and editors agree with it.

### Indentation and line length

- Indent with **2 spaces**. Never use tabs.
- **100 columns** is the limit. Objective-C's long, descriptive names need
  the extra room.
- **Never break user-visible strings** across lines, so they stay greppable.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Braces

- Opening braces go **last on the line**, for methods and functions as well
  as control statements. The closing brace goes on its own line, unless an
  `else` or a do-loop's `while` follows it.
- **Always use braces** for the bodies of `if`, `else`, `for`, `while` and
  `do`, even when the body is a single statement. A statement added later
  can't silently fall outside the block.

```objc
if (!data) {
  return nil;
} else if (data.length > kMaxImageBytes) {
  return nil;
}
```

### Methods

- Put a space after the `-` or `+`, and none between the return type and the
  name: `- (void)removeAllImages;`.
- When a declaration doesn't fit on one line, put each keyword on its own
  line and line up the colons.

```objc
- (void)storeImageData:(NSData *)data
                forKey:(NSString *)key
            completion:(ABCStoreCompletion)completion {
  ...
}
```

- Format long message sends the same way: one argument per line, with the
  colons lined up.
- No spaces just inside the brackets of a message send:
  `[cache imageDataForKey:key]`.

### Interfaces and properties

```objc
@interface ABCImageCache : NSObject<NSCopying>

@property(nonatomic, readonly) NSUInteger count;

- (instancetype)initWithCapacity:(NSUInteger)capacity NS_DESIGNATED_INITIALIZER;

@end
```

- No space between `@property` and its attributes. List the attributes in
  this order: atomicity, ownership (`strong`, `weak`, `copy`), access
  (`readonly`), then a custom `getter=`.
- No space between a superclass and its protocol list:
  `NSObject<NSCopying>`.
- Separate groups of methods in an `@implementation` with
  `#pragma mark - <Group name>`, so editors can show an outline.

### Spacing

- Put a space after `if`, `for`, `while`, `switch` and `@catch`, and before
  an opening brace.
- Put one space on each side of binary and ternary operators. No space after
  a unary operator.
- The `*` sticks to the name, not the type: `NSString *name`, `int *count`.
- Put two spaces before a trailing `//` comment.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Classes and protocols | Prefix + `PascalCase` | `ABCImageCache`, `ABCImageCacheDelegate` |
| Methods | `camelCase`, read as a phrase | `-storeImageData:forKey:` |
| Properties and local variables | `camelCase` | `imageCount` |
| Instance variables | `_` + `camelCase` | `_imageCount` |
| File-local constants | `k` + `PascalCase` | `kMaxImageBytes` |
| Exported constants and notification names | Prefix + `PascalCase` | `ABCImageCacheDidEvictNotification` |
| Enum types and values | Prefix + `PascalCase`; values start with the type name | `ABCLoadState`, `ABCLoadStateIdle` |
| C functions | Prefix + `PascalCase` | `ABCImageSizeMake()` |
| Category methods on classes you don't own | Lowercase prefix + `_` + `camelCase` | `-abc_trimmedString` |
| Macros | `UPPER_SNAKE_CASE`, with the prefix | `ABC_ASSERT_MAIN_THREAD` |

- **Prefixes.** Objective-C has no namespaces, so every exported name starts
  with a prefix of **three or more capital letters** (`ABC`). Apple reserves
  two-letter prefixes.
- **Category methods** on classes you don't own carry a lowercase prefix. If
  two categories add a method with the same name, which one runs is
  undefined.
- **Methods read like phrases.** Name every argument with a keyword:
  `-insertObject:atIndex:`, not `-insert::`. Don't use `and` to join
  arguments.
- **Getters have no `get` prefix.** A property `count` has the getter
  `-count`. Methods starting with `get` return values through pointer
  arguments.
- **Boolean properties read as adjectives**, with an `is` getter:
  `@property(nonatomic, getter=isEnabled) BOOL enabled;`.
- **Initialisers** start with `init` (`-initWithCapacity:`). Convenience
  constructors start with the class name minus its prefix
  (`+imageCacheWithCapacity:`).
- **Delegate methods** start with the name of the object sending them, which
  is also the first argument: `-imageCache:didEvictImageForKey:`.
- Spell words out. `-setBackgroundColor:`, not `-setBgColor:`. Common
  abbreviations such as `URL`, `HTTP` and `ID` stay in capitals.
- Use inclusive terms. Say primary/secondary or leader/follower instead of
  master/slave, and allowlist/denylist instead of whitelist/blacklist.

### Reserved names

- Never start a method name with `_`. Apple reserves that for its own private
  methods, and a clash silently overrides the framework's method.
- Never declare C names that contain `__`, or that start with `_` followed by
  a capital letter. The C standard reserves these.

## Comments

- Use `//` for comments, and `///` for API documentation.
- Comments explain **what** and **why**, not **how**. Good names and small
  methods should make the "how" obvious.
- Start every file with a short comment describing what it contains.
- Write a TODO as `// TODO: <issue link> - <what needs doing>`. The link
  gives the context and an owner.

### API documentation

- Document every public class, method, property and constant with a `///`
  comment on its **declaration in the header**. The header is where someone
  using the API reads its contract.
- Say what the method does, what it returns, what may be `nil`, and what
  errors it reports. Don't repeat the signature.
- Comments in the `.m` file explain the implementation, and only when it's
  tricky.

```objc
/// Returns the cached data for @c key, or nil if nothing is cached under it.
- (nullable NSData *)imageDataForKey:(NSString *)key;
```

## Language usage

### Declarations

- Declare each variable **where it's first needed**, in the narrowest scope
  that works, and initialise it in the declaration. Small scopes and
  initialised variables prevent uninitialised-variable bugs.
- One declaration per line.
- Declare constants as typed `static const` (or `extern const`) variables,
  not `#define`s. Typed constants are checked by the compiler and visible in
  the debugger.

  ```objc
  // ABCImageCache.h
  extern NSString *const ABCImageCacheDidEvictNotification;

  // ABCImageCache.m
  NSString *const ABCImageCacheDidEvictNotification = @"ABCImageCacheDidEvictNotification";
  static const NSUInteger kMaxImageBytes = 1024 * 1024;
  ```

- Don't use magic numbers. Give each constant a name, and add a comment
  explaining the size chosen for each limit.

### Types

- Use `BOOL` with `YES` and `NO`. Use `nil` for object pointers, and `NULL`
  for C pointers.
- Return `instancetype` from initialisers and convenience constructors, so
  subclasses get the right type.
- Declare enums with `NS_ENUM`, and bit masks with `NS_OPTIONS`. Both fix the
  underlying type, and let the compiler check `switch` statements:

  ```objc
  typedef NS_ENUM(NSInteger, ABCLoadState) {
    ABCLoadStateIdle,
    ABCLoadStateLoading,
    ABCLoadStateFinished,
  };
  ```

- Give collections their element types with lightweight generics:
  `NSArray<NSString *> *names`.
- Give a block type a `typedef` when it's used more than once:
  `typedef void (^ABCStoreCompletion)(NSError *_Nullable error);`.
- Use literal syntax for `NSString`, `NSNumber`, `NSArray` and
  `NSDictionary` (`@"text"`, `@42`, `@(count)`, `@[...]`, `@{...}`). It's
  shorter, and it fails loudly on `nil` elements.
- Use `NSInteger` and `NSUInteger` for counts and indexes in Objective-C
  APIs, to match Foundation.

### Properties and messages

- Expose state through properties, not public instance variables. Declare
  instance variables only in the `@implementation` block, and only when a
  property won't do.
- Make properties `nonatomic`. Atomic properties don't make a class
  thread-safe (see [idioms.md](idioms.md#concurrency)).
- Use dot syntax for properties, and brackets for everything else.
  `view.frame` reads a property. `[view layoutIfNeeded]` performs an action.
- Create objects with `[[ABCImageCache alloc] init]`, not `[ABCImageCache new]`.
  Spelling out the initialiser keeps every allocation looking the same,
  whichever initialiser it calls.

### Statements and expressions

- Test objects with `if (obj)` and `if (!obj)`.
- Never compare a `BOOL` to `YES` or `NO`. Any non-zero value is true, so
  `flag == YES` can be false for a true value.
- Don't put assignments inside conditions.
- `switch` on an `NS_ENUM` without a `default` case when you mean to handle
  every value. The compiler then warns when a new value is added and isn't
  handled.

### Nullability

- Wrap every header in `NS_ASSUME_NONNULL_BEGIN` and `NS_ASSUME_NONNULL_END`,
  and mark the exceptions `nullable`. Every pointer in the API then states
  whether it may be `nil`, and the compiler checks callers.
- Use `nullable` in method and property declarations, and `_Nullable` inside
  other C types such as block parameters.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Google Objective-C Style Guide and borrows from:

- [Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html)
- [Apple: Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
- [clang-format style options](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)
- [clang-tidy checks](https://clang.llvm.org/extra/clang-tidy/checks/list.html)
