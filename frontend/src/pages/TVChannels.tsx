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
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useAllTVChannels, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel } from '../hooks/useTVChannels';
import { AdvancedSearchFilters } from '../components/AdvancedSearch';
import TVChannelsTable from '../components/TVChannelsTable';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import AdvancedSearch from '../components/AdvancedSearch';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { getShellLayout } from '../styles/layout';

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
  const { data: channelsData, isLoading, isError, refetch } = useAllTVChannels(skip, pageSize);
  const deleteMutation = useDeleteTVChannel();
  const createMutation = useCreateTVChannel();
  const updateMutation = useUpdateTVChannel();

  const channels = useMemo(() => channelsData?.items ?? [], [channelsData?.items]);
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
    setFormData((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
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

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this TV channel?')) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(id);
      setNotice('TV channel deleted.');
    } catch {
      setNotice('Failed to delete TV channel.');
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={3}>
        <Alert severity="error">Error loading TV channels.</Alert>
      </Box>
    );
  }

  const totalChannels = channelsData?.total || 0;
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
            <Button variant="outlined" onClick={() => refetch()}>
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
        sx={
          isWideDesktop
            ? {
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 2fr) minmax(280px, 1fr)',
                gridTemplateAreas: 'primary supporting',
                gap: theme.appTokens.layout.pageGap,
                alignItems: 'start',
              }
            : undefined
        }
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
            channels={filteredChannels}
            loading={isLoading}
            totalCount={totalChannels}
            page={page - 1}
            pageSize={pageSize}
            onPageChange={(nextPage) => setPage(nextPage + 1)}
            onPageSizeChange={setPageSize}
            onSortChange={() => undefined}
            onEdit={handleOpenEditDialog}
            onDelete={handleDelete}
            onPlay={(id) => navigate(`/tv-channels/${id}`)}
          />
        </ContentSection>

        <ContentSection title="Filters" wideLayout="supporting">
          {isPhone ? (
            <Collapse in={showFilters} id="tv-channels-filters-panel" unmountOnExit>
              <AdvancedSearch filters={filters} onChange={setFilters} categories={categories} />
            </Collapse>
          ) : (
            <Box id="tv-channels-filters-panel">
              <AdvancedSearch filters={filters} onChange={setFilters} categories={categories} />
            </Box>
          )}
        </ContentSection>
      </Box>

      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} {...dialogMobileProps}>
        <DialogTitle>Add TV Channel</DialogTitle>
        <DialogContent>
          <Box my={2}>
            <TextField autoFocus name="name" label="Channel Name" fullWidth value={formData.name} onChange={handleFormChange} required margin="dense" />
            <TextField name="logo_url" label="Logo URL" fullWidth value={formData.logo_url || ''} onChange={handleFormChange} margin="dense" />
            <TextField
              name="description"
              label="Description"
              fullWidth
              value={formData.description || ''}
              onChange={handleFormChange}
              margin="dense"
              multiline
              rows={3}
            />
            <TextField name="category" label="Category" fullWidth value={formData.category || ''} onChange={handleFormChange} margin="dense" />
            <TextField name="country" label="Country" fullWidth value={formData.country || ''} onChange={handleFormChange} margin="dense" />
            <TextField name="language" label="Language" fullWidth value={formData.language || ''} onChange={handleFormChange} margin="dense" />
            <TextField
              name="channel_number"
              label="Channel Number"
              type="number"
              fullWidth
              value={formData.channel_number || ''}
              onChange={handleFormChange}
              margin="dense"
            />
            <FormControlLabel
              control={<Switch checked={formData.is_active === true} onChange={handleFormChange} name="is_active" color="primary" />}
              label="Active"
            />
            <FormControlLabel
              control={<Switch checked={formData.is_favorite === true} onChange={handleFormChange} name="is_favorite" color="primary" />}
              label="Favorite"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" color="primary" disabled={createMutation.isLoading || !formData.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} {...dialogMobileProps}>
        <DialogTitle>Edit TV Channel</DialogTitle>
        <DialogContent>
          <Box my={2}>
            <TextField autoFocus name="name" label="Channel Name" fullWidth value={formData.name || ''} onChange={handleFormChange} required margin="dense" />
            <TextField name="logo_url" label="Logo URL" fullWidth value={formData.logo_url || ''} onChange={handleFormChange} margin="dense" />
            <TextField
              name="description"
              label="Description"
              fullWidth
              value={formData.description || ''}
              onChange={handleFormChange}
              margin="dense"
              multiline
              rows={3}
            />
            <TextField name="category" label="Category" fullWidth value={formData.category || ''} onChange={handleFormChange} margin="dense" />
            <TextField name="country" label="Country" fullWidth value={formData.country || ''} onChange={handleFormChange} margin="dense" />
            <TextField name="language" label="Language" fullWidth value={formData.language || ''} onChange={handleFormChange} margin="dense" />
            <TextField
              name="epg_id"
              label="EPG ID"
              fullWidth
              value={formData.epg_id || ''}
              onChange={handleFormChange}
              margin="dense"
            />
            <TextField
              name="channel_number"
              label="Channel Number"
              type="number"
              fullWidth
              value={formData.channel_number || ''}
              onChange={handleFormChange}
              margin="dense"
            />
            <FormControlLabel
              control={<Switch checked={formData.is_active === true} onChange={handleFormChange} name="is_active" color="primary" />}
              label="Active"
            />
            <FormControlLabel
              control={<Switch checked={formData.is_favorite === true} onChange={handleFormChange} name="is_favorite" color="primary" />}
              label="Favorite"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdate} variant="contained" color="primary" disabled={updateMutation.isLoading || !formData.name}>
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TVChannels;
