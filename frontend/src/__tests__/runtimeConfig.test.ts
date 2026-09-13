import {
  getApiBaseUrl,
  getPlaylistDownloadBaseUrl,
  shouldDisableGridVirtualization,
} from '../config/runtime';

describe('runtime config', () => {
  it('uses the backend origin for API requests during local development', () => {
    expect(getApiBaseUrl({ dev: true, backendOrigin: 'http://localhost:8000' })).toBe(
      'http://localhost:8000/api'
    );
  });

  it('uses relative API requests outside local development', () => {
    expect(getApiBaseUrl({ dev: false, backendOrigin: 'http://localhost:8000' })).toBe('/api');
  });

  it('uses the backend origin for playlist downloads during local development', () => {
    expect(
      getPlaylistDownloadBaseUrl({ dev: true, backendOrigin: 'http://localhost:8000' })
    ).toBe('http://localhost:8000');
  });

  it('keeps playlist downloads relative outside local development', () => {
    expect(getPlaylistDownloadBaseUrl({ dev: false, backendOrigin: 'http://localhost:8000' })).toBe('');
  });

  it('disables grid virtualization in tests only', () => {
    expect(shouldDisableGridVirtualization({ mode: 'test' })).toBe(true);
    expect(shouldDisableGridVirtualization({ mode: 'development' })).toBe(false);
    expect(shouldDisableGridVirtualization({ mode: 'production' })).toBe(false);
  });
});
