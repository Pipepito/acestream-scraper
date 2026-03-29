import React, { act } from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

import TVChannels from '../pages/TVChannels';
import { createAppTheme } from '../theme';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';

const mockNavigate = jest.fn();
const mockUseAllTVChannels = jest.fn();
const mockUseDeleteTVChannel = jest.fn();
const mockUseCreateTVChannel = jest.fn();
const mockUseUpdateTVChannel = jest.fn();

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');

  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

jest.mock('../hooks/useTVChannels', () => ({
  useAllTVChannels: (...args: unknown[]) => mockUseAllTVChannels(...args),
  useDeleteTVChannel: (...args: unknown[]) => mockUseDeleteTVChannel(...args),
  useCreateTVChannel: (...args: unknown[]) => mockUseCreateTVChannel(...args),
  useUpdateTVChannel: (...args: unknown[]) => mockUseUpdateTVChannel(...args),
}));

jest.mock('../components/AdvancedSearch', () => ({
  __esModule: true,
  default: ({ categories }: { categories?: string[] }) => (
    <div data-testid="advanced-search">filters:{categories?.join(',') || 'none'}</div>
  ),
}));

jest.mock('../components/TVChannelsTable', () => ({
  __esModule: true,
  default: ({ channels, onEdit }: { channels: Array<{ id: number; name: string }>; onEdit: (channel: { id: number; name: string }) => void }) => (
    <div data-testid="tv-channels-table">
      rows:{channels.length}
      {channels[0] ? (
        <button type="button" onClick={() => onEdit(channels[0])}>
          Open edit dialog
        </button>
      ) : null}
    </div>
  ),
}));

type LegacyUserEventWithSetup = typeof userEvent & {
  setup?: () => {
    click: (element: Element) => Promise<void>;
  };
};

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

const renderPage = ({
  isPhone = false,
  isDesktop = true,
  isWideDesktop = false,
}: {
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
} = {}) => {
  const theme = createAppTheme('light');

  mockResponsiveShellQueries(mockUseMediaQuery, theme, {
    isPhone,
    isDesktop,
    isWideDesktop,
  });

  return render(
    <ThemeProvider theme={theme}>
      <TVChannels />
    </ThemeProvider>
  );
};

const click = async (element: Element) => {
  const legacyUserEvent = userEvent as LegacyUserEventWithSetup;

  if (typeof legacyUserEvent.setup === 'function') {
    const user = legacyUserEvent.setup();
    await act(async () => {
      await user.click(element);
    });
    return;
  }

  await act(async () => {
    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
};

describe('TVChannels responsive page behavior', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMediaQuery.mockReset();

    mockUseAllTVChannels.mockReturnValue({
      data: {
        items: [
          {
            id: 7,
            name: 'Arena TV',
            logo_url: '',
            description: 'Primary sports feed',
            category: 'Sports',
            country: 'RS',
            language: 'en',
            channel_number: 7,
            is_active: true,
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }],
          },
        ],
        total: 1,
      },
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    });
    mockUseDeleteTVChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  });

  it('keeps primary actions visible while collapsing filters on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add TV Channel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show filters/i })).toBeInTheDocument();
    expect(screen.queryByTestId('advanced-search')).not.toBeInTheDocument();

    await click(screen.getByRole('button', { name: /show filters/i }));

    expect(screen.getByTestId('advanced-search')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /hide filters/i })).toBeInTheDocument();
  });

  it('uses a wide desktop two-zone layout with supporting filters beside inventory', () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: true });

    const layout = screen.getByTestId('tv-channels-page-layout');
    const filtersSection = screen.getByRole('region', { name: 'Filters' });
    const inventorySection = screen.getByRole('region', { name: 'TV Channel Inventory' });

    expect(layout).toHaveStyle({
      display: 'grid',
      gridTemplateColumns: 'minmax(0, 2fr) minmax(280px, 1fr)',
    });
    expect(inventorySection).toHaveStyle({ gridArea: 'primary' });
    expect(filtersSection).toHaveStyle({ gridArea: 'supporting' });
  });

  it('opens create and edit dialogs with mobile-safe full-screen sizing on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Add TV Channel' }));

    const createDialog = screen.getByRole('dialog', { name: 'Add TV Channel' });
    expect(within(createDialog).getByRole('textbox', { name: /channel name/i })).toBeInTheDocument();
    expect(createDialog).toHaveClass('MuiDialog-paperFullScreen');

    await click(within(createDialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Add TV Channel' })).not.toBeInTheDocument();
    });

    await click(screen.getByRole('button', { name: /show filters/i }));
    await click(screen.getByRole('button', { name: 'Open edit dialog' }));

    const editDialog = screen.getByRole('dialog', { name: 'Edit TV Channel' });
    expect(within(editDialog).getByDisplayValue('Arena TV')).toBeInTheDocument();
    expect(editDialog).toHaveClass('MuiDialog-paperFullScreen');
  });
});
