import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  useCreateEPGSource,
  useUpdateEPGSource,
  useDeleteEPGSource,
  useRefreshAllEPGSources
} from './useEPG';
import { EPGSource, epgService } from '../services/epgService';
import { SnackbarSeverity } from './useSnackbar';

export interface EPGSourceFormData {
  url: string;
  name: string;
  enabled: boolean;
}

/**
 * Hook owning EPG source CRUD/refresh state and handlers for the EPG page.
 */
export interface EPGRefreshWatchOptions {
  /** How often to re-read a source while its refresh runs in the backend. */
  pollIntervalMs?: number;
  /** Give up waiting (the job keeps running server-side) after this long. */
  timeoutMs?: number;
}

const DEFAULT_REFRESH_POLL_MS = 3000;
const DEFAULT_REFRESH_TIMEOUT_MS = 15 * 60 * 1000;

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export const useEPGSourceManagement = (
  showSnackbar: (message: string, severity: SnackbarSeverity) => void,
  watchOptions: EPGRefreshWatchOptions = {}
) => {
  const queryClient = useQueryClient();
  const pollIntervalMs = watchOptions.pollIntervalMs ?? DEFAULT_REFRESH_POLL_MS;
  const refreshTimeoutMs = watchOptions.timeoutMs ?? DEFAULT_REFRESH_TIMEOUT_MS;
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);
  const [openSourceDialog, setOpenSourceDialog] = useState(false);
  const [isEditSource, setIsEditSource] = useState(false);
  const [editSourceId, setEditSourceId] = useState<number | null>(null);
  const [sourceFormData, setSourceFormData] = useState<EPGSourceFormData>({
    url: '',
    name: '',
    enabled: true
  });

  const { mutateAsync: createSource } = useCreateEPGSource();
  const { mutateAsync: updateSource } = useUpdateEPGSource(editSourceId || 0);
  const { mutateAsync: deleteSource } = useDeleteEPGSource();
  const { mutateAsync: refreshAllSources, isPending: isRefreshAllPending } = useRefreshAllEPGSources();
  const [isWatchingRefreshAll, setIsWatchingRefreshAll] = useState(false);
  const isRefreshingAll = isRefreshAllPending || isWatchingRefreshAll;

  /**
   * The backend queues the refresh and answers immediately; the only completion
   * signal is the source's `last_updated` moving. Poll it so the feedback we show
   * reflects what actually happened.
   */
  const waitForSourceRefresh = useCallback(
    async (id: number, previousLastUpdated: string | null | undefined): Promise<EPGSource | null> => {
      const deadline = Date.now() + refreshTimeoutMs;
      while (Date.now() < deadline) {
        await sleep(pollIntervalMs);
        if (!mountedRef.current) return null;
        const source = await epgService.getSource(id);
        if (source.last_updated && source.last_updated !== previousLastUpdated) {
          return source;
        }
      }
      return null;
    },
    [pollIntervalMs, refreshTimeoutMs]
  );

  const describeRefreshOutcome = async (source: EPGSource | null, name: string) => {
    if (!source) {
      showSnackbar(`EPG refresh for ${name} is still running. Reload the page later to see the result.`, 'warning');
      return;
    }
    if (source.last_error) {
      showSnackbar(`EPG refresh failed for ${name}: ${source.last_error}`, 'error');
      return;
    }
    const { total } = await epgService.getChannels(source.id, 0, 1);
    showSnackbar(`EPG source ${name} refreshed: ${total} channels loaded.`, 'success');
  };

  // State for tracking which source is being refreshed
  const [refreshingSourceId, setRefreshingSourceId] = useState<number | null>(null);

  // Source form handlers
  const handleAddSourceClick = () => {
    setIsEditSource(false);
    setEditSourceId(null);
    setSourceFormData({
      url: '',
      name: '',
      enabled: true
    });
    setOpenSourceDialog(true);
  };

  const handleEditSourceClick = (source: EPGSource) => {
    setIsEditSource(true);
    setEditSourceId(source.id);
    setSourceFormData({
      url: source.url,
      name: source.name,
      enabled: source.enabled
    });
    setOpenSourceDialog(true);
  };

  const handleCloseSourceDialog = () => {
    setOpenSourceDialog(false);
  };

  const handleSourceFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setSourceFormData({
      ...sourceFormData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSourceFormSubmit = async () => {
    try {
      if (isEditSource && editSourceId) {
        await updateSource(sourceFormData);
        showSnackbar('EPG source updated successfully', 'success');
      } else {
        await createSource(sourceFormData);
        showSnackbar('EPG source added successfully', 'success');
      }
      handleCloseSourceDialog();
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleDeleteSourceClick = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this EPG source?')) {
      try {
        await deleteSource(id);
        showSnackbar('EPG source deleted successfully', 'success');
      } catch (error) {
        showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      }
    }
  };

  const handleRefreshSourceClick = async (id: number) => {
    setRefreshingSourceId(id);
    let name = `source ${id}`;
    try {
      const before = await epgService.getSource(id);
      name = before.name || name;
      const result = await epgService.refreshSource(id);
      if (!result.success) {
        showSnackbar(`Error refreshing EPG source: ${result.error || 'Unknown error'}`, 'error');
        return;
      }
      showSnackbar(`EPG refresh started for ${name}. Large guides can take a few minutes.`, 'info');
      const after = await waitForSourceRefresh(id, before.last_updated);
      if (!mountedRef.current) return;
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      await describeRefreshOutcome(after, name);
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      if (mountedRef.current) setRefreshingSourceId(null);
    }
  };

  const handleRefreshAllClick = async () => {
    setIsWatchingRefreshAll(true);
    try {
      const sources = await epgService.getSources();
      const enabled = sources.filter((source) => source.enabled);
      const results = await refreshAllSources();
      const failedToStart = results.filter((r) => !r.success).length;
      if (enabled.length === 0) {
        showSnackbar('No enabled EPG sources to refresh.', 'warning');
        return;
      }
      showSnackbar(
        failedToStart === 0
          ? `EPG refresh started for ${enabled.length} source${enabled.length === 1 ? '' : 's'}. The table updates as each one finishes.`
          : `${failedToStart} of ${enabled.length} sources could not be started.`,
        failedToStart === 0 ? 'info' : 'warning'
      );
      const outcomes = await Promise.all(enabled.map((source) => waitForSourceRefresh(source.id, source.last_updated)));
      if (!mountedRef.current) return;
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      const finished = outcomes.filter((o): o is EPGSource => o !== null);
      const failed = finished.filter((o) => Boolean(o.last_error)).length;
      const stillRunning = outcomes.length - finished.length;
      if (failed === 0 && stillRunning === 0) {
        showSnackbar(`All ${finished.length} EPG sources refreshed successfully`, 'success');
      } else {
        const parts = [`${finished.length - failed} refreshed`];
        if (failed > 0) parts.push(`${failed} failed`);
        if (stillRunning > 0) parts.push(`${stillRunning} still running`);
        showSnackbar(`EPG refresh: ${parts.join(', ')}`, failed > 0 ? 'error' : 'warning');
      }
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      if (mountedRef.current) setIsWatchingRefreshAll(false);
    }
  };

  return {
    openSourceDialog,
    isEditSource,
    sourceFormData,
    refreshingSourceId,
    isRefreshingAll,
    handleAddSourceClick,
    handleEditSourceClick,
    handleCloseSourceDialog,
    handleSourceFormChange,
    handleSourceFormSubmit,
    handleDeleteSourceClick,
    handleRefreshSourceClick,
    handleRefreshAllClick
  };
};
