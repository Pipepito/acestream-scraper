import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssignTVChannelDialog from '../components/AssignTVChannelDialog';
import type { TVChannel } from '../types/tvChannelTypes';

it('finds a channel beyond the first 100 by number and category, and resets when reopened', async () => {
  const user = userEvent.setup();
  const channels = Array.from({ length: 150 }, (_, index) => ({ id: index + 1, name: `Channel ${index + 1}`, channel_number: index + 1, category: index === 149 ? 'Documentaries' : 'General' } as TVChannel));
  const props = { open: true, onClose: jest.fn(), tvChannels: channels, onAssign: jest.fn() };
  const { rerender } = render(<AssignTVChannelDialog {...props} />);
  await user.type(screen.getByRole('combobox'), 'Documentaries');
  await user.click(await screen.findByRole('option', { name: /150 · Channel 150/ }));
  await user.click(screen.getByRole('button', { name: 'Assign' }));
  expect(props.onAssign).toHaveBeenCalledWith(150);
  rerender(<AssignTVChannelDialog {...props} open={false} />);
  rerender(<AssignTVChannelDialog {...props} />);
  expect(screen.getByRole('button', { name: 'Assign' })).toBeDisabled();
  await user.type(screen.getByRole('combobox'), '150');
  expect(await screen.findByRole('option', { name: /150 · Channel 150/ })).toBeInTheDocument();
});

it('offers retry and prevents assignment when the catalogue fails', async () => {
  const retry = jest.fn();
  render(<AssignTVChannelDialog open onClose={jest.fn()} onAssign={jest.fn()} catalogError="Unable to load channels" onRetry={retry} />);
  expect(screen.getByRole('combobox')).toBeDisabled();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Retry' }));
  expect(retry).toHaveBeenCalled();
});
