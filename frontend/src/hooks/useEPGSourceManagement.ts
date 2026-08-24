import React, { useState } from 'react';
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
export const useEPGSourceManagement = (
  showSnackbar: (message: string, severity: SnackbarSeverity) => void
) => {
  const queryClient = useQueryClient();
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
  const { mutateAsync: refreshAllSources, isPending: isRefreshingAll } = useRefreshAllEPGSources();

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
    try {
      setRefreshingSourceId(id);
      // Use the epgService directly since we need to pass the specific source ID
      const result = await epgService.refreshSource(id);
      if (result.success) {
        showSnackbar(`EPG source refreshed successfully. Found ${result.channels_found} channels and ${result.programs_found} programs.`, 'success');
      } else {
        showSnackbar(`Error refreshing EPG source: ${result.error || 'Unknown error'}`, 'error');
      }
      // Invalidate queries to refresh the data
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setRefreshingSourceId(null);
    }
  };

  const handleRefreshAllClick = async () => {
    try {
      const results = await refreshAllSources();
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;

      if (failCount === 0) {
        showSnackbar(`All ${results.length} EPG sources refreshed successfully`, 'success');
      } else {
        showSnackbar(`${successCount} sources refreshed, ${failCount} failed`, 'warning');
      }
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
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
