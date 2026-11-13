import { translateKnown } from '../i18n/text';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
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
  const tUi = useUiText();
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
    openSourceDialog, sourcePending, sourceError, sourceConfirmation,
    isEditSource,
    sourceFormData,
    selectSourceProvider,
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
    isApplyingMatches,
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
      <InputLabel id="epg-source-filter-label">{tUi("EPG Source")}</InputLabel>
      <Select labelId="epg-source-filter-label" label={tUi("EPG Source")} disabled={isApplyingMatches} value={selectedSourceId?.toString() ?? 'all'} onChange={handleSourceFilterChange}>
        <MenuItem value="all">{tUi("All sources")}</MenuItem>
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
        title={tUi("EPG")}
        subtitle={tUi("Programme guides for your channels: sources, guide channels, matching rules and the XML export.")}
        actions={
          <Button variant="outlined" startIcon={<FileDownloadIcon />} onClick={() => selectTab('export')}>
            {tUi("Export XML")}</Button>
        }
      />

      <StatusLine
        aria-label={tUi("EPG summary")}
        items={[
          { label: uiText("Sources"), value: tUi('{{total}} ({{enabled}} enabled)', { total: sourceCount, enabled: enabledSourceCount }), tone: failingSources > 0 ? 'error' : 'default' },
          { label: uiText("Guide channels"), value: guideChannelTotal === undefined ? '…' : String(guideChannelTotal) },
          { label: uiText("Linked to a TV channel"), value: tvChannels ? String(linkedCount) : '…' },
          { label: uiText("Last refresh"), value: formatRelativeTime(lastRefresh), tone: lastRefresh ? 'default' : 'warning' },
          ...(failingSources > 0 ? [{ label: uiText("Failing"), value: String(failingSources), tone: 'error' as const }] : []),
        ]}
      />

      <Tabs
        value={activeTab}
        onChange={(_event, value: EPGTab) => selectTab(value)}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
        aria-label={tUi("EPG sections")}
        sx={{
          mb: 2, borderBottom: `1px solid ${theme.appTokens.surface.border}`,
          // Keep every section legible on phones, including longer Spanish labels.
          '& .MuiTabs-flexContainer': { flexWrap: { xs: 'wrap', sm: 'nowrap' } },
          '& .MuiTabs-scroller': { overflow: { xs: 'visible !important' } },
          '& .MuiTabs-scrollButtons': { display: { xs: 'none', sm: 'inline-flex' } },
          '& .MuiTabs-indicator': { display: { xs: 'none', sm: 'block' } },
          '& .MuiTab-root': {
            minWidth: { xs: 'auto', sm: 90 }, px: { xs: 1.5, sm: 2 },
            '&.Mui-selected': { bgcolor: { xs: 'action.selected', sm: 'transparent' }, textDecoration: { xs: 'underline', sm: 'none' } },
          },
        }}
      >
        {EPG_TABS.map((tab) => (
          <Tab key={tab} value={tab} label={translateKnown(TAB_LABELS[tab])} id={`epg-tab-${tab}`} aria-controls={`epg-tabpanel-${tab}`} />
        ))}
      </Tabs>

      <Box role="tabpanel" id={`epg-tabpanel-${activeTab}`} aria-labelledby={`epg-tab-${activeTab}`}>
        {activeTab === 'sources' ? (
          <ContentSection
            title={tUi("Sources")}
            description={tUi("Each source is an XMLTV feed. Automatic refresh follows your schedule in Settings; refresh by hand after adding one.")}
            actions={
              <>
                <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={handleAddSourceClick}>
                  {tUi("Add EPG Source")}</Button>
                <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRefreshAllClick} disabled={isRefreshingAll}>
                  {tUi("Refresh All")}</Button>
              </>
            }
          >
            {isLoadingSources || isRefreshingAll ? <LinearProgress sx={{ mb: 2 }} /> : null}
            <Button component={RouterLink} to="/settings?tab=automation" sx={{ mb: 1 }}>{tUi("Edit refresh schedule")}</Button>
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
            title={tUi("Guide channels")}
            description={tUi("Channels found in the sources. Select unlinked ones to create TV channels from them.")}
            actions={
              <Button
                variant="contained"
                color="primary"
                disabled={!isTVChannelCatalogReady || selectedEPGChannelIds.length === 0}
                onClick={handleBulkCreateTVChannels}
              >
                {tUi("Create TV Channels (")}{selectedEPGChannelIds.length})
              </Button>
            }
          >
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }} justifyContent="space-between" sx={{ mb: 2 }}>
              {sourceSelect}
              <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
                <Typography variant="body2" color="text.secondary">
                  {isLoadingChannels && !epgChannelPage ? tUi("Loading channels…") : totalEPGChannels === 0
                    ? tUi("Showing 0-0 of 0 channels")
                    : tUi("Showing {{value0}}-{{value1}} of {{value2}} channels", { value0: (channelPage - 1) * channelPageSize + 1, value1: Math.min(channelPage * channelPageSize, totalEPGChannels), value2: totalEPGChannels })}
                </Typography>
                <TablePagination
                  component="div"
                  count={isLoadingChannels && !epgChannelPage ? -1 : totalEPGChannels}
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
                {tUi("Loading TV channels to work out which guide channels are already linked.")}</Alert>
            ) : null}

            {!isLoadingTVChannelCatalog && tvChannelCatalogError ? (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {tUi("Unable to check which guide channels are linked right now. Try again after the TV channels load.")}</Alert>
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
            title={tUi("Matching")}
            description={tUi("Preview stream assignments, select the guide channels you reviewed, then apply. Existing channel settings are preserved.")}
            actions={
              <>
                <Button variant="outlined" color="primary" onClick={handleAnalyzeMatches} disabled={isAnalyzingMatches || isApplyingMatches}>
                  {tUi("Analyze Matches")}</Button>
                <Button
                  variant="contained"
                  color="primary"
                  disabled={isAnalyzingMatches || isApplyingMatches || !matchAnalysis || selectedMatchRowIds.length === 0}
                  onClick={handleCreateMatchedTVChannels}
                >
                  {isApplyingMatches ? tUi("Applying…") : tUi("Apply reviewed matches")}
                </Button>
              </>
            }
          >
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              {sourceSelect}
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel id="epg-match-strictness-label">{tUi("Match Strictness")}</InputLabel>
                <Select labelId="epg-match-strictness-label" label={tUi("Match Strictness")} value={matchStrictness} disabled={isApplyingMatches} onChange={handleMatchStrictnessChange}>
                  <MenuItem value="loose">{tUi("Loose")}</MenuItem>
                  <MenuItem value="balanced">{tUi("Balanced")}</MenuItem>
                  <MenuItem value="strict">{tUi("Strict")}</MenuItem>
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
                {tUi("Run an analysis to see which scraped streams match unlinked guide channels.")}</Typography>
            )}
          </ContentSection>
        ) : null}

        {activeTab === 'rules' ? (
          <ContentSection title={tUi("Matching rules")}>
            <RulesTab />
          </ContentSection>
        ) : null}

        {activeTab === 'export' ? (
          <ContentSection title={tUi("Export XML")} description={tUi("Download a guide file with only your TV channels, for players that need their own EPG.")}>
            <EPGXmlOutputPanel onNotify={showSnackbar} />
          </ContentSection>
        ) : null}
      </Box>

      {sourceConfirmation}
      {/* EPG Source Dialog */}
      <EPGSourceDialog
        open={openSourceDialog} pending={sourcePending} error={sourceError}
        isEdit={isEditSource}
        formData={sourceFormData}
        onSelectProvider={selectSourceProvider}
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
