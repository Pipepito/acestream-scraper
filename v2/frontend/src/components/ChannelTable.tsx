import React, { useState } from 'react';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
  GridValueGetterParams,
  GridRenderCellParams,
  GridSortModel,
  GridFilterModel,
} from '@mui/x-data-grid';
import { Chip, Box, IconButton, Tooltip, CircularProgress } from '@mui/material';
import { CheckCircle, Cancel, Refresh } from '@mui/icons-material';
import { Channel, ChannelFilters } from '../services/channelService';
import { formatDate } from '../utils/errorUtils';

interface ChannelTableProps {
  channels: Channel[];
  loading: boolean;
  onCheckStatus: (id: string) => void;
  onEdit: (channel: Channel) => void;
  onDelete: (id: string) => void;
  checkingStatus: Record<string, boolean>;
  filters: ChannelFilters;
  onFilterChange: (filters: ChannelFilters) => void;
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (model: GridSortModel) => void;
}

/**
 * Channel table component for displaying and managing acestream channels
 */
const ChannelTable: React.FC<ChannelTableProps> = ({
  channels,
  loading,
  onCheckStatus,
  onEdit,
  onDelete,
  checkingStatus,
  filters,
  onFilterChange,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onSortChange,
}) => {
  const [filterModel, setFilterModel] = useState<GridFilterModel>({
    items: [],
  });

  // Column definitions
  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'group',
      headerName: 'Group',
      flex: 0.5,
      minWidth: 150,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams<Channel>) => (
        <Chip 
          label={params.row.status} 
          color={params.row.status === 'active' ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'is_online',
      headerName: 'Online',
      width: 100,
      renderCell: (params: GridRenderCellParams<Channel>) => (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {params.row.is_online === null ? (
            <Chip label="Unknown" size="small" color="default" />
          ) : params.row.is_online ? (
            <CheckCircle color="success" />
          ) : (
            <Cancel color="error" />
          )}
        </Box>
      ),
    },
    {
      field: 'last_checked',
      headerName: 'Last Checked',
      width: 170,
      valueGetter: (params: GridValueGetterParams<Channel>) => formatDate(params.row.last_checked),
    },
    {
      field: 'added_at',
      headerName: 'Added',
      width: 170,
      valueGetter: (params: GridValueGetterParams<Channel>) => formatDate(params.row.added_at),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams<Channel>) => (
        <Box sx={{ display: 'flex' }}>
          <Tooltip title="Check status">
            <IconButton 
              size="small" 
              onClick={() => onCheckStatus(params.row.id)}
              disabled={checkingStatus[params.row.id]}
            >
              {checkingStatus[params.row.id] ? (
                <CircularProgress size={20} />
              ) : (
                <Refresh fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  // Handle filter changes
  const handleFilterModelChange = (model: GridFilterModel) => {
    setFilterModel(model);
    const newFilters: ChannelFilters = { ...filters };
    
    // Convert grid filters to API filters
    if (model.items.length > 0) {
      model.items.forEach(item => {
        if (item.field === 'name' && item.value) {
          newFilters.search = String(item.value);
        }
        if (item.field === 'group' && item.value) {
          newFilters.group = String(item.value);
        }
      });
    } else {
      // Reset search and group filters when cleared
      delete newFilters.search;
      delete newFilters.group;
    }
    
    onFilterChange(newFilters);
  };

  return (
    <DataGrid
      rows={channels}
      columns={columns}
      loading={loading}
      filterModel={filterModel}
      onFilterModelChange={handleFilterModelChange}
      disableRowSelectionOnClick
      autoHeight
      pagination
      paginationMode="server"
      rowCount={totalCount}
      pageSizeOptions={[10, 25, 50, 100]}
      page={page}
      pageSize={pageSize}
      onPageChange={onPageChange}
      onPaginationModelChange={(model) => {
        onPageChange(model.page);
        onPageSizeChange(model.pageSize);
      }}
      sortingMode="server"
      onSortModelChange={onSortChange}
      slots={{
        toolbar: GridToolbar,
      }}
    />
  );
};

export default ChannelTable;
