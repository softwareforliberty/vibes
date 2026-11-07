# PHP Idioms and Principles

How to write PHP well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep PHP code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Be strict.** Every file declares `strict_types=1`, every value has a
  type, and PHPStan checks them all. Loose conversions hide bugs.
- **Optimise for the reader.** Code is read far more often than it's
  written. Prefer the plain, obvious version over the clever one.
- **Small objects with one job each.** A class that's hard to name is doing
  too much.
- **Errors should never pass silently.** Throw them, handle them where
  something can be done, and never suppress them.
- **Never trust input.** Everything from a request, a file, a database or
  another service is validated on the way in and escaped on the way out.

## Classes and objects

- **Make classes `final` by default.** Open a class for extension only when
  you've designed it for that. Callers can't depend on internals you never
  meant to expose.
- **Prefer composition to inheritance.** Build objects from collaborators
  passed to the constructor.
- **Depend on interfaces at boundaries**: storage, clocks, mail, HTTP. Code
  that takes a `UserRepository` interface works with a database, an API or
  a test fake.
- Use **readonly classes** for value objects, and return a new object
  instead of changing one:

  ```php
  final readonly class Money
  {
      public function __construct(
          public int $amount,
          public string $currency,
      ) {}

      public function add(Money $other): Money
      {
          if ($other->currency !== $this->currency) {
              throw new CurrencyMismatchException($this, $other);
          }

          return new Money($this->amount + $other->amount, $this->currency);
      }
  }
  ```

- Use **enums** for fixed sets of values, instead of class constants or
  bare strings. A typo then fails at once, and `match` can check every case
  is handled.
- Avoid magic methods (`__get`, `__set`, `__call`). They hide what an object
  can do from readers and from PHPStan.
- **Avoid global and static mutable state**: globals, static properties and
  singletons. They're shared by everything, including tests. Pass objects
  in instead.

## Types

- Give every parameter, property and return value a native type, and add a
  docblock type only where native types can't say enough, such as
  `list<Invoice>` or `array<string, int>`.
- **Prefer objects to associative arrays for structured data.** An array's
  keys aren't checked anywhere. A class's properties are.
- Use **strict comparison**: `===` and `!==`, never `==` and `!=`. Loose
  comparison converts types first, with surprising results. Pass `true` as
  the third argument to `in_array()` and `array_search()` for the same
  reason.
- Use nullable types (`?User`) only when "no value" is a normal outcome, and
  handle `null` straight away with `??`, `?->` or an early return.
- Use `match` instead of `switch` when choosing a value. It compares
  strictly, has no fall-through, and throws if no arm matches.

## Errors and exceptions

- **Throw exceptions for errors.** Don't return `false`, `null` or `-1` to
  signal failure. A caller can forget to check a return value, but an
  exception can't be ignored by accident.
- **Catch the most specific exception you can handle.** Catch `\Throwable`
  only at the top level of the program, where errors are logged and turned
  into a response.
- Keep `try` blocks small, so you only catch exceptions from the line you
  expect to fail.
- **Chain exceptions** when you translate one into another, by passing the
  original as `previous`, so the cause stays in the trace:

  ```php
  try {
      $row = $this->connection->fetch($id);
  } catch (PDOException $e) {
      throw new StorageException("Could not load invoice {$id}.", 0, $e);
  }
  ```

- Give each package its own exception classes, all implementing one marker
  interface. Callers can then catch everything from your package in one
  place.
- **Handle each error at the level that can do something about it**: retry,
  fall back, or report to the user. Lower levels let it propagate.
- **Report each error once.** Code either logs an exception or throws it,
  not both, so one failure doesn't produce a cascade of messages.
- **Never use the `@` error-suppression operator.** It hides the error and
  everything that went wrong after it.
- Report every error level in development, and convert PHP warnings and
  notices into exceptions with an error handler, so nothing fails quietly.
- Use the functions that throw: pass `JSON_THROW_ON_ERROR` to
  `json_decode()` and `json_encode()`, which otherwise return `null` or
  `false` on failure.

## Resources

- Release what you acquire in a `finally` block, so it's released even when
  an exception is thrown:

  ```php
  $handle = fopen($path, 'rb');
  if ($handle === false) {
      throw new FileException("Could not open {$path}.");
  }

  try {
      $header = fread($handle, 512);
  } finally {
      fclose($handle);
  }
  ```

- Wrap related database writes in a transaction, and roll it back in a
  `catch` before rethrowing.
- Use **generators** (`yield`) to process large files or result sets, so
  rows are handled one at a time instead of all held in memory.

## Arrays and iteration

- Use `foreach` for loops with side effects, and `array_map()`,
  `array_filter()` and `array_reduce()` to transform data.
- `array_filter()` keeps the original keys. Wrap it in `array_values()` when
  you need a list.
- Never use `foreach` by reference (`foreach ($items as &$item)`). The
  reference outlives the loop and silently changes the last item later.
  Build a new array instead.
- Use `array_key_exists()` to test whether a key is present. `isset()`
  returns `false` for a key whose value is `null`.

## Dependencies and autoloading

- Manage dependencies with **Composer**, commit `composer.lock` for
  applications, and load classes through its PSR-4 autoloader. Never use
  `require` or `include` to load classes.
- Pass dependencies through the constructor. Don't create them inside the
  class with `new`, and don't fetch them from a global container.

## Security

- **Never build SQL by string concatenation or interpolation.** Use PDO
  prepared statements with bound parameters, so the driver escapes values:

  ```php
  $statement = $pdo->prepare('SELECT * FROM users WHERE email = :email');
  $statement->execute(['email' => $email]);
  ```

  Turn off emulated prepares (`PDO::ATTR_EMULATE_PREPARES => false`) and set
  `PDO::ATTR_ERRMODE` to `PDO::ERRMODE_EXCEPTION`.
- **Escape output for the context it goes into.** For HTML, use
  `htmlspecialchars($value, ENT_QUOTES, 'UTF-8')`, or a template engine
  that escapes by default.
- **Never call `unserialize()` on data you don't trust.** It can create
  arbitrary objects and run their magic methods. Use `json_decode()` for
  data from outside the program.
- Avoid running shell commands. When you must, pass every argument through
  `escapeshellarg()`.
- Never pass input to `eval()`, `extract()`, `include` or `require`, or use
  it as a function or class name.
- Hash passwords with `password_hash()` and check them with
  `password_verify()`. Never store or compare them yourself.
- Use `random_bytes()` and `random_int()` for tokens, never `rand()` or
  `mt_rand()`. Compare secrets with `hash_equals()`, which takes the same
  time however much of the value matches.
- Resolve file paths built from input with `realpath()`, and check they stay
  inside the intended directory before you open them.

## Testable design

- **Pass dependencies in** through the constructor, typed as interfaces.
  Tests can then pass a fake.
- Don't create the current time with `new DateTimeImmutable()` deep in your
  logic. Inject a clock, such as one implementing the PSR-20
  `ClockInterface`.
- Keep the core logic in methods that take values and return values. Push
  I/O to the edges of the program.
- Read superglobals (`$_GET`, `$_POST`, `$_SERVER`) only at the entry point,
  and pass the values on as ordinary arguments or a request object.
- Write tests with PHPUnit.

## Performance

- **Measure before you optimise.** Use a profiler to find the slow part, and
  optimise only that.
- Enable OPcache in production, so scripts are compiled once instead of on
  every request.
- Load related records in one query instead of one query per record.
- Choose the right data structure first. Looking up an array key takes the
  same time however large the array grows, while `in_array()` gets slower
  as the array grows.
- **Stream large input** with `fgets` in a loop, an `SplFileObject` or a
  generator, rather than `file()` or `file_get_contents()`, which read the
  whole file into memory. Copy streams with `stream_copy_to_stream`.

## Sources

- [PHP manual: security](https://www.php.net/manual/en/security.php)
- [PHP manual: `unserialize()` warning](https://www.php.net/manual/en/function.unserialize.php)
- [PHP manual: password hashing](https://www.php.net/manual/en/book.password.php)
- [PSR-20: Clock](https://www.php-fig.org/psr/psr-20/)
- [PHPStan documentation](https://phpstan.org/user-guide/getting-started)
