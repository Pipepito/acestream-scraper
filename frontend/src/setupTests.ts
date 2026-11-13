import './i18n';
// React Router 7 uses the browser Encoding API; jsdom needs Node's implementation.
import { TextDecoder, TextEncoder } from 'node:util';

Object.assign(globalThis, { TextDecoder, TextEncoder });

// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom has no media stack: HTMLMediaElement.play() is a "not implemented"
// stub that returns undefined and logs to the virtual console. Components
// that autoplay a <video> (the stream player) would fill the test output
// with those traces, so resolve playback quietly instead.
if (typeof window !== 'undefined') {
  window.HTMLMediaElement.prototype.play = function play(): Promise<void> {
    return Promise.resolve();
  };

  // From version 27, jsdom answers `:focus-visible` itself, and answers false for
  // focus that a test moved with the Tab key, where every browser answers true.
  // The component library falls back to its own keyboard tracking when the
  // selector is not supported, which is how earlier jsdom versions behaved. Keep
  // that behaviour, so keyboard focus still opens tooltips in tests.
  const nativeMatches = Element.prototype.matches;
  Element.prototype.matches = function matches(this: Element, selectors: string): boolean {
    if (selectors === ':focus-visible') {
      throw new SyntaxError("':focus-visible' is decided by the component library in tests");
    }
    return nativeMatches.call(this, selectors);
  };
}
