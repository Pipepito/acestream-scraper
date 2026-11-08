import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useCallback, useRef, useState } from 'react';
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
import { getErrorMessage } from '../utils/errorUtils';
import { statusLabel } from '../i18n/status';
import { searchService, SearchResultItem } from '../services/searchService';
import { formatBitrate } from '../utils/format';
import SavedSearchDialog from '../components/imports/SavedSearchDialog';
import { Link as RouterLink } from 'react-router-dom';
import AddAndLinkDialog from '../components/search/AddAndLinkDialog';
import SearchBroadcastStatus from '../components/SearchBroadcastStatus';

const Search: React.FC = () => {
  const tUi = useUiText();
  const [linkStream, setLinkStream] = useState<SearchResultItem | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);
  const [importMessage, setImportMessage] = useState<(() => string) | null>(null);
  const importing = useRef(false);
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
    onError: (error) => showSnackbar(() => tUi('Could not play: {{details}}', { details: getErrorMessage(error) }), 'error'),
  });
  const searchErrorMessage = getErrorMessage(searchError);

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
    if (importing.current) return;
    importing.current = true;
    try {
      const outcome = await addChannelMutation.mutateAsync(channel);
      setImportRuleId(outcome.rule_ids?.[0]);
      if (outcome.outcome !== 'added' && outcome.outcome !== 'existing') {
        setImportMessage(() => () => tUi('{{name}}: {{outcome}}. Rules: {{rules}}.', { name: channel.name, outcome: statusLabel(outcome.outcome), rules: outcome.rule_ids?.join(', ') || '—' }));
        return;
      }
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
      setSelectedChannels((prev) => prev.filter((item) => item.id !== channel.id));
      markAdded([channel.id]);
      showSnackbar(() => (tUi("{{name}}: {{outcome}}.", { name: channel.name, outcome: statusLabel(outcome.outcome) })), 'success');
    } catch (error) {
      showSnackbar(() => (tUi("Could not add {{name}}: {{details}}", { name: channel.name, details: getErrorMessage(error) })), 'error');
    } finally { importing.current = false; }
  };

  const handleAddSelectedChannels = async () => {
    if (selectedChannels.length === 0 || importing.current) return;
    importing.current = true;

    setBulkBusy(true);
    try {
      const result = await searchService.importResults(selectedChannels);
      setImportRuleId(result.items.find(item => item.rule_ids?.length)?.rule_ids?.[0]);
      const successful = result.items.filter(item => item.outcome === 'added' || item.outcome === 'existing').map(item => item.infohash);
      markAdded(successful);
      setSelectedChannels(prev => prev.filter(item => !successful.includes(item.id)));
      if (successful.length) void queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
      setImportMessage(() => () => tUi("{{added}} added, {{existing}} existing, {{excluded}} excluded, {{unresolved}} unresolved, {{deferred}} deferred.", { added: result.added ?? 0, existing: result.existing ?? 0, excluded: result.excluded ?? 0, unresolved: result.unresolved ?? 0, deferred: result.deferred ?? 0 }));
    } catch (error) {
      showSnackbar(() => (getErrorMessage(error)), 'error');
    } finally {
      importing.current = false; setBulkBusy(false);
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
      <PageHeader title={tUi("Search")} subtitle={tUi("Find streams in the AceStream catalogue and add them to your channels.")} />

      <ContentSection title={tUi("Search")}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={7}>
            <TextField
              fullWidth
              label={tUi("Search Query")}
              helperText={tUi("Leave blank to browse all published channels.")}
              placeholder={tUi("Enter search terms...")}
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
              <InputLabel id="search-category-label">{tUi("Category")}</InputLabel>
              <Select labelId="search-category-label" value={category} label={tUi("Category")} onChange={handleCategoryChange}>
                <MenuItem value="">{tUi("All Categories")}</MenuItem>
                <MenuItem value="sports">{tUi("Sports")}</MenuItem>
                <MenuItem value="movies">{tUi("Movies")}</MenuItem>
                <MenuItem value="tv">{tUi("TV")}</MenuItem>
                <MenuItem value="news">{tUi("News")}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button fullWidth variant="contained" size="large" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? <CircularProgress size={24} color="inherit" /> : tUi("Search")}
            </Button>
          </Grid>
        </Grid>
      </ContentSection>

      {activeSearch?.query ? <Button sx={{ mb: 2 }} onClick={() => setSaveOpen(true)}>{tUi("Save search")}</Button> : null}
      {saveOpen && activeSearch ? <SavedSearchDialog initial={{ name: activeSearch.query.slice(0, 100), query: activeSearch.query, category: activeSearch.category, refresh_enabled: false }} onClose={() => setSaveOpen(false)} /> : null}
      {importMessage ? <Alert severity="info" sx={{ mb: 2 }}>{importMessage()}<Button component={RouterLink} to={`/scraper?tab=exclusions${importRuleId ? `#rule-${importRuleId}` : ''}`}>{importRuleId ? tUi("Exclusion rule #{{value0}}", { value0: importRuleId }) : tUi("Import exclusions")}</Button></Alert> : null}
      {searchError && activeSearch ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          {tUi("Search for \"")}{activeSearch.query}{tUi("\" failed.")}{' '}{searchErrorMessage}
        </Alert>
      ) : null}

      {searchResults && activeSearch ? (
        <ContentSection
          title={tUi("Results")}
          actions={
            hasSelection ? (
              <Button variant="contained" onClick={handleAddSelectedChannels} disabled={addChannelMutation.isPending || bulkBusy} aria-label={tUi("Add {{value0}} selected channels", { value0: selectedChannels.length })}>
                {addChannelMutation.isPending ? <CircularProgress size={24} /> : tUi("Add {{value0}} selected channels", { value0: selectedChannels.length })}
              </Button>
            ) : null
          }
        >
          <StatusLine
            aria-label={tUi("Search summary")}
            items={[
              { label: uiText("Results"), value: `${totalResults} ${activeSearch.query ? `for ‘${activeSearch.query}’` : 'in all channels'}${activeSearch.category ? ` in ${activeSearch.category}` : ''}` },
              { label: uiText("Selected"), value: String(selectedChannels.length) },
              ...(addedIds.size > 0 ? [{ label: uiText("Added this session"), value: String(addedIds.size), tone: 'success' as const }] : []),
            ]}
          />
          {results.length === 0 ? (
            <Box sx={{ py: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                {tUi("No channels found matching your search criteria.")}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {tUi("Try a broader query or adjust the category, then search again.")}</Typography>
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
                      <TableCell>{tUi("Name")}</TableCell>
                      <TableCell>{tUi("Categories")}</TableCell>
                      <TableCell>{tUi("Bitrate")}</TableCell>
                      <TableCell>{tUi("Availability")}</TableCell>
                      <TableCell>{tUi("Action")}</TableCell>
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
                            <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
                              <Button
                                size="small"
                                startIcon={<PlayArrowRounded />}
                                onClick={() => playMutation.mutate(channel)}
                                disabled={playMutation.isPending}
                                aria-label={tUi("play {{value0}}", { value0: channel.name })}
                              >
                                {playMutation.isPending && playMutation.variables?.id === channel.id ? tUi("Resolving…") : tUi("Play")}
                              </Button>
                              <Button size="small" variant="outlined" onClick={() => setLinkStream(channel)} disabled={addChannelMutation.isPending || bulkBusy} aria-label={tUi("Add and Link {{value0}}", { value0: channel.name })}>{tUi("Add and Link")}</Button>
                              {added ? (
                                <Chip size="small" color="success" icon={<CheckIcon />} label={tUi("Added")} aria-label={tUi("Added {{value0}}", { value0: channel.name })} />
                              ) : (
                                <Button size="small" variant="outlined" onClick={() => handleAddChannel(channel)} disabled={addChannelMutation.isPending || bulkBusy} aria-label={tUi("Add {{value0}}", { value0: channel.name })}>
                                  {tUi("Add")}</Button>
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

      {linkStream ? <AddAndLinkDialog stream={linkStream} onClose={() => setLinkStream(null)} onAdded={() => { markAdded([linkStream.id]); showSnackbar(() => (tUi("{{name}} added and linked.", { name: linkStream.name })), 'success'); setLinkStream(null); }} /> : null}
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
