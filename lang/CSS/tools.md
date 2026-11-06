# CSS Tools

The free/open source tools that lint, format and check CSS code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with HTML and JavaScript) |
| [Stylelint](https://stylelint.io/) with [stylelint-config-standard](https://github.com/stylelint/stylelint-config-standard) | MIT | Linting, Auditing, Code quality | Linting for errors, modern notation, naming, unsafe URLs and selector complexity |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [PurgeCSS](https://purgecss.com/) | MIT | Code quality | Reporting selectors no page uses |

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

Stylesheets must pass both checks with **no errors or warnings**:

```sh
npx prettier --check "**/*.css"
npx stylelint "**/*.css"
```

`.prettierrc.json`, shared by CSS, HTML and JavaScript:

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

`.stylelintrc.json`:

```json
{
  "extends": ["stylelint-config-standard"],
  "rules": {
    "at-rule-disallowed-list": ["import"],
    "declaration-no-important": true,
    "function-url-scheme-allowed-list": ["data", "https"],
    "max-nesting-depth": [
      0,
      { "ignoreAtRules": ["container", "layer", "media", "supports"] }
    ],
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

- Prettier owns layout. Stylelint (since version 15) checks only for errors
  and conventions, not layout, so the two never conflict.
- The standard config's class-name pattern allows only kebab-case. The
  override above also allows the BEM `__element` and `--modifier` parts used
  by the [naming rules](coding-style.md#naming).
- The other overrides enforce rules from the [style guide](coding-style.md)
  and [idioms](idioms.md): no `@import` (combine files in the build
  instead), no nesting, short selectors with low specificity, and no
  `!important`. They also give the auditing and complexity checks below.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of CSS, and Opengrep doesn't
parse it. Stylelint covers the main risk: CSS can load resources from other
sites. `function-url-scheme-allowed-list` allows only relative, `https:` and
`data:` URLs in `url()`, and `at-rule-disallowed-list` bans `@import`, so a
stylesheet can't pull in code from an unpinned source.

### Dependency vulnerabilities

CSS has no package manager, so there are no third-party dependencies to
audit. Stylesheets installed through npm are audited with the
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

CSS has no functions, so there's no cyclomatic complexity to measure. Its
equivalent is selector complexity, which Stylelint limits:
`selector-max-compound-selectors`, `selector-max-specificity` and
`max-nesting-depth` keep every selector short and easy to override, as the
[selector rules](coding-style.md#selectors) require.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format css --min-tokens 50 --exit-code 1 .
```

### Dead code

Report selectors that no page or script uses. Treat the report as a review
list rather than a gate: a class that JavaScript adds at run time is only
found when its full name appears in the scanned files.

```sh
npx purgecss --config purgecss.config.js
```

`purgecss.config.js` lists the stylesheets to check and the pages and
scripts that use them, and `rejected` adds each file's unused selectors to
the report:

```js
export default {
  content: ['**/*.html', '**/*.js'],
  css: ['**/*.css'],
  rejected: true,
};
```

The file is an ES module, so the project's `package.json` sets
`"type": "module"`, as for the [JavaScript tools](../JavaScript/tools.md).

### Coverage

CSS has no executable code, so there's no coverage to measure.
