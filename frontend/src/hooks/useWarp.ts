/**
 * React Query hooks for WARP service
 */
import { useQuery, useMutation, UseQueryResult, UseMutationResult, useQueryClient } from 'react-query';
import {
  getWarpStatus,
  connectWarp,
  disconnectWarp,
  setWarpMode,
  registerWarpLicense
} from '../services/warpService';
import { WarpStatus, WarpResponse, WarpMode } from '../types/warpTypes';

// Query keys
const WARP_KEYS = {
  all: ['warp'] as const,
  status: ['warp', 'status'] as const
};

/**
 * Hook for fetching WARP status
 */
export function useWarpStatus(): UseQueryResult<WarpStatus, Error> {
  return useQuery(WARP_KEYS.status, getWarpStatus, {
    refetchInterval: 10000, // Refetch status every 10 seconds
    staleTime: 5000
  });
}

/**
 * Hook for connecting to WARP
 */
export function useWarpConnect(): UseMutationResult<WarpResponse, Error, void> {
  const queryClient = useQueryClient();
  
  return useMutation(connectWarp, {
    onSuccess: () => {
      queryClient.invalidateQueries(WARP_KEYS.all);
    }
  });
}

/**
 * Hook for disconnecting from WARP
 */
export function useWarpDisconnect(): UseMutationResult<WarpResponse, Error, void> {
  const queryClient = useQueryClient();
  
  return useMutation(disconnectWarp, {
    onSuccess: () => {
      queryClient.invalidateQueries(WARP_KEYS.all);
    }
  });
}

/**
 * Hook for setting WARP mode
 */
export function useWarpSetMode(): UseMutationResult<WarpResponse, Error, WarpMode> {
  const queryClient = useQueryClient();
  
  return useMutation(setWarpMode, {
    onSuccess: () => {
      queryClient.invalidateQueries(WARP_KEYS.all);
    }
  });
}

/**
 * Hook for registering a WARP license
 */
export function useWarpRegisterLicense(): UseMutationResult<WarpResponse, Error, string> {
  const queryClient = useQueryClient();
  
  return useMutation(registerWarpLicense, {
    onSuccess: () => {
      queryClient.invalidateQueries(WARP_KEYS.all);
    }
  });
}
