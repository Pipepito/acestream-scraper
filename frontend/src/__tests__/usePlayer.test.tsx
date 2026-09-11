import React from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePlayerSessionStatus } from '../hooks/usePlayer';
import { playerService } from '../services/playerService';
import { ApiError } from '../services/apiErrors';

jest.mock('../services/playerService', () => ({ playerService: { getSession: jest.fn() } }));
const getSession = playerService.getSession as jest.Mock;

it.each([503, 0])('resumes heartbeat polling after a transient %s failure', async (status) => {
  jest.useFakeTimers();
  const client = new QueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  getSession.mockReset().mockRejectedValueOnce(new ApiError({ status, message: 'Unavailable', kind: 'server', canRetry: true }))
    .mockResolvedValue({ id: 's1', state: 'ready' });
  const view = renderHook(() => usePlayerSessionStatus('s1'), { wrapper });
  await waitFor(() => expect(view.result.current.isError).toBe(true));
  await act(async () => { jest.advanceTimersByTime(2100); });
  await waitFor(() => expect(view.result.current.data?.state).toBe('ready'));
  expect(getSession).toHaveBeenCalledTimes(2);
  view.unmount(); client.clear(); jest.useRealTimers();
});

it.each([401, 403, 404])('stops polling when the session returns %s', async (status) => {
  jest.useFakeTimers();
  const client = new QueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  getSession.mockReset().mockRejectedValue(new ApiError({ status, message: 'Unavailable', kind: 'auth', canRetry: false }));
  const view = renderHook(() => usePlayerSessionStatus('s1'), { wrapper });
  await waitFor(() => expect(view.result.current.isError).toBe(true));
  await act(async () => { jest.advanceTimersByTime(10000); });
  expect(getSession).toHaveBeenCalledTimes(1);
  view.unmount(); client.clear(); jest.useRealTimers();
});
