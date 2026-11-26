const { TestEnvironment } = require('jest-environment-jsdom');

// React Router's data router uses the Fetch standard for local navigations too.
// Use Node's native implementation; jsdom does not provide these browser APIs.
const web = { Request, Response, Headers, AbortController, AbortSignal };
module.exports = class BrowserEnvironment extends TestEnvironment {
  async setup() {
    await super.setup();
    Object.assign(this.global, web);
  }
};
