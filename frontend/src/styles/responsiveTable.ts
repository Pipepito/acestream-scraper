import type { SxProps, Theme } from '@mui/material/styles';

/** Keep every field and action visible on phones without a horizontal table pan. */
export const responsiveTableSx = {
  '@media (max-width: 599.95px)': {
    '& table, & tbody': { display: 'block', width: '100%' },
    '& thead': { position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clipPath: 'inset(50%)' },
    '& tbody tr': { display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', columnGap: 1.5, borderBottom: '1px solid', borderColor: 'divider', py: 1 },
    '& tbody td': { display: 'block', border: 0, px: 0, py: 0.5, whiteSpace: 'normal', textAlign: 'left', overflowWrap: 'anywhere' },
    '& tbody td:first-of-type, & td[data-label="URL"], & td[data-label="Actions"], & td[colspan]': { gridColumn: '1 / -1' },
    '& td[data-label]::before': { content: 'attr(data-label)', display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'text.secondary', mb: 0.25 },
  },
} satisfies SxProps<Theme>;
