import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import {
  Alert, Avatar, Box, Breadcrumbs, Button, Checkbox, Chip, FormControlLabel,
  List, ListItem, ListItemButton, ListItemText, MenuItem, Pagination, Snackbar, Stack,
  Switch, TextField, Typography,
} from '@mui/material';
import RowActionsMenu from '../components/RowActionsMenu';
import AssignTVChannelDialog, { type AssignChoice } from '../components/AssignTVChannelDialog';
import FolderMatchDialog from '../components/catalogues/FolderMatchDialog';
import { useTVChannelCatalog } from '../hooks/useTVChannels';
import FolderOutlined from '@mui/icons-material/FolderOutlined';
import StarOutlineRounded from '@mui/icons-material/StarOutlineRounded';
import StarRounded from '@mui/icons-material/StarRounded';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import EventImportPanel from '../components/events/EventImportPanel';
import ConfirmDialog from '../components/ConfirmDialog';
import { catalogueService, type CatalogueEntry, type CataloguePreviewRequest, type CatalogueView, type FolderAssignRequest } from '../services/catalogueService';
import { getErrorMessage } from '../utils/errorUtils';

const STORAGE_KEY = 'acestream.catalogue-history.v1';
interface BrowserHistory { favorites: string[]; recent: string[] }
function loadHistory(): BrowserHistory {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
    if (typeof value === 'object' && value !== null) {
      const stored = value as Partial<BrowserHistory>;
      const clean = (items: unknown): string[] => Array.isArray(items) ? items.filter((id): id is string => typeof id === 'string').slice(0, 500) : [];
      return { favorites: clean(stored.favorites), recent: clean(stored.recent) };
    }
  } catch { /* Storage can be unavailable in private browsing. */ }
  return { favorites: [], recent: [] };
}
const kindLabels: Record<CatalogueEntry['kind'], string> = {
  folder: 'Folder', acestream: 'AceStream', hls: 'HLS', mpegts: 'MPEG-TS', resolver: 'Broadcaster',
  vod: 'VOD · unavailable', unsupported: 'Unsupported', invalid: 'Invalid',
};

interface CataloguesProps { embedded?: boolean }

const Catalogues: React.FC<CataloguesProps> = ({ embedded = false }) => {
  const tUi = useUiText();
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  /** Rewrite only the catalogue browsing keys: the host page's own params (such as Scraper's `tab`) survive. */
  const setBrowseParams = (next: Record<string, string>) => setParams((current) => {
    const merged = new URLSearchParams(current);
    merged.delete('catalogue'); merged.delete('folder');
    Object.entries(next).forEach(([key, value]) => merged.set(key, value));
    return merged;
  });
  const catalogueId = Number(params.get('catalogue')) || null;
  const folder = params.get('folder') ?? 'root';
  const list = useQuery({ queryKey: ['catalogues'], queryFn: catalogueService.list });
  const saved = useQuery({ queryKey: ['catalogue', catalogueId], queryFn: () => catalogueService.get(catalogueId!), enabled: catalogueId !== null });
  const [preview, setPreview] = useState<CatalogueView | null>(null);
  const [adding, setAdding] = useState(false);
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [branches, setBranches] = useState<string[]>(['root']);
  const [confirmLive, setConfirmLive] = useState(false);
  const [eventEntry, setEventEntry] = useState<CatalogueEntry | null>(null);
  const [mode, setMode] = useState<'compatible' | 'acestream'>('compatible');
  const [refreshEnabled, setRefreshEnabled] = useState(false);
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('all');
  const [historyFilter, setHistoryFilter] = useState('all');
  const [history, setHistory] = useState(loadHistory);
  const [showArtwork, setShowArtwork] = useState(false);
  const [details, setDetails] = useState<string | null>(null);
  const [playing, setPlaying] = useState<CatalogueEntry | null>(null);
  const [page, setPage] = useState(1);
  const [fileError, setFileError] = useState('');
  const [confirmRemove, setConfirmRemove] = useState(false);
  const view = preview ?? saved.data;
  const entries = view?.entries;
  const byId = useMemo(() => new Map(entries?.map((entry) => [entry.id, entry]) ?? []), [entries]);
  const itemKey = (entry: CatalogueEntry) => `${view?.id ?? 'preview'}:${entry.id}`;
  const detail = details ? byId.get(details) : undefined;
  const detailsRef = useRef<HTMLDivElement>(null);
  const eventRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (eventEntry) {
      eventRef.current?.focus();
      eventRef.current?.scrollIntoView?.({ block: 'start' });
    }
  }, [eventEntry]);
  useEffect(() => { if (details) detailsRef.current?.focus(); }, [details]);
  const busy = saved.isFetching;

  const navigateFolder = (id: string) => {
    setBrowseParams({ ...(catalogueId ? { catalogue: String(catalogueId) } : {}), folder: id });
    setPage(1); setDetails(null);
  };
  const resetBrowse = () => { setEventEntry(null); setSearch(''); setKind('all'); setHistoryFilter('all'); setPage(1); setDetails(null); };
  const prepare = useMutation({ mutationFn: catalogueService.preview, onSuccess: (result) => {
    setPreview(result); setName(result.name); setBranches(result.selected_branches ?? ['root']);
    setMode(result.mode ?? 'compatible'); setRefreshEnabled(result.refresh_enabled ?? false);
    setAdding(false); setUrl(''); setConfirmLive(false); setEventEntry(null); resetBrowse();
    setBrowseParams(result.id ? { catalogue: String(result.id) } : {});
  } });
  const save = useMutation({ mutationFn: catalogueService.save, onSuccess: (result) => {
    queryClient.setQueryData(['catalogue', result.id], result);
    void queryClient.invalidateQueries({ queryKey: ['catalogues'] });
    void queryClient.invalidateQueries({ queryKey: ['channel-sources'] });
    void queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
    setPreview(null); setBrowseParams({ catalogue: String(result.id) }); resetBrowse();
  } });
  const remove = useMutation({ mutationFn: catalogueService.remove, onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: ['catalogues'] });
    void queryClient.invalidateQueries({ queryKey: ['channel-sources'] });
    setBrowseParams({}); setConfirmRemove(false); setPreview(null); setDetails(null);
  } });
  const pending = prepare.isPending || save.isPending || remove.isPending;
  const tvCatalog = useTVChannelCatalog();
  const [assignFolderEntry, setAssignFolderEntry] = useState<CatalogueEntry | null>(null);
  const [matchOpen, setMatchOpen] = useState(false);
  const [notice, setNotice] = useState<{ message: string; moveTo?: { catalogueId: number; folder: CatalogueEntry; tvChannelId: number } } | null>(null);
  const invalidateAssignments = (id: number) => {
    void queryClient.invalidateQueries({ queryKey: ['catalogue', id] });
    void queryClient.invalidateQueries({ queryKey: ['tvChannels'] });
    void queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
  };
  const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`;
  const assignFolder = useMutation({
    mutationFn: ({ catalogueId, folder, request }: { catalogueId: number; folder: CatalogueEntry; request: FolderAssignRequest }) =>
      catalogueService.assignFolder(catalogueId, folder.id, request),
    onSuccess: (result, { catalogueId, folder, request }) => {
      setAssignFolderEntry(null);
      invalidateAssignments(catalogueId);
      if (request.reassign) {
        setNotice({ message: `${plural(result.moved ?? 0, 'stream')} moved to ${result.tv_channel.name}.` });
        return;
      }
      const skipped = result.skipped_other_channel ?? 0;
      setNotice({
        message: `${plural(result.assigned ?? 0, 'stream')} assigned to ${result.tv_channel.name}.${skipped ? ` ${plural(skipped, 'stream')} ${skipped === 1 ? 'is' : 'are'} on another TV channel.` : ''}`,
        moveTo: skipped ? { catalogueId, folder, tvChannelId: result.tv_channel.id } : undefined,
      });
    },
  });
  const error = fileError || [list.error, saved.error, prepare.error, save.error, remove.error].filter(Boolean).map((err) => getErrorMessage(err)).join(' ');
  const startPreview = (request: CataloguePreviewRequest) => { setFileError(''); prepare.mutate(request); };
  const updateHistory = (next: BrowserHistory) => {
    setHistory(next);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { /* Keep working in memory. */ }
  };
  const favorite = (entry: CatalogueEntry) => {
    const key = itemKey(entry);
    updateHistory({ ...history, favorites: history.favorites.includes(key)
      ? history.favorites.filter((value) => value !== key) : [key, ...history.favorites].slice(0, 500) });
  };
  const inspect = (entry: CatalogueEntry) => {
    setDetails(entry.id);
    const key = itemKey(entry);
    if (!preview) updateHistory({ ...history, recent: [key, ...history.recent.filter((id) => id !== key)].slice(0, 100) });
  };
  const filtered = useMemo(() => {
    const global = search.trim() !== '' || kind !== 'all' || historyFilter !== 'all';
    return (entries ?? []).filter((entry) => entry.id !== 'root'
      && (global || entry.parent_id === folder)
      && entry.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())
      && (kind === 'all' || entry.kind === kind)
      && (historyFilter === 'all' || history[historyFilter as 'favorites' | 'recent'].includes(`${view?.id ?? 'preview'}:${entry.id}`)))
      .sort(historyFilter === 'recent' ? (a, b) => history.recent.indexOf(`${view?.id}:${a.id}`) - history.recent.indexOf(`${view?.id}:${b.id}`) : () => 0);
  }, [entries, folder, search, kind, historyFilter, history, view?.id]);
  const breadcrumbs: CatalogueEntry[] = [];
  let current = byId.get(folder);
  while (current && breadcrumbs.length < 20) {
    breadcrumbs.unshift(current);
    current = current.parent_id ? byId.get(current.parent_id) : undefined;
  }
  const variants = detail ? (entries ?? []).filter((entry) => entry.id !== detail.id && entry.kind !== 'folder'
    && entry.parent_id === detail.parent_id && entry.name === detail.name) : [];

  const addButton = <Button variant="contained" disabled={pending} onClick={() => { setAdding(true); setPreview(null); prepare.reset(); save.reset(); }}>{tUi("Add catalogue")}</Button>;
  return <Box sx={{ '& > section, & > div > section': { height: 'auto' } }}>
    {embedded
      ? <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>{addButton}</Box>
      : <PageHeader title={tUi("Catalogues")} subtitle={tUi("Browse Wiseplay/W3U folders and review compatible streams before importing.")} primaryActions={addButton} />}
    <StatusLine items={[{ label: uiText("Saved"), value: list.data?.length ?? '—' },
      ...(view ? [{ label: uiText("Compatible"), value: view.counts.accepted ?? 0 }, { label: uiText("Excluded"), value: view.counts.excluded ?? 0 }, { label: uiText("Duplicates"), value: view.counts.duplicates ?? 0 },
        { label: uiText("Invalid"), value: view.counts.invalid ?? 0 }, { label: uiText("Unsupported"), value: view.counts.unsupported ?? 0 },
        { label: uiText("Fetch failures"), value: view.counts.failed_fetches ?? 0 }] : [])]} />
    {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
    {prepare.isPending ? <Alert severity="info" role="status" sx={{ mb: 2 }}>{tUi("Reading catalogue folders… Preview is bounded to 45 seconds. Nothing has been imported.")}</Alert> : null}
    {adding ? <ContentSection title={tUi("Add W3U catalogue")} description={tUi("Use a catalogue URL or a local JSON/W3U file up to 4 MiB. Linked folders are fetched by the server.")}>
      <Stack spacing={2}>
        <TextField label={tUi("Catalogue URL")} value={url} onChange={(event) => setUrl(event.target.value)} fullWidth type="url" />
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Button variant="contained" disabled={pending || !url.trim()} onClick={() => startPreview({ url: url.trim() })}>{tUi("Preview URL")}</Button>
          <Button component="label" variant="outlined" disabled={pending}>{tUi("Choose W3U file")}<input type="file" accept=".w3u,.json,application/json" hidden onChange={(event) => {
              const file = event.target.files?.[0]; event.target.value = '';
              if (!file) return;
              if (file.size > 4 * 1024 * 1024) { setFileError('Choose a W3U file no larger than 4 MiB.'); return; }
              void file.text().then((sample) => startPreview({ sample })).catch(() => setFileError('Unable to read the selected file.'));
            }} />
          </Button>
          <Button onClick={() => setAdding(false)} disabled={pending}>{tUi("Cancel")}</Button>
        </Stack>
      </Stack>
    </ContentSection> : null}
    <ContentSection title={tUi("Saved catalogues")}>
      {list.isPending ? <Typography role="status">{tUi("Loading catalogues…")}</Typography> : !list.data?.length ? <Typography>{tUi("No catalogues yet. Add a W3U URL or file to inspect its folders and playback compatibility.")}</Typography> :
        <List disablePadding>{list.data.map((catalogue) => <ListItem key={catalogue.id} disablePadding>
          <ListItemButton selected={catalogue.id === catalogueId} disabled={pending} onClick={() => {
            setPreview(null); setAdding(false); resetBrowse(); setBrowseParams({ catalogue: String(catalogue.id) }); prepare.reset(); save.reset();
          }}><ListItemText primary={catalogue.name} secondary={`${catalogue.origin} · ${catalogue.partial ? uiText("Partial refresh") : uiText("Saved")} · ${catalogue.refresh_enabled ? uiText("Scheduled refresh on") : uiText("Manual refresh")}`} sx={{ overflowWrap: 'anywhere' }} /></ListItemButton>
        </ListItem>)}</List>}
    </ContentSection>
    {busy && !view ? <Typography role="status">{tUi("Loading catalogue…")}</Typography> : null}
    {view ? <>
      <ContentSection title={preview ? tUi("Review import") : view.name} actions={!preview ? <>
        <Button disabled={pending} onClick={() => setMatchOpen(true)}>{tUi("Match folders to TV channels")}</Button>
        <Button variant="outlined" disabled={pending} onClick={() => startPreview({ catalogue_id: view.id })}>{view.can_refresh ? tUi("Preview refresh") : tUi("Review selection")}</Button>
        <Button color="error" disabled={pending} onClick={() => setConfirmRemove(true)}>{tUi("Remove catalogue")}</Button>
      </> : undefined}>
        {view.partial ? <Alert severity="warning" sx={{ mb: 2 }}>{tUi("This is a partial catalogue. Previously saved entries remain available and are marked Retained.")}</Alert> : null}
        {(view.warnings ?? []).map((warning) => <Alert key={warning} severity="warning" sx={{ mb: 1 }}>{warning}</Alert>)}
        {preview ? <Stack spacing={1.5} sx={{ mb: 3 }}>
          <TextField label={tUi("Catalogue name")} value={name} onChange={(event) => setName(event.target.value)} inputProps={{ maxLength: 255 }} />
          <TextField select label={tUi("Import streams")} value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}>
            <MenuItem value="compatible">{tUi("Compatible live streams")}</MenuItem><MenuItem value="acestream">{tUi("AceStream only")}</MenuItem>
          </TextField>
          <FormControlLabel control={<Checkbox checked={branches.includes('root')} onChange={(_, checked) => setBranches(checked ? ['root'] : [])} />} label={tUi("All folders")} />
          <Typography variant="body2">{tUi("Clear All folders to select individual folders below. Selecting a folder includes its descendants. Unsupported items remain browsable; no TV assignments are created.")}</Typography>
          <FormControlLabel control={<Checkbox checked={confirmLive} onChange={(_, checked) => setConfirmLive(checked)} />} label={tUi("Import selected compatible entries as permanent live channels")} />
          <Typography variant="body2">{tUi("Check this only after reviewing the selected folders. Event and VOD records are excluded. Unchecked saves the catalogue and keeps previously reviewed imports. New streams need review after refresh.")}</Typography>
          <FormControlLabel control={<Switch checked={refreshEnabled} disabled={!view.can_refresh} onChange={(_, checked) => setRefreshEnabled(checked)} />} label={tUi("Refresh with scheduled scraping")} />
          <Stack direction="row" spacing={1}>
            <Button variant="contained" disabled={pending || !name.trim()} onClick={() => save.mutate({ preview_token: preview.preview_token!, name, selected_branches: branches, mode, refresh_enabled: refreshEnabled, confirm_live: confirmLive })}>{confirmLive ? tUi("Save catalogue and import") : tUi("Save catalogue")}</Button>
            <Button disabled={pending} onClick={() => { setPreview(null); resetBrowse(); }}>{tUi("Discard preview")}</Button>
          </Stack>
        </Stack> : null}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
          <TextField label={tUi("Search catalogue")} value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} fullWidth />
          <TextField select label={tUi("Content type")} value={kind} onChange={(event) => { setKind(event.target.value); setPage(1); }} sx={{ minWidth: 180 }}>
            <MenuItem value="all">{tUi("All types")}</MenuItem>{Object.entries(kindLabels).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}
          </TextField>
          <TextField select label={tUi("Show")} value={historyFilter} onChange={(event) => { setHistoryFilter(event.target.value); setPage(1); }} sx={{ minWidth: 150 }}>
            <MenuItem value="all">{tUi("All entries")}</MenuItem><MenuItem value="favorites">{tUi("Favorites")}</MenuItem><MenuItem value="recent">{tUi("Recent")}</MenuItem>
          </TextField>
        </Stack>
        <FormControlLabel control={<Switch checked={showArtwork} onChange={(_, checked) => setShowArtwork(checked)} />} label={tUi("Load publisher artwork")} />
        <Typography variant="caption" component="p" color="text.secondary" sx={{ mb: 2 }}>{tUi("Artwork loads from publishers in this browser. Favorites and the last 100 accessed items stay in this browser only.")}</Typography>
        <Breadcrumbs aria-label={tUi("Catalogue folders")} sx={{ mb: 2, overflowWrap: 'anywhere' }}>
          {breadcrumbs.map((entry) => <Button key={entry.id} onClick={() => navigateFolder(entry.id)} aria-current={entry.id === folder ? 'location' : undefined}>{entry.id === 'root' ? view.name : entry.name}</Button>)}
        </Breadcrumbs>
        {folder !== 'root' ? <Button onClick={() => navigateFolder(byId.get(folder)?.parent_id ?? 'root')}>{tUi("Back to parent folder")}</Button> : null}
        {!preview && view.id && folder !== 'root' && byId.get(folder) ? <Button onClick={() => setAssignFolderEntry(byId.get(folder) ?? null)}>{tUi("Assign this folder's streams to a TV channel…")}</Button> : null}
        {preview && folder !== 'root' ? <FormControlLabel control={<Checkbox checked={branches.includes(folder) || branches.includes('root')} disabled={branches.includes('root')}
          onChange={(_, checked) => setBranches(checked ? [...branches, folder] : branches.filter((id) => id !== folder))} />} label={tUi("Include {{value0}}", { value0: byId.get(folder)?.name ?? 'this folder' })} /> : null}
        {search || kind !== 'all' || historyFilter !== 'all' ? <Typography variant="body2">{tUi("Showing matches across all folders.")}</Typography> : null}
        <List disablePadding aria-label={tUi("Catalogue entries")}>
          {filtered.slice((page - 1) * 50, page * 50).map((entry) => <ListItem key={entry.id} disableGutters divider sx={{ alignItems: 'flex-start' }}
            secondaryAction={!preview && view.id && entry.kind === 'folder' ? <RowActionsMenu label={tUi("More actions for {{value0}}", { value0: entry.name })} actions={[{ label: uiText("Assign streams to TV channel…"), onClick: () => setAssignFolderEntry(entry) }]} /> : undefined}>
            {preview && entry.kind === 'folder' ? <Checkbox inputProps={{ 'aria-label': `Include ${entry.name}` }} disabled={branches.includes('root')}
              checked={branches.includes(entry.id) || branches.includes('root')} onChange={(_, checked) => setBranches(checked ? [...branches, entry.id] : branches.filter((id) => id !== entry.id))} /> : null}
            <ListItemButton selected={details === entry.id} onClick={() => entry.kind === 'folder' ? navigateFolder(entry.id) : inspect(entry)} sx={{ gap: 1.5, minWidth: 0 }}>
              {showArtwork && entry.image ? <Avatar src={entry.image} alt="" imgProps={{ loading: 'lazy', referrerPolicy: 'no-referrer' }} variant="rounded" /> : entry.kind === 'folder' ? <FolderOutlined /> : null}
              <Box sx={{ minWidth: 0, flex: 1, overflowWrap: 'anywhere' }}>
                <Typography fontWeight={600}>{entry.name}</Typography>
                <Typography variant="body2" color="text.secondary">{kindLabels[entry.kind]}{entry.content_type === 'event' ? tUi(" · Event") : ''}{entry.number ? tUi(" · #{{value0}}", { value0: entry.number }) : ''} · {entry.origin}</Typography>
                {entry.reason ? <Typography variant="caption" color="text.secondary">{entry.reason}</Typography> : null}
                <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                  {entry.duplicate ? <Chip size="small" label={tUi("Duplicate source")} /> : null}{entry.retained ? <Chip size="small" label={tUi("Retained")} /> : null}
                </Stack>
              </Box>
            </ListItemButton>
          </ListItem>)}
        </List>
        {!filtered.length ? <Typography sx={{ py: 3 }}>{tUi("No entries match. Try another folder or clear the filters.")}</Typography> : null}
        {filtered.length > 50 ? <Pagination page={page} count={Math.ceil(filtered.length / 50)} onChange={(_, next) => setPage(next)} sx={{ mt: 2 }} /> : null}
      </ContentSection>
      {detail ? <Box ref={detailsRef} tabIndex={-1} sx={{ scrollMarginTop: 80 }}><ContentSection title={detail.name} actions={<Button onClick={() => setDetails(null)}>{tUi("Close details")}</Button>}>
        <Stack spacing={1.5}>
          <Typography>{detail.reason}</Typography>
          {detail.description ? <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{detail.description}</Typography> : null}
          <Typography variant="body2">{tUi("Folder:")}{' '}{byId.get(detail.parent_id ?? '')?.name ?? view.name} {' '}{tUi("· Source:")}{' '}{detail.origin}</Typography>
          {detail.guide_id ? <Typography variant="body2">{tUi("Publisher guide ID:")}{' '}{detail.guide_id} {' '}{tUi("(no assignment inferred)")}</Typography> : null}
          {detail.header_names?.length ? <Typography variant="body2">{tUi("Source headers:")}{' '}{detail.header_names.join(', ')}{tUi(". Values are private.")}</Typography> : null}
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            {detail.imported && detail.channel_id && !preview ? <Button variant="contained" onClick={() => setPlaying(detail)}>{tUi("Play source")}</Button> : null}
            {!preview && view.id && ['acestream', 'hls', 'mpegts', 'resolver'].includes(detail.kind) && detail.content_type !== 'vod' ? <Button variant="outlined" onClick={() => setEventEntry(detail)}>{tUi("Add as event")}</Button> : null}
            {!preview ? <Button startIcon={history.favorites.includes(itemKey(detail)) ? <StarRounded /> : <StarOutlineRounded />} onClick={() => favorite(detail)}>{history.favorites.includes(itemKey(detail)) ? tUi("Remove favorite") : tUi("Add favorite")}</Button> : null}
          </Stack>
          {detail.excluded_rule_ids?.length ? <Alert severity="info">{tUi("Excluded from permanent channel imports.")}{' '}<Button href={`/scraper?tab=exclusions#rule-${detail.excluded_rule_ids[0]}`}>{tUi("Review exclusion")}</Button></Alert> : null}
          {!detail.imported && detail.channel_id ? <Typography variant="body2">{tUi("Review this source as a live channel, or add it as an event to choose a broadcast in Events.")}</Typography> : null}
          {variants.length ? <Box><Typography variant="subtitle2">{tUi("Other entries with this title in the same folder")}</Typography>
            {variants.map((entry) => <Button key={entry.id} onClick={() => inspect(entry)}>{kindLabels[entry.kind]} · {entry.origin} · {entry.channel_id?.slice(-8) ?? 'unavailable'}</Button>)}
          </Box> : null}
        </Stack>
      </ContentSection></Box> : null}
    </> : null}
    {eventEntry && view?.id && !preview ? <Box ref={eventRef} tabIndex={-1} sx={{ scrollMarginTop: 80 }}><EventImportPanel key={`${view.id}:${eventEntry.id}`} zone={Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'}
      catalogue={{ id: view.id, revision: view.revision ?? 1, entryIds: [eventEntry.id], title: eventEntry.name }} onClose={() => setEventEntry(null)} /></Box> : null}
    <Button component={RouterLink} to="/events">{tUi("Open Events")}</Button>
    <ChannelPlayerDialog open={Boolean(playing)} contentId={playing?.channel_id ?? null} title={playing?.name ?? ''} onClose={() => setPlaying(null)} />
    <AssignTVChannelDialog open={Boolean(assignFolderEntry)} tvChannels={tvCatalog.data ?? []} createName={assignFolderEntry?.name}
      loading={assignFolder.isPending} error={assignFolder.isError ? getErrorMessage(assignFolder.error) : null}
      catalogLoading={tvCatalog.isLoading} catalogError={tvCatalog.isError ? uiText("Could not load TV channels.") : null} onRetry={() => void tvCatalog.refetch()}
      onClose={() => { setAssignFolderEntry(null); assignFolder.reset(); }}
      onAssign={(choice: AssignChoice) => { if (view?.id && assignFolderEntry) assignFolder.mutate({ catalogueId: view.id, folder: assignFolderEntry,
        request: 'tvChannelId' in choice ? { tv_channel_id: choice.tvChannelId, reassign: false } : { create_name: choice.createName, reassign: false } }); }} />
    {view?.id ? <FolderMatchDialog open={matchOpen} catalogueId={view.id} entries={entries ?? []} onClose={() => setMatchOpen(false)}
      onApplied={(message) => { if (view.id) invalidateAssignments(view.id); setNotice({ message }); }} /> : null}
    <Snackbar open={notice !== null} autoHideDuration={notice?.moveTo ? null : 6000} onClose={() => setNotice(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
      <Alert severity="success" onClose={() => setNotice(null)} action={notice?.moveTo ? <Button color="inherit" size="small" onClick={() => {
        const target = notice.moveTo!;
        setNotice(null);
        assignFolder.mutate({ catalogueId: target.catalogueId, folder: target.folder, request: { tv_channel_id: target.tvChannelId, reassign: true } });
      }}>{tUi("Move them too")}</Button> : undefined}>{notice?.message}</Alert>
    </Snackbar>
    <ConfirmDialog open={confirmRemove} title={tUi("Remove catalogue?")} confirmLabel={tUi("Remove catalogue")} danger busy={remove.isPending} body="Remove this catalogue and its refresh settings. Imported channels and manual assignments are kept; manage them in Acestream Channels." onConfirm={() => { if (view?.id) remove.mutate(view.id); }} onClose={() => setConfirmRemove(false)} />
  </Box>;
};
export default Catalogues;
