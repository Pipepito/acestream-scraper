/**
 * ESLint config for the Acestream Scraper SPA.
 *
 * Goals: catch real bugs (unused imports, hook rule violations, broken
 * a11y) without blocking on stylistic noise. Pairs with `tsc --noEmit`
 * (called by `npm run build`) so type errors stay the TypeScript
 * compiler's job, not ESLint's.
 */
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  env: {
    browser: true,
    es2022: true,
    node: true,
    jest: true,
  },
  plugins: ['@typescript-eslint', 'react', 'react-hooks', 'jsx-a11y'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  settings: {
    react: { version: 'detect' },
  },
  rules: {
    'react/react-in-jsx-scope': 'off', // Vite + new JSX transform
    'react/prop-types': 'off', // We use TypeScript for prop types
    '@typescript-eslint/no-unused-vars': [
      'warn',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    '@typescript-eslint/no-explicit-any': 'off', // Allow strategic any in services
    '@typescript-eslint/no-empty-function': 'off',
    'no-empty': ['error', { allowEmptyCatch: true }],
  },
  ignorePatterns: [
    'dist',
    'build',
    'node_modules',
    'public',
    'scripts',
    '*.config.js',
    '*.config.ts',
    'vite-env.d.ts',
  ],
  overrides: [
    {
      files: ['**/__tests__/**/*.{ts,tsx}', '**/*.test.{ts,tsx}', 'src/setupTests.ts', 'src/testUtils/**/*.{ts,tsx}'],
      env: { jest: true, node: true },
      plugins: ['testing-library'],
      extends: ['plugin:testing-library/react'],
      rules: {
        '@typescript-eslint/no-non-null-assertion': 'off',
        // Tests legitimately use dynamic require() inside jest.mock factories
        // and isolateModules blocks; the runtime no-var-requires rule does
        // not apply to that style.
        '@typescript-eslint/no-var-requires': 'off',
        '@typescript-eslint/no-require-imports': 'off',
        // The existing test suite uses direct DOM access in a handful of
        // root/portal/legacy-route tests where Testing Library queries are
        // not a clean substitute. Keep the rules on so new violations get
        // surfaced, but downgrade to warnings so the v2 release isn't
        // blocked on stylistic test cleanups. Address in a dedicated
        // test-modernisation pass post-release.
        'testing-library/no-node-access': 'warn',
        'testing-library/no-container': 'warn',
        'testing-library/no-unnecessary-act': 'warn',
        'testing-library/await-async-events': 'warn',
        'testing-library/render-result-naming-convention': 'warn',
        'testing-library/no-wait-for-multiple-assertions': 'warn',
      },
    },
  ],
};
