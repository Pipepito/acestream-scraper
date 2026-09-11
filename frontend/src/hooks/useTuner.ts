import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../services/apiErrors';
import { tunerService, type TunerSettings, type TunerSettingsUpdate, type TunerStatus } from '../services/tunerService';

export const TUNER_STATUS_QUERY_KEY = ['tuner', 'status'] as const;
export const TUNER_SETTINGS_QUERY_KEY = ['tuner', 'settings'] as const;

/** What the tuner would serve right now, plus how the allowlist sees this caller. */
export const useTunerStatus = () =>
  useQuery<TunerStatus, ApiError>({
    queryKey: TUNER_STATUS_QUERY_KEY,
    queryFn: tunerService.getStatus,
    refetchInterval: 30_000,
  });

export const useTunerSettings = () =>
  useQuery<TunerSettings, ApiError>({ queryKey: TUNER_SETTINGS_QUERY_KEY, queryFn: tunerService.getSettings });

export const useUpdateTunerSettings = () => {
  const queryClient = useQueryClient();
  return useMutation<TunerSettings, ApiError, TunerSettingsUpdate>({
    mutationFn: tunerService.updateSettings,
    // The lineup size and the friendly name both come back in the status.
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['tuner'] }),
  });
};
