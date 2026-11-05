# GraphQL Tools

The free/open source tools that lint, format and check GraphQL code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting | Formatting (shared with JavaScript and TypeScript) |
| [ESLint](https://eslint.org/) with [GraphQL-ESLint](https://the-guild.dev/graphql/eslint) | MIT | Linting, Code quality | Linting schemas and operations, and finding unused types and fields |
| [GraphQL Inspector](https://the-guild.dev/graphql/inspector) | MIT | Linting, Auditing, Code quality | Breaking-change checks, operation validation with depth and alias limits, and schema coverage |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Configuration

The examples assume the schema lives in `schema/` and client operations in
`operations/`, as the [file rules](coding-style.md#files) describe. Code must
pass both checks with **no errors or warnings**:

```sh
npx prettier --check "**/*.graphql"
npx eslint "**/*.graphql"
```

Prettier uses the same `.prettierrc.json` as the
[JavaScript tools](../JavaScript/tools.md#configuration).

`.graphqlrc.yml` tells GraphQL-ESLint where the schema and operations are,
so rules can check one against the other:

```yaml
schema: schema/**/*.graphql
documents: operations/**/*.graphql
```

`eslint.config.js`:

```js
import graphqlPlugin from '@graphql-eslint/eslint-plugin';

export default [
  {
    files: ['**/*.graphql'],
    languageOptions: { parser: graphqlPlugin.parser },
    plugins: { '@graphql-eslint': graphqlPlugin },
  },
  {
    files: ['schema/**/*.graphql'],
    rules: {
      ...graphqlPlugin.configs['flat/schema-recommended'].rules,
      '@graphql-eslint/input-name': ['error', { checkInputType: true }],
      '@graphql-eslint/no-unused-fields': 'error',
      '@graphql-eslint/require-description': [
        'error',
        {
          types: true,
          EnumValueDefinition: true,
          FieldDefinition: true,
          InputValueDefinition: true,
        },
      ],
    },
  },
  {
    files: ['operations/**/*.graphql'],
    rules: {
      ...graphqlPlugin.configs['flat/operations-recommended'].rules,
      '@graphql-eslint/selection-set-depth': ['error', { maxDepth: 5 }],
    },
  },
];
```

- The recommended schema rules check the [naming rules](coding-style.md#naming),
  require a reason on every `@deprecated`, and require an `id` field on
  object types. The overrides add the `Input` naming for mutation inputs and
  a description on every type, field, argument and enum value.
- The recommended operation rules reject anonymous operations, check every
  operation against the schema, and report unused fragments and variables.
- Prettier owns layout, and ESLint checks only for errors and conventions,
  so the two never conflict.

## Breaking changes

Compare the schema with the base branch on every change, and fail the build
on a breaking change, as the [evolution rules](idioms.md#evolution) require:

```sh
git worktree add ../base origin/main
npx graphql-inspector diff '../base/schema/**/*.graphql' 'schema/**/*.graphql'
```

GraphQL Inspector sorts changes into breaking, dangerous and safe. Adding an
enum value is reported as dangerous: check that clients have a fallback
before merging it.

## Auditing

### Security analysis

No maintained FOSS tool does security analysis of GraphQL, and Opengrep
doesn't parse it. The closest check is to validate every known operation
against the schema with the same depth and alias limits the server
enforces, as the [security idioms](idioms.md#security) require:

```sh
npx graphql-inspector validate 'operations/**/*.graphql' \
  'schema/**/*.graphql' --maxDepth 5 --maxAliasCount 5
```

This checks only the operations in the repository. The server must still
enforce depth, cost and alias limits at run time, for every request.

### Dependency vulnerabilities

GraphQL has no package manager, so there are no third-party dependencies to
audit. The server and client libraries are audited with the tools of the
language they're written in, such as the
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

GraphQL has no functions, so there's no cyclomatic complexity to measure.
Its equivalent is query depth, which GraphQL-ESLint's `selection-set-depth`
rule and GraphQL Inspector's `--maxDepth` limit to 5 levels.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format graphql --min-tokens 50 --exitCode 1 .
```

### Dead code

GraphQL-ESLint's `no-unreachable-types` rule (in the recommended schema
rules) reports types no query, mutation or subscription can reach, and
`no-unused-fields` reports fields no operation in `operations/` selects.
Deprecate an unused field before removing it, because clients outside the
repository may still use it.

### Coverage

GraphQL has no executable code, so test coverage belongs to the language the
server is written in. GraphQL Inspector can report how much of the schema
the operations use, which helps find fields to deprecate:

```sh
npx graphql-inspector coverage 'operations/**/*.graphql' \
  'schema/**/*.graphql'
```
