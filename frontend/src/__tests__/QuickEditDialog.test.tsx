import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import QuickEditDialog from '../components/QuickEditDialog';

describe('QuickEditDialog', () => {
  it('shows error alert on save failure', async () => {
    const onSave = jest.fn().mockRejectedValue(new Error('Save failed'));
    render(
      <QuickEditDialog
        open={true}
        onClose={() => {}}
        channel={{ id: '1', name: 'Test', group: '', logo: '', is_active: true }}
        onSave={onSave}
      />
    );
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'New Name' } });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => {
      expect(screen.getByText(/save failed/i)).toBeInTheDocument();
    });
  });
});
