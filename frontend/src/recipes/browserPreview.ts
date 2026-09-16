import { checkSample, prepareHtml, validateRecipe } from './engine';
import { ExtractionRecipe, RecipePreview } from './types';
export async function browserPreview(recipe: ExtractionRecipe, sample: string): Promise<RecipePreview> {
  checkSample(sample);
  validateRecipe(recipe);
  const html = recipe.mode === 'html' ? prepareHtml(recipe, sample) : undefined;
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL('./preview.worker.ts', import.meta.url), { type: 'module' });
    const stop = () => { clearTimeout(timer); worker.terminate(); };
    const timer = setTimeout(() => { stop(); reject(new Error('Extraction exceeded its time limit; simplify the pattern')); }, 15000);
    worker.onmessage = event => { stop(); if (event.data.error) reject(new Error(event.data.error)); else resolve(event.data.result); };
    worker.onerror = () => { stop(); reject(new Error('Could not run sample preview')); };
    worker.postMessage({ recipe, sample, html });
  });
}
