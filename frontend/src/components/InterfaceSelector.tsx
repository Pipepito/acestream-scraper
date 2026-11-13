import { useUiText } from '../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Box, Button, ButtonBase, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material';
import PaletteOutlined from '@mui/icons-material/PaletteOutlined';
import CheckCircleOutline from '@mui/icons-material/CheckCircleOutline';
import { useTranslation } from 'react-i18next';
import { interfaceIds, useAppPreferences, type AppLanguage } from '../preferences/AppPreferences';

const colors = { lime: ['#f3f4ed', '#c0ef54', '#242d22'], coral: ['#f6f3ee', '#ffad87', '#202336'], cyan: ['#101f21', '#55dfc4', '#eff9f2'] };
export default function InterfaceSelector() {
  const tUi = useUiText();
  const [open, setOpen] = useState(false);
  const preferences = useAppPreferences();
  const { t } = useTranslation();
  return <>
    <Button color="inherit" startIcon={<PaletteOutlined />} onClick={() => setOpen(true)} aria-haspopup="dialog" aria-label={t('interface')}
      sx={{ minWidth: 44, minHeight: 44, '& .MuiButton-startIcon': { mr: { xs: 0, sm: 1 }, ml: { xs: 0, sm: -0.5 } } }}><Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>{t('interface')}</Box></Button>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md" aria-labelledby="interface-title">
      <DialogTitle id="interface-title">{t('chooseInterface')}</DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          <Box role="group" aria-label={t('interface')} sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, minmax(0, 1fr))' } }}>
            {interfaceIds.map(id => <ButtonBase key={id} aria-pressed={preferences.interface === id} onClick={() => preferences.setPreference('interface', id)} sx={{ textAlign: 'left', display: 'block', border: 2, borderColor: preferences.interface === id ? 'text.primary' : 'divider', borderRadius: 2, overflow: 'hidden' }}>
              <Box aria-hidden sx={{ bgcolor: colors[id][0], color: colors[id][2], height: 116, p: 2, display: 'grid', gap: 1, gridTemplateColumns: id === 'coral' ? '1fr 1fr' : '1fr' }}>
                <Box sx={{ bgcolor: colors[id][1], height: id === 'lime' ? 18 : 48, borderRadius: id === 'lime' ? 0 : 2 }} />
                <Box sx={{ borderTop: '3px solid', opacity: 0.6, width: '70%' }} />
                <Box sx={{ borderTop: '3px solid', opacity: 0.4, width: '50%' }} />
              </Box>
              <Box sx={{ p: 2 }}><Stack direction="row" justifyContent="space-between" alignItems="center"><Typography fontWeight={700}>{t(id)}</Typography>{preferences.interface === id ? <CheckCircleOutline aria-label={t('selected')} /> : null}</Stack>
                <Typography variant="body2" sx={{ mt: 1 }}>{t(`${id}Description`)}</Typography></Box>
            </ButtonBase>)}
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField fullWidth select label={t('language')} value={preferences.language} onChange={event => preferences.setPreference('language', event.target.value as AppLanguage)}><MenuItem value="en" lang="en">{tUi("English")}</MenuItem><MenuItem value="es" lang="es">{tUi("Español")}</MenuItem></TextField>
            <TextField fullWidth select label={t('theme')} value={preferences.mode} onChange={event => preferences.setPreference('mode', event.target.value as 'light' | 'dark')}><MenuItem value="light">{t('light')}</MenuItem><MenuItem value="dark">{t('dark')}</MenuItem></TextField>
          </Stack>
          {preferences.storageFailure ? <Alert severity="warning" action={<Button color="inherit" onClick={preferences.retryStorage}>{t('retry')}</Button>}>{t(preferences.storageFailure === 'read' ? 'preferenceReadError' : 'preferenceError')}</Alert> : null}
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={() => setOpen(false)}>{t('close')}</Button></DialogActions>
    </Dialog>
  </>;
}
