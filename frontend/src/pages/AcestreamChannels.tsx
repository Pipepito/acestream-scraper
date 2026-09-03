import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Snackbar, Stack, useMediaQuery, useTheme } from '@mui/material';
import { Add, FileDownload, Refresh } from '@mui/icons-material';
import type { GridSortModel } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { keepPreviousData } from '@tanstack/react-query';

import ChannelTable from '../components/ChannelTable';
import ChannelCardList from '../components/channels/ChannelCardList';
import ChannelFilterBar from '../components/channels/ChannelFilterBar';
import { useAcestreamChannels, useDeleteAcestreamChannel } from '../hooks/useChannels';
import { AcestreamChannel, AcestreamChannelFilters, UpdateAcestreamChannelDTO, acestreamChannelService } from '../services/channelService';
import { getErrorMessage } from '../utils/errorUtils';
import BulkOperations from '../components/BulkOperations';
import BatchAssignDialog from '../components/BatchAssignDialog';
import QuickEditDialog, { type QuickEditChannel, type QuickEditValues } from '../components/QuickEditDialog';
import AssignTVChannelDialog from '../components/AssignTVChannelDialog';
import { useAllTVChannels } from '../hooks/useTVChannels';
import { tvChannelService } from '../services/tvChannelService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import InlineStatusNotice from '../components/state/InlineStatusNotice';
import StatusLine from '../components/StatusLine';
import { useConfirm } from '../components/ConfirmDialog';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import PlayOnMenu from '../components/player/PlayOnMenu';

type SnackbarNotice = {
  message: string;
  error?: unknown;
};

interface BulkStatusCheckSummary {
  message?: string | null;
  background?: boolean;
  total_channels?: number;
  total_checked?: number;
  online_count?: number;
  offline_count?: number;
}

/** Turn the bulk status-check payload into one sentence a user can act on. */
export const describeBulkStatusCheck = (data: BulkStatusCheckSummary): string => {
  if (data.message) return data.message;
  if (data.background) {
    return `Status check started in the background for ${data.total_channels ?? 0} channels. Refresh the list in a few minutes to see the results.`;
  }
  const checked = data.total_checked ?? 0;
  return `Checked ${checked} channels: ${data.online_count ?? 0} online, ${data.offline_count ?? 0} offline.`;
};

const hasAnyFilter = (filters: AcestreamChannelFilters): boolean =>
  Boolean(filters.search || filters.group || filters.is_online !== undefined || filters.is_active !== undefined);

const AcestreamChannels: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isCompact = useMediaQuery(theme.breakpoints.down('md'));
  const { confirm, dialog: confirmDialog } = useConfirm();

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<AcestreamChannelFilters>({});
  const [checkingStatus, setCheckingStatus] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<SnackbarNotice | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [checkingAll, setCheckingAll] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [batchAssignOpen, setBatchAssignOpen] = useState(false);
  const [editorMode, setEditorMode] = useState<'edit' | 'create' | null>(null);
  const [editorChannel, setEditorChannel] = useState<QuickEditChannel | null>(null);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignTargetIds, setAssignTargetIds] = useState<string[]>([]);
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);
  const [groups, setGroups] = useState<string[]>([]);
  const [groupError, setGroupError] = useState<string | null>(null);
  const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string } | null>(null);
  const [playOnTarget, setPlayOnTarget] = useState<{ contentId: string; title: string } | null>(null);

  const {
    data: channelsData = { items: [], total: 0 },
    isLoading,
    refetch,
    error: fetchError,
  } = useAcestreamChannels({ ...filters, page: page + 1, page_size: pageSize }, { placeholderData: keepPreviousData });
  const { data: onlineData } = useAcestreamChannels({ is_online: true, page: 1, page_size: 1 });
  const { data: allData } = useAcestreamChannels({ page: 1, page_size: 1 });

  const channels = channelsData.items;
  const totalCount = channelsData.total;
  const deleteChannel = useDeleteAcestreamChannel();
  const { data: tvChannels } = useAllTVChannels(0, 100);
  const selectedChannels = useMemo(() => channels.filter((channel) => selectedIds.includes(channel.id)), [channels, selectedIds]);
  const filtered = hasAnyFilter(filters);

  useEffect(() => {
    if (!isLoading && page > 0 && page * pageSize >= totalCount) {
      setPage(0);
    }
  }, [isLoading, page, pageSize, totalCount]);

  useEffect(() => {
    setGroupError(null);
    acestreamChannelService
      .getGroups()
      .then((loadedGroups) => setGroups(loadedGroups ?? []))
      .catch((err) => setGroupError(getErrorMessage(err)));
  }, []);

  const handleFilterChange = useCallback((newFilters: AcestreamChannelFilters) => {
    setFilters((prevFilters) => {
      if (JSON.stringify(prevFilters) !== JSON.stringify(newFilters)) {
        setPage(0);
        return newFilters;
      }
      return prevFilters;
    });
  }, []);

  const handleSortChange = useCallback((model: GridSortModel) => {
    void model;
    setPage(0);
  }, []);

  const handleCopyId = useCallback(async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setNotice({ message: 'Acestream ID copied.' });
    } catch {
      setError('Unable to copy the Acestream ID right now.');
    }
  }, []);

  const handleCheckStatus = useCallback(
    (channel: AcestreamChannel) => {
      setCheckingStatus((prev) => ({ ...prev, [channel.id]: true }));
      acestreamChannelService
        .checkAcestreamChannelStatus(channel.id)
        .then(() => refetch())
        .catch((err) => setError(`Failed to check status: ${getErrorMessage(err)}`))
        .finally(() => setCheckingStatus((prev) => ({ ...prev, [channel.id]: false })));
    },
    [refetch]
  );

  const handleEdit = useCallback((channel: AcestreamChannel) => {
    setEditorChannel(channel);
    setEditorMode('edit');
  }, []);

  const handleAdd = () => {
    setEditorChannel({ id: '', name: '', group: '', logo: '', is_active: true });
    setEditorMode('create');
  };

  const closeEditor = () => {
    setEditorMode(null);
    setEditorChannel(null);
  };

  const handleEditorSave = async (values: QuickEditValues) => {
    if (editorMode === 'create') {
      await acestreamChannelService.createAcestreamChannel(values);
      setNotice({ message: `Added ${values.name}.` });
    } else if (editorChannel?.id) {
      const { id, ...updates } = values;
      void id;
      await acestreamChannelService.updateAcestreamChannel(editorChannel.id, updates);
      setNotice({ message: `Saved ${values.name}.` });
    }
    closeEditor();
    refetch();
  };

  const handleToggleHidden = useCallback(
    async (channel: AcestreamChannel) => {
      const hide = channel.is_active !== false;
      try {
        await acestreamChannelService.updateAcestreamChannel(channel.id, { is_active: !hide });
        setNotice({ message: hide ? `${channel.name} is now hidden from the playlist.` : `${channel.name} is back in the playlist.` });
        refetch();
      } catch (err) {
        setError(`Failed to update ${channel.name}: ${getErrorMessage(err)}`);
      }
    },
    [refetch]
  );

  const handleDelete = useCallback(
    async (channel: AcestreamChannel) => {
      const ok = await confirm({
        title: `Delete ${channel.name}?`,
        body: 'The channel is removed from the inventory and the playlist. It comes back if a source still lists it.',
        confirmLabel: 'Delete',
        danger: true,
      });
      if (!ok) return;
      deleteChannel.mutate(channel.id, {
        onSuccess: () => setNotice({ message: `Deleted ${channel.name}.` }),
        onError: (err) => setError(`Failed to delete channel: ${getErrorMessage(err)}`),
      });
    },
    [confirm, deleteChannel]
  );

  const handleOpenAssignDialog = useCallback((ids: string[]) => {
    setAssignTargetIds(ids);
    setAssignDialogOpen(true);
  }, []);

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
      setNotice({ message: `Linked ${assignTargetIds.length} channel${assignTargetIds.length === 1 ? '' : 's'} to ${assigned?.name ?? 'the TV channel'}.` });
      refetch();
    } catch (err) {
      setAssignError(getErrorMessage(err));
    } finally {
      setAssigning(false);
    }
  };

  const handleOpenTV = useCallback(
    (channel: AcestreamChannel) => {
      if (channel.tv_channel_id) navigate(`/tv-channels/${channel.tv_channel_id}`);
    },
    [navigate]
  );

  const handleToggleTVFavorite = useCallback(
    async (channel: AcestreamChannel) => {
      if (!channel.tv_channel_id) return;
      try {
        await tvChannelService.update(channel.tv_channel_id, { is_favorite: !channel.tv_channel_is_favorite });
        refetch();
      } catch (err) {
        setError(`Failed to update linked TV favorite: ${getErrorMessage(err)}`);
      }
    },
    [refetch]
  );

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
    try {
      const data = await acestreamChannelService.checkAllStatuses();
      setNotice({ message: describeBulkStatusCheck(data) });
    } catch (err) {
      setNotice({ message: getErrorMessage(err), error: err });
    } finally {
      setCheckingAll(false);
    }
  };

  const rowHandlers = {
    onPlay: (channel: AcestreamChannel) => setPlayerTarget({ contentId: channel.id, title: channel.name }),
    onPlayOn: (channel: AcestreamChannel) => setPlayOnTarget({ contentId: channel.id, title: channel.name }),
    onCheckStatus: handleCheckStatus,
    onEdit: handleEdit,
    onToggleHidden: handleToggleHidden,
    onAssignTV: (channel: AcestreamChannel) => handleOpenAssignDialog([channel.id]),
    onOpenTV: handleOpenTV,
    onToggleTVFavorite: handleToggleTVFavorite,
    onDelete: handleDelete,
  };

  const allTotal = allData?.total;
  const onlineTotal = onlineData?.total;

  return (
    <Box sx={{ width: '100%' }}>
      <PageHeader
        title="Acestream Channels"
        subtitle="Streams found by the scraper. Hide the ones you don't want in the playlist and link the rest to TV channels."
        actions={
          <Button variant="contained" startIcon={<Add />} onClick={handleAdd}>
            Add channel
          </Button>
        }
        overflowActions={[
          { label: 'Refresh', icon: <Refresh fontSize="small" />, onClick: () => void refetch() },
          { label: checkingAll ? 'Checking…' : 'Check all statuses', onClick: () => void handleCheckAllStatuses(), disabled: checkingAll },
          { label: 'Export CSV', icon: <FileDownload fontSize="small" />, onClick: () => void handleExportCSV() },
        ]}
      />

      <StatusLine
        aria-label="Channel summary"
        items={[
          { label: 'Channels', value: allTotal === undefined ? '…' : String(allTotal) },
          {
            label: 'Online',
            value: onlineTotal === undefined ? '…' : String(onlineTotal),
            tone: onlineTotal === 0 && (allTotal ?? 0) > 0 ? 'warning' : 'default',
          },
          { label: 'Matching filters', value: filtered ? String(totalCount) : 'all' },
          { label: 'Selected', value: String(selectedIds.length) },
        ]}
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

      <ContentSection
        title="Channels"
        actions={
          selectedIds.length > 0 ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)}>
                Bulk actions ({selectedIds.length})
              </Button>
              <Button variant="outlined" onClick={() => setBatchAssignOpen(true)}>
                Set group
              </Button>
              <Button variant="outlined" onClick={() => handleOpenAssignDialog(selectedIds)}>
                Link to TV channel
              </Button>
            </Stack>
          ) : undefined
        }
      >
        <ChannelFilterBar filters={filters} groups={groups} onChange={handleFilterChange} />
        {isCompact ? (
          <ChannelCardList
            channels={channels}
            loading={isLoading}
            checkingStatus={checkingStatus}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            totalCount={totalCount}
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onCopyId={handleCopyId}
            {...rowHandlers}
          />
        ) : (
          <ChannelTable
            channels={channels}
            loading={isLoading}
            checkingStatus={checkingStatus}
            hasActiveFilters={filtered}
            totalCount={totalCount}
            page={page}
            pageSize={pageSize}
            onPaginationModelChange={({ page: newPage, pageSize: newPageSize }) => {
              if (page !== newPage) setPage(newPage);
              if (pageSize !== newPageSize) setPageSize(newPageSize);
            }}
            onSortChange={handleSortChange}
            onSelectionChange={setSelectedIds}
            onCopyId={handleCopyId}
            {...rowHandlers}
          />
        )}
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
        open={editorMode !== null}
        mode={editorMode ?? 'edit'}
        onClose={closeEditor}
        channel={editorChannel}
        onSave={handleEditorSave}
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

      <StreamPlayerDialog
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
        extraActions={playerTarget ? <PlayOnMenu contentId={playerTarget.contentId} title={playerTarget.title} /> : undefined}
      />

      <Dialog
        open={Boolean(playOnTarget)}
        onClose={() => setPlayOnTarget(null)}
        aria-labelledby="acestream-play-on-title"
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle id="acestream-play-on-title">Play on…</DialogTitle>
        <DialogContent>
          {playOnTarget ? (
            <PlayOnMenu contentId={playOnTarget.contentId} title={playOnTarget.title} onDone={() => setPlayOnTarget(null)} />
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPlayOnTarget(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {confirmDialog}

      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={5000}
        onClose={() => setNotice(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setNotice(null)} severity={notice?.error ? 'error' : 'success'} sx={{ width: '100%' }}>
          {notice?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AcestreamChannels;
