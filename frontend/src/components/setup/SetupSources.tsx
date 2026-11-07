import React, { useState } from 'react';
import { Alert, Box, Button, FormControl, InputLabel, MenuItem, Select, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useURLs } from '../../hooks/useScrapers';
import { scraperService, type ScrapedURL } from '../../services/scraperService';
import { getErrorMessage } from '../../utils/errorUtils';

export default function SetupSources({ active, onBusyChange }: { active: boolean; onBusyChange: (busy: boolean) => void }) {
  const client = useQueryClient();
  const sources = useURLs(undefined, { enabled: active });
  const [address, setAddress] = useState('');
  const [showProviders, setShowProviders] = useState(false);
  const [notice, setNotice] = useState<{ text: string; severity: 'success' | 'warning' | 'error' } | null>(null);
  const providers = useQuery({ queryKey: ['builtin-providers'], queryFn: scraperService.getProviders, enabled: active && showProviders });
  const importSource = useMutation({
    mutationFn: async (existing?: ScrapedURL) => {
      onBusyChange(true);
      setNotice(null);
      let source = existing ?? sources.data?.find(item => item.url === address.trim());
      if (!source) {
        const created = await scraperService.createURL({ url: address.trim(), url_type: 'auto', enabled: true });
        client.setQueryData<ScrapedURL[]>(['urls', undefined], previous => [...(previous ?? []), created]);
        source = created;
      }
      setAddress('');
      return scraperService.scrapeURL(source.id);
    },
    onSuccess: result => setNotice({
      severity: !result.success ? 'error' : result.channels_found ? 'success' : 'warning',
      text: !result.success ? `Source saved, but channels could not be read. ${result.error || 'Check the address or try again.'}`
        : result.channels_found ? `Found ${result.channels_found} channels. You can add another source or continue.`
          : 'Source saved, but no channels were found. Check that the link contains a channel list, or try another source.',
    }),
    onError: error => setNotice({ severity: 'error', text: `Could not finish adding channels. ${getErrorMessage(error)}` }),
    onSettled: () => {
      onBusyChange(false);
      for (const key of ['urls', 'channels', 'acestreamChannels', 'channel-sources']) void client.invalidateQueries({ queryKey: [key] });
    },
  });
  return <Stack spacing={2.5}>
    <Typography>Paste a link to a page or playlist that lists your channels. We&apos;ll read it and add the channels we find. This link is called a <strong>source</strong>.</Typography>
    <Box component="form" onSubmit={event => { event.preventDefault(); if (address.trim() && !importSource.isPending && sources.isSuccess) importSource.mutate(undefined); }}>
      <TextField fullWidth label="Channel source link" placeholder="https://…" value={address} disabled={importSource.isPending}
        onChange={event => setAddress(event.target.value)} helperText="Use a channel-list link from your provider or a source you have permission to use." inputProps={{ maxLength: 4096 }} />
      <Button type="submit" variant="contained" sx={{ mt: 2 }} disabled={!address.trim() || importSource.isPending || !sources.isSuccess}>{importSource.isPending ? 'Finding channels…' : 'Add source and find channels'}</Button>
    </Box>
    {importSource.isPending ? <Typography role="status">Reading the source. This can take a little while.</Typography> : null}
    {notice ? <Alert severity={notice.severity}>{notice.text}</Alert> : null}
    <Box>
      <Button aria-expanded={showProviders} onClick={() => setShowProviders(value => !value)}>Choose a built-in broadcaster</Button>
      {showProviders ? <>
        {providers.isError ? <Alert severity="error">Could not load broadcasters. <Button onClick={() => void providers.refetch()}>Try again</Button></Alert> : null}
        <FormControl fullWidth sx={{ mt: 2 }}><InputLabel id="setup-broadcaster-label">Broadcaster</InputLabel>
          <Select labelId="setup-broadcaster-label" label="Broadcaster" value={providers.data?.find(provider => provider.url === address)?.id ?? ''} disabled={importSource.isPending || providers.isPending}
            onChange={event => setAddress(providers.data?.find(provider => provider.id === event.target.value)?.url ?? '')}>
            <MenuItem value="">Choose a broadcaster</MenuItem>{providers.data?.map(provider => <MenuItem key={provider.id} value={provider.id}>{provider.name}</MenuItem>)}
          </Select>
        </FormControl>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Choosing one fills in the link. Add it when you&apos;re ready. Availability may depend on your region.</Typography>
      </> : null}
    </Box>
    {sources.isPending ? <Typography role="status">Loading your saved sources…</Typography> : null}
    {sources.isError ? <Alert severity="error">Could not load your saved sources. <Button onClick={() => void sources.refetch()}>Try again</Button></Alert> : null}
    {sources.data?.length ? <Box><Typography component="h3" variant="subtitle1" sx={{ mb: 1 }}>Your sources</Typography>
      <Stack component="ul" spacing={1.5} sx={{ listStyle: 'none', p: 0, m: 0 }}>{sources.data.map(source => <Box component="li" key={source.id} sx={{ overflowWrap: 'anywhere' }}>
        <Typography>{source.name || source.url}</Typography>
        <Typography variant="body2" color="text.secondary">{source.last_processed ? source.status === 'OK' ? source.channels_found == null ? 'Channels imported' : `${source.channels_found} channels found` : 'Could not read channels on the last attempt' : 'Saved — channels have not been read yet'}{source.enabled ? '' : ' · Automatic updates are paused'}</Typography>
        <Button disabled={importSource.isPending} onClick={() => importSource.mutate(source)}>Find channels</Button>
      </Box>)}</Stack>
    </Box> : null}
    <Typography variant="body2" color="text.secondary">Sources are saved as you add them. You can manage them later in Scraper.</Typography>
  </Stack>;
}
