/**
 * React Query hooks for WARP service
 */
import { useQuery, useMutation, UseQueryResult, UseMutationResult, useQueryClient } from '@tanstack/react-query';
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
  return useQuery({
    queryKey: WARP_KEYS.status,
    queryFn: getWarpStatus,
    refetchInterval: 10000, // Refetch status every 10 seconds
    staleTime: 5000
  });
}

/**
 * Hook for connecting to WARP
 */
export function useWarpConnect(): UseMutationResult<WarpResponse, Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: connectWarp,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WARP_KEYS.all });
    }
  });
}

/**
 * Hook for disconnecting from WARP
 */
export function useWarpDisconnect(): UseMutationResult<WarpResponse, Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disconnectWarp,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WARP_KEYS.all });
    }
  });
}

/**
 * Hook for setting WARP mode
 */
export function useWarpSetMode(): UseMutationResult<WarpResponse, Error, WarpMode> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: setWarpMode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WARP_KEYS.all });
    }
  });
}

/**
 * Hook for registering a WARP license
 */
export function useWarpRegisterLicense(): UseMutationResult<WarpResponse, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: registerWarpLicense,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WARP_KEYS.all });
    }
  });
}
