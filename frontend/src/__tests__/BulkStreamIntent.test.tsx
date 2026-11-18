import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import BulkOperations from '../components/BulkOperations';

it('submits one activation request for the whole selection (SRC-F15)', async () => {
  const activate = jest.fn().mockResolvedValue(undefined);
  render(<BulkOperations open onClose={jest.fn()} selectedChannels={[{ id: 'one' }, { id: 'two' }]}
    onBulkEdit={jest.fn()} onBulkDelete={jest.fn()} onBulkActivate={activate} />);
  fireEvent.click(screen.getByRole('button', { name: 'Bulk Activate/Deactivate' }));
  fireEvent.click(screen.getByRole('button', { name: 'Activate All' }));
  await screen.findByText('All operations completed successfully.');
  expect(activate).toHaveBeenCalledTimes(1);
  expect(activate).toHaveBeenCalledWith(true);
});

it('submits one supported stream edit without TV metadata or row ids (SRC-F15)', async () => {
  const edit = jest.fn().mockResolvedValue(undefined);
  render(<BulkOperations open onClose={jest.fn()} selectedChannels={[{ id: 'one' }, { id: 'two' }]}
    onBulkEdit={edit} onBulkDelete={jest.fn()} onBulkActivate={jest.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Bulk Edit' }));
  expect(screen.queryByRole('checkbox', { name: 'Country' })).not.toBeInTheDocument();
  expect(screen.queryByRole('checkbox', { name: 'Language' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Group' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Group' }), { target: { value: 'News' } });
  fireEvent.click(screen.getByRole('button', { name: 'Update' }));
  await screen.findByText('All operations completed successfully.');
  expect(edit).toHaveBeenCalledTimes(1);
  expect(edit).toHaveBeenCalledWith({ group: 'News' });
});
