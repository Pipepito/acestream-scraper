import React from 'react';
import { render, screen } from '@testing-library/react';

import TVChannelsTable from '../components/TVChannelsTable';

describe('TVChannelsTable', () => {
  const renderTable = (ui: React.ReactElement) => render(<div style={{ width: 1400, height: 700 }}>{ui}</div>);

  it('groups dense row actions under an accessible label', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            acestream_channels: [{ channel_id: 'ace-1' }],
          } as any,
        ]}
        loading={false}
        totalCount={1}
        page={0}
        pageSize={25}
        onPageChange={jest.fn()}
        onPageSizeChange={jest.fn()}
        onSortChange={jest.fn()}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
        onPlay={jest.fn()}
      />
    );

    expect(screen.getByRole('group', { name: 'TV channel actions for Arena TV' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'edit tv channel Arena TV' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'delete tv channel Arena TV' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'play tv channel Arena TV' })).toBeInTheDocument();
  });
});
