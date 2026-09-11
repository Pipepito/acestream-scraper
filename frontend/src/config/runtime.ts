type RuntimeOptions = {
  dev?: boolean;
  backendOrigin?: string;
  mode?: string;
};

const DEFAULT_BACKEND_ORIGIN = 'http://localhost:8000';

const getBackendOrigin = (backendOrigin?: string): string => backendOrigin ?? DEFAULT_BACKEND_ORIGIN;

export const getApiBaseUrl = ({ dev = false, backendOrigin }: RuntimeOptions = {}): string =>
  dev ? `${getBackendOrigin(backendOrigin)}/api` : '/api';

export const getPlaylistDownloadBaseUrl = ({
  dev = false,
  backendOrigin,
}: RuntimeOptions = {}): string => (dev ? getBackendOrigin(backendOrigin) : '');

export const shouldDisableGridVirtualization = ({ mode }: RuntimeOptions = {}): boolean =>
  mode === 'test';
