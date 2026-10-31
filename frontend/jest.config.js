module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  // Share RTL's DOM event/async wrappers with user-event even when npm installs
  // two DOM Testing Library versions. Otherwise React updates escape act().
  moduleNameMapper: {
    '^@testing-library/dom$': require.resolve('@testing-library/dom', {
      paths: [require.resolve('@testing-library/react')],
    }),
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  testPathIgnorePatterns: ['/node_modules/'],
};
