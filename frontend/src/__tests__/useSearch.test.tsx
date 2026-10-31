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

it('sends selected infohashes to authoritative server import, never manual creation', async () => {
  api.post.mockResolvedValueOnce({ data: { items: [{ infohash: INFOHASH, content_id: CONTENT_ID, outcome: 'added' }] } });
  const { result } = setup();
  await act(async () => { await result.current.mutateAsync(channel); });
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post).toHaveBeenCalledWith('/v1/search/import', { items: [{ infohash: INFOHASH, name: channel.name, category: 'sports' }] }, { timeout: 135000 });
});

it('returns excluded outcomes without retrying through manual creation', async () => {
  api.post.mockResolvedValueOnce({ data: { items: [{ infohash: INFOHASH, outcome: 'excluded', rule_ids: [1] }] } });
  const { result } = setup();
  await act(async () => { expect((await result.current.mutateAsync(channel)).outcome).toBe('excluded'); });
  expect(api.post).toHaveBeenCalledTimes(1);
});
