import React from 'react';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
  GridRenderCellParams,
  GridSortModel,
} from '@mui/x-data-grid';
import { Box, IconButton, Avatar, Tooltip, Chip, useMediaQuery, useTheme } from '@mui/material';
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
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('md'));

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
    {
      field: 'actions',
      headerName: 'Actions',
      width: 160,
      sortable: false,
      renderCell: (params: GridRenderCellParams<TVChannel>) => (
        <Box display="flex" gap={1} role="group" aria-label={`TV channel actions for ${params.row.name}`}>
          <Tooltip title="Edit">
            <IconButton size="small" aria-label={`edit tv channel ${params.row.name}`} onClick={() => onEdit(params.row)}>
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" aria-label={`delete tv channel ${params.row.name}`} onClick={() => onDelete(params.row.id)}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Play">
            <span>
              <IconButton
                size="small"
                color="primary"
                aria-label={`play tv channel ${params.row.name}`}
                disabled={!params.row.acestream_channels?.length}
                onClick={() => onPlay(params.row.id)}
              >
                <PlayArrow fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      ),
    },
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
  ];

  return (
    <DataGrid
      rows={channels}
      columns={columns}
      getRowId={(row) => row.id}
      loading={loading}
      density={isCompact ? 'compact' : 'standard'}
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
      columnVisibilityModel={{
        country: !isCompact,
        language: !isCompact,
      }}
      sortingMode="server"
      onSortModelChange={onSortChange}
      slots={{ toolbar: GridToolbar }}
    />
  );
};

export default TVChannelsTable;
