import React, { useState, useCallback } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  Pagination,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  SelectChangeEvent
} from '@mui/material';
import { CreateAcestreamChannelDTO } from '../services/channelService';
import { SearchResultItem } from '../services/searchService';
import { useQueryClient } from 'react-query';
import { useSearch, useAddAcestreamChannel } from '../hooks/useSearch';

const Search: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [selectedChannels, setSelectedChannels] = useState<SearchResultItem[]>([]);

  const queryClient = useQueryClient();

  // Use a separate state to track when to execute the search
  const [activeSearch, setActiveSearch] = useState<{ query: string; page: number; category: string } | null>(null);

  // Search query
  const { data: searchResults, isLoading: searchLoading, error: searchError } = useSearch(
    activeSearch?.query || '',
    activeSearch?.page || 1,
    pageSize,
    activeSearch?.category || '',
    { enabled: !!activeSearch }
  );

  // Add channel mutation
  const addChannelMutation = useAddAcestreamChannel();

  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) return;

    setActiveSearch({
      query: searchQuery,
      page: 1,
      category: category
    });
    setPage(1);
  }, [searchQuery, category]);

  const handlePageChange = useCallback((_: React.ChangeEvent<unknown>, newPage: number) => {
    if (!activeSearch) return;

    setActiveSearch({
      ...activeSearch,
      page: newPage
    });
    setPage(newPage);
  }, [activeSearch]);

  const handleCategoryChange = (event: SelectChangeEvent) => {
    setCategory(event.target.value as string);
  };

  const handleChannelSelection = (channel: SearchResultItem, checked: boolean) => {
    if (checked) {
      setSelectedChannels(prev => [...prev, channel]);
    } else {
      setSelectedChannels(prev => prev.filter(c => c.id !== channel.id));
    }
  };

  // Map SearchResultItem to CreateAcestreamChannelDTO
  const mapToCreateAcestreamChannelDTO = (item: SearchResultItem): CreateAcestreamChannelDTO => ({
    id: item.id, // Set the acestream channel id to the search result id
    name: item.name,
    group: item.categories && item.categories.length > 0 ? item.categories[0] : undefined,
    // Add more mappings if needed (logo, tvg_id, etc.)
  });

  const handleAddChannel = async (channel: SearchResultItem) => {
    try {
      await addChannelMutation.mutateAsync(mapToCreateAcestreamChannelDTO(channel));
      queryClient.invalidateQueries('channels');
    } catch (error) {
      console.error('Failed to add channel:', error);
    }
  };

  // Optionally, implement batch add by looping over selectedChannels
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

  const isChannelSelected = (channel: SearchResultItem) => {
    return selectedChannels.some(c => c.id === channel.id);
  };

  const allChannelsSelected = searchResults?.results && searchResults.results.length > 0 &&
    searchResults.results.every((channel: SearchResultItem) => isChannelSelected(channel));

  const hasSelection = selectedChannels.length > 0;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <>
        <Typography variant="h4" gutterBottom>
          Search Channels
        </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search Query"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter search terms..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={category}
                  label="Category"
                  onChange={handleCategoryChange}
                >
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
        </CardContent>
      </Card>

      {searchError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Search failed: {String(searchError)}
        </Alert>
      )}

      {searchResults && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Search Results ({searchResults.pagination?.total_results || 0} found)
              </Typography>
              {hasSelection && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleAddSelectedChannels}
                  disabled={addChannelMutation.isLoading}
                >
                  {addChannelMutation.isLoading ? <CircularProgress size={24} /> : `Add ${selectedChannels.length} Selected`}
                </Button>
              )}
            </Box>

            {(!searchResults.results || searchResults.results.length === 0) ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No channels found matching your search criteria.
                </Typography>
              </Box>
            ) : (
              <>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={allChannelsSelected}
                            onChange={(e) => handleSelectAll(e.target.checked)}
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
                        <TableRow key={channel.id}>
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={isChannelSelected(channel)}
                              onChange={(e) => handleChannelSelection(channel, e.target.checked)}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {channel.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {channel.categories?.map((cat, index) => (
                                <Chip key={index} label={cat} size="small" />
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
                            >
                              {addChannelMutation.isLoading ? <CircularProgress size={16} /> : 'Add'}
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {searchResults.pagination && searchResults.pagination.total_pages > 1 && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                    <Pagination
                      count={searchResults.pagination.total_pages}
                      page={page}
                      onChange={handlePageChange}
                      color="primary"
                    />
                  </Box>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
      </>
    </Container>
  );
};

export default Search;
