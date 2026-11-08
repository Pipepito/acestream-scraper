import React, { useState } from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, Link, Outlet, RouterProvider, useLocation } from 'react-router-dom';
import { UnsavedChangesProvider } from '../components/UnsavedChanges';
import { useSettingDraft } from '../hooks/useSettingDraft';
import { AppPreferencesProvider, useAppPreferences } from '../preferences/AppPreferences';

function Editor() {
  const [server, setServer] = useState('saved');
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState(false);
  const draft = useSettingDraft(server, '', pending);
  const preferences = useAppPreferences();
  const location = useLocation();
  return <>
    <label>Value<input value={draft.value} onChange={event => draft.change(event.target.value)} /></label>
    <output aria-label="Location">{location.pathname}{location.search}</output>
    {failure && <p role="alert">Save failed</p>}
    <button onClick={() => setServer('external refresh')}>Refresh</button>
    <button onClick={() => setPending(true)}>Save</button>
    <button onClick={() => { setPending(false); setFailure(true); }}>Fail save</button>
    <button onClick={() => { setServer(draft.value); draft.saved(draft.value); setPending(false); }}>Finish save</button>
    <button onClick={() => preferences.setPreference('interface', 'coral')}>Coral</button>
    <button onClick={() => preferences.setPreference('language', 'es')}>Spanish</button>
    <Link to="?tab=network">Network tab</Link><Link to="/other">Other page</Link>
  </>;
}
function setup() {
  const router = createMemoryRouter([{ element: <AppPreferencesProvider><UnsavedChangesProvider><Outlet /></UnsavedChangesProvider></AppPreferencesProvider>, children: [
    { path: '/settings', element: <Editor /> }, { path: '/other', element: <h1>Other page</h1> },
  ] }], { initialEntries: ['/other', '/settings?tab=playback'], initialIndex: 1 });
  render(<RouterProvider router={router} />);
  return router;
}
beforeEach(() => localStorage.clear());

it('retains drafts through background refreshes and interface/language changes', async () => {
  setup();
  const input = screen.getByRole('textbox', { name: 'Value' });
  fireEvent.change(input, { target: { value: 'my draft' } });
  fireEvent.click(screen.getByText('Refresh'));
  fireEvent.click(screen.getByText('Coral'));
  fireEvent.click(screen.getByText('Spanish'));
  expect(screen.getByRole('textbox', { name: 'Value' })).toBe(input);
  expect(input).toHaveValue('my draft');
  fireEvent.click(screen.getByText('Network tab'));
  expect(await screen.findByRole('dialog', { name: '¿Descartar los cambios sin guardar?' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
  expect(input).toHaveValue('my draft');
});

it('blocks query tabs and browser Back, cancels without discarding, and leaves only on confirmation', async () => {
  const router = setup();
  fireEvent.change(screen.getByRole('textbox', { name: 'Value' }), { target: { value: 'draft' } });
  fireEvent.click(screen.getByText('Network tab'));
  expect(await screen.findByRole('dialog', { name: 'Discard unsaved changes?' })).toBeInTheDocument();
  expect(router.state.location.search).toBe('?tab=playback');
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  await act(async () => { await router.navigate(-1); });
  expect(await screen.findByRole('dialog', { name: 'Discard unsaved changes?' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Discard and leave' }));
  expect(await screen.findByRole('heading', { name: 'Other page' })).toBeInTheDocument();
});

it('keeps a failed save dirty and guards document unload', async () => {
  setup();
  fireEvent.change(screen.getByRole('textbox', { name: 'Value' }), { target: { value: 'draft' } });
  fireEvent.click(screen.getByText('Save'));
  fireEvent.click(screen.getByText('Fail save'));
  expect(screen.getByRole('alert')).toHaveTextContent('Save failed');
  const unload = new Event('beforeunload', { cancelable: true });
  window.dispatchEvent(unload);
  expect(unload.defaultPrevented).toBe(true);
  fireEvent.click(screen.getByText('Other page'));
  expect(await screen.findByRole('dialog', { name: 'Discard unsaved changes?' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  await waitFor(() => expect(screen.getByRole('textbox')).toHaveValue('draft'));
});

it('waits for an in-flight save before completing requested navigation', async () => {
  setup();
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'draft' } });
  fireEvent.click(screen.getByText('Save'));
  fireEvent.click(screen.getByText('Other page'));
  expect(await screen.findByRole('dialog', { name: 'Saving changes…' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Discard and leave' })).toBeDisabled();
  // Complete the existing request while its page is behind the modal.
  fireEvent.click(screen.getByRole('button', { name: 'Finish save', hidden: true }));
  expect(await screen.findByRole('heading', { name: 'Other page' })).toBeInTheDocument();
});
