import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ChannelArtwork from '../components/livetv/ChannelArtwork';
import type { TVChannel } from '../types/tvChannelTypes';

it('uses the saved logo, then the mapped guide logo, then category decoration', () => {
  const channel = { id: 1, name: 'One', logo_url: '/logo.png', epg_logo_url: '/guide.png', category: 'sports' } as TVChannel;
  const view = render(<ChannelArtwork channel={channel} />);
  expect(screen.getByRole('img', { name: 'One' })).toHaveAttribute('src', '/logo.png');
  fireEvent.error(screen.getByRole('img', { name: 'One' }));
  expect(screen.getByRole('img', { name: 'One' })).toHaveAttribute('src', '/guide.png');
  fireEvent.error(screen.getByRole('img', { name: 'One' }));
  expect(screen.queryByRole('img', { name: 'One' })).not.toBeInTheDocument();
  expect(screen.getByText('Channel category illustration · sports')).toBeInTheDocument();
  view.rerender(<ChannelArtwork channel={{ ...channel, logo_url: '/replacement.png' }} />);
  expect(screen.getByRole('img', { name: 'One' })).toHaveAttribute('src', '/replacement.png');
});
