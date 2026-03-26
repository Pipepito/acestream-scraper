import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BulkOperations from '../components/BulkOperations';

describe('BulkOperations', () => {
  it('shows error alert on bulk edit failure', async () => {
    const onBulkEdit = jest.fn().mockRejectedValue(new Error('Bulk edit failed'));

    render(
      <BulkOperations
        open={true}
        onClose={() => {}}
        selectedChannels={[{ id: '1' }]}
        onBulkEdit={onBulkEdit}
        onBulkDelete={jest.fn()}
        onBulkActivate={jest.fn()}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'Bulk Edit' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Update' }));

    expect(await screen.findByText(/failed/i)).toBeInTheDocument();
  });
});
