import React from 'react';
import { DataGrid, GridColDef, GridRenderCellParams, GridSortModel } from '@mui/x-data-grid';
import {
  Box,
  IconButton,
  Avatar,
  Tooltip,
  Chip,
  Button,
  CircularProgress,
  Paper,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  type SelectChangeEvent,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Edit, Delete, OpenInNew, Star, StarBorder } from '@mui/icons-material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import { TVChannel } from '../types/tvChannelTypes';
import RowActionsMenu, { type RowAction } from './RowActionsMenu';
import EmptyState from './state/EmptyState';
import { shouldDisableGridVirtualization } from '../config/runtime';

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
  onOpen: (id: number) => void;
  onToggleFavorite: (channel: TVChannel) => void;
  /** Plays the channel's best stream. Omit it and the Play control stays disabled. */
  onPlay?: (channel: TVChannel) => void;
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
  onOpen,
  onToggleFavorite,
  onPlay,
}) => {
  const theme = useTheme();
  const isCompact = useMediaQuery(theme.breakpoints.down('md'));

  const totalPages = totalCount > 0 ? Math.ceil(totalCount / pageSize) : 0;
  const rangeStart = totalCount === 0 ? 0 : page * pageSize + 1;
  const rangeEnd = totalCount === 0 ? 0 : Math.min(totalCount, (page + 1) * pageSize);

  const handlePageSizeChange = (event: SelectChangeEvent<number>) => {
    const nextPageSize = Number(event.target.value);

    onPageSizeChange(nextPageSize);
    onPageChange(0);
  };

  const hasNumbers = channels.some((channel) => Boolean(channel.channel_number));
  const hasLanguage = channels.some((channel) => Boolean(channel.language));
  const hasCountry = channels.some((channel) => Boolean(channel.country));

  const renderActions = (channel: TVChannel, isMobile = false) => {
    const canPlay = Boolean(onPlay) && Boolean(channel.acestream_channels?.length);

    if (isMobile) {
      return (
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap alignItems="center">
          <Tooltip title={channel.is_favorite ? 'Remove from favorites' : 'Add to favorites'}>
            <IconButton
              size="medium"
              color={channel.is_favorite ? 'warning' : 'default'}
              aria-label={`toggle favorite for tv channel ${channel.name}`}
              aria-pressed={channel.is_favorite}
              onClick={() => onToggleFavorite(channel)}
            >
              {channel.is_favorite ? <Star fontSize="small" /> : <StarBorder fontSize="small" />}
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<Edit fontSize="small" />}
            aria-label={`edit tv channel ${channel.name}`}
            onClick={() => onEdit(channel)}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete fontSize="small" />}
            aria-label={`delete tv channel ${channel.name}`}
            onClick={() => onDelete(channel.id)}
          >
            Delete
          </Button>
          <Button
            variant="outlined"
            startIcon={<PlayArrowRounded fontSize="small" />}
            aria-label={`play tv channel ${channel.name}`}
            disabled={!canPlay}
            onClick={() => onPlay?.(channel)}
          >
            Play
          </Button>
          <Button
            variant="contained"
            startIcon={<OpenInNew fontSize="small" />}
            aria-label={`open tv channel ${channel.name}`}
            onClick={() => onOpen(channel.id)}
          >
            Open
          </Button>
        </Stack>
      );
    }

    // Two visible actions (play, open) and the rest behind "More actions", the
    // row-action rule the Acestream rows follow. Favorite state stays visible
    // on the row through the star next to the name.
    const menuActions: RowAction[] = [
      {
        label: channel.is_favorite ? 'Remove from favorites' : 'Add to favorites',
        icon: channel.is_favorite ? <Star fontSize="small" /> : <StarBorder fontSize="small" />,
        onClick: () => onToggleFavorite(channel),
      },
      { label: 'Edit', icon: <Edit fontSize="small" />, onClick: () => onEdit(channel) },
      { label: 'Delete', icon: <Delete fontSize="small" />, danger: true, onClick: () => onDelete(channel.id) },
    ];

    return (
      <Box display="flex" gap={0.25} role="group" aria-label={`TV channel actions for ${channel.name}`}>
        <Tooltip title={canPlay ? 'Play the best stream' : 'No stream to play yet'}>
          <span>
            <IconButton
              size="small"
              color="primary"
              aria-label={`play tv channel ${channel.name}`}
              disabled={!canPlay}
              onClick={() => onPlay?.(channel)}
            >
              <PlayArrowRounded fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
        <Tooltip title="Open channel page">
          <IconButton size="small" color="primary" aria-label={`open tv channel ${channel.name}`} onClick={() => onOpen(channel.id)}>
            <OpenInNew fontSize="small" />
          </IconButton>
        </Tooltip>
        <RowActionsMenu label={`More actions for ${channel.name}`} actions={menuActions} />
      </Box>
    );
  };

  const DesktopEmptyState = () => (
    <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', py: 3, px: 2 }}>
      <EmptyState
        title="No TV channels to show"
        description="Add a TV channel or adjust your filters to start organizing playback sources."
      />
    </Box>
  );

  const DesktopPageEmptyState = () => (
    <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', py: 3, px: 2 }}>
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          borderRadius: 2,
          borderColor: theme.appTokens.surface.border,
          backgroundColor: theme.appTokens.surface.raised,
          width: '100%',
          maxWidth: 480,
        }}
      >
        <Typography variant="sectionTitle" component="h2">
          No TV channels on this page
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
          Move between pages to keep browsing the list.
        </Typography>
      </Paper>
    </Box>
  );

  const MobileLoadingState = () => (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        minHeight: 200,
        py: 3,
        gap: 1,
      }}
    >
      <CircularProgress aria-label="Loading TV channels" size={28} />
      <Typography variant="sectionTitle" component="p">
        Loading TV channels
      </Typography>
      <Typography variant="body2" color="text.secondary" align="center">
        Preparing the latest results.
      </Typography>
    </Box>
  );

  const DesktopLoadingState = () => (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        minHeight: 280,
        py: 4,
        px: 2,
        gap: 1,
      }}
    >
      <CircularProgress aria-label="Loading TV channels" size={28} />
      <Typography variant="sectionTitle" component="p">
        Loading TV channels
      </Typography>
      <Typography variant="body2" color="text.secondary" align="center">
        Refreshing the latest results.
      </Typography>
    </Box>
  );

  const MobilePagination = () => (
    <Paper
      variant="outlined"
      sx={{
        p: 1.5,
        borderRadius: 2,
        borderColor: theme.appTokens.surface.border,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      <Stack spacing={1.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
          <Typography variant="body2" color="text.secondary">
            {`${rangeStart}-${rangeEnd} of ${totalCount}`}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {totalPages > 0 ? `Page ${page + 1} of ${totalPages}` : 'Page 0 of 0'}
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel id="tv-channels-mobile-page-size-label">Rows per page</InputLabel>
            <Select
              labelId="tv-channels-mobile-page-size-label"
              value={pageSize}
              label="Rows per page"
              onChange={handlePageSizeChange}
              inputProps={{ 'aria-label': 'Rows per page' }}
            >
              {[10, 25, 50, 100].map((size) => (
                <MenuItem key={size} value={size}>
                  {size}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" disabled={page === 0} aria-label="Go to previous page" onClick={() => onPageChange(page - 1)}>
              Previous
            </Button>
            <Button
              variant="outlined"
              disabled={page >= totalPages - 1 || totalPages === 0}
              aria-label="Go to next page"
              onClick={() => onPageChange(page + 1)}
            >
              Next
            </Button>
          </Stack>
        </Stack>
      </Stack>
    </Paper>
  );

  const renderMobileMetadata = (channel: TVChannel) => {
    const secondaryMetadata = [
      channel.language ? `Language: ${channel.language}` : null,
      channel.country ? `Country: ${channel.country}` : null,
    ].filter(Boolean);

    if (secondaryMetadata.length === 0) {
      return null;
    }

    return (
      <Stack spacing={0.5}>
        {secondaryMetadata.map((item) => (
          <Typography key={item} variant="body2" color="text.secondary">
            {item}
          </Typography>
        ))}
      </Stack>
    );
  };

  const getStatusChipSx = (isActive: boolean) => ({
    borderColor: isActive ? theme.appTokens.status.success.border : theme.appTokens.status.warning.border,
    backgroundColor: isActive ? theme.appTokens.status.success.bg : theme.appTokens.status.warning.bg,
    color: isActive ? theme.appTokens.status.success.text : theme.appTokens.status.warning.text,
  });

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
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      minWidth: 140,
      renderCell: (params: GridRenderCellParams<TVChannel>) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, minWidth: 0 }}>
          {params.row.is_favorite ? <Star fontSize="small" color="warning" titleAccess="Favorite" /> : null}
          <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 600 }}>
            {params.row.name}
          </Box>
        </Box>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 130,
      sortable: false,
      renderCell: (params: GridRenderCellParams<TVChannel>) => renderActions(params.row),
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
          size="small"
          variant="outlined"
          sx={getStatusChipSx(params.row.is_active)}
        />
      ),
      filterable: true,
    },
  ];

  if (isCompact) {
    if (loading) {
      return <MobileLoadingState />;
    }

    return (
      <Stack spacing={1.5}>
        {channels.length ? (
          channels.map((channel) => {
            const streamCount = channel.acestream_channels?.length ?? 0;

            return (
              <Paper
                key={channel.id}
                component="article"
                aria-label={channel.name}
                variant="outlined"
                sx={{
                  p: 2,
                  borderRadius: 2,
                  borderColor: theme.appTokens.surface.border,
                  backgroundColor: theme.appTokens.surface.raised,
                }}
              >
                <Stack spacing={1.5}>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    {channel.logo_url ? <Avatar src={channel.logo_url} alt={channel.name} /> : <Avatar>{channel.name.charAt(0)}</Avatar>}
                    <Box sx={{ minWidth: 0, flex: 1 }}>
                      <Typography variant="sectionTitle" component="h3" sx={{ overflowWrap: 'break-word' }}>
                        {channel.name}
                      </Typography>
                      {channel.channel_number ? (
                        <Typography variant="body2" color="text.secondary">
                          Channel {channel.channel_number}
                        </Typography>
                      ) : null}
                    </Box>
                    <Chip
                      label={channel.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      variant="outlined"
                      sx={getStatusChipSx(channel.is_active)}
                    />
                  </Stack>

                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {channel.category ? <Chip label={channel.category} size="small" variant="outlined" /> : null}
                    <Chip label={`${streamCount} ${streamCount === 1 ? 'stream' : 'streams'}`} size="small" variant="outlined" />
                  </Stack>

                  {renderMobileMetadata(channel)}

                  {renderActions(channel, true)}
                </Stack>
              </Paper>
            );
          })
        ) : totalCount === 0 ? (
          <DesktopEmptyState />
        ) : (
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              borderRadius: 2,
              borderColor: theme.appTokens.surface.border,
              backgroundColor: theme.appTokens.surface.raised,
            }}
          >
            <Typography variant="sectionTitle" component="h2">
              No TV channels on this page
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
              Move between pages to keep browsing the list.
            </Typography>
          </Paper>
        )}
        {totalCount > 0 ? <MobilePagination /> : null}
      </Stack>
    );
  }

  return (
    <Paper
      component="section"
      role="region"
      aria-label="TV channel inventory"
      variant="outlined"
      sx={{
        borderRadius: 2,
        overflow: 'hidden',
        borderColor: theme.appTokens.surface.border,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      {loading ? <DesktopLoadingState /> : null}
      {!loading && channels.length === 0 ? (totalCount === 0 ? <DesktopEmptyState /> : <DesktopPageEmptyState />) : null}
      {/* Mount the grid only when there is something to lay out: a grid hidden with display:none has no
          width, and MUI X logs a useResizeContainer error for it on every render. */}
      {!loading && channels.length > 0 ? (
      <DataGrid
        rows={channels}
        columns={columns}
        getRowId={(row) => row.id}
        loading={false}
        density={isCompact ? 'compact' : 'standard'}
        columnBuffer={12}
        disableVirtualization={shouldDisableGridVirtualization({ mode: process.env.NODE_ENV })}
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
          channel_number: hasNumbers,
          country: !isCompact && hasCountry,
          language: !isCompact && hasLanguage,
        }}
        sortingMode="server"
        onSortModelChange={onSortChange}
        disableColumnMenu
        slots={{ noRowsOverlay: DesktopEmptyState }}
        sx={{
          border: 0,
          backgroundColor: 'transparent',
          '& .MuiDataGrid-main': {
            overflow: 'hidden',
          },
          '& .MuiDataGrid-toolbarContainer': {
            px: 1.5,
            py: 1,
            borderBottom: `1px solid ${theme.appTokens.surface.border}`,
            position: 'static',
            top: 'auto',
            zIndex: 'auto',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: theme.appTokens.surface.canvas,
            position: 'static',
            top: 'auto',
            zIndex: 'auto',
          },
        }}
      />
      ) : null}
    </Paper>
  );
};

export default TVChannelsTable;
