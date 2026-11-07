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
      '@graphql-eslint/description-style': 'off',
      '@graphql-eslint/input-name': [
        'error',
        { checkInputType: true, caseSensitiveInputType: false },
      ],
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
      '@graphql-eslint/strict-id-in-types': [
        'error',
        { exceptions: { suffixes: ['Error', 'Payload'] } },
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
