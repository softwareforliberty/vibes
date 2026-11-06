# HTML Tools

The free/open source tools that lint, format and check HTML code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with CSS and JavaScript) |
| [html-validate](https://html-validate.org/) | MIT | Linting | Offline validation, accessibility and best-practice checks |
| [Nu HTML Checker](https://validator.github.io/validator/) (`vnu`) | MIT | Linting | Validation against the HTML standard |
| [axe-core CLI](https://github.com/dequelabs/axe-core-npm) (`@axe-core/cli`) | MPL-2.0 | Auditing | Accessibility testing of rendered pages |
| [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci) | Apache-2.0 | Auditing, Code quality | Accessibility, best-practice and performance audits |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [lychee](https://github.com/lycheeverse/lychee) | Apache-2.0 OR MIT | Code quality | Finding broken links |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.prettierrc.json`](.prettierrc.json) | Prettier |
| [`.htmlvalidate.json`](.htmlvalidate.json) | html-validate |
| [`lighthouserc.json`](lighthouserc.json) | Lighthouse CI |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/html.yaml`](.opengrep/html.yaml) | Opengrep |

## Configuration

Markup must pass all three checks with **no errors**:

```sh
npx prettier --check "**/*.html"
npx html-validate "**/*.html"
java -jar vnu.jar --skip-non-html .
```

`.prettierrc.json`, shared by HTML, CSS and JavaScript:

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

`.htmlvalidate.json`:

```json
{
  "extends": ["html-validate:recommended"],
  "rules": {
    "doctype-style": ["error", { "style": "lowercase" }],
    "void-style": ["error", { "style": "selfclose" }]
  }
}
```

- Prettier owns layout. Don't hand-format markup it will rewrite.
- Prettier writes `<!doctype html>` in lowercase and void elements with a
  closing slash (`<br />`). html-validate is set to expect both, so the
  formatter and the validator agree. In HTML the slash is optional and has
  no effect.
- `vnu` checks against the current standard. html-validate adds rules the
  standard doesn't cover, such as accessibility checks and banned inline
  styles. Run both.

## Auditing

### Security analysis

html-validate's recommended rules already reject inline `style` attributes,
which keeps markup compatible with the
[security rules](idioms.md#security). Opengrep adds checks the validator
can't express: the starter rules in
[`.opengrep/html.yaml`](.opengrep/html.yaml) reject inline `on*` handlers,
`javascript:` URLs and `target="_blank"` links without
`rel="noopener noreferrer"`.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

HTML has no package manager, so there are no third-party dependencies to
audit. Scripts and stylesheets installed through npm are audited with the
[JavaScript tools](../JavaScript/tools.md). Files loaded from a CDN can't be
scanned, so pin each one with an `integrity` hash, as the
[security rules](idioms.md#security) require.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

### Accessibility

Static checks can't see the rendered page, so also test the built pages in a
browser. The axe-core CLI runs the axe rules against a page and fails on any
violation. Lighthouse CI runs Lighthouse's accessibility, best-practice and
performance audits, and fails when a score drops below the preset's limits.

```sh
npx @axe-core/cli http://localhost:8080/ --exit
npx @lhci/cli autorun
```

`lighthouserc.json`:

```json
{
  "ci": {
    "collect": { "staticDistDir": "." },
    "assert": { "preset": "lighthouse:recommended" }
  }
}
```

- Automated tools find only part of all accessibility problems. Keep testing
  with a keyboard and a screen reader, as the
  [accessibility rules](idioms.md#accessibility) describe.

## Code quality

### Complexity

HTML has no functions, so there's no complexity to measure.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format markup --min-tokens 50 --exitCode 1 .
```

### Broken links

Check every link and resource reference in the markup. A broken link is dead
code that visitors can see.

```sh
lychee "**/*.html"
```

### Coverage

HTML has no executable code, so there's no coverage to measure.
