import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
    fireEvent.click(screen.getByText('Edit'));
    fireEvent.click(screen.getByText('Apply Edit'));
    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });
});
