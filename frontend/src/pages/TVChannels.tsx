import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Pagination,
  CircularProgress,
  TextField,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  useTheme,
  useMediaQuery,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, PlayArrow as PlayIcon } from '@mui/icons-material';
import { useAllTVChannels, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel } from '../hooks/useTVChannels';
import { AdvancedSearchFilters } from '../components/AdvancedSearch';
import TVChannelsTable from '../components/TVChannelsTable';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { Link as RouterLink } from 'react-router-dom';
import './TVChannels.css';


const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];



const TVChannels: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);
  const [filters, setFilters] = useState<AdvancedSearchFilters>({});
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
    is_active: true
  });

  // Memoize query params for backend
  const queryParams = useMemo(() => {
    const params: Record<string, any> = {
      skip: (page - 1) * pageSize,
      limit: pageSize
    };
    if (filters.search) params.search = filters.search;
    if (filters.category) params.category = filters.category;
    if (filters.group) params.group = filters.group;
    if (filters.status) params.status = filters.status;
    if (filters.sort) params.sort = filters.sort;
    if (filters.country) params.country = filters.country;
    if (filters.language) params.language = filters.language;
    if (filters.is_active) params.is_active = filters.is_active;
    if (filters.is_online) params.is_online = filters.is_online;
    return params;
  }, [filters, page, pageSize]);

  // TODO: To support advanced filtering, update tvChannelService and useAllTVChannels to accept filter params
  const { data: channelsData, isLoading, isError } = useAllTVChannels(queryParams.skip, queryParams.limit);
  const deleteMutation = useDeleteTVChannel();
  const createMutation = useCreateTVChannel();
  const updateMutation = useUpdateTVChannel();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));



  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(event.target.value));
    setPage(1); // Reset to first page when page size changes
  };

  const handleFilterChange = (newFilters: AdvancedSearchFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  };

  const handleOpenCreateDialog = () => {
    setFormData({
      name: '',
      logo_url: '',
      description: '',
      category: '',
      country: '',
      language: '',
      is_active: true,
      is_favorite: false
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
      channel_number: channel.channel_number
    });
    setOpenEditDialog(true);
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync(formData as TVChannelCreate);
      setOpenCreateDialog(false);
    } catch (error) {
      console.error('Error creating TV channel:', error);
    }
  };

  const handleUpdate = async () => {
    if (!selectedChannel) return;

    try {
      await updateMutation.mutateAsync({
        id: selectedChannel.id,
        updates: formData as TVChannelUpdate
      });
      setOpenEditDialog(false);
    } catch (error) {
      console.error('Error updating TV channel:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this TV channel?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        console.error('Error deleting TV channel:', error);
      }
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
        <Typography color="error">Error loading TV channels.</Typography>
      </Box>
    );
  }


  const totalChannels = channelsData?.total || 0;
  const totalPages = Math.ceil(totalChannels / pageSize);
  const channels = channelsData?.items || [];

  return (
    <Box sx={{ width: '100%' }}>
      <Box p={isMobile ? 1 : 3}>
        <Box display="flex" flexDirection={isMobile ? 'column' : 'row'} justifyContent="space-between" alignItems={isMobile ? 'stretch' : 'center'} mb={3} gap={2}>
          <Typography variant="h4">TV Channels</Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleOpenCreateDialog}
            sx={{ width: isMobile ? '100%' : 'auto' }}
          >
            Add TV Channel
          </Button>
        </Box>




        {/* Table grid handles pagination and page size */}


        <Paper sx={{ p: { xs: 1, sm: 2 }, width: '100%', overflowX: 'auto' }}>
          <TVChannelsTable
            channels={channels}
            loading={isLoading}
            totalCount={totalChannels}
            page={page - 1}
            pageSize={pageSize}
            onPageChange={p => setPage(p + 1)}
            onPageSizeChange={setPageSize}
            onSortChange={() => {}}
            onEdit={handleOpenEditDialog}
            onDelete={handleDelete}
            onPlay={id => navigate(`/tv-channels/${id}`)}
          />
        </Paper>

        {/* Pagination is handled by ChannelTable (DataGrid) */}

        {/* Create TV Channel Dialog */}
        <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Add TV Channel</DialogTitle>
          <DialogContent>
            <Box my={2}>
              <TextField
                autoFocus
                name="name"
                label="Channel Name"
                fullWidth
                value={formData.name}
                onChange={handleFormChange}
                required
                margin="dense"
              />
              <TextField
                name="logo_url"
                label="Logo URL"
                fullWidth
                value={formData.logo_url}
                onChange={handleFormChange}
                margin="dense"
              />
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
              <TextField
                name="category"
                label="Category"
                fullWidth
                value={formData.category || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="country"
                label="Country"
                fullWidth
                value={formData.country || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="language"
                label="Language"
                fullWidth
                value={formData.language || ''}
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
                control={
                  <Switch
                    checked={formData.is_active === true}
                    onChange={handleFormChange}
                    name="is_active"
                    color="primary"
                  />
                }
                label="Active"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_favorite === true}
                    onChange={handleFormChange}
                    name="is_favorite"
                    color="primary"
                  />
                }
                label="Favorite"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateDialog(false)} color="inherit">
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              color="primary"
              variant="contained"
              disabled={!formData.name}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit TV Channel Dialog */}
        <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Edit TV Channel</DialogTitle>
          <DialogContent>
            <Box my={2}>
              <TextField
                autoFocus
                name="name"
                label="Channel Name"
                fullWidth
                value={formData.name}
                onChange={handleFormChange}
                required
                margin="dense"
              />
              <TextField
                name="logo_url"
                label="Logo URL"
                fullWidth
                value={formData.logo_url}
                onChange={handleFormChange}
                margin="dense"
              />
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
              <TextField
                name="category"
                label="Category"
                fullWidth
                value={formData.category || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="country"
                label="Country"
                fullWidth
                value={formData.country || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="language"
                label="Language"
                fullWidth
                value={formData.language || ''}
                onChange={handleFormChange}
                margin="dense"
              />
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
                control={
                  <Switch
                    checked={formData.is_active === true}
                    onChange={handleFormChange}
                    name="is_active"
                    color="primary"
                  />
                }
                label="Active"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_favorite === true}
                    onChange={handleFormChange}
                    name="is_favorite"
                    color="primary"
                  />
                }
                label="Favorite"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenEditDialog(false)} color="inherit">
              Cancel
            </Button>
            <Button
              onClick={handleUpdate}
              color="primary"
              variant="contained"
              disabled={!formData.name}
            >
              Update
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Box>
  );
};

export default TVChannels;

/* Add styles for the page size select */
// You can move this to TVChannels.css if preferred
const style = document.createElement('style');
style.innerHTML = `
.tvchannels-page-size-select {
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 1rem;
}
`;
if (typeof document !== 'undefined' && !document.getElementById('tvchannels-page-size-style')) {
  style.id = 'tvchannels-page-size-style';
  document.head.appendChild(style);
}
