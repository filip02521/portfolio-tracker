import { createTheme, Theme } from '@mui/material/styles';

export const createAppTheme = (mode: 'light' | 'dark'): Theme => {
  const isLight = mode === 'light';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#2563EB', // Deep Blue
        light: '#3B82F6',
        dark: '#1E40AF',
      },
      secondary: {
        main: '#10B981', // Emerald Green
        light: '#34D399',
        dark: '#047857',
      },
      success: {
        main: '#10B981',
        light: '#34D399',
        dark: '#047857',
      },
      warning: {
        main: '#F59E0B',
        light: '#FBBF24',
        dark: '#D97706',
      },
      error: {
        main: '#DC2626',
        light: '#F87171',
        dark: '#B91C1C',
      },
      info: {
        main: '#3B82F6',
        light: '#60A5FA',
        dark: '#2563EB',
      },
      background: {
        default: isLight ? '#FAFBFC' : '#1A202C',
        paper: isLight ? '#FFFFFF' : '#2D3748',
      },
      text: {
        primary: isLight ? '#0F172A' : '#F8FAFC',
        secondary: isLight ? '#64748B' : '#E2E8F0',
      },
      divider: isLight ? '#CBD5E0' : 'rgba(226, 232, 240, 0.16)',
    },
    typography: {
      fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
      h1: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 700,
        fontSize: '2.75rem',
        letterSpacing: '-0.02em',
      },
      h2: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 600,
        fontSize: '2rem',
        letterSpacing: '-0.01em',
      },
      h3: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 600,
        fontSize: '1.5rem',
      },
      h4: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 600,
        fontSize: '1.25rem',
      },
      h5: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 600,
        fontSize: '1.125rem',
      },
      h6: {
        fontFamily: '"Outfit", sans-serif',
        fontWeight: 600,
        fontSize: '1rem',
      },
      body1: {
        lineHeight: 1.6,
      },
      body2: {
        lineHeight: 1.6,
      },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            background: isLight
              ? '#FFFFFF'
              : '#2D3748',
            border: `1px solid ${isLight ? '#E2E8F0' : 'rgba(226, 232, 240, 0.12)'}`,
            backdropFilter: isLight ? 'none' : 'none',
            borderRadius: '16px',
            boxShadow: isLight 
              ? '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)'
              : '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              borderColor: isLight
                ? 'rgba(37, 99, 235, 0.4)'
                : 'rgba(37, 99, 235, 0.5)',
              boxShadow: isLight
                ? '0 8px 24px rgba(37, 99, 235, 0.12), 0 4px 12px rgba(0, 0, 0, 0.08)'
                : '0 8px 24px rgba(37, 99, 235, 0.2), 0 4px 12px rgba(0, 0, 0, 0.3)',
              transform: 'translateY(-2px)',
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: '12px',
            textTransform: 'none',
            fontWeight: 600,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            padding: '10px 24px',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 6px 20px rgba(37, 99, 235, 0.3)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
            '&.Mui-disabled': {
              opacity: 0.7,
            },
          },
          contained: {
            boxShadow: '0 2px 8px rgba(37, 99, 235, 0.2)',
            '&:hover': {
              boxShadow: '0 6px 24px rgba(37, 99, 235, 0.4)',
            },
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            '&:focus-visible': {
              outline: '2px solid',
              outlineColor: 'primary.main',
              outlineOffset: '2px',
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            '&:focus-visible': {
              outline: '2px solid',
              outlineColor: 'primary.main',
              outlineOffset: '2px',
            },
          },
          outlined: {
            borderColor: isLight ? '#CBD5E0' : 'rgba(226, 232, 240, 0.16)',
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            height: 6,
            borderRadius: 4,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: isLight
              ? 'linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)'
              : 'linear-gradient(135deg, #1E40AF 0%, #2563EB 100%)',
            boxShadow: isLight
              ? '0 2px 8px rgba(37, 99, 235, 0.15)'
              : '0 4px 16px rgba(0, 0, 0, 0.2)',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          elevation1: {
            boxShadow: isLight
              ? '0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)'
              : '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)',
          },
          elevation2: {
            boxShadow: isLight
              ? '0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)'
              : '0 4px 6px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)',
          },
          elevation8: {
            boxShadow: isLight
              ? '0 10px 24px rgba(0, 0, 0, 0.15), 0 4px 8px rgba(0, 0, 0, 0.1)'
              : '0 10px 24px rgba(0, 0, 0, 0.5), 0 4px 8px rgba(0, 0, 0, 0.4)',
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 16,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              '&:focus-within': {
                outline: '2px solid transparent',
              },
            },
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderColor: isLight ? '#CBD5E0' : 'rgba(226, 232, 240, 0.16)',
          },
          head: {
            fontWeight: 600,
            backgroundColor: isLight ? '#F8FAFC' : '#1E293B',
          },
        },
      },
    },
  });
};

export default createAppTheme;

