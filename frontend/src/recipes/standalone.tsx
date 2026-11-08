import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import { recipeResources } from './messages.generated';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Box, Button, Container, CssBaseline, Link, MenuItem, TextField, Stack, ThemeProvider, Typography } from '@mui/material';
import { createAppTheme } from '../theme';
import RecipeBuilder from './RecipeBuilder';
import { browserPreview } from './browserPreview';
const preferredLanguage = () => {
  try { const saved = localStorage.getItem('recipe-language-v1'); if (saved === 'en' || saved === 'es') return saved; } catch { /* Browser preference still works. */ }
  return navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en';
};
void i18next.use(initReactI18next).init({ resources: recipeResources, lng: preferredLanguage(), fallbackLng: 'en', supportedLngs: ['en', 'es'], defaultNS: 'ui', keySeparator: false, nsSeparator: false, initAsync: false, interpolation: { escapeValue: false }, react: { useSuspense: false } });
function Standalone() {
  const tUi = useUiText();
  const [language, setLanguage] = useState<'en' | 'es'>(preferredLanguage);
  const [storageFailed, setStorageFailed] = useState(false);
  useEffect(() => { document.documentElement.lang = language; void i18next.changeLanguage(language); }, [language]);
  const embedded = new URLSearchParams(window.location.search).get('embedded') === '1';
  const [dark, setDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches);
  const theme = useMemo(() => createAppTheme(dark ? 'dark' : 'light', 'cyan', language), [dark, language]);
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
    {!embedded && <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}><Box><Typography variant="overline">{tUi("ACESTREAM SCRAPER")}</Typography><Typography variant="h4" component="h1">{tUi("Extraction builder")}</Typography></Box><Button onClick={() => setDark(!dark)}>{dark ? tUi("Light theme") : tUi("Dark theme")}</Button></Stack>}
    <Stack direction="row" justifyContent="flex-end" sx={{ mb: 2 }}><TextField select label={tUi('Language')} value={language} onChange={event => {
      const next = event.target.value === 'es' ? 'es' : 'en'; setLanguage(next);
      try { localStorage.setItem('recipe-language-v1', next); setStorageFailed(false); } catch { setStorageFailed(true); }
    }}><MenuItem value="en">English</MenuItem><MenuItem value="es">Español</MenuItem></TextField></Stack>
    {storageFailed ? <Typography role="status">{tUi('Your language could not be remembered in this browser.')}</Typography> : null}
    <RecipeBuilder preview={browserPreview} />
    {!embedded && <Box component="footer" sx={{ mt: 5 }}><Link href="../#recipes">{tUi("All tools and docs")}</Link></Box>}
  </Container></ThemeProvider>;
}
createRoot(document.getElementById('root')!).render(<Standalone />);
