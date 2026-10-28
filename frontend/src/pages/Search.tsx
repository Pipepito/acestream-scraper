import React, { useCallback, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  SelectChangeEvent,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import StatusLine from '../components/StatusLine';
import { useAddSearchResult, useSearch } from '../hooks/useSearch';
import { useSnackbar } from '../hooks/useSnackbar';
import { normalizeApiError } from '../services/apiErrors';
import { searchService, SearchResultItem } from '../services/searchService';
import { formatBitrate } from '../utils/format';
import SavedSearchDialog from '../components/imports/SavedSearchDialog';
import { Link as RouterLink } from 'react-router-dom';
import SearchBroadcastStatus from '../components/SearchBroadcastStatus';

const Search: React.FC = () => {
  const [saveOpen, setSaveOpen] = useState(false);
  const [importMessage, setImportMessage] = useState('');
  const [importRuleId, setImportRuleId] = useState<number>();
  const [bulkBusy, setBulkBusy] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [selectedChannels, setSelectedChannels] = useState<SearchResultItem[]>([]);
  const [addedIds, setAddedIds] = useState<Set<string>>(() => new Set());
  const [activeSearch, setActiveSearch] = useState<{ query: string; page: number; category: string } | null>(null);
  const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string } | null>(null);
  const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();

  const queryClient = useQueryClient();

  const { data: searchResults, isLoading: searchLoading, error: searchError } = useSearch(
    activeSearch?.query || '',
    activeSearch?.page || 1,
    pageSize,
    activeSearch?.category || '',
    { enabled: !!activeSearch }
  );

  const addChannelMutation = useAddSearchResult();
  const playMutation = useMutation({
    mutationFn: (channel: SearchResultItem) => searchService.resolveContentId(channel.id),
    onSuccess: (contentId, channel) => setPlayerTarget({ contentId, title: channel.name }),
    onError: (error) => showSnackbar(`Could not play: ${normalizeApiError(error).message}`, 'error'),
  });
  const searchErrorMessage = searchError instanceof Error ? searchError.message : String(searchError);

  const handleSearch = useCallback(() => {

    setActiveSearch({
      query: searchQuery.trim(),
      page: 1,
      category,
    });
    setPage(1);
    setSelectedChannels([]);
  }, [category, searchQuery]);

  const handlePageChange = useCallback((_: React.ChangeEvent<unknown>, newPage: number) => {
    if (!activeSearch) return;

    setActiveSearch({
      ...activeSearch,
      page: newPage,
    });
    setPage(newPage);
    setSelectedChannels([]);
  }, [activeSearch]);

  const handleCategoryChange = (event: SelectChangeEvent) => {
    setCategory(event.target.value as string);
  };

  const handleChannelSelection = (channel: SearchResultItem, checked: boolean) => {
    if (checked) {
      setSelectedChannels((prev) => (prev.some((item) => item.id === channel.id) ? prev : [...prev, channel]));
    } else {
      setSelectedChannels((prev) => prev.filter((item) => item.id !== channel.id));
    }
  };

  const markAdded = (ids: string[]) => {
    setAddedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      return next;
    });
  };

  const handleAddChannel = async (channel: SearchResultItem) => {
    try {
      const outcome = await addChannelMutation.mutateAsync(channel);
      setImportRuleId(outcome.rule_ids?.[0]);
      if (outcome.outcome !== 'added' && outcome.outcome !== 'existing') {
        setImportMessage(`${channel.name}: ${outcome.outcome}${outcome.rule_ids?.length ? ` (rule ${outcome.rule_ids.join(', ')})` : ''}.`);
        return;
      }
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
      setSelectedChannels((prev) => prev.filter((item) => item.id !== channel.id));
      markAdded([channel.id]);
      showSnackbar(`${channel.name}: ${outcome.outcome}.`, 'success');
    } catch (error) {
      showSnackbar(`Could not add ${channel.name}: ${normalizeApiError(error).message}`, 'error');
    }
  };

  const handleAddSelectedChannels = async () => {
    if (selectedChannels.length === 0) return;

    setBulkBusy(true);
    try {
      const result = await searchService.importResults(selectedChannels);
      setImportRuleId(result.items.find(item => item.rule_ids?.length)?.rule_ids?.[0]);
      const successful = result.items.filter(item => item.outcome === 'added' || item.outcome === 'existing').map(item => item.infohash);
      markAdded(successful);
      setSelectedChannels(prev => prev.filter(item => !successful.includes(item.id)));
      if (successful.length) void queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
      setImportMessage(`${result.added} added, ${result.existing} existing, ${result.excluded} excluded, ${result.unresolved} unresolved, ${result.deferred} deferred.`);
    } catch (error) {
      showSnackbar(normalizeApiError(error).message, 'error');
    } finally {
      setBulkBusy(false);
    }
  };

  const results = searchResults?.results ?? [];
  const selectableResults = results.filter((channel) => !addedIds.has(channel.id));

  const handleSelectAll = (checked: boolean) => {
    setSelectedChannels(checked ? selectableResults : []);
  };

  const isChannelSelected = (channel: SearchResultItem) => selectedChannels.some((item) => item.id === channel.id);
  const hasSelection = selectedChannels.length > 0;
  const totalResults = searchResults?.pagination?.total_results ?? 0;

  return (
    <Box>
      <PageHeader title="Search" subtitle="Find streams in the AceStream catalogue and add them to your channels." />

      <ContentSection title="Search">
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={7}>
            <TextField
              fullWidth
              label="Search Query"
              helperText="Leave blank to browse all published channels."
              placeholder="Enter search terms..."
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSearch();
                }
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel id="search-category-label">Category</InputLabel>
              <Select labelId="search-category-label" value={category} label="Category" onChange={handleCategoryChange}>
                <MenuItem value="">All Categories</MenuItem>
                <MenuItem value="sports">Sports</MenuItem>
                <MenuItem value="movies">Movies</MenuItem>
                <MenuItem value="tv">TV</MenuItem>
                <MenuItem value="news">News</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button fullWidth variant="contained" size="large" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? <CircularProgress size={24} color="inherit" /> : 'Search'}
            </Button>
          </Grid>
        </Grid>
      </ContentSection>

      {activeSearch?.query ? <Button sx={{ mb: 2 }} onClick={() => setSaveOpen(true)}>Save search</Button> : null}
      {saveOpen && activeSearch ? <SavedSearchDialog initial={{ name: activeSearch.query.slice(0, 100), query: activeSearch.query, category: activeSearch.category, refresh_enabled: false }} onClose={() => setSaveOpen(false)} /> : null}
      {importMessage ? <Alert severity="info" sx={{ mb: 2 }}>{importMessage}<Button component={RouterLink} to={`/scraper?tab=exclusions${importRuleId ? `#rule-${importRuleId}` : ''}`}>{importRuleId ? `Exclusion rule #${importRuleId}` : 'Import exclusions'}</Button></Alert> : null}
      {searchError && activeSearch ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          Search for &quot;{activeSearch.query}&quot; failed. {searchErrorMessage}
        </Alert>
      ) : null}

      {searchResults && activeSearch ? (
        <ContentSection
          title="Results"
          actions={
            hasSelection ? (
              <Button variant="contained" onClick={handleAddSelectedChannels} disabled={addChannelMutation.isPending || bulkBusy} aria-label={`Add ${selectedChannels.length} selected channels`}>
                {addChannelMutation.isPending ? <CircularProgress size={24} /> : `Add ${selectedChannels.length} selected channels`}
              </Button>
            ) : null
          }
        >
          <StatusLine
            aria-label="Search summary"
            items={[
              { label: 'Results', value: `${totalResults} ${activeSearch.query ? `for ‘${activeSearch.query}’` : 'in all channels'}${activeSearch.category ? ` in ${activeSearch.category}` : ''}` },
              { label: 'Selected', value: String(selectedChannels.length) },
              ...(addedIds.size > 0 ? [{ label: 'Added this session', value: String(addedIds.size), tone: 'success' as const }] : []),
            ]}
          />
          {results.length === 0 ? (
            <Box sx={{ py: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No channels found matching your search criteria.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try a broader query or adjust the category, then search again.
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectableResults.length > 0 && selectedChannels.length === selectableResults.length}
                          indeterminate={hasSelection && selectedChannels.length < selectableResults.length}
                          onChange={(event) => handleSelectAll(event.target.checked)}
                          inputProps={{ 'aria-label': 'select all search results' }}
                          disabled={selectableResults.length === 0}
                        />
                      </TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Categories</TableCell>
                      <TableCell>Bitrate</TableCell>
                      <TableCell>Availability</TableCell>
                      <TableCell>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {results.map((channel) => {
                      const added = addedIds.has(channel.id);
                      return (
                        <TableRow key={channel.id} selected={isChannelSelected(channel)}>
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={isChannelSelected(channel)}
                              disabled={added}
                              onChange={(event) => handleChannelSelection(channel, event.target.checked)}
                              inputProps={{ 'aria-label': `select search result ${channel.name}` }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {channel.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {(channel.categories ?? []).map((item) => (
                              <Chip key={item} label={item} size="small" sx={{ mr: 0.5 }} />
                            ))}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                              {formatBitrate(channel.bitrate)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <SearchBroadcastStatus channel={channel} />
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Button
                                size="small"
                                startIcon={<PlayArrowRounded />}
                                onClick={() => playMutation.mutate(channel)}
                                disabled={playMutation.isPending}
                                aria-label={`play ${channel.name}`}
                              >
                                {playMutation.isPending && playMutation.variables?.id === channel.id ? 'Resolving…' : 'Play'}
                              </Button>
                              {added ? (
                                <Chip size="small" color="success" icon={<CheckIcon />} label="Added" aria-label={`Added ${channel.name}`} />
                              ) : (
                                <Button size="small" variant="outlined" onClick={() => handleAddChannel(channel)} disabled={addChannelMutation.isPending || bulkBusy} aria-label={`Add ${channel.name}`}>
                                  Add
                                </Button>
                              )}
                            </Stack>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
              {(searchResults.pagination?.total_pages ?? 0) > 1 ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination count={searchResults.pagination?.total_pages ?? 1} page={page} onChange={handlePageChange} color="primary" />
                </Box>
              ) : null}
            </>
          )}
        </ContentSection>
      ) : null}

      <ChannelPlayerDialog
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
      />

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={closeSnackbar} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={closeSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Search;
