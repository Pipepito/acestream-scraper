import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { act } from 'react';
import ChannelTable from '../components/ChannelTable';
import { acestreamChannelService } from '../services/channelService';
import { ApiError } from '../services/apiErrors';
import { formatDateTime } from '../utils/formatters';

let capturedProcessRowUpdate:
  | ((newRow: Record<string, unknown>, oldRow: Record<string, unknown>) => Promise<Record<string, unknown>>)
  | undefined;

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock('@mui/x-data-grid', () => {
  const React = require('react');

  type MockRow = Record<string, unknown> & { id: React.Key };
  type MockColumn = {
    field: string;
    valueGetter?: (params: { row: MockRow }) => unknown;
    renderCell?: (params: { row: MockRow; value: unknown }) => React.ReactNode;
  };
  type MockFilterItem = { field?: string; value?: unknown };
  type MockFilterModel = { items?: MockFilterItem[] };
  type MockDataGridProps = {
    rows: MockRow[];
    columns: MockColumn[];
    slots?: {
      noRowsOverlay?: React.ComponentType;
      noResultsOverlay?: React.ComponentType;
    };
    processRowUpdate?: (newRow: Record<string, unknown>, oldRow: Record<string, unknown>) => Promise<Record<string, unknown>>;
    filterModel?: MockFilterModel;
    onFilterModelChange?: (model: MockFilterModel) => void;
  };

  const DataGrid = ({ rows, columns, slots, processRowUpdate, filterModel, onFilterModelChange }: MockDataGridProps) => {
    capturedProcessRowUpdate = processRowUpdate;

    const NoRowsOverlay = slots?.noRowsOverlay;
    const NoResultsOverlay = slots?.noResultsOverlay;
    const hasVisibleRows = rows.length > 0;
    const hasActiveFilters = Boolean(
      filterModel?.items?.some((item) => item.value !== undefined && item.value !== '')
    );

    return (
      <div role="grid">
        <button
          type="button"
          onClick={() => onFilterModelChange?.({ items: [{ field: 'name', value: '' }] })}
        >
          apply empty name filter
        </button>
        <button
          type="button"
          onClick={() => onFilterModelChange?.({ items: [{ field: 'name', value: 'Missing channel' }] })}
        >
          apply active name filter
        </button>
        {!hasVisibleRows && !hasActiveFilters && NoRowsOverlay ? (
          <div data-testid="no-rows-overlay">
            <NoRowsOverlay />
          </div>
        ) : null}
        {!hasVisibleRows && hasActiveFilters && NoResultsOverlay ? (
          <div data-testid="no-results-overlay">
            <NoResultsOverlay />
          </div>
        ) : null}
        {rows.map((row) => (
          <div key={String(row.id)} role="row">
            {columns.map((column) => {
              const field = String(column.field);
              const valueGetter = column.valueGetter;
              const renderCell = column.renderCell;
              const value = valueGetter ? valueGetter({ row }) : row[field];

              return (
                <div key={field} data-field={field}>
                  {renderCell ? renderCell({ row, value }) : value as React.ReactNode}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    );
  };

  return {
    __esModule: true,
    DataGrid,
    GridToolbar: () => <div data-testid="grid-toolbar" />,
  };
});

jest.mock('../services/channelService', () => ({
  __esModule: true,
  acestreamChannelService: {
    updateAcestreamChannel: jest.fn(),
  },
}));

const updateAcestreamChannelMock = jest.mocked(acestreamChannelService.updateAcestreamChannel);
const originalClipboard = navigator.clipboard;

const theme = createTheme({
  appTokens: {
    surface: {
      border: '#d0d7de',
      raised: '#ffffff',
    },
    layout: {
      cardRadius: 12,
    },
  },
  typography: {
    sectionTitle: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    helperText: {
      fontSize: '0.875rem',
    },
  },
} as any);

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

const renderTable = (overrides: Partial<React.ComponentProps<typeof ChannelTable>> = {}) =>
  render(
    <ThemeProvider theme={theme}>
      <div style={{ width: 1600, height: 700 }}>
        <ChannelTable
          channels={[baseChannel]}
          loading={false}
          onCheckStatus={jest.fn()}
          onEdit={jest.fn()}
          onDelete={jest.fn().mockResolvedValue(undefined)}
          checkingStatus={{}}
          filters={{}}
          onFilterChange={jest.fn()}
          totalCount={1}
          page={0}
          pageSize={25}
          onPaginationModelChange={jest.fn()}
          onSortChange={jest.fn()}
          onSelectionChange={jest.fn()}
          {...overrides}
        />
      </div>
    </ThemeProvider>
  );

describe('ChannelTable', () => {
  beforeEach(() => {
    capturedProcessRowUpdate = undefined;
    jest.clearAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: originalClipboard,
    });
  });

  it('renders dense edge-case data, accessible actions, and formatted timestamps', () => {
    const edgeCaseChannel = {
      ...baseChannel,
      id: 'acestream-超長-🚀-مرحبا-שלום-1234567890',
      name: '🚀 超長いチャンネル名 مرحبا بالعالم שלום עולם very very very long channel name',
      group: '体育 / ニュース / أخبار / חדשות',
    };

    renderTable({ channels: [edgeCaseChannel] });

    expect(screen.getByText(edgeCaseChannel.name)).toBeInTheDocument();
    expect(screen.getByRole('group', { name: `Acestream channel actions for ${edgeCaseChannel.name}` })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: `copy acestream id ${edgeCaseChannel.id}` })).toBeInTheDocument();
    expect(screen.getByText(formatDateTime(edgeCaseChannel.last_checked))).toBeInTheDocument();
    expect(screen.getByText(formatDateTime(edgeCaseChannel.last_seen))).toBeInTheDocument();
  });

  it('renders the no rows overlay without also rendering no results', () => {
    renderTable({ channels: [], totalCount: 0 });

    expect(screen.getByTestId('no-rows-overlay')).toBeInTheDocument();
    expect(screen.getByText('No channels to show')).toBeInTheDocument();
    expect(screen.getByText('Adjust your filters or add a channel to start monitoring stream health.')).toBeInTheDocument();
    expect(screen.queryByTestId('no-results-overlay')).not.toBeInTheDocument();
    expect(screen.queryByText('No channels match the current filters')).not.toBeInTheDocument();
  });

  it('renders the no results overlay when an active filter leaves no matching rows', () => {
    renderTable({ channels: [], totalCount: 0 });

    fireEvent.click(screen.getByRole('button', { name: 'apply active name filter' }));

    expect(screen.getByTestId('no-results-overlay')).toBeInTheDocument();
    expect(screen.getByText('No channels match the current filters')).toBeInTheDocument();
    expect(screen.getByText('Adjust or clear the filters to see more channels.')).toBeInTheDocument();
    expect(screen.queryByTestId('no-rows-overlay')).not.toBeInTheDocument();
    expect(screen.queryByText('When data becomes available, it will appear here.')).not.toBeInTheDocument();
  });

  it('clears the server search filter when the grid filter remains but has an empty value', () => {
    const onFilterChange = jest.fn();

    renderTable({ filters: { search: 'Existing search' }, onFilterChange });

    fireEvent.click(screen.getByRole('button', { name: 'apply empty name filter' }));

    expect(onFilterChange).toHaveBeenCalledWith({});
  });

  it('renders online status with explicit text semantics for true and false values', () => {
    renderTable({
      channels: [
        baseChannel,
        {
          ...baseChannel,
          id: 'acestream-2',
          name: 'Offline Channel',
          is_online: false,
        },
      ],
      totalCount: 2,
    });

    const rows = screen.getAllByRole('row');
    const onlineRow = rows.find((row) => within(row).queryByText(baseChannel.name));
    const offlineRow = rows.find((row) => within(row).queryByText('Offline Channel'));

    expect(onlineRow).toBeDefined();
    expect(offlineRow).toBeDefined();
    expect(within(onlineRow as HTMLElement).getByText('Online')).toBeInTheDocument();
    expect(within(offlineRow as HTMLElement).getByText('Offline')).toBeInTheDocument();
  });

  it('shows fixed user-safe copy when clipboard access fails', async () => {
    const writeText = jest.fn().mockRejectedValue(new Error('permission denied'));
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText,
      },
    });

    renderTable();

    fireEvent.click(screen.getByRole('button', { name: `copy acestream id ${baseChannel.id}` }));

    await waitFor(() => {
      expect(screen.getByText('Unable to copy the Acestream ID right now.')).toBeInTheDocument();
    });
  });

  it('shows backend error detail for row-action failures', async () => {
    updateAcestreamChannelMock.mockRejectedValueOnce(
      new ApiError({ message: 'Channel API exploded', status: 422, kind: 'validation', canRetry: false })
    );

    renderTable();

    fireEvent.click(screen.getByRole('button', { name: `deactivate channel ${baseChannel.name}` }));

    await waitFor(() => {
      expect(screen.getByText('Channel API exploded')).toBeInTheDocument();
    });
  });

  it('does not surface a second delete failure message from the table when delete rejects', async () => {
    const onDelete = jest.fn().mockRejectedValue(new ApiError({
      message: 'Delete failed upstream',
      status: 500,
      kind: 'server',
      canRetry: true,
    }));

    renderTable({ onDelete });

    fireEvent.click(screen.getByRole('button', { name: `delete channel ${baseChannel.name}` }));

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith(baseChannel.id);
    });

    expect(screen.queryByText('Delete failed upstream')).not.toBeInTheDocument();
  });

  it('returns the previous row and shows the inline-save failure message when inline save fails', async () => {
    updateAcestreamChannelMock.mockRejectedValueOnce(new Error('save failed'));

    renderTable();

    expect(capturedProcessRowUpdate).toBeDefined();

    const oldRow = { ...baseChannel };
    const newRow = { ...baseChannel, name: 'Updated Name' };
    let result: Record<string, unknown> | undefined;

    await act(async () => {
      result = await capturedProcessRowUpdate?.(newRow, oldRow);
    });

    expect(result).toEqual(oldRow);

    await waitFor(() => {
      expect(screen.getByText('The channel could not be updated. Try again.')).toBeInTheDocument();
    });
  });
});
