# C++ Idioms and Principles

How to write C++ well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep C++ code correct, safe and maintainable. It builds on the
[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines).
Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. Prefer the obvious version unless profiling proves it too slow.
- **Let the type system do the work.** Catch mistakes at compile time
  instead of at run time. A strong type, a `const` or a concept is a check
  the compiler runs for free on every build.
- **Every resource is owned by an object.** Memory, files, locks and sockets
  are released by a destructor, never by a remembered call.
- **Say what you mean.** Choose the construct that states the intent: an
  algorithm instead of a raw loop, `std::optional` instead of a magic value,
  `std::unique_ptr` instead of a commented `// caller frees`.
- **Keep scope small.** Give variables, functions and classes the narrowest
  visibility that works.
- **Never invoke undefined behaviour.** An optimising compiler is free to
  assume it never happens, and "it works on my compiler" isn't correctness.

## Resource management (RAII)

- **Tie every resource to an object's lifetime.** The constructor acquires
  it, and the destructor releases it. Releases then happen on every path,
  including early returns and exceptions.
- **Never call `new` or `delete` directly.** Use `std::make_unique`,
  `std::make_shared` and the standard containers.
- **Follow the rule of zero.** Build classes from members that already
  manage themselves (`std::string`, `std::vector`, `std::unique_ptr`), so the
  compiler-generated copy, move and destructor are correct.
- **Otherwise follow the rule of five.** A class that defines or deletes any
  of the destructor, copy constructor, copy assignment, move constructor or
  move assignment declares all five.
- Wrap C resources in a `std::unique_ptr` with a custom deleter, instead of
  writing a new class for each one:

  ```cpp
  struct FileCloser {
    void operator()(std::FILE *file) const { std::fclose(file); }
  };

  using UniqueFile = std::unique_ptr<std::FILE, FileCloser>;
  ```

### Ownership

| Type | Meaning |
| --- | --- |
| `std::unique_ptr<T>` | Sole owner. The default for heap objects |
| `std::shared_ptr<T>` | One of several owners, when no single owner clearly outlives the others |
| `std::weak_ptr<T>` | Observes a shared object without keeping it alive. Breaks reference cycles |
| `T *` | Non-owning, and may be null |
| `T &` | Non-owning, and never null |

- **Raw pointers and references never own.** Anything that must be freed is
  held by a smart pointer or a container.
- Pass a smart pointer to a function only to transfer or share ownership. A
  function that just uses the object takes `T &` or `T *`.
- Prefer `std::unique_ptr`. A `std::shared_ptr` costs an atomic count on every
  copy, and makes it hard to tell when the object dies.

## Lifetimes

- **Views don't own.** `std::string_view` and `std::span` point into someone
  else's data. Don't return one into a temporary or a local, and don't store
  one in a member unless the API comment states how long the data must live.
- Never return a pointer or reference to a local variable.
- A lambda that captures by reference must not outlive the scope it was
  created in. Capture by value, or capture an owning pointer, when it escapes.
- **Know what invalidates iterators.** Inserting into a `std::vector` can move
  every element. Don't hold iterators, pointers or references into a
  container across a call that may change it.
- **Treat a moved-from object as empty.** Only assign to it or destroy it.

## Passing and returning values

| Parameter is… | Cheap to copy (a few words or less) | Expensive to copy |
| --- | --- | --- |
| Read only | `T` | `const T &` |
| Kept by the callee (a "sink") | `T`, then `std::move` it into place | `T`, then `std::move` it into place |
| Read and modified | `T &` | `T &` |

- **Return results; don't use output parameters.** Return a struct to hand
  back several values. Returning by value is cheap: the compiler elides or
  moves the copy.
- Don't write `return std::move(local);`. It blocks copy elision.
- Use `std::optional<T>` for a value that may be absent, instead of a magic
  value or a null pointer.
- Use `std::variant` for a value that is exactly one of several types,
  instead of a union and a tag.

## Error handling

- **Use exceptions when a function can't do its job** and the immediate
  caller can't reasonably recover: a constructor that can't establish its
  invariant, or a resource that can't be acquired. RAII makes the unwinding
  safe.
- **Return `std::expected` (C++23) or an equivalent result type for failures
  callers routinely handle on the spot**, such as invalid input or a missing
  key. Mark functions returning one `[[nodiscard]]`.
- Throw by value, catch by `const` reference, and throw types derived from
  `std::exception`.
- **Destructors, move operations and `swap` never throw**, and are marked
  `noexcept`. Containers rely on non-throwing moves to stay efficient and
  correct.
- **Give every operation at least the basic guarantee**: if it throws,
  nothing leaks and every object is still valid. Give the strong guarantee
  (no change on failure) where it's cheap, for example with copy-and-swap.
- Catch an exception only where you can handle it, or at a boundary: `main`,
  a thread's entry function, or a callback called from C.
- **Never let an exception cross a C or callback boundary.** Catch it there
  and convert it into an error value.
- Don't use exceptions for ordinary control flow.

### Errors versus bugs

- An **error** is something that can happen in a correct program: a missing
  file, bad input, a dropped connection. Report it with an exception or a
  result type.
- A **bug** is a broken assumption inside the program. Catch it with
  `assert()`, or `static_assert` when it can be checked at compile time.
- Never use `assert()` to validate input from outside the program. Asserts
  vanish when `NDEBUG` is defined, and so do any side effects inside them.

## Const and compile-time code

- **Make everything `const` that can be**: variables, member functions,
  references and pointers to data that isn't modified. `const` documents
  intent, and the compiler enforces it.
- A member function that doesn't change the object's observable state is
  `const`. Use `mutable` only for internals that don't affect that state,
  such as a cache or a mutex.
- Use `constexpr` for values and functions that can be computed at compile
  time, and `consteval` when they must be.
- Check assumptions about types and sizes with `static_assert`.

## Classes and interfaces

- **Use a class to maintain an invariant.** The constructor establishes it,
  and every public member function preserves it. Data without an invariant is
  a plain `struct`.
- Keep data members private, and the public interface small. Every public
  function is a promise you must keep.
- **A polymorphic base class has a public virtual destructor**, or a protected
  non-virtual one. Otherwise deleting through a base pointer is undefined
  behaviour.
- **Prevent slicing.** Delete copying in polymorphic base classes, and pass
  polymorphic objects by reference or pointer.
- Prefer composition to inheritance. Inherit to share an interface, not to
  reuse an implementation.
- Prefer non-member, non-friend functions for operations that only need the
  public interface. The class stays smaller, and its encapsulation stronger.
- Overload operators only where the meaning is obvious. Use `= default` for
  `operator==` and `operator<=>` when member-wise comparison is right.
- Hide implementation details behind a pointer (the pimpl idiom) when a
  header must stay stable, or when its dependencies are expensive to compile.

## Templates and generic code

- **Constrain templates with concepts.** Errors then point at the call site,
  and the requirements are part of the interface:

  ```cpp
  template <std::unsigned_integral T>
  bool IsPowerOfTwo(T value) {
    return value != 0 && (value & (value - 1)) == 0;
  }
  ```

- Use the standard concepts (`std::integral`, `std::ranges::range`, …) before
  writing your own.
- Prefer `constexpr` functions and `if constexpr` to template
  metaprogramming. Ordinary code is easier to read and debug.
- Write generic code only when there are at least two real uses for it.
- Use type erasure (`std::function`, `std::any`, or a small hand-written
  wrapper) at API boundaries where templates would leak into every caller.

## Containers, algorithms and strings

- **Use `std::vector` by default.** Contiguous storage is cache-friendly, and
  usually beats node-based containers even for inserts. Use `std::array` when
  the size is fixed at compile time.
- **Prefer algorithms to raw loops.** `std::ranges::sort`,
  `std::ranges::find_if` and friends name the intent, and are hard to get
  wrong.
- Use a range-based `for` loop when you need every element. Use an index only
  when you need the index.
- Call `reserve()` when you know roughly how many elements are coming.
- Write `'\n'`, not `std::endl`. `std::endl` also flushes the stream, which is
  slow.
- Take read-only string parameters as `std::string_view`, and store strings
  as `std::string`.

## Integers and undefined behaviour

- **Mixing signed and unsigned integers causes silent bugs.** Compare across
  them with `std::cmp_less` and friends, and get a signed size with
  `std::ssize()`.
- Brace initialisation rejects narrowing conversions. Where you narrow on
  purpose, use `static_cast`, and check the range first if it can overflow.
- **Check for overflow before the arithmetic, not after.** Signed overflow is
  undefined behaviour, so a check that runs afterwards may be optimised away.

Code must never rely on undefined behaviour. The most common traps:

| Trap | Instead |
| --- | --- |
| Signed integer overflow | Check the bounds first |
| Indexing out of bounds | Check the index, or iterate with algorithms and range-for |
| Dereferencing a null, dangling or moved-from pointer | Use references for non-null values, and smart pointers for ownership |
| Using a view or reference after its data is gone | Keep the owner alive longer than every view |
| Reading an uninitialised variable | Initialise every variable where it's declared |
| Reinterpreting an object through a pointer of another type | Use `std::bit_cast` or `std::memcpy` |
| Two threads touching the same data, at least one writing | Protect it with a mutex, or make it atomic |

## Concurrency

- **Use `std::jthread`**, which joins on destruction. Never detach a thread:
  nothing can wait for it, or stop it cleanly.
- **Lock with RAII.** Use `std::scoped_lock`, never bare `lock()` and
  `unlock()` calls. Lock several mutexes with one `std::scoped_lock`, which
  avoids deadlock.
- **Document what protects shared data.** Note the mutex that guards each
  member beside it: `int count_;  // Guarded by mutex_.` Clang's
  `-Wthread-safety` analysis can check these annotations.
- Use `std::atomic` for simple shared counters and flags. **`volatile` is not
  a synchronisation tool**: it makes no promises about atomicity or ordering
  between threads.
- Always wait on a condition variable with a predicate, because wakeups can
  be spurious.
- Prefer passing data between threads to sharing it. Immutable data needs no
  locks.

## Performance

- **Measure before you optimise**, and optimise what the profiler points at.
- Choose the right algorithm and data layout first.
- Avoid accidental copies. Loop with `const auto &` over containers of large
  elements, and move values you no longer need.
- Construct elements in place with `emplace_back` when it avoids a temporary.
- Leave inlining and micro-optimisation to the compiler.
- **Stream large input** with `std::getline` or `read` into a reused buffer,
  rather than reading the whole file into memory.
- **Memory-map a large file that's read at random positions or many times.**
  The standard library can't, so wrap `mmap` (`MapViewOfFile` on Windows) in a
  class that unmaps in its destructor, or use Boost.Interprocess's
  `file_mapping` and `mapped_region`, and view the bytes through `std::span`.
  Don't map for one pass from start to end, where buffered reads are as fast,
  or a file another process may shrink, which crashes the program with `SIGBUS`
  when it's read.

## Sources

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [Clang thread safety analysis](https://clang.llvm.org/docs/ThreadSafetyAnalysis.html)
