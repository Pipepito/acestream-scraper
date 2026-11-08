import React from 'react';
import { render } from '@testing-library/react';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { createAppTheme } from '../theme';

it('registers both selected font faces instead of overwriting Inter with the second face', () => {
  render(<ThemeProvider theme={createAppTheme('light', 'lime')}><CssBaseline /></ThemeProvider>);
  const faces = Array.from(document.styleSheets).flatMap(sheet => Array.from(sheet.cssRules))
    .filter(rule => rule.type === CSSRule.FONT_FACE_RULE).map(rule => rule.cssText);
  expect(faces.some(css => /font-family: Inter/.test(css) && /font-display: swap/.test(css))).toBe(true);
  expect(faces.some(css => /font-family: "Barlow Condensed"/.test(css) && /font-display: swap/.test(css))).toBe(true);
});
