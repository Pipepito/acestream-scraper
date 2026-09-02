import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import ConfirmDialog, { useConfirm } from '../components/ConfirmDialog';

describe('ConfirmDialog', () => {
  it('confirms and closes', () => {
    const onConfirm = jest.fn();
    const onClose = jest.fn();
    render(<ConfirmDialog open title="Delete URL?" body="This cannot be undone." confirmLabel="Delete" danger onConfirm={onConfirm} onClose={onClose} />);
    const dialog = screen.getByRole('dialog', { name: 'Delete URL?' });
    expect(dialog).toHaveTextContent('This cannot be undone.');
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('useConfirm resolves true on confirm and false on cancel', async () => {
    let result: Promise<boolean> | undefined;
    const Harness: React.FC = () => {
      const { confirm, dialog } = useConfirm();
      return (
        <div>
          <button type="button" onClick={() => { result = confirm({ title: 'Remove?', body: 'Sure?', confirmLabel: 'Remove' }); }}>go</button>
          {dialog}
        </div>
      );
    };
    render(<Harness />);
    fireEvent.click(screen.getByRole('button', { name: 'go' }));
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
    await act(async () => { await expect(result).resolves.toBe(true); });
    fireEvent.click(screen.getByRole('button', { name: 'go' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await act(async () => { await expect(result).resolves.toBe(false); });
  });
});
