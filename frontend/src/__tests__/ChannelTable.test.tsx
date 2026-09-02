import React, { act } from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ChannelTable from '../components/ChannelTable';
import { acestreamChannelService } from '../services/channelService';
import { createAppTheme } from '../theme';
import { formatRelativeTime } from '../utils/format';

let capturedProcessRowUpdate:
  | ((newRow: Record<string, unknown>, oldRow: Record<string, unknown>) => Promise<Record<string, unknown>>)
  | undefined;

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() },
}));

jest.mock('@mui/x-data-grid', () => {
  const React = require('react');
  type MockRow = Record<string, unknown> & { id: React.Key };
  type MockColumn = { field: string; renderCell?: (params: { row: MockRow; value: unknown }) => React.ReactNode };
  type MockDataGridProps = {
    rows: MockRow[];
    columns: MockColumn[];
    slots?: { noRowsOverlay?: React.ComponentType };
    processRowUpdate?: (newRow: Record<string, unknown>, oldRow: Record<string, unknown>) => Promise<Record<string, unknown>>;
  };
  const DataGrid = ({ rows, columns, slots, processRowUpdate }: MockDataGridProps) => {
    capturedProcessRowUpdate = processRowUpdate;
    const NoRowsOverlay = slots?.noRowsOverlay;
    return (
      <div role="grid">
        {rows.length === 0 && NoRowsOverlay ? (
          <div data-testid="no-rows-overlay">
            <NoRowsOverlay />
          </div>
        ) : null}
        {rows.map((row) => (
          <div key={String(row.id)} role="row">
            {columns.map((column) => (
              <div key={column.field} data-field={column.field}>
                {column.renderCell ? column.renderCell({ row, value: row[column.field] }) : (row[column.field] as React.ReactNode)}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };
  return { __esModule: true, DataGrid };
});

jest.mock('../services/channelService', () => ({
  __esModule: true,
  acestreamChannelService: { updateAcestreamChannel: jest.fn() },
}));

const updateAcestreamChannelMock = jest.mocked(acestreamChannelService.updateAcestreamChannel);

const baseChannel = {
  id: 'acestream-1',
  name: 'Test Channel',
  group: 'Sports',
  is_active: true,
  is_online: true,
  status: 'active',
  last_seen: '2024-01-15T13:45:00Z',
  last_checked: '2024-01-16T09:00:00Z',
  epg_update_protected: false,
};

const handlers = () => ({
  onCheckStatus: jest.fn(),
  onEdit: jest.fn(),
  onToggleHidden: jest.fn(),
  onAssignTV: jest.fn(),
  onOpenTV: jest.fn(),
  onToggleTVFavorite: jest.fn(),
  onDelete: jest.fn(),
  onCopyId: jest.fn(),
});

const mountTable = (overrides: Partial<React.ComponentProps<typeof ChannelTable>> = {}) => {
  const props = handlers();
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ChannelTable
        channels={[baseChannel]}
        loading={false}
        checkingStatus={{}}
        totalCount={1}
        page={0}
        pageSize={25}
        onPaginationModelChange={jest.fn()}
        onSortChange={jest.fn()}
        onSelectionChange={jest.fn()}
        {...props}
        {...overrides}
      />
    </ThemeProvider>
  );
  return props;
};

describe('ChannelTable', () => {
  beforeEach(() => {
    capturedProcessRowUpdate = undefined;
    jest.clearAllMocks();
  });

  it('renders name with group, the ID with a copy button, online state and relative last check', () => {
    const edgeCaseChannel = {
      ...baseChannel,
      id: 'acestream-超長-🚀-مرحبا-שלום-1234567890',
      name: '🚀 超長いチャンネル名 مرحبا بالعالم שלום עולם very very very long channel name',
      group: '体育 / ニュース / أخبار / חדשות',
    };
    const handlersOf = mountTable({ channels: [edgeCaseChannel] });

    expect(screen.getByText(edgeCaseChannel.name)).toBeInTheDocument();
    expect(screen.getByText(edgeCaseChannel.group)).toBeInTheDocument();
    expect(screen.getByRole('group', { name: `Acestream channel actions for ${edgeCaseChannel.name}` })).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText(formatRelativeTime(edgeCaseChannel.last_checked))).toBeInTheDocument();
    expect(screen.queryByText('Hidden')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: `copy acestream id ${edgeCaseChannel.id}` }));
    expect(handlersOf.onCopyId).toHaveBeenCalledWith(edgeCaseChannel.id);
  });

  it('marks channels hidden from the playlist and shows the linked TV channel', () => {
    mountTable({ channels: [{ ...baseChannel, is_active: false, tv_channel_id: 4, tv_channel_name: 'Arena TV' }] });

    expect(screen.getByText('Hidden')).toBeInTheDocument();
    expect(screen.getByText('Sports · TV: Arena TV')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'go to tv channel Arena TV' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: `assign tv channel to ${baseChannel.name}` })).not.toBeInTheDocument();
  });

  it('renders the empty overlay, with filter-specific copy when filters are active', () => {
    const { unmount } = render(<div />);
    unmount();
    mountTable({ channels: [], totalCount: 0 });
    expect(screen.getByText('No channels to show')).toBeInTheDocument();
  });

  it('renders the no-match overlay when filters leave nothing', () => {
    mountTable({ channels: [], totalCount: 0, hasActiveFilters: true });
    expect(screen.getByText('No channels match the current filters')).toBeInTheDocument();
    expect(screen.queryByText('No channels to show')).not.toBeInTheDocument();
  });

  it('renders online status with explicit text for true, false and unknown', () => {
    mountTable({
      channels: [
        baseChannel,
        { ...baseChannel, id: 'acestream-2', name: 'Offline Channel', is_online: false },
        { ...baseChannel, id: 'acestream-3', name: 'Unknown Channel', is_online: null },
      ],
      totalCount: 3,
    });

    const rows = screen.getAllByRole('row');
    const offlineRow = rows.find((row) => within(row).queryByText('Offline Channel')) as HTMLElement;
    const unknownRow = rows.find((row) => within(row).queryByText('Unknown Channel')) as HTMLElement;
    expect(within(offlineRow).getByText('Offline')).toBeInTheDocument();
    expect(within(unknownRow).getByText('Unknown')).toBeInTheDocument();
  });

  it('exposes check status and TV link as visible buttons and the rest behind More actions', () => {
    const handlersOf = mountTable();

    fireEvent.click(screen.getByRole('button', { name: `check channel status ${baseChannel.name}` }));
    expect(handlersOf.onCheckStatus).toHaveBeenCalledWith(expect.objectContaining({ id: baseChannel.id }));

    fireEvent.click(screen.getByRole('button', { name: `assign tv channel to ${baseChannel.name}` }));
    expect(handlersOf.onAssignTV).toHaveBeenCalledWith(expect.objectContaining({ id: baseChannel.id }));

    fireEvent.click(screen.getByRole('button', { name: `More actions for ${baseChannel.name}` }));
    const menu = screen.getByRole('menu');
    expect(within(menu).getByRole('menuitem', { name: 'Edit' })).toBeInTheDocument();
    expect(within(menu).getByRole('menuitem', { name: 'Hide from playlist' })).toBeInTheDocument();
    expect(within(menu).getByRole('menuitem', { name: 'Delete' })).toBeInTheDocument();
    expect(within(menu).queryByRole('menuitem', { name: /favorites/ })).not.toBeInTheDocument();

    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Hide from playlist' }));
    expect(handlersOf.onToggleHidden).toHaveBeenCalledWith(expect.objectContaining({ id: baseChannel.id }));
  });

  it('offers Show in playlist and the TV favorite toggle for hidden, linked channels', () => {
    const handlersOf = mountTable({
      channels: [{ ...baseChannel, is_active: false, tv_channel_id: 4, tv_channel_name: 'Arena TV', tv_channel_is_favorite: true }],
    });

    fireEvent.click(screen.getByRole('button', { name: `More actions for ${baseChannel.name}` }));
    const menu = screen.getByRole('menu');
    expect(within(menu).getByRole('menuitem', { name: 'Show in playlist' })).toBeInTheDocument();
    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Remove Arena TV from favorites' }));
    expect(handlersOf.onToggleTVFavorite).toHaveBeenCalledWith(expect.objectContaining({ tv_channel_id: 4 }));
  });

  it('returns the previous row and shows the inline-save failure message when inline save fails', async () => {
    updateAcestreamChannelMock.mockRejectedValueOnce(new Error('save failed'));
    mountTable();
    expect(capturedProcessRowUpdate).toBeDefined();

    const oldRow = { ...baseChannel };
    const newRow = { ...baseChannel, name: 'Updated Name' };
    let result: Record<string, unknown> | undefined;
    await act(async () => {
      result = await capturedProcessRowUpdate?.(newRow, oldRow);
    });

    expect(result).toEqual(oldRow);
    expect(updateAcestreamChannelMock).toHaveBeenCalledWith(baseChannel.id, { name: 'Updated Name' });
    expect(await screen.findByText('The channel could not be updated. Try again.')).toBeInTheDocument();
  });
});
