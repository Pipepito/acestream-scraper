import { getAbsolutePlaylistUrl } from '../services/playlistService';

describe('getAbsolutePlaylistUrl', () => {
  afterEach(() => window.localStorage.removeItem('apiToken'));

  it('resolves against the supplied public base URL', () => {
    expect(getAbsolutePlaylistUrl({ only_online: true }, 'https://scraper.example.com')).toBe(
      'https://scraper.example.com/api/v1/playlists/m3u?only_online=true'
    );
  });

  it('falls back to window.location.origin', () => {
    expect(getAbsolutePlaylistUrl({ only_online: true })).toBe('http://localhost/api/v1/playlists/m3u?only_online=true');
  });

  it('appends the API token as a query parameter', () => {
    window.localStorage.setItem('apiToken', 'a b');
    expect(getAbsolutePlaylistUrl({}, 'http://x')).toBe('http://x/api/v1/playlists/m3u?token=a+b');
  });
});
