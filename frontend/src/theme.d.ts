import '@mui/material/styles';
import '@mui/material/Typography';

export interface AppStatusToken {
  bg: string;
  border: string;
  text: string;
  icon: string;
}

export interface AppTokens {
  surface: {
    canvas: string;
    panel: string;
    muted: string;
    raised: string;
    border: string;
  };
  text: {
    primary: string;
    secondary: string;
    muted: string;
    inverse: string;
  };
  shell: {
    navBg: string;
    navBorder: string;
    appBarBg: string;
    appBarBorder: string;
    accent: string;
    activeNavBg: string;
    activeNavText: string;
    activeNavBorder: string;
    contentGlow: string;
  };
  hero: {
    bg: string;
    border: string;
    accent: string;
    muted: string;
    spotlight: string;
  };
  status: {
    success: AppStatusToken;
    warning: AppStatusToken;
    error: AppStatusToken;
    info: AppStatusToken;
  };
  action: {
    primaryBg: string;
    primaryHover: string;
    primaryText: string;
    secondaryBg: string;
    secondaryText: string;
    dangerBg: string;
    dangerText: string;
    focusRing: string;
    disabledBg: string;
    disabledText: string;
    accentWarm: string;
  };
  layout: {
    pageGap: number;
    sectionGap: number;
    panelPadding: number;
    cardRadius: number;
    elevatedShadow: string;
    divider: string;
    shell: {
      navWidth: number;
      phoneMaxWidth: number;
      desktopMinWidth: number;
      wideMinWidth: number;
      standardContentMaxWidth: number;
      wideContentMaxWidth: number;
      pagePaddingX: {
        xs: number;
        sm: number;
        md: number;
      };
      pagePaddingY: number;
    };
  };
  motion: {
    durationShort: number;
    durationStandard: number;
    durationReduced: number;
    durationNone: number;
    easingStandard: string;
  };
}

declare module '@mui/material/styles' {
  interface TypographyVariants {
    pageTitle: React.CSSProperties;
    sectionTitle: React.CSSProperties;
    helperText: React.CSSProperties;
    statusMeta: React.CSSProperties;
    denseData: React.CSSProperties;
  }

  interface TypographyVariantsOptions {
    pageTitle?: React.CSSProperties;
    sectionTitle?: React.CSSProperties;
    helperText?: React.CSSProperties;
    statusMeta?: React.CSSProperties;
    denseData?: React.CSSProperties;
  }

  interface Theme {
    appTokens: AppTokens;
  }

  interface ThemeOptions {
    appTokens?: AppTokens;
  }
}

declare module '@mui/material/Typography' {
  interface TypographyPropsVariantOverrides {
    pageTitle: true;
    sectionTitle: true;
    helperText: true;
    statusMeta: true;
    denseData: true;
  }
}

export {};
