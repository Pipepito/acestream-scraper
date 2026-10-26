import React from 'react';
import { act, renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAddSearchResult } from '../hooks/useSearch';
import apiClient from '../services/apiClient';

jest.mock('../services/apiClient');
const api = jest.mocked(apiClient);
const INFOHASH = '42832fbf9a1d3bdcca043e09951d6769fbbe04e7';
const CONTENT_ID = 'e72d03fb9694164317260f684470be9ab781ed95';
const channel = { id: INFOHASH, name: 'NBA TV [US]', categories: ['sports'] };

function setup() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(() => useAddSearchResult(), { wrapper });
}

beforeEach(() => jest.resetAllMocks());

it('resolves a search infohash before saving the content ID and metadata', async () => {
  api.post.mockResolvedValueOnce({ data: { content_id: CONTENT_ID } })
    .mockResolvedValueOnce({ data: { id: CONTENT_ID, name: channel.name } });
  const { result } = setup();
  await act(async () => { await result.current.mutateAsync(channel); });
  expect(api.post).toHaveBeenNthCalledWith(1, `/v1/search/${INFOHASH}/resolve`, {});
  expect(api.post).toHaveBeenNthCalledWith(2, '/v1/acestream-channels/', {
    id: CONTENT_ID, name: channel.name, group: 'sports',
  });
});

it('does not save an unresolved infohash and can retry after resolution fails', async () => {
  api.post.mockRejectedValueOnce(new Error('Engine unavailable'));
  const { result } = setup();
  await act(async () => {
    await expect(result.current.mutateAsync(channel)).rejects.toThrow('Engine unavailable');
  });
  expect(api.post).toHaveBeenCalledTimes(1);
  api.post.mockResolvedValueOnce({ data: { content_id: CONTENT_ID } })
    .mockResolvedValueOnce({ data: { id: CONTENT_ID } });
  await act(async () => { await result.current.mutateAsync(channel); });
  expect(api.post).toHaveBeenLastCalledWith('/v1/acestream-channels/', {
    id: CONTENT_ID, name: channel.name, group: 'sports',
  });
});
