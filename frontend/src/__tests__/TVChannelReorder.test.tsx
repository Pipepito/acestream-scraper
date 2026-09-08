import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import TVChannelReorder from '../components/TVChannelReorder';
import TVChannelFilters from '../components/TVChannelFilters';
import { TVChannel } from '../types/tvChannelTypes';
const channels = [{ id: 1, name: 'News' }, { id: 2, name: 'Sports' }, { id: 3, name: 'Films' }] as TVChannel[];
it('keeps advanced filters collapsed and reports active hidden filters', () => {
  const change = jest.fn();
  render(<TVChannelFilters channels={channels} filters={{ number: 'yes' }} onChange={change} />);
  expect(screen.getByRole('textbox', { name: 'Search' })).toBeVisible();
  expect(screen.queryByRole('combobox', { name: 'Country' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Advanced filters (1 active)' }));
  expect(screen.getByRole('combobox', { name: 'Country' })).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }));
  expect(change).toHaveBeenCalledWith({});
});
it('previews keyboard reordering and saves the full list with its original order', async () => {
  const save = jest.fn().mockResolvedValue(undefined);
  render(<TVChannelReorder channels={channels} onSave={save} onCancel={jest.fn()} />);
  fireEvent.keyDown(screen.getByRole('button', { name: 'Drag Films' }), { key: 'ArrowUp' });
  expect(within(screen.getByRole('list')).getAllByRole('listitem')[1]).toHaveTextContent('Films');
  expect(save).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Save order' }));
  await waitFor(() => expect(save).toHaveBeenCalledWith([1, 3, 2], [1, 2, 3]));
});
it('supports dropping a handle onto another row', () => {
  render(<TVChannelReorder channels={channels} onSave={jest.fn()} onCancel={jest.fn()} />);
  const dataTransfer = { setData: jest.fn(), effectAllowed: '', dropEffect: '' };
  fireEvent.dragStart(screen.getByRole('button', { name: 'Drag News' }), { dataTransfer });
  fireEvent.drop(within(screen.getByRole('list')).getAllByRole('listitem')[2], { dataTransfer });
  expect(within(screen.getByRole('list')).getAllByRole('listitem')[2]).toHaveTextContent('News');
});
it('retains the draft on failure and can cancel', async () => {
  const cancel = jest.fn();
  render(<TVChannelReorder channels={channels} onSave={jest.fn().mockRejectedValue(new Error('Failed to save order'))} onCancel={cancel} />);
  fireEvent.click(screen.getByRole('button', { name: 'Move News down' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save order' }));
  expect(await screen.findByRole('alert')).toBeVisible();
  expect(within(screen.getByRole('list')).getAllByRole('listitem')[1]).toHaveTextContent('News');
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(cancel).toHaveBeenCalledTimes(1);
});
