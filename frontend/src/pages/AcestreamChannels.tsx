import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Button, Alert, IconButton, Snackbar, Stack, Tooltip, useMediaQuery, useTheme } from '@mui/material';
import { Add, FileDownload, Refresh } from '@mui/icons-material';
import TvIcon from '@mui/icons-material/Tv';
import type { GridSortModel } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';

import ChannelTable from '../components/ChannelTable';
import { useAcestreamChannels, useDeleteAcestreamChannel } from '../hooks/useChannels';
import {
  AcestreamChannel,
  AcestreamChannelFilters,
  CreateAcestreamChannelDTO,
  UpdateAcestreamChannelDTO,
  acestreamChannelService,
} from '../services/channelService';
import { ApiError, getApiErrorKindFromStatus } from '../services/apiErrors';
import { getErrorMessage } from '../utils/errorUtils';
import BulkOperations from '../components/BulkOperations';
import AdvancedSearch, { AdvancedSearchFilters } from '../components/AdvancedSearch';
import BatchAssignDialog from '../components/BatchAssignDialog';
import QuickEditDialog from '../components/QuickEditDialog';
import AssignTVChannelDialog from '../components/AssignTVChannelDialog';
import { useAllTVChannels } from '../hooks/useTVChannels';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import InlineStatusNotice from '../components/state/InlineStatusNotice';

type EditableChannel = Partial<AcestreamChannel> & { id?: string };
type SnackbarNotice = {
  message: string;
  error?: unknown;
};

function mapFiltersToAdvanced(filters: AcestreamChannelFilters): AdvancedSearchFilters {
  return {
    search: filters.search,
    group: filters.group,
    country: filters.country,
    language: filters.language,
    is_active: typeof filters.is_active === 'boolean' ? String(filters.is_active) : '',
    is_online: typeof filters.is_online === 'boolean' ? String(filters.is_online) : '',
  };
}

function mapAdvancedToFilters(filters: AdvancedSearchFilters): AcestreamChannelFilters {
  return {
    search: filters.search || undefined,
    group: filters.group || undefined,
    country: filters.country || undefined,
    language: filters.language || undefined,
    is_active: filters.is_active === '' || filters.is_active === undefined ? undefined : filters.is_active === 'true',
    is_online: filters.is_online === '' || filters.is_online === undefined ? undefined : filters.is_online === 'true',
  };
}

const AcestreamChannels: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<AcestreamChannelFilters>({});
  const [checkingStatus, setCheckingStatus] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [checkingAll, setCheckingAll] = useState(false);
  const [checkAllResult, setCheckAllResult] = useState<SnackbarNotice | null>(null);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [batchAssignOpen, setBatchAssignOpen] = useState(false);
  const [quickEditOpen, setQuickEditOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignTargetIds, setAssignTargetIds] = useState<string[]>([]);
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);
  const [quickEditChannel, setQuickEditChannel] = useState<EditableChannel | null>(null);
  const [groups, setGroups] = useState<string[]>([]);
  const [groupError, setGroupError] = useState<string | null>(null);
  const [groupLoading, setGroupLoading] = useState(false);

  const {
    data: channelsData = { items: [], total: 0 },
    isLoading,
    refetch,
    error: fetchError,
  } = useAcestreamChannels(
    {
      ...filters,
      page: page + 1,
      page_size: pageSize,
    },
    { keepPreviousData: true }
  );

  const channels = channelsData.items;
  const totalCount = channelsData.total;
  const selectedChannels = useMemo(
    () => channels.filter((channel) => selectedIds.includes(channel.id)),
    [channels, selectedIds]
  );

  const deleteChannel = useDeleteAcestreamChannel();
  const { data: tvChannels } = useAllTVChannels(0, 100);

  useEffect(() => {
    if (!isLoading && page > 0 && page * pageSize >= totalCount) {
      setPage(0);
    }
  }, [isLoading, page, pageSize, totalCount]);

  useEffect(() => {
    setGroupLoading(true);
    setGroupError(null);
    acestreamChannelService
      .getGroups()
      .then((loadedGroups) => setGroups(loadedGroups ?? []))
      .catch((err) => setGroupError(getErrorMessage(err)))
      .finally(() => setGroupLoading(false));
  }, []);

  const handleCheckStatus = useCallback(
    (id: string) => {
      setCheckingStatus((prev) => ({ ...prev, [id]: true }));
      acestreamChannelService
        .checkAcestreamChannelStatus(id)
        .then(() => refetch())
        .catch((err) => setError(`Failed to check status: ${getErrorMessage(err)}`))
        .finally(() => setCheckingStatus((prev) => ({ ...prev, [id]: false })));
    },
    [refetch]
  );

  const handleQuickEdit = (channel: AcestreamChannel) => {
    setQuickEditChannel(channel);
    setQuickEditOpen(true);
  };

  const handleQuickEditSave = async (updates: UpdateAcestreamChannelDTO) => {
    if (!quickEditChannel?.id) {
      return;
    }

    await acestreamChannelService.updateAcestreamChannel(quickEditChannel.id, updates);
    setQuickEditOpen(false);
    setQuickEditChannel(null);
    refetch();
  };

  const handleAddChannel = () => {
    setQuickEditChannel({
      id: '',
      name: '',
      group: '',
      logo: '',
      is_active: true,
    });
    setAddDialogOpen(true);
  };

  const handleAddChannelSave = async (values: CreateAcestreamChannelDTO) => {
    if (!values.id || !values.name) {
      setError('Acestream ID and name are required.');
      return;
    }

    await acestreamChannelService.createAcestreamChannel(values);
    setAddDialogOpen(false);
    setQuickEditChannel(null);
    refetch();
  };

  const handleDelete = useCallback(
    (id: string) =>
      new Promise<boolean>((resolve, reject) => {
        if (window.confirm('Are you sure you want to delete this channel?')) {
          deleteChannel.mutate(id, {
            onSuccess: () => {
              resolve(true);
            },
            onError: (err) => {
              setError(`Failed to delete channel: ${getErrorMessage(err)}`);
              reject(err);
            },
          });
          return;
        }

        resolve(false);
      }),
    [deleteChannel]
  );

  const handleOpenAssignDialog = (ids: string[]) => {
    setAssignTargetIds(ids);
    setAssignDialogOpen(true);
  };

  const handleCloseAssignDialog = () => {
    setAssignDialogOpen(false);
    setAssignTargetIds([]);
    setAssignError(null);
  };

  const handleAssignTVChannel = async (tvChannelId: number) => {
    setAssigning(true);
    setAssignError(null);
    try {
      await Promise.all(assignTargetIds.map((id) => acestreamChannelService.assignToTVChannel(id, tvChannelId)));

      const assigned = tvChannels?.items.find((tvChannel) => tvChannel.id === tvChannelId);
      if (assigned) {
        await Promise.all(
          assignTargetIds.map((id) =>
            acestreamChannelService.updateAcestreamChannel(id, {
              tvg_id: assigned.epg_id || '',
              tvg_name: assigned.name,
              group: assigned.category || '',
              logo: assigned.logo_url || '',
            })
          )
        );
      }

      handleCloseAssignDialog();
      refetch();
    } catch (err) {
      setAssignError(getErrorMessage(err));
    } finally {
      setAssigning(false);
    }
  };

  const handleFilterChange = useCallback((newFilters: AcestreamChannelFilters) => {
    setFilters((prevFilters) => {
      if (JSON.stringify(prevFilters) !== JSON.stringify(newFilters)) {
        setPage(0);
        return newFilters;
      }

      return prevFilters;
    });
  }, []);

  const handleAdvancedFilterChange = (newFilters: AdvancedSearchFilters) => {
    handleFilterChange(mapAdvancedToFilters(newFilters));
  };

  const handleSortChange = useCallback((model: GridSortModel) => {
    void model;
    setPage(0);
  }, []);

  const handleBulkEdit = async (updates: Partial<UpdateAcestreamChannelDTO>) => {
    await acestreamChannelService.bulkEditAcestreamChannels(selectedIds, updates);
    refetch();
  };

  const handleBulkDelete = async (ids: string[] = selectedIds) => {
    await acestreamChannelService.bulkDeleteAcestreamChannels(ids);
    setSelectedIds([]);
    refetch();
  };

  const handleBulkActivate = async (active: boolean) => {
    await acestreamChannelService.bulkActivateAcestreamChannels(selectedIds, active);
    refetch();
  };

  const handleBatchAssign = async (group: string) => {
    await acestreamChannelService.bulkEditAcestreamChannels(selectedIds, { group });
    refetch();
  };

  const handleExportCSV = async () => {
    try {
      const blob = await acestreamChannelService.exportAcestreamChannelsCSV();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'acestream_channels.csv';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Failed to export CSV: ${getErrorMessage(err)}`);
    }
  };

  const handleCheckAllStatuses = async () => {
    setCheckingAll(true);
    setCheckAllResult(null);
    try {
      const response = await fetch('/api/v1/channels/check_status_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        const payload = (await response.json()) as { error?: { message?: string }; detail?: string };
        const error = new ApiError({
          message: payload.error?.message ?? payload.detail ?? response.statusText ?? 'Request failed',
          status: response.status,
          kind: getApiErrorKindFromStatus(response.status),
          canRetry: response.status >= 500 || response.status === 429,
          data: payload,
        });

        setCheckAllResult({ message: getErrorMessage(error), error });
        return;
      }
      const data = (await response.json()) as { message?: string };
      setCheckAllResult({ message: data.message || 'Acestream status check task triggered successfully.' });
    } catch (err) {
      setCheckAllResult({ message: getErrorMessage(err), error: err });
    } finally {
      setCheckingAll(false);
    }
  };

  const checkAllSeverity = checkAllResult?.error ? 'error' : 'success';

  return (
    <Box sx={{ width: '100%' }}>
      <PageHeader
        title="Acestream Channels"
        subtitle="Manage source channels, status checks, grouping, and TV-channel assignments."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" startIcon={<Refresh />} onClick={() => refetch()}>
              Refresh
            </Button>
            <Button variant="outlined" onClick={handleCheckAllStatuses} disabled={checkingAll}>
              {checkingAll ? 'Checking...' : 'Check All Statuses'}
            </Button>
            <Button variant="outlined" startIcon={<FileDownload />} onClick={handleExportCSV}>
              CSV
            </Button>
            <Button variant="contained" startIcon={<Add />} onClick={handleAddChannel}>
              Add
            </Button>
          </Stack>
        }
      />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      ) : null}

      {fetchError ? (
        <Box sx={{ mb: 2 }}>
          <InlineStatusNotice
            severity="error"
            title="Unable to load channels"
            description={getErrorMessage(fetchError)}
            action={
              <Button variant="outlined" onClick={() => refetch()}>
                Try again
              </Button>
            }
          />
        </Box>
      ) : null}

      {groupError ? (
        <Box sx={{ mb: 2 }}>
          <InlineStatusNotice severity="error" title="Unable to load groups" description={groupError} />
        </Box>
      ) : null}

      <ContentSection title="Filters" description="Use table and field filters to narrow channels quickly.">
        <AdvancedSearch
          filters={mapFiltersToAdvanced(filters)}
          groups={groups}
          onChange={handleAdvancedFilterChange}
        />
      </ContentSection>

      <ContentSection
        title="Channels"
        description="Review stream health, edit metadata, and assign channels to TV entries."
        actions={
          selectedIds.length > 0 ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)}>
                Bulk Actions ({selectedIds.length})
              </Button>
              <Button variant="outlined" onClick={() => setBatchAssignOpen(true)}>
                Batch Group
              </Button>
              <Button variant="outlined" onClick={() => handleOpenAssignDialog(selectedIds)}>
                Assign TV Channel
              </Button>
            </Stack>
          ) : undefined
        }
      >
        <ChannelTable
          channels={channels}
          loading={isLoading || groupLoading}
          onCheckStatus={handleCheckStatus}
          onEdit={handleQuickEdit}
          onDelete={handleDelete}
          checkingStatus={checkingStatus}
          filters={filters}
          onFilterChange={handleFilterChange}
          totalCount={totalCount}
          page={page}
          pageSize={pageSize}
          onPaginationModelChange={({ page: newPage, pageSize: newPageSize }) => {
            if (page !== newPage) {
              setPage(newPage);
            }
            if (pageSize !== newPageSize) {
              setPageSize(newPageSize);
            }
          }}
          onSortChange={handleSortChange}
          onSelectionChange={setSelectedIds}
          onActionComplete={refetch}
          extraActions={(row) => {
            const assignedTvChannel = tvChannels?.items.find((tvChannel) => tvChannel.id === row.tv_channel_id);
            if (row.tv_channel_id && assignedTvChannel) {
              return (
                <Tooltip title={`Open TV channel: ${assignedTvChannel.name}`} arrow>
                  <IconButton color="primary" aria-label={`go to tv channel ${assignedTvChannel.name}`} onClick={() => navigate(`/tv-channels/${assignedTvChannel.id}`)}>
                    <TvIcon />
                  </IconButton>
                </Tooltip>
              );
            }

            return (
              <Tooltip title="Assign to TV Channel" arrow>
                <IconButton aria-label={`assign tv channel to ${row.name}`} onClick={() => handleOpenAssignDialog([row.id])}>
                  <TvIcon />
                </IconButton>
              </Tooltip>
            );
          }}
        />
      </ContentSection>

      <BulkOperations
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        selectedChannels={selectedChannels}
        onBulkEdit={handleBulkEdit}
        onBulkDelete={handleBulkDelete}
        onBulkActivate={handleBulkActivate}
      />

      <BatchAssignDialog
        open={batchAssignOpen}
        onClose={() => setBatchAssignOpen(false)}
        selectedChannels={selectedChannels}
        groups={groups}
        onAssign={handleBatchAssign}
      />

      <QuickEditDialog
        open={quickEditOpen}
        onClose={() => setQuickEditOpen(false)}
        channel={quickEditChannel}
        onSave={handleQuickEditSave}
        fullScreen={isMobile}
      />

      <QuickEditDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        channel={quickEditChannel}
        onSave={handleAddChannelSave}
        fullScreen={isMobile}
      />

      <AssignTVChannelDialog
        open={assignDialogOpen}
        onClose={handleCloseAssignDialog}
        tvChannels={tvChannels}
        onAssign={handleAssignTVChannel}
        loading={assigning}
        error={assignError}
      />

      <Snackbar
        open={Boolean(checkAllResult)}
        autoHideDuration={5000}
        onClose={() => setCheckAllResult(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setCheckAllResult(null)} severity={checkAllSeverity} sx={{ width: '100%' }}>
          {checkAllResult?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AcestreamChannels;
