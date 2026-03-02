import React from 'react';
import { render, screen } from '@testing-library/react';

import ChannelTable from '../components/ChannelTable';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status = 500) {
      super(message);
      this.status = status;
    }
  },
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock('../services/channelService', () => ({
  __esModule: true,
  acestreamChannelService: {
    updateAcestreamChannel: jest.fn().mockResolvedValue({}),
  },
}));

describe('Acestream channel operational table flow', () => {
  it('renders channel row content', () => {
    render(
      <ChannelTable
        channels={[
          {
            id: 'ace-100',
            name: 'Alpha Sports',
            group: 'Sports',
            status: 'active',
            is_online: true,
            is_active: true,
            last_seen: '2026-02-27T00:00:00Z',
            epg_update_protected: false,
          },
        ]}
        loading={false}
        onCheckStatus={jest.fn()}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
        checkingStatus={{}}
        filters={{}}
        onFilterChange={jest.fn()}
        totalCount={1}
        page={0}
        pageSize={25}
        onPaginationModelChange={jest.fn()}
        onSortChange={jest.fn()}
        onSelectionChange={jest.fn()}
      />
    );

    expect(screen.getByText('Alpha Sports')).toBeInTheDocument();
    expect(screen.getByRole('grid')).toBeInTheDocument();
  });

  it('renders multiple channels without crashing for mixed status values', () => {
    render(
      <ChannelTable
        channels={[
          {
            id: 'ace-101',
            name: 'Beta News',
            group: 'News',
            status: 'active',
            is_online: false,
            is_active: true,
            last_seen: '2026-02-27T00:00:00Z',
            epg_update_protected: false,
          },
          {
            id: 'ace-102',
            name: 'Gamma Movies',
            group: 'Movies',
            status: 'inactive',
            is_online: null,
            is_active: false,
            last_seen: '2026-02-27T00:00:00Z',
            epg_update_protected: false,
          },
        ]}
        loading={false}
        onCheckStatus={jest.fn()}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
        checkingStatus={{}}
        filters={{}}
        onFilterChange={jest.fn()}
        totalCount={1}
        page={0}
        pageSize={25}
        onPaginationModelChange={jest.fn()}
        onSortChange={jest.fn()}
        onSelectionChange={jest.fn()}
      />
    );

    expect(screen.getByText('Beta News')).toBeInTheDocument();
    expect(screen.getByText('Gamma Movies')).toBeInTheDocument();
  });
});
