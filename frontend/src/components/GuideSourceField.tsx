import React from 'react';
import { MenuItem, TextField } from '@mui/material';
import { useEPGSources } from '../hooks/useEPG';
import { useUiText } from '../i18n/useUiText';

interface GuideSourceFieldProps {
  value: number | '' | null | undefined;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

/**
 * The guide source a TV channel's EPG ID is looked up in. Two sources can
 * use different ids for the same channel (Alpha.TV, Alpha), so the id
 * alone does not say which guide is meant.
 */
const GuideSourceField: React.FC<GuideSourceFieldProps> = ({ value, onChange }) => {
  const tUi = useUiText();
  const { data: sources } = useEPGSources();
  return (
    <TextField
      select
      name="epg_source_id"
      label={tUi("Guide source")}
      value={value ?? ''}
      onChange={onChange}
      fullWidth
      helperText={tUi("The guide the EPG ID belongs to.")}
    >
      <MenuItem value="">{tUi("Not set")}</MenuItem>
      {(sources ?? []).map((source) => (
        <MenuItem key={source.id} value={source.id}>
          {source.name || source.url}
        </MenuItem>
      ))}
    </TextField>
  );
};

/** The value an edit form sends: an emptied choice removes the source. */
export const guideSourcePayload = (value: number | string | null | undefined): number | null =>
  value === '' || value === null || value === undefined ? null : Number(value);

export default GuideSourceField;
