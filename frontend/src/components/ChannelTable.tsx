import React, { useMemo, useState } from 'react';
import {
  DataGrid,
  GridColDef,
  GridToolbar,
  GridValueGetterParams,
  GridRenderCellParams,
  GridSortModel,
  GridFilterModel,
} from '@mui/x-data-grid';
import { Chip, Box, IconButton, Tooltip, Snackbar, Alert, useMediaQuery, useTheme } from '@mui/material';
import { CheckCircle, Cancel, Refresh, Edit, Delete, PowerSettingsNew, ContentCopy } from '@mui/icons-material';
import { AcestreamChannel, AcestreamChannelFilters, acestreamChannelService } from '../services/channelService';
import { formatDate } from '../utils/errorUtils';

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
  const [filterModel, setFilterModel] = useState<GridFilterModel>({ items: [] });
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const columns = useMemo<GridColDef[]>(
    () => [
      {
        field: 'id',
        headerName: 'Acestream ID',
        minWidth: 240,
        flex: 1.15,
        filterable: true,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <Box sx={{ display: 'flex', alignItems: 'center', fontFamily: 'monospace', fontSize: 12.5, width: '100%' }}>
            <Box sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{params.row.id}</Box>
            <Tooltip title="Copy ID">
              <IconButton
                size="small"
                aria-label={`copy acestream id ${params.row.id}`}
                sx={{ ml: 0.5 }}
                onClick={(event) => {
                  event.stopPropagation();
                  void navigator.clipboard.writeText(params.row.id);
                }}
              >
                <ContentCopy fontSize="inherit" />
              </IconButton>
            </Tooltip>
          </Box>
        ),
      },
      {
        field: 'name',
        headerName: 'Name',
        flex: 1,
        minWidth: 180,
        editable: true,
        filterable: true,
      },
      {
        field: 'group',
        headerName: 'Group',
        flex: 0.8,
        minWidth: 120,
        editable: true,
        filterable: true,
      },
      {
        field: 'is_active',
        headerName: 'Active',
        width: 110,
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
        width: 96,
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
        width: 150,
        valueGetter: (params: GridValueGetterParams<AcestreamChannel>) => formatDate(params.row.last_checked),
      },
      {
        field: 'last_seen',
        headerName: 'Last Scraped',
        width: 150,
        valueGetter: (params: GridValueGetterParams<AcestreamChannel>) => formatDate(params.row.last_seen),
      },
      {
        field: 'actions',
        headerName: 'Actions',
        width: isMobile ? 210 : 260,
        sortable: false,
        filterable: false,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <Box display="flex" gap={0.25}>
            <Tooltip title="Edit">
              <IconButton
                size="small"
                aria-label={`edit channel ${params.row.name}`}
                onClick={() => {
                  onEdit(params.row);
                  onActionComplete?.();
                }}
              >
                <Edit fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete">
              <IconButton
                size="small"
                aria-label={`delete channel ${params.row.name}`}
                onClick={async () => {
                  await onDelete(params.row.id);
                  onActionComplete?.();
                }}
              >
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={params.row.is_active ? 'Deactivate' : 'Activate'}>
              <IconButton
                size="small"
                aria-label={`${params.row.is_active ? 'deactivate' : 'activate'} channel ${params.row.name}`}
                onClick={async (event) => {
                  event.stopPropagation();
                  try {
                    await acestreamChannelService.updateAcestreamChannel(params.row.id, {
                      is_active: !params.row.is_active,
                    });
                    onActionComplete?.();
                  } catch (err) {
                    setError('Failed to update channel status');
                  }
                }}
              >
                {params.row.is_active ? <PowerSettingsNew color="warning" /> : <CheckCircle color="success" />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Check Status">
              <IconButton
                size="small"
                aria-label={`check channel status ${params.row.name}`}
                onClick={(event) => {
                  event.stopPropagation();
                  onCheckStatus(params.row.id);
                }}
                disabled={checkingStatus[params.row.id]}
              >
                <Refresh color="primary" />
              </IconButton>
            </Tooltip>
            {extraActions?.(params.row)}
          </Box>
        ),
      },
    ],
    [checkingStatus, extraActions, isMobile, onActionComplete, onCheckStatus, onDelete, onEdit]
  );

  const handleFilterModelChange = (model: GridFilterModel) => {
    setFilterModel(model);
    const newFilters: AcestreamChannelFilters = { ...filters };
    let hasIsActive = false;

    model.items.forEach((item) => {
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
        }
      } else if (item.field === 'is_online' && item.value !== undefined && item.value !== '') {
        newFilters.is_online = item.value === 'true' || item.value === true;
      }
    });

    if (!model.items.some((item) => item.field === 'name')) {
      delete newFilters.search;
    }
    if (!model.items.some((item) => item.field === 'group')) {
      delete newFilters.group;
    }
    if (!model.items.some((item) => item.field === 'is_online')) {
      delete newFilters.is_online;
    }
    if (!hasIsActive) {
      delete newFilters.is_active;
      delete newFilters.active_only;
    }

    onFilterChange(newFilters);
  };

  return (
    <>
      {error ? (
        <Snackbar open autoHideDuration={5000} onClose={() => setError(null)}>
          <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        </Snackbar>
      ) : null}
      <DataGrid
        rows={channels}
        getRowId={(row) => row.id}
        columns={columns}
        loading={loading}
        density={isMobile ? 'compact' : 'standard'}
        filterModel={filterModel}
        onFilterModelChange={handleFilterModelChange}
        checkboxSelection
        disableRowSelectionOnClick
        onRowSelectionModelChange={(ids) => onSelectionChange?.(ids as string[])}
        onRowDoubleClick={(params) => onEdit(params.row as AcestreamChannel)}
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
          } catch {
            setError('Failed to save inline changes');
            return oldRow;
          }
        }}
        slots={{
          toolbar: GridToolbar,
        }}
      />
    </>
  );
};

export default ChannelTable;

