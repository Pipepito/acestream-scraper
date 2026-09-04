import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Snackbar,
  Stack,
  Tab,
  TablePagination,
  Tabs,
  Typography,
  useTheme,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { Add as AddIcon, Refresh as RefreshIcon, FileDownload as FileDownloadIcon } from '@mui/icons-material';
import { useEPGSources, useEPGChannels } from '../hooks/useEPG';
import { useTVChannelCatalog } from '../hooks/useTVChannels';
import { useSnackbar } from '../hooks/useSnackbar';
import { useEPGSourceManagement } from '../hooks/useEPGSourceManagement';
import { useEPGMatchAnalysis } from '../hooks/useEPGMatchAnalysis';
import { useEPGChannelSelection } from '../hooks/useEPGChannelSelection';
import { EPGMatchStrictness } from '../services/tvChannelService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import EPGSourcesTable from '../components/EPGSourcesTable';
import EPGSourceDialog from '../components/EPGSourceDialog';
import EPGMatchAnalysisPanel from '../components/EPGMatchAnalysisPanel';
import EPGChannelInventoryTable from '../components/EPGChannelInventoryTable';
import EPGXmlOutputPanel from '../components/EPGXmlOutputPanel';
import RulesTab from '../components/epg/RulesTab';
import { formatRelativeTime } from '../utils/format';

export const EPG_TABS = ['sources', 'channels', 'matching', 'rules', 'export'] as const;
export type EPGTab = (typeof EPG_TABS)[number];
const TAB_LABELS: Record<EPGTab, string> = {
  sources: 'Sources',
  channels: 'Channels',
  matching: 'Matching',
  rules: 'Rules',
  export: 'Export',
};

const isEPGTab = (value: string | null): value is EPGTab => EPG_TABS.includes(value as EPGTab);

const EPG: React.FC = () => {
  const theme = useTheme();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const activeTab: EPGTab = isEPGTab(tabParam) ? tabParam : 'sources';
  const selectTab = (tab: EPGTab) => {
    const next = new URLSearchParams(searchParams);
    if (tab === 'sources') next.delete('tab');
    else next.set('tab', tab);
    setSearchParams(next, { replace: true });
  };

  // Snackbar state
  const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();

  // React Query hooks
  const { data: epgSources, isLoading: isLoadingSources } = useEPGSources();
  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined);
  const [channelPage, setChannelPage] = useState(1);
  const [channelPageSize, setChannelPageSize] = useState(50);

  // Keep the list query last so the newest call always reflects the visible page.
  const { data: allChannelsPage } = useEPGChannels(undefined, 1, 1);
  const { data: epgChannelPage, isLoading: isLoadingChannels } = useEPGChannels(selectedSourceId, channelPage, channelPageSize);
  const {
    data: tvChannels,
    isLoading: isLoadingTVChannelCatalog,
    error: tvChannelCatalogError,
  } = useTVChannelCatalog();

  const {
    openSourceDialog,
    isEditSource,
    sourceFormData,
    refreshingSourceId,
    isRefreshingAll,
    handleAddSourceClick,
    handleEditSourceClick,
    handleCloseSourceDialog,
    handleSourceFormChange,
    handleSourceFormSubmit,
    handleDeleteSourceClick,
    handleRefreshSourceClick,
    handleRefreshAllClick,
  } = useEPGSourceManagement(showSnackbar);

  const {
    matchStrictness,
    setMatchStrictness,
    isAnalyzingMatches,
    matchAnalysis,
    matchFilter,
    setMatchFilter,
    selectedMatchRowIds,
    filteredMatchRows,
    handleAnalyzeMatches,
    handleToggleMatchRow,
    handleCreateMatchedTVChannels,
  } = useEPGMatchAnalysis(selectedSourceId, showSnackbar);

  const epgChannels = useMemo(() => epgChannelPage?.items || [], [epgChannelPage]);
  const totalEPGChannels = epgChannelPage?.total || 0;
  const sourceCount = epgSources?.length ?? 0;
  const enabledSourceCount = epgSources?.filter((source) => source.enabled).length ?? 0;
  const totalChannelPages = Math.max(1, Math.ceil(totalEPGChannels / channelPageSize));

  const {
    selectedEPGChannelIds,
    visibleUnmappedChannelIds,
    isTVChannelCatalogReady,
    isChannelMapped,
    handleSelectAllChannels,
    handleSelectChannel,
    handleBulkCreateTVChannels,
  } = useEPGChannelSelection({
    epgChannels,
    tvChannels,
    isLoadingTVChannelCatalog,
    tvChannelCatalogError,
    selectedSourceId,
    channelPage,
    channelPageSize,
    showSnackbar,
  });

  const guideChannelTotal = allChannelsPage?.total;
  const linkedCount = (tvChannels ?? []).filter((channel) => Boolean(channel.epg_id)).length;
  const lastRefresh = (epgSources ?? [])
    .map((source) => source.last_updated)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);
  const failingSources = (epgSources ?? []).filter((source) => source.enabled && source.error_count > 0).length;

  useEffect(() => {
    if (!isLoadingChannels && channelPage > totalChannelPages) {
      setChannelPage(1);
    }
  }, [channelPage, totalChannelPages, isLoadingChannels]);

  const handleSourceFilterChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value;
    setSelectedSourceId(value === 'all' ? undefined : Number(value));
    setChannelPage(1);
  };

  const handleChannelPageChange = (_event: unknown, page: number) => {
    setChannelPage(page + 1);
  };

  const handleChannelPageSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setChannelPageSize(Number(event.target.value));
    setChannelPage(1);
  };

  const handleMatchStrictnessChange = (event: SelectChangeEvent<string>) => {
    setMatchStrictness(event.target.value as EPGMatchStrictness);
  };

  const sourceSelect = (
    <FormControl size="small" sx={{ minWidth: 240 }}>
      <InputLabel id="epg-source-filter-label">EPG Source</InputLabel>
      <Select labelId="epg-source-filter-label" label="EPG Source" value={selectedSourceId?.toString() ?? 'all'} onChange={handleSourceFilterChange}>
        <MenuItem value="all">All sources</MenuItem>
        {(epgSources || []).map((source) => (
          <MenuItem key={source.id} value={source.id.toString()}>
            {source.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title="EPG"
        subtitle="Programme guides for your channels: sources, guide channels, matching rules and the XML export."
        actions={
          <Button variant="outlined" startIcon={<FileDownloadIcon />} onClick={() => selectTab('export')}>
            Export XML
          </Button>
        }
      />

      <StatusLine
        aria-label="EPG summary"
        items={[
          { label: 'Sources', value: `${sourceCount} (${enabledSourceCount} enabled)`, tone: failingSources > 0 ? 'error' : 'default' },
          { label: 'Guide channels', value: guideChannelTotal === undefined ? '…' : String(guideChannelTotal) },
          { label: 'Linked to a TV channel', value: tvChannels ? String(linkedCount) : '…' },
          { label: 'Last refresh', value: formatRelativeTime(lastRefresh), tone: lastRefresh ? 'default' : 'warning' },
          ...(failingSources > 0 ? [{ label: 'Failing', value: String(failingSources), tone: 'error' as const }] : []),
        ]}
      />

      <Tabs
        value={activeTab}
        onChange={(_event, value: EPGTab) => selectTab(value)}
        variant="scrollable"
        scrollButtons="auto"
        aria-label="EPG sections"
        sx={{ mb: 2, borderBottom: `1px solid ${theme.appTokens.surface.border}` }}
      >
        {EPG_TABS.map((tab) => (
          <Tab key={tab} value={tab} label={TAB_LABELS[tab]} id={`epg-tab-${tab}`} aria-controls={`epg-tabpanel-${tab}`} />
        ))}
      </Tabs>

      <Box role="tabpanel" id={`epg-tabpanel-${activeTab}`} aria-labelledby={`epg-tab-${activeTab}`}>
        {activeTab === 'sources' ? (
          <ContentSection
            title="Sources"
            description="Each source is an XMLTV feed. Refreshes run every hour; refresh by hand after adding one."
            actions={
              <>
                <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={handleAddSourceClick}>
                  Add EPG Source
                </Button>
                <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRefreshAllClick} disabled={isRefreshingAll}>
                  Refresh All
                </Button>
              </>
            }
          >
            {isLoadingSources || isRefreshingAll ? <LinearProgress sx={{ mb: 2 }} /> : null}
            <EPGSourcesTable
              sources={epgSources}
              refreshingSourceId={refreshingSourceId}
              onRefreshSource={handleRefreshSourceClick}
              onEditSource={handleEditSourceClick}
              onDeleteSource={handleDeleteSourceClick}
            />
          </ContentSection>
        ) : null}

        {activeTab === 'channels' ? (
          <ContentSection
            title="Guide channels"
            description="Channels found in the sources. Select unlinked ones to create TV channels from them."
            actions={
              <Button
                variant="contained"
                color="primary"
                disabled={!isTVChannelCatalogReady || selectedEPGChannelIds.length === 0}
                onClick={handleBulkCreateTVChannels}
              >
                Create TV Channels ({selectedEPGChannelIds.length})
              </Button>
            }
          >
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} justifyContent="space-between" sx={{ mb: 2 }}>
              {sourceSelect}
              <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
                <Typography variant="body2" color="text.secondary">
                  {totalEPGChannels === 0
                    ? 'Showing 0-0 of 0 channels'
                    : `Showing ${(channelPage - 1) * channelPageSize + 1}-${Math.min(channelPage * channelPageSize, totalEPGChannels)} of ${totalEPGChannels} channels`}
                </Typography>
                <TablePagination
                  component="div"
                  count={totalEPGChannels}
                  page={Math.max(channelPage - 1, 0)}
                  onPageChange={handleChannelPageChange}
                  rowsPerPage={channelPageSize}
                  onRowsPerPageChange={handleChannelPageSizeChange}
                  rowsPerPageOptions={[25, 50, 100]}
                />
              </Stack>
            </Stack>

            {isLoadingChannels ? <LinearProgress sx={{ mb: 2 }} /> : null}

            {isLoadingTVChannelCatalog ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                Loading TV channels to work out which guide channels are already linked.
              </Alert>
            ) : null}

            {!isLoadingTVChannelCatalog && tvChannelCatalogError ? (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Unable to check which guide channels are linked right now. Try again after the TV channels load.
              </Alert>
            ) : null}

            <EPGChannelInventoryTable
              channels={epgChannels}
              sources={epgSources}
              selectedChannelIds={selectedEPGChannelIds}
              visibleUnmappedChannelIds={visibleUnmappedChannelIds}
              isTVChannelCatalogReady={isTVChannelCatalogReady}
              isChannelMapped={isChannelMapped}
              onSelectAll={handleSelectAllChannels}
              onSelectChannel={handleSelectChannel}
            />
          </ContentSection>
        ) : null}

        {activeTab === 'matching' ? (
          <ContentSection
            title="Matching"
            description="Find scraped streams that belong to unlinked guide channels and create the TV channels in one go."
            actions={
              <>
                <Button variant="outlined" color="primary" onClick={handleAnalyzeMatches} disabled={isAnalyzingMatches}>
                  Analyze Matches
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  disabled={!matchAnalysis || selectedMatchRowIds.length === 0}
                  onClick={handleCreateMatchedTVChannels}
                >
                  Create Matched TV Channels
                </Button>
              </>
            }
          >
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              {sourceSelect}
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel id="epg-match-strictness-label">Match Strictness</InputLabel>
                <Select labelId="epg-match-strictness-label" label="Match Strictness" value={matchStrictness} onChange={handleMatchStrictnessChange}>
                  <MenuItem value="loose">Loose</MenuItem>
                  <MenuItem value="balanced">Balanced</MenuItem>
                  <MenuItem value="strict">Strict</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {isAnalyzingMatches ? <LinearProgress sx={{ mb: 2 }} /> : null}

            {matchAnalysis ? (
              <EPGMatchAnalysisPanel
                analysis={matchAnalysis}
                matchFilter={matchFilter}
                onMatchFilterChange={setMatchFilter}
                filteredRows={filteredMatchRows}
                selectedRowIds={selectedMatchRowIds}
                onToggleRow={handleToggleMatchRow}
              />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Run an analysis to see which scraped streams match unlinked guide channels.
              </Typography>
            )}
          </ContentSection>
        ) : null}

        {activeTab === 'rules' ? (
          <ContentSection title="Matching rules">
            <RulesTab />
          </ContentSection>
        ) : null}

        {activeTab === 'export' ? (
          <ContentSection title="Export XML" description="Download a guide file with only your TV channels, for players that need their own EPG.">
            <EPGXmlOutputPanel onNotify={showSnackbar} />
          </ContentSection>
        ) : null}
      </Box>

      {/* EPG Source Dialog */}
      <EPGSourceDialog
        open={openSourceDialog}
        isEdit={isEditSource}
        formData={sourceFormData}
        onChange={handleSourceFormChange}
        onClose={handleCloseSourceDialog}
        onSubmit={handleSourceFormSubmit}
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={closeSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EPG;
