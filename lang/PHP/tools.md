# PHP Tools

The free/open source tools that lint, format and check PHP code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [PHP-CS-Fixer](https://cs.symfony.com/) | MIT | Formatting | Formatting and style fixes |
| [PHPStan](https://phpstan.org/) | MIT | Linting | Static analysis and type checking |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [Psalm](https://psalm.dev/) | MIT | Auditing | Taint analysis of untrusted input |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [Composer](https://getcomposer.org/) (`composer audit`) | MIT | Auditing | Checking packages against the Packagist advisory database |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [dead-code-detector](https://github.com/shipmonk-rnd/dead-code-detector) | MIT | Code quality | Finding unused classes, methods and constants (PHPStan extension) |
| [PHPUnit](https://phpunit.de/) | BSD-3-Clause | Code quality | Running tests and reporting coverage |
| [PCOV](https://github.com/krakjoe/pcov) | PHP-3.01 | Code quality | Collecting coverage data for PHPUnit |
| [Deptrac](https://github.com/deptrac/deptrac) | MIT | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.php-cs-fixer.dist.php`](.php-cs-fixer.dist.php) | PHP-CS-Fixer |
| [`phpstan.neon`](phpstan.neon) | PHPStan and dead-code-detector |
| [`psalm.xml`](psalm.xml) | Psalm |
| [`phpunit.xml.dist`](phpunit.xml.dist) | PHPUnit |
| [`bin/check-coverage.php`](bin/check-coverage.php) | The coverage check in CI |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/php.yaml`](.opengrep/php.yaml) | Opengrep |

## Configuration

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
includes:
    - vendor/shipmonk/dead-code-detector/rules.neon

parameters:
    level: max
    paths:
        - src
        - tests
```

- `declare_strict_types` is marked "risky" because it changes how PHP
  converts arguments, which is why risky rules are allowed.
- PHPStan runs at its highest level, so every value needs a known type.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Psalm's taint analysis follows user input (`$_GET`, `$_POST`, request
bodies) through the code and reports any path that reaches a dangerous sink
unescaped: SQL, shell commands, HTML output, `unserialize()`. Use Psalm for
taint analysis only; PHPStan stays the type checker and dead-code finder.
Psalm 7 runs its type checks in the same pass, so `psalm.xml` sets the most
lenient error level (8) and turns off its unused-code checks, and the two
tools don't report the same problems.

```sh
vendor/bin/psalm --taint-analysis
```

`psalm.xml` at the project root:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<psalm errorLevel="8" findUnusedCode="false">
  <projectFiles>
    <directory name="src"/>
  </projectFiles>
</psalm>
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `composer.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

A library that doesn't commit `composer.lock` is scanned in CI after
`composer install`, which writes one.

`composer audit` checks the installed packages against the Packagist
security advisories, and needs no extra tool:

```sh
composer audit
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
lizard -l php -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format php --min-tokens 50 --exit-code 1 src
```

### Dead code

dead-code-detector is a PHPStan extension, so it runs as part of
`phpstan analyse` and reports unused classes, methods and constants. PHPStan
already analyses `tests` as well as `src`, so code used only by tests isn't
reported as dead. The `includes` entry in `phpstan.neon` (see
[Configuration](#configuration)) loads its rules.

### Coverage

Measure coverage on every test run, and fail the build when line coverage
falls below 80%. Raise the minimum as coverage grows; never lower it to make
a build pass.

PCOV collects line coverage for PHPUnit, and is faster than a debugger-based
driver. `phpunit.xml.dist` tells PHPUnit which code to measure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit bootstrap="vendor/autoload.php" failOnWarning="true" failOnRisky="true">
  <testsuites>
    <testsuite name="default">
      <directory>tests</directory>
    </testsuite>
  </testsuites>
  <!-- Coverage is measured for this code only. -->
  <source>
    <include>
      <directory>src</directory>
    </include>
  </source>
</phpunit>
```

PHPUnit has no built-in minimum, so write a Clover report and check it:

```sh
php -d pcov.enabled=1 vendor/bin/phpunit --coverage-clover build/clover.xml
php bin/check-coverage.php build/clover.xml 80
```

`bin/check-coverage.php`:

```php
<?php

declare(strict_types=1);

[, $report, $minimum] = $argv;

$metrics = simplexml_load_file($report)->project->metrics;
$total = (int) $metrics['statements'];
$covered = (int) $metrics['coveredstatements'];
$percent = $total === 0 ? 100.0 : 100 * $covered / $total;

if ($percent < (float) $minimum) {
    fwrite(STDERR, sprintf(
        "Line coverage %.1f%% is below %s%%.\n",
        $percent,
        $minimum,
    ));
    exit(1);
}
```

### Architecture

Deptrac sorts the project's classes into layers and checks every dependency
between them against a ruleset, so the core can't come to depend on its
edges. It's how PHP projects
[enforce their layers](../../architecture/README.md#enforce-it).

Install it with `composer require --dev deptrac/deptrac`. It exits non-zero
when any dependency breaks the ruleset:

```sh
vendor/bin/deptrac analyse --no-progress
```

It reads `deptrac.yaml` from the repository root. The rules depend on each
project's layers, so there's no template for them here. The layer names and
directories are examples: replace them with the layers in the project's
`design.md`.

```yaml
---
deptrac:
  paths:
    - src
  layers:
    - name: Core
      collectors:
        - type: directory
          value: src/Core/.*
    - name: Adapters
      collectors:
        - type: directory
          value: src/Adapters/.*
    - name: Cli
      collectors:
        - type: directory
          value: src/Cli/.*
  ruleset:
    Core: ~
    Adapters:
      - Core
    Cli:
      - Core
      - Adapters
```

Each layer in `ruleset` lists the layers it may depend on, and `~` means
none: the core depends on nothing, and the edges may depend on the core.
Deptrac has no cycle check of its own, but a ruleset that only allows
dependencies in one direction keeps the layers from forming a cycle. Cycles
between classes in the same layer aren't checked.

Deptrac caches its results in `.deptrac.cache`; add it to `.gitignore`.
