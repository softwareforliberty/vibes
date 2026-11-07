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
