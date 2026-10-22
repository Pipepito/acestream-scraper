import React from 'react';
import userEvent from '@testing-library/user-event';
import { act, render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { Route, Routes } from 'react-router-dom';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import Changelog from '../pages/Changelog';
import WhatsNewNotice from '../components/WhatsNewNotice';
import { currentRelease } from '../data/changelog';

const key = 'acestream.changelog.seen.v1';
const renderPage = (path = '/', mode: 'light' | 'dark' = 'light') => render(
  <ThemeProvider theme={createAppTheme(mode)}>
    <TestMemoryRouter initialEntries={[path]}>
      <WhatsNewNotice />
      <Routes>
        <Route path="/" element={<p>Overview</p>} />
        <Route path="/changelog" element={<Changelog />} />
      </Routes>
    </TestMemoryRouter>
  </ThemeProvider>
);

beforeEach(() => localStorage.setItem(key, 'v2.1.0'));
afterEach(() => jest.restoreAllMocks());

it.each(['light', 'dark'] as const)('opens readable version history and acknowledges the update in %s mode', async (mode) => {
  renderPage('/', mode);
  await userEvent.setup().click(screen.getByRole('link', { name: `What’s new in ${currentRelease.version}` }));
  expect(await screen.findByRole('heading', { name: 'Changelog', level: 1 })).toBeVisible();
  expect(screen.getByRole('heading', { name: 'v2.1.0' })).toBeVisible();
  expect(screen.getByRole('link', { name: 'v2.0.0' })).toHaveAttribute('href', '#v2.0.0');
  expect(localStorage.getItem(key)).toBe(currentRelease.version);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('dismisses persistently without navigating away', async () => {
  const view = renderPage();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Dismiss changelog notice' }));
  expect(screen.getByText('Overview')).toBeVisible();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  view.unmount();
  renderPage();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('acknowledges a direct visit and describes development builds without inventing publication dates', () => {
  renderPage('/changelog');
  expect(localStorage.getItem(key)).toBe(currentRelease.version);
  expect(screen.getByText(/Development builds may include changes before/)).toBeVisible();
});

it('responds to another tab acknowledging the current version', () => {
  renderPage();
  act(() => {
    localStorage.setItem(key, currentRelease.version);
    window.dispatchEvent(new Event('storage'));
  });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('dismisses when browser storage writes are unavailable', async () => {
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  renderPage();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Dismiss changelog notice' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
