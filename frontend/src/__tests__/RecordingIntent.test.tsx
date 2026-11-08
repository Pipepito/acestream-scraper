import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RecordingDialog from '../components/recordings/RecordingDialog';
import { recordingService, type Recording } from '../services/recordingService';

jest.mock('../services/recordingService', () => ({ recordingService: { create: jest.fn(), edit: jest.fn() } }));
const service = jest.mocked(recordingService);
const originalCrypto = globalThis.crypto;
const programme = { id: 7, epg_channel_id: 10, title: 'Una película',
  start_time: new Date(Date.now() + 3600_000).toISOString(), end_time: new Date(Date.now() + 7200_000).toISOString() };
function mount(recording?: Recording) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}>
    <RecordingDialog channelId={1} channelName="One" programme={programme} recording={recording} onClose={jest.fn()} />
  </QueryClientProvider>);
}
beforeEach(() => { jest.clearAllMocks(); Object.defineProperty(globalThis, 'crypto', { configurable: true, value: { getRandomValues: originalCrypto.getRandomValues.bind(originalCrypto) } }); });
afterEach(() => Object.defineProperty(globalThis, 'crypto', { configurable: true, value: originalCrypto }));

it('opens over private HTTP and retains a secure intent key and exact programme on retry', async () => {
  service.create.mockRejectedValueOnce(new Error('Network interrupted')).mockResolvedValueOnce({ id: 'saved' } as Recording);
  mount();
  expect(service.create).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));
  await waitFor(() => expect(service.create).toHaveBeenCalledTimes(2));
  expect(service.create.mock.calls[0][0]).toEqual(service.create.mock.calls[1][0]);
  expect(service.create.mock.calls[0][0]).toMatchObject({ programme, start_time: programme.start_time, end_time: programme.end_time,
    idempotency_key: expect.stringMatching(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/) });
});

it('generates different keys for separate creation intents', async () => {
  service.create.mockResolvedValue({ id: 'saved' } as Recording);
  const view = mount();
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));
  await waitFor(() => expect(service.create).toHaveBeenCalledTimes(1));
  view.unmount();
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));
  await waitFor(() => expect(service.create).toHaveBeenCalledTimes(2));
  expect(service.create.mock.calls[0][0].idempotency_key).not.toEqual(service.create.mock.calls[1][0].idempotency_key);
});

it('contains missing cryptography without submitting or blocking cancellation', () => {
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: undefined });
  mount();
  expect(screen.getByRole('alert')).toHaveTextContent('secure recording request');
  expect(screen.getByRole('button', { name: 'Schedule' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeEnabled();
  expect(service.create).not.toHaveBeenCalled();
});

it('edits an existing recording without generating a creation key', async () => {
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: undefined });
  service.edit.mockResolvedValue({ id: 'existing' } as Recording);
  mount({ id: 'existing', revision: 2, state: 'scheduled', timezone: 'UTC', start_time: programme.start_time,
    end_time: programme.end_time, snapshot: { title: programme.title } } as Recording);
  fireEvent.click(screen.getByRole('button', { name: 'Save times' }));
  await waitFor(() => expect(service.edit).toHaveBeenCalledWith('existing', { expected_revision: 2, start_time: programme.start_time, end_time: programme.end_time }));
  expect(service.create).not.toHaveBeenCalled();
});
