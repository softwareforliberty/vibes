# Sass (SCSS) Tools

The free/open source tools that lint, format and check Sass code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Dart Sass](https://sass-lang.com/dart-sass/) | MIT | Linting | Compiling, with deprecations treated as errors |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with CSS, HTML and JavaScript) |
| [Stylelint](https://stylelint.io/) with [stylelint-config-standard-scss](https://github.com/stylelint-scss/stylelint-config-standard-scss) | MIT | Linting, Auditing, Code quality | Linting for errors, modern notation, naming, unsafe URLs, selector complexity and unused private members |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [PurgeCSS](https://purgecss.com/) | MIT | Code quality | Reporting selectors no page uses |
| [True](https://www.oddbird.net/true/) | BSD-3-Clause | Code quality | Unit-testing mixins and functions |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.prettierrc.json`](.prettierrc.json) | Prettier |
| [`.stylelintrc.json`](.stylelintrc.json) | Stylelint |
| [`purgecss.config.js`](purgecss.config.js) | PurgeCSS |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Configuration

Stylesheets must pass all three checks with **no errors or warnings**:

```sh
npx prettier --check "**/*.scss"
npx stylelint "**/*.scss"
npx sass --fatal-deprecation=1.80.0 --no-source-map src/main.scss dist/main.css
```

`--fatal-deprecation=1.80.0` turns every deprecation that Dart Sass 1.80 or
earlier reports into an error, including `@import` and the global built-in
functions. Raise the version each time you upgrade Dart Sass, so newer
deprecations fail the build too.

Prettier uses the same `.prettierrc.json` as the
[CSS tools](../CSS/tools.md#configuration).

`.stylelintrc.json`:

```json
{
  "extends": ["stylelint-config-standard-scss"],
  "rules": {
    "at-rule-disallowed-list": ["extend", "import"],
    "declaration-no-important": true,
    "function-url-scheme-allowed-list": ["data", "https"],
    "max-nesting-depth": [
      0,
      {
        "ignoreAtRules": [
          "container",
          "each",
          "else",
          "for",
          "if",
          "include",
          "layer",
          "media",
          "supports"
        ]
      }
    ],
    "scss/no-global-function-names": true,
    "scss/no-unused-private-members": true,
    "scss/selector-no-union-class-name": true,
    "selector-class-pattern": [
      "^[a-z][a-z0-9]*(-[a-z0-9]+)*(__[a-z0-9]+(-[a-z0-9]+)*)?(--[a-z0-9]+(-[a-z0-9]+)*)?$",
      { "message": "Use BEM in kebab-case: block__element--modifier" }
    ],
    "selector-max-compound-selectors": 2,
    "selector-max-id": 0,
    "selector-max-specificity": "0,3,0"
  }
}
```

- The overrides repeat the [CSS Stylelint rules](../CSS/tools.md#configuration),
  so plain CSS and SCSS are held to the same limits.
- On top of those, they ban `@import` and `@extend`, and global built-in
  functions such as `map-get()`, as the [module rules](coding-style.md#modules)
  and [idioms](idioms.md#mixins-functions-and-placeholders) require.
- `scss/selector-no-union-class-name` rejects class names built with `&`
  (`&__item`), as the [nesting rules](coding-style.md#nesting) require.
- Prettier owns layout, and Stylelint checks only for errors and
  conventions, so the two never conflict.
- stylelint-config-standard-scss supports each new major version of
  Stylelint some time after it ships. Install the Stylelint version its peer
  dependency allows, or `npm install` fails.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of Sass, and Opengrep doesn't
parse it. As in CSS, Stylelint covers the main risk:
`function-url-scheme-allowed-list` allows only relative, `https:` and `data:`
URLs, and `@use` can only load files from the project or installed
packages, never a remote URL.

### Dependency vulnerabilities

Sass has no package manager of its own, so there are no third-party
dependencies to audit here. Sass libraries and Dart Sass itself are
installed through npm and audited with the
[JavaScript tools](../JavaScript/tools.md).

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

Stylesheets have no cyclomatic complexity to measure; Sass's control flow is
limited to small mixins and functions. The equivalent is selector
complexity, which the [Stylelint configuration](#configuration) limits
exactly as for CSS: `selector-max-compound-selectors`,
`selector-max-specificity` and `max-nesting-depth`.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format scss --min-tokens 50 --exit-code 1 src
```

### Dead code

`scss/no-unused-private-members` reports private variables, mixins,
functions and placeholders that their own file never uses. For selectors,
report what no page or script uses from the compiled CSS. Treat the report
as a review list rather than a gate: a class that JavaScript adds at run time
is only found when its full name appears in the scanned files.

```sh
npx purgecss --config purgecss.config.js
```

`purgecss.config.js` lists the compiled stylesheets to check and the pages
and scripts that use them, and `rejected` adds each file's unused selectors
to the report:

```js
export default {
  content: ['**/*.html', '**/*.js'],
  css: ['dist/**/*.css'],
  rejected: true,
};
```

The file is an ES module, so the project's `package.json` sets
`"type": "module"`, as for the [JavaScript tools](../JavaScript/tools.md).

No maintained FOSS tool finds public mixins or functions that no other file
uses.

### Coverage

No maintained FOSS tool measures coverage for Sass. Test every public mixin
and function with True, which runs tests written in Sass and fails the build
when the compiled output doesn't match the expected CSS.
