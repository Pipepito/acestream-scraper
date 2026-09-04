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
import { useQueryClient } from '@tanstack/react-query';

import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import PlayOnMenu from '../components/player/PlayOnMenu';
import StatusLine from '../components/StatusLine';
import { useAddAcestreamChannel, useSearch } from '../hooks/useSearch';
import { useSnackbar } from '../hooks/useSnackbar';
import { normalizeApiError } from '../services/apiErrors';
import { CreateAcestreamChannelDTO } from '../services/channelService';
import { SearchResultItem } from '../services/searchService';
import { formatBitrate } from '../utils/format';

const Search: React.FC = () => {
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

  const addChannelMutation = useAddAcestreamChannel();
  const searchErrorMessage = searchError instanceof Error ? searchError.message : String(searchError);

  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) return;

    setActiveSearch({
      query: searchQuery,
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

  const mapToCreateAcestreamChannelDTO = (item: SearchResultItem): CreateAcestreamChannelDTO => ({
    id: item.id,
    name: item.name,
    group: item.categories && item.categories.length > 0 ? item.categories[0] : undefined,
  });

  const markAdded = (ids: string[]) => {
    setAddedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      return next;
    });
  };

  const handleAddChannel = async (channel: SearchResultItem) => {
    try {
      await addChannelMutation.mutateAsync(mapToCreateAcestreamChannelDTO(channel));
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
      setSelectedChannels((prev) => prev.filter((item) => item.id !== channel.id));
      markAdded([channel.id]);
      showSnackbar(`Added ${channel.name} to your channels.`, 'success');
    } catch (error) {
      showSnackbar(`Could not add ${channel.name}: ${normalizeApiError(error).message}`, 'error');
    }
  };

  const handleAddSelectedChannels = async () => {
    if (selectedChannels.length === 0) return;

    const successfulChannelIds: string[] = [];
    let failure: unknown = null;

    try {
      for (const channel of selectedChannels) {
        await addChannelMutation.mutateAsync(mapToCreateAcestreamChannelDTO(channel));
        successfulChannelIds.push(channel.id);
      }
    } catch (error) {
      failure = error;
    } finally {
      if (successfulChannelIds.length > 0) {
        queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
        setSelectedChannels((prev) => prev.filter((channel) => !successfulChannelIds.includes(channel.id)));
        markAdded(successfulChannelIds);
      }
      if (failure) {
        showSnackbar(`Added ${successfulChannelIds.length}; the next one failed: ${normalizeApiError(failure).message}`, 'error');
      } else {
        showSnackbar(`Added ${successfulChannelIds.length} channel${successfulChannelIds.length === 1 ? '' : 's'}.`, 'success');
      }
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
              <InputLabel>Category</InputLabel>
              <Select value={category} label="Category" onChange={handleCategoryChange}>
                <MenuItem value="">All Categories</MenuItem>
                <MenuItem value="sports">Sports</MenuItem>
                <MenuItem value="movies">Movies</MenuItem>
                <MenuItem value="tv">TV</MenuItem>
                <MenuItem value="news">News</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button fullWidth variant="contained" size="large" onClick={handleSearch} disabled={!searchQuery.trim() || searchLoading}>
              {searchLoading ? <CircularProgress size={24} color="inherit" /> : 'Search'}
            </Button>
          </Grid>
        </Grid>
      </ContentSection>

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
              <Button variant="contained" onClick={handleAddSelectedChannels} disabled={addChannelMutation.isPending} aria-label={`Add ${selectedChannels.length} selected channels`}>
                {addChannelMutation.isPending ? <CircularProgress size={24} /> : `Add ${selectedChannels.length} selected channels`}
              </Button>
            ) : null
          }
        >
          <StatusLine
            aria-label="Search summary"
            items={[
              { label: 'Results', value: `${totalResults} for ‘${activeSearch.query}’${activeSearch.category ? ` in ${activeSearch.category}` : ''}` },
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
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Button
                                size="small"
                                startIcon={<PlayArrowRounded />}
                                onClick={() => setPlayerTarget({ contentId: channel.id, title: channel.name })}
                                aria-label={`play ${channel.name}`}
                              >
                                Play
                              </Button>
                              {added ? (
                                <Chip size="small" color="success" icon={<CheckIcon />} label="Added" aria-label={`Added ${channel.name}`} />
                              ) : (
                                <Button size="small" variant="outlined" onClick={() => handleAddChannel(channel)} disabled={addChannelMutation.isPending} aria-label={`Add ${channel.name}`}>
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

      <StreamPlayerDialog
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
        extraActions={playerTarget ? <PlayOnMenu contentId={playerTarget.contentId} title={playerTarget.title} /> : undefined}
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
