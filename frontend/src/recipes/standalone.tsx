import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Box, Button, Container, CssBaseline, Link, Stack, ThemeProvider, Typography } from '@mui/material';
import { createAppTheme } from '../theme';
import RecipeBuilder from './RecipeBuilder';
import { browserPreview } from './browserPreview';
function Standalone() {
  const embedded = new URLSearchParams(window.location.search).get('embedded') === '1';
  const [dark, setDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches);
  const theme = useMemo(() => createAppTheme(dark ? 'dark' : 'light'), [dark]);
  useEffect(() => {
    if (!embedded) return;
    const observer = new ResizeObserver(() => window.parent.postMessage({ type: 'recipe-builder-height', height: document.getElementById('root')!.getBoundingClientRect().height + 8 }, window.location.origin));
    observer.observe(document.getElementById('root')!);
    const preference = window.matchMedia('(prefers-color-scheme: dark)');
    const updateTheme = () => setDark(preference.matches);
    preference.addEventListener('change', updateTheme);
    return () => { observer.disconnect(); preference.removeEventListener('change', updateTheme); };
  }, [embedded]);
  return <ThemeProvider theme={theme}><CssBaseline /><Container maxWidth="xl" disableGutters={embedded} sx={{ py: embedded ? 0 : { xs: 2, md: 5 } }}>
    {!embedded && <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}><Box><Typography variant="overline">ACESTREAM SCRAPER</Typography><Typography variant="h4" component="h1">Extraction builder</Typography></Box><Button onClick={() => setDark(!dark)}>{dark ? 'Light theme' : 'Dark theme'}</Button></Stack>}
    <RecipeBuilder preview={browserPreview} />
    {!embedded && <Box component="footer" sx={{ mt: 5 }}><Link href="../#recipes">All tools and docs</Link></Box>}
  </Container></ThemeProvider>;
}
createRoot(document.getElementById('root')!).render(<Standalone />);
