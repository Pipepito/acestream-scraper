import React from 'react';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
  GridRenderCellParams,
  GridSortModel,
  GridFilterModel,
} from '@mui/x-data-grid';
import { Box, IconButton, Avatar, Tooltip, Chip } from '@mui/material';
import { Edit, Delete, PlayArrow } from '@mui/icons-material';
import { TVChannel } from '../types/tvChannelTypes';

interface TVChannelsTableProps {
  channels: TVChannel[];
  loading: boolean;
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (model: GridSortModel) => void;
  onEdit: (channel: TVChannel) => void;
  onDelete: (id: number) => void;
  onPlay: (id: number) => void;
}

const TVChannelsTable: React.FC<TVChannelsTableProps> = ({
  channels,
  loading,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onSortChange,
  onEdit,
  onDelete,
  onPlay,
}) => {
  const columns: GridColDef[] = [
    {
      field: 'logo_url',
      headerName: 'Logo',
      width: 60,
      renderCell: (params: GridRenderCellParams<TVChannel>) =>
        params.row.logo_url ? (
          <Avatar src={params.row.logo_url} alt={params.row.name} />
        ) : null,
      sortable: false,
      filterable: false,
    },
    { field: 'name', headerName: 'Name', flex: 1, minWidth: 140 },
    { field: 'channel_number', headerName: 'Number', width: 90 },
    { field: 'category', headerName: 'Category', width: 120 },
    { field: 'language', headerName: 'Language', width: 100 },
    { field: 'country', headerName: 'Country', width: 100 },
    {
      field: 'acestream_channels',
      headerName: 'Streams',
      width: 90,
      valueGetter: (params) => Array.isArray(params.row.acestream_channels) ? params.row.acestream_channels.length : 0,
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 90,
      renderCell: (params: GridRenderCellParams<TVChannel>) => (
        <Chip
          label={params.row.is_active ? 'Active' : 'Inactive'}
          color={params.row.is_active ? 'success' : 'default'}
          size="small"
        />
      ),
      filterable: true,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 160,
      sortable: false,
      renderCell: (params: GridRenderCellParams<TVChannel>) => (
        <Box display="flex" gap={1}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => onEdit(params.row)}>
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" onClick={() => onDelete(params.row.id)}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Play">
            <span>
              <IconButton size="small" color="primary" disabled={!params.row.acestream_channels?.length} onClick={() => onPlay(params.row.id)}>
                <PlayArrow fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <DataGrid
      rows={channels}
      columns={columns}
      getRowId={(row) => row.id}
      loading={loading}
      autoHeight
      pagination
      paginationMode="server"
      rowCount={totalCount}
      pageSizeOptions={[10, 25, 50, 100]}
      paginationModel={{ page, pageSize }}
      onPaginationModelChange={(model) => {
        onPageChange(model.page);
        onPageSizeChange(model.pageSize);
      }}
      sortingMode="server"
      onSortModelChange={onSortChange}
      slots={{ toolbar: GridToolbar }}
    />
  );
};

export default TVChannelsTable;
