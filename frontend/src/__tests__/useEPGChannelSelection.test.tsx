import React from 'react';
import { act, renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEPGChannelSelection } from '../hooks/useEPGChannelSelection';
import { EPGChannel } from '../services/epgService';
import { TVChannel } from '../types/tvChannelTypes';

jest.mock('../services/tvChannelService', () => ({ tvChannelService: { create: jest.fn() } }));

const stamp = '2026-11-09T00:00:00Z';
const epgChannel = (id: number, xmlId: string, sourceId: number, sources?: number[]): EPGChannel => ({
  id, channel_xml_id: xmlId, name: xmlId, epg_source_id: sourceId, created_at: stamp, updated_at: stamp,
  sources: sources?.map((source_id, index) => ({ channel_id: id * 10 + index, source_id, name: `Guide ${source_id}`, enabled: true })),
});
const tvChannel = (id: number, epgId: string, sourceId?: number): TVChannel => ({
  id, name: `TV ${id}`, epg_id: epgId, epg_source_id: sourceId, created_at: stamp, updated_at: stamp,
  is_active: true, is_favorite: false, acestream_channels: [],
});

function setup(epgChannels: EPGChannel[], tvChannels: TVChannel[]) {
  const client = new QueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(() => useEPGChannelSelection({
    epgChannels, tvChannels, isLoadingTVChannelCatalog: false, tvChannelCatalogError: null,
    selectedSourceId: undefined, channelPage: 0, channelPageSize: 25, showSnackbar: jest.fn(),
  }), { wrapper });
}

it('treats a shared guide channel as linked when a TV channel uses any of its sources', () => {
  // The row is listed under guide 1, but the TV channel was assigned through
  // guide 2: offering it again would create a duplicate TV channel.
  const shared = epgChannel(1, 'la1.es', 1, [1, 2]);
  const other = epgChannel(2, 'la2.es', 1, [1, 2]);
  const { result } = setup([shared, other], [tvChannel(10, 'la1.es', 2)]);
  expect(result.current.isChannelMapped(shared)).toBe(true);
  expect(result.current.isChannelMapped(other)).toBe(false);
  expect(result.current.visibleUnmappedChannelIds).toEqual([2]);
  act(() => result.current.handleSelectChannel(1));
  expect(result.current.selectedEPGChannelIds).toEqual([]);
});

it('keeps the same guide ID from an unrelated source selectable', () => {
  const channel = epgChannel(3, 'sport.tv', 1);
  const { result } = setup([channel], [tvChannel(11, 'sport.tv', 9)]);
  expect(result.current.isChannelMapped(channel)).toBe(false);
  act(() => result.current.handleSelectChannel(3));
  expect(result.current.selectedEPGChannelIds).toEqual([3]);
});

it('links a guide ID assigned without a source to every guide that carries it', () => {
  const channel = epgChannel(4, 'news.tv', 5);
  const { result } = setup([channel], [tvChannel(12, 'news.tv')]);
  expect(result.current.isChannelMapped(channel)).toBe(true);
});
