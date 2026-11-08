import { Alert,Box,Button,Checkbox,FormControl,FormControlLabel,InputLabel,Link,MenuItem,Select,Stack,Typography } from '@mui/material';
import { useMutation,useQueryClient } from '@tanstack/react-query';
import React,{ useEffect,useState } from 'react';
import { useCreateEPGSource,useEPGSources } from '../../hooks/useEPG';
import { useEPGMatchAnalysis } from '../../hooks/useEPGMatchAnalysis';
import { useEPGSourceManagement } from '../../hooks/useEPGSourceManagement';
import { type SnackbarSeverity } from '../../hooks/useSnackbar';
import { useUiText } from '../../i18n/useUiText';
import { epgProviders } from '../../services/epgProviders';
import { type CreateEPGSourceDTO,type EPGSource } from '../../services/epgService';
import { getErrorMessage } from '../../utils/errorUtils';
import GuideSourceFields from '../GuideSourceFields';
import { useUnsavedChanges } from '../UnsavedChanges';

export default function SetupGuide({ active, onBusyChange }: { active: boolean; onBusyChange: (busy: boolean) => void }) {
  const tUi = useUiText();
  const client = useQueryClient();
  const sources = useEPGSources({ enabled: active });
  const [selectedId, setSelectedId] = useState<number>();
  const [custom, setCustom] = useState(false);
  const [address, setAddress] = useState('');
  const [name, setName] = useState('');
  const [enabled, setEnabled] = useState(true);
  const create = useCreateEPGSource();
  const [visible, setVisible] = useState(20);
  const [notice, setNotice] = useState<{ text: string; severity: SnackbarSeverity } | null>(null);
  const showNotice = (text: string, severity: SnackbarSeverity) => setNotice({ text, severity });
  const refresh = useEPGSourceManagement(showNotice);
  const matches = useEPGMatchAnalysis(selectedId, showNotice);
  const add = useMutation({
    mutationFn: async (data: CreateEPGSourceDTO) => {
      const existing = sources.data?.find(source => source.url === data.url);
      const source = existing ?? await create.mutateAsync(data);
      client.setQueryData<EPGSource[]>(['epg-sources'], previous => [...(previous ?? []).filter(item => item.id !== source.id), source]);
      setSelectedId(source.id);
      setName(''); setAddress('');
      setNotice(null);
      if (!source.last_updated || source.last_error) void refresh.handleRefreshSourceClick(source.id);
      return source;
    },
    onError: error => showNotice(`Could not add this guide. ${getErrorMessage(error)}`, 'error'),
    onSettled: () => { void client.invalidateQueries({ queryKey: ['epg-sources'] }); },
  });
  // A background download can continue after leaving setup. Writes and reviewed
  // matching stay on this step until the response is known.
  const busy = add.isPending || matches.isAnalyzingMatches || matches.isApplyingMatches;
  useEffect(() => { onBusyChange(busy); }, [busy, onBusyChange]);
  useUnsavedChanges(Boolean(name || address), busy);
  const downloading = refresh.refreshingSourceId !== null;
  const selected = sources.data?.find(source => source.id === selectedId);
  const ready = Boolean(selected?.last_updated && !selected.last_error && !downloading);
  const rows = matches.matchAnalysis?.rows.filter(row => row.can_apply ?? row.is_creatable) ?? [];
  return <Stack spacing={2.5}>
    <Typography>{tUi("A programme guide adds show names and times to your channels. It does not provide streams. You can skip this and add one later.")}</Typography>
    {sources.isPending ? <Typography role="status">{tUi("Loading your guides…")}</Typography> : null}
    {sources.isError ? <Alert severity="error">{tUi("Could not load your guides.")}{' '}<Button onClick={() => void sources.refetch()}>{tUi("Try again")}</Button></Alert> : null}
    {!selected ? <>
      {epgProviders.map(provider => <Box key={provider.id}>
        <Typography component="h3" variant="subtitle1">{provider.name}</Typography>
        <Typography variant="body2" color="text.secondary">{provider.description}</Typography>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 1 }}>
          <Button variant="contained" disabled={busy || downloading || !sources.isSuccess} onClick={() => add.mutate({ name: provider.name, url: provider.url, enabled: true })}>{tUi("Use")}{' '}{provider.name}</Button>
          <Link href={provider.website} target="_blank" rel="noopener noreferrer">{tUi("About this guide")}</Link>
        </Stack>
      </Box>)}
      <Button aria-expanded={custom} onClick={() => setCustom(value => !value)}>{tUi("Use another guide")}</Button>
      {custom ? <Box component="form" onSubmit={event => { event.preventDefault(); if (name.trim() && address.trim() && !busy && sources.isSuccess) add.mutate({ name: name.trim(), url: address.trim(), enabled }); }}>
        <Stack spacing={2}><GuideSourceFields value={{ name, url: address, enabled }} disabled={busy} onChange={event => {
          if (event.target.name === 'name') setName(event.target.value);
          else if (event.target.name === 'url') setAddress(event.target.value);
          else if (event.target.name === 'enabled') setEnabled(event.target.checked);
        }} />
          <Button type="submit" variant="contained" disabled={busy || !sources.isSuccess || !name.trim() || !address.trim()}>{tUi("Add programme guide")}</Button>
        </Stack>
      </Box> : null}
    </> : null}
    {sources.data?.length ? <FormControl fullWidth><InputLabel id="setup-guide-label">{tUi("Saved programme guide")}</InputLabel>
      <Select labelId="setup-guide-label" label={tUi("Saved programme guide")} value={selectedId ?? ''} disabled={busy || downloading} onChange={event => { setSelectedId(Number(event.target.value) || undefined); setNotice(null); setVisible(20); }}>
        <MenuItem value="">{tUi("Choose or add a guide")}</MenuItem>{sources.data.map(source => <MenuItem key={source.id} value={source.id}>{source.name}</MenuItem>)}
      </Select>
    </FormControl> : null}
    {notice ? <Alert severity={notice.severity}>{notice.text}</Alert> : null}
    {selected ? <>
      {downloading ? <Typography role="status">{tUi("Downloading programme times. Large guides can take a few minutes. You can finish setup while this continues, then match channels in EPG.")}</Typography> : <>
        {selected.last_error ? <Alert severity="warning">{tUi("The guide could not be downloaded. Try again or choose another guide.")}</Alert> : null}
        {!ready ? <Button disabled={busy} onClick={() => void refresh.handleRefreshSourceClick(selected.id)}>{tUi("Download programme times")}</Button> : <Button variant="contained" disabled={busy} onClick={() => { setVisible(20); setNotice(null); void matches.handleAnalyzeMatches(); }}>{matches.isAnalyzingMatches ? tUi("Finding matches…") : tUi("Find matching channels")}</Button>}
      </>}
      {matches.matchAnalysis ? <Box>
        <Typography component="h3" variant="subtitle1">{tUi("Review channel matches")}</Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>{tUi("Select the matches you want to keep. This connects your streams to the guide and creates TV channels where needed.")}</Typography>
        {!rows.length ? <Alert severity="info">{tUi("No new matches to apply. Your channels may already be linked, or their names may differ from this guide. You can review all channels in EPG later.")}</Alert> : <>
          <Stack spacing={1}>{rows.slice(0, visible).map(row => <Box key={row.epg_channel_id} sx={{ overflowWrap: 'anywhere' }}>
            <FormControlLabel control={<Checkbox checked={matches.selectedMatchRowIds.includes(row.epg_channel_id)} disabled={busy} onChange={() => matches.handleToggleMatchRow(row)} />} label={row.epg_channel_name} />
            <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>{tUi("Your streams:")}{' '}{row.candidates.map(candidate => candidate.name).join(', ')}</Typography>
          </Box>)}</Stack>
          {visible < rows.length ? <Button onClick={() => setVisible(count => count + 20)}>{tUi("Show more matches (")}{rows.length - visible} {' '}{tUi("remaining)")}</Button> : null}
          <Button variant="contained" sx={{ mt: 2 }} disabled={busy || !matches.selectedMatchRowIds.length} onClick={() => void matches.handleCreateMatchedTVChannels()}>{matches.isApplyingMatches ? tUi("Saving matches…") : tUi("Save selected matches ({{value0}})", { value0: matches.selectedMatchRowIds.length })}</Button>
        </>}
      </Box> : null}
    </> : null}
    <Typography variant="body2" color="text.secondary">{tUi("Guides are saved when you add them. Matching is optional and always needs your selection.")}</Typography>
  </Stack>;
}
