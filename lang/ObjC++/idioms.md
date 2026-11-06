# Objective-C++ Idioms and Principles

How to write Objective-C++ well. [coding-style.md](coding-style.md) covers how
code looks. This guide covers how it's designed: how to bridge Objective-C and
C++ cleanly, and keep ownership, errors and threads correct across the
boundary. It builds on the
[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines),
Apple's Cocoa conventions and the
[Clang ARC specification](https://clang.llvm.org/docs/AutomaticReferenceCounting.html).
Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. Prefer the obvious version unless profiling proves it too slow.
- **Objective-C++ is a bridge, not a home.** Write core logic in pure C++ or
  pure Objective-C, and use `.mm` files only for the thin layer that connects
  them. Mixed code is harder to read and slower to compile, and a header
  that contains C++ can't be imported by plain Objective-C files.
- **Convert at the boundary.** Strings, collections, errors and ownership
  change form in exactly one place: the bridging layer. Neither side should
  see the other's types.
- **Each language keeps its own idioms.** C++ code uses RAII and smart
  pointers. Objective-C code uses ARC and Cocoa patterns. Don't force one
  language's patterns onto the other.
- **Never invoke undefined behaviour.** An optimising compiler is free to
  assume it never happens, and "it works on my compiler" isn't correctness.

## Keeping the boundary clean

- **Keep C++ out of Objective-C headers.** A public header that `.m` files or
  Swift import declares only Objective-C. Hold the C++ parts in instance
  variables declared in the `@implementation`, which only the `.mm` file sees:

  ```objc
  // ABCSpellChecker.mm
  #import "ABCSpellChecker.h"

  #include <memory>

  #include "myproject/spell/checker.h"

  @implementation ABCSpellChecker {
    std::unique_ptr<myproject::spell::Checker> _checker;
  }
  ```

- **Keep Objective-C out of C++ headers.** A C++ class that needs to call into
  Objective-C declares an abstract interface in plain C++. A `.mm` file
  implements it.
- Wrap each direction of the bridge in one small class or set of functions,
  so the rest of the code never mixes the languages.

## Ownership across the boundary

| Holding… | Inside… | Use |
| --- | --- | --- |
| A C++ object | An Objective-C object | A value instance variable, or `std::unique_ptr` when it's large or optional |
| A shared C++ object | An Objective-C object | `std::shared_ptr` instance variable |
| An Objective-C object | A C++ object (in `.mm`-only code) | A plain object pointer, which ARC keeps strong |
| A back-reference to an Objective-C owner | A C++ object | A `__weak` pointer |

- **C++ instance variables are constructed when the object is allocated, and
  destroyed after `dealloc` runs.** They must be default-constructible. Don't
  use them from `dealloc` expecting them to be gone, or from `+alloc`
  expecting them to be set up.
- **Under ARC, object pointers in C++ classes are strong references.** Copying
  the C++ object retains the Objective-C object, and destroying it releases
  it. You never need a smart pointer around an Objective-C object.
- **Break retain cycles across the boundary too.** If an Objective-C object
  owns a C++ object that points back to it, the back-pointer is `__weak`.
- **Never call `new` or `delete` directly.** Use `std::make_unique`,
  `std::make_shared` and the standard containers.

## Blocks and lambdas

- **A block copies the C++ objects it captures**, using their copy
  constructors. Capture a large object through a `std::shared_ptr`, or a
  reference whose lifetime you control, instead.
- **A lambda that captures an Objective-C object holds a strong reference to
  it**, just like a block. If `self` stores the lambda, capture `self` weakly
  and turn it back into a strong reference at the start of the lambda.
- Pass blocks to Objective-C APIs, and lambdas or `std::function` to C++
  APIs, so each side sees its own idiom.

```objc
__weak __typeof__(self) weakSelf = self;
_checker->SetCallback([weakSelf](const std::string &word) {
  ABCSpellChecker *strongSelf = weakSelf;
  if (!strongSelf) {
    return;
  }
  [strongSelf reportMisspelledWord:ToNSString(word)];
});
```

## Strings and collections

- **Convert `NSString` to `std::string` by copying the UTF-8 bytes
  immediately.** The pointer `UTF8String` returns is only valid while the
  string lives, and it's `nil` for a `nil` string. Constructing a
  `std::string` from a null pointer is undefined behaviour:

  ```objc
  std::string ToStdString(NSString *string) {
    if (!string) {
      return std::string();
    }
    return std::string(string.UTF8String);
  }
  ```

- **Convert `std::string` to `NSString` with an explicit length**, so
  embedded null characters survive. The result is `nil` when the bytes aren't
  valid UTF-8, so callers must check it:

  ```objc
  NSString *_Nullable ToNSString(const std::string &text) {
    return [[NSString alloc] initWithBytes:text.data()
                                    length:text.size()
                                  encoding:NSUTF8StringEncoding];
  }
  ```

- Convert collections element by element at the boundary. Don't expose
  `std::vector` through an Objective-C API, or `NSArray` through a C++ one.
- Standard containers of Objective-C object pointers (`std::vector<NSString *>`)
  are fine inside `.mm` code. ARC retains each element.

## Error handling

- **Never let an exception cross a language boundary.** Mixing the two
  exception models is fragile, and ARC code isn't exception-safe by default,
  so objects leak while an exception unwinds through it. Catch C++ exceptions
  in the bridging layer, and convert them into an `NSError` or an error
  value.
- **Convert errors at the boundary.** An Objective-C API reports failures the
  Cocoa way: return `NO` or `nil`, and fill in an `NSError **` parameter that
  comes last. A C++ API reports them the C++ way: an exception, or a result
  type such as `std::expected`.
- **Check the return value, not the error.** Only a `NO` or `nil` result
  means failure.
- **The error pointer may be `NULL`.** Check it before writing through it.
- Objective-C exceptions are for programmer errors only. C++ exceptions
  report errors the immediate caller can't reasonably handle.

```objc
- (nullable NSArray<NSString *> *)suggestionsForWord:(NSString *)word error:(NSError **)error {
  try {
    std::vector<std::string> results = _checker->Suggest(ToStdString(word));
    NSMutableArray<NSString *> *suggestions = [NSMutableArray array];
    for (const std::string &result : results) {
      NSString *suggestion = ToNSString(result);
      if (suggestion) {
        [suggestions addObject:suggestion];
      }
    }
    return [suggestions copy];
  } catch (const std::exception &) {
    if (error) {
      *error = [NSError errorWithDomain:ABCSpellCheckerErrorDomain
                                   code:ABCSpellCheckerErrorInternal
                               userInfo:nil];
    }
    return nil;
  }
}
```

### Errors versus bugs

- An **error** is something that can happen in a correct program: a missing
  file, bad input, a dropped connection. Report it with the API's own error
  mechanism.
- A **bug** is a broken assumption inside the program. Catch it with
  `assert()` in C++ code, or `NSAssert()` in Objective-C code.
- Never use assertions to validate input from outside the program. They can
  be compiled out, along with any side effects inside them.

## Nullability and optional values

- Objective-C APIs state what may be `nil` with nullability annotations.
- C++ APIs state it with types: a reference is never null, a pointer may be,
  and `std::optional` holds a value that may be absent.
- **Check for `nil` before handing an Objective-C value to C++.** Sending a
  message to `nil` silently returns zero, but C++ code receiving a null
  pointer or an empty value may not expect it.

## Concurrency

- **Protect shared mutable state with one mechanism**: a serial dispatch
  queue, a `std::mutex`, or another lock. Don't guard the same data with two
  different mechanisms. Document beside it which one guards it.
- Update UI only on the main thread.
- A C++ callback that may run on another thread must hop to the main queue
  before touching Objective-C UI objects.
- **`volatile` is not a synchronisation tool.** It makes no promises about
  atomicity or ordering between threads.
- Prefer passing immutable data between threads to sharing mutable objects.

## Performance

- **Measure before you optimise**, and optimise what the profiler points at.
- Converting strings and collections at the boundary copies them. Cross the
  boundary with whole batches instead of one element at a time, when
  profiling shows the cost matters.

## Sources

- [Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [Clang: Objective-C Automatic Reference Counting](https://clang.llvm.org/docs/AutomaticReferenceCounting.html)
- [Apple: Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
