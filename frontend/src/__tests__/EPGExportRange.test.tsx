import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import EPGXmlOutputPanel from '../components/EPGXmlOutputPanel';
import { useDownloadEPGXML } from '../hooks/useEPG';
jest.mock('../hooks/useEPG', () => ({ useDownloadEPGXML: jest.fn() }));

it('names both date controls and preserves an explicit zero in the export request', async () => {
  const download = jest.fn().mockResolvedValue(undefined);
  (useDownloadEPGXML as jest.Mock).mockReturnValue({ mutateAsync: download, isPending: false });
  render(<EPGXmlOutputPanel onNotify={jest.fn()} />);
  const past = screen.getByRole('slider', { name: 'Past programmes (days)' });
  const future = screen.getByRole('slider', { name: 'Future programmes (days)' });
  fireEvent.change(past, { target: { value: '0' } });
  fireEvent.change(future, { target: { value: '0' } });
  expect(past).toHaveAttribute('aria-valuenow', '0');
  expect(future).toHaveAttribute('aria-valuenow', '0');
  fireEvent.click(screen.getByRole('button', { name: 'Generate and Download EPG XML' }));
  fireEvent.click(screen.getByRole('button', { name: 'Generate and Download EPG XML' }));
  await waitFor(() => expect(download).toHaveBeenCalledTimes(1));
  expect(download).toHaveBeenCalledWith({ search_term: '', favorites_only: false, days_back: 0, days_forward: 0 });
});
