import { createAppTheme } from '../theme';
import { getShellContentMaxWidth, getShellLayout } from '../styles/layout';

const collectKeys = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map(collectKeys);
  }

  if (value && typeof value === 'object') {
    return Object.keys(value as Record<string, unknown>)
      .sort()
      .reduce<Record<string, unknown>>((accumulator, key) => {
        accumulator[key] = collectKeys((value as Record<string, unknown>)[key]);
        return accumulator;
      }, {});
  }

  return true;
};

describe('createAppTheme', () => {
  const originalMatchMedia = window.matchMedia;

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('exposes a theme factory with semantic tokens and typed typography roles', () => {
    const lightTheme = createAppTheme('light');
    const darkTheme = createAppTheme('dark');

    expect(lightTheme).toBeDefined();
    expect(darkTheme).toBeDefined();
    expect(lightTheme.appTokens).toBeDefined();
    expect(darkTheme.appTokens).toBeDefined();
    expect(lightTheme.typography.pageTitle).toBeDefined();
    expect(lightTheme.typography.sectionTitle).toBeDefined();
    expect(lightTheme.typography.helperText).toBeDefined();
    expect(lightTheme.typography.statusMeta).toBeDefined();
    expect(lightTheme.typography.denseData).toBeDefined();
  });

  it('defines the full light-mode semantic token contract', () => {
    const theme = createAppTheme('light');

    expect(theme.appTokens.surface).toMatchObject({
      canvas: expect.any(String),
      panel: expect.any(String),
      muted: expect.any(String),
      raised: expect.any(String),
      border: expect.any(String),
    });

    expect(theme.appTokens.text).toMatchObject({
      primary: expect.any(String),
      secondary: expect.any(String),
      muted: expect.any(String),
      inverse: expect.any(String),
    });

    expect(theme.appTokens.shell).toMatchObject({
      navBg: expect.any(String),
      navBorder: expect.any(String),
      appBarBg: expect.any(String),
      appBarBorder: expect.any(String),
      accent: expect.any(String),
      activeNavBg: expect.any(String),
      activeNavText: expect.any(String),
      activeNavBorder: expect.any(String),
      contentGlow: expect.any(String),
    });

    expect(theme.appTokens.hero).toMatchObject({
      bg: expect.any(String),
      border: expect.any(String),
      accent: expect.any(String),
      muted: expect.any(String),
      spotlight: expect.any(String),
    });

    expect(theme.appTokens.status).toMatchObject({
      success: {
        bg: expect.any(String),
        border: expect.any(String),
        text: expect.any(String),
        icon: expect.any(String),
      },
      warning: {
        bg: expect.any(String),
        border: expect.any(String),
        text: expect.any(String),
        icon: expect.any(String),
      },
      error: {
        bg: expect.any(String),
        border: expect.any(String),
        text: expect.any(String),
        icon: expect.any(String),
      },
      info: {
        bg: expect.any(String),
        border: expect.any(String),
        text: expect.any(String),
        icon: expect.any(String),
      },
    });

    expect(theme.appTokens.action).toMatchObject({
      primaryBg: expect.any(String),
      primaryHover: expect.any(String),
      primaryText: expect.any(String),
      secondaryBg: expect.any(String),
      secondaryText: expect.any(String),
      dangerBg: expect.any(String),
      dangerText: expect.any(String),
      focusRing: expect.any(String),
      disabledBg: expect.any(String),
      disabledText: expect.any(String),
      accentWarm: expect.any(String),
    });

    expect(theme.appTokens.layout).toMatchObject({
      pageGap: expect.any(Number),
      sectionGap: expect.any(Number),
      panelPadding: expect.any(Number),
      cardRadius: expect.any(Number),
      elevatedShadow: expect.any(String),
      divider: expect.any(String),
      shell: {
        navWidth: expect.any(Number),
        phoneMaxWidth: expect.any(Number),
        desktopMinWidth: expect.any(Number),
        wideMinWidth: expect.any(Number),
        standardContentMaxWidth: expect.any(Number),
        wideContentMaxWidth: expect.any(Number),
        pagePaddingX: {
          xs: expect.any(Number),
          sm: expect.any(Number),
          md: expect.any(Number),
        },
        pagePaddingY: expect.any(Number),
      },
    });

    expect(theme.appTokens.motion).toMatchObject({
      durationShort: expect.any(Number),
      durationStandard: expect.any(Number),
      durationReduced: expect.any(Number),
      durationNone: expect.any(Number),
      easingStandard: expect.any(String),
    });

    expect(theme.typography).toMatchObject({
      pageTitle: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
      sectionTitle: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
      body1: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
      helperText: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
      statusMeta: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
      denseData: expect.objectContaining({ fontFamily: expect.stringContaining('IBM Plex Sans') }),
    });
  });

  it('keeps the same semantic token shape in dark mode', () => {
    const lightTheme = createAppTheme('light');
    const darkTheme = createAppTheme('dark');

    expect(collectKeys(darkTheme.appTokens)).toEqual(collectKeys(lightTheme.appTokens));
  });

  it('wires bounded shared mui defaults through semantic theme values', () => {
    const theme = createAppTheme('light');

    expect(theme.components?.MuiAppBar).toBeDefined();
    expect(theme.components?.MuiPaper).toBeDefined();
    expect(theme.components?.MuiButton).toBeDefined();
    expect(theme.components?.MuiAppBar?.defaultProps?.elevation).toBe(0);
    expect(theme.components?.MuiAppBar?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        backgroundColor: theme.appTokens.shell.appBarBg,
        color: theme.appTokens.text.primary,
        borderBottom: `1px solid ${theme.appTokens.shell.appBarBorder}`,
      })
    );
    expect(theme.components?.MuiPaper?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        backgroundColor: theme.appTokens.surface.panel,
        borderColor: theme.appTokens.surface.border,
      })
    );
    expect(theme.components?.MuiButton?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        borderRadius: theme.appTokens.layout.cardRadius,
        textTransform: 'none',
      })
    );
    expect(theme.components?.MuiCard?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        borderRadius: theme.appTokens.layout.cardRadius,
        border: `1px solid ${theme.appTokens.surface.border}`,
      })
    );
    expect(theme.components?.MuiChip?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        borderRadius: theme.appTokens.layout.cardRadius,
      })
    );
    expect(theme.components?.MuiChip?.styleOverrides?.outlined).toEqual(
      expect.objectContaining({
        borderColor: theme.appTokens.shell.activeNavBorder,
      })
    );
  });

  it('exposes visible focus treatment and non-color status emphasis in shared defaults', () => {
    const theme = createAppTheme('light');

    expect(theme.components?.MuiButton?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        '&.Mui-focusVisible': expect.objectContaining({
          boxShadow: `0 0 0 4px ${theme.appTokens.action.focusRing}`,
          outline: expect.stringContaining('solid'),
          outlineOffset: 2,
        }),
      })
    );

    expect(theme.components?.MuiAlert?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        borderLeftStyle: 'solid',
        borderLeftWidth: 4,
      })
    );
    expect(theme.components?.MuiAlert?.styleOverrides?.standardSuccess).toEqual(
      expect.objectContaining({
        backgroundColor: theme.appTokens.status.success.bg,
        borderColor: theme.appTokens.status.success.border,
        color: theme.appTokens.status.success.text,
        '& .MuiAlert-icon': expect.objectContaining({
          color: theme.appTokens.status.success.icon,
        }),
      })
    );
  });

  it('derives shared shell layout defaults from semantic theme tokens', () => {
    const theme = createAppTheme('dark');
    const layout = getShellLayout(theme);

    expect(layout).toEqual(theme.appTokens.layout.shell);
    expect(layout.pagePaddingY).toBe(theme.appTokens.layout.pageGap);
    expect(layout.pagePaddingX.sm).toBe(theme.appTokens.layout.pageGap);
    expect(layout.navWidth).toBe(theme.appTokens.layout.shell.navWidth);
    expect(layout.wideContentMaxWidth).toBe(theme.appTokens.layout.shell.wideContentMaxWidth);
    expect(layout.standardContentMaxWidth).toBeLessThan(layout.wideContentMaxWidth);
  });

  it('defines explicit shared shell breakpoints and content width tiers', () => {
    const theme = createAppTheme('light');
    const layout = getShellLayout(theme);
    const standardContentMaxWidth = getShellContentMaxWidth(theme, 'standard');
    const wideContentMaxWidth = getShellContentMaxWidth(theme, 'wide');

    expect(layout.phoneMaxWidth).toBe(899.95);
    expect(layout.desktopMinWidth).toBe(900);
    expect(layout.wideMinWidth).toBe(1280);
    expect(layout.navWidth).toBeGreaterThan(0);
    expect(layout.pagePaddingX.md).toBeGreaterThan(layout.pagePaddingX.xs);
    expect(layout.pagePaddingY).toBeGreaterThan(0);
    expect(standardContentMaxWidth).toBe(layout.standardContentMaxWidth);
    expect(wideContentMaxWidth).toBe(layout.wideContentMaxWidth);
    expect(wideContentMaxWidth).toBeGreaterThan(standardContentMaxWidth);
  });

  it('uses reduced-motion timing when the user preference is enabled', () => {
    window.matchMedia = jest.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    const theme = createAppTheme('light');

    expect(theme.appTokens.motion.durationStandard).toBe(theme.appTokens.motion.durationReduced);
    expect(theme.components?.MuiButton?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        transitionDuration: `${theme.appTokens.motion.durationReduced}ms`,
      })
    );
  });
});
