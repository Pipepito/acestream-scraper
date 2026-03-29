import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  CircularProgress,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Alert,
  Stack,
  Collapse,
  Divider,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useAllTVChannels, useTVChannelCatalog, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel } from '../hooks/useTVChannels';
import { AdvancedSearchFilters } from '../components/AdvancedSearch';
import TVChannelsTable from '../components/TVChannelsTable';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import AdvancedSearch from '../components/AdvancedSearch';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { getShellLayout, getWidePageSplitLayout } from '../styles/layout';

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const TVChannels: React.FC = () => {
  const theme = useTheme();
  const shellLayout = getShellLayout(theme);
  const isPhone = useMediaQuery(`(max-width:${shellLayout.phoneMaxWidth}px)`);
  const isWideDesktop = useMediaQuery(`(min-width:${shellLayout.wideMinWidth}px)`);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[1]);
  const [filters, setFilters] = useState<AdvancedSearchFilters>({});
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<TVChannel | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<TVChannel | null>(null);
  const [formData, setFormData] = useState<TVChannelCreate | TVChannelUpdate>({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    is_active: true,
  });
  const [notice, setNotice] = useState<string | null>(null);

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

  const channels = useMemo(() => channelCatalog ?? [], [channelCatalog]);
  const filteredChannels = useMemo(() => {
    return channels.filter((channel) => {
      const search = filters.search?.toLowerCase().trim();
      if (search && !channel.name.toLowerCase().includes(search) && !String(channel.channel_number || '').includes(search)) {
        return false;
      }

      if (filters.category && channel.category !== filters.category) {
        return false;
      }

      if (filters.country && channel.country !== filters.country) {
        return false;
      }

      if (filters.language && channel.language !== filters.language) {
        return false;
      }

      if (filters.is_active === 'true' && !channel.is_active) {
        return false;
      }

      if (filters.is_active === 'false' && channel.is_active) {
        return false;
      }

      return true;
    });
  }, [channels, filters]);

  const paginatedChannels = useMemo(() => {
    return filteredChannels.slice(skip, skip + pageSize);
  }, [filteredChannels, skip, pageSize]);

  React.useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(filteredChannels.length / pageSize));

    if (page > maxPage) {
      setPage(maxPage);
    }
  }, [filteredChannels.length, page, pageSize]);

  const categories = useMemo(
    () => Array.from(new Set(channels.map((channel) => channel.category).filter(Boolean) as string[])).sort(),
    [channels]
  );

  const handleOpenCreateDialog = () => {
    setFormData({
      name: '',
      logo_url: '',
      description: '',
      category: '',
      country: '',
      language: '',
      is_active: true,
      is_favorite: false,
    });
    setOpenCreateDialog(true);
  };

  const handleOpenEditDialog = (channel: TVChannel) => {
    setSelectedChannel(channel);
    setFormData({
      name: channel.name,
      logo_url: channel.logo_url || '',
      description: channel.description || '',
      category: channel.category || '',
      country: channel.country || '',
      language: channel.language || '',
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
      epg_id: channel.epg_id || '',
      channel_number: channel.channel_number,
    });
    setOpenEditDialog(true);
  };

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : name === 'channel_number' ? (value === '' ? '' : Number(value)) : value,
    }));
  };

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync(formData as TVChannelCreate);
      setOpenCreateDialog(false);
      setNotice('TV channel created.');
    } catch {
      setNotice('Failed to create TV channel.');
    }
  };

  const handleUpdate = async () => {
    if (!selectedChannel) {
      return;
    }
    try {
      await updateMutation.mutateAsync({
        id: selectedChannel.id,
        updates: formData as TVChannelUpdate,
      });
      setOpenEditDialog(false);
      setNotice('TV channel updated.');
    } catch {
      setNotice('Failed to update TV channel.');
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

  const renderDialogSections = (mode: 'create' | 'edit') => (
    <Stack spacing={3} sx={{ py: 1 }}>
      <Box>
        <Typography variant="sectionTitle" component="h3" gutterBottom>
          Channel basics
        </Typography>
        <Stack spacing={2}>
          <TextField autoFocus name="name" label="Channel Name" fullWidth value={formData.name || ''} onChange={handleFormChange} required />
          <TextField
            name="description"
            label="Description"
            fullWidth
            value={formData.description || ''}
            onChange={handleFormChange}
            multiline
            rows={3}
          />
        </Stack>
      </Box>

      <Divider />

      <Box>
        <Typography variant="sectionTitle" component="h3" gutterBottom>
          Optional metadata
        </Typography>
        <Stack spacing={2}>
          <TextField name="logo_url" label="Logo URL" fullWidth value={formData.logo_url || ''} onChange={handleFormChange} />
          <TextField name="category" label="Category" fullWidth value={formData.category || ''} onChange={handleFormChange} />
          <TextField name="country" label="Country" fullWidth value={formData.country || ''} onChange={handleFormChange} />
          <TextField name="language" label="Language" fullWidth value={formData.language || ''} onChange={handleFormChange} />
          {mode === 'edit' ? <TextField name="epg_id" label="EPG ID" fullWidth value={formData.epg_id || ''} onChange={handleFormChange} /> : null}
          <TextField name="channel_number" label="Channel Number" type="number" fullWidth value={formData.channel_number || ''} onChange={handleFormChange} />
        </Stack>
      </Box>

      <Divider />

      <Box>
        <Typography variant="sectionTitle" component="h3" gutterBottom>
          Visibility & favorites
        </Typography>
        <Stack spacing={1}>
          <FormControlLabel
            control={<Switch checked={formData.is_active === true} onChange={handleFormChange} name="is_active" color="primary" />}
            label="Active"
          />
          <FormControlLabel
            control={<Switch checked={formData.is_favorite === true} onChange={handleFormChange} name="is_favorite" color="primary" />}
            label="Favorite"
          />
        </Stack>
      </Box>
    </Stack>
  );

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

  if (isCatalogError) {
    return (
      <Box p={3}>
        <Alert severity="error">Error loading TV channels.</Alert>
      </Box>
    );
  }

  const totalChannels = filteredChannels.length;
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
        subtitle="Manage TV-channel metadata and launch detailed channel playback checks."
        primaryActions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" onClick={() => refetchCatalog()}>
              Refresh
            </Button>
            <Button variant="contained" color="primary" onClick={handleOpenCreateDialog}>
              Add TV Channel
            </Button>
          </Stack>
        }
      />

      {notice ? (
        <Alert severity={notice.startsWith('Failed') ? 'error' : 'success'} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      ) : null}

      <Box
        data-testid="tv-channels-page-layout"
        sx={getWidePageSplitLayout(theme, isWideDesktop)}
      >
        <ContentSection
          title="TV Channel Inventory"
          description="Edit metadata, remove stale entries, or open the channel detail page."
          wideLayout="primary"
          actions={
            isPhone ? (
              <Button
                variant="outlined"
                onClick={() => setFiltersOpen((current) => !current)}
                aria-expanded={filtersOpen}
                aria-controls="tv-channels-filters-panel"
              >
                {filtersOpen ? 'Hide Filters' : 'Show Filters'}
              </Button>
            ) : null
          }
        >
          <TVChannelsTable
            channels={paginatedChannels}
            loading={isCatalogLoading}
            totalCount={totalChannels}
            page={page - 1}
            pageSize={pageSize}
            onPageChange={(nextPage) => setPage(nextPage + 1)}
            onPageSizeChange={setPageSize}
            onSortChange={() => undefined}
            onEdit={handleOpenEditDialog}
            onDelete={handleRequestDelete}
            onPlay={(id) => navigate(`/tv-channels/${id}`)}
          />
        </ContentSection>

        <ContentSection
          title="Filters"
          description="Use these filters to narrow the inventory before you edit, review, or remove a channel."
          wideLayout="supporting"
        >
          {isPhone ? (
            <Collapse in={showFilters} id="tv-channels-filters-panel" unmountOnExit>
              <AdvancedSearch
                filters={filters}
                onChange={setFilters}
                categories={categories}
                visibleFields={{
                  search: true,
                  category: true,
                  country: true,
                  language: true,
                  is_active: true,
                  group: false,
                  status: false,
                  sort: false,
                  is_online: false,
                }}
              />
            </Collapse>
          ) : (
            <Box id="tv-channels-filters-panel">
              <AdvancedSearch
                filters={filters}
                onChange={setFilters}
                categories={categories}
                visibleFields={{
                  search: true,
                  category: true,
                  country: true,
                  language: true,
                  is_active: true,
                  group: false,
                  status: false,
                  sort: false,
                  is_online: false,
                }}
              />
            </Box>
          )}
        </ContentSection>
      </Box>

      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} {...dialogMobileProps}>
        <DialogTitle>Add TV Channel</DialogTitle>
        <DialogContent dividers>{renderDialogSections('create')}</DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" color="primary" disabled={createMutation.isLoading || !formData.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} {...dialogMobileProps}>
        <DialogTitle>Edit TV Channel</DialogTitle>
        <DialogContent dividers>{renderDialogSections('edit')}</DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdate} variant="contained" color="primary" disabled={updateMutation.isLoading || !formData.name}>
            Update
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteCandidate !== null} onClose={() => setDeleteCandidate(null)} fullWidth maxWidth="xs">
        <DialogTitle>Delete TV Channel</DialogTitle>
        <DialogContent dividers>
          <Typography>
            Remove {deleteCandidate?.name || 'this TV channel'} from the TV channel inventory? This cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteCandidate(null)} variant="contained" data-action-priority="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="outlined" data-action-priority="danger">
            Delete TV Channel
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TVChannels;
