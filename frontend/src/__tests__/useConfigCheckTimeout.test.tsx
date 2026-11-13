import React from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAcestreamCheckTimeout, useUpdateAcestreamCheckTimeout } from '../hooks/useConfig';
import { configService } from '../services/configService';

jest.mock('../services/configService', () => ({
  configService: { getAcestreamCheckTimeout: jest.fn(), updateAcestreamCheckTimeout: jest.fn() },
}));

const service = jest.mocked(configService);

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper };
}

beforeEach(() => jest.resetAllMocks());

it('loads the saved stream check timeout', async () => {
  service.getAcestreamCheckTimeout.mockResolvedValue(20);
  const { wrapper } = setup();
  const { result } = renderHook(() => useAcestreamCheckTimeout(), { wrapper });
  await waitFor(() => expect(result.current.data).toBe(20));
});

it('refreshes the timeout and the settings list after saving', async () => {
  // Both views show the value: a stale one would offer Save again for the
  // number that was just stored.
  service.updateAcestreamCheckTimeout.mockResolvedValue(undefined);
  const { client, wrapper } = setup();
  const invalidate = jest.spyOn(client, 'invalidateQueries');
  const { result } = renderHook(() => useUpdateAcestreamCheckTimeout(), { wrapper });
  await act(async () => { await result.current.mutateAsync(30); });
  expect(service.updateAcestreamCheckTimeout.mock.calls[0][0]).toBe(30);
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ['acestreamCheckTimeout'] });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ['allSettings'] });
});

it('leaves the cached values alone when saving fails', async () => {
  service.updateAcestreamCheckTimeout.mockRejectedValue(new Error('Unavailable'));
  const { client, wrapper } = setup();
  const invalidate = jest.spyOn(client, 'invalidateQueries');
  const { result } = renderHook(() => useUpdateAcestreamCheckTimeout(), { wrapper });
  await act(async () => { await expect(result.current.mutateAsync(30)).rejects.toThrow('Unavailable'); });
  expect(invalidate).not.toHaveBeenCalled();
});
