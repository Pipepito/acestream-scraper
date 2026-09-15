export interface RecipeField { selector: string; attribute: string; path: string; pattern: string }
export type FieldName = 'name' | 'id' | 'group' | 'logo' | 'epg_id';
export interface ExtractionRecipe {
  schema_version: 1;
  name: string;
  version: string;
  mode: 'html' | 'regex' | 'json';
  records: string;
  flags: string;
  fields: Partial<Record<FieldName, RecipeField>> & { name: RecipeField; id: RecipeField };
}
export interface RecipePreview {
  channels: { channel_id: string; name: string; metadata: Record<string, string> }[];
  record_count: number;
  invalid_count: number;
  duplicate_count: number;
  issues: { record: number; message: string }[];
}
export const MAX_SAMPLE_BYTES = 32 * 1024 * 1024;
export const MAX_RECIPE_BYTES = 512 * 1024;
export const MAX_RECORDS = 1000;
export const fieldLabels: Record<FieldName, string> = { name: 'Channel name', id: 'AceStream ID', group: 'Group', logo: 'Logo', epg_id: 'EPG ID' };
export const emptyField = (): RecipeField => ({ selector: '', attribute: '', path: '', pattern: '' });
export const newRecipe = (): ExtractionRecipe => ({ schema_version: 1, name: 'My recipe', version: '1.0.0', mode: 'html', records: '', flags: 'is', fields: { name: emptyField(), id: emptyField() } });
