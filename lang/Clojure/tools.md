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

## Recommended setup

Format, then check. Code must pass with **no warnings** and no findings.

```sh
clojure -M:cljfmt check
clj-kondo --lint src test --fail-level warning
```

Add the formatter as an alias in `deps.edn`:

```clojure
{:aliases
 {:cljfmt {:deps {dev.weavejester/cljfmt {:mvn/version "0.13.0"}}
           :main-opts ["-m" "cljfmt.main"]}}}
```

Configure clj-kondo in `.clj-kondo/config.edn`, turning on the linters the
style guide relies on:

```clojure
{:linters {:missing-docstring {:level :warning}
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
jscpd --format clojure --min-tokens 50 --exitCode 1 src/
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

```clojure
;; deps.edn
{:aliases
 {:coverage {:extra-paths ["test"]
             :extra-deps {cloverage/cloverage {:mvn/version "1.2.4"}}
             :main-opts ["-m" "cloverage.coverage"
                         "-p" "src" "-s" "test"
                         "--line-fail-threshold" "80"]}}}
```

```sh
clojure -M:coverage
```

cloverage is the only FOSS coverage tool for Clojure. Its releases are
infrequent, so check it still supports your Clojure version before relying
on it.
