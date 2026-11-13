import React from 'react';
import { render } from '@testing-library/react';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { createAppTheme } from '../theme';

it('registers both selected font faces instead of overwriting Inter with the second face', () => {
  const theme = createAppTheme('light', 'lime');
  render(<ThemeProvider theme={theme}><CssBaseline /></ThemeProvider>);
  const registered = Array.from(document.styleSheets).flatMap(sheet => Array.from(sheet.cssRules))
    .filter(rule => rule.type === CSSRule.FONT_FACE_RULE).map(rule => rule.cssText);
  expect(registered.filter(css => /font-family: Inter/.test(css))).toHaveLength(1);
  expect(registered.filter(css => /font-family: "Barlow Condensed"/.test(css))).toHaveLength(1);

  // The test DOM keeps a face's family but not its `src` and `font-display`
  // descriptors, so those are read from the faces the theme declares.
  const overrides = theme.components?.MuiCssBaseline?.styleOverrides;
  const declared = typeof overrides === 'function' ? overrides(theme) : overrides;
  const faces = String(Array.isArray(declared) ? declared[0] : declared).match(/@font-face \{[^}]*\}/g) ?? [];
  expect(faces).toHaveLength(2);
  for (const face of faces) {
    expect(face).toMatch(/src: url\(/);
    expect(face).toMatch(/font-display: swap/);
  }
});
