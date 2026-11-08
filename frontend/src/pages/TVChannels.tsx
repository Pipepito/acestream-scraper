import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { lazy, Suspense, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  Switch,
  Alert,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useReorderTVChannels, useTVChannelCatalog, useTVChannelPage, useTVInventory, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel, useToggleTVChannelFavorite } from '../hooks/useTVChannels';
import { useTVChannelForm } from '../hooks/useTVChannelForm';
import TVChannelFilters, { TVFilters } from '../components/TVChannelFilters';
import { GridSortModel } from '@mui/x-data-grid';
import TVChannelsTable from '../components/TVChannelsTable';
import TVChannelFormDialog from '../components/TVChannelFormDialog';
import TVChannelDeleteDialog from '../components/TVChannelDeleteDialog';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import { getShellLayout } from '../styles/layout';
import type { TVBrowseParams } from '../services/tvChannelService';

const TVChannelReorder = lazy(() => import('../components/TVChannelReorder'));
const TVAutoMatchDialog = lazy(() => import('../components/TVAutoMatchDialog'));

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const TVChannels: React.FC = () => {
  const tUi = useUiText();
  const [reordering, setReordering] = useState(false);
  const reorderMutation = useReorderTVChannels();
  const [autoMatchOpen, setAutoMatchOpen] = useState(false);
  const theme = useTheme();
  const shellLayout = getShellLayout(theme);
  const isPhone = useMediaQuery(`(max-width:${shellLayout.phoneMaxWidth}px)`);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[1]);
  const [filters, setFilters] = useState<TVFilters>({});
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [sortModel, setSortModel] = useState<GridSortModel>([]);
  const [deleteCandidate, setDeleteCandidate] = useState<TVChannel | null>(null);
  const [notice, setNotice] = useState<{ message: () => string; error?: boolean } | null>(null);
  const saving = useRef(false);
  const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string; tvChannelId: number } | null>(null);
  const {
    openCreateDialog,
    setOpenCreateDialog,
    openEditDialog,
    setOpenEditDialog,
    selectedChannel,
    formData,
    formErrors,
    setFormErrors,
    handleOpenCreateDialog,
    handleOpenEditDialog,
    handleFormChange,
    validateForm,
  } = useTVChannelForm();

  const skip = (page - 1) * pageSize;
  const params: TVBrowseParams = { skip, limit: pageSize };
  Object.entries(filters).forEach(([key, value]) => {
    if (value === '') return;
    Object.assign(params, { [key]: key === 'is_active' || key === 'is_favorite' ? value === 'true' : key === 'epg_source_id' || key.startsWith('min_') || key.startsWith('max_') ? Number(value) : value });
  });
  if (favoritesOnly) params.is_favorite = true;
  const sort = sortModel[0];
  if (sort?.sort) { params.sort = sort.field as TVBrowseParams['sort']; params.direction = sort.sort; }
  const catalog = useTVChannelPage(params);
  const inventory = useTVInventory();
  const completeCatalog = useTVChannelCatalog(undefined, undefined, reordering);
  const channelCatalog = catalog.data;
  const isCatalogLoading = catalog.isLoading;
  const isCatalogError = catalog.isError;
  const refetchCatalog = () => { void inventory.refetch(); return catalog.refetch(); };
  const deleteMutation = useDeleteTVChannel();
  const createMutation = useCreateTVChannel();
  const updateMutation = useUpdateTVChannel();
  const toggleFavoriteMutation = useToggleTVChannelFavorite();

  const channels = useMemo(() => channelCatalog?.items ?? [], [channelCatalog]);
  const paginatedChannels = channels;
  const totalChannels = channelCatalog?.total ?? 0;
  React.useEffect(() => {
    if (!catalog.isPlaceholderData && channelCatalog) {
      const maxPage = Math.max(1, Math.ceil(totalChannels / pageSize));
      if (page > maxPage) setPage(maxPage);
    }
  }, [catalog.isPlaceholderData, channelCatalog, totalChannels, page, pageSize]);
  const hasFilters = favoritesOnly || Object.values(filters).some(Boolean);
  const inventoryTotal = inventory.data?.total ?? totalChannels;
  const favoriteCount = inventory.data?.favorites;
  const withStreamsCount = inventory.data?.with_streams;
  const handleFiltersChange = (nextFilters: TVFilters) => {
    setPage(1);
    setFilters(nextFilters);
    if (nextFilters.is_favorite !== filters.is_favorite) setFavoritesOnly(false);
    if (!Object.keys(nextFilters).length) setFavoritesOnly(false);
  };

  const handleFavoritesOnlyChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPage(1);
    setFavoritesOnly(event.target.checked);
    setFilters(current => ({ ...current, is_favorite: '' }));
  };

  const handleToggleFavorite = async (channel: TVChannel) => {
    try {
      // Send the intended state explicitly (idempotent under double-clicks)
      // and derive the notice from the server's response, not the possibly
      // stale row the user clicked.
      const updated = await toggleFavoriteMutation.mutateAsync({ id: channel.id, value: !channel.is_favorite });
      setNotice({ message: () => updated.is_favorite ? tUi('Added {{name}} to favorites.', { name: channel.name }) : tUi('Removed {{name}} from favorites.', { name: channel.name }) });
    } catch {
      setNotice({ message: () => tUi('Failed to update favorite state.'), error: true });
    }
  };

  const handleCreate = async () => {
    if (saving.current) return;
    const payload = validateForm();

    if (!payload) {
      return;
    }

    saving.current = true;
    try {
      await createMutation.mutateAsync(payload as TVChannelCreate);
      setOpenCreateDialog(false);
      setNotice({ message: () => tUi('TV channel created.') });
    } catch (error) {
      setFormErrors({ submit: error });
    } finally { saving.current = false; }
  };

  const handleUpdate = async () => {
    if (saving.current) return;
    if (!selectedChannel) {
      return;
    }

    const payload = validateForm();

    if (!payload) {
      return;
    }

    saving.current = true;
    try {
      await updateMutation.mutateAsync({
        id: selectedChannel.id,
        updates: payload as TVChannelUpdate,
      });
      setOpenEditDialog(false);
      setNotice({ message: () => tUi('TV channel updated.') });
    } catch (error) {
      setFormErrors({ submit: error });
    } finally { saving.current = false; }
  };

  const handleRequestDelete = (id: number) => {
    const channel = channels.find((item) => item.id === id) ?? null;
    setDeleteCandidate(channel);
  };

  const handleConfirmDelete = async () => {
    if (saving.current) return;
    if (!deleteCandidate) {
      return;
    }

    saving.current = true;
    try {
      await deleteMutation.mutateAsync(deleteCandidate.id);
      setNotice({ message: () => tUi('TV channel deleted.') });
      setDeleteCandidate(null);
    } catch {
      setNotice({ message: () => tUi('Failed to delete TV channel.'), error: true });
    } finally { saving.current = false; }
  };

  if (isCatalogLoading) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="50vh" gap={1.5}>
        <CircularProgress aria-label={tUi("Loading TV channels")} />
        <Typography variant="sectionTitle" component="p">
          {tUi("Loading TV channels")}</Typography>
        <Typography variant="body2" color="text.secondary" align="center">
          {tUi("Preparing the latest TV channel inventory and actions.")}</Typography>
      </Box>
    );
  }

  if (isCatalogError && !channelCatalog) {
    return (
      <Box p={3}>
        <Stack spacing={2} alignItems="flex-start">
          <Alert severity="error">{tUi("We could not load the TV channel inventory. Try refreshing to reconnect.")}</Alert>
          <Button variant="outlined" disabled={reordering} onClick={() => refetchCatalog()}>
            {tUi("Retry loading TV channels")}</Button>
        </Stack>
      </Box>
    );
  }

  const dialogMobileProps = isPhone
    ? {
        fullScreen: true,
      }
    : {
        fullScreen: false,
        fullWidth: true,
        maxWidth: 'sm' as const,
      };

  return (
    <Box sx={{ width: '100%' }}>
      <PageHeader
        title={tUi("TV Channels")}
        subtitle={tUi("The channels you publish. Each one groups its streams and carries the EPG for the playlist.")}
        primaryActions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" disabled={reordering || inventoryTotal < 2} onClick={() => setReordering(true)}>{tUi("Reorder channels")}</Button>
            <Button variant="outlined" disabled={reordering} onClick={() => setAutoMatchOpen(true)}>{tUi("Auto-match streams")}</Button>
            <Button variant="outlined" disabled={reordering} onClick={() => refetchCatalog()}>
              {tUi("Refresh")}</Button>
            <Button variant="contained" color="primary" disabled={reordering} onClick={handleOpenCreateDialog}>
              {tUi("Add TV Channel")}</Button>
          </Stack>
        }
      />

      <StatusLine
        aria-label={tUi("TV channel summary")}
        items={[
          { label: favoritesOnly ? uiText("Favorites") : uiText("Channels"), value: String(inventoryTotal) },
          ...(favoritesOnly ? [] : [{ label: uiText("Favorites"), value: favoriteCount == null ? '—' : String(favoriteCount) }]),
          { label: uiText("With streams"), value: withStreamsCount == null ? '—' : String(withStreamsCount), tone: withStreamsCount === 0 && inventoryTotal > 0 ? 'warning' as const : 'default' as const },
          { label: uiText("Matching filters"), value: hasFilters ? String(totalChannels) : 'all' },
        ]}
      />

      {notice ? (
        <Alert severity={notice.error ? 'error' : 'success'} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice.message()}
        </Alert>
      ) : null}

      <Box data-testid="tv-channels-page-layout">
        <ContentSection
          title={tUi("Channels")}

        >
          {reordering ? completeCatalog.isLoading ? <CircularProgress aria-label={tUi("Loading TV channels")} /> : completeCatalog.isError ? <Alert severity="error" action={<Button onClick={() => void completeCatalog.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load channels.")}<Button onClick={() => setReordering(false)}>{tUi("Cancel")}</Button></Alert> : <Suspense fallback={<CircularProgress aria-label={tUi("Loading TV channels")} />}><TVChannelReorder channels={completeCatalog.data ?? []} onCancel={() => setReordering(false)} onSave={async (ids, expected) => {
            await reorderMutation.mutateAsync({ ids, expected });
            setSortModel([]); setFilters({}); setFavoritesOnly(false); setPage(1);
            setReordering(false); setNotice({ message: () => tUi('Channel order and numbers saved.') });
          }} /></Suspense> : <>
          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch checked={favoritesOnly} onChange={handleFavoritesOnlyChange} name="favorites_only" color="primary" />}
              label={tUi("Favorites only")}
            />
            <Box id="tv-channels-filters-panel">
              <TVChannelFilters channels={channels} inventory={inventory.data} filters={filters} onChange={handleFiltersChange} />
            </Box>
          </Box>
          <TVChannelsTable
            channels={paginatedChannels}
            loading={catalog.isFetching}
            totalCount={totalChannels}
            page={page - 1}
            pageSize={pageSize}
            onPageChange={(nextPage) => setPage(nextPage + 1)}
            onPageSizeChange={(size) => { setPage(1); setPageSize(size); }}
            onSortChange={(model) => { setPage(1); setSortModel(model); }}
            onNumberChange={async (channel, number) => { await updateMutation.mutateAsync({ id: channel.id, updates: { channel_number: number } }); setNotice({ message: () => tUi('Updated number for {{name}}.', { name: channel.name }) }); }}
            onEdit={handleOpenEditDialog}
            onDelete={handleRequestDelete}
            onOpen={(id) => navigate(`/tv-channels/${id}`)}
            onToggleFavorite={handleToggleFavorite}
            onPlay={(channel) => setPlayerTarget({ contentId: channel.acestream_channels[0].id, title: channel.name, tvChannelId: channel.id })}
          />
          {totalChannels === 0 && hasFilters ? (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography component="span" sx={{ display: 'block', fontWeight: 600 }}>
                {tUi("No TV channels match the current filters")}</Typography>
              <Typography component="span" variant="body2">
                {tUi("Reset the filters or broaden your search to see the full list.")}</Typography>
            </Alert>
          ) : null}
          </>}
        </ContentSection>
      </Box>

      {autoMatchOpen ? <Suspense fallback={<CircularProgress aria-label={tUi("Loading auto-match")} />}><TVAutoMatchDialog onClose={() => setAutoMatchOpen(false)} /></Suspense> : null}

      <TVChannelFormDialog
        mode="create"
        open={openCreateDialog}
        formData={formData}
        formErrors={formErrors}
        submitting={createMutation.isPending}
        dialogProps={dialogMobileProps}
        onChange={handleFormChange}
        onClose={() => setOpenCreateDialog(false)}
        onSubmit={handleCreate}
      />

      <TVChannelFormDialog
        mode="edit"
        open={openEditDialog}
        formData={formData}
        formErrors={formErrors}
        submitting={updateMutation.isPending}
        dialogProps={dialogMobileProps}
        onChange={handleFormChange}
        onClose={() => setOpenEditDialog(false)}
        onSubmit={handleUpdate}
      />

      <TVChannelDeleteDialog
        channel={deleteCandidate}
        submitting={deleteMutation.isPending}
        onCancel={() => setDeleteCandidate(null)}
        onConfirm={handleConfirmDelete}
      />

      <ChannelPlayerDialog
        tvChannelId={playerTarget?.tvChannelId}
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
      />
    </Box>
  );
};

export default TVChannels;
