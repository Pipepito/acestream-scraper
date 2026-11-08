import { getContrastRatio } from '@mui/material/styles';
import { createAppTheme } from '../theme';

/** Normal text 4.5:1, essential non-text controls/icons 3:1; disabled controls excluded. */
for (const preset of ['lime', 'coral', 'cyan'] as const) for (const mode of ['light', 'dark'] as const) {
  it(`${preset} ${mode}: semantic text, states, actions and essential borders meet contrast thresholds`, () => {
    const theme = createAppTheme(mode, preset);
    const { appTokens: t, palette } = theme;
    const readings: Array<{ role: string; foreground: string; background: string; minimum: number; ratio: number }> = [];
    const check = (role: string, foreground: string, background: string, minimum = 4.5) => {
      const ratio = getContrastRatio(foreground, background);
      readings.push({ role, foreground, background, minimum, ratio });
      expect({ role, foreground, background, passes: ratio >= minimum }).toEqual({ role, foreground, background, passes: true });
    };
    for (const surface of ['canvas', 'panel', 'raised'] as const) {
      for (const text of ['primary', 'secondary', 'muted'] as const) check(`${text}/${surface}`, t.text[text], t.surface[surface]);
      check(`link/${surface}`, t.action.secondaryText, t.surface[surface]);
      check(`control-border/${surface}`, t.action.controlBorder, t.surface[surface], 3);
      check(`focus/${surface}`, t.action.focusRing, t.surface[surface], 3);
      for (const status of ['success', 'warning', 'error', 'info'] as const) check(`${status}-text/${surface}`, palette[status].main, t.surface[surface]);
    }
    for (const status of ['success', 'warning', 'error', 'info'] as const) {
      check(`${status}-alert-text`, t.status[status].text, t.status[status].bg);
      check(`${status}-alert-icon`, t.status[status].icon, t.status[status].bg, 3);
      check(`${status}-filled-text`, palette[status].contrastText, palette[status].main);
    }
    check('primary-button', t.action.primaryText, t.action.primaryBg);
    check('primary-button-hover', t.action.primaryText, t.action.primaryHover);
    check('secondary-button', palette.secondary.contrastText, palette.secondary.main);
    check('danger-button', t.action.dangerText, t.action.dangerBg);
    check('selected-navigation', t.shell.activeNavText, t.shell.activeNavBg);
    if (process.env.UX_CONTRAST_REPORT) {
      const fs = jest.requireActual<typeof import('node:fs')>('node:fs');
      fs.mkdirSync(process.env.UX_CONTRAST_REPORT, { recursive: true });
      fs.writeFileSync(`${process.env.UX_CONTRAST_REPORT}/${preset}-${mode}.json`, JSON.stringify({ preset, mode, typography: { body: theme.typography.body2, helper: theme.typography.helperText }, readings }, null, 2));
    }
  });
}
