# Ruby Coding Style

A general-purpose coding style for Ruby projects. It builds on the community
[Ruby Style Guide](https://rubystyle.guide/) and the defaults of
[RuboCop](https://rubocop.org/), which enforces it (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (errors,
resources, objects, security and other idioms), see [idioms.md](idioms.md).

The tools that check Ruby code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Ruby 3.2**. That version adds `Data.define`,
which [idioms.md](idioms.md) relies on for value objects.

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- Line up `end` with the start of the line that opened the block, so each
  block's start and end are easy to match.
- Line up `when` with its `case`, and `rescue` and `ensure` with the
  `begin` or `def` they belong to.
- Break long method chains with one call per line and the **dot at the
  start** of each line. A leading dot shows the line continues the chain:

  ```ruby
  active_names = users
    .select(&:active?)
    .map(&:name)
  ```

### Line length

- Lines are at most **80 characters**.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Whitespace and files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- One blank line between method definitions, and none at the start or end of
  a class or method body.
- Start every file with the magic comment
  `# frozen_string_literal: true`, followed by a blank line. String
  literals are then frozen, which prevents accidental mutation and saves
  allocations.

### One thing per line

- One statement per line. Don't join statements with `;`.
- Write multi-line method bodies across multiple lines. Don't squeeze them
  onto one line with `;`.

## Spacing

- One space around operators, after commas and colons, and after `#` in
  comments: `sum = a + b`, `f(a, b)`, `{ key: value }`.
- No spaces just inside parentheses or square brackets: `f(x)`, `items[0]`.
- One space just inside braces for hash literals and blocks:
  `{ name: 'Ada' }`, `items.map { |item| item * 2 }`.
- No space after `!`, and no space around `..` and `...` in ranges:
  `!done`, `1..10`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Files and directories | `snake_case`, matching the class they define | `user_store.rb` |
| Classes and modules | `CamelCase`, with acronyms in capitals | `UserStore`, `HTTPClient` |
| Methods and variables | `snake_case` | `load_config`, `retry_count` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| Predicate methods | End in `?`, no `is_` or `has_` prefix | `empty?`, `admin?` |

- End a method's name with `!` only when a safer method of the same name
  exists without it, such as `save` and `save!`. The `!` warns the caller
  that this version mutates the receiver or raises.
- Don't prefix readers and writers with `get_` and `set_`. Use `name` and
  `name=`.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Strings

- Use **single quotes** unless the string needs interpolation or escape
  sequences. A double-quoted string then signals that something inside it is
  special.
- Use interpolation, not concatenation: `"#{greeting}, #{name}"`. It reads
  in output order and converts values to strings for you.
- Use a heredoc with `<<~` for multi-line text. It strips the common
  indentation, so the text can be indented with the code.

## Methods

- Put parentheses around a method's parameters when it has any. Leave them
  out when it has none:

  ```ruby
  def full_name(separator: ' ')
    [first_name, last_name].join(separator)
  end

  def admin?
    role == :admin
  end
  ```

- Use parentheses on method calls with arguments, except for methods used as
  language keywords or DSLs: `puts`, `raise`, `require`, `attr_reader`,
  `include`.
- Use **keyword arguments** for optional parameters and flags, so the call
  site names them: `connect(host, timeout: 5)`.
- Keep methods short. Aim for under 10 lines and no more than 5 parameters.
  RuboCop flags longer methods and longer parameter lists.
- Leave out an explicit `return` on the last expression. Ruby returns it
  already.
- Don't use `self.` to call a method on the receiver, except for writers
  (`self.name = value`), which would otherwise create a local variable.

## Conditionals

- Use `&&`, `||` and `!`, never `and`, `or` and `not`. The word forms have
  surprisingly low precedence.
- Use `unless` for a single negative condition, but never with `else`.
  Rewrite those as an `if` with the positive case first.
- Use the modifier form for a single short statement:
  `return if items.empty?`.
- Don't use `then` on multi-line `if` or `case` statements.
- Use the ternary operator only for simple, one-line choices, and never nest
  it.
- Use `&.` (safe navigation) to call a method on something that may be
  `nil`, but don't chain it more than once. A long `&.` chain hides where the
  `nil` came from.

## Blocks

- Use `{ ... }` for single-line blocks and `do ... end` for multi-line ones.
- Use the symbol shorthand when a block calls a single method:
  `names.map(&:upcase)`.
- Name block parameters for what they hold. Use `_` for a parameter you
  don't use.

## Collections

- Use literals: `[]` and `{}`, not `Array.new` and `Hash.new`, unless you
  need a default value.
- Use `%w[]` for arrays of words and `%i[]` for arrays of symbols.
- Use the `key: value` hash syntax when the keys are symbols.
- Don't put a trailing comma after the last item of a multi-line literal.

## Classes and modules

- Order the contents of a class the same way every time:
  1. `extend` and `include`
  2. constants
  3. attribute macros (`attr_reader` and friends)
  4. class methods
  5. `initialize`
  6. public instance methods
  7. `protected`, then `private` methods
- Define class methods with `def self.name`.
- Indent `private` and `protected` to the same level as the methods around
  them, and leave a blank line after each.
- Use `attr_reader` and `attr_writer` instead of hand-written accessors.

## Exceptions

- Raise with the class and message as separate arguments:
  `raise ArgumentError, 'name is required'`.
- When a whole method needs `rescue` or `ensure`, attach it to the `def`
  instead of wrapping the body in `begin ... end`. It saves a level of
  indentation:

  ```ruby
  def read_config(path)
    JSON.parse(File.read(path))
  rescue Errno::ENOENT
    {}
  end
  ```

## Comments

- Comments start with `# ` (hash and one space).
- Comments explain **why**, not **what**. The code already says what it
  does.
- Don't leave commented-out code. Version control keeps the history.
- Give every class and module a comment describing its job. Document public
  methods with [YARD](https://yardoc.org/) tags for parameters, return
  values and raised errors:

  ```ruby
  # Finds a user by ID.
  #
  # @param id [Integer] ID of the user to find
  # @return [User] the matching user
  # @raise [UserNotFoundError] if no user has that ID
  def find(id)
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
RuboCop, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Ruby Style Guide and borrows from:

- [The Ruby Style Guide](https://rubystyle.guide/)
- [RuboCop documentation](https://docs.rubocop.org/rubocop/)
- [YARD tags overview](https://rubydoc.info/gems/yard/file/docs/Tags.md)
