import React from 'react';
import { TextField } from '@mui/material';

export const PASSWORD_REQUIREMENT = 'Use 12–128 characters.';

export function validNewPassword(value: string): boolean {
  // Python validates Unicode characters, not JavaScript UTF-16 code units.
  const length = Array.from(value).length;
  return length >= 12 && length <= 128;
}

export default function NewPasswordField({ label, value, onChange }: {
  label: string; value: string; onChange: (value: string) => void;
}) {
  return <TextField required type="password" label={label} autoComplete="new-password"
    value={value} onChange={event => onChange(event.target.value)}
    error={value.length > 0 && !validNewPassword(value)} helperText={PASSWORD_REQUIREMENT} />;
}
