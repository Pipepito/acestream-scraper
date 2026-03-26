import React from 'react';

jest.mock('react-dom/client', () => ({
  __esModule: true,
  default: {
    createRoot: jest.fn(() => ({ render: jest.fn() })),
  },
  createRoot: jest.fn(() => ({ render: jest.fn() })),
}));

jest.mock('../App', () => ({
  __esModule: true,
  default: () => <div>mock-app</div>,
}));

describe('index bootstrap', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="root"></div>';
    jest.resetModules();
  });

  it('renders the app with the default theme export shape', async () => {
    await import('../index');

    const reactDomClient = await import('react-dom/client');
    const createRootMock = jest.mocked(reactDomClient.default.createRoot);
    const renderMock = jest.mocked(createRootMock.mock.results[0]?.value?.render);

    expect(createRootMock).toHaveBeenCalledWith(document.getElementById('root'));
    expect(renderMock).toHaveBeenCalledTimes(1);
  });
});
