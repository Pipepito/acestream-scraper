import { matchesTVFilters } from '../components/TVChannelFilters';
import { TVChannel } from '../types/tvChannelTypes';
const channel = { id: 1, name: 'News', category: 'News', country: 'ES', language: 'spa', channel_number: 0, is_active: true, is_favorite: false, epg_id: 'news.es', epg_source_id: 3, acestream_channels: [{ id: 'abc', name: 'Backup', is_online: true }, { id: 'def', is_online: null }] } as TVChannel;
it('combines independent filters, including number zero and stream metadata', () => {
  expect(matchesTVFilters(channel, { search: ' backup ', country: 'ES', epg: 'yes', signal: 'verified', min_streams: '2', max_number: '0', is_favorite: 'false' })).toBe(true);
  expect(matchesTVFilters(channel, { country: 'ES', min_number: '1' })).toBe(false);
  expect(matchesTVFilters(channel, { epg_source_id: '2' })).toBe(false);
});
it('distinguishes missing streams, unchecked signal and absent metadata', () => {
  expect(matchesTVFilters(channel, { logo_url: 'no', website: 'no', streams: 'multiple' })).toBe(true);
  expect(matchesTVFilters(channel, { signal: 'unknown' })).toBe(false);
  expect(matchesTVFilters({ ...channel, acestream_channels: [] }, { streams: 'none', signal: 'unknown' })).toBe(false);
  expect(matchesTVFilters({ ...channel, channel_number: null }, { number: 'no' })).toBe(true);
});
