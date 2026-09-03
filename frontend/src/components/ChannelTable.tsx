import React, { useMemo, useState } from 'react';
import { DataGrid, GridColDef, GridRenderCellParams, GridSortModel } from '@mui/x-data-grid';
import { Alert, Box, Chip, IconButton, Snackbar, Tooltip, Typography } from '@mui/material';
import { ContentCopy } from '@mui/icons-material';
import EmptyState from './state/EmptyState';
import ChannelRowActions, { type ChannelActionHandlers } from './channels/ChannelRowActions';
import OnlineChip from './channels/OnlineChip';
import { AcestreamChannel, acestreamChannelService } from '../services/channelService';
import { shouldDisableGridVirtualization } from '../config/runtime';
import { formatRelativeTime } from '../utils/format';
import { formatDateTime } from '../utils/formatters';

const INLINE_SAVE_FAILURE_MESSAGE = 'The channel could not be updated. Try again.';

const ChannelTableEmptyOverlay = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', py: 3, px: 2 }}>
    <EmptyState title="No channels to show" description="Adjust your filters or add a channel to start monitoring stream health." />
  </Box>
);

export interface ChannelTableProps extends ChannelActionHandlers {
  channels: AcestreamChannel[];
  loading: boolean;
  checkingStatus: Record<string, boolean>;
  hasActiveFilters?: boolean;
  totalCount: number;
  page: number;
  pageSize: number;
  onPaginationModelChange: (model: { page: number; pageSize: number }) => void;
  onSortChange: (model: GridSortModel) => void;
  onSelectionChange?: (selectedIds: string[]) => void;
  onCopyId: (id: string) => void;
}

const ChannelTable: React.FC<ChannelTableProps> = ({
  channels,
  loading,
  checkingStatus,
  hasActiveFilters = false,
  totalCount,
  page,
  pageSize,
  onSortChange,
  onPaginationModelChange,
  onSelectionChange,
  onCopyId,
  onPlay,
  onCheckStatus,
  onEdit,
  onToggleHidden,
  onAssignTV,
  onOpenTV,
  onToggleTVFavorite,
  onDelete,
}) => {
  const [error, setError] = useState<string | null>(null);

  const columns = useMemo<GridColDef[]>(
    () => [
      {
        field: 'name',
        headerName: 'Channel',
        flex: 1,
        minWidth: 220,
        editable: true,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <Box sx={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
            <Box sx={{ minWidth: 0 }}>
              <Typography component="span" sx={{ display: 'block', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {params.row.name}
              </Typography>
              <Typography component="span" variant="body2" color="text.secondary" sx={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {params.row.group || 'No group'}
                {params.row.tv_channel_name ? ` · TV: ${params.row.tv_channel_name}` : ''}
              </Typography>
            </Box>
            {params.row.is_active === false ? <Chip label="Hidden" size="small" variant="outlined" sx={{ minWidth: 72 }} /> : null}
          </Box>
        ),
      },
      {
        field: 'id',
        headerName: 'ID',
        minWidth: 180,
        flex: 0.8,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <Box sx={{ display: 'flex', alignItems: 'center', fontFamily: 'monospace', fontSize: 12.5, width: '100%', minWidth: 0 }}>
            <Box sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0 }}>{params.row.id}</Box>
            <Tooltip title="Copy ID">
              <IconButton
                size="small"
                aria-label={`copy acestream id ${params.row.id}`}
                sx={{ ml: 0.5 }}
                onClick={(event) => {
                  event.stopPropagation();
                  onCopyId(params.row.id);
                }}
              >
                <ContentCopy fontSize="inherit" />
              </IconButton>
            </Tooltip>
          </Box>
        ),
      },
      {
        field: 'is_online',
        headerName: 'Online',
        width: 110,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => <OnlineChip isOnline={params.row.is_online} />,
      },
      {
        field: 'last_checked',
        headerName: 'Last checked',
        width: 130,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <Tooltip title={params.row.last_checked ? formatDateTime(params.row.last_checked) : 'Never checked'}>
            <span>{formatRelativeTime(params.row.last_checked)}</span>
          </Tooltip>
        ),
      },
      {
        field: 'actions',
        headerName: 'Actions',
        width: 140,
        sortable: false,
        filterable: false,
        renderCell: (params: GridRenderCellParams<AcestreamChannel>) => (
          <ChannelRowActions
            channel={params.row}
            checking={Boolean(checkingStatus[params.row.id])}
            onPlay={onPlay}
            onCheckStatus={onCheckStatus}
            onEdit={onEdit}
            onToggleHidden={onToggleHidden}
            onAssignTV={onAssignTV}
            onOpenTV={onOpenTV}
            onToggleTVFavorite={onToggleTVFavorite}
            onDelete={onDelete}
          />
        ),
      },
    ],
    [checkingStatus, onAssignTV, onCheckStatus, onCopyId, onDelete, onEdit, onOpenTV, onPlay, onToggleHidden, onToggleTVFavorite]
  );

  const NoRowsOverlay = hasActiveFilters
    ? () => (
        <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', py: 3, px: 2 }}>
          <EmptyState title="No channels match the current filters" description="Adjust or clear the filters to see more channels." />
        </Box>
      )
    : ChannelTableEmptyOverlay;

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
        rowHeight={56}
        columnBuffer={12}
        disableVirtualization={shouldDisableGridVirtualization({ mode: process.env.NODE_ENV })}
        disableColumnFilter
        disableColumnMenu
        checkboxSelection
        disableRowSelectionOnClick
        onRowSelectionModelChange={(ids) => onSelectionChange?.(ids as string[])}
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
            await acestreamChannelService.updateAcestreamChannel(newRow.id, { name: newRow.name });
            return newRow;
          } catch {
            setError(INLINE_SAVE_FAILURE_MESSAGE);
            return oldRow;
          }
        }}
        onProcessRowUpdateError={() => setError(INLINE_SAVE_FAILURE_MESSAGE)}
        slots={{ noRowsOverlay: NoRowsOverlay }}
        sx={{ '& .MuiDataGrid-cell': { alignItems: 'center' } }}
      />
    </>
  );
};

export default ChannelTable;
