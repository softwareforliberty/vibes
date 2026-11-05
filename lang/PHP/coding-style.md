# PHP Coding Style

A general-purpose coding style for PHP projects. It builds on the
[PER Coding Style](https://www.php-fig.org/per/coding-style/), with
[PSR-1](https://www.php-fig.org/psr/psr-1/) naming and
[PSR-4](https://www.php-fig.org/psr/psr-4/) autoloading (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (errors,
types, resources, security and other idioms), see [idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [PHP-CS-Fixer](https://cs.symfony.com/) | MIT | Formatting and style fixes |
| [PHPStan](https://phpstan.org/) | MIT | Static analysis and type checking |

### Configuration

Code must pass both tools with **no errors**:

```sh
vendor/bin/php-cs-fixer fix --dry-run --diff   # check
vendor/bin/php-cs-fixer fix                    # apply fixes
vendor/bin/phpstan analyse
```

`.php-cs-fixer.dist.php` at the project root:

```php
<?php

declare(strict_types=1);

$finder = PhpCsFixer\Finder::create()
    ->in([__DIR__ . '/src', __DIR__ . '/tests']);

return (new PhpCsFixer\Config())
    ->setRiskyAllowed(true)
    ->setRules([
        '@PER-CS' => true,
        'declare_strict_types' => true,
    ])
    ->setFinder($finder);
```

`phpstan.neon` at the project root:

```neon
parameters:
    level: max
    paths:
        - src
        - tests
```

- The baseline language is **PHP 8.2**. That version adds readonly classes,
  which [idioms.md](idioms.md) relies on for value objects, and 8.1 added
  enums.
- `declare_strict_types` is marked "risky" because it changes how PHP
  converts arguments, which is why risky rules are allowed.
- PHPStan runs at its highest level, so every value needs a known type.

## Files

- Use only the `<?php` opening tag. Leave out the closing `?>` in files
  that contain only PHP, so stray whitespace after it can't leak into the
  output.
- Use UTF-8 without a byte-order mark, LF line endings, and end every file
  with a newline.
- No trailing whitespace.
- Put the parts of a file header in this order, each separated by one blank
  line:
  1. the `<?php` tag
  2. the file-level docblock, if any
  3. `declare(strict_types=1);`
  4. the `namespace` declaration
  5. class `use` imports, then function imports, then constant imports
  6. the code
- **One class, interface, trait or enum per file**, named after it, in a
  directory that matches its namespace. That's what PSR-4 autoloading
  expects: `App\Billing\Invoice` lives in `src/Billing/Invoice.php`.
- A file either declares symbols (classes, functions, constants) or has side
  effects (output, changing settings), never both.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs.
- When a list of arguments or parameters doesn't fit on one line, put one
  item per line, end with a trailing comma, and put the closing parenthesis
  on its own line. Adding an item then changes only one line in a diff:

  ```php
  $user = $this->users->create(
      name: $name,
      email: $email,
      roles: ['admin'],
  );
  ```

- Break long method chains with one call per line and the `->` at the start
  of each line.

### Line length

- Keep lines to **80 characters** where you can. The hard limit is **120**.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Blank lines and statements

- One statement per line.
- One blank line between methods, and none at the start or end of a class
  or method body.
- Use single blank lines inside methods, sparingly, to separate logical
  steps.

## Keywords and types

- Write all keywords and type names in lowercase: `true`, `false`, `null`,
  `int`, `string`, `array`.
- Use the short type names: `bool`, not `boolean`; `int`, not `integer`.
- Always use parentheses when creating an object, even with no arguments:
  `new Invoice()`.

## Braces

- Classes, interfaces, traits, enums and functions put the opening brace
  **on its own line**:

  ```php
  final class Invoice
  {
      public function total(): int
      {
          return $this->subtotal + $this->tax;
      }
  }
  ```

- Control structures (`if`, `foreach`, `while`, `switch`, `try`) put the
  opening brace **at the end of the line**, after one space.
- **Always use braces** around the body of a control structure, even a
  single statement. Adding a second line to a body without braces silently
  puts it outside the condition.
- Write `elseif`, not `else if`, so every branch keeps the same shape:

  ```php
  if ($amount < 0) {
      throw new InvalidArgumentException('Amount must not be negative.');
  } elseif ($amount === 0) {
      return;
  } else {
      $this->charge($amount);
  }
  ```

- Indent `case` once inside `switch`, and the body of each `case` once more.
  Mark every intentional fall-through with a `// no break` comment.

## Spacing

- One space after control keywords: `if (`, `foreach (`, `while (`.
- No space between a function name and its parenthesis: `count($items)`.
- No spaces just inside parentheses or brackets: `f($x)`, `$items[0]`.
- One space around binary operators, including `.` for concatenation and
  `=>` in arrays: `$a + $b`, `'Hello, ' . $name`, `['id' => 1]`.
- No space after unary operators: `!$done`, `$i++`.
- One space after a cast: `(int) $value`.
- A return type follows the closing parenthesis with a colon and one space:
  `function total(): int`. A nullable type has no space after the `?`:
  `?string`.
- Closures have a space after `function` and around `use`:
  `function ($item) use ($rate) {`. Arrow functions have a space after
  `fn`: `fn ($item) => $item * $rate`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Namespaces | `StudlyCaps`, starting with a vendor name | `Acme\Billing` |
| Classes, interfaces, traits, enums | `StudlyCaps` | `Invoice`, `HttpClient` |
| Exceptions | `StudlyCaps` ending in `Exception` | `PaymentDeclinedException` |
| Methods, functions, properties, variables | `camelCase` | `sendReminder()`, `$retryCount` |
| Class constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Enum cases | `StudlyCaps` | `Status::Pending` |

- Name an interface for the role it plays (`Clock`, `UserRepository`), and
  each implementation for how it fills it (`SystemClock`,
  `PdoUserRepository`). Callers depend on the role, so it gets the plain
  name.
- Don't prefix private members with `_`. The `private` keyword already says
  it.
- Treat acronyms as words in `StudlyCaps` and `camelCase`: `HttpClient`,
  `parseXml()`. The word boundaries stay visible.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Classes

- Declare visibility on **every** property, constant and method. Code that
  states its visibility can't expose something by accident.
- Put `abstract` or `final` before the visibility, and `static` after it:
  `final public const`, `public static function`.
- Declare one property per statement, with a type. Never use `var`.
- Order class members the same way every time: `use` traits, constants,
  properties, the constructor, then public, protected and private methods.
- Use constructor property promotion for properties that are only set from
  the constructor:

  ```php
  public function __construct(
      private readonly UserRepository $users,
      private readonly Clock $clock,
  ) {}
  ```

- Write an empty body as `{}` on the same line as the closing parenthesis.

## Functions and methods

- Give every parameter, property and return value a type. Use `void` when
  nothing is returned and `never` when the function always throws or exits.
- Put parameters with default values after the ones without.
- Use **named arguments** for flags and optional parameters, so the call
  site says what each value means: `$mailer->send($message, retry: false)`.
- Keep functions short and focused on one thing. A function that needs
  more than a screen probably does more than one job.

## Strings and arrays

- Use **single quotes** unless the string needs interpolation or escape
  sequences. A double-quoted string then signals that something inside it
  is special.
- Wrap interpolated variables in braces: `"Hello, {$user->name}"`. It
  marks exactly where the variable ends.
- Use the short array syntax `[]`, never `array()`.
- Write multi-line arrays with one item per line and a trailing comma.

## Comments and docblocks

- Use `//` for single-line comments and `/* ... */` for longer ones on
  their own lines. Use `/** ... */` only for docblocks.
- Comments explain **why**, not **what**. The code already says what it
  does.
- Don't leave commented-out code. Version control keeps the history.
- Write a docblock only to add something the signature can't say: a
  description, `@throws`, or a more precise type such as
  `@param list<string> $names` or `@return array<string, int>`. A docblock
  that only repeats the declared types is noise:

  ```php
  /**
   * Sends a reminder to every customer with an overdue invoice.
   *
   * @param list<Invoice> $invoices
   *
   * @throws MailerException if the mail server rejects a message
   */
  public function sendReminders(array $invoices): void
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
both tools, so updates from upstream stay easy to merge. Install
dependencies with Composer into `vendor/`, and never edit them there.

## Sources

This guide starts from the PER Coding Style and borrows from:

- [PER Coding Style](https://www.php-fig.org/per/coding-style/)
- [PSR-1: Basic Coding Standard](https://www.php-fig.org/psr/psr-1/)
- [PSR-4: Autoloader](https://www.php-fig.org/psr/psr-4/)
- [PHP-CS-Fixer documentation](https://cs.symfony.com/)
- [PHPStan documentation](https://phpstan.org/user-guide/getting-started)
