import React from 'react';
import i18next from 'i18next';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { useUiText } from '../i18n/useUiText';
import { useSnackbar } from '../hooks/useSnackbar';

it('keeps the same notification open across a language change and does not reopen after dismissal', async () => {
  function Harness() {
    const t = useUiText();
    const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();
    return <><button onClick={() => showSnackbar(() => t('EPG source added successfully'), 'success')}>send</button><button onClick={closeSnackbar}>close</button>{snackbar.open ? <div role="status">{snackbar.message}</div> : null}</>;
  }
  render(<Harness />);
  fireEvent.click(screen.getByRole('button', { name: 'send' }));
  const original = screen.getByRole('status');
  expect(original).toHaveTextContent('EPG source added successfully');
  try {
    await act(async () => { await i18next.changeLanguage('es'); });
    expect(screen.getByRole('status')).toBe(original);
    expect(original).toHaveTextContent(i18next.t('EPG source added successfully', { ns: 'ui' }));
    fireEvent.click(screen.getByRole('button', { name: 'close' }));
    await act(async () => { await i18next.changeLanguage('en'); });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  } finally { await act(async () => { await i18next.changeLanguage('en'); }); }
});
