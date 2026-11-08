import { translateKnown } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React from 'react';
import { Accordion, AccordionDetails, AccordionSummary, MenuItem, Stack, TextField, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { emptyField, ExtractionRecipe, FieldName, fieldLabels } from './types';
interface Props { recipe: ExtractionRecipe; onChange: (recipe: ExtractionRecipe) => void }
export default function RecipeFields({ recipe, onChange }: Props) {
  const tUi = useUiText();
  const update = (key: FieldName, property: string, value: string) => onChange({ ...recipe, fields: { ...recipe.fields, [key]: { ...emptyField(), ...recipe.fields[key], [property]: value } } });
  return <Stack spacing={2}>
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
      <TextField label={tUi("Recipe name")} value={recipe.name} onChange={e => onChange({ ...recipe, name: e.target.value })} fullWidth />
      <TextField label={tUi("Recipe version")} value={recipe.version} onChange={e => onChange({ ...recipe, version: e.target.value })} sx={{ minWidth: 130 }} />
      <TextField select label={tUi("Source format")} value={recipe.mode} onChange={e => onChange({ ...recipe, mode: e.target.value as ExtractionRecipe['mode'], records: '', fields: { name: emptyField(), id: emptyField() } })} sx={{ minWidth: 150 }}>
        <MenuItem value="html">{tUi("HTML elements")}</MenuItem><MenuItem value="regex">{tUi("Text / regex")}</MenuItem><MenuItem value="json">{tUi("JSON response")}</MenuItem>
      </TextField>
    </Stack>
    <TextField label={recipe.mode === 'html' ? tUi("Repeating row selector") : recipe.mode === 'json' ? tUi("Records array path") : tUi("Repeating record regex")} value={recipe.records} onChange={e => onChange({ ...recipe, records: e.target.value })} helperText={recipe.mode === 'json' ? tUi("For example data.channels. Leave blank for a root array.") : recipe.mode === 'html' ? tUi("For example .channel or table tr. Pick a row visually or enter its CSS selector.") : tUi("Each match is one record. Name and ID rules run inside that record.")} fullWidth />
    {(['name', 'id', 'group', 'logo', 'epg_id'] as FieldName[]).map(key => <Accordion key={key} defaultExpanded={key === 'name' || key === 'id'} disableGutters elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider', '&:before': { display: 'none' } }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight={600}>{translateKnown(fieldLabels[key])}{key !== 'name' && key !== 'id' ? tUi(" (optional)") : ''}</Typography></AccordionSummary>
      <AccordionDetails><Stack spacing={2}>
        {recipe.mode === 'html' && <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label={tUi("{{value0}} selector", { value0: translateKnown(fieldLabels[key]) })} value={recipe.fields[key]?.selector ?? ''} onChange={e => update(key, 'selector', e.target.value)} helperText={tUi("Relative to each row. Blank selects the row itself.")} fullWidth />
          <TextField label={tUi("{{value0}} attribute", { value0: translateKnown(fieldLabels[key]) })} value={recipe.fields[key]?.attribute ?? ''} onChange={e => update(key, 'attribute', e.target.value)} helperText={tUi("Blank reads text; or use href, value, data-acestream-id…")} fullWidth />
        </Stack>}
        {recipe.mode === 'json' && <TextField label={tUi("{{value0}} JSON path", { value0: translateKnown(fieldLabels[key]) })} value={recipe.fields[key]?.path ?? ''} onChange={e => update(key, 'path', e.target.value)} helperText={tUi("Relative to each object, for example stream.id. An ID array creates several streams with the same name.")} fullWidth />}
        <TextField label={tUi("{{value0}} regex", { value0: translateKnown(fieldLabels[key]) })} value={recipe.fields[key]?.pattern ?? ''} onChange={e => update(key, 'pattern', e.target.value)} helperText={tUi("Optional for HTML/JSON. The first capture group is the value, or the whole match without a capture.")} fullWidth />
      </Stack></AccordionDetails>
    </Accordion>)}
    <TextField label={tUi("Regex flags")} value={recipe.flags} onChange={e => onChange({ ...recipe, flags: e.target.value })} helperText={tUi("i: ignore case · m: line anchors · s: dot includes newlines. Use plain captures; named groups and backreferences are unsupported.")} />
  </Stack>;
}
