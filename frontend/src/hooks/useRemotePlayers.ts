import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../services/apiErrors';
import {
  remotePlayerService,
  type RemotePlayer,
  type RemotePlayerCommand,
  type RemotePlayerCreate,
  type RemotePlayerPlayResult,
  type RemotePlayerProbe,
  type RemotePlayerStatus,
  type RemotePlayerTestRequest,
  type RemotePlayerUpdate,
  type ScanRequest,
  type ScanResult,
} from '../services/remotePlayerService';

export const REMOTE_PLAYERS_QUERY_KEY = ['remote-players'] as const;
export const remotePlayerStatusKey = (id: number) => ['remote-players', id, 'status'] as const;

export const useRemotePlayers = () =>
  useQuery<RemotePlayer[], ApiError>({ queryKey: REMOTE_PLAYERS_QUERY_KEY, queryFn: remotePlayerService.list });

const useInvalidatePlayers = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: REMOTE_PLAYERS_QUERY_KEY });
};

export const useCreateRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<RemotePlayer, ApiError, RemotePlayerCreate>({ mutationFn: remotePlayerService.create, onSuccess: () => void invalidate() });
};

export const useUpdateRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<RemotePlayer, ApiError, { id: number; data: RemotePlayerUpdate }>({
    mutationFn: ({ id, data }) => remotePlayerService.update(id, data),
    onSuccess: () => void invalidate(),
  });
};

export const useDeleteRemotePlayer = () => {
  const invalidate = useInvalidatePlayers();
  return useMutation<void, ApiError, number>({ mutationFn: remotePlayerService.remove, onSuccess: () => void invalidate() });
};

export const useTestRemotePlayer = () =>
  useMutation<RemotePlayerProbe, ApiError, RemotePlayerTestRequest>({ mutationFn: remotePlayerService.test });

/** Live status for one player card; polled while the card is on screen. */
export const useRemotePlayerStatus = (id: number, enabled = true) =>
  useQuery<RemotePlayerStatus, ApiError>({
    queryKey: remotePlayerStatusKey(id),
    queryFn: () => remotePlayerService.status(id),
    enabled,
    retry: false,
    refetchInterval: 5_000,
  });

export const usePlayOnRemotePlayer = () =>
  useMutation<RemotePlayerPlayResult, ApiError, { id: number; contentId: string; title?: string }>({
    mutationFn: ({ id, contentId, title }) => remotePlayerService.play(id, contentId, title),
  });

export const useRemotePlayerCommand = () => {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, { id: number; command: RemotePlayerCommand; value?: number }>({
    mutationFn: ({ id, command, value }) => remotePlayerService.command(id, command, value),
    onSuccess: (_data, { id }) => void queryClient.invalidateQueries({ queryKey: remotePlayerStatusKey(id) }),
  });
};

export const useScanRemotePlayers = () => useMutation<ScanResult, ApiError, ScanRequest>({ mutationFn: remotePlayerService.scan });

export const useScanDefault = (enabled: boolean) =>
  useQuery({ queryKey: ['remote-players', 'scan-default'], queryFn: remotePlayerService.scanDefault, enabled, staleTime: 60_000 });
