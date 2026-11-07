# Clojure Coding Style

A general-purpose coding style for Clojure projects. It builds on the
community [Clojure Style Guide](https://guide.clojure.style/) and the
defaults of the [cljfmt](https://github.com/weavejester/cljfmt) formatter,
and fills the gaps from other long-lived FOSS Clojure projects (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (data,
pure functions, namespaces, validation and other idioms), see
[idioms.md](idioms.md).

The tools that check Clojure code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Clojure 1.11** on the JVM. That version adds
`parse-long`, `update-vals`, `update-keys` and `:as-alias`, which this guide
relies on. Projects are built with the Clojure CLI and `deps.edn`.

## Source files

- Encode source files in **UTF-8**.
- One namespace per file. The file path matches the namespace, with hyphens
  in the namespace turned into underscores in the path:
  `billing.invoice-lines` lives in `src/billing/invoice_lines.clj`. The
  runtime finds namespaces by this mapping.
- Give every namespace at least two segments (`billing.core`, not `billing`).
  Single-segment namespaces end up in the default Java package, which causes
  clashes.
- Use `.clj` for JVM-only code, `.cljs` for ClojureScript, and `.cljc` only
  for code that genuinely runs on both.

### The ns form

- Start every file with one `ns` form. Put `:require` before `:import`.
- Require every namespace with an alias (`:as`) or with the specific names it
  uses (`:refer`). **Never use `:use` or `:refer :all`.** Names then always
  show where they come from.
- Sort the required namespaces alphabetically, one per line.
- Use the conventional alias for well-known namespaces: `str` for
  `clojure.string`, `set` for `clojure.set`, `io` for `clojure.java.io`.

```clojure
(ns billing.invoice
  (:require
   [billing.tax :as tax]
   [clojure.string :as str])
  (:import
   (java.time Instant)))
```

## Layout

### Indentation

- Indent with **spaces**. Never use tabs.
- Indent the body of a special form or macro (`defn`, `let`, `when`, `fn`) by
  **2 spaces**.
- Line up the arguments of a function call vertically when they span several
  lines. If the first argument is on the next line, indent it 1 space.
- cljfmt applies these rules, so never fight the formatter by hand.

```clojure
(defn total
  [items]
  (reduce +
          0
          (map :price items)))
```

### Line length

- The limit is **80 columns**.
- **Never split a user-visible string** across lines just to fit the limit.
  Messages stay greppable when they're whole.

### Parentheses

- **Gather closing brackets on the last line** of the form. A closing bracket
  never sits alone on its own line.
- No whitespace just inside brackets: `(foo bar)`, not `( foo bar )`.
- Separate top-level forms with **one blank line**.
- Don't put blank lines inside a function, except between the pairs of a
  `let`, `cond` or `case` when grouping makes them easier to read.

### Whitespace

- No trailing whitespace.
- Never more than one blank line in a row.
- End every file with a newline.
- Use commas only inside a map literal on one line, to separate pairs:
  `{:id 1, :name "Ada"}`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Functions, vars, locals, namespaces | `kebab-case` | `total-price`, `billing.invoice` |
| Predicates (return a boolean) | End in `?` | `paid?`, `valid-order?` |
| Functions with side effects that aren't safe in a transaction | End in `!` | `save-order!`, `reset-cache!` |
| Dynamic vars | Wrapped in earmuffs | `*db*`, `*clock*` |
| Conversion functions | `a->b` | `order->row` |
| Protocols, records, types | `UpperCamelCase` | `Storage`, `OrderRow` |
| Unused bindings | Start with `_` | `_request`, `_` |

- Write keywords in `kebab-case` too, and **namespace-qualify** keywords that
  leave the namespace: `:billing.order/id`.
- Treat acronyms as words in `UpperCamelCase` names: `HttpClient`, not
  `HTTPClient`. Every JVM language in these guides follows the same rule.
- Don't repeat the namespace in a var's name. In `billing.invoice`, write
  `total`, not `invoice-total`; callers read it as `invoice/total`.

## Definitions

- Write `defn` with the docstring after the name and the parameter vector on
  its own line.
- Mark helpers private with `defn-`. Use `^:private` metadata for other
  private vars.
- Give each arity of a multi-arity function its own line, ordered from fewest
  to most parameters.
- Put a `:pre`/`:post` map, if any, right after the parameter vector.

```clojure
(defn apply-discount
  "Returns `order` with `rate` taken off every line price."
  [order rate]
  (let [discount (fn [line] (update line :price * (- 1 rate)))]
    (update order :lines #(mapv discount %))))
```

## Forms

- Use `when` instead of `(if x (do ...))`, and `when-not` or `if-not` instead
  of wrapping a condition in `not`.
- Use `cond` for more than two branches, and finish it with `:else`.
- Use `case` for dispatch on constants. It's faster and fails loudly on an
  unknown value when no default is given.
- Use the threading macros (`->`, `->>`) for pipelines of three or more
  steps. Don't thread a single call.
- Prefer `#(...)` only for short one-line lambdas with at most one argument
  (`%`). Write `fn` for anything longer, so arguments get names.

## Comments

- Use `;;` for a comment on its own line, indented like the code it
  describes.
- Use `;` for a short comment at the end of a line.
- Use `;;;` for a comment that heads a section of top-level forms.
- Comments explain **why**, not **what**.
- Use `(comment ...)` blocks for REPL examples kept with the code, never for
  disabling real code.

### Docstrings

- Give every public var a docstring. Start it with a complete sentence that
  says what the var does.
- Refer to arguments in backticks: `` `order` ``.
- Indent the second and later lines of a docstring by 2 spaces, so they
  line up under the text after the opening quote.

```clojure
(defn total
  "Returns the sum of every line price in `order`.
  Prices are in the order's currency, before tax."
  [order]
  (transduce (map :price) + 0 (:lines order)))
```

## Generated and third-party code

Generated sources and vendored third-party code keep their own style. Exclude
them from cljfmt and clj-kondo, so updates stay easy to merge.

## Sources

- [The Clojure Style Guide](https://guide.clojure.style/)
- [cljfmt](https://github.com/weavejester/cljfmt)
- [clj-kondo linters](https://github.com/clj-kondo/clj-kondo/blob/master/doc/linters.md)
- [Clojure reference: namespaces](https://clojure.org/reference/namespaces)
