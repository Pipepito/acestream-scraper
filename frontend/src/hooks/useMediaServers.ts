import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../services/apiErrors';
import {
  mediaServerService,
  type MediaServer,
  type MediaServerCreate,
  type MediaServerProbe,
  type MediaServerRefreshResult,
  type MediaServerStatus,
  type MediaServerTestRequest,
  type MediaServerUpdate,
} from '../services/mediaServerService';

export const MEDIA_SERVERS_QUERY_KEY = ['media-servers'] as const;
export const mediaServerStatusKey = (id: number) => ['media-servers', id, 'status'] as const;

export const useMediaServers = () =>
  useQuery<MediaServer[], ApiError>({ queryKey: MEDIA_SERVERS_QUERY_KEY, queryFn: mediaServerService.list });

const useInvalidateServers = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: MEDIA_SERVERS_QUERY_KEY });
};

export const useCreateMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<MediaServer, ApiError, MediaServerCreate>({ mutationFn: mediaServerService.create, onSuccess: () => void invalidate() });
};

export const useUpdateMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<MediaServer, ApiError, { id: number; data: MediaServerUpdate }>({
    mutationFn: ({ id, data }) => mediaServerService.update(id, data),
    onSuccess: () => void invalidate(),
  });
};

export const useDeleteMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<void, ApiError, number>({ mutationFn: mediaServerService.remove, onSuccess: () => void invalidate() });
};

export const useTestMediaServer = () =>
  useMutation<MediaServerProbe, ApiError, MediaServerTestRequest>({ mutationFn: mediaServerService.test });

export const useConnectMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<MediaServer, ApiError, number>({ mutationFn: mediaServerService.connect, onSuccess: () => void invalidate() });
};

export const useRefreshMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<MediaServerRefreshResult, ApiError, number>({ mutationFn: mediaServerService.refresh, onSuccess: () => void invalidate() });
};

export const useDisconnectMediaServer = () => {
  const invalidate = useInvalidateServers();
  return useMutation<MediaServer, ApiError, number>({ mutationFn: mediaServerService.disconnect, onSuccess: () => void invalidate() });
};

/** Channel count, guide state and the Plex paste values for one card; polled while the card is on screen. */
export const useMediaServerStatus = (id: number, enabled = true) =>
  useQuery<MediaServerStatus, ApiError>({
    queryKey: mediaServerStatusKey(id),
    queryFn: () => mediaServerService.status(id),
    enabled,
    retry: false,
    refetchInterval: 30_000,
  });
