import { translateKnown } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { ToggleButton, ToggleButtonGroup } from '@mui/material';

export type BrowseMode = 'tv' | 'streams' | 'events';

export const BROWSE_MODES: Array<{ value: BrowseMode; label: string }> = [
  { value: 'tv', label: 'TV channels' },
  { value: 'streams', label: 'Streams' },
  { value: 'events', label: 'Events' },
];

export const parseBrowseMode = (value: string | null): BrowseMode => value === 'streams' || value === 'events' ? value : 'tv';

interface BrowseModeToggleProps {
  value: BrowseMode;
  onChange: (mode: BrowseMode) => void;
}

/** One list, three views: the toggle keeps the side column to a single scrolling list. */
const BrowseModeToggle: React.FC<BrowseModeToggleProps> = ({ value, onChange }) => { const tUi = useUiText(); return (
  <ToggleButtonGroup exclusive size="small" value={value} onChange={(_, next: BrowseMode | null) => { if (next) onChange(next); }}
    aria-label={tUi("Browse")} sx={{ maxWidth: '100%', overflowX: 'auto' }}>
    {BROWSE_MODES.map((mode) => <ToggleButton key={mode.value} value={mode.value} sx={{ whiteSpace: 'nowrap' }}>{translateKnown(mode.label)}</ToggleButton>)}
  </ToggleButtonGroup>
); };

export default BrowseModeToggle;
