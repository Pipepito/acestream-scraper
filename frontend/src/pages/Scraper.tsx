import React, { useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
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
  Switch,
  FormControlLabel,
  FormHelperText,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Refresh as RefreshIcon, PlayArrow as PlayArrowIcon } from '@mui/icons-material';
import { useURLs, useCreateURL, useUpdateURL, usePatchURL, useDeleteURL, useScrapeAllURLs } from '../hooks/useScrapers';
import { CreateURLDTO, UpdateURLDTO, ScrapedURL, scraperService } from '../services/scraperService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import RowActionsMenu from '../components/RowActionsMenu';
import { useConfirm } from '../components/ConfirmDialog';
import { formatRelativeTime } from '../utils/format';
import { formatDateTime } from '../utils/formatters';

interface URLFormData {
  url: string;
  url_type: string;
  enabled: boolean;
  scrape_bare_ids: boolean;
}

export const URL_TYPE_LABELS: Record<string, string> = {
  auto: 'Auto-detect',
  regular: 'Regular HTTP',
  zeronet: 'ZeroNet',
  ipfs: 'IPFS',
};

/**
 * The backend stores the outcome of the last scrape as a free-form status string
 * ("OK", "Error: ...", "pending"). Surface it so a failing source is visible.
 */
export const describeScrapeResult = (status: string | null | undefined): { label: string; color: 'success' | 'error' | 'default'; detail?: string } => {
  if (!status || status === 'pending' || status === 'active') return { label: 'Not scraped yet', color: 'default' };
  if (status === 'OK') return { label: 'OK', color: 'success' };
  if (/^error/i.test(status)) return { label: 'Error', color: 'error', detail: status };
  return { label: status, color: 'default' };
};

const renderScrapeResult = (url: { status?: string | null }) => {
  const result = describeScrapeResult(url.status);
  return (
    <Chip
      label={result.label}
      color={result.color}
      size="small"
      variant={result.color === 'default' ? 'outlined' : 'filled'}
      title={result.detail}
      aria-label={result.detail ? `Last scrape failed: ${result.detail}` : undefined}
    />
  );
};

const initialFormData: URLFormData = {
  url: '',
  url_type: 'auto',
  enabled: true,
  scrape_bare_ids: false
};

const Scraper: React.FC = () => {
  const queryClient = useQueryClient();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [openDialog, setOpenDialog] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentId, setCurrentId] = useState<number | null>(null);

  const [formData, setFormData] = useState<URLFormData>(initialFormData);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Queries and mutations
  const { data: urls, isLoading, refetch } = useURLs();
  const createURL = useCreateURL();
  const updateURL = useUpdateURL(currentId || 0);
  const patchURL = usePatchURL();
  const deleteURL = useDeleteURL();
  const scrapeAllURLs = useScrapeAllURLs();

  const totalSourceCount = urls?.length ?? 0;
  const enabledSourceCount = urls?.filter((url) => url.enabled).length ?? 0;
  const failingSourceCount = urls?.filter((url) => /^error/i.test(url.status ?? '')).length ?? 0;
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

  const handleOpenDialog = (edit = false, url?: ScrapedURL) => {
    setIsEdit(edit);
    if (edit && url) {
      setFormData({
        url: url.url,
        url_type: url.url_type,
        enabled: url.enabled,
        scrape_bare_ids: url.scrape_bare_ids ?? false
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
    if (await confirm({ title: 'Delete this source?', body: 'Channels already found from it stay in the inventory.', confirmLabel: 'Delete', danger: true })) {
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

  const [bareIdsUpdatingId, setBareIdsUpdatingId] = useState<number | null>(null);
  const handleToggleBareIds = async (url: ScrapedURL, checked: boolean) => {
    setBareIdsUpdatingId(url.id);

    try {
      await patchURL.mutateAsync({ id: url.id, data: { scrape_bare_ids: checked } });
      setSnackbar({
        open: true,
        message: checked
          ? 'Bare content ID harvesting enabled'
          : 'Bare content ID harvesting disabled',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error: ${(error as Error).message}`,
        severity: 'error'
      });
    } finally {
      setBareIdsUpdatingId(null);
    }
  };

  const [enabledUpdatingId, setEnabledUpdatingId] = useState<number | null>(null);
  const handleToggleEnabled = async (url: ScrapedURL, checked: boolean) => {
    setEnabledUpdatingId(url.id);
    try {
      await patchURL.mutateAsync({ id: url.id, data: { enabled: checked } });
      setSnackbar({ open: true, message: checked ? 'Source enabled' : 'Source disabled; it is skipped by scheduled scrapes', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`, severity: 'error' });
    } finally {
      setEnabledUpdatingId(null);
    }
  };

  const [scrapingId, setScrapingId] = useState<number | null>(null);
  const handleScrape = async (id: number) => {
    setScrapingId(id);

    try {
      await scraperService.scrapeURL(id);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['url', id] }),
        queryClient.invalidateQueries({ queryKey: ['urls'] }),
        queryClient.invalidateQueries({ queryKey: ['channels'] }),
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
    if (await confirm({ title: 'Scrape all enabled sources?', body: `${enabledSourceCount} source${enabledSourceCount === 1 ? '' : 's'} will be fetched now; results appear in the table as each finishes.`, confirmLabel: 'Scrape all' })) {
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
        title="Scraper"
        subtitle="Source URLs and the channels each one yields."
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
              disabled={scrapeAllURLs.isPending || enabledSourceCount === 0}
            >
              Scrape all
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => refetch()} disabled={isLoading}>
              Refresh
            </Button>
          </Stack>
        }
      />

      <StatusLine
        aria-label="Source status"
        items={[
          { label: 'Sources', value: `${enabledSourceCount} of ${totalSourceCount} enabled` },
          { label: 'Last scrape', value: formatRelativeTime(latestProcessedAt), tone: latestProcessedAt ? 'default' : 'warning' },
          { label: 'Channels found', value: String(totalExtractedChannels) },
          ...(failingSourceCount > 0 ? [{ label: 'Failing', value: String(failingSourceCount), tone: 'error' as const }] : []),
        ]}
      />

      <ContentSection title="Sources">
        {isLoading && <LinearProgress sx={{ mb: 2 }} />}
        <TableContainer sx={{ maxHeight: 640 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Enabled</TableCell>
                <TableCell>Last result</TableCell>
                <TableCell>Last scraped</TableCell>
                <TableCell align="right">Channels</TableCell>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {urls && urls.length > 0 ? (
                urls.map((url) => (
                  <TableRow key={url.id} hover>
                    <TableCell sx={{ wordBreak: 'break-all' }}>{url.url}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>{URL_TYPE_LABELS[url.url_type] ?? url.url_type}</TableCell>
                    <TableCell>
                      <Switch
                        size="small"
                        checked={url.enabled}
                        onChange={(e) => handleToggleEnabled(url, e.target.checked)}
                        disabled={enabledUpdatingId === url.id}
                        inputProps={{ 'aria-label': `Enable ${url.url}` }}
                      />
                    </TableCell>
                    <TableCell>{renderScrapeResult(url)}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Tooltip title={url.last_processed ? formatDateTime(url.last_processed) : ''}>
                        <span>{formatRelativeTime(url.last_processed)}</span>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right">{url.channels_found || 0}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<PlayArrowIcon />}
                          onClick={() => handleScrape(url.id)}
                          disabled={scrapingId === url.id || !url.enabled}
                          aria-label={`Scrape URL ${url.url}`}
                        >
                          Scrape
                        </Button>
                        <RowActionsMenu
                          label={`More actions for ${url.url}`}
                          actions={[
                            { label: 'Edit', onClick: () => handleOpenDialog(true, url) },
                            { label: 'Harvest bare IDs', checked: Boolean(url.scrape_bare_ids), onClick: () => handleToggleBareIds(url, !url.scrape_bare_ids), disabled: bareIdsUpdatingId === url.id },
                            { label: 'Delete', danger: true, onClick: () => handleDelete(url.id) },
                          ]}
                        />
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    {isLoading ? (
                      'Loading…'
                    ) : (
                      <Typography variant="body2">No source URLs yet. Add one to start scraping.</Typography>
                    )}
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
              <MenuItem value="ipfs">IPFS</MenuItem>
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
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.scrape_bare_ids}
                  onChange={(e) => setFormData({ ...formData, scrape_bare_ids: e.target.checked })}
                />
              }
              label="Harvest bare content IDs"
            />
            <FormHelperText sx={{ ml: 0 }}>
              Also collect raw 40-character acestream hashes from pages that don&apos;t use acestream:// links.
            </FormHelperText>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            disabled={!formData.url || createURL.isPending || updateURL.isPending}
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
      {confirmDialog}
    </Box>
  );
};

export default Scraper;
