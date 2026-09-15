/** @jest-environment jsdom */
import catalogue from './catalogue.json';
import { checkSample, extractPrepared, prepareHtml, validateRecipe } from './engine';
import { previewDocument } from './VisualPicker';
import { sourceRules } from './sourceRules';
import { MAX_SAMPLE_BYTES, newRecipe } from './types';

test('accepts multi-megabyte samples while keeping a byte-based upper bound', () => {
  const sample = JSON.stringify({ ...JSON.parse(catalogue[1].sample), pageState: 'x'.repeat(8 * 1024 * 1024) });
  expect(() => checkSample(sample)).not.toThrow();
  expect(extractPrepared(validateRecipe(catalogue[1].recipe), sample).channels).toHaveLength(2);
  expect(() => checkSample('é'.repeat(MAX_SAMPLE_BYTES / 2 + 1))).toThrow('32 MiB');
});

describe('portable recipe fixtures', () => {
  test.each(catalogue)('$id produces correctly paired names and IDs', entry => {
    const recipe = validateRecipe(entry.recipe);
    const result = extractPrepared(recipe, entry.sample, recipe.mode === 'html' ? prepareHtml(recipe, entry.sample) : undefined);
    expect(result.channels.map(channel => channel.name)).toEqual(entry.expected.map(row => row.name));
    expect(result.channels.map(channel => channel.channel_id)).toEqual(entry.expected.map(row => row.channel_id));
    expect(result.invalid_count).toBe(0);
  });
  test('does not cross-pair missing fields', () => {
    const recipe = validateRecipe(catalogue[0].recipe);
    const sample = `<section class="channel"><h3>One</h3></section><section class="channel"><a href="acestream://${'a'.repeat(40)}">Watch</a></section>`;
    const result = extractPrepared(recipe, sample, prepareHtml(recipe, sample));
    expect(result.channels).toHaveLength(0);
    expect(result.invalid_count).toBe(2);
  });
  test('rejects executable or unsupported recipe properties', () => {
    expect(() => validateRecipe({ ...catalogue[0].recipe, script: 'alert(1)' })).toThrow();
    expect(() => validateRecipe({ ...catalogue[0].recipe, schema_version: 2 })).toThrow();
  });
  test('an unmatched optional capture is missing, not the whole match', () => {
    const recipe = validateRecipe(JSON.parse(JSON.stringify(catalogue[1].recipe)));
    recipe.fields.name.pattern = '(Missing)?Other';
    const result = extractPrepared(recipe, JSON.stringify({ data: { channels: [{ title: 'Other', stream: { id: 'a'.repeat(40) } }] } }));
    expect(result.channels).toHaveLength(0);
    expect(result.invalid_count).toBe(1);
  });
  test('preview removes executable markup, navigation and resource URLs', () => {
    const html = previewDocument('<div onclick="alert(1)"><script>alert(1)</script><iframe src="https://evil.test"></iframe><img src="https://evil.test/x"><a href="https://evil.test">Name</a><input type="password" value="secret"><form action="https://evil.test">submit</form></div>');
    expect(html).not.toContain('<script');
    expect(html).not.toContain('<iframe');
    expect(html).not.toContain('onclick');
    expect(html).not.toContain('src="https://');
    expect(html).not.toContain('secret');
    expect(html).not.toContain('<form');
    expect(html).toContain("script-src 'none'");
    expect(html).toContain('data-picker-href=');
  });
});


test('raw source authoring generalizes both fields across different IDs', () => {
  const first = `First channel | ${'a'.repeat(40)}`;
  const sample = first + `\nOther channel | ${'b'.repeat(40)}`;
  const recipe = sourceRules(newRecipe(), first, [
    { field: 'name', start: 0, end: 13 },
    { field: 'id', start: 16, end: 56 },
  ]);
  const result = extractPrepared(recipe, sample);
  expect(result.channels.map(row => row.name)).toEqual(['First channel', 'Other channel']);
  expect(result.channels.map(row => row.channel_id)).toEqual(['a'.repeat(40), 'b'.repeat(40)]);
});
