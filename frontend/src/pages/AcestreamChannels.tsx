import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { normalizeApiError } from '../services/apiErrors';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Snackbar, Stack, useMediaQuery, useTheme } from '@mui/material';
import { Add, FileDownload, Refresh } from '@mui/icons-material';
import type { GridSortModel } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';

import ChannelTable from '../components/ChannelTable';
import ChannelCardList from '../components/channels/ChannelCardList';
import ChannelFilterBar from '../components/channels/ChannelFilterBar';
import { useAcestreamChannels, useDeleteAcestreamChannel } from '../hooks/useChannels';
import { AcestreamChannel, AcestreamChannelFilters, UpdateAcestreamChannelDTO, acestreamChannelService } from '../services/channelService';
import { getErrorMessage } from '../utils/errorUtils';
import BulkOperations from '../components/BulkOperations';
import BatchAssignDialog from '../components/BatchAssignDialog';
import QuickEditDialog, { type QuickEditChannel, type QuickEditValues } from '../components/QuickEditDialog';
import AssignTVChannelDialog, { type AssignChoice } from '../components/AssignTVChannelDialog';
import { useTVChannelCatalog } from '../hooks/useTVChannels';
import { tvChannelService } from '../services/tvChannelService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import InlineStatusNotice from '../components/state/InlineStatusNotice';
import StatusLine from '../components/StatusLine';
import { useConfirm } from '../components/ConfirmDialog';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import PlayOnMenu from '../components/player/PlayOnMenu';

type SnackbarNotice = {
  message: string | (() => string);
  error?: unknown;
  /** Set by callers that distinguish more than "worked"/"failed" (a warning). */
  severity?: 'success' | 'warning' | 'error';
};

const hasAnyFilter = (filters: AcestreamChannelFilters): boolean =>
  Boolean(filters.source_url || filters.search || filters.group || filters.is_online !== undefined || filters.is_active !== undefined || filters.assigned !== undefined);

const AcestreamChannels: React.FC = () => {
  const tUi = useUiText();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
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

  const sources = useQuery({ queryKey: ['channel-sources'], queryFn: acestreamChannelService.getSources });

  const channels = channelsData.items;
  const totalCount = channelsData.total;
  const deleteChannel = useDeleteAcestreamChannel();
  const { data: tvChannels, isLoading: loadingTVChannels, error: tvChannelsError, refetch: reloadTVChannels } = useTVChannelCatalog();
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
      setNotice({ message: uiText("Acestream ID copied.") });
    } catch {
      setNotice({ message: uiText("ID selected. Press Ctrl+C or ⌘C, or use your device’s Copy menu."), severity: 'warning' });
    }
  }, []);

  const handleCheckStatus = useCallback(
    (channel: AcestreamChannel) => {
      setCheckingStatus((prev) => ({ ...prev, [channel.id]: true }));
      acestreamChannelService
        .checkAcestreamChannelStatus(channel.id)
        .then(() => refetch())
        .catch((err) => setError(uiText('Failed to check status: {{error}}', { error: getErrorMessage(err) })))
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
      try {
        await acestreamChannelService.createAcestreamChannel(values);
      } catch (error) {
        const detail = normalizeApiError(error);
        if (detail.code !== 'IMPORT_EXCLUDED') throw error;
        const context = detail.context as { rule_ids?: number[] } | undefined;
        const ruleIds = context?.rule_ids ?? [];
        const accepted = await confirm(() => ({ title: uiText("Add excluded stream?"), body: <Stack spacing={1}><span>{tUi("This stream matches import rule")}{' '}{ruleIds.join(', ')}{tUi(". Add anyway applies only to this manual addition.")}</span><Button href={`/scraper?tab=exclusions#rule-${ruleIds[0] ?? ''}`}>{tUi("Review import exclusions")}</Button></Stack>, confirmLabel: uiText("Add anyway") }));
        if (!accepted) return;
        await acestreamChannelService.createAcestreamChannel({ ...values, allow_excluded: true });
      }
      if (values.tv_channel_id) {
        for (const key of ['tvChannels', 'tvChannel', 'tvChannelAcestreams']) void queryClient.invalidateQueries({ queryKey: [key] });
      }
      setNotice({ message: () => uiText('Added {{name}}.', { name: values.name }) });
    } else if (editorChannel?.id) {
      const { id, ...updates } = values;
      void id;
      await acestreamChannelService.updateAcestreamChannel(editorChannel.id, updates);
      setNotice({ message: () => uiText('Saved {{name}}.', { name: values.name }) });
    }
    closeEditor();
    refetch();
  };

  const handleToggleHidden = useCallback(
    async (channel: AcestreamChannel) => {
      const hide = channel.is_active !== false;
      try {
        await acestreamChannelService.updateAcestreamChannel(channel.id, { is_active: !hide });
        setNotice({ message: () => hide ? uiText('{{name}} is now hidden from the playlist.', { name: channel.name }) : uiText('{{name}} is back in the playlist.', { name: channel.name }) });
        refetch();
      } catch (err) {
        setError(uiText('Failed to update {{name}}: {{error}}', { name: channel.name, error: getErrorMessage(err) }));
      }
    },
    [refetch]
  );

  const handleDelete = useCallback(
    async (channel: AcestreamChannel) => {
      const ok = await confirm(() => ({
        title: uiText("Delete {{name}}?", { name: channel.name }),
        body: uiText("The channel is removed from the inventory and the playlist. It comes back if a source still lists it."),
        confirmLabel: uiText("Delete"),
        danger: true,
      }));
      if (!ok) return;
      deleteChannel.mutate(channel.id, {
        onSuccess: () => setNotice({ message: () => uiText('Deleted {{name}}.', { name: channel.name }) }),
        onError: (err) => setError(uiText('Failed to delete channel: {{error}}', { error: getErrorMessage(err) })),
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

  const handleAssignTVChannel = async (choice: AssignChoice) => {
    if (!('tvChannelId' in choice)) return;
    const tvChannelId = choice.tvChannelId;
    setAssigning(true);
    setAssignError(null);
    try {
      await Promise.all(assignTargetIds.map((id) => acestreamChannelService.assignToTVChannel(id, tvChannelId)));
      const assigned = tvChannels?.find((tvChannel) => tvChannel.id === tvChannelId);
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
      const linkedCount = assignTargetIds.length;
      setNotice({ message: () => assigned ? uiText('Linked {{count}} channels to {{name}}.', { count: linkedCount, name: assigned.name }) : uiText('Linked {{count}} channels to the TV channel.', { count: linkedCount }) });
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
        setError(uiText('Failed to update linked TV favorite: {{error}}', { error: getErrorMessage(err) }));
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
      setError(uiText('Failed to export CSV: {{error}}', { error: getErrorMessage(err) }));
    }
  };

  const handleCheckAllStatuses = async () => {
    setCheckingAll(true);
    try {
      const data = await acestreamChannelService.runStatusCheckNow();
      setNotice({ message: data.message, severity: data.status === 'disabled' ? 'warning' : 'success' });
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
        title={tUi("Acestream Channels")}
        subtitle={tUi("Streams found by the scraper. Hide the ones you don't want in the playlist and link the rest to TV channels.")}
        actions={
          <Button variant="contained" startIcon={<Add />} onClick={handleAdd}>
            {tUi("Add channel")}</Button>
        }
        overflowActions={[
          { label: uiText("Refresh"), icon: <Refresh fontSize="small" />, onClick: () => void refetch() },
          { label: checkingAll ? uiText("Requesting…") : uiText("Run status check now"), onClick: () => void handleCheckAllStatuses(), disabled: checkingAll },
          { label: uiText("Export CSV"), icon: <FileDownload fontSize="small" />, onClick: () => void handleExportCSV() },
        ]}
      />

      <StatusLine
        aria-label={tUi("Channel summary")}
        items={[
          { label: uiText("Channels"), value: allTotal === undefined ? '…' : String(allTotal) },
          {
            label: uiText("Online"),
            value: onlineTotal === undefined ? '…' : String(onlineTotal),
            tone: onlineTotal === 0 && (allTotal ?? 0) > 0 ? 'warning' : 'default',
          },
          { label: uiText("Matching filters"), value: filtered ? String(totalCount) : uiText('all') },
          { label: uiText("Selected"), value: String(selectedIds.length) },
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
            title={tUi("Unable to load channels")}
            description={getErrorMessage(fetchError)}
            action={
              <Button variant="outlined" onClick={() => refetch()}>
                {tUi("Try again")}</Button>
            }
          />
        </Box>
      ) : null}

      {groupError ? (
        <Box sx={{ mb: 2 }}>
          <InlineStatusNotice severity="error" title={tUi("Unable to load groups")} description={groupError} />
        </Box>
      ) : null}

      <ContentSection
        title={tUi("Channels")}
        actions={
          selectedIds.length > 0 ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)}>
                {tUi("Bulk actions (")}{selectedIds.length})
              </Button>
              <Button variant="outlined" onClick={() => setBatchAssignOpen(true)}>
                {tUi("Set group")}</Button>
              <Button variant="outlined" onClick={() => handleOpenAssignDialog(selectedIds)}>
                {tUi("Link to TV channel")}</Button>
            </Stack>
          ) : undefined
        }
      >
        {sources.isError ? <Alert severity="error" action={<Button onClick={() => void sources.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load source filters.")}</Alert> : null}
        <ChannelFilterBar filters={filters} groups={groups} sources={sources.data ?? []} onChange={handleFilterChange} />
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
        catalogLoading={loadingTVChannels}
        catalogError={tvChannelsError ? getErrorMessage(tvChannelsError) : null}
        onRetry={() => void reloadTVChannels()}
        onAssign={handleAssignTVChannel}
        loading={assigning}
        error={assignError}
      />

      <ChannelPlayerDialog
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
      />

      <Dialog
        open={Boolean(playOnTarget)}
        onClose={() => setPlayOnTarget(null)}
        aria-labelledby="acestream-play-on-title"
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle id="acestream-play-on-title">{tUi("Play on…")}</DialogTitle>
        <DialogContent>
          {playOnTarget ? (
            <PlayOnMenu
              contentId={playOnTarget.contentId}
              title={playOnTarget.title}
              onDone={() => setPlayOnTarget(null)}
              notify={(message, severity) => setNotice({ message, severity })}
            />
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPlayOnTarget(null)}>{tUi("Close")}</Button>
        </DialogActions>
      </Dialog>

      {confirmDialog}

      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={5000}
        onClose={() => setNotice(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setNotice(null)}
          severity={notice?.severity ?? (notice?.error ? 'error' : 'success')}
          sx={{ width: '100%' }}
        >
          {typeof notice?.message === 'function' ? notice.message() : notice?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AcestreamChannels;
