import { createTheme } from '@mui/material/styles';
import type { AppTokens } from './theme.d';

export type ThemeMode = 'light' | 'dark';

const fontFamily = [
  '"IBM Plex Sans"',
  'system-ui',
  '-apple-system',
  'BlinkMacSystemFont',
  '"Segoe UI"',
  'Roboto',
  '"Helvetica Neue"',
  'Arial',
  'sans-serif',
].join(',');

const tokenSets: Record<ThemeMode, AppTokens> = {
  light: {
    surface: {
      canvas: '#f3f6fb',
      panel: '#ffffff',
      muted: '#e7eef6',
      raised: '#fbfdff',
      border: 'rgba(16, 33, 47, 0.08)',
    },
    text: {
      primary: '#10212f',
      secondary: '#41556a',
      muted: '#66788a',
      inverse: '#f8fbff',
    },
    status: {
      success: {
        bg: '#e7f7ef',
        border: '#9ed8b7',
        text: '#14532d',
        icon: '#1f8f59',
      },
      warning: {
        bg: '#fff4e5',
        border: '#f5c27a',
        text: '#8a4b08',
        icon: '#d97706',
      },
      error: {
        bg: '#fdecec',
        border: '#f1a7a7',
        text: '#8f1d1d',
        icon: '#d14343',
      },
      info: {
        bg: '#e8f2ff',
        border: '#9ec0f7',
        text: '#0f3f78',
        icon: '#0b5ed7',
      },
    },
    action: {
      primaryBg: '#0f766e',
      primaryHover: '#115e59',
      primaryText: '#f7fffd',
      secondaryBg: '#dce9fb',
      secondaryText: '#0b5ed7',
      dangerBg: '#d14343',
      dangerText: '#fff7f7',
      focusRing: 'rgba(11, 94, 215, 0.24)',
      disabledBg: '#dbe4ec',
      disabledText: '#708191',
      accentWarm: '#dd8a42',
    },
    layout: {
      pageGap: '24px',
      sectionGap: '16px',
      panelPadding: '20px',
      cardRadius: 10,
      elevatedShadow: '0 8px 20px rgba(16, 33, 47, 0.06)',
      divider: 'rgba(16, 33, 47, 0.08)',
    },
    motion: {
      durationShort: 120,
      durationStandard: 180,
      durationReduced: 80,
      durationNone: 0,
      easingStandard: 'cubic-bezier(0.2, 0, 0, 1)',
    },
  },
  dark: {
    surface: {
      canvas: '#0f1720',
      panel: '#17222d',
      muted: '#1c2c38',
      raised: '#223240',
      border: 'rgba(166, 193, 214, 0.16)',
    },
    text: {
      primary: '#edf5fb',
      secondary: '#b6c8d8',
      muted: '#89a1b3',
      inverse: '#10212f',
    },
    status: {
      success: {
        bg: '#103122',
        border: '#1f6b45',
        text: '#a8e4bf',
        icon: '#5fd48d',
      },
      warning: {
        bg: '#3a2610',
        border: '#8f5e23',
        text: '#ffd39d',
        icon: '#f0a84b',
      },
      error: {
        bg: '#3b1719',
        border: '#8c3438',
        text: '#ffb6b6',
        icon: '#ff7f86',
      },
      info: {
        bg: '#13273f',
        border: '#25538b',
        text: '#afd0ff',
        icon: '#66a6ff',
      },
    },
    action: {
      primaryBg: '#14b8a6',
      primaryHover: '#0f9385',
      primaryText: '#08201d',
      secondaryBg: '#163355',
      secondaryText: '#bfd8ff',
      dangerBg: '#d86363',
      dangerText: '#2a0f10',
      focusRing: 'rgba(102, 166, 255, 0.3)',
      disabledBg: '#243543',
      disabledText: '#7c93a5',
      accentWarm: '#f0a84b',
    },
    layout: {
      pageGap: '24px',
      sectionGap: '16px',
      panelPadding: '20px',
      cardRadius: 10,
      elevatedShadow: '0 14px 32px rgba(0, 0, 0, 0.28)',
      divider: 'rgba(166, 193, 214, 0.16)',
    },
    motion: {
      durationShort: 120,
      durationStandard: 180,
      durationReduced: 80,
      durationNone: 0,
      easingStandard: 'cubic-bezier(0.2, 0, 0, 1)',
    },
  },
};

export const createAppTheme = (mode: ThemeMode) => {
  const prefersReducedMotion =
    typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

  const appTokens = {
    ...tokenSets[mode],
    motion: {
      ...tokenSets[mode].motion,
      durationStandard: prefersReducedMotion
        ? tokenSets[mode].motion.durationReduced
        : tokenSets[mode].motion.durationStandard,
    },
  };

  return createTheme({
    appTokens,
    palette: {
      mode,
      primary: {
        main: appTokens.action.primaryBg,
        dark: appTokens.action.primaryHover,
        light: mode === 'light' ? '#14b8a6' : '#5eead4',
        contrastText: appTokens.action.primaryText,
      },
      secondary: {
        main: mode === 'light' ? '#0b5ed7' : '#66a6ff',
        contrastText: appTokens.text.inverse,
      },
      background: {
        default: appTokens.surface.canvas,
        paper: appTokens.surface.panel,
      },
      text: {
        primary: appTokens.text.primary,
        secondary: appTokens.text.secondary,
      },
      error: {
        main: appTokens.status.error.icon,
      },
      warning: {
        main: appTokens.status.warning.icon,
      },
      success: {
        main: appTokens.status.success.icon,
      },
      info: {
        main: appTokens.status.info.icon,
      },
    },
    shape: {
      borderRadius: appTokens.layout.cardRadius,
    },
    typography: {
      fontFamily,
      h1: {
        fontFamily,
      },
      h2: {
        fontFamily,
      },
      h3: {
        fontFamily,
      },
      h4: {
        fontFamily,
        fontWeight: 600,
        letterSpacing: '-0.02em',
      },
      h5: {
        fontFamily,
      },
      h6: {
        fontFamily,
      },
      body1: {
        fontFamily,
        fontSize: '0.95rem',
        lineHeight: 1.55,
      },
      body2: {
        fontFamily,
        fontSize: '0.875rem',
        lineHeight: 1.45,
      },
      pageTitle: {
        fontFamily,
        fontSize: 'clamp(1.75rem, 2.2vw, 2.35rem)',
        fontWeight: 700,
        lineHeight: 1.15,
        letterSpacing: '-0.03em',
      },
      sectionTitle: {
        fontFamily,
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.3,
        letterSpacing: '-0.01em',
      },
      helperText: {
        fontFamily,
        fontSize: '0.8125rem',
        lineHeight: 1.45,
        color: appTokens.text.secondary,
      },
      statusMeta: {
        fontFamily,
        fontSize: '0.75rem',
        fontWeight: 500,
        lineHeight: 1.4,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
      },
      denseData: {
        fontFamily,
        fontSize: '0.8125rem',
        fontWeight: 500,
        lineHeight: 1.35,
      },
    },
    components: {
      MuiAppBar: {
        defaultProps: {
          elevation: 0,
          color: 'transparent',
        },
        styleOverrides: {
          root: {
            backgroundColor: appTokens.surface.panel,
            color: appTokens.text.primary,
            borderBottom: `1px solid ${appTokens.layout.divider}`,
            backdropFilter: 'blur(6px)',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundColor: appTokens.surface.panel,
            backgroundImage: 'none',
            borderColor: appTokens.surface.border,
          },
          rounded: {
            borderRadius: appTokens.layout.cardRadius,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 14,
            border: `1px solid ${appTokens.surface.border}`,
            boxShadow: appTokens.layout.elevatedShadow,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
        },
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: appTokens.layout.cardRadius,
            fontWeight: 600,
            transitionDuration: `${appTokens.motion.durationStandard}ms`,
            transitionTimingFunction: appTokens.motion.easingStandard,
            '&.Mui-focusVisible': {
              boxShadow: `0 0 0 4px ${appTokens.action.focusRing}`,
            },
          },
          contained: {
            boxShadow: 'none',
            '&:hover': {
              boxShadow: appTokens.layout.elevatedShadow,
            },
          },
          containedPrimary: {
            backgroundColor: appTokens.action.primaryBg,
            color: appTokens.action.primaryText,
            '&:hover': {
              backgroundColor: appTokens.action.primaryHover,
            },
            '&.Mui-disabled': {
              backgroundColor: appTokens.action.disabledBg,
              color: appTokens.action.disabledText,
            },
          },
          outlined: {
            borderColor: appTokens.surface.border,
            color: appTokens.text.primary,
            backgroundColor: appTokens.action.secondaryBg,
            '&:hover': {
              borderColor: appTokens.action.secondaryText,
              backgroundColor: appTokens.surface.muted,
            },
          },
        },
      },
    },
  });
};

const theme = createAppTheme('light');

export default theme;
