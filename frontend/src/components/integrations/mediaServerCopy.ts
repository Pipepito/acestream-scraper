import { ApiError } from '../../services/apiErrors';
import type { MediaServerKind, MediaServerSyncStatus } from '../../services/mediaServerService';
import { getErrorMessage } from '../../utils/errorUtils';

/** How a section reports the outcome of a media-server action. */
export type MediaServerNotify = (message: string, severity: 'success' | 'warning' | 'error') => void;

export const KIND_LABEL: Record<MediaServerKind, string> = { jellyfin: 'Jellyfin', plex: 'Plex' };

/** The chip each sync outcome earns. */
export const SYNC_META: Record<MediaServerSyncStatus, string> = {
  ok: 'Guide up to date',
  error: 'Refresh failed',
  never: 'Not synced yet',
  manual: 'Rescan the guide in Plex',
};

/** Outcomes that still need the user to do something. */
export const SYNC_NEEDS_ATTENTION: MediaServerSyncStatus[] = ['error', 'manual'];

/** Plain-language copy for the errors the media-server endpoints raise. */
export const describeMediaServerError = (error: unknown): string => {
  if (error instanceof ApiError) {
    if (error.code === 'MEDIA_SERVER_AUTH') return 'The server rejected the API key/token.';
    if (error.code === 'MEDIA_SERVER_UNREACHABLE') return 'The server did not answer. Check the address and that it is reachable from this server.';
    if (error.code === 'MEDIA_SERVER_ERROR' || error.code === 'MEDIA_SERVER_NOT_CONNECTED' || error.code === 'MEDIA_SERVER_URL_FORBIDDEN') {
      return error.message;
    }
  }
  return getErrorMessage(error);
};
