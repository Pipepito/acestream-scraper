import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TablePagination,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useEPGSources, useEPGChannels } from '../hooks/useEPG';
import { useTVChannelCatalog } from '../hooks/useTVChannels';
import { useSnackbar } from '../hooks/useSnackbar';
import { useEPGSourceManagement } from '../hooks/useEPGSourceManagement';
import { useEPGMatchAnalysis } from '../hooks/useEPGMatchAnalysis';
import { useEPGChannelSelection } from '../hooks/useEPGChannelSelection';
import { EPGMatchStrictness } from '../services/tvChannelService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import EPGPageHero from '../components/EPGPageHero';
import EPGSourcesTable from '../components/EPGSourcesTable';
import EPGSourceDialog from '../components/EPGSourceDialog';
import EPGMatchAnalysisPanel from '../components/EPGMatchAnalysisPanel';
import EPGChannelInventoryTable from '../components/EPGChannelInventoryTable';
import EPGXmlOutputPanel from '../components/EPGXmlOutputPanel';

const EPG: React.FC = () => {
  const navigate = useNavigate();

  // Snackbar state
  const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();

  // React Query hooks
  const { data: epgSources, isLoading: isLoadingSources } = useEPGSources();
  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined);
  const [channelPage, setChannelPage] = useState(1);
  const [channelPageSize, setChannelPageSize] = useState(50);

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

  const unmappedVisibleCount = visibleUnmappedChannelIds.length;

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

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title="EPG Management"
        subtitle="Manage source ingestion, map channels, and generate XML output."
      />

      <EPGPageHero
        sourceCount={sourceCount}
        enabledSourceCount={enabledSourceCount}
        unmappedVisibleCount={unmappedVisibleCount}
      />

      <ContentSection
        title="Source Operations"
          description="Track source health, add feeds, and refresh ingestion without leaving the page."
          actions={
            <>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={handleAddSourceClick}
              >
                Add EPG Source
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRefreshAllClick}
                disabled={isRefreshingAll}
              >
                Refresh All
              </Button>
            </>
          }
        >
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip label={`${(epgSources || []).length} sources`} size="small" />
            <Chip
              label={`${(epgSources || []).filter((source) => source.enabled).length} enabled`}
              color="success"
              size="small"
            />
          </Box>

          {isLoadingSources || isRefreshingAll ? (
            <LinearProgress sx={{ mb: 2 }} />
          ) : null}

          <EPGSourcesTable
            sources={epgSources}
            refreshingSourceId={refreshingSourceId}
            onRefreshSource={handleRefreshSourceClick}
            onEditSource={handleEditSourceClick}
            onDeleteSource={handleDeleteSourceClick}
          />
        </ContentSection>

        <ContentSection
          title="Channel Matching"
          description="Analyze unmatched EPG channels, refine source scope, and create TV-channel entries with explicit selection controls."
          actions={
            <>
              <Button
                variant="outlined"
                color="primary"
                onClick={handleAnalyzeMatches}
                disabled={isAnalyzingMatches}
              >
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
              <Button
                variant="contained"
                color="primary"
                disabled={!isTVChannelCatalogReady || selectedEPGChannelIds.length === 0}
                onClick={handleBulkCreateTVChannels}
              >
                Create TV Channels ({selectedEPGChannelIds.length})
              </Button>
            </>
          }
        >
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 240 }}>
              <InputLabel id="epg-source-filter-label">EPG Source</InputLabel>
              <Select
                labelId="epg-source-filter-label"
                label="EPG Source"
                value={selectedSourceId?.toString() ?? 'all'}
                onChange={handleSourceFilterChange}
              >
                <MenuItem value="all">All sources</MenuItem>
                {(epgSources || []).map((source) => (
                  <MenuItem key={source.id} value={source.id.toString()}>
                    {source.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel id="epg-match-strictness-label">Match Strictness</InputLabel>
              <Select
                labelId="epg-match-strictness-label"
                label="Match Strictness"
                value={matchStrictness}
                onChange={handleMatchStrictnessChange}
              >
                <MenuItem value="loose">Loose</MenuItem>
                <MenuItem value="balanced">Balanced</MenuItem>
                <MenuItem value="strict">Strict</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {isAnalyzingMatches ? (
            <LinearProgress sx={{ mb: 2 }} />
          ) : null}

          {matchAnalysis ? (
            <EPGMatchAnalysisPanel
              analysis={matchAnalysis}
              matchFilter={matchFilter}
              onMatchFilterChange={setMatchFilter}
              filteredRows={filteredMatchRows}
              selectedRowIds={selectedMatchRowIds}
              onToggleRow={handleToggleMatchRow}
            />
          ) : null}
        </ContentSection>

        <ContentSection
          title="Channel Inventory"
          description="Review imported channels, filter by source, and open detailed schedules without losing bulk actions."
        >
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
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
          </Box>

          {isLoadingChannels ? (
            <LinearProgress sx={{ mb: 2 }} />
          ) : null}

          {isLoadingTVChannelCatalog ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Loading TV channel catalog before channel-creation selections become available.
            </Alert>
          ) : null}

          {!isLoadingTVChannelCatalog && tvChannelCatalogError ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Unable to verify existing TV channel mappings right now. Retry after the catalog loads.
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
            onViewPrograms={(id) => navigate(`/epg/channels/${id}`)}
          />
        </ContentSection>

        <ContentSection
          title="XML Output"
          description="Generate a downloadable XML export with a clear date window and optional channel filtering."
        >
          <EPGXmlOutputPanel onNotify={showSnackbar} />
        </ContentSection>

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
