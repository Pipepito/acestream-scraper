import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import PlaybackRoutingFields from '../components/player/PlaybackRoutingFields';
import { usePlaybackRouting, useUpdatePlaybackRouting } from '../hooks/useConfig';

jest.mock('../hooks/useConfig');
const query = usePlaybackRouting as jest.Mock;
const update = useUpdatePlaybackRouting as jest.Mock;
const mutate = jest.fn();
beforeEach(() => {
  jest.clearAllMocks();
  query.mockReturnValue({ data: { use_acexy: false, acexy_url: 'http://localhost:8080' } });
  update.mockReturnValue({ mutate, reset: jest.fn() });
});
it('saves the proxy route and restores direct mode', () => {
  render(<PlaybackRoutingFields />);
  expect(screen.getByRole('button', { name: 'Save playback routing' })).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Route playback through Acexy' }));
  fireEvent.change(screen.getByLabelText('Acexy URL', { exact: false }), { target: { value: 'http://proxy:8080' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save playback routing' }));
  expect(mutate).toHaveBeenLastCalledWith({ use_acexy: true, acexy_url: 'http://proxy:8080' }, expect.anything());
  fireEvent.click(screen.getByRole('checkbox', { name: 'Route playback through Acexy' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save playback routing' }));
  expect(mutate).toHaveBeenLastCalledWith({ use_acexy: false, acexy_url: 'http://proxy:8080' }, expect.anything());
});
it('reports loading, read failures with retry, and save failures', () => {
  query.mockReturnValue({ isLoading: true });
  const view = render(<PlaybackRoutingFields />);
  expect(screen.getByRole('progressbar', { name: 'Loading playback routing' })).toBeInTheDocument();
  const refetch = jest.fn();
  query.mockReturnValue({ isError: true, refetch });
  view.rerender(<PlaybackRoutingFields />);
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  expect(refetch).toHaveBeenCalled();
  query.mockReturnValue({ data: { use_acexy: false, acexy_url: 'http://localhost:8080' } });
  update.mockReturnValue({ mutate, reset: jest.fn(), isError: true, error: new Error('Save failed') });
  view.rerender(<PlaybackRoutingFields />);
  expect(screen.getByText('Something went wrong. Try again.')).toBeInTheDocument();
});
