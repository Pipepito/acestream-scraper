import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { ApiError } from '../services/apiClient';
import TelegramSection from '../components/integrations/TelegramSection';
import { createAppTheme } from '../theme';

const mockStatus = jest.fn();
const mockLogin = jest.fn();
const mockCode = jest.fn();
const mockSave = jest.fn();
const mockPreview = jest.fn();
const mockSources = jest.fn();
const mockLogout = jest.fn();
const mockApi = {
  status: mockStatus, sources: mockSources, login: mockLogin, code: mockCode,
  password: jest.fn(), disconnect: jest.fn(), reconnect: jest.fn(), logout: mockLogout,
  chats: jest.fn().mockResolvedValue([{ id: '-100123', label: 'Sports group', kind: 'channel' }]),
  topics: jest.fn().mockResolvedValue([]), save: mockSave, preview: mockPreview,
  resolve: jest.fn().mockResolvedValue({ id: '123', label: 'Raul', kind: 'user' }),
};
jest.mock('../services/telegramService', () => ({ ...jest.requireActual('../services/telegramService'), telegramService: () => mockApi }));

function setup(mode: 'light' | 'dark' = 'light') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(<QueryClientProvider client={client}><ThemeProvider theme={createAppTheme(mode)}><TelegramSection /></ThemeProvider></QueryClientProvider>);
  return client;
}
async function unlock() {
  fireEvent.change(screen.getByLabelText('Telegram admin token'), { target: { value: 'private-admin-token' } });
  fireEvent.click(screen.getByRole('button', { name: 'Unlock Telegram settings' }));
  await screen.findByRole('button', { name: 'Lock settings' });
}
beforeEach(() => {
  jest.clearAllMocks();
  mockStatus.mockResolvedValue({ state: 'disconnected', message: '', account_label: '', queue_size: 0 });
  mockSources.mockResolvedValue([]);
  mockLogin.mockResolvedValue({ state: 'code_required' });
  mockSave.mockResolvedValue({});
  mockPreview.mockResolvedValue({ chat_id: '-100123', messages: [{ message_id: 12, sender_id: '123', outcome: 'matched', result: { channels: [{ channel_id: 'a'.repeat(40), name: '🇪🇸 Sports' }], duplicate_count: 1, invalid_count: 0 } }] });
});

test.each(['light', 'dark'] as const)('requires unlock and clears secret fields when locked (%s)', async mode => {
  const client = setup(mode);
  expect(mockStatus).not.toHaveBeenCalled();
  await unlock();
  await screen.findByRole('button', { name: 'Send login code' });
  fireEvent.change(screen.getByLabelText('Telegram API hash'), { target: { value: 'secret-hash' } });
  fireEvent.click(screen.getByRole('button', { name: 'Lock settings' }));
  expect(screen.getByLabelText('Telegram admin token')).toHaveValue('');
  expect(screen.queryByLabelText('Telegram API hash')).not.toBeInTheDocument();
  expect(JSON.stringify(client.getQueryCache().getAll().map(query => query.queryKey))).not.toContain('private-admin-token');
  expect(localStorage.getItem('telegram')).toBeNull();
});

test('clears login credentials after submission and shows the code step', async () => {
  setup(); await unlock();
  fireEvent.change(await screen.findByLabelText('Telegram API ID'), { target: { value: '12345' } });
  fireEvent.change(screen.getByLabelText('Telegram API hash'), { target: { value: 'a'.repeat(32) } });
  fireEvent.change(screen.getByLabelText('Phone number with country code'), { target: { value: '+123456789' } });
  mockStatus.mockResolvedValue({ state: 'code_required' });
  fireEvent.click(screen.getByRole('button', { name: 'Send login code' }));
  await screen.findByLabelText('Telegram login code');
  expect(mockLogin).toHaveBeenCalledWith(12345, 'a'.repeat(32), '+123456789');
});

test('shows admin errors without exposing source controls', async () => {
  mockStatus.mockRejectedValue(new ApiError({ message: 'Configure a separate encryption key', status: 503, kind: 'server', canRetry: true }));
  setup(); await unlock();
  expect(await screen.findByText('Configure a separate encryption key')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Add Telegram source' })).not.toBeInTheDocument();
});

test('new source defaults to new messages, resolves identities and previews before saving', async () => {
  mockStatus.mockResolvedValue({ state: 'connected', account_label: 'Test' });
  setup(); await unlock();
  fireEvent.click(await screen.findByRole('button', { name: 'Add Telegram source' }));
  fireEvent.change(screen.getByLabelText('Source name'), { target: { value: 'Sports' } });
  fireEvent.mouseDown(screen.getByLabelText('Joined chat'));
  fireEvent.click(await screen.findByRole('option', { name: 'Sports group (-100123)' }));
  expect(screen.getByLabelText('Initial history count')).toHaveValue(0);
  fireEvent.change(screen.getByLabelText('Telegram username'), { target: { value: '@raul' } });
  fireEvent.click(screen.getByRole('button', { name: 'Resolve and add' }));
  await screen.findByText('Raul · 123');
  const senders = screen.getByLabelText('Allowed sender IDs');
  fireEvent.change(senders, { target: { value: '123, ' } });
  expect(senders).toHaveValue('123, ');
  fireEvent.change(senders, { target: { value: '123, 456' } });
  fireEvent.click(screen.getByRole('button', { name: 'Test against recent messages' }));
  expect(await screen.findByText(/🇪🇸 Sports/)).toBeInTheDocument();
  expect(mockSave).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Save source' }));
  await waitFor(() => expect(mockSave).toHaveBeenCalledWith(expect.objectContaining({ chat_id: '-100123', sender_ids: ['123', '456'], name: 'Sports' }), undefined));
});

test('revocation requires the concrete confirmation', async () => {
  mockStatus.mockResolvedValue({ state: 'connected', account_label: 'Test' });
  setup(); await unlock();
  fireEvent.click(screen.getByRole('button', { name: 'Revoke session and remove account' }));
  expect(await screen.findByRole('dialog', { name: 'Revoke Telegram session?' })).toBeInTheDocument();
  expect(mockLogout).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Revoke and remove' }));
  await waitFor(() => expect(mockLogout).toHaveBeenCalledTimes(1));
});
