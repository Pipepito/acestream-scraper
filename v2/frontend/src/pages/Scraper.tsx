import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  TextField, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';
import { useURLs, useCreateURL, useUpdateURL, useDeleteURL, useScrapeURL, useScrapeAllURLs } from '../hooks/useScrapers';
import { CreateURLDTO, UpdateURLDTO, ScrapedURL } from '../services/scraperService';
import { formatDistanceToNow } from 'date-fns';

interface URLFormData {
  url: string;
  url_type: string;
  enabled: boolean;
}

const initialFormData: URLFormData = {
  url: '',
  url_type: 'auto',
  enabled: true
};

const Scraper: React.FC = () => {
  const [openDialog, setOpenDialog] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [formData, setFormData] = useState<URLFormData>(initialFormData);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  // Queries and mutations
  const { data: urls, isLoading, refetch } = useURLs();
  const createURL = useCreateURL();
  const updateURL = useUpdateURL(currentId || 0);
  const deleteURL = useDeleteURL();
  const scrapeURL = useScrapeURL(currentId || 0);
  const scrapeAllURLs = useScrapeAllURLs();

  const handleOpenDialog = (edit = false, url?: ScrapedURL) => {
    setIsEdit(edit);
    if (edit && url) {
      setFormData({
        url: url.url,
        url_type: url.url_type,
        enabled: url.enabled
      });
      setCurrentId(url.id);
    } else {
      setFormData(initialFormData);
      setCurrentId(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const name = e.target.name as keyof URLFormData;
    const value = e.target.name === 'enabled' 
      ? (e.target as HTMLInputElement).checked
      : e.target.value;
    
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async () => {
    try {
      if (isEdit && currentId) {
        const updateData: UpdateURLDTO = { ...formData };
        await updateURL.mutateAsync(updateData);
        setSnackbar({
          open: true,
          message: 'URL updated successfully',
          severity: 'success'
        });
      } else {
        const createData: CreateURLDTO = { ...formData };
        await createURL.mutateAsync(createData);
        setSnackbar({
          open: true,
          message: 'URL added successfully',
          severity: 'success'
        });
      }
      handleCloseDialog();
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error: ${(error as Error).message}`,
        severity: 'error'
      });
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this URL?')) {
      try {
        await deleteURL.mutateAsync(id);
        setSnackbar({
          open: true,
          message: 'URL deleted successfully',
          severity: 'success'
        });
      } catch (error) {
        setSnackbar({
          open: true,
          message: `Error: ${(error as Error).message}`,
          severity: 'error'
        });
      }
    }
  };

  const handleScrape = async (id: number) => {
    setCurrentId(id);
    try {
      await scrapeURL.mutateAsync();
      setSnackbar({
        open: true,
        message: 'Scraping completed',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error: ${(error as Error).message}`,
        severity: 'error'
      });
    }
  };

  const handleScrapeAll = async () => {
    if (confirm('Start scraping all enabled URLs?')) {
      try {
        await scrapeAllURLs.mutateAsync();
        setSnackbar({
          open: true,
          message: 'Scraping all URLs completed',
          severity: 'success'
        });
      } catch (error) {
        setSnackbar({
        open: true,
        message: `Error: ${(error as Error).message}`,
        severity: 'error'
        });
      }
    }
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" gutterBottom>
          URL Scraper
        </Typography>
        <Box>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />} 
            onClick={() => handleOpenDialog(false)}
          >
            Add URL
          </Button>
          <Button 
            variant="outlined" 
            color="secondary" 
            startIcon={<PlayArrowIcon />} 
            onClick={handleScrapeAll}
            disabled={scrapeAllURLs.isLoading}
            sx={{ ml: 2 }}
          >
            Scrape All Enabled
          </Button>
          <IconButton color="primary" onClick={() => refetch()} disabled={isLoading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        {isLoading && <LinearProgress />}
        
        <TableContainer sx={{ maxHeight: 640 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Scraped</TableCell>
                <TableCell>Channels Found</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {urls && urls.length > 0 ? (
                urls.map((url) => (
                  <TableRow key={url.id} hover>
                    <TableCell>{url.url}</TableCell>
                    <TableCell>{url.url_type}</TableCell>
                    <TableCell>
                      <Chip 
                        label={url.enabled ? "Enabled" : "Disabled"} 
                        color={url.enabled ? "success" : "default"} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      {url.last_processed ? formatDistanceToNow(new Date(url.last_processed), { addSuffix: true }) : 'Never'}
                    </TableCell>
                    <TableCell>{url.channels_found || 0}</TableCell>
                    <TableCell>
                      <IconButton 
                        color="primary" 
                        onClick={() => handleScrape(url.id)}
                        disabled={scrapeURL.isLoading && currentId === url.id}
                      >
                        <PlayArrowIcon />
                      </IconButton>
                      <IconButton color="primary" onClick={() => handleOpenDialog(true, url)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton color="error" onClick={() => handleDelete(url.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    {isLoading ? 'Loading...' : 'No URLs found'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* URL Form Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>{isEdit ? 'Edit URL' : 'Add URL'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="url"
            label="URL"
            type="text"
            fullWidth
            value={formData.url}
            onChange={handleChange}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>URL Type</InputLabel>
            <Select
              name="url_type"
              value={formData.url_type}
              label="URL Type"
              onChange={handleChange}
            >
              <MenuItem value="auto">Auto-detect</MenuItem>
              <MenuItem value="regular">Regular HTTP</MenuItem>
              <MenuItem value="zeronet">ZeroNet</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              name="enabled"
              value={formData.enabled}
              label="Status"
              onChange={handleChange}
            >
              <MenuItem value={true}>Enabled</MenuItem>
              <MenuItem value={false}>Disabled</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            color="primary"
            disabled={!formData.url || createURL.isLoading || updateURL.isLoading}
          >
            {isEdit ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

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

export default Scraper;
