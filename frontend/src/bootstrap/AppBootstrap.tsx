import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { UnsavedChangesProvider } from '../components/UnsavedChanges';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../App';
import StartupGate from '../components/StartupGate';
import AccessGate from '../components/access/AccessGate';
import { createAppTheme, type ThemeMode } from '../theme';
import { AppPreferencesProvider, useAppPreferences } from '../preferences/AppPreferences';

type AppThemeModeValue = {
  mode: ThemeMode;
  setMode: React.Dispatch<React.SetStateAction<ThemeMode>>;
  toggleMode: () => void;
};

const router = createBrowserRouter([{ path: '*', element: (
  <AccessGate><StartupGate><UnsavedChangesProvider><App /></UnsavedChangesProvider></StartupGate></AccessGate>
) }]);

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

const ApplicationProviders: React.FC = () => {
  const preferences = useAppPreferences();
  const { mode, setPreference } = preferences;
  const theme = React.useMemo(() => createAppTheme(mode, preferences.interface, preferences.language), [mode, preferences.interface, preferences.language]);
  const handleSetMode = React.useCallback<React.Dispatch<React.SetStateAction<ThemeMode>>>((value) => {
    setPreference('mode', typeof value === 'function' ? value(mode) : value);
  }, [mode, setPreference]);

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
          <RouterProvider router={router} />
        </ThemeProvider>
      </AppThemeModeContext.Provider>
    </QueryClientProvider>
  );
};

const AppBootstrap = () => <AppPreferencesProvider><ApplicationProviders /></AppPreferencesProvider>;
export default AppBootstrap;
