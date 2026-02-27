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
import { Chip, Box, IconButton, Tooltip, CircularProgress, Snackbar, Alert } from '@mui/material';
import { CheckCircle, Cancel, Refresh, Edit, Delete, PowerSettingsNew, Block, HelpOutline } from '@mui/icons-material';
import { AcestreamChannel, AcestreamChannelFilters, acestreamChannelService } from '../services/channelService';
import { formatDate } from '../utils/errorUtils';
import ChannelActivityLogDialog from './ChannelActivityLogDialog';

interface ChannelTableProps {
  channels: AcestreamChannel[];
  loading: boolean;
  onCheckStatus: (id: string) => void;
  onEdit: (channel: AcestreamChannel) => void;
  onDelete: (id: string) => void;
  checkingStatus: Record<string, boolean>;
  filters: AcestreamChannelFilters;
  onFilterChange: (filters: AcestreamChannelFilters) => void;
  totalCount: number;
  page: number;
  pageSize: number;
  onPaginationModelChange: (model: { page: number; pageSize: number }) => void;
  onSortChange: (model: GridSortModel) => void;
  onSelectionChange?: (selectedIds: string[]) => void;
  extraActions?: (row: AcestreamChannel) => React.ReactNode;
  onActionComplete?: () => void;
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
  onSortChange,
  onPaginationModelChange,
  onSelectionChange,
  extraActions,
  onActionComplete,
}) => {
  const [filterModel, setFilterModel] = useState<GridFilterModel>({
    items: [],
  });
  const [activityLogOpen, setActivityLogOpen] = useState(false);
  const [activityLogChannelId, setActivityLogChannelId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Column definitions
  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'Acestream ID',
      minWidth: 260,
      flex: 1.2,
      filterable: true,
      renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
        <Box sx={{ display: 'flex', alignItems: 'center', fontFamily: 'monospace', fontSize: 13 }}>
          {params.row.id}
          <IconButton size="small" sx={{ ml: 1 }} onClick={() => navigator.clipboard.writeText(params.row.id)}>
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"
              />
            </svg>
          </IconButton>
        </Box>
      ),
    },
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 120, // was 200
      editable: true,
      filterable: true,
    },
    {
      field: 'group',
      headerName: 'Group',
      flex: 0.7, // was 0.5
      minWidth: 90, // was 150
      editable: true,
      filterable: true,
    },
    {
      field: 'is_active',
      headerName: 'Active',
      width: 80, // was 100
      type: 'boolean',
      editable: true,
      filterable: true,
      renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
        <Chip
          label={params.row.is_active ? 'Active' : 'Inactive'}
          color={params.row.is_active ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'is_online',
      headerName: 'Online',
      width: 80, // was 100
      filterable: true,
      renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
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
      width: 120, // was 170
      valueGetter: (params: GridValueGetterParams<AcestreamChannel>) => formatDate(params.row.last_checked),
    },
    {
      field: 'last_seen',
      headerName: 'Last Scraped',
      width: 120, // was 170
      valueGetter: (params: GridValueGetterParams<AcestreamChannel>) => formatDate(params.row.last_seen),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 260,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Box display="flex" gap={1}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => { onEdit(params.row); onActionComplete && onActionComplete(); }}>
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" onClick={async () => { await onDelete(params.row.id); onActionComplete && onActionComplete(); }}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={params.row.is_active ? 'Deactivate' : 'Activate'}>
            <IconButton
              size="small"
              onClick={async (e) => {
                e.stopPropagation();
                try {
                  await acestreamChannelService.updateAcestreamChannel(params.row.id, { is_active: !params.row.is_active });
                  onActionComplete && onActionComplete();
                } catch (err: any) {
                  setError('Failed to update channel: ' + (err?.message || 'Unknown error'));
                }
              }}
            >
              {params.row.is_active ? <PowerSettingsNew color="warning" /> : <CheckCircle color="success" />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Check Status">
            <IconButton
              size="small"
              onClick={async (e) => {
                e.stopPropagation();
                try {
                  const resp = await fetch(`/api/v1/acestream-channels/${params.row.id}/check_status`, { method: 'POST' });
                  if (!resp.ok) throw new Error('Failed to check status');
                  const data = await resp.json();
                  setError(`Status: ${data.status || data.message || 'Unknown'}`);
                  onActionComplete && onActionComplete();
                } catch (err: any) {
                  setError('Failed to check status: ' + (err?.message || 'Unknown error'));
                }
              }}
            >
              <Refresh color="primary" />
            </IconButton>
          </Tooltip>
          {extraActions && extraActions(params.row)}
        </Box>
      ),
    },
  ];

  // Handle filter changes
  const handleFilterModelChange = (model: GridFilterModel) => {
    setFilterModel(model);
    const newFilters: AcestreamChannelFilters = { ...filters };

    // Track if is_active is present
    let hasIsActive = false;

    // Convert grid filters to API filters (only supported fields)
    model.items.forEach(item => {
      if (item.field === 'name' && item.value) {
        newFilters.search = String(item.value);
      } else if (item.field === 'group' && item.value) {
        newFilters.group = String(item.value);
      } else if (item.field === 'is_active') {
        if (item.value === true || item.value === 'true') {
          newFilters.is_active = true;
          hasIsActive = true;
        } else if (item.value === false || item.value === 'false') {
          newFilters.is_active = false;
          hasIsActive = true;
        } else {
          delete newFilters.is_active;
          delete newFilters.active_only;
        }
      } else if (item.field === 'is_online' && item.value !== undefined && item.value !== '') {
        newFilters.is_online = item.value === 'true' || item.value === true;
      } else if (item.field === 'country' && item.value) {
        newFilters.country = String(item.value);
      } else if (item.field === 'language' && item.value) {
        newFilters.language = String(item.value);
      }
    });

    // Remove filters if cleared
    if (!model.items.some(item => item.field === 'name')) delete newFilters.search;
    if (!model.items.some(item => item.field === 'group')) delete newFilters.group;
    if (!model.items.some(item => item.field === 'is_online')) delete newFilters.is_online;
    if (!model.items.some(item => item.field === 'country')) delete newFilters.country;
    if (!model.items.some(item => item.field === 'language')) delete newFilters.language;
    // If is_active is not present, ensure it's removed
    if (!hasIsActive) {
      delete newFilters.is_active;
      delete newFilters.active_only;
    }

    onFilterChange(newFilters);
  };

  const handleCellEditCommit = async (params: any) => {
    const { id, field, value } = params;
    try {
      await acestreamChannelService.updateAcestreamChannel(id, { [field]: value });
    } catch (err: any) {
      setError('Failed to update channel: ' + (err?.message || 'Unknown error'));
    }
  };

  return (
    <>
      {error && (
        <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
          <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        </Snackbar>
      )}
      <DataGrid
        rows={channels}
        columns={columns}
        loading={loading}
        filterModel={filterModel}
        onFilterModelChange={handleFilterModelChange}
        checkboxSelection
        onRowSelectionModelChange={(ids) => {
          if (onSelectionChange) onSelectionChange(ids as string[]);
        }}
        onRowClick={(params) => onEdit(params.row)}
        autoHeight
        pagination
        paginationMode="server"
        rowCount={totalCount}
        pageSizeOptions={[10, 25, 50, 100]}
        paginationModel={{ page, pageSize }}
        onPaginationModelChange={onPaginationModelChange}
        sortingMode="server"
        onSortModelChange={onSortChange}
        processRowUpdate={async (newRow, oldRow) => {
          try {
            await acestreamChannelService.updateAcestreamChannel(newRow.id, newRow);
            return newRow;
          } catch (err) {
            // Optionally show error feedback
            return oldRow;
          }
        }}
        onCellEditStop={handleCellEditCommit}
        slots={{
          toolbar: GridToolbar,
        }}
      />
      {activityLogChannelId && (
        <ChannelActivityLogDialog
          open={activityLogOpen}
          onClose={() => setActivityLogOpen(false)}
          channelId={activityLogChannelId}
        />
      )}
    </>
  );
};

export default ChannelTable;
