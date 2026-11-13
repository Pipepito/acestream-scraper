/**
 * The channel number an edit form sends. An emptied field is null, so the
 * number is removed instead of the field being silently ignored; 0 is a
 * number like any other.
 */
export const channelNumberPayload = (value: number | string | null | undefined): number | null =>
  value === '' || value === null || value === undefined ? null : Number(value);
