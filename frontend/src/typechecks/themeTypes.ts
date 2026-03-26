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

// @ts-expect-error invalid semantic token key
theme.appTokens.surface.background;

// @ts-expect-error invalid status family
theme.appTokens.status.okay.bg;

// @ts-expect-error invalid typography variant
theme.typography.captionStrong;

// @ts-expect-error invalid typography variant
theme.typography.pageHeading;

export {};
