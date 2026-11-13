import React from 'react';
import { act, renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWarpReconnect } from '../hooks/useWarp';
import { reconnectWarp } from '../services/warpService';

jest.mock('../services/warpService', () => ({
  getWarpStatus: jest.fn(), connectWarp: jest.fn(), disconnectWarp: jest.fn(), reconnectWarp: jest.fn(),
  setWarpMode: jest.fn(), registerWarpLicense: jest.fn(),
}));

const reconnect = jest.mocked(reconnectWarp);

function setup() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  const invalidate = jest.spyOn(client, 'invalidateQueries');
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { invalidate, ...renderHook(() => useWarpReconnect(), { wrapper }) };
}

beforeEach(() => jest.resetAllMocks());

it('refreshes the WARP status after a reconnect', async () => {
  reconnect.mockResolvedValue({ success: true, message: 'Reconnect requested', details: null });
  const { result, invalidate } = setup();
  await act(async () => { await result.current.mutateAsync(); });
  expect(reconnect).toHaveBeenCalledTimes(1);
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ['warp'] });
});

it('refreshes the WARP status after a failed reconnect too', async () => {
  // A failed reconnect can leave WARP disconnected: the page must show the
  // real state, not the one from before the attempt.
  reconnect.mockRejectedValue(new Error('WARP reconnect failed'));
  const { result, invalidate } = setup();
  await act(async () => { await expect(result.current.mutateAsync()).rejects.toThrow('WARP reconnect failed'); });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ['warp'] });
});
