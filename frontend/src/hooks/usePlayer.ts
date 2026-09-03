import { useMutation, useQuery } from '@tanstack/react-query';
import { playerService, type PlayerCapabilities, type PlayerSessionStatus } from '../services/playerService';
import { ApiError } from '../services/apiErrors';

export const PLAYER_CAPABILITIES_QUERY_KEY = ['player', 'capabilities'] as const;
export const playerSessionKey = (id: string) => ['player', 'session', id] as const;

/** Whether this server can prepare browser-playable streams (ffmpeg present). */
export const usePlayerCapabilities = () =>
  useQuery<PlayerCapabilities>({
    queryKey: PLAYER_CAPABILITIES_QUERY_KEY,
    queryFn: playerService.getCapabilities,
    staleTime: 60_000,
  });

export const useStartPlayerSession = () =>
  useMutation<PlayerSessionStatus, ApiError, string>({
    mutationFn: (contentId) => playerService.startSession(contentId),
  });

/** Polls the session: 2 s while starting (also the heartbeat), 10 s while ready, stops on error or once the session is gone. */
export const usePlayerSessionStatus = (id: string | null) =>
  useQuery<PlayerSessionStatus, ApiError>({
    queryKey: playerSessionKey(id ?? ''),
    queryFn: () => playerService.getSession(id as string),
    enabled: Boolean(id),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data;
      const error = query.state.error;
      if (error || !status || status.state === 'error' || status.state === 'stopped') return false;
      return status.state === 'ready' ? 10_000 : 2_000;
    },
  });
