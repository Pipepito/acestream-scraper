import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import RecipeBuilder from '../recipes/RecipeBuilder';
import catalogue from '../recipes/catalogue.json';
import { validateRecipe } from '../recipes/engine';
const result = { channels: [{ channel_id: 'a'.repeat(40), name: 'News', metadata: {} }], record_count: 1, invalid_count: 0, duplicate_count: 0, issues: [] };

test('requires a passing test before saving and invalidates results after editing', async () => {
  const save = jest.fn().mockResolvedValue(undefined);
  const preview = jest.fn().mockResolvedValue(result);
  render(<RecipeBuilder initialRecipe={validateRecipe(catalogue[1].recipe)} onSave={save} preview={preview} />);
  expect(screen.getByRole('button', { name: 'Save to source' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('HTML, text or JSON sample'), { target: { value: catalogue[1].sample } });
  fireEvent.click(screen.getByRole('button', { name: 'Test sample' }));
  await screen.findByText('1 records · 1 channels · 0 invalid · 0 duplicates');
  fireEvent.click(screen.getByRole('button', { name: 'Save to source' }));
  await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
  await screen.findByText('Recipe saved. Run the source scrape when ready.');
  fireEvent.change(screen.getByLabelText('Recipe name'), { target: { value: 'Edited' } });
  expect(screen.getByRole('button', { name: 'Save to source' })).toBeDisabled();
});

test('standalone never offers a connection to an installed scraper', () => {
  render(<RecipeBuilder preview={jest.fn()} />);
  expect(screen.queryByRole('button', { name: 'Load source URL' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Save to source' })).not.toBeInTheDocument();
  expect(screen.getByText(/helper never connects/)).toBeInTheDocument();
});
