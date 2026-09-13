import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import RulesTab from '../components/epg/RulesTab';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseAllEPGStringMappings = jest.fn();
const mockUseDeleteGlobalEPGStringMapping = jest.fn();

jest.mock('../hooks/useEPG', () => ({
  useAllEPGStringMappings: (...args: unknown[]) => mockUseAllEPGStringMappings(...args),
  useDeleteGlobalEPGStringMapping: (...args: unknown[]) => mockUseDeleteGlobalEPGStringMapping(...args),
}));

describe('EPG RulesTab', () => {
  const renderTab = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <RulesTab />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAllEPGStringMappings.mockReturnValue({
      data: [
        { id: 11, epg_channel_id: 101, search_pattern: 'Sport TV', is_exclusion: false },
        { id: 12, epg_channel_id: 202, search_pattern: 'Regional Feed', is_exclusion: true },
      ],
      isLoading: false,
      error: undefined,
    });
    mockUseDeleteGlobalEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false });
  });

  it('renders the rules with their type and a link to the guide channel', () => {
    renderTab();
    const table = screen.getByRole('table', { name: 'Matching rules' });
    expect(within(table).getByText('Sport TV')).toBeInTheDocument();
    expect(within(table).getByText('Include')).toBeInTheDocument();
    expect(within(table).getByText('Exclude')).toBeInTheDocument();
    expect(within(table).getByRole('link', { name: 'Channel #101' })).toHaveAttribute('href', '/epg/channels/101');
  });

  it('confirms before deleting a rule', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseDeleteGlobalEPGStringMapping.mockReturnValue({ mutateAsync, isPending: false });
    renderTab();

    fireEvent.click(screen.getByRole('button', { name: 'Delete mapping Sport TV' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete the rule “Sport TV”?' });
    expect(mutateAsync).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(11));
    expect(await screen.findByText('Deleted rule Sport TV')).toBeInTheDocument();
  });

  it('shows an empty state and an error state', () => {
    mockUseAllEPGStringMappings.mockReturnValue({ data: [], isLoading: false, error: undefined });
    const { unmount } = renderTab();
    expect(screen.getByText(/No rules yet/)).toBeInTheDocument();
    unmount();

    mockUseAllEPGStringMappings.mockReturnValue({ data: undefined, isLoading: false, error: new Error('boom') });
    renderTab();
    expect(screen.getByText('Unable to load the matching rules right now.')).toBeInTheDocument();
  });
});
