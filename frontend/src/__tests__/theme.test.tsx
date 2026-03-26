import { createAppTheme } from '../theme';

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
      pageGap: expect.any(String),
      sectionGap: expect.any(String),
      panelPadding: expect.any(String),
      cardRadius: expect.any(Number),
      elevatedShadow: expect.any(String),
      divider: expect.any(String),
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
        backgroundColor: theme.appTokens.surface.panel,
        color: theme.appTokens.text.primary,
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
        border: `1px solid ${theme.appTokens.surface.border}`,
      })
    );
    expect(theme.components?.MuiChip?.styleOverrides?.root).toEqual(
      expect.objectContaining({
        borderRadius: 8,
      })
    );
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
