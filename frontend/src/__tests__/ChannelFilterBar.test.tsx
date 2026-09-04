import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import ChannelFilterBar from '../components/channels/ChannelFilterBar';

describe('ChannelFilterBar', () => {
  it('debounces the search box and trims the value', async () => {
    const onChange = jest.fn();
    render(<ChannelFilterBar filters={{}} groups={['Sports']} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText('Search'), { target: { value: '  Alpha ' } });
    expect(onChange).not.toHaveBeenCalled();
    await waitFor(() => expect(onChange).toHaveBeenCalledWith({ search: 'Alpha' }));
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('maps the selects to the API filters and offers a reset once anything is set', () => {
    const onChange = jest.fn();
    const { rerender } = render(<ChannelFilterBar filters={{}} groups={['Sports', 'News']} onChange={onChange} />);
    expect(screen.queryByRole('button', { name: 'Reset filters' })).not.toBeInTheDocument();

    fireEvent.mouseDown(screen.getByLabelText('Group'));
    fireEvent.click(within(screen.getByRole('listbox')).getByText('News'));
    expect(onChange).toHaveBeenLastCalledWith({ group: 'News' });

    fireEvent.mouseDown(screen.getByLabelText('Online'));
    fireEvent.click(within(screen.getByRole('listbox')).getByText('Offline'));
    expect(onChange).toHaveBeenLastCalledWith({ is_online: false });

    fireEvent.mouseDown(screen.getByLabelText('Playlist'));
    fireEvent.click(within(screen.getByRole('listbox')).getByText('Hidden'));
    expect(onChange).toHaveBeenLastCalledWith({ is_active: false });

    rerender(<ChannelFilterBar filters={{ group: 'News', is_active: false }} groups={['Sports', 'News']} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }));
    expect(onChange).toHaveBeenLastCalledWith({});
  });
});
