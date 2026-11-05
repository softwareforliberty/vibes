# Ruby Tools

The free/open source tools that lint, format and check Ruby code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [RuboCop](https://rubocop.org/) | MIT | Formatting, Linting, Code quality | Linting, formatting and complexity limits |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [bundler-audit](https://github.com/rubysec/bundler-audit) | GPL-3.0-or-later | Auditing | Checking gems against the Ruby Advisory Database |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [Reek](https://github.com/troessner/reek) | MIT | Code quality | Finding code smells |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Flay](https://github.com/seattlerb/flay) | MIT | Code quality | Finding structurally similar code |
| [debride](https://github.com/seattlerb/debride) | MIT | Code quality | Finding unused methods |
| [SimpleCov](https://github.com/simplecov-ruby/simplecov) | MIT | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.rubocop.yml`](.rubocop.yml) | RuboCop |
| [`.reek.yml`](.reek.yml) | Reek |
| [`.simplecov`](.simplecov) | SimpleCov |
| [`debride_whitelist.txt`](debride_whitelist.txt) | debride |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/ruby.yaml`](.opengrep/ruby.yaml) | Opengrep |

## Configuration

Code must pass RuboCop with **no offences**:

```sh
rubocop        # check
rubocop -a     # apply safe automatic fixes
```

Put the settings in `.rubocop.yml` at the project root:

```yaml
---
AllCops:
  TargetRubyVersion: 3.2
  NewCops: enable

Layout/LineLength:
  Max: 80

Style/AndOr:
  EnforcedStyle: always
```

- New cops are enabled as RuboCop adds them, so the rules keep up with the
  language.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Brakeman isn't listed: its licence restricts commercial use, so it isn't
free/open source.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `Gemfile.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

bundler-audit checks the same lockfile against the Ruby Advisory Database,
and also flags gem sources fetched over insecure `http://` or `git://` URLs:

```sh
bundle-audit check --update
```

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

Fail the build on any function with a cyclomatic complexity over 10 or more
than 60 lines of code. A function past either limit is hard to test and
should be split.

```sh
lizard -l ruby -C 10 -L 60 -w lib
```

RuboCop's `Metrics` cops already hold methods to tighter limits than these,
so lizard acts as a backstop for code where a cop has been disabled.

Reek finds design smells the metrics miss, such as feature envy, data
clumps and utility functions:

```sh
reek lib
```

`.reek.yml` turns off Reek's statement-count and parameter-count checks,
because RuboCop's `Metrics` cops already enforce those limits:

```yaml
---
detectors:
  # RuboCop's Metrics cops already limit method length and parameter
  # lists, so Reek doesn't report the same problems a second time.
  TooManyStatements:
    enabled: false
  LongParameterList:
    enabled: false
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format ruby --min-tokens 50 --exitCode 1 lib
```

Flay compares the shape of the code rather than its text, so it also catches
copies where only the names or literal values changed:

```sh
flay lib
```

### Dead code

debride lists methods that are never called. Ruby is dynamic, so it can't see
calls made through `send` or metaprogramming: confirm each finding before
deleting it, and list methods that are called indirectly in a whitelist
file.

```sh
debride --whitelist debride_whitelist.txt lib
```

`debride_whitelist.txt` lists one method name per line. It starts empty;
add a name only after confirming the method is called indirectly.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

SimpleCov reads its settings from `.simplecov` when it's required, so
require it at the top of the test helper, before any application code loads:

```ruby
# frozen_string_literal: true

require 'simplecov'
```

`.simplecov`:

```ruby
# frozen_string_literal: true

SimpleCov.start do
  enable_coverage :branch
  minimum_coverage line: 80, branch: 80
end
```
