# TypeScript Tools

The free/open source tools that lint, format and check TypeScript code, and
how to run them. They enforce the rules in [coding-style.md](coding-style.md)
and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with JavaScript, HTML and CSS) |
| [TypeScript](https://www.typescriptlang.org/) compiler (`tsc`) | Apache-2.0 | Linting | Type checking |
| [ESLint](https://eslint.org/) with [typescript-eslint](https://typescript-eslint.io/) | MIT | Linting, Auditing | Linting for bugs, unsafe types and unsafe patterns |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [npm](https://github.com/npm/cli) (`npm audit`) | Artistic-2.0 | Auditing | Checking packages against the npm advisory database |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Knip](https://knip.dev/) | ISC | Code quality | Finding unused files, exports, types and dependencies |
| [c8](https://github.com/bcoe/c8) | ISC | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.prettierrc.json`](.prettierrc.json) | Prettier |
| [`tsconfig.json`](tsconfig.json) | `tsc` and typescript-eslint |
| [`eslint.config.js`](eslint.config.js) | ESLint |
| [`.npmrc`](.npmrc) | npm (`npm audit`) |
| [`knip.json`](knip.json) | Knip |
| [`.c8rc.json`](.c8rc.json) | c8 |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/typescript.yaml`](.opengrep/typescript.yaml) | Opengrep |

## Configuration

Code must pass all three checks with **no errors or warnings**:

```sh
npx prettier --check .
npx tsc --noEmit
npx eslint .
```

Prettier uses the same `.prettierrc.json` as the
[JavaScript tools](../JavaScript/tools.md#configuration), so TypeScript and
JavaScript are formatted identically.

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "nodenext",
    "types": ["node"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "rewriteRelativeImportExtensions": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

- `strict` turns on every strict check, including `noImplicitAny` and
  `strictNullChecks`. The options after it add checks `strict` leaves out,
  such as treating `items[i]` as possibly `undefined`.
- `types` loads the Node.js types from `@types/node`, which the tests need.
  TypeScript 6 and later load no `@types` package unless it's listed here.
- `verbatimModuleSyntax` makes [`import type`](coding-style.md#imports-and-exports)
  required for type-only imports.
- `erasableSyntaxOnly` rejects `enum`, `namespace` and parameter properties,
  as the [style guide](coding-style.md#forbidden-constructs) requires, so
  Node.js can run the source by stripping the types.
- `rewriteRelativeImportExtensions` turns the `.ts` extension in relative
  imports into `.js` in the compiled output.
- `rootDir` and `outDir` compile `src/` into `dist/` with the same layout.
  TypeScript 6 and later stop with an error if `rootDir` is missing when the
  sources aren't next to `tsconfig.json`.
- For browser code, add `"lib": ["es2022", "dom", "dom.iterable"]` and set
  `"module": "es2022"` with `"moduleResolution": "bundler"` if a bundler
  resolves imports.

`eslint.config.js`:

```js
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      curly: ['error', 'all'],
      eqeqeq: ['error', 'always'],
      'func-style': ['error', 'declaration', { allowArrowFunctions: true }],
      'no-eval': 'error',
      'no-new-func': 'error',
      'no-param-reassign': 'error',
      'no-shadow': 'off',
      'no-var': 'error',
      'object-shorthand': 'error',
      'prefer-arrow-callback': 'error',
      'prefer-const': 'error',
      'prefer-object-has-own': 'error',
      'prefer-template': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/explicit-module-boundary-types': 'error',
      '@typescript-eslint/no-shadow': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
    },
  },
  {
    ...tseslint.configs.disableTypeChecked,
    files: ['**/*.js'],
  },
];
```

- The rules repeat the [JavaScript ESLint rules](../JavaScript/tools.md#configuration),
  except where typescript-eslint replaces a core rule with a type-aware
  version: `no-shadow`, `no-implied-eval`, `no-throw-literal` and
  `prefer-promise-reject-errors`. The `strictTypeChecked` set includes the
  type-aware versions of the last three.
- `strictTypeChecked` also bans `any`, non-null assertions and floating
  promises, as the [style guide](coding-style.md#forbidden-constructs) and
  [JavaScript idioms](../JavaScript/idioms.md#async-code) require.
- The last block turns off type-aware rules for JavaScript files, such as
  `eslint.config.js` itself, which `tsconfig.json` doesn't include.
- `eslint.config.js` is an ES module, like all code in this guide, so the
  project's `package.json` sets `"type": "module"`.
- Prettier owns layout, and ESLint checks only for bugs and unsafe patterns,
  so the two never conflict.

## Auditing

### Security analysis

The ESLint [configuration](#configuration) rejects `eval()`, implied `eval()`
and `new Function()`, and typescript-eslint's `no-unsafe-*` rules stop
`any`-typed outside data from flowing into calls and assignments unchecked.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

The starter rules in
[`.opengrep/typescript.yaml`](.opengrep/typescript.yaml) reject markup
assigned to `innerHTML` or `outerHTML`, markup passed to
`insertAdjacentHTML()`, and shell commands run with `exec()`, as the
[JavaScript idioms](../JavaScript/idioms.md#the-dom) forbid. Add a rule for
each new unsafe pattern you find.

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
lizard -l typescript -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format typescript --min-tokens 50 --exitCode 1 src
```

### Dead code

Knip follows the imports from each entry point and reports files nothing
imports, exports and types nothing uses, and dependencies in `package.json`
that no file needs. The compiler's `noUnusedLocals` and
`noUnusedParameters` options are left off, because ESLint's
`@typescript-eslint/no-unused-vars` (in `strictTypeChecked`) reports the
same problems without blocking a build mid-edit.

```sh
npx knip
```

Knip finds the test files, and the tools a project uses, from the
`package.json` scripts that run them. Run the checks on this page from
scripts, such as `"test": "c8 node --test 'src/**/*.test.ts'"`, or Knip
reports them as unused.

For browser code, list each page's entry module in `knip.json`:

```json
{
  "entry": ["src/main.ts"],
  "project": ["src/**/*.ts"]
}
```

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

Node.js 22.18 and later run the `.ts` tests directly by stripping the types,
which keeps line and column positions intact. c8 reads the coverage V8
collects, so it maps straight back to the source. It reads the minimums
from [`.c8rc.json`](.c8rc.json):

```sh
npx c8 node --test 'src/**/*.test.ts'
```

```json
{
  "check-coverage": true,
  "branches": 80,
  "lines": 80
}
```
