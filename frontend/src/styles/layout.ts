import type { Theme } from '@mui/material/styles';

export const getShellLayout = (theme: Theme) => theme.appTokens.layout.shell;

export type ShellContentMode = 'standard' | 'wide';

export const getShellContentMaxWidth = (theme: Theme, mode: ShellContentMode = 'standard') => {
  const layout = getShellLayout(theme);

  return mode === 'wide' ? layout.contentMaxWidth : layout.standardContentMaxWidth;
};
