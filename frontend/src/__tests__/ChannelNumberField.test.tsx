import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ChannelNumberField from '../components/ChannelNumberField';
import { TVChannel } from '../types/tvChannelTypes';
it('saves zero and clears a number without treating zero as missing', async () => {
  const onSave = jest.fn().mockResolvedValue(undefined);
  render(<ChannelNumberField channel={{ name: 'News', channel_number: 4 } as TVChannel} onSave={onSave} />);
  const field = screen.getByRole('spinbutton', { name: 'Channel number for News' });
  fireEvent.change(field, { target: { value: '0' } }); fireEvent.keyDown(field, { key: 'Enter' });
  await waitFor(() => expect(onSave).toHaveBeenCalledWith(expect.anything(), 0));
  await waitFor(() => expect(field).not.toBeDisabled());
  fireEvent.change(field, { target: { value: '' } }); fireEvent.blur(field);
  await waitFor(() => expect(onSave).toHaveBeenCalledWith(expect.anything(), null));
});
it('rejects fractional numbers and exposes save failures without discarding the draft', async () => {
  const onSave = jest.fn().mockRejectedValue(new Error('Cannot save'));
  render(<ChannelNumberField channel={{ name: 'News' } as TVChannel} onSave={onSave} />);
  const field = screen.getByRole('spinbutton');
  fireEvent.change(field, { target: { value: '1.5' } }); fireEvent.blur(field);
  expect(onSave).not.toHaveBeenCalled();
  expect(screen.getByText(/Use a whole number/)).toBeInTheDocument();
  fireEvent.change(field, { target: { value: '12' } }); fireEvent.blur(field);
  await waitFor(() => expect(field).toHaveAttribute('aria-invalid', 'true'));
  expect(field).toHaveValue(12);
});
