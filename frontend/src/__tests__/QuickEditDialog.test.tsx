import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import QuickEditDialog from '../components/QuickEditDialog';
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => ({ data: [{ id: 7, name: 'Sports TV', is_active: true, acestream_channels: [] }] }) }));

describe('QuickEditDialog', () => {
  it('shows error alert on save failure', async () => {
    const onSave = jest.fn().mockRejectedValue(new Error('Save failed'));
    render(
      <QuickEditDialog open onClose={() => {}} channel={{ id: '1', name: 'Test', group: '', logo: '', is_active: true }} onSave={onSave} />
    );
    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: 'New Name' } });
    fireEvent.click(screen.getByText('Save'));
    expect(await screen.findByText(/save failed/i)).toBeInTheDocument();
  });

  it('edits only the playlist-relevant fields and shows a read-only summary', async () => {
    const onSave = jest.fn().mockResolvedValue(undefined);
    render(
      <QuickEditDialog
        open
        onClose={() => {}}
        channel={{ id: 'abc', name: 'Test', group: 'Sports', is_active: true, epg_update_protected: false, check_error: 'timeout' }}
        onSave={onSave}
      />
    );

    expect(screen.getByRole('heading', { name: 'Edit channel' })).toBeInTheDocument();
    expect(screen.getByLabelText(/Acestream ID/)).toHaveAttribute('readonly');
    expect(screen.queryByLabelText(/Source URL/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Original URL/)).not.toBeInTheDocument();
    expect(screen.getByText(/Last checked never · Last scraped never · Last error: timeout/)).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Show in playlist'));
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith({
        id: 'abc',
        name: 'Test',
        group: 'Sports',
        logo: '',
        tvg_id: '',
        tvg_name: '',
        is_active: false,
        epg_update_protected: false,
      })
    );
  });

  it('asks for the ID when creating and disables Save until name and ID are filled', () => {
    render(<QuickEditDialog open mode="create" onClose={() => {}} channel={{ id: '', name: '' }} onSave={jest.fn()} />);

    expect(screen.getByRole('heading', { name: 'Add channel' })).toBeInTheDocument();
    expect(screen.getByLabelText(/Acestream ID/)).not.toHaveAttribute('readonly');
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/^Name/), { target: { value: 'New' } });
    fireEvent.change(screen.getByLabelText(/Acestream ID/), { target: { value: 'deadbeef' } });
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
  });
});

  it('adds the chosen TV channel to a manual stream save', async () => {
    const onSave = jest.fn().mockResolvedValue(undefined);
    render(<QuickEditDialog open mode="create" onClose={() => {}} channel={{ id: 'a'.repeat(40), name: 'Sports' }} onSave={onSave} />);
    fireEvent.change(screen.getByRole('combobox', { name: 'Link to TV channel (optional)' }), { target: { value: 'Sports' } });
    fireEvent.click(await screen.findByRole('option', { name: 'Sports TV' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ tv_channel_id: 7 })));
  });
