import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

jest.mock('../App', () => ({
  __esModule: true,
  default: function MockApp() {
    const { useTheme } = require('@mui/material/styles');
    const { useAppThemeMode } = require('../bootstrap/AppBootstrap');
    const theme = useTheme();
    const { mode, setMode, toggleMode } = useAppThemeMode();

    return (
      <div>
        <div data-testid="theme-mode">{theme.palette.mode}</div>
        <div data-testid="controller-mode">{mode}</div>
        <button type="button" onClick={() => setMode('dark')}>
          force dark
        </button>
        <button type="button" onClick={toggleMode}>
          toggle theme
        </button>
      </div>
    );
  },
}));

describe('index entrypoint', () => {
  beforeEach(() => {
    // eslint-disable-next-line testing-library/no-node-access
    document.body.innerHTML = '<div id="root"></div>';
  });

  afterEach(() => {
    jest.dontMock('react-dom/client');
    jest.dontMock('../bootstrap/AppBootstrap');
  });

  it('creates the root from #root and renders AppBootstrap inside StrictMode', () => {
    const renderApp = jest.fn();
    const createRoot = jest.fn(() => ({ render: renderApp }));
    const AppBootstrap = jest.fn(() => null);
    // eslint-disable-next-line testing-library/no-node-access
    const rootElement = document.getElementById('root');

    jest.isolateModules(() => {
      jest.doMock('react-dom/client', () => ({
        __esModule: true,
        default: { createRoot },
      }));
      jest.doMock('../bootstrap/AppBootstrap', () => ({
        __esModule: true,
        default: AppBootstrap,
      }));

      require('../index');
    });

    expect(rootElement).not.toBeNull();
    expect(createRoot).toHaveBeenCalledWith(rootElement);
    expect(renderApp).toHaveBeenCalledTimes(1);

    const renderedTree = renderApp.mock.calls[0][0] as React.ReactElement<{
      children: React.ReactElement;
    }>;

    expect(renderedTree.type).toBe(React.StrictMode);
    // eslint-disable-next-line testing-library/no-node-access
    expect(renderedTree.props.children.type).toBe(AppBootstrap);
  });
});

describe('AppBootstrap', () => {
  it('mounts the app with a real light-default theme controller that can switch to dark at runtime', async () => {
    const { default: AppBootstrap } = await import('../bootstrap/AppBootstrap');

    render(<AppBootstrap />);

    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
    expect(screen.getByTestId('controller-mode')).toHaveTextContent('light');

    fireEvent.click(screen.getByRole('button', { name: 'force dark' }));

    expect(screen.getByTestId('theme-mode')).toHaveTextContent('dark');
    expect(screen.getByTestId('controller-mode')).toHaveTextContent('dark');

    fireEvent.click(screen.getByRole('button', { name: 'toggle theme' }));

    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
    expect(screen.getByTestId('controller-mode')).toHaveTextContent('light');
  });

  it('renders without React Router future-flag warnings', async () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    const { default: AppBootstrap } = await import('../bootstrap/AppBootstrap');

    render(<AppBootstrap />);

    expect(
      warnSpy.mock.calls.some(
        ([message]) =>
          typeof message === 'string' && message.includes('React Router Future Flag Warning')
      )
    ).toBe(false);

    warnSpy.mockRestore();
  });
});
