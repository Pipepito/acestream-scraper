import { createAppTheme } from '../theme';

const theme = createAppTheme('light');

const canvas = theme.appTokens.surface.canvas;
const successBackground = theme.appTokens.status.success.bg;
const pageTitle = theme.typography.pageTitle;
const statusMeta = theme.typography.statusMeta;

void canvas;
void successBackground;
void pageTitle;
void statusMeta;

const invalidSurfaceKey =
  // @ts-expect-error invalid semantic token key
  theme.appTokens.surface.background;

const invalidStatusFamily =
  // @ts-expect-error invalid status family
  theme.appTokens.status.okay.bg;

const invalidCaptionVariant =
  // @ts-expect-error invalid typography variant
  theme.typography.captionStrong;

const invalidPageHeadingVariant =
  // @ts-expect-error invalid typography variant
  theme.typography.pageHeading;

void invalidSurfaceKey;
void invalidStatusFamily;
void invalidCaptionVariant;
void invalidPageHeadingVariant;

export {};
