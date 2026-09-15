/** Check before DOM construction; raw samples and worker tests retain 32 MiB support. */
export const MAX_RENDER_BYTES = 2 * 1024 * 1024;
const MAX_MARKUP_TOKENS = 20_000;
export function renderingLimit(sample: string): string | null {
  if (sample.length > MAX_RENDER_BYTES || new Blob([sample]).size > MAX_RENDER_BYTES) {
    return 'This sample is too large for visual rendering. Use Raw source to select a record and generate regex, or copy a smaller channel section for the visual picker. Installed extraction tests still accept sources up to 32 MiB.';
  }
  let tokens = 0;
  for (let index = 0; index < sample.length; index++) {
    if (sample[index] === '<' && ++tokens > MAX_MARKUP_TOKENS) {
      return 'This sample has too much markup for visual rendering. Use Raw source or copy a smaller channel section. Installed extraction tests can still use the full source.';
    }
  }
  return null;
}
