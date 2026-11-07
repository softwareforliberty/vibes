# Haskell Coding Style

A general-purpose coding style for Haskell projects. It builds on the
[Kowainik Haskell style guide](https://kowainik.github.io/posts/2019-02-06-style-guide)
and Johan Tibell's
[Haskell style guide](https://github.com/tibbe/haskell-style-guide), and
matches the layout that [Fourmolu](https://fourmolu.github.io/) produces (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (types,
totality, errors, effects, laziness and other idioms), see
[idioms.md](idioms.md).

The tools that check Haskell code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **GHC 9.6** with **GHC2021** as the default language. GHC2021
turns on long-stable extensions such as `ImportQualifiedPost`,
`ScopedTypeVariables` and `TypeApplications`, so files don't need to repeat
them in pragmas.

Enable these extra extensions project-wide in the `.cabal` file, not per
file, so every module reads the same way:

```cabal
default-language:   GHC2021
default-extensions:
    DerivingStrategies
    DuplicateRecordFields
    LambdaCase
    OverloadedRecordDot
    OverloadedStrings
```

Any other extension goes in a `{-# LANGUAGE ... #-}` pragma at the top of the
one module that needs it, so its use stays visible.

## Layout

The formatter owns layout. Don't fight it with manual alignment; run it and
commit what it produces.

### Indentation

- Indent with **4 spaces**. Never use tabs; GHC warns about them because
  layout depends on exact columns.
- Indent the body of `where`, `let`, `do`, `case` and guards by one level
  from the line that opens it.
- Put `where` on its own line, indented half a level (2 spaces), with its
  bindings one level in. The keyword then stands out from both the body and
  the bindings:

  ```haskell
  area :: Shape -> Double
  area shape =
      case shape of
          Circle r -> circleArea r
          Rect w h -> w * h
    where
      circleArea r = pi * r * r
  ```

### Line length

- Lines are at most **80 characters**. Fourmolu breaks long expressions to
  fit.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Lists, records and exports

- When a list, record, import list or export list doesn't fit on one line,
  put one item per line with **leading commas**. Adding an item then changes
  one line in a diff:

  ```haskell
  data User = User
      { name :: Text
      , email :: Text
      , roles :: [Role]
      }
  ```

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- One module per file, with the file path matching the module name:
  `Data/Queue.hs` holds `module Data.Queue`.

## Naming

- Functions and values are `camelCase`: `parseConfig`, `maxRetries`.
- Types, constructors, type classes and modules are `PascalCase`:
  `HttpClient`, `ParseError`, `Data.Queue`.
- Treat acronyms as words: `HttpClient`, `parseJson`. Mixed-case acronyms
  run together and are hard to read (`HTTPURLParser`).
- Type variables are short and lowercase: `a`, `m`, `k`, `v`. Use a word
  only when a letter would be unclear: `env`, `err`.
- Name predicates as questions: `isEmpty`, `hasExpired`.
- Use a prime (`config'`) only for a value directly derived from the
  unprimed one, and never more than one prime. `config''` says nothing.
- Name `IO` actions with a verb (`readConfig`) and pure functions for what
  they return (`defaultConfig`).

## Modules

### Exports

- Every module has an **explicit export list**. It documents the module's
  API and lets GHC warn about unused internal definitions.
- Export a type's constructors only when callers should build or match on
  them. Export the type alone (`Queue`, not `Queue (..)`) to keep it
  abstract behind smart constructors.

### Imports

- Import qualified modules with the postfix form, using a short alias:

  ```haskell
  import Data.Map.Strict qualified as Map
  import Data.Text qualified as Text
  ```

- An unqualified import has an **explicit import list**, except for the
  Prelude. Callers can then see where every name comes from:

  ```haskell
  import Control.Monad (forM_, unless, when)
  ```

- Keep imports in one block, sorted alphabetically. Fourmolu sorts them.

## Declarations

### Type signatures

- Every top-level definition has a type signature. The signature is the
  function's documentation and makes type errors point at the right place.
- Give local definitions in `where` a signature when the type isn't obvious
  from one glance.

### Data types

- Declare a deriving strategy on every `deriving` clause, so it's clear
  whether the instance is built in, newtype-derived or generic:

  ```haskell
  newtype UserId = UserId Int
      deriving stock (Show)
      deriving newtype (Eq, Ord)
  ```

- Name record fields without a type prefix and read them with dot syntax
  (`user.email`). `DuplicateRecordFields` lets two records share a field
  name.

### Functions

- Prefer pattern matching and guards to nested `if`. They keep every case
  at the same indentation:

  ```haskell
  classify :: Int -> Text
  classify n
      | n < 0 = "negative"
      | n == 0 = "zero"
      | otherwise = "positive"
  ```

- Put helpers that only one function uses in its `where` clause.
- Use point-free style only when it reads more clearly than naming the
  argument. `sum . map size` is fine; a chain of five operators is not.
- Don't define new operators, except where a library's domain has a
  well-known one. A named function is searchable and self-explanatory.
- Use `LambdaCase` (`\case`) for a lambda that only matches on its argument.

## Strings

- Use `Text` for text and `ByteString` for binary data. `String` is a lazy
  linked list of characters: slow and memory-hungry.
- `OverloadedStrings` lets string literals be `Text` directly.

## Comments

- Comment with `--`. Use `{- ... -}` only to comment out a block during
  development, and never commit it.
- Document every exported definition with a Haddock comment (`-- |`) placed
  before it. Say what it does, what it returns, and any precondition:

  ```haskell
  -- | Remove the oldest item from the queue.
  --
  -- Returns 'Nothing' when the queue is empty.
  pop :: Queue a -> Maybe (a, Queue a)
  ```

- Every module starts with a Haddock module header describing its job.
- Comments explain **why**, not **what**. The types already say what.

## Warnings

Build with `-Wall` plus the extra warnings in [tools.md](tools.md), and fix
every warning. Don't silence one with a pragma unless a comment beside it
says why.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Kowainik and Tibell style guides and borrows from:

- [Kowainik Haskell style guide](https://kowainik.github.io/posts/2019-02-06-style-guide)
- [Johan Tibell's Haskell style guide](https://github.com/tibbe/haskell-style-guide)
- [Fourmolu](https://fourmolu.github.io/)
- [GHC User's Guide: GHC2021](https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/control.html)
- [Haddock documentation](https://haskell-haddock.readthedocs.io/)
