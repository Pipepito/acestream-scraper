import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0f766e',
      dark: '#115e59',
      light: '#14b8a6',
    },
    secondary: {
      main: '#0b5ed7',
    },
    background: {
      default: '#f3f6fb',
      paper: '#ffffff',
    },
    text: {
      primary: '#10212f',
      secondary: '#41556a',
    },
  },
  typography: {
    fontFamily: [
      '"IBM Plex Sans"',
      'system-ui',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#10212f',
          borderBottom: '1px solid rgba(16, 33, 47, 0.08)',
          backdropFilter: 'blur(6px)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderColor: 'rgba(16, 33, 47, 0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 10,
          fontWeight: 600,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 8px 24px rgba(15, 118, 110, 0.22)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          border: '1px solid rgba(16, 33, 47, 0.08)',
          boxShadow: '0 8px 20px rgba(16, 33, 47, 0.06)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  },
});

export default theme;
