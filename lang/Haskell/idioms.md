# Haskell Idioms and Principles

How to write Haskell well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Haskell code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Make illegal states unrepresentable.** Spend effort on the types, so
  that wrong programs fail to compile instead of failing at run time.
- **Every function is total.** It returns a value for every input, or its
  type says it might not.
- **Keep effects at the edges.** Pure functions hold the logic; a thin `IO`
  layer talks to the world.
- **Errors are values.** A failure the caller should handle shows up in the
  return type.
- **Clarity beats cleverness.** Reach for the simplest abstraction that
  works. A plain function beats a type class, and a type class beats a
  type-level trick.

## Types

- **Wrap primitive values in a `newtype`** when they have meaning: `UserId`,
  `Email`, `Port`. The compiler then stops you mixing up two `Int`s, at no
  run-time cost.
- **Use smart constructors** for values with rules. Export the type
  without its constructor, plus a function that checks the rules:

  ```haskell
  module Email (Email, mkEmail, emailText) where

  newtype Email = Email Text

  mkEmail :: Text -> Maybe Email
  mkEmail t
      | "@" `Text.isInfixOf` t = Just (Email t)
      | otherwise = Nothing

  emailText :: Email -> Text
  emailText (Email t) = t
  ```

  Every `Email` in the program has then passed the check.
- **Model alternatives as sum types**, not as a record of optional fields.
  `data Payment = Card CardDetails | Invoice InvoiceDetails` can't be both or
  neither; a record with two `Maybe` fields can.
- Use `NonEmpty` for a list that must have at least one element, so
  `head` is safe by construction.
- Use `Map` and `Set` from `containers` for keyed and unique data. A list of
  pairs makes every lookup linear.

## Totality

- **Never call partial functions**: `head`, `tail`, `init`, `last`, `!!`,
  `fromJust`, `read`. Each crashes on some input. Use pattern matching,
  `NonEmpty`, `Map.lookup`, `listToMaybe` or `readMaybe` instead.
- Match every constructor. `-Wincomplete-patterns` (part of `-Wall`) warns
  about a missed case; don't silence it with a catch-all `_` that hides
  constructors added later.
- Don't call `error` or `undefined` for a case that can happen. Reserve
  `error` for a broken invariant, and say which one in the message.

## Errors

- **Return `Maybe`** when there's one obvious way to fail and the caller
  doesn't need to know why.
- **Return `Either`** with a sum type of errors when the caller needs to
  know why:

  ```haskell
  data ConfigError
      = MissingField Text
      | InvalidPort Int
      deriving stock (Show, Eq)

  parseConfig :: Value -> Either ConfigError Config
  ```

- Use exceptions only for failures of the outside world in `IO`: a missing
  file, a dropped connection. Throw them with `throwIO`, never `throw`;
  `throw` in pure code goes off at an unpredictable point under lazy
  evaluation.
- Never catch `SomeException` and carry on. It also catches asynchronous
  exceptions such as thread cancellation and `Ctrl-C`. Catch the specific
  exception type you can handle.
- **Release resources with `bracket`** (or a `with...` function built on
  it), so they're released even when an exception is thrown:

  ```haskell
  withFile path ReadMode $ \h -> do
      contents <- Text.hGetContents h
      pure (parseLines contents)
  ```

## Effects

- **Write the logic as pure functions** and keep `IO` in a thin outer
  layer that reads input, calls the pure core and writes output. Pure
  functions are easy to test and reason about.
- Pass dependencies in as arguments or a record of functions, instead of
  reaching for global state.
- Choose the simplest effect structure that fits: plain `IO` with explicit
  arguments, then `ReaderT Env IO`. Add a monad transformer stack or an
  effect library only when the project already uses one.
- Never use `unsafePerformIO` to fake a pure function. It breaks the
  guarantees every other part of the code relies on.

## Laziness and strictness

Laziness is a feature, but it leaks memory when work piles up unevaluated.

- **Use `foldl'`, never `foldl`.** `foldl` builds a chain of unevaluated
  additions before computing anything.
- **Make record fields strict** with `!` (or `StrictData` in the module),
  unless the field is meant to be lazy:

  ```haskell
  data Stats = Stats
      { count :: !Int
      , total :: !Double
      }
  ```

- Use `Data.Map.Strict`, not `Data.Map.Lazy`, for maps that are updated in
  a loop.
- Accumulate state in a strict way. `modifyIORef'` and `modifyTVar'` force
  the new value; their unprimed versions don't.
- When memory grows unexpectedly, profile with `+RTS -hT` before guessing.

## Type classes

- Write a type class only when several types share behaviour that has laws.
  To pass different behaviour into a function, pass a function or a record
  of functions instead.
- **No orphan instances.** Define an instance in the module that defines
  the class or the type. An orphan changes behaviour depending on what's
  imported.
- Make instances lawful: a `Monoid`'s `<>` is associative, and `mempty` is
  its identity. Code that uses the class relies on the laws.
- Derive `Show` for debugging, but don't parse its output. Use a real
  serialisation format for data that leaves the program.

## Concurrency

- Run concurrent work with the `async` library (`concurrently`,
  `mapConcurrently`, `race`). It cancels the other threads when one fails,
  so no thread is leaked.
- Share state between threads with STM (`TVar`). Transactions compose and
  can't deadlock the way nested locks can.
- Never fork a thread with `forkIO` and forget about it. An exception in it
  is lost and nothing waits for it to finish.

## Performance

- Choose the right data structure first: `Text`, `ByteString`, `Vector`,
  `Map`. Most performance problems are a `String` or a list in the wrong
  place.
- **Measure before you optimise.** Build with profiling and let the profile
  point at the cost centre.
- Add `INLINE` and `SPECIALISE` pragmas only where the profile shows they
  help.

## Testing

- Test pure functions with **property tests** (QuickCheck or Hedgehog).
  A property such as "decoding an encoded value gives it back" checks
  thousands of inputs.
- Use example-based tests (hspec or tasty) for specific cases and
  regressions.
- Keep the `IO` layer thin enough that testing the pure core covers most
  of the logic.

## Sources

- [Kowainik Haskell style guide](https://kowainik.github.io/posts/2019-02-06-style-guide)
- [Johan Tibell's Haskell style guide](https://github.com/tibbe/haskell-style-guide)
- [GHC User's Guide: warnings](https://downloads.haskell.org/ghc/latest/docs/users_guide/using-warnings.html)
- [Control.Exception documentation](https://hackage.haskell.org/package/base/docs/Control-Exception.html)
- [async package](https://hackage.haskell.org/package/async)
