import type { Theme } from '@mui/material/styles';
import type { SxProps } from '@mui/material/styles';

export const getShellLayout = (theme: Theme) => theme.appTokens.layout.shell;

export type ShellContentMode = 'standard' | 'wide';
export type WidePageSplitRegion = 'default' | 'primary' | 'supporting';

export const getShellContentMaxWidth = (theme: Theme, mode: ShellContentMode = 'standard') => {
  const layout = getShellLayout(theme);

  return mode === 'wide' ? layout.wideContentMaxWidth : layout.standardContentMaxWidth;
};

export const getWidePageSplitLayout = (theme: Theme, active = true): SxProps<Theme> | undefined => {
  if (!active) {
    return undefined;
  }

  return {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 2fr) minmax(280px, 1fr)',
    gridTemplateAreas: 'primary supporting',
    gap: theme.appTokens.layout.pageGap,
    alignItems: 'start',
  };
};

export const getWidePageSplitRegionStyles = (
  active: boolean,
  region: WidePageSplitRegion = 'default'
): SxProps<Theme> | undefined => {
  if (!active || region === 'default') {
    return undefined;
  }

  return {
    gridArea: region,
    alignSelf: 'start',
  };
};
