// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom has no media stack: HTMLMediaElement.play() is a "not implemented"
// stub that returns undefined and logs to the virtual console. Components
// that autoplay a <video> (the stream player) would fill the test output
// with those traces, so resolve playback quietly instead.
window.HTMLMediaElement.prototype.play = function play(): Promise<void> {
  return Promise.resolve();
};
