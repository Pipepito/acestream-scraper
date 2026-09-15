import { ExtractionRecipe, FieldName, MAX_RECORDS, MAX_SAMPLE_BYTES, RecipeField, RecipePreview } from './types';

export type PreparedRecord = Partial<Record<FieldName, string[]>>;
const fieldNames: FieldName[] = ['name', 'id', 'group', 'logo', 'epg_id'];
const fail = (message: string): never => { throw new Error(message); };
const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
export function validateRecipe(value: unknown): ExtractionRecipe {
  if (!object(value) || value.schema_version !== 1 || !['html', 'regex', 'json'].includes(String(value.mode))) return fail('Unsupported recipe format or version');
  if (Object.keys(value).some(key => !['schema_version', 'name', 'version', 'mode', 'records', 'flags', 'fields'].includes(key))) return fail('Unexpected recipe property');
  if (typeof value.name !== 'string' || !value.name.length || value.name.length > 100 || typeof value.version !== 'string' || !/^\d+\.\d+\.\d+$/.test(value.version)) return fail('Provide a recipe name and version such as 1.0.0');
  if (typeof value.records !== 'string' || value.records.length > 1024 || (value.mode !== 'json' && !value.records.trim())) return fail('Choose a repeating record');
  if (typeof value.flags !== 'string' || !/^[ims]{0,3}$/.test(value.flags)) return fail('Regex flags may contain i, m and s');
  if (!object(value.fields) || !value.fields.name || !value.fields.id || Object.keys(value.fields).some(key => !fieldNames.includes(key as FieldName))) return fail('Choose name and ID fields');
  const patterns: string[] = value.mode === 'regex' ? [value.records] : [];
  for (const field of Object.values(value.fields)) {
    if (!object(field) || Object.keys(field).some(key => !['selector', 'attribute', 'path', 'pattern'].includes(key))) return fail('Invalid field rule');
    for (const [key, limit] of Object.entries({ selector: 256, attribute: 80, path: 256, pattern: 1024 })) {
      if (typeof field[key] !== 'string' || (field[key] as string).length > limit) return fail(`Invalid ${key} rule`);
    }
    if (field.pattern) patterns.push(field.pattern as string);
    if (field.path && !/^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*$/.test(field.path as string)) return fail('JSON paths use dot-separated keys or array indices');
  }
  if (value.mode === 'json' && value.records && !/^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*$/.test(value.records)) return fail('Invalid JSON records path');
  patterns.forEach(pattern => {
    if (/\(\?(?!:|=|!)|\\(?:[1-9]|[AbBZzGKNpPk]|u|U|x)/.test(pattern)) fail('Use portable regex; no named groups or backreferences');
    new RegExp(pattern, Array.from(new Set(value.flags as string)).join(''));
  });
  return value as unknown as ExtractionRecipe;
}

export function checkSample(sample: string): void {
  if (new Blob([sample]).size > MAX_SAMPLE_BYTES) fail('Sample exceeds 32 MiB');
}
export function pathValue(value: unknown, path: string): unknown {
  for (const part of path ? path.split('.') : []) {
    if (Array.isArray(value) && /^\d+$/.test(part)) value = value[Number(part)];
    else if (object(value) && Object.prototype.hasOwnProperty.call(value, part)) value = value[part];
    else return undefined;
  }
  return value;
}
const strings = (value: unknown): string[] => (Array.isArray(value) ? value : [value]).slice(0, MAX_RECORDS).filter(item => typeof item === 'string' || typeof item === 'number').map(String);

export function prepareHtml(recipe: ExtractionRecipe, sample: string): PreparedRecord[] {
  checkSample(sample);
  // Parse in an inert document. Never insert the original sample into the app DOM.
  const template = document.createElement('template');
  template.innerHTML = sample;
  const records = Array.from(template.content.querySelectorAll(recipe.records));
  if (records.length > MAX_RECORDS) fail('More than 1000 records; narrow the record rule');
  return records.map(record => Object.fromEntries(Object.entries(recipe.fields).map(([key, field]) => {
    const nodes = field.selector ? Array.from(record.querySelectorAll(field.selector)) : [record];
    return [key, nodes.slice(0, MAX_RECORDS).map(node => field.attribute ? node.getAttribute(field.attribute) ?? '' : node.textContent ?? '')];
  })));
}

/** Runs in a terminable worker in production. Never run user regex in a React event handler. */
export function extractPrepared(recipe: ExtractionRecipe, sample: string, html?: PreparedRecord[]): RecipePreview {
  const flags = Array.from(new Set(recipe.flags)).join('');
  let records: PreparedRecord[];
  if (recipe.mode === 'html') records = html ?? [];
  else {
    let raw: unknown[];
    if (recipe.mode === 'json') {
      const selected = pathValue(JSON.parse(sample), recipe.records);
      if (!Array.isArray(selected)) return fail('The records path must select a JSON array');
      raw = selected;
    } else {
      raw = [];
      const pattern = new RegExp(recipe.records, `${flags}g`);
      const matches = sample.matchAll(pattern);
      for (let index = 0; index <= MAX_RECORDS; index++) { const next = matches.next(); if (next.done) break; raw.push(next.value[0]); }
    }
    if (raw.length > MAX_RECORDS) return fail('More than 1000 records; narrow the record rule');
    records = raw.map(record => Object.fromEntries(Object.entries(recipe.fields).map(([key, field]) => [key, strings(recipe.mode === 'json' ? pathValue(record, field.path) : record)])));
  }
  const result: RecipePreview = { channels: [], record_count: records.length, invalid_count: 0, duplicate_count: 0, issues: [] };
  const seen = new Set<string>();
  records.forEach((record, index) => {
    const values: Partial<Record<FieldName, string[]>> = {};
    Object.entries(recipe.fields).forEach(([key, field]: [string, RecipeField]) => {
      values[key as FieldName] = (record[key as FieldName] ?? []).map(raw => {
        const match = field.pattern ? new RegExp(field.pattern, flags).exec(raw) : null;
        return (field.pattern ? match ? match.length > 1 ? match[1] ?? '' : match[0] : '' : raw).replace(/\s+/g, ' ').trim();
      }).filter(Boolean);
    });
    const names = values.name ?? [], ids = (values.id ?? []).map(value => value.replace(/^acestream:\/\//, '').toLowerCase());
    let reason = names.length !== 1 || names[0].length > 200 ? 'Choose exactly one channel name per record (up to 200 characters)' : !ids.length ? 'No channel ID found' : '';
    if (ids.some(value => !/^[0-9a-f]{40}$/.test(value))) reason = 'Expected a 40-character hexadecimal ID or acestream:// link';
    if (reason) { result.invalid_count++; result.issues.push({ record: index + 1, message: reason }); return; }
    const metadata: Record<string, string> = {};
    ([['group', 'group_title'], ['logo', 'tvg_logo'], ['epg_id', 'tvg_id']] as const).forEach(([key, target]) => {
      const value = values[key]?.[0]?.slice(0, 2048);
      if (value && (key !== 'logo' || /^https?:\/\//.test(value))) metadata[target] = value;
    });
    ids.forEach(channel_id => {
      if (seen.has(channel_id)) { result.duplicate_count++; result.issues.push({ record: index + 1, message: 'Duplicate ID ignored' }); }
      else { seen.add(channel_id); result.channels.push({ channel_id, name: names[0], metadata }); }
      if (result.channels.length > MAX_RECORDS) fail('More than 1000 channel IDs; narrow the rule');
    });
  });
  result.issues = result.issues.slice(0, 1000);
  return result;
}
