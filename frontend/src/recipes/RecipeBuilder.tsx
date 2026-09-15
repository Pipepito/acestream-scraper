import React, { useRef, useState } from 'react';
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Chip, LinearProgress, Link, MenuItem, Stack, Tab, Tabs, TextField, Typography } from '@mui/material';
import catalogue from './catalogue.json';
import { validateRecipe, checkSample } from './engine';
import { emptyField, ExtractionRecipe, FieldName, fieldLabels, MAX_RECIPE_BYTES, MAX_SAMPLE_BYTES, newRecipe, RecipePreview } from './types';
import RecipeFields from './RecipeFields';
import RecipeResults from './RecipeResults';
import VisualPicker from './VisualPicker';
import JsonPicker from './JsonPicker';
import { sourceRules, SourceFieldSelection } from './sourceRules';

interface Props {
  initialRecipe?: ExtractionRecipe | null;
  sourceIdentity?: string;
  preview: (recipe: ExtractionRecipe, sample: string) => Promise<RecipePreview>;
  fetchSample?: () => Promise<string>;
  onSave?: (recipe: ExtractionRecipe | null) => Promise<void>;
}
function download(name: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default function RecipeBuilder({ initialRecipe, sourceIdentity, preview, fetchSample, onSave }: Props) {
  const [recipe, setRecipe] = useState<ExtractionRecipe>(initialRecipe ?? newRecipe());
  const [sample, setSample] = useState('');
  const [pastedRecipe, setPastedRecipe] = useState('');
  const [view, setView] = useState('source');
  const [target, setTarget] = useState<FieldName | 'records'>('records');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [result, setResult] = useState<RecipePreview | null>(null);
  const [tested, setTested] = useState('');
  const [rawTemplate, setRawTemplate] = useState<{ text: string; start: number; fields: SourceFieldSelection[] } | null>(null);
  const [selection, setSelection] = useState({ start: 0, end: 0, text: '' });
  const source = useRef<HTMLTextAreaElement>(null);
  const sampleInput = useRef<HTMLInputElement>(null);
  const recipeInput = useRef<HTMLInputElement>(null);
  const [template, setTemplate] = useState('');
  const [testedSource, setTestedSource] = useState<string | undefined>();
  const revision = useRef(0);
  const changeRecipe = (next: ExtractionRecipe) => { revision.current++; setRecipe(next); setResult(null); setTested(''); setNotice(''); };
  const changeSample = (next: string) => { checkSample(next); revision.current++; setSample(next); setRawTemplate(null); setSelection({ start: 0, end: 0, text: '' }); setResult(null); setTested(''); setNotice(''); };
  const run = async (action: () => Promise<void>) => {
    setError(''); setNotice(''); setBusy(true);
    try { await action(); } catch (cause) { setError((cause as Error).message); } finally { setBusy(false); }
  };
  const readFile = async (file: File | undefined, isRecipe: boolean) => {
    if (!file) return;
    await run(async () => {
      if (file.size > (isRecipe ? MAX_RECIPE_BYTES : MAX_SAMPLE_BYTES)) throw new Error(isRecipe ? 'Recipe exceeds 512 KiB' : 'Sample exceeds 32 MiB');
      const text = await file.text();
      if (isRecipe) changeRecipe(validateRecipe(JSON.parse(text)));
      else changeSample(text);
    });
  };
  const assignVisual = (selector: string, attribute: string, value: string) => {
    if (target === 'records') changeRecipe({ ...recipe, records: selector });
    else changeRecipe({ ...recipe, fields: { ...recipe.fields, [target]: { ...emptyField(), ...recipe.fields[target], selector, attribute } } });
    const start = sample.indexOf(value.trim());
    if (start >= 0 && value.trim()) setSelection({ start, end: start + value.trim().length, text: value.trim() });
    setNotice(`Assigned ${target === 'records' ? 'repeating row' : fieldLabels[target]}. Test all records to check the selection.`);
  };
  const assignSource = () => {
    if (!selection.text) return;
    try {
      if (target === 'records') {
        setRawTemplate({ text: selection.text, start: selection.start, fields: [] });
        changeRecipe(sourceRules(recipe, selection.text, []));
        setNotice('Record template selected. Select its name and ID next, then test all matches.');
      } else {
        if (!rawTemplate) throw new Error('Select a whole record template first');
        const fields = [...rawTemplate.fields.filter(field => field.field !== target), { field: target, start: selection.start - rawTemplate.start, end: selection.end - rawTemplate.start }];
        changeRecipe(sourceRules(recipe, rawTemplate.text, fields));
        setRawTemplate({ ...rawTemplate, fields });
        setNotice('Rule updated for every selected field. Test all records and adjust the regex if needed.');
      }
    } catch (cause) { setError((cause as Error).message); }
  };
  return <Stack spacing={3}>
    <Stack spacing={1}>
      <Typography variant="h5" component="h2">Teach the scraper a new source</Typography>
      <Typography color="text.secondary">Provide a sample, identify a channel row and its fields, then review every extracted result.</Typography>
      <Typography variant="body2"><Link href="https://github.com/Pipepito/acestream-scraper/wiki/Extraction-Recipes" target="_blank" rel="noreferrer">Builder guide: examples, limitations and troubleshooting ↗</Link></Typography>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap"><Chip label="1 · Sample" variant="outlined" /><Chip label="2 · Fields" variant="outlined" /><Chip label="3 · Test and save" variant="outlined" /></Stack>
    </Stack>
    {busy && <LinearProgress aria-label="Working on recipe" />}
    {error && <Alert severity="error">{error}</Alert>}
    {notice && <Alert severity="success">{notice}</Alert>}
    <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField select label="Recipe catalogue" value={template} onChange={e => setTemplate(e.target.value)} fullWidth>
            <MenuItem value="">Choose a starter recipe</MenuItem>{catalogue.map(entry => <MenuItem key={entry.id} value={entry.id}>{entry.recipe.name} · v{entry.recipe.version}</MenuItem>)}
          </TextField>
          <Button disabled={!template} onClick={() => {
            const entry = catalogue.find(item => item.id === template);
            if (entry) { changeRecipe(validateRecipe(entry.recipe)); changeSample(entry.sample); setNotice(`${entry.description} By ${entry.author}.`); }
          }}>Load template and sample</Button>
        </Stack>
        <Typography variant="caption" color="text.secondary">Catalogue entries are versioned. Loading replaces this draft. These initial templates use synthetic samples, not verified websites.</Typography>
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          {fetchSample && <Button variant="contained" onClick={() => void run(async () => { changeSample(await fetchSample()); setNotice('Source fetched. Select fields and test with the backend. No channels were changed.'); })}>Load source URL</Button>}
          <Button variant="outlined" onClick={() => sampleInput.current?.click()}>Upload sample</Button>
          <Button variant="outlined" onClick={() => recipeInput.current?.click()}>Import recipe</Button>
        </Stack>
        <Accordion disableGutters elevation={0}>
          <AccordionSummary><Typography>Paste a recipe</Typography></AccordionSummary>
          <AccordionDetails><Stack spacing={1}><TextField label="Recipe JSON" multiline minRows={4} maxRows={12} value={pastedRecipe} onChange={e => setPastedRecipe(e.target.value)} fullWidth /><Button disabled={!pastedRecipe} onClick={() => void run(async () => { if (new Blob([pastedRecipe]).size > MAX_RECIPE_BYTES) throw new Error('Recipe exceeds 512 KiB'); changeRecipe(validateRecipe(JSON.parse(pastedRecipe))); setPastedRecipe(''); setNotice('Recipe imported. Test it against your sample or source URL.'); })}>Load pasted recipe</Button></Stack></AccordionDetails>
        </Accordion>
        <input ref={sampleInput} type="file" accept=".html,.htm,.txt,.json" hidden onChange={e => { void readFile(e.target.files?.[0], false); e.target.value = ''; }} />
        <input ref={recipeInput} type="file" accept=".json" hidden onChange={e => { void readFile(e.target.files?.[0], true); e.target.value = ''; }} />
        <Typography variant="body2" color="text.secondary">In your browser’s developer tools, copy the channel container’s outer HTML, or copy a JSON response from Network. You can also paste a text list. Samples stay here unless you explicitly test them in your installed app.</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="flex-start">
          <Stack spacing={2} sx={{ flex: 1, minWidth: 0, width: '100%' }}>
            <Tabs value={view} onChange={(_, value) => setView(value)} aria-label="Sample view"><Tab value="source" label="Raw source" /><Tab value="visual" label={recipe.mode === 'json' ? 'JSON fields' : 'Visual picker'} disabled={recipe.mode === 'regex'} /></Tabs>
            <TextField select label="Assign selection to" value={target} onChange={e => setTarget(e.target.value as FieldName | 'records')} fullWidth>
              <MenuItem value="records">Repeating record</MenuItem>{Object.entries(fieldLabels).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}
            </TextField>
            {view === 'source' || recipe.mode === 'regex' ? <>
              <TextField inputRef={source} label="HTML, text or JSON sample" value={sample} onChange={e => { try { changeSample(e.target.value); } catch (cause) { setError((cause as Error).message); } }} multiline minRows={12} maxRows={24} fullWidth inputProps={{ spellCheck: false, style: { fontFamily: 'monospace', fontSize: 13 } }} onSelect={() => { const node = source.current; if (node) setSelection({ start: node.selectionStart, end: node.selectionEnd, text: sample.slice(node.selectionStart, node.selectionEnd) }); }} />
              <Button disabled={!selection.text || recipe.mode === 'json'} onClick={assignSource}>Use selected text as {target === 'records' ? 'record template' : fieldLabels[target].toLowerCase()}</Button>
              <Typography variant="caption">Select a whole record first, then its name and ID. Text selections generate editable regex rules. For JSON, use the field picker.</Typography>
            </> : recipe.mode === 'json' ? <JsonPicker sample={sample} records={recipe.records} pickingRecord={target === 'records'} onPick={path => target === 'records' ? changeRecipe({ ...recipe, records: path }) : changeRecipe({ ...recipe, fields: { ...recipe.fields, [target]: { ...emptyField(), ...recipe.fields[target], path } } })} /> : <VisualPicker sample={sample} records={recipe.records} pickingRecord={target === 'records'} onPick={assignVisual} />}
          </Stack>
          <Box sx={{ flex: 1, minWidth: 0, width: '100%' }}><RecipeFields recipe={recipe} onChange={changeRecipe} /></Box>
        </Stack>
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Button variant="contained" disabled={!sample} onClick={() => void run(async () => {
            const current = revision.current;
            const validated = validateRecipe(recipe);
            const output = await preview(validated, sample);
            if (revision.current === current) { setResult(output); setTested(JSON.stringify(recipe)); setTestedSource(sourceIdentity); }
          })}>{fetchSample ? 'Test with scraper engine' : 'Test sample'}</Button>
          {fetchSample && <Button variant="outlined" onClick={() => void run(async () => {
            const validated = validateRecipe(recipe);
            const fetched = await fetchSample();
            changeSample(fetched);
            const output = await preview(validated, fetched);
            setResult(output); setTested(JSON.stringify(recipe)); setTestedSource(sourceIdentity);
          })}>Fetch and test source URL</Button>}
          <Button variant="outlined" onClick={() => void run(async () => { download('extraction-recipe.json', validateRecipe(recipe)); setNotice('Recipe exported without the sample or source URL.'); })}>Export recipe</Button>
          <Button onClick={() => void run(async () => { await navigator.clipboard.writeText(JSON.stringify(validateRecipe(recipe), null, 2)); setNotice('Recipe copied. Import or paste it into your scraper.'); })}>Copy recipe</Button>
          {onSave && <Button variant="contained" color="secondary" disabled={tested !== JSON.stringify(recipe) || testedSource !== sourceIdentity || !result?.channels.length || !!result.invalid_count} onClick={() => void run(async () => { await onSave(validateRecipe(recipe)); setNotice('Recipe saved. Run the source scrape when ready.'); })}>Save to source</Button>}
          {onSave && initialRecipe && <Button onClick={() => void run(async () => { await onSave(null); setNotice('Automatic extraction restored for this source.'); })}>Use automatic extraction</Button>}
        </Stack>
      </Stack>
    </Box>
    <Alert severity="info">{fetchSample ? 'Tests do not import or remove channels. A pasted browser snapshot may differ from the response your scraper can fetch.' : 'This preview checks your sample only. Import the recipe into your scraper and test the actual source URL there. The helper never connects to your installation.'}</Alert>
    {result && <RecipeResults result={result} />}
    <Typography variant="body2">Share a working recipe through the <Link href="https://github.com/Pipepito/acestream-scraper/issues/new?title=Recipe%20catalogue%20submission" target="_blank" rel="noreferrer">catalogue contribution form</Link>. Attach the exported recipe and a small sanitized example only; publication follows review.</Typography>
  </Stack>;
}
