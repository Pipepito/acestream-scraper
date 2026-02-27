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
    updateAcestreamChannel: jest.fn(),
  },
}));

describe('ChannelTable', () => {
  it('renders channel rows and action controls', () => {
    render(
      <ChannelTable
        channels={[
          {
            id: 'acestream-1',
            name: 'Test Channel',
            group: 'Sports',
            is_active: true,
            is_online: true,
            status: 'active',
            last_seen: '',
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

    expect(screen.getByText('Test Channel')).toBeInTheDocument();
    expect(screen.getByRole('grid')).toBeInTheDocument();
  });
});
