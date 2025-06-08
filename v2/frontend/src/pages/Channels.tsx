import React, { useState, useCallback } from 'react';
import { Typography, Box, Button, Alert, Paper } from '@mui/material';
import { Add, Refresh } from '@mui/icons-material';
import { GridSortModel } from '@mui/x-data-grid';
import ChannelTable from '../components/ChannelTable';
import { useChannels, useCheckChannelStatus, useDeleteChannel } from '../hooks/useChannels';
import { ChannelFilters } from '../services/channelService';
import { getErrorMessage } from '../utils/errorUtils';

/**
 * Channels page component
 */
const Channels: React.FC = () => {
  // State for pagination and sorting
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortModel, setSortModel] = useState<GridSortModel>([]);
  const [filters, setFilters] = useState<ChannelFilters>({});
  const [checkingStatus, setCheckingStatus] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  
  // Queries and mutations
  const { 
    data: channels = [], 
    isLoading,
    refetch,
    error: fetchError 
  } = useChannels({
    ...filters,
    page: page + 1, // Backend uses 1-based indexing
    page_size: pageSize
  });

  const deleteChannel = useDeleteChannel();
  const checkStatus = useCheckChannelStatus('');

  // Handler for check status
  const handleCheckStatus = useCallback((id: string) => {
    setCheckingStatus(prev => ({ ...prev, [id]: true }));
    
    checkStatus.mutate(id, {
      onSuccess: () => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
      },
      onError: (err) => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
        setError(`Failed to check status: ${getErrorMessage(err)}`);
      }
    });
  }, [checkStatus]);

  // Handler for editing a channel
  const handleEdit = useCallback((channel) => {
    // To be implemented - open edit dialog
    console.log('Edit channel:', channel);
  }, []);

  // Handler for deleting a channel
  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Are you sure you want to delete this channel?')) {
      deleteChannel.mutate(id, {
        onError: (err) => {
          setError(`Failed to delete channel: ${getErrorMessage(err)}`);
        }
      });
    }
  }, [deleteChannel]);

  // Handler for filter changes
  const handleFilterChange = useCallback((newFilters: ChannelFilters) => {
    setFilters(newFilters);
    setPage(0); // Reset to first page on filter change
  }, []);

  // Handler for sort changes
  const handleSortChange = useCallback((model: GridSortModel) => {
    setSortModel(model);
    // Implement server-side sorting logic here
  }, []);

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Channels
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => refetch()}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Add />}
            onClick={() => {/* To be implemented - open add channel dialog */}}
          >
            Add Channel
          </Button>
        </Box>
      </Box>
      
      {(error || fetchError) && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error || getErrorMessage(fetchError)}
        </Alert>
      )}
      
      <Paper sx={{ p: 2 }}>
        <ChannelTable 
          channels={channels || []}
          loading={isLoading}
          onCheckStatus={handleCheckStatus}
          onEdit={handleEdit}
          onDelete={handleDelete}
          checkingStatus={checkingStatus}
          filters={filters}
          onFilterChange={handleFilterChange}
          totalCount={100} // This should come from API
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          onSortChange={handleSortChange}
        />
      </Paper>
    </Box>
  );
};

export default Channels;
