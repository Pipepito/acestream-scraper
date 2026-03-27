import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from 'react-query';
import App from '../App';
import { createAppTheme, type ThemeMode } from '../theme';

type AppThemeModeValue = {
  mode: ThemeMode;
  setMode: React.Dispatch<React.SetStateAction<ThemeMode>>;
  toggleMode: () => void;
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AppThemeModeContext = React.createContext<AppThemeModeValue | null>(null);

const getNextMode = (mode: ThemeMode): ThemeMode => (mode === 'light' ? 'dark' : 'light');

export const useAppThemeMode = () => {
  const context = React.useContext(AppThemeModeContext);

  if (!context) {
    throw new Error('useAppThemeMode must be used within AppBootstrap');
  }

  return context;
};

const AppBootstrap: React.FC = () => {
  const [mode, setMode] = React.useState<ThemeMode>('light');
  const theme = React.useMemo(() => createAppTheme(mode), [mode]);
  const controller = React.useMemo<AppThemeModeValue>(
    () => ({
      mode,
      setMode,
      toggleMode: () => setMode((currentMode) => getNextMode(currentMode)),
    }),
    [mode]
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AppThemeModeContext.Provider value={controller}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <App />
          </BrowserRouter>
        </ThemeProvider>
      </AppThemeModeContext.Provider>
    </QueryClientProvider>
  );
};

export default AppBootstrap;
