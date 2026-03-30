import React, { useMemo, useState } from 'react';
import { useQueryClient } from 'react-query';
import {
  Box,
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
  Snackbar,
  SelectChangeEvent,
  Stack,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { useURLs, useCreateURL, useUpdateURL, useDeleteURL, useScrapeAllURLs } from '../hooks/useScrapers';
import { CreateURLDTO, UpdateURLDTO, ScrapedURL, scraperService } from '../services/scraperService';
import { formatDistanceToNow } from 'date-fns';
import { alpha, useTheme } from '@mui/material/styles';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

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
  const theme = useTheme();
  const queryClient = useQueryClient();
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
  const scrapeAllURLs = useScrapeAllURLs();

  const totalSourceCount = urls?.length ?? 0;
  const enabledSourceCount = urls?.filter((url) => url.enabled).length ?? 0;
  const totalExtractedChannels = urls?.reduce((sum, url) => sum + (url.channels_found || 0), 0) ?? 0;
  const latestProcessedAt = useMemo(() => {
    if (!urls?.length) {
      return null;
    }

    return urls.reduce<string | null>((latest, url) => {
      if (!url.last_processed) {
        return latest;
      }

      if (!latest || new Date(url.last_processed).getTime() > new Date(latest).getTime()) {
        return url.last_processed;
      }

      return latest;
    }, null);
  }, [urls]);
  const latestProcessedLabel = latestProcessedAt
    ? `Latest scrape finished ${formatDistanceToNow(new Date(latestProcessedAt), { addSuffix: true })}`
    : 'No completed scrape yet';
  const sourceReadinessLabel = totalSourceCount === 0
    ? 'No source URLs configured yet.'
    : enabledSourceCount === 0
      ? 'Sources are listed, but none are enabled for intake.'
      : `${enabledSourceCount} of ${totalSourceCount} source${totalSourceCount === 1 ? '' : 's'} enabled for intake.`;
  const nextStepLabel = totalSourceCount === 0
    ? 'Add your first source URL to start the pipeline.'
    : enabledSourceCount === 0
      ? 'Enable at least one source, then run a scrape.'
      : 'Run a scrape, then review extracted channels after the scrape completes.';

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.name as keyof URLFormData;
    const value = e.target.value;

    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSelectChange = (e: SelectChangeEvent<string>) => {
    const name = e.target.name as keyof URLFormData;
    const value = e.target.value;

    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleEnabledChange = (e: SelectChangeEvent<string>) => {
    const value = e.target.value === 'true';

    setFormData({
      ...formData,
      enabled: value
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
    if (window.confirm('Are you sure you want to delete this URL?')) {
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

  const [scrapingId, setScrapingId] = useState<number | null>(null);
  const handleScrape = async (id: number) => {
    setScrapingId(id);

    try {
      await scraperService.scrapeURL(id);
      await Promise.all([
        queryClient.invalidateQueries(['url', id]),
        queryClient.invalidateQueries('urls'),
        queryClient.invalidateQueries('channels'),
      ]);

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
    } finally {
      setScrapingId(null);
    }
  };

  const handleScrapeAll = async () => {
    if (window.confirm('Start scraping all enabled URLs?')) {
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
      <PageHeader
        title="URL Scraper"
        subtitle="Manage source URLs and trigger scrape jobs."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={() => handleOpenDialog(false)}>
              Add URL
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<PlayArrowIcon />}
              onClick={handleScrapeAll}
              disabled={scrapeAllURLs.isLoading || enabledSourceCount === 0}
            >
              Scrape All Enabled
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => refetch()} disabled={isLoading}>
              Refresh
            </Button>
          </Stack>
        }
      />

      <Box
        sx={{
          mb: 3,
          p: { xs: 2, md: 2.5 },
          borderRadius: 2.5,
          bgcolor: theme.appTokens.hero.bg,
          border: `1px solid ${theme.appTokens.hero.border}`,
          backgroundImage: theme.appTokens.hero.spotlight,
        }}
      >
        <Stack spacing={2}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0, maxWidth: 760 }}>
              <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
                Source intake stage
              </Typography>
              <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
                Sources feed the pipeline before extracted-channel review and TV organization.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Use this intake summary to confirm source coverage, trigger scraping, and hand off to extracted-channel review without guessing what comes next.
              </Typography>
            </Box>
            <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 300 } }}>
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
                  border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}`,
                }}
              >
                <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                  Source readiness
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  {sourceReadinessLabel}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {latestProcessedLabel}
                </Typography>
              </Box>
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: theme.appTokens.surface.panel,
                  border: `1px solid ${theme.appTokens.surface.border}`,
                }}
              >
                <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                  Next step
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  {nextStepLabel}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {totalExtractedChannels > 0
                    ? `${totalExtractedChannels} extracted channel${totalExtractedChannels === 1 ? '' : 's'} found in current source results.`
                    : 'Extracted channel totals appear here after successful scrapes.'}
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25 }}>
            {[
              {
                title: 'Sources',
                label: 'Current intake stage',
                body: `${enabledSourceCount}/${totalSourceCount} enabled`,
                active: true,
              },
              {
                title: 'Extracted channels',
                label: 'Next review stage',
                body: 'Check scraped channel results and routing.',
                active: false,
              },
              {
                title: 'TV organization',
                label: 'Downstream output stage',
                body: 'Organize the final catalog for downstream workflows.',
                active: false,
              },
            ].map((stage) => (
              <Box
                key={stage.title}
                sx={{
                  flex: '1 1 180px',
                  minWidth: { xs: '100%', sm: 180 },
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: stage.active ? alpha(theme.appTokens.hero.accent, 0.10) : theme.appTokens.surface.panel,
                  border: `1px solid ${stage.active ? alpha(theme.appTokens.hero.accent, 0.24) : theme.appTokens.surface.border}`,
                }}
              >
                <Typography variant="statusMeta" sx={{ color: stage.active ? theme.appTokens.hero.accent : 'text.secondary', mb: 0.75 }}>
                  {stage.label}
                </Typography>
                <Typography variant="sectionTitle" sx={{ mb: 0.5 }}>
                  {stage.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stage.body}
                </Typography>
              </Box>
            ))}
          </Box>
        </Stack>
      </Box>

      <ContentSection title="Configured URLs" description="Run single URL checks or scrape all enabled sources.">
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
                         disabled={scrapingId === url.id}
                          aria-label={`Scrape URL ${url.url}`}
                        >
                        <PlayArrowIcon />
                      </IconButton>
                      <IconButton color="primary" onClick={() => handleOpenDialog(true, url)} aria-label={`Edit URL ${url.url}`}>
                        <EditIcon />
                      </IconButton>
                      <IconButton color="error" onClick={() => handleDelete(url.id)} aria-label={`Delete URL ${url.url}`}>
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
      </ContentSection>

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
            <InputLabel id="scraper-url-type-label">URL Type</InputLabel>
            <Select
              id="scraper-url-type"
              labelId="scraper-url-type-label"
              name="url_type"
              value={formData.url_type}
              label="URL Type"
              onChange={handleSelectChange}
            >
              <MenuItem value="auto">Auto-detect</MenuItem>
              <MenuItem value="regular">Regular HTTP</MenuItem>
              <MenuItem value="zeronet">ZeroNet</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="scraper-status-label">Status</InputLabel>
            <Select
              id="scraper-status"
              labelId="scraper-status-label"
              name="enabled"
              value={formData.enabled ? 'true' : 'false'}
              label="Status"
              onChange={handleEnabledChange}
            >
              <MenuItem value="true">Enabled</MenuItem>
              <MenuItem value="false">Disabled</MenuItem>
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
