# Swift Coding Style

A general-purpose coding style for Swift projects. It builds on the
[Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
and the [Google Swift Style Guide](https://google.github.io/swift/), and fills
the gaps from other long-lived FOSS Swift projects and their tools (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (value
types, optionals, errors, memory, concurrency and other idioms), see
[idioms.md](idioms.md).

The tools that check Swift code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Swift 5.9**.

## Source files

- Encode source files in **UTF-8**.
- A file holding one primary type is named after it: `ImageCache.swift`.
- A file that only extends a type to add a conformance is named
  `Type+Protocol.swift`: `ImageCache+Codable.swift`. A file of other
  extensions is named after what they add: `String+Escaping.swift`.
- Keep one primary type per file. Small helper types used only by that type
  may share its file, as `private` declarations.

### Imports

- Import whole modules, one per line, sorted in lexicographic order.
  swift-format applies the order.
- Import only what the file uses. An unused import slows builds and hides
  real dependencies.
- Use `@testable import` only in test targets.

## Layout

swift-format applies these rules automatically. They're written out here so
reviewers and editors agree with it.

### Indentation and line length

- Indent with **2 spaces**. Never use tabs.
- **100 columns** is the limit. Swift's descriptive argument labels need the
  room.
- **Never break user-visible strings** across lines, so they stay greppable.
  Use a multi-line string literal (`"""`) for genuinely multi-line text.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### One thing per line

- One statement per line. Don't use semicolons.
- One variable per declaration: `var count = 0` and `var total = 0` on two
  lines, not `var count = 0, total = 0`.

### Wrapping

When a declaration, call or collection doesn't fit on one line, put **every**
argument, parameter or element on its own line, indented one level, with the
closing bracket on its own line:

```swift
let request = URLRequest(
  url: endpoint,
  cachePolicy: .reloadIgnoringLocalCacheData,
  timeoutInterval: 30
)
```

- Don't mix: either everything fits on one line, or every item gets its own
  line. Partly wrapped lists hide items. swift-format wraps calls and
  declarations this way, but it keeps a collection's line breaks as written,
  so put each element on its own line yourself.
- Multi-line collection literals end every element with a trailing comma, so
  adding an element changes one line in a diff.

## Braces

- Opening braces go **last on the line**, for every kind of block: types,
  functions, closures and control flow. The one exception is a type or
  function whose header swift-format has to wrap, such as a long list of
  conformances: it puts the `{` on a line of its own.
- `else`, `catch` and the closing brace of a `repeat` sit on the same line as
  the preceding closing brace: `} else {`, `} catch {`, `} while condition`.
- Swift requires braces around every body, so there are no brace-free bodies
  to style.
- A `guard` keeps its `else {` on the same line as the condition when it fits.

## Spacing

- A colon has no space before it and one after: `let count: Int`,
  `[String: Int]`, `func load(from url: URL)`. A ternary `? :` has spaces on
  both sides.
- Put one space on each side of binary operators: `a + b`, `x == y`. Range
  operators take no spaces: `0..<count`, `start...end`.
- No space between a function name and `(`, and no spaces just inside
  brackets or parentheses.
- Put the return arrow between single spaces: `func size() -> Int`.

## Naming

Names follow the Swift API Design Guidelines. **Clarity at the point of use**
is the goal: a call should read clearly where it's written, not just where
it's declared.

| Kind | Convention | Example |
| --- | --- | --- |
| Types and protocols | `UpperCamelCase` | `ImageCache`, `ImageLoading` |
| Functions, methods, properties, variables | `lowerCamelCase` | `storeImage(_:forKey:)`, `imageCount` |
| Enum cases | `lowerCamelCase` | `.idle`, `.loading` |
| Constants, global and static | `lowerCamelCase` | `maxImageBytes` |
| Generic parameters | `UpperCamelCase`, descriptive or a single letter | `Element`, `T` |

- **No `k` prefix and no `UPPER_SNAKE_CASE`** for constants. A constant is
  just a `let`, and the type system already says it can't change.
- **No type prefixes.** Modules are namespaces, so `ImageCache` doesn't need
  `ABCImageCache`. A Swift type exposed to Objective-C gets a prefixed
  Objective-C name instead, following the
  [Objective-C naming rules](../ObjC/coding-style.md#naming):
  `@objc(ABCImageCache) final class ImageCache: NSObject`.
- **Acronyms take one case**, depending on where they fall: `URLSession`,
  `userID`, `httpStatus`, `isRepresentableAsASCII`.
- **Protocols** that describe what something is are nouns (`Collection`).
  Protocols that describe a capability end in `-able`, `-ible` or `-ing`
  (`Equatable`, `ProgressReporting`).
- **Booleans read as assertions**: `isEmpty`, `canSend`, `hasChanges`.
- **Methods read as phrases at the call site.** Name side-effecting methods
  as verbs (`sort()`, `append(_:)`), and side-effect-free ones as nouns or
  past participles (`distance(to:)`, `sorted()`).
- **Mutating and non-mutating pairs** share a stem: `sort()` and `sorted()`,
  `formUnion(_:)` and `union(_:)`.
- **Factory methods** start with `make`: `makeIterator()`.
- **Argument labels:**
  - Omit needless words. A label that only repeats the type adds noise:
    `remove(_ member: Element)`, not `remove(element member: Element)`.
  - When the first argument completes a prepositional phrase, the label
    starts with the preposition: `move(to: point)`, `load(from: url)`.
  - Omit the first label when the argument completes the base name's
    phrase, or when the function is a value-preserving conversion:
    `contains(element)`, `Int64(value)`.
  - Label every other argument.
- Spell words out. Use a common abbreviation only when it's better known
  than the full word (`url`, `id`, `max`).
- Use inclusive terms. Say primary/secondary or leader/follower instead of
  master/slave, and allowlist/denylist instead of whitelist/blacklist.

## Declarations

- Declare with **`let`** by default, and use `var` only when the value must
  change. The compiler warns about a `var` that's never mutated.
- Let the compiler infer types where the right-hand side makes them obvious:
  `let names = [String]()`, `let limit = 10`. Spell the type out when it
  isn't obvious, or when a literal needs a specific type:
  `let ratio: Double = 1`.
- Use sugared type names: `[Int]`, `[String: Int]`, `Int?`, not `Array<Int>`,
  `Dictionary<String, Int>`, `Optional<Int>`.
- Give every declaration an explicit access level when it's anything other
  than `internal`. Prefer `private` to `fileprivate`.
- Mark classes `final` unless they're designed to be subclassed.
- Put attributes that apply to a whole declaration on the line before it:

  ```swift
  @MainActor
  final class ImageViewModel {
  ```

  Attributes that describe a type or parameter stay inline:
  `completion: @escaping @Sendable () -> Void`.

### Type layout

Order members inside a type as:

1. Nested types and type aliases
2. Static and class properties
3. Instance properties
4. Initialisers
5. Methods

- Put each protocol conformance in its own extension, introduced by a
  `// MARK: - ProtocolName` comment. The conformance and its members stay
  together and are easy to find.
- Don't leave empty or unused members, `init`s that only call `super`, or
  commented-out code.

## Statements and expressions

- Don't put parentheses around `if`, `guard`, `while` or `switch`
  conditions.
- Use `guard` to exit early, so the main path stays at the shallowest
  indentation.
- Unwrap with the shorthand when the name stays the same: `if let image {`,
  `guard let data else {`.
- Line up `case` labels with the `switch`, without indenting them. Swift
  cases don't fall through, so `fallthrough` is used only when you mean it.
- Use `for … where` instead of an `if` that wraps the whole loop body.
- Leave out `self.` unless the compiler needs it, such as in an `init` that
  shadows a property or in an escaping closure.
- Leave out `return` in single-expression functions, closures and computed
  properties.
- Leave out the type name when the context makes it clear: `.zero`,
  `.reloadIgnoringLocalCacheData`.

### Closures

- Use **trailing closure syntax** only for the last closure argument. When a
  call takes more than one closure, label them all, or use multiple trailing
  closures.
- Never use a trailing closure in the condition of an `if`, `guard` or
  `while`. It's ambiguous to the reader, and sometimes to the compiler.
- Use `$0`-style shorthand only in short, single-line closures. Name the
  parameters when the closure is longer, or when the meaning isn't obvious.
- Leave out the parentheses around closure parameters: `{ item, index in`.

## Comments

- Use `//` for comments, and `///` for documentation. Don't use `/* */`
  comments.
- Comments explain **what** and **why**, not **how**. Good names and small
  functions should make the "how" obvious.
- Use `// MARK: - Section` to divide a file into sections. Xcode and other
  editors show these in their outlines.
- Write a TODO as `// TODO: <issue link> - <what needs doing>`. The link
  gives the context and an owner.

### Documentation comments

Document every public declaration with a `///` comment directly above it.
Start with a one-sentence summary, then add detail and the standard
callouts:

```swift
/// Stores image data in the cache, evicting the oldest entries if needed.
///
/// - Parameters:
///   - data: The encoded image to store.
///   - key: The key to store it under. An existing entry is replaced.
/// - Returns: The number of bytes evicted to make room.
/// - Throws: `CacheError.tooLarge` if `data` exceeds the cache's capacity.
@discardableResult
public func store(_ data: Data, forKey key: String) throws -> Int {
```

- Describe what the declaration does and what it returns, using the summary
  line. Don't repeat the signature.
- Document every parameter, the return value, and every error it can throw.

## Generated and third-party code

Generated sources and vendored third-party code keep their own format and are
excluded from the formatter and linters, so regenerating or updating them
stays a clean replacement.

## Sources

This guide starts from the Swift API Design Guidelines and the Google Swift
Style Guide, and borrows from:

- [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
- [Google Swift Style Guide](https://google.github.io/swift/)
- [swift-format](https://github.com/swiftlang/swift-format)
- [SwiftLint rule directory](https://realm.github.io/SwiftLint/rule-directory.html)
- [The Swift Programming Language](https://docs.swift.org/swift-book/)
