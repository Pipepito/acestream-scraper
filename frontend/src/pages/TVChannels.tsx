import TVChannelReorder from '../components/TVChannelReorder';
import React, { lazy, Suspense, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  Switch,
  Alert,
  Stack,
  Collapse,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useReorderTVChannels, useTVChannelCatalog, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel, useToggleTVChannelFavorite } from '../hooks/useTVChannels';
import { useTVChannelForm } from '../hooks/useTVChannelForm';
import TVChannelFilters, { matchesTVFilters, TVFilters } from '../components/TVChannelFilters';
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
import { normalizeApiError } from '../services/apiErrors';

const TVAutoMatchDialog = lazy(() => import('../components/TVAutoMatchDialog'));

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const TVChannels: React.FC = () => {
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
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [deleteCandidate, setDeleteCandidate] = useState<TVChannel | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
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
  const {
    data: channelCatalog,
    isLoading: isCatalogLoading,
    isError: isCatalogError,
    refetch: refetchCatalog,
  } = useTVChannelCatalog();
  const deleteMutation = useDeleteTVChannel();
  const createMutation = useCreateTVChannel();
  const updateMutation = useUpdateTVChannel();
  const toggleFavoriteMutation = useToggleTVChannelFavorite();

  const channels = useMemo(() => channelCatalog ?? [], [channelCatalog]);
  const filteredChannels = useMemo(() => {
    const result = channels.filter(channel => (!favoritesOnly || channel.is_favorite) && matchesTVFilters(channel, filters));
    const sort = sortModel[0];
    if (sort?.sort) result.sort((a, b) => {
      const value = (c: TVChannel): string | number => sort.field === 'acestream_channels' ? c.acestream_channels.length : (c[sort.field as keyof TVChannel] == null ? '' : typeof c[sort.field as keyof TVChannel] === 'number' ? Number(c[sort.field as keyof TVChannel]) : String(c[sort.field as keyof TVChannel]));
      const left = value(a), right = value(b);
      const compared = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right), undefined, { numeric: true });
      return (sort.sort === 'desc' ? -compared : compared) || a.id - b.id;
    });
    return result;
  }, [channels, filters, favoritesOnly, sortModel]);

  const paginatedChannels = useMemo(() => {
    return filteredChannels.slice(skip, skip + pageSize);
  }, [filteredChannels, skip, pageSize]);

  React.useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredChannels.length / pageSize));

    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [filteredChannels.length, page, pageSize]);

  const totalChannels = filteredChannels.length;
  const hasFilters = favoritesOnly || Object.values(filters).some(Boolean);
  const favoriteCount = channels.filter((channel) => channel.is_favorite).length;
  const withStreamsCount = channels.filter((channel) => (channel.acestream_channels?.length ?? 0) > 0).length;
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
      setNotice(updated.is_favorite ? `Added ${channel.name} to favorites.` : `Removed ${channel.name} from favorites.`);
    } catch {
      setNotice('Failed to update favorite state.');
    }
  };

  const handleCreate = async () => {
    const payload = validateForm();

    if (!payload) {
      return;
    }

    try {
      await createMutation.mutateAsync(payload as TVChannelCreate);
      setOpenCreateDialog(false);
      setNotice('TV channel created.');
    } catch (error) {
      setFormErrors({ submit: normalizeApiError(error).message });
    }
  };

  const handleUpdate = async () => {
    if (!selectedChannel) {
      return;
    }

    const payload = validateForm();

    if (!payload) {
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: selectedChannel.id,
        updates: payload as TVChannelUpdate,
      });
      setOpenEditDialog(false);
      setNotice('TV channel updated.');
    } catch (error) {
      setFormErrors({ submit: normalizeApiError(error).message });
    }
  };

  const handleRequestDelete = (id: number) => {
    const channel = channels.find((item) => item.id === id) ?? null;
    setDeleteCandidate(channel);
  };

  const handleConfirmDelete = async () => {
    if (!deleteCandidate) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(deleteCandidate.id);
      setNotice('TV channel deleted.');
      setDeleteCandidate(null);
    } catch {
      setNotice('Failed to delete TV channel.');
    }
  };

  if (isCatalogLoading) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="50vh" gap={1.5}>
        <CircularProgress aria-label="Loading TV channels" />
        <Typography variant="sectionTitle" component="p">
          Loading TV channels
        </Typography>
        <Typography variant="body2" color="text.secondary" align="center">
          Preparing the latest TV channel inventory and actions.
        </Typography>
      </Box>
    );
  }

  if (isCatalogError && !channelCatalog) {
    return (
      <Box p={3}>
        <Stack spacing={2} alignItems="flex-start">
          <Alert severity="error">We could not load the TV channel inventory. Try refreshing to reconnect.</Alert>
          <Button variant="outlined" disabled={reordering} onClick={() => refetchCatalog()}>
            Retry loading TV channels
          </Button>
        </Stack>
      </Box>
    );
  }

  const showFilters = !isPhone || filtersOpen;
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
        title="TV Channels"
        subtitle="The channels you publish. Each one groups its streams and carries the EPG for the playlist."
        primaryActions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" disabled={reordering || channels.length < 2} onClick={() => setReordering(true)}>Reorder channels</Button>
            <Button variant="outlined" disabled={reordering} onClick={() => setAutoMatchOpen(true)}>Auto-match streams</Button>
            <Button variant="outlined" disabled={reordering} onClick={() => refetchCatalog()}>
              Refresh
            </Button>
            <Button variant="contained" color="primary" disabled={reordering} onClick={handleOpenCreateDialog}>
              Add TV Channel
            </Button>
          </Stack>
        }
      />

      <StatusLine
        aria-label="TV channel summary"
        items={[
          { label: favoritesOnly ? 'Favorites' : 'Channels', value: String(channels.length) },
          ...(favoritesOnly ? [] : [{ label: 'Favorites', value: String(favoriteCount) }]),
          { label: 'With streams', value: String(withStreamsCount), tone: withStreamsCount === 0 && channels.length > 0 ? 'warning' as const : 'default' as const },
          { label: 'Matching filters', value: hasFilters ? String(totalChannels) : 'all' },
        ]}
      />

      {notice ? (
        <Alert severity={notice.startsWith('Failed') ? 'error' : 'success'} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      ) : null}

      <Box data-testid="tv-channels-page-layout">
        <ContentSection
          title="Channels"
          actions={
            isPhone && !reordering ? (
              <Button
                variant="outlined"
                onClick={() => setFiltersOpen((current) => !current)}
                aria-expanded={filtersOpen}
                aria-controls="tv-channels-filters-panel"
              >
                {filtersOpen ? 'Hide filters' : 'Show filters'}
              </Button>
            ) : null
          }
        >
          {reordering ? <TVChannelReorder channels={channels} onCancel={() => setReordering(false)} onSave={async (ids, expected) => {
            await reorderMutation.mutateAsync({ ids, expected });
            setSortModel([]); setFilters({}); setFavoritesOnly(false); setPage(1);
            setReordering(false); setNotice('Channel order and numbers saved.');
          }} /> : <>
          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={<Switch checked={favoritesOnly} onChange={handleFavoritesOnlyChange} name="favorites_only" color="primary" />}
              label="Favorites only"
            />
            {isPhone ? (
              <Collapse in={showFilters} id="tv-channels-filters-panel" unmountOnExit>
                <TVChannelFilters channels={channels} filters={filters} onChange={handleFiltersChange} />
              </Collapse>
            ) : (
              <Box id="tv-channels-filters-panel">
                <TVChannelFilters channels={channels} filters={filters} onChange={handleFiltersChange} />
              </Box>
            )}
          </Box>
          <TVChannelsTable
            channels={paginatedChannels}
            loading={isCatalogLoading}
            totalCount={totalChannels}
            page={page - 1}
            pageSize={pageSize}
            onPageChange={(nextPage) => setPage(nextPage + 1)}
            onPageSizeChange={setPageSize}
            onSortChange={(model) => { setPage(1); setSortModel(model); }}
            onNumberChange={async (channel, number) => { await updateMutation.mutateAsync({ id: channel.id, updates: { channel_number: number } }); setNotice(`Updated number for ${channel.name}.`); }}
            onEdit={handleOpenEditDialog}
            onDelete={handleRequestDelete}
            onOpen={(id) => navigate(`/tv-channels/${id}`)}
            onToggleFavorite={handleToggleFavorite}
            onPlay={(channel) => setPlayerTarget({ contentId: channel.acestream_channels[0].id, title: channel.name, tvChannelId: channel.id })}
          />
          {totalChannels === 0 && hasFilters ? (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography component="span" sx={{ display: 'block', fontWeight: 600 }}>
                No TV channels match the current filters
              </Typography>
              <Typography component="span" variant="body2">
                Reset the filters or broaden your search to see the full list.
              </Typography>
            </Alert>
          ) : null}
          </>}
        </ContentSection>
      </Box>

      {autoMatchOpen ? <Suspense fallback={<CircularProgress aria-label="Loading auto-match" />}><TVAutoMatchDialog onClose={() => setAutoMatchOpen(false)} /></Suspense> : null}

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
