import { useUnsavedChanges } from '../components/UnsavedChanges';
import { getErrorMessage } from '../utils/errorUtils';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, MenuItem, Stack, TextField } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import RecipeBuilder from '../recipes/RecipeBuilder';
import { ExtractionRecipe, RecipePreview } from '../recipes/types';
import { scraperService, ScrapedURL } from '../services/scraperService';
import apiClient from '../services/apiClient';

export default function ExtractionBuilder() {
  const [params] = useSearchParams();
  const id = Number(params.get('source')) || null;
  return <SourceBuilderPage key={id ?? 'new'} id={id} />;
}

function SourceBuilderPage({ id }: { id: number | null }) {
  const tUi = useUiText();
  const [source, setSource] = useState<ScrapedURL | null>(null);
  const [url, setUrl] = useState('');
  const [urlType, setUrlType] = useState('auto');
  const [savedId, setSavedId] = useState<number | null>(id);
  const [error, setError] = useState<unknown>(null);
  const [builderState, setBuilderState] = useState({ dirty: false, pending: false });
  const [baseline, setBaseline] = useState({ url: '', type: 'auto' });
  useUnsavedChanges(builderState.dirty || url !== baseline.url || urlType !== baseline.type, builderState.pending);
  const [ready, setReady] = useState(!id);
  const queries = useQueryClient();
  useEffect(() => {
    let cancelled = false;
    if (id) scraperService.getURL(id).then(value => {
      if (!cancelled) { setSource(value); setBaseline({ url: value.url, type: value.url_type }); setUrl(value.url); setUrlType(value.url_type); setReady(true); }
    }).catch(cause => { if (!cancelled) setError(cause); });
    return () => { cancelled = true; };
  }, [id]);
  const save = async (recipe: ExtractionRecipe | null) => {
    if (!url.trim()) throw new Error('Enter a source URL before saving');
    const value = savedId ? await scraperService.updateURL(savedId, { url, url_type: urlType, extraction_recipe: recipe })
      : await scraperService.createURL({ url, url_type: urlType, extraction_recipe: recipe });
    setSavedId(value.id); setSource(value); setBaseline({ url, type: urlType });
    await queries.invalidateQueries({ queryKey: ['urls'] });
  };
  return <Box>
    <PageHeader title={tUi("Extraction builder")} subtitle={tUi("Configure a source without changing scraper code.")} actions={<Button component={RouterLink} to="/scraper">{tUi("Back to sources")}</Button>} />
    <Stack spacing={3}>
      {error !== null && <Alert severity="error">{getErrorMessage(error)}</Alert>}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField disabled={builderState.pending} label={tUi("Source URL")} value={url} onChange={e => setUrl(e.target.value)} fullWidth />
        <TextField select disabled={builderState.pending} label={tUi("Source type")} value={urlType} onChange={e => setUrlType(e.target.value)} sx={{ minWidth: 170 }}>
          <MenuItem value="auto">{tUi("Auto-detect")}</MenuItem><MenuItem value="regular">{tUi("HTTP")}</MenuItem><MenuItem value="zeronet">{tUi("ZeroNet")}</MenuItem><MenuItem value="ipfs">{tUi("IPFS")}</MenuItem>
        </TextField>
      </Stack>
      {ready && <RecipeBuilder key={id ?? 'new'} sourceIdentity={`${url}:${urlType}`} initialRecipe={source?.extraction_recipe} onDraftState={setBuilderState} onSave={save}
        fetchSample={async () => (await apiClient.post<{ sample: string }>('/v1/scrapers/recipes/sample', { url, url_type: urlType })).data.sample}
        preview={async (recipe, sample) => (await apiClient.post<RecipePreview>('/v1/scrapers/recipes/preview', { recipe, sample })).data} />}
    </Stack>
  </Box>;
}
