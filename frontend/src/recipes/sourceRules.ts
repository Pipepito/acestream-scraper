import { emptyField, ExtractionRecipe, FieldName } from './types';
export interface SourceFieldSelection { field: FieldName; start: number; end: number }
const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export function sourceRules(recipe: ExtractionRecipe, template: string, selections: SourceFieldSelection[]): ExtractionRecipe {
  const ordered = [...selections].sort((a, b) => a.start - b.start);
  ordered.forEach((selection, index) => {
    if (selection.start < 0 || selection.end > template.length || selection.start >= selection.end || (index && ordered[index - 1].end > selection.start)) throw new Error('Select non-overlapping fields inside the chosen record');
  });
  const pattern = (capture?: FieldName) => {
    let offset = 0, result = '';
    ordered.forEach(selection => {
      result += escape(template.slice(offset, selection.start));
      const value = selection.field === 'id' ? '[0-9a-fA-F]{40}' : '[^\\r\\n]*?';
      result += selection.field === capture ? `(${value})` : `(?:${value})`;
      offset = selection.end;
    });
    return result + escape(template.slice(offset));
  };
  const fields = { name: emptyField(), id: emptyField() } as ExtractionRecipe['fields'];
  ordered.forEach(selection => { fields[selection.field] = { ...emptyField(), pattern: pattern(selection.field) }; });
  return { ...recipe, mode: 'regex', records: pattern(), fields };
}
