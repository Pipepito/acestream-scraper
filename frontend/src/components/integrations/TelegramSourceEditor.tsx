import { useUiText } from '../../i18n/useUiText';
import React, { lazy, Suspense, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import type { TelegramSource, TelegramSourceCreate, TelegramService, TelegramPreview } from '../../services/telegramService';
import type { ExtractionRecipe } from '../../recipes/types';
import apiClient from '../../services/apiClient';
import type { RecipePreview } from '../../recipes/types';
import { telegramError as getErrorMessage } from '../../services/telegramService';
const RecipeBuilder = lazy(() => import('../../recipes/RecipeBuilder'));

interface Props { api: TelegramService; source?: TelegramSource; onSaved: () => Promise<void>; onCancel: () => void }
export default function TelegramSourceEditor({ api, source, onSaved, onCancel }: Props) {
  const tUi = useUiText();
  const [form, setForm] = useState<TelegramSourceCreate>(() => ({ name: source?.name ?? '', chat_id: source?.chat_id ?? '',
    topic_id: source?.topic_id, enabled: source?.enabled ?? true, sender_ids: source?.sender_ids ?? [],
    sender_rule: source?.sender_rule ?? 'posting', include_forwards: source?.include_forwards ?? true,
    include: source?.include ?? '', exclude: source?.exclude ?? '', filter_mode: source?.filter_mode ?? 'keyword',
    bare_ids: source?.bare_ids ?? true, recipe: source?.recipe ?? null }));
  const [username, setUsername] = useState('');
  const [senderInput, setSenderInput] = useState((source?.sender_ids ?? []).join(', '));
  const [senderLabels, setSenderLabels] = useState(source?.sender_labels ?? {});
  const [recipeOpen, setRecipeOpen] = useState(false);
  const [preset, setPreset] = useState<ExtractionRecipe | null>(null);
  const [preview, setPreview] = useState<TelegramPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const chats = useQuery({ queryKey: ['telegram', 'chats'], queryFn: api.chats, retry: false });
  const topics = useQuery({ queryKey: ['telegram', 'topics', form.chat_id], queryFn: () => api.topics(form.chat_id), enabled: !!form.chat_id, retry: false });
  const update = <K extends keyof TelegramSourceCreate>(key: K, value: TelegramSourceCreate[K]) => {
    setForm(previous => ({ ...previous, [key]: value })); setPreview(null);
  };
  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError('');
    try { await action(); } catch (cause) { setError(getErrorMessage(cause)); } finally { setBusy(false); }
  };
  const resolve = () => run(async () => {
    const peer = await api.resolve(username);
    const ids = Array.from(new Set([...(form.sender_ids ?? []), peer.id]));
    update('sender_ids', ids);
    setSenderInput(ids.join(', '));
    setSenderLabels(previous => ({ ...previous, [peer.id]: peer.label })); setUsername('');
  });
  return <Stack spacing={2} component="section" aria-label={source ? tUi("Edit Telegram source") : tUi("Add Telegram source")}>
    <Typography variant="h6">{source ? tUi("Edit source") : tUi("Add a Telegram source")}</Typography>
    {error && <Alert severity="error">{error}</Alert>}
    {chats.error && <Alert severity="error">{getErrorMessage(chats.error)}</Alert>}
    <Box component="fieldset" disabled={busy} sx={{ border: 0, p: 0, m: 0, minWidth: 0 }}>
      <Stack spacing={2}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField fullWidth label={tUi("Source name")} value={form.name} inputProps={{ maxLength: 100 }} onChange={event => update('name', event.target.value)} />
          <TextField fullWidth select label={tUi("Joined chat")} value={form.chat_id} disabled={!!source} onChange={event => { update('chat_id', event.target.value); update('topic_id', null); }}>
            {(chats.data ?? []).map(chat => <MenuItem key={chat.id} value={chat.id}>{chat.label} ({chat.id})</MenuItem>)}
          </TextField>
        </Stack>
        <Button onClick={() => void chats.refetch()} sx={{ alignSelf: 'flex-start' }}>{tUi("Refresh joined chats")}</Button>
        <Typography variant="body2" color="text.secondary">{tUi("Only joined groups and channels are listed (up to 500). This app never joins chats for you.")}</Typography>
        {topics.error && <Alert severity="error">{getErrorMessage(topics.error)}</Alert>}
        {(topics.data?.length ?? 0) > 0 && <TextField select label={tUi("Topic")} value={form.topic_id ?? ''} onChange={event => update('topic_id', event.target.value ? Number(event.target.value) : null)}>
          <MenuItem value="">{tUi("All topics")}</MenuItem>{topics.data?.map(topic => <MenuItem key={topic.id} value={topic.id}>{topic.label}</MenuItem>)}
        </TextField>}
        <Typography variant="subtitle2">{tUi("Allowed senders")}</Typography>
        <Typography variant="body2">{tUi("An empty list accepts all senders. Usernames resolve to stable identities; names and signatures in message text do not count.")}</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth label={tUi("Telegram username")} value={username} onChange={event => setUsername(event.target.value)} />
          <Button disabled={!username.trim()} onClick={() => void resolve()}>{tUi("Resolve and add")}</Button>
        </Stack>
        <TextField label={tUi("Allowed sender IDs")} value={senderInput} helperText={tUi("Comma-separated user or channel IDs. Clear to accept all senders.")} onChange={event => {
          setSenderInput(event.target.value);
          update('sender_ids', Array.from(new Set(event.target.value.split(',').map(value => value.trim()).filter(Boolean))));
        }} />
        {(form.sender_ids ?? []).map(id => <Typography key={id} variant="body2">{senderLabels[id] ?? 'Telegram identity'} · {id}</Typography>)}
        <FormControlLabel control={<Checkbox checked={form.include_forwards ?? true} onChange={event => update('include_forwards', event.target.checked)} />} label={tUi("Include forwarded messages")} />
        <TextField select label={tUi("Sender identity for forwards")} value={form.sender_rule ?? 'posting'} onChange={event => update('sender_rule', event.target.value as 'posting' | 'original')}>
          <MenuItem value="posting">{tUi("Account posting in the selected chat")}</MenuItem><MenuItem value="original">{tUi("Original author, when Telegram identifies them")}</MenuItem>
        </TextField>
        <Alert severity="info">{tUi("Anonymous admins and broadcast posts can identify a group or channel. A human-only allowlist skips these posts. Hidden original authors never match an allowlist.")}</Alert>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField select fullWidth label={tUi("Message filter mode")} value={form.filter_mode ?? 'keyword'} onChange={event => update('filter_mode', event.target.value as 'keyword' | 'regex')}><MenuItem value="keyword">{tUi("Keywords")}</MenuItem><MenuItem value="regex">{tUi("Bounded regular expressions")}</MenuItem></TextField>
          <TextField fullWidth label={tUi("Must include")} value={form.include ?? ''} onChange={event => update('include', event.target.value)} inputProps={{ maxLength: 512 }} />
          <TextField fullWidth label={tUi("Must exclude")} value={form.exclude ?? ''} onChange={event => update('exclude', event.target.value)} inputProps={{ maxLength: 512 }} />
        </Stack>
        <FormControlLabel control={<Checkbox checked={form.bare_ids ?? true} onChange={event => update('bare_ids', event.target.checked)} />} label={tUi("Recognize bare 40-character IDs in name/ID pairs")} />
        <Typography variant="body2">{tUi("Extraction:")}{' '}{form.recipe ? tUi("Custom recipe") : tUi("Automatic name/ID pairs and AceStream links")}</Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button onClick={() => void run(async () => { setPreset(await api.preset()); setRecipeOpen(true); })}>{tUi("Edit extraction recipe")}</Button>
          {form.recipe && <Button onClick={() => update('recipe', null)}>{tUi("Use automatic extraction")}</Button>}
        </Stack>
        {recipeOpen && <Suspense fallback={<Typography>{tUi("Loading recipe builder…")}</Typography>}><RecipeBuilder
          initialRecipe={(form.recipe as ExtractionRecipe | null) ?? preset} sourceIdentity={`telegram-${source?.id ?? 'new'}`}
          preview={async (recipe, sample) => (await apiClient.post<RecipePreview>('/v1/scrapers/recipes/preview', { recipe, sample })).data}
          onSave={async recipe => { update('recipe', recipe); setRecipeOpen(false); }}
        /></Suspense>}
        {!source && <>
          <TextField type="number" label={tUi("Initial history count")} value={form.history_count ?? 0} inputProps={{ min: 0, max: 1000 }} onChange={event => update('history_count', Number(event.target.value))} helperText={tUi("0 starts with new messages only. Opt in to at most 1,000 recent messages.")} />
          {(form.history_count ?? 0) > 0 && <TextField type="datetime-local" label={tUi("Ignore history before (local time)")} InputLabelProps={{ shrink: true }} onChange={event => update('history_since', event.target.value ? new Date(event.target.value).toISOString() : null)} />}
        </>}
        <Button variant="outlined" disabled={!form.chat_id} onClick={() => void run(async () => { setPreview(await api.preview(form)); })}>{tUi("Test against recent messages")}</Button>
        {preview && <Stack spacing={1} aria-label={tUi("Telegram preview results")}>
          <Typography variant="subtitle2">{tUi("Preview only · no catalogue changes")}</Typography>
          {preview.messages.length === 0 && <Typography>{tUi("No recent messages.")}</Typography>}
          {preview.messages.map(message => <Box key={message.message_id} sx={{ borderBottom: 1, borderColor: 'divider', py: 1, overflowWrap: 'anywhere' }}>
            <Typography variant="body2">{tUi("Message")}{' '}{message.message_id} {' '}{tUi("· sender")}{' '}{message.sender_id ?? 'unverified'} · {message.outcome} · {message.result.duplicate_count} {' '}{tUi("duplicates ·")}{' '}{message.result.invalid_count} {' '}{tUi("invalid")}</Typography>
            {message.result.channels.map(channel => <Typography key={channel.channel_id} variant="body2">{channel.name} — {channel.channel_id}{message.excluded_rule_ids?.[channel.channel_id]?.length ? <Button href={`/scraper?tab=exclusions#rule-${message.excluded_rule_ids[channel.channel_id][0]}`}>{tUi("Excluded · Review rule")}</Button> : null}</Typography>)}
          </Box>)}
        </Stack>}
        <Stack direction="row" spacing={1}><Button variant="contained" disabled={!form.name.trim() || !form.chat_id} onClick={() => void run(async () => { await api.save(form, source?.id); await onSaved(); })}>{tUi("Save source")}</Button><Button onClick={onCancel}>{tUi("Cancel")}</Button></Stack>
      </Stack>
    </Box>
  </Stack>;
}
