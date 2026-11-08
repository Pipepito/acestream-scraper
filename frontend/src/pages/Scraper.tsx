import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';
import { responsiveTableSx } from '../styles/responsiveTable';
import React, { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Tabs,
  Tab,
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
import ImportExclusions from '../components/imports/ImportExclusions';
import SavedSearches from '../components/imports/SavedSearches';
import StatusLine from '../components/StatusLine';
import RowActionsMenu from '../components/RowActionsMenu';
import { useConfirm } from '../components/ConfirmDialog';
import DeleteSourceDialog from '../components/scraper/DeleteSourceDialog';
import OrphanedSourcesDialog from '../components/scraper/OrphanedSourcesDialog';
import { formatRelativeTime } from '../utils/format';
import { formatDateTime } from '../utils/formatters';

interface URLFormData {
  name: string;
  url: string;
  url_type: string;
  enabled: boolean;
  scrape_bare_ids: boolean;
}

export const URL_TYPE_LABELS: Record<string, string> = {
  broadcaster: 'Built-in broadcaster',
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
  if (!status || status === 'pending' || status === 'active') return { label: uiText("Not scraped yet"), color: 'default' };
  if (status === 'OK') return { label: 'OK', color: 'success' };
  if (/^error/i.test(status)) return { label: uiText("Error"), color: 'error', detail: status };
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
  name: '',
  url: '',
  url_type: 'auto',
  enabled: true,
  scrape_bare_ids: false
};

const ScraperSources: React.FC<{ navigation: React.ReactNode }> = ({ navigation }) => {
  const tUi = useUiText();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [openDialog, setOpenDialog] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentId, setCurrentId] = useState<number | null>(null);

  const [formData, setFormData] = useState<URLFormData>(initialFormData);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Queries and mutations
  const { data: urls, isLoading, refetch } = useURLs();
  const providers = useQuery({ queryKey: ['builtin-providers'], queryFn: scraperService.getProviders, enabled: openDialog });
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
        name: url.name ?? '',
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
          message: uiText("URL updated successfully"),
          severity: 'success'
        });
      } else {
        const createData: CreateURLDTO = { ...formData };
        await createURL.mutateAsync(createData);
        setSnackbar({
          open: true,
          message: uiText("URL added successfully"),
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

  const [deletingSource, setDeletingSource] = useState<ScrapedURL | null>(null);
  const [cleanupOpen, setCleanupOpen] = useState(false);
  const handleDelete = (source: ScrapedURL) => setDeletingSource(source);
  const confirmDelete = async (deleteStreams: boolean) => {
    if (!deletingSource) return;
    try {
      const result = await deleteURL.mutateAsync({ id: deletingSource.id, deleteStreams });
      setDeletingSource(null);
      setSnackbar({
        open: true,
        message: deleteStreams ? `Source deleted with ${result.deleted_streams} stream${result.deleted_streams === 1 ? '' : 's'}.` : uiText("Source deleted. Its streams stay in the inventory."),
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

  const [bareIdsUpdatingId, setBareIdsUpdatingId] = useState<number | null>(null);
  const handleToggleBareIds = async (url: ScrapedURL, checked: boolean) => {
    setBareIdsUpdatingId(url.id);

    try {
      await patchURL.mutateAsync({ id: url.id, data: { scrape_bare_ids: checked } });
      setSnackbar({
        open: true,
        message: checked
          ? uiText("Bare content ID harvesting enabled")
          : uiText("Bare content ID harvesting disabled"),
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
      setSnackbar({ open: true, message: checked ? uiText("Source enabled") : uiText("Source disabled; it is skipped by scheduled scrapes"), severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: `Error: ${error instanceof Error ? error.message : uiText("Unknown error")}`, severity: 'error' });
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
        message: uiText("Scraping completed"),
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
    if (await confirm({ title: uiText("Scrape all enabled sources?"), body: `${enabledSourceCount} source${enabledSourceCount === 1 ? '' : 's'} will be fetched now; results appear in the table as each finishes.`, confirmLabel: uiText("Scrape all") })) {
      try {
        await scrapeAllURLs.mutateAsync();
        setSnackbar({
          open: true,
          message: uiText("Scraping all URLs completed"),
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
        title={tUi("Scraper")}
        subtitle={tUi("Source URLs and the channels each one yields.")}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={() => handleOpenDialog(false)}>
              {tUi("Add URL")}</Button>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<PlayArrowIcon />}
              onClick={handleScrapeAll}
              disabled={scrapeAllURLs.isPending || enabledSourceCount === 0}
            >
              {tUi("Scrape all")}</Button>
          </Stack>
        }
        overflowActions={[{ label: uiText("Extraction builder"), onClick: () => navigate('/scraper/builder') }, { label: uiText("Clean up removed sources…"), onClick: () => setCleanupOpen(true) }, { label: uiText("Refresh"), icon: <RefreshIcon fontSize="small" />, onClick: () => void refetch(), disabled: isLoading }]}
      />

      {navigation}
      <StatusLine
        aria-label={tUi("Source status")}
        items={[
          { label: uiText("Sources"), value: `${enabledSourceCount} of ${totalSourceCount} enabled` },
          { label: uiText("Last scrape"), value: formatRelativeTime(latestProcessedAt), tone: latestProcessedAt ? 'default' : 'warning' },
          { label: uiText("Channels found"), value: String(totalExtractedChannels) },
          ...(failingSourceCount > 0 ? [{ label: uiText("Failing"), value: String(failingSourceCount), tone: 'error' as const }] : []),
        ]}
      />

      <ContentSection actions={<Button component={RouterLink} to="/settings?tab=automation">{tUi("Edit schedule")}</Button>} title={tUi("Sources")}>
        {isLoading && <LinearProgress sx={{ mb: 2 }} />}
        <TableContainer sx={[responsiveTableSx, { maxHeight: { xs: 'none', sm: 640 } }]}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>{tUi("URL")}</TableCell>
                <TableCell>{tUi("Type")}</TableCell>
                <TableCell>{tUi("Enabled")}</TableCell>
                <TableCell>{tUi("Last result")}</TableCell>
                <TableCell>{tUi("Last scraped")}</TableCell>
                <TableCell align="right">{tUi("Channels")}</TableCell>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{tUi("Actions")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {urls && urls.length > 0 ? (
                urls.map((url) => (
                  <TableRow key={url.id} hover>
                    <TableCell data-label="URL" sx={{ overflowWrap: 'anywhere' }}>{url.name ? <Typography variant="body2" fontWeight={600}>{url.name}</Typography> : null}{url.url}</TableCell>
                    <TableCell data-label={uiText("Type")} sx={{ whiteSpace: 'nowrap' }}>{URL_TYPE_LABELS[url.url_type] ?? url.url_type}{url.extraction_recipe && <Chip size="small" label={tUi("Custom recipe")} sx={{ ml: 1 }} />}</TableCell>
                    <TableCell data-label={uiText("Enabled")}>
                      <Switch
                        size="small"
                        checked={url.enabled}
                        onChange={(e) => handleToggleEnabled(url, e.target.checked)}
                        disabled={enabledUpdatingId === url.id}
                        inputProps={{ 'aria-label': `Enable ${url.url}` }}
                      />
                    </TableCell>
                    <TableCell data-label={uiText("Last result")}>{renderScrapeResult(url)}</TableCell>
                    <TableCell data-label={uiText("Last scraped")} sx={{ whiteSpace: 'nowrap' }}>
                      <Tooltip title={url.last_processed ? formatDateTime(url.last_processed) : ''}>
                        <span>{formatRelativeTime(url.last_processed)}</span>
                      </Tooltip>
                    </TableCell>
                    <TableCell data-label={uiText("Channels")} align="right">{url.channels_found || 0}</TableCell>
                    <TableCell data-label={uiText("Actions")} sx={{ whiteSpace: 'nowrap' }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<PlayArrowIcon />}
                          onClick={() => handleScrape(url.id)}
                          disabled={scrapingId === url.id || !url.enabled}
                          aria-label={tUi("Scrape URL {{value0}}", { value0: url.url })}
                        >
                          {tUi("Scrape")}</Button>
                        <RowActionsMenu
                          label={tUi("More actions for {{value0}}", { value0: url.url })}
                          actions={[
                            { label: uiText("Edit"), onClick: () => handleOpenDialog(true, url) },
                            { label: uiText("Configure extraction"), disabled: url.url_type === 'broadcaster', onClick: () => navigate(`/scraper/builder?source=${url.id}`) },
                            { label: uiText("Harvest bare IDs"), checked: Boolean(url.scrape_bare_ids), onClick: () => handleToggleBareIds(url, !url.scrape_bare_ids), disabled: url.url_type === 'broadcaster' || bareIdsUpdatingId === url.id || Boolean(url.extraction_recipe) },
                            { label: uiText("Delete"), danger: true, onClick: () => handleDelete(url) },
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
                      <Typography variant="body2">{tUi("No source URLs yet. Add one to start scraping.")}</Typography>
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
        <DialogTitle>{isEdit ? tUi("Edit URL") : tUi("Add URL")}</DialogTitle>
        <DialogContent>
          {providers.isError ? <Alert severity="error" action={<Button onClick={() => void providers.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load built-in providers.")}</Alert> : null}
          {!isEdit ? <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel id="builtin-provider-label">{tUi("Built-in provider")}</InputLabel>
            <Select labelId="builtin-provider-label" label={tUi("Built-in provider")}
              value={formData.url_type === 'broadcaster' ? providers.data?.find(provider => provider.url === formData.url)?.id ?? '' : ''}
              onChange={event => {
                const provider = providers.data?.find(item => item.id === event.target.value);
                setFormData(previous => {
                  const previousProvider = providers.data?.find(item => item.url === previous.url);
                  const customName = previous.name && previous.name !== previousProvider?.name;
                  return provider
                    ? { ...previous, url: provider.url, url_type: 'broadcaster', name: customName ? previous.name : provider.name, scrape_bare_ids: false }
                    : { ...previous, url: '', url_type: 'auto', name: customName ? previous.name : '' };
                });
              }}>
              <MenuItem value="">{tUi("Custom source URL")}</MenuItem>
              {providers.data?.map(provider => <MenuItem key={provider.id} value={provider.id}>{provider.name}</MenuItem>)}
            </Select>
            <FormHelperText>{tUi("Built-in broadcasters import channels directly through their adapter. Saving does not import channels.")}</FormHelperText>
          </FormControl> : null}
          <TextField label={tUi("Friendly name (optional)")} name="name" fullWidth value={formData.name} onChange={handleChange} inputProps={{ maxLength: 255 }} helperText={tUi("Shown in the source list and channel filters.")} sx={{ mb: 2 }} />
          <TextField
            margin="dense"
            name="url"
            label={tUi("URL")}
            type="text"
            fullWidth
            value={formData.url}
            onChange={handleChange}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="scraper-url-type-label">{tUi("URL Type")}</InputLabel>
            <Select
              id="scraper-url-type"
              labelId="scraper-url-type-label"
              name="url_type"
              value={formData.url_type}
              label={tUi("URL Type")}
              onChange={handleSelectChange}
            >
              <MenuItem value="broadcaster">{tUi("Built-in broadcaster")}</MenuItem>
              <MenuItem value="auto">{tUi("Auto-detect")}</MenuItem>
              <MenuItem value="regular">{tUi("Regular HTTP")}</MenuItem>
              <MenuItem value="zeronet">{tUi("ZeroNet")}</MenuItem>
              <MenuItem value="ipfs">{tUi("IPFS")}</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="scraper-status-label">{tUi("Status")}</InputLabel>
            <Select
              id="scraper-status"
              labelId="scraper-status-label"
              name="enabled"
              value={formData.enabled ? 'true' : 'false'}
              label={tUi("Status")}
              onChange={handleEnabledChange}
            >
              <MenuItem value="true">{tUi("Enabled")}</MenuItem>
              <MenuItem value="false">{tUi("Disabled")}</MenuItem>
            </Select>
          </FormControl>
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  disabled={formData.url_type === 'broadcaster'}
                  checked={formData.scrape_bare_ids}
                  onChange={(e) => setFormData({ ...formData, scrape_bare_ids: e.target.checked })}
                />
              }
              label={tUi("Harvest bare content IDs")}
            />
            <FormHelperText sx={{ ml: 0 }}>
              {tUi("Also collect raw 40-character acestream hashes from pages that don't use acestream:// links.")}</FormHelperText>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>{tUi("Cancel")}</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            disabled={!formData.url || createURL.isPending || updateURL.isPending}
          >
            {isEdit ? tUi("Update") : tUi("Add")}
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
      <DeleteSourceDialog open={Boolean(deletingSource)} source={deletingSource} busy={deleteURL.isPending} onClose={() => setDeletingSource(null)} onConfirm={(deleteStreams) => void confirmDelete(deleteStreams)} />
      <OrphanedSourcesDialog open={cleanupOpen} onClose={() => setCleanupOpen(false)} onDone={(message) => setSnackbar({ open: true, message, severity: 'success' })} />
    </Box>
  );
};

const Catalogues = React.lazy(() => import('./Catalogues'));

const Scraper: React.FC = () => {
  const tUi = useUiText();
  const [params, setParams] = useSearchParams();
  const selected = params.get('tab');
  const tab = selected === 'w3u' || selected === 'searches' || selected === 'exclusions' ? selected : 'sources';
  const navigation = <Tabs value={tab} onChange={(_, value: string) => { const next = new URLSearchParams(params); next.set('tab', value); setParams(next); }} aria-label={tUi("Scraper sections")} variant="scrollable" scrollButtons="auto" allowScrollButtonsMobile sx={{ mb: 2 }}>
    <Tab value="sources" label={tUi("Sources")} /><Tab value="w3u" label={tUi("W3U catalogues")} /><Tab value="searches" label={tUi("Saved searches")} /><Tab value="exclusions" label={tUi("Import exclusions")} />
  </Tabs>;
  return <Box>
    {tab === 'sources' ? <ScraperSources navigation={navigation} /> : <><PageHeader title={tUi("Scraper")} subtitle={tUi("Manage discoveries and future imports.")} />{navigation}
      {tab === 'w3u' ? <React.Suspense fallback={<p role="status">{tUi("Loading catalogues…")}</p>}><Catalogues embedded /></React.Suspense> : tab === 'searches' ? <SavedSearches /> : <ImportExclusions />}</>}
  </Box>;
};
export default Scraper;
