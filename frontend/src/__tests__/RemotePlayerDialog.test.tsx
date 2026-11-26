import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiError } from '../services/apiErrors';
import RemotePlayerDialog from '../components/integrations/RemotePlayerDialog';
import { remotePlayerService } from '../services/remotePlayerService';

const mockCreate = jest.fn();
jest.mock('../hooks/useBaseUrls', () => ({ useBaseUrls: () => ({ data: [] }) }));
jest.mock('../hooks/useRemotePlayers', () => ({
  useCreateRemotePlayer: () => ({ mutateAsync: mockCreate, isPending: false }),
  useUpdateRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTestRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));
jest.mock('../services/remotePlayerService', () => ({ remotePlayerService: {
  startAndroidPairing: jest.fn(), finishAndroidPairing: jest.fn(),
} }));
const start = remotePlayerService.startAndroidPairing as jest.Mock;
const finish = remotePlayerService.finishAndroidPairing as jest.Mock;
const fingerprint = 'a'.repeat(64);

const openAndroid = async () => {
  render(<RemotePlayerDialog open player={null} onClose={jest.fn()} notify={jest.fn()} />);
  fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'Android TV' } });
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Player' }));
  fireEvent.click(await screen.findByRole('option', { name: 'VLC Android (3.6+)' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Host' }), { target: { value: '192.168.1.20' } });
};
const pair = async () => {
  fireEvent.click(screen.getByRole('button', { name: 'Request pairing code' }));
  fireEvent.change(await screen.findByRole('textbox', { name: 'Pairing code' }), { target: { value: '123456' } });
  await userEvent.click(screen.getByRole('button', { name: 'Pair with VLC Android' }));
};
beforeEach(() => {
  jest.clearAllMocks();
  start.mockResolvedValue({ challenge: 'challenge', fingerprint });
  finish.mockResolvedValue({ password: 'paired-credential' });
  mockCreate.mockResolvedValue({});
});

test('pairs Android over HTTPS and saves its session instead of the code', async () => {
  await openAndroid();
  expect(screen.getByRole('textbox', { name: 'Port' })).toHaveValue('8443');
  expect(screen.queryByLabelText('Password')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Add player' })).toBeDisabled();
  await pair();
  await screen.findByText('Paired with VLC Android. Save this player to keep the connection.');
  expect(start).toHaveBeenCalledWith('192.168.1.20', 8443);
  expect(finish).toHaveBeenCalledWith({ host: '192.168.1.20', port: 8443, challenge: 'challenge', fingerprint, code: '123456' });
  fireEvent.click(screen.getByRole('button', { name: 'Add player' }));
  await waitFor(() => expect(mockCreate).toHaveBeenCalledWith(expect.objectContaining({ kind: 'vlc_android', port: 8443, password: 'paired-credential' })));
});

test('shows expired code errors and allows another attempt', async () => {
  finish.mockRejectedValue(new ApiError({ message: 'The code is incorrect or expired. Request a new code.', status: 502, kind: 'server', canRetry: false, code: 'REMOTE_PLAYER_AUTH', context: { kind: 'pairing_required' } }));
  await openAndroid();
  await pair();
  expect(await screen.findByText(/Request a new code if the previous one has expired/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Add player' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Request pairing code' }));
  await waitFor(() => expect(start).toHaveBeenCalledTimes(2));
});

test('changing the address clears the new paired credential', async () => {
  await openAndroid();
  await pair();
  await screen.findByText('Paired with VLC Android. Save this player to keep the connection.');
  fireEvent.change(screen.getByRole('textbox', { name: 'Host' }), { target: { value: '192.168.1.21' } });
  expect(screen.getByRole('button', { name: 'Add player' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Request pairing code' })).toBeEnabled();
});

test('keeps drafts through background refresh and requires an explicit discard', async () => {
  const close = jest.fn();
  const player = { id: 1, name: 'Living room', kind: 'vlc' as const, host: '192.168.1.20', port: 8080, username: null, base_url_id: null, has_password: false, created_at: '', updated_at: '' };
  const { rerender } = render(<RemotePlayerDialog open player={player} onClose={close} notify={jest.fn()} />);
  fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'My draft' } });
  rerender(<RemotePlayerDialog open player={{ ...player, name: 'Server refresh' }} onClose={close} notify={jest.fn()} />);
  expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My draft');
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(await screen.findByRole('dialog', { name: 'Discard unsaved changes?' })).toBeInTheDocument();
  expect(close).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }));
  await waitFor(() => expect(close).toHaveBeenCalledTimes(1));
});

test('keeps the failed draft, prevents duplicate submissions and does not close while saving', async () => {
  const close = jest.fn();
  let rejectSave: (error: unknown) => void = () => undefined;
  mockCreate.mockImplementation(() => new Promise((_, reject) => { rejectSave = reject; }));
  render(<RemotePlayerDialog open player={null} onClose={close} notify={jest.fn()} />);
  fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), { target: { value: 'Bedroom' } });
  fireEvent.change(screen.getByRole('textbox', { name: 'Host' }), { target: { value: '192.168.1.21' } });
  const save = screen.getByRole('button', { name: 'Add player' });
  fireEvent.click(save); fireEvent.click(save);
  expect(mockCreate).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
  expect(screen.getByRole('textbox', { name: 'Name' })).toBeDisabled();
  rejectSave(new ApiError({ status: 409, kind: 'unknown', canRetry: false, message: 'Duplicate' }));
  expect(await screen.findByText('A player named "Bedroom" already exists.')).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Bedroom');
  expect(save).toBeEnabled();
  expect(close).not.toHaveBeenCalled();
});
