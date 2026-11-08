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
  await screen.findByText('1 record · 1 channel · 0 invalid · 0 duplicates');
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

test('dense HTML falls back to raw source before building the visual document', () => {
  render(<RecipeBuilder preview={jest.fn()} />);
  fireEvent.change(screen.getByLabelText('HTML, text or JSON sample'), { target: { value: '<div></div>'.repeat(10001) } });
  fireEvent.click(screen.getByRole('tab', { name: 'Visual picker' }));
  expect(screen.getByText(/too much markup for visual rendering/)).toBeInTheDocument();
  expect(screen.queryByTitle('Source visual picker')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('tab', { name: 'Raw source' }));
  expect(screen.getByLabelText('HTML, text or JSON sample')).toHaveValue('<div></div>'.repeat(10001));
});

test('retains a dirty recipe and localized success feedback without repeating a pending save', async () => {
  const { act } = await import('@testing-library/react');
  const { default: i18n } = await import('../i18n');
  let finish!: () => void;
  const save = jest.fn(() => new Promise<void>(resolve => { finish = resolve; }));
  const state = jest.fn();
  render(<RecipeBuilder initialRecipe={validateRecipe(catalogue[1].recipe)} onSave={save} onDraftState={state} preview={jest.fn().mockResolvedValue(result)} />);
  fireEvent.change(screen.getByLabelText('Recipe name'), { target: { value: 'My original recipe' } });
  expect(state).toHaveBeenLastCalledWith({ dirty: true, pending: false });
  fireEvent.change(screen.getByLabelText('HTML, text or JSON sample'), { target: { value: catalogue[1].sample } });
  fireEvent.click(screen.getByRole('button', { name: 'Test sample' }));
  await screen.findByText('1 record · 1 channel · 0 invalid · 0 duplicates');
  fireEvent.click(screen.getByRole('button', { name: 'Save to source' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save to source' }));
  expect(save).toHaveBeenCalledTimes(1);
  expect(state).toHaveBeenLastCalledWith({ dirty: true, pending: true });
  await act(async () => finish());
  expect(await screen.findByText('Recipe saved. Run the source scrape when ready.')).toBeVisible();
  expect(state).toHaveBeenLastCalledWith({ dirty: false, pending: false });
  try {
    await act(async () => { await i18n.changeLanguage('es'); });
    expect(screen.getByDisplayValue('My original recipe')).toBeInTheDocument();
    expect(screen.getByText('Se ha guardado la receta. Ejecuta la extracción de la fuente cuando quieras.')).toBeVisible();
    expect(save).toHaveBeenCalledTimes(1);
  } finally { await act(async () => { await i18n.changeLanguage('en'); }); }
});
