# Clojure Tools

The free/open source tools that lint, format and check Clojure code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [cljfmt](https://github.com/weavejester/cljfmt) | EPL-1.0 | Formatting | Formatting: applies [Layout](coding-style.md#layout) automatically |
| [clj-kondo](https://github.com/clj-kondo/clj-kondo) | EPL-1.0 | Linting, Code quality | Static analysis, including unused code and missing docstrings |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [nvd-clojure](https://github.com/rm-hull/nvd-clojure) | MIT | Auditing | Checking the resolved classpath against known vulnerabilities, using OWASP Dependency-Check |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [cloverage](https://github.com/cloverage/cloverage) | EPL-1.0 | Code quality | Measuring test coverage |
| [clj-depend](https://github.com/fabiodomingues/clj-depend) | EPL-2.0 | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.cljfmt.edn`](.cljfmt.edn) | cljfmt, and Calva when it formats |
| [`.clj-kondo/config.edn`](.clj-kondo/config.edn) | clj-kondo |
| [`deps.edn`](deps.edn) | Clojure CLI: the `cljfmt` and `coverage` aliases |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/clojure.yaml`](.opengrep/clojure.yaml) | Opengrep |

`deps.edn` is a template: merge its aliases into the project's own
`deps.edn`.

## Recommended setup

Format, then check. Code must pass with **no warnings** and no findings.

```sh
clojure -M:cljfmt check
clj-kondo --lint src test --fail-level warning
```

Add the formatter and coverage aliases in [`deps.edn`](deps.edn):

```clojure
;; Template: merge these aliases into the project's deps.edn.
{:aliases
 {:cljfmt {:deps {dev.weavejester/cljfmt {:mvn/version "0.16.6"}}
           :main-opts ["-m" "cljfmt.main"]}
  :coverage {:extra-paths ["test"]
             :extra-deps {cloverage/cloverage {:mvn/version "1.2.4"}}
             :main-opts ["-m" "cloverage.coverage"
                         "-p" "src" "-s" "test"
                         "--fail-threshold" "80"]}}}
```

Configure cljfmt in [`.cljfmt.edn`](.cljfmt.edn). It turns on every
whitespace rule the [Layout](coding-style.md#layout) section asks for:

```clojure
{:insert-missing-whitespace? true
 :remove-consecutive-blank-lines? true
 :remove-multiple-non-indenting-spaces? true
 :remove-surrounding-whitespace? true
 :remove-trailing-whitespace? true}
```

Configure clj-kondo in [`.clj-kondo/config.edn`](.clj-kondo/config.edn),
turning on the linters the style guide relies on, including the 80-column
line limit:

```clojure
{:linters {:line-length {:level :warning :max-line-length 80}
           :missing-docstring {:level :warning}
           :refer-all {:level :error}
           :use {:level :error}
           :unused-namespace {:level :warning}
           :unused-private-var {:level :warning}
           :unused-binding {:level :warning}
           :single-key-in {:level :warning}}}
```

- Run clj-kondo in the editor too: it's fast enough to lint on every save.
- Turn on `*warn-on-reflection*` in namespaces that call Java (see
  [Java interop](idioms.md#java-interop)), and treat any reflection warning
  as a failure.
- Because the formatter owns layout, never hand-format code it will rewrite.
  Run it before every commit.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Opengrep's Clojure support is experimental: it matches syntax patterns, but
doesn't do taint tracking. Write rules for the calls the idioms forbid, such
as `read-string` on untrusted input (use `clojure.edn/read-string`) and
`eval`.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `pom.xml` and checks every pinned version
against the OSV database.

```sh
osv-scanner scan source -r .
```

- `deps.edn` has no lockfile, and OSV-Scanner doesn't read `deps.edn`.
  Generate a `pom.xml` from it with `clojure -X:deps mvn-pom` and commit it,
  so OSV-Scanner has a file to read. OSV-Scanner resolves its transitive
  dependencies through deps.dev, which needs network access.
- nvd-clojure runs OWASP Dependency-Check against the resolved classpath.
  Use it when the build itself must fail on a vulnerable dependency:

  ```sh
  clojure -Ttools install nvd-clojure/nvd-clojure \
    '{:mvn/version "RELEASE"}' :as nvd
  clojure -J-Dclojure.main.report=stderr -Tnvd nvd.task/check \
    :classpath "\"$(clojure -Spath)\""
  ```

  It needs an NVD API key to download its database.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

No maintained FOSS tool measures the complexity of Clojure functions: lizard
doesn't support Clojure, and clj-kondo has no complexity linter. Review
function size instead, against the [Functions](idioms.md#functions) idioms:
a function that needs a long `let` with many steps should be split.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format clojure --min-tokens 50 --exit-code 1 src/
```

### Dead code

clj-kondo's `:unused-private-var`, `:unused-binding` and `:unused-namespace`
linters report unused private functions, local bindings and requires. With
`--fail-level warning`, each one fails the check. clj-kondo can't see unused
*public* vars, because another project may call them.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

The `coverage` alias in [`deps.edn`](deps.edn) runs cloverage with
`--fail-threshold 80`, which fails the build when line or form coverage falls
below 80%:

```sh
clojure -M:coverage
```

cloverage is the only FOSS coverage tool for Clojure. Its releases are
infrequent, so check it still supports your Clojure version before relying
on it.

### Mutation testing

No maintained FOSS mutation testing tool works for Clojure. mutant, the
best known, last released in 2017 and is archived. Heretic is unreleased
and says it isn't ready for use. clj-mutate has no licence. apophis has
one 0.1 release and no runner or minimum score, and it makes few mutants:
for a function with `>=` and `-`, only `if` turned into `if-not`.

Rely on the [test reviewer](../../../agents/test-reviewer.md) instead,
which checks that each test pins down the behaviour it covers, not just
runs it, and on the coverage minimum in [Coverage](#coverage). When you
write a test, ask what change to the code would still pass it, such as
`>=` turned into `>`, and add the case that catches it.

### Architecture

Check the dependency rules between the project's layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks.
clj-depend reads each namespace's `ns` form and checks its requires against
the layers you define.

Define the layers in `.clj-depend/config.edn`. Each layer lists the layers it
may require; a require of any other layer is a breach. This one stops the
core requiring the edges, which may require the core. The namespace names are
examples: replace them with the layers in the project's `design.md`.

```clojure
{:source-paths #{"src"}
 :layers {:core {:defined-by "^app\\.core(\\.|$)"
                 :accesses-layers #{}}
          :adapters {:defined-by "^app\\.adapters(\\.|$)"
                     :accesses-layers #{:core}}
          :cli {:defined-by "^app\\.cli(\\.|$)"
                :accesses-layers #{:adapters :core}}}}
```

`:defined-by` is a regular expression that may match anywhere in a namespace
name, so anchor it with `^`.

`scripts/check` runs it from the repository root. It prints each breach, such
as `"app.core.pricing" should not depend on "app.adapters.store"`, and exits
non-zero:

```sh
clojure -Sdeps \
  '{:deps {com.fabiodomingues/clj-depend {:mvn/version "0.11.1"}}}' \
  -M -m clj-depend.main
```

- clj-depend also reports two namespaces that require each other. Clojure
  refuses to load any cycle, so loading the code, as the tests do, catches
  longer ones.
- Without `.clj-depend/config.edn`, clj-depend has no layers to check and
  passes, so commit the file.

## Sources

- [mutant](https://github.com/jstepien/mutant)
- [Heretic](https://github.com/parenstech/heretic)
- [clj-mutate](https://github.com/unclebob/clj-mutate)
- [apophis](https://github.com/thomascothran/apophis)
