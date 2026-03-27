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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useQueryClient } from 'react-query';

import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import { useAddAcestreamChannel, useSearch } from '../hooks/useSearch';
import { CreateAcestreamChannelDTO } from '../services/channelService';
import { SearchResultItem } from '../services/searchService';

const Search: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [selectedChannels, setSelectedChannels] = useState<SearchResultItem[]>([]);
  const [activeSearch, setActiveSearch] = useState<{ query: string; page: number; category: string } | null>(null);

  const queryClient = useQueryClient();

  const { data: searchResults, isLoading: searchLoading, error: searchError } = useSearch(
    activeSearch?.query || '',
    activeSearch?.page || 1,
    pageSize,
    activeSearch?.category || '',
    { enabled: !!activeSearch }
  );

  const addChannelMutation = useAddAcestreamChannel();

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

  const handleAddChannel = async (channel: SearchResultItem) => {
    try {
      await addChannelMutation.mutateAsync(mapToCreateAcestreamChannelDTO(channel));
      queryClient.invalidateQueries('channels');
    } catch (error) {
      console.error('Failed to add channel:', error);
    }
  };

  const handleAddSelectedChannels = async () => {
    if (selectedChannels.length === 0) return;

    try {
      for (const channel of selectedChannels) {
        await addChannelMutation.mutateAsync(mapToCreateAcestreamChannelDTO(channel));
      }
      queryClient.invalidateQueries('channels');
      setSelectedChannels([]);
    } catch (error) {
      console.error('Failed to add channels:', error);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked && searchResults?.results) {
      setSelectedChannels(searchResults.results);
    } else {
      setSelectedChannels([]);
    }
  };

  const isChannelSelected = (channel: SearchResultItem) => selectedChannels.some((item) => item.id === channel.id);

  const allChannelsSelected = Boolean(
    searchResults?.results &&
      searchResults.results.length > 0 &&
      searchResults.results.every((channel: SearchResultItem) => isChannelSelected(channel))
  );

  const hasSelection = selectedChannels.length > 0;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title="Search Channels"
        subtitle="Search the upstream catalog, compare channel quality, and add the right Acestream entries with explicit selection controls."
      />

      <ContentSection
        title="Search Filters"
        description="Use a plain-language query first, then narrow the category before you run the search."
      >
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Query"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Enter search terms..."
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
          <Grid item xs={12} md={3}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={!searchQuery.trim() || searchLoading}
              sx={{ height: '56px' }}
            >
              {searchLoading ? <CircularProgress size={24} /> : 'Search'}
            </Button>
          </Grid>
        </Grid>
      </ContentSection>

      {searchError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          Search failed: {String(searchError)}
        </Alert>
      ) : null}

      {searchResults ? (
        <ContentSection
          title="Search Results"
          description="Review the returned channels, compare categories and bitrate, then add a single result or a selected batch."
          actions={
            hasSelection ? (
              <Button
                variant="contained"
                color="primary"
                onClick={handleAddSelectedChannels}
                disabled={addChannelMutation.isLoading}
                aria-label={`Add ${selectedChannels.length} selected channels`}
              >
                {addChannelMutation.isLoading ? <CircularProgress size={24} /> : `Add ${selectedChannels.length} selected channels`}
              </Button>
            ) : null
          }
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {searchResults.pagination?.total_results || 0} results found
            </Typography>
          </Box>

          {!searchResults.results || searchResults.results.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No channels found matching your search criteria.
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={allChannelsSelected}
                          onChange={(event) => handleSelectAll(event.target.checked)}
                          inputProps={{ 'aria-label': 'select all search results' }}
                        />
                      </TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Categories</TableCell>
                      <TableCell>Bitrate</TableCell>
                      <TableCell>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.results.map((channel: SearchResultItem) => (
                      <TableRow key={channel.id} selected={isChannelSelected(channel)}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={isChannelSelected(channel)}
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
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {channel.categories?.map((item, index) => (
                              <Chip key={index} label={item} size="small" />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {channel.bitrate ? `${channel.bitrate} kbps` : 'Unknown'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => handleAddChannel(channel)}
                            disabled={addChannelMutation.isLoading}
                            aria-label={`Add ${channel.name}`}
                          >
                            {addChannelMutation.isLoading ? <CircularProgress size={16} /> : 'Add'}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {searchResults.pagination && searchResults.pagination.total_pages > 1 ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination count={searchResults.pagination.total_pages} page={page} onChange={handlePageChange} color="primary" />
                </Box>
              ) : null}
            </>
          )}
        </ContentSection>
      ) : null}
    </Box>
  );
};

export default Search;
