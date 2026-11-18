/** Defer the media decoder/controller bundle until a viewer actually opens. */
export const loadHls = () => import('hls.js').then(module => module.default);
