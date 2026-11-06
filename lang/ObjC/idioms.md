# Objective-C Idioms and Principles

How to write Objective-C well. [coding-style.md](coding-style.md) covers how
code looks. This guide covers how it's designed: the idioms and principles
that keep Objective-C code correct, safe and maintainable. It builds on
Apple's Cocoa conventions and the
[Clang ARC specification](https://clang.llvm.org/docs/AutomaticReferenceCounting.html).
Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. Prefer the obvious version unless profiling proves it too slow.
- **Follow the framework's conventions.** Cocoa's naming, memory, error and
  delegation patterns are what other Objective-C developers expect. Code that
  follows them needs less explanation.
- **Make the API state its contract.** Nullability, generics, designated
  initialisers and `readonly` let the compiler check what comments can only
  describe.
- **Prefer immutability.** Immutable objects can be shared freely, between
  objects and between threads.
- **Keep scope small.** Expose the minimum in headers. Everything else stays
  in the `.m` file.

## Memory management (ARC)

All code uses Automatic Reference Counting. ARC inserts the retains and
releases. Your job is to choose the right ownership for each reference, and
to avoid cycles.

| Attribute | Meaning | Use for |
| --- | --- | --- |
| `strong` | Owns the object | The default for object properties |
| `weak` | Doesn't own; becomes `nil` when the object dies | Delegates, parents, and anything that would create a cycle |
| `copy` | Owns a private copy | `NSString`, collections and blocks |
| `assign` | Plain value, no ownership | Scalars (`NSInteger`, `BOOL`, structs) |

- **Use `copy` for types with mutable subclasses** (`NSString`, `NSArray`,
  `NSDictionary`). Otherwise a caller can pass an `NSMutableString`, and
  change it behind your back.
- **Never use `unsafe_unretained` or `assign` for objects.** A dangling
  pointer crashes later, far from the cause. `weak` becomes `nil` instead.
- **Break retain cycles.** Two objects holding strong references to each
  other are never freed. The child, delegate or observer side of the
  relationship is `weak`.
- Use `@autoreleasepool` inside long loops that create many temporary
  objects, so memory is released on each pass instead of at the end.

### Blocks

A block strongly captures every object it uses, including `self`. If `self`
also keeps the block, neither is ever freed.

- When a block is stored by `self`, or by something `self` owns, capture
  `self` weakly. Turn it back into a strong reference at the start of the
  block, and stop if it's already gone:

  ```objc
  __weak __typeof__(self) weakSelf = self;
  self.loader.completion = ^(NSData *data) {
    __typeof__(self) strongSelf = weakSelf;
    if (!strongSelf) {
      return;
    }
    [strongSelf storeImageData:data];
  };
  ```

- A block that runs once and isn't stored (`dispatch_async`, an animation)
  can capture `self` directly.
- Accessing an instance variable inside a block captures `self`. Write
  `self->_count` instead of `_count`, so the capture is visible.
  `-Wimplicit-retain-self` flags the hidden form.

### Core Foundation

- ARC doesn't manage Core Foundation objects. You release what you get from a
  function with `Create` or `Copy` in its name, and don't release anything
  else.
- Cross between the two worlds with explicit bridging casts.
  `CFBridgingRelease()` hands a Core Foundation object to ARC.
  `CFBridgingRetain()` takes one out of ARC. `(__bridge T)` converts without
  any change in ownership.

## Initialisation and teardown

- **Every class has one designated initialiser**, marked
  `NS_DESIGNATED_INITIALIZER`. Every other initialiser calls it, and it calls
  the superclass's designated initialiser.
- **Mark an inherited initialiser that would produce an invalid object
  `NS_UNAVAILABLE`.** For example, `- (instancetype)init NS_UNAVAILABLE;` on
  a class that needs a capacity.
- Assign `self` before testing it:

  ```objc
  - (instancetype)initWithCapacity:(NSUInteger)capacity {
    self = [super init];
    if (self) {
      _capacity = capacity;
      _entries = [[NSMutableDictionary alloc] init];
    }
    return self;
  }
  ```

- **Use instance variables directly in initialisers and `dealloc`**, not
  property accessors. A subclass may override an accessor, and it would run
  on a half-built or half-destroyed object.
- Under ARC, `dealloc` only releases what ARC can't: Core Foundation objects,
  observers and timers. Never call `[super dealloc]`.

## Nullability

- **Annotate every header.** With `NS_ASSUME_NONNULL_BEGIN` in place, mark
  each pointer that may be `nil` as `nullable`. Callers then know what to
  check, and the compiler warns when they pass `nil` where it isn't allowed.
- **Sending a message to `nil` does nothing, and returns zero.** It hides
  bugs as easily as it prevents crashes. Check for `nil` where it means
  something went wrong, instead of relying on the silent zero.
- Never put `nil` in a collection. Use `NSNull` when you need a placeholder.

## Error handling

- **Report recoverable errors with `NSError`.** The method returns `NO` or
  `nil` on failure, and fills in an `NSError **` parameter, which comes last:

  ```objc
  - (nullable NSData *)readImageForKey:(NSString *)key
                                 error:(NSError **)error;
  ```

- **Check the return value, not the error.** A method may write to the error
  pointer even when it succeeds. Only a `NO` or `nil` result means failure.
- **The error pointer may be `NULL`.** Check it before writing through it:

  ```objc
  if (error) {
    *error = [NSError errorWithDomain:ABCImageCacheErrorDomain
                                 code:ABCImageCacheErrorNotFound
                             userInfo:nil];
  }
  return nil;
  ```

- Give each module its own error domain (a prefixed string constant), and its
  error codes an `NS_ENUM`.
- Pass a callee's `NSError` up unchanged, or wrap it in your own error with
  the original under `NSUnderlyingErrorKey`. Don't throw away the cause.
- **Exceptions are for programmer errors only**: a broken precondition or an
  impossible state. Code under ARC isn't exception-safe by default, and
  objects leak while an exception unwinds, so never use them for recoverable
  errors.
- **Never let an exception cross a C or callback boundary.** Catch it there
  and convert it into an error value.
- Check preconditions with `NSParameterAssert()` and `NSAssert()`. Never use
  them to validate input from outside the program. They can be compiled out,
  along with any side effects inside them.

## Immutability and encapsulation

- **Expose immutable types in the public API.** A property returns an
  `NSArray`, even when the class keeps an `NSMutableArray` inside. Return a
  copy, so callers can't change the internals.
- Declare properties `readonly` in the header, and redeclare them `readwrite`
  in the class extension in the `.m` file, when the class needs to set them.
- Keep private properties, methods and protocol conformances in the class
  extension, not the header.
- Never iterate over a mutable collection while changing it. Iterate over a
  copy, or collect the changes and apply them afterwards.

## Protocols, delegates and categories

- **Keep a delegate `weak`.** The delegate usually owns the object it
  delegates for, so a strong reference would create a cycle.
- Before calling an `@optional` protocol method, check that the receiver
  implements it with `respondsToSelector:`.
- **Use a block for a single callback**, and a delegate protocol for several
  related callbacks over an object's lifetime.
- Prefer composition and delegation to subclassing framework classes.
- **Never override an existing method in a category.** If two categories
  define the same method, which one runs is undefined. Add new, prefixed
  methods instead.

## Concurrency

- **Atomic properties don't make a class thread-safe.** They only stop a
  single read or write from tearing. Operations that touch several values
  still race.
- **Protect shared mutable state with one mechanism**: a serial dispatch
  queue or a lock. Document beside each shared property which one guards it.
- Update UI only on the main thread.
- Create singletons with `dispatch_once`, which is thread-safe and runs the
  setup exactly once.
- **`volatile` is not a synchronisation tool.** It makes no promises about
  atomicity or ordering between threads.
- Prefer passing immutable data between threads to sharing mutable objects.

## Notifications and observation

- Remove every observer you add, before it's deallocated.
- Prefer the block-based APIs, and keep the token they return, so removal is
  in one place.
- Use key-value observing sparingly. Its callbacks are hard to trace, and
  observing a key that isn't KVO-compliant fails silently.

## Performance

- **Measure before you optimise**, and optimise what the profiler points at.
- Choose the right algorithm and collection first.
- Don't bypass ARC or message sending for speed unless a profile shows it
  matters.
- **Stream large input** with `NSInputStream` or `NSFileHandle`, rather than
  reading the whole file into memory.
- **Memory-map a large file that's read at random positions or many times**
  with `[NSData dataWithContentsOfFile:options:error:]` and
  `NSDataReadingMappedIfSafe`, which maps the file only where that's safe and
  reads it otherwise. Don't map a file you read once from start to end, where
  buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.

## Sources

- [Apple: Coding Guidelines for Cocoa](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CodingGuidelines/CodingGuidelines.html)
- [Google Objective-C Style Guide](https://google.github.io/styleguide/objcguide.html)
- [Clang: Objective-C Automatic Reference Counting](https://clang.llvm.org/docs/AutomaticReferenceCounting.html)
- [Clang: Nullability attributes](https://clang.llvm.org/docs/AttributeReference.html#nullability-attributes)
