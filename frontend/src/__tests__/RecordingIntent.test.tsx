import React from 'react';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RecordingDialog from '../components/recordings/RecordingDialog';
import { recordingService, type Recording } from '../services/recordingService';
import i18n from '../i18n';

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
afterEach(async () => {
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: originalCrypto });
  await act(async () => { await i18n.changeLanguage('en'); });
});

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

it('pins the reviewed programme and exact times when the guide refreshes', async () => {
  service.create.mockResolvedValue({ id: 'saved' } as Recording);
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  const content = (selected: typeof programme) => <QueryClientProvider client={client}>
    <RecordingDialog channelId={1} channelName="One" programme={selected} onClose={jest.fn()} />
  </QueryClientProvider>;
  const { rerender } = render(content(programme));
  rerender(content({ ...programme, id: 99, title: 'Changed guide row', start_time: new Date(Date.now() + 7200_000).toISOString() }));
  expect(screen.getByText(programme.title)).toBeVisible();
  expect(screen.queryByText('Changed guide row')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));
  await waitFor(() => expect(service.create).toHaveBeenCalledWith(expect.objectContaining({ programme,
    start_time: programme.start_time, end_time: programme.end_time })));
});

it('locks the submitted time draft, retains it on failure and confirms discard in the current language', async () => {
  let rejectSave!: (reason: Error) => void;
  service.edit.mockImplementation(() => new Promise((_resolve, reject) => { rejectSave = reject; }));
  const close = jest.fn();
  const recording = { id: 'existing', revision: 2, state: 'scheduled', timezone: 'UTC', start_time: programme.start_time,
    end_time: programme.end_time, snapshot: { title: programme.title } } as Recording;
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}>
    <RecordingDialog channelId={1} channelName="One" recording={recording} onClose={close} />
  </QueryClientProvider>);
  const end = screen.getByLabelText('End', { exact: true });
  const draft = new Date(Date.parse(programme.end_time) + 60000).toISOString().slice(0, 16);
  fireEvent.change(end, { target: { value: draft } });
  fireEvent.click(screen.getByRole('button', { name: 'Save times' }));
  await waitFor(() => expect(end).toBeDisabled());
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
  await act(async () => { rejectSave(new Error('Controlled save failure')); });
  expect(await screen.findByRole('alert')).toBeVisible();
  expect(end).toHaveValue(draft);
  expect(end).toBeEnabled();
  await act(async () => { await i18n.changeLanguage('es'); });
  expect(end).toHaveValue(draft);
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
  const confirmation = await screen.findByRole('dialog', { name: '¿Descartar los cambios sin guardar?' });
  expect(close).not.toHaveBeenCalled();
  fireEvent.click(within(confirmation).getByRole('button', { name: 'Descartar cambios' }));
  await waitFor(() => expect(close).toHaveBeenCalledTimes(1));
  expect(service.edit).toHaveBeenCalledTimes(1);
});
