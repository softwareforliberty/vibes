# Perl Tools

The free/open source tools that lint, format and check Perl code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [perltidy](https://metacpan.org/pod/Perl::Tidy) | GPL-2.0-or-later | Formatting | Formatting |
| [Perl::Critic](https://metacpan.org/pod/Perl::Critic) | Artistic-1.0-Perl OR GPL-1.0-or-later | Linting, Auditing, Code quality | Linting, security policies, complexity limits and unused code |
| [CPAN::Audit](https://metacpan.org/pod/CPAN::Audit) | Artistic-1.0-Perl OR GPL-1.0-or-later | Auditing | Checking CPAN dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Devel::Cover](https://metacpan.org/pod/Devel::Cover) | Artistic-1.0-Perl OR GPL-1.0-or-later | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.perltidyrc`](.perltidyrc) | perltidy |
| [`.perlcriticrc`](.perlcriticrc) | Perl::Critic |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Formatting

perltidy owns layout. Put the settings in `.perltidyrc`, starting from the
*Perl Best Practices* preset:

```text
--perl-best-practices
--nostandard-output
--nostandard-error-output
--warning-output
```

Format files in place, deleting the backup copies:

```sh
perltidy -b -bext='/' lib/My/App/UserStore.pm
```

In CI, fail on any file perltidy would change:

```sh
git ls-files '*.pl' '*.pm' '*.t' | while read -r file; do
  perltidy --assert-tidy -o /dev/null "$file" || exit 1
done
```

Don't hand-format code perltidy will rewrite, and don't argue with its
output in review.

## Linting

Code must pass Perl::Critic with **no violations**:

```sh
perlcritic lib bin t
```

Put the settings in `.perlcriticrc`:

```ini
severity = 3
verbose  = 8

# use v5.36 turns on warnings, which this policy doesn't recognise in
# every Perl::Critic release. It already treats use v5.12 or later as
# turning on strict.
[-TestingAndDebugging::RequireUseWarnings]

# Signatures look like prototypes to this policy.
[-Subroutines::ProhibitSubroutinePrototypes]

[Subroutines::ProhibitExcessComplexity]
max_mccabe = 10
```

Severity 3 adds the *Perl Best Practices* policies on top of the most
serious ones. Never silence a policy with a `## no critic` comment without
naming the policy and giving the reason on the same line.

## Auditing

### Security analysis

No Opengrep or other FOSS taint analyser supports Perl. Perl::Critic's
policies are the closest check, and severity 3 in the
[linting](#linting) config includes the ones that catch the unsafe patterns
in [idioms.md](idioms.md#security):

- `InputOutput::ProhibitTwoArgOpen` and
  `InputOutput::ProhibitBarewordFileHandles` for unsafe `open` calls.
- `BuiltinFunctions::ProhibitStringyEval` for string `eval`.
- `InputOutput::ProhibitBacktickOperators` for shell commands built from
  strings.

Run programs that handle untrusted input under taint mode (`-T`) in their
tests too, so Perl itself rejects unchecked data.

### Dependency vulnerabilities

The OSV database has no CPAN ecosystem, so use CPAN::Audit. It checks the
dependencies a project declares against the CPAN Security Advisory
database, and fails when any has a known vulnerability:

```sh
cpan-audit deps .
```

Commit the `cpanfile.snapshot` lockfile for applications, so the audited
versions are the ones that get installed.

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

Fail the build on any subroutine with a cyclomatic complexity over 10. A
subroutine past that limit is hard to test and should be split. The
`Subroutines::ProhibitExcessComplexity` setting in the
[linting](#linting) config enforces it.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format perl --min-tokens 50 --exitCode 1 lib
```

### Dead code

Perl::Critic's `Subroutines::ProhibitUnusedPrivateSubroutines` and
`Variables::ProhibitUnusedVariables` policies report unused private
subroutines and variables. No tool finds unused public subroutines, because
Perl can call them by name at run time.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
cover -delete
HARNESS_PERL_SWITCHES=-MDevel::Cover prove -lr t
cover -report text
```

Devel::Cover has no minimum of its own. Check the branch total in its
summary in CI, and fail the build when it's under 80%.
