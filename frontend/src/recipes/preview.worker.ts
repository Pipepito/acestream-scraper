import { extractPrepared, validateRecipe } from './engine';
self.onmessage = event => {
  try { self.postMessage({ result: extractPrepared(validateRecipe(event.data.recipe), event.data.sample, event.data.html) }); }
  catch (error) { self.postMessage({ error: (error as Error).message }); }
};
