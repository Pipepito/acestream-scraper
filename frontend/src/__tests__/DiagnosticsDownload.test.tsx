import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import DiagnosticsDownload from '../components/DiagnosticsDownload';
import { systemService } from '../services/systemService';

jest.mock('../services/systemService', () => ({ systemService: { downloadDiagnostics: jest.fn() } }));
const download = systemService.downloadDiagnostics as jest.Mock;

beforeEach(() => download.mockReset());

test('downloads once and displays progress while gathering', async () => {
  let finish: () => void = () => undefined;
  download.mockImplementation(() => new Promise<void>((resolve) => { finish = resolve; }));
  render(<DiagnosticsDownload />);
  fireEvent.click(screen.getByRole('button', { name: 'Download diagnostics' }));
  expect(screen.getByRole('button', { name: 'Gathering diagnostics…' })).toBeDisabled();
  expect(download).toHaveBeenCalledTimes(1);
  finish();
  await waitFor(() => expect(screen.getByRole('button', { name: 'Download diagnostics' })).toBeEnabled());
});

test('allows retry after a failed download', async () => {
  download.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(undefined);
  render(<DiagnosticsDownload />);
  fireEvent.click(screen.getByRole('button', { name: 'Download diagnostics' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not download diagnostics');
  fireEvent.click(screen.getByRole('button', { name: 'Download diagnostics' }));
  await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  expect(download).toHaveBeenCalledTimes(2);
});
