import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../App';
import { createAppTheme, type ThemeMode } from '../theme';

const APP_THEME_MODE_STORAGE_KEY = 'app-theme-mode';

const isThemeMode = (value: string | null): value is ThemeMode => value === 'light' || value === 'dark';

const getSystemThemeMode = (): ThemeMode => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'light';
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const getInitialThemeMode = (): ThemeMode => {
  if (typeof window === 'undefined') {
    return 'light';
  }

  const storedMode = window.localStorage.getItem(APP_THEME_MODE_STORAGE_KEY);

  if (isThemeMode(storedMode)) {
    return storedMode;
  }

  return getSystemThemeMode();
};

const hasStoredThemeMode = (): boolean => {
  if (typeof window === 'undefined') {
    return false;
  }

  return isThemeMode(window.localStorage.getItem(APP_THEME_MODE_STORAGE_KEY));
};

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
  const [mode, setMode] = React.useState<ThemeMode>(() => getInitialThemeMode());
  const [hasExplicitPreference, setHasExplicitPreference] = React.useState<boolean>(() => hasStoredThemeMode());
  const theme = React.useMemo(() => createAppTheme(mode), [mode]);

  React.useEffect(() => {
    if (typeof window === 'undefined' || !hasExplicitPreference) {
      return;
    }

    window.localStorage.setItem(APP_THEME_MODE_STORAGE_KEY, mode);
  }, [hasExplicitPreference, mode]);

  const handleSetMode = React.useCallback<React.Dispatch<React.SetStateAction<ThemeMode>>>((value) => {
    setHasExplicitPreference(true);
    setMode(value);
  }, []);

  const controller = React.useMemo<AppThemeModeValue>(
    () => ({
      mode,
      setMode: handleSetMode,
      toggleMode: () => handleSetMode((currentMode) => getNextMode(currentMode)),
    }),
    [handleSetMode, mode]
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
