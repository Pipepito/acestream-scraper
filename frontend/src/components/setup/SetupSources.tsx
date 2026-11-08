import { useUnsavedChanges } from '../UnsavedChanges';
import { Alert,Box,Button,Stack,Typography } from '@mui/material';
import { useMutation,useQueryClient } from '@tanstack/react-query';
import React,{ useEffect,useRef,useState } from 'react';
import { useURLs } from '../../hooks/useScrapers';
import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import { scraperService,type ScrapedURL } from '../../services/scraperService';
import { getErrorMessage } from '../../utils/errorUtils';
import SourceEditor from '../scraper/SourceEditor';

export default function SetupSources({ active, onBusyChange }: { active: boolean; onBusyChange: (busy: boolean) => void }) {
  const tUi = useUiText();
  const client = useQueryClient();
  const sources = useURLs(undefined, { enabled: active });
  const [savingSource, setSavingSource] = useState(false);
  const [notice, setNotice] = useState<{ text: string; severity: 'success' | 'warning' | 'error'; diagnostic?: string } | null>(null);
  const importing = useRef(false);
  const importSource = useMutation({
    mutationFn: async (source: ScrapedURL) => {
      setNotice(null);
      return scraperService.scrapeURL(source.id);
    },
    onSuccess: result => setNotice({
      severity: !result.success ? 'error' : result.channels_found ? 'success' : 'warning',
      diagnostic: !result.success ? result.error : undefined,
      text: !result.success ? tUi('Source saved, but channels could not be read. Check the address or try again.')
        : result.channels_found ? tUi('sourceImportCount', { count: result.channels_found })
          : uiText("Source saved, but no channels were found. Check that the link contains a channel list, or try another source."),
    }),
    onError: error => setNotice({ severity: 'error', text: tUi('Could not finish adding channels. {{error}}', { error: getErrorMessage(error) }) }),
    onSettled: () => {
      importing.current = false;
      for (const key of ['urls', 'channels', 'acestreamChannels', 'channel-sources']) void client.invalidateQueries({ queryKey: [key] });
    },
  });
  useUnsavedChanges(false, importSource.isPending);
  const runImport = (source: ScrapedURL) => { if (!importing.current) { importing.current = true; importSource.mutate(source); } };
  useEffect(() => { onBusyChange(savingSource || importSource.isPending); }, [savingSource, importSource.isPending, onBusyChange]);
  return <Stack spacing={2.5}>
    <Typography>{tUi("Paste a link to a page or playlist that lists your channels. We'll read it and add the channels we find. This link is called a")}{' '}<strong>{tUi("source")}</strong>.</Typography>
    <SourceEditor active={active} disabled={importSource.isPending || !sources.isSuccess} reuseSources={sources.data}
      onSavingChange={setSavingSource} submitLabel={importSource.isPending ? tUi('Finding channels…') : tUi('Add source and find channels')}
      onSaved={source => { client.setQueryData<ScrapedURL[]>(['urls', undefined], previous => previous?.some(item => item.id === source.id) ? previous : [...(previous ?? []), source]); runImport(source); }} />
    {importSource.isPending ? <Typography role="status">{tUi("Reading the source. This can take a little while.")}</Typography> : null}
    {notice ? <Alert severity={notice.severity}>{notice.text}{notice.diagnostic ? <details><summary>{tUi("Original diagnostic")}</summary><Box sx={{ overflowWrap: "anywhere" }}>{notice.diagnostic}</Box></details> : null}</Alert> : null}
    {sources.isPending ? <Typography role="status">{tUi("Loading your saved sources…")}</Typography> : null}
    {sources.isError ? <Alert severity="error">{tUi("Could not load your saved sources.")}{' '}<Button onClick={() => void sources.refetch()}>{tUi("Try again")}</Button></Alert> : null}
    {sources.data?.length ? <Box><Typography component="h3" variant="subtitle1" sx={{ mb: 1 }}>{tUi("Your sources")}</Typography>
      <Stack component="ul" spacing={1.5} sx={{ listStyle: 'none', p: 0, m: 0 }}>{sources.data.map(source => <Box component="li" key={source.id} sx={{ overflowWrap: 'anywhere' }}>
        <Typography>{source.name || source.url}</Typography>
        <Typography variant="body2" color="text.secondary">{source.last_processed ? source.status === 'OK' ? source.channels_found == null ? tUi("Channels imported") : tUi("{{value0}} channels found", { value0: source.channels_found }) : tUi("Could not read channels on the last attempt") : tUi("Saved — channels have not been read yet")}{source.enabled ? '' : tUi(" · Automatic updates are paused")}</Typography>
        <Button disabled={importSource.isPending || savingSource} onClick={() => runImport(source)}>{tUi("Find channels")}</Button>
      </Box>)}</Stack>
    </Box> : null}
    <Typography variant="body2" color="text.secondary">{tUi("Sources are saved as you add them. You can manage them later in Scraper.")}</Typography>
  </Stack>;
}
