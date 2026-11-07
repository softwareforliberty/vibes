# JavaScript Tools

The free/open source tools that lint, format and check JavaScript code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with HTML and CSS) |
| [ESLint](https://eslint.org/) | MIT | Linting, Auditing | Linting for bugs and unsafe patterns |
| [TypeScript](https://www.typescriptlang.org/) compiler (`tsc`) | Apache-2.0 | Linting | Optional: checking JSDoc type annotations |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [npm](https://github.com/npm/cli) (`npm audit`) | Artistic-2.0 | Auditing | Checking packages against the npm advisory database |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Knip](https://knip.dev/) | ISC | Code quality | Finding unused files, exports and dependencies |
| [c8](https://github.com/bcoe/c8) | ISC | Code quality | Measuring test coverage |
| [StrykerJS](https://stryker-mutator.io/docs/stryker-js/introduction/) | Apache-2.0 | Code quality | Mutation testing |
| [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) | MIT | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.prettierrc.json`](.prettierrc.json) | Prettier |
| [`eslint.config.js`](eslint.config.js) | ESLint |
| [`tsconfig.json`](tsconfig.json) | `tsc`, for the optional type check |
| [`.npmrc`](.npmrc) | npm (`npm audit`) |
| [`knip.json`](knip.json) | Knip |
| [`.c8rc.json`](.c8rc.json) | c8 |
| [`stryker.config.json`](stryker.config.json) | StrykerJS |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/javascript.yaml`](.opengrep/javascript.yaml) | Opengrep |

## Configuration

Code must pass both checks with **no errors or warnings**:

```sh
npx prettier --check .
npx eslint .
```

`.prettierrc.json`, shared by JavaScript, HTML and CSS:

```json
{
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "endOfLine": "lf"
}
```

`eslint.config.js` (ESLint's flat config format):

```js
import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser }, // globals.node for Node.js code
    },
    rules: {
      curly: ['error', 'all'],
      eqeqeq: ['error', 'always'],
      'func-style': ['error', 'declaration', { allowArrowFunctions: true }],
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-param-reassign': 'error',
      'no-shadow': 'error',
      'no-throw-literal': 'error',
      'no-var': 'error',
      'object-shorthand': 'error',
      'prefer-arrow-callback': 'error',
      'prefer-const': 'error',
      'prefer-object-has-own': 'error',
      'prefer-promise-reject-errors': 'error',
      'prefer-template': 'error',
    },
  },
];
```

- `eslint.config.js` is an ES module, like all code in this guide, so the
  project's `package.json` sets `"type": "module"`.
- Prettier owns layout. Don't hand-format code it will rewrite, and don't
  argue with its output in review. ESLint checks only for bugs and unsafe
  patterns, so the two never conflict.
- Optional type checking: add `// @ts-check` to the top of a file to check
  its [JSDoc](coding-style.md#comments) types in the editor, or run
  `npx tsc` to check every file with the settings in `tsconfig.json`. The
  source stays plain JavaScript.

`tsconfig.json`, for the optional type check:

```json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "nodenext",
    "types": ["node"],
    "strict": true,
    "allowJs": true,
    "checkJs": true,
    "noEmit": true
  },
  "include": ["src"]
}
```

- Install `typescript` and `@types/node` as dev dependencies, so `npx tsc`
  runs the project's compiler.
- `allowJs` and `checkJs` check the JSDoc types in `.js` files, and
  `noEmit` stops `tsc` writing any output.
- `types` loads the Node.js types, which the tests need. TypeScript 6 and
  later load no `@types` package unless it's listed here.

## Auditing

### Security analysis

The ESLint [configuration](#configuration) already rejects `eval()`,
implied `eval()` (strings passed to `setTimeout()`) and `new Function()`.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

The starter rules in
[`.opengrep/javascript.yaml`](.opengrep/javascript.yaml) reject markup
assigned to `innerHTML` or `outerHTML`, markup passed to
`insertAdjacentHTML()`, and shell commands run with `exec()`, as the
[idioms](idioms.md#the-dom) forbid. Add a rule for each new unsafe pattern
you find.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `package-lock.json`, `yarn.lock` and
`pnpm-lock.yaml` and checks every pinned version against the OSV database.

```sh
osv-scanner scan source -r .
```

`npm audit` checks the same lockfile against the npm advisory database, and
comes with npm. [`.npmrc`](.npmrc) sets `audit-level=low`, so it fails on any
vulnerability rated low or above:

```sh
npm audit
```

```ini
audit-level=low
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
lizard -l javascript -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format javascript --min-tokens 50 --exit-code 1 src
```

### Dead code

Knip follows the imports from each entry point and reports files nothing
imports, exports nothing uses, and dependencies in `package.json` that no
file needs. Every export is [named](coding-style.md#imports-and-exports), so
an unused one shows up by name.

```sh
npx knip
```

Knip finds the test files, and the tools a project uses, from the
`package.json` scripts that run them. Run the checks on this page from
scripts, such as `"test": "c8 node --test"`, or Knip reports them as unused.

Knip reads Node.js entry points from `package.json`. For browser code, list
each page's entry module in `knip.json`:

```json
{
  "entry": ["src/main.js"],
  "project": ["src/**/*.js"]
}
```

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

c8 reads the coverage V8 collects natively, so the code runs unmodified.
It reads the minimums from [`.c8rc.json`](.c8rc.json):

```sh
npx c8 node --test
```

```json
{
  "check-coverage": true,
  "branches": 80,
  "lines": 80
}
```

### Mutation testing

StrykerJS makes small changes to the code, such as turning `>=` into `>`,
and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. A full run is slow, so
`scripts/audit` mutates only the source files changed since the base
branch, and skips the run when there are none:

```sh
files=$(git diff --name-only --diff-filter=d origin/main... \
  -- 'src/*.js' ':!*.test.js' | paste -sd, -)
[ -z "$files" ] || npx stryker run --mutate "$files"
```

Install it as development dependencies. This guide was checked with
StrykerJS 10.1.1:

```sh
npm install --save-dev @stryker-mutator/core@10.1.1 \
  @stryker-mutator/tap-runner@10.1.1
```

The TAP runner runs each test file under Node.js, so it works with
`node --test` and needs no test framework. It records which test files
reach each mutant, and runs only those. The settings are in
[`stryker.config.json`](stryker.config.json):

```json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "testRunner": "tap",
  "tap": {
    "testFiles": ["src/**/*.test.js"]
  },
  "reporters": ["clear-text", "progress"],
  "thresholds": { "high": 90, "low": 80, "break": 80 }
}
```

`break` makes the run exit non-zero when the mutation score, the share of
mutants the tests kill, is under 80%. That's the same bar as coverage.
Some mutants can't be killed, because they don't change what the code
does, so 100% is rarely reachable; 80% leaves room for them and still
fails a change whose tests check little.

The report prints each survivor with its file, line and a diff:

```text
[Survived] EqualityOperator
src/price.js:7:7
-     if (total >= 100) {
+     if (total > 100) {
```

Read it as a missing test: here, no test passes exactly 100, so the
boundary isn't pinned down. Write the test that fails on the mutant, not
one that just runs the line. `NoCoverage` means no test reaches the line at
all. If a mutant can't change behaviour, disable it on that line with a
`// Stryker disable next-line` comment naming the mutator and the reason,
rather than writing a test that contorts the code.

### Architecture

dependency-cruiser follows the imports between the project's own modules
and checks them against rules, so the core can't come to depend on its edges.
It's how JavaScript projects
[enforce their layers](../../../architecture/README.md#enforce-it).

Install it as a development dependency
(`npm install --save-dev dependency-cruiser`). It exits non-zero when any
rule with `error` severity is broken:

```sh
npx depcruise src
```

It reads its rules from `.dependency-cruiser.js` in the repository root. They
depend on each project's layers, so there's no template for them here. The
directory names are examples: replace them with the layers in the project's
`design.md`.

```js
export default {
  forbidden: [
    {
      name: 'core-not-to-edges',
      comment: "The core doesn't depend on the edges.",
      severity: 'error',
      from: { path: '^src/core/' },
      to: { path: '^src/(adapters|cli)/' },
    },
    {
      name: 'no-circular',
      comment: 'Modules form no import cycles.',
      severity: 'error',
      from: {},
      to: { circular: true },
    },
  ],
};
```

The edges may import the core, and the report names each broken rule with
the import that breaks it.

## Sources

- [StrykerJS documentation](https://stryker-mutator.io/docs/stryker-js/introduction/)
