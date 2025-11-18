import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Stack,
  Divider,
  Chip,
  useTheme,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import { KeyboardShortcut } from '../../hooks/useKeyboardShortcuts';

export interface KeyboardShortcutsDialogProps {
  open: boolean;
  onClose: () => void;
  shortcuts: KeyboardShortcut[];
}

const categoryLabels: Record<KeyboardShortcut['category'], string> = {
  navigation: 'Navigation',
  actions: 'Actions',
  modals: 'Modals',
  search: 'Search',
};

const categoryIcons: Record<KeyboardShortcut['category'], React.ReactNode> = {
  navigation: '🧭',
  actions: '⚡',
  modals: '📋',
  search: '🔍',
};

const formatKey = (shortcut: KeyboardShortcut): string => {
  const parts: string[] = [];
  
  if (shortcut.ctrlKey || shortcut.metaKey) {
    parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
  }
  if (shortcut.shiftKey) {
    parts.push('Shift');
  }
  if (shortcut.altKey) {
    parts.push('Alt');
  }
  
  // Format the main key
  let key = shortcut.key;
  if (key === 'Escape') {
    key = 'Esc';
  } else if (key.length === 1) {
    key = key.toUpperCase();
  }
  parts.push(key);
  
  return parts.join(' + ');
};

export const KeyboardShortcutsDialog: React.FC<KeyboardShortcutsDialogProps> = ({
  open,
  onClose,
  shortcuts,
}) => {
  const theme = useTheme();

  // Group shortcuts by category
  const groupedShortcuts = React.useMemo(() => {
    const groups: Record<KeyboardShortcut['category'], KeyboardShortcut[]> = {
      navigation: [],
      actions: [],
      modals: [],
      search: [],
    };

    shortcuts.forEach((shortcut) => {
      groups[shortcut.category].push(shortcut);
    });

    return groups;
  }, [shortcuts]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          boxShadow: theme.palette.mode === 'dark' 
            ? '0 8px 32px rgba(0, 0, 0, 0.4)' 
            : '0 8px 32px rgba(0, 0, 0, 0.12)',
        },
      }}
    >
      <DialogTitle>
        <Stack direction="row" spacing={2} alignItems="center">
          <KeyboardIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 700, flex: 1 }}>
            Keyboard Shortcuts
          </Typography>
          <Button
            onClick={onClose}
            size="small"
            sx={{ minWidth: 'auto', p: 1 }}
          >
            <CloseIcon />
          </Button>
        </Stack>
      </DialogTitle>
      
      <DialogContent>
        <Stack spacing={3}>
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => {
            if (categoryShortcuts.length === 0) {
              return null;
            }

            return (
              <Box key={category}>
                <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="h6" sx={{ fontSize: '1.25rem' }}>
                    {categoryIcons[category as KeyboardShortcut['category']]}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>
                    {categoryLabels[category as KeyboardShortcut['category']]}
                  </Typography>
                </Stack>
                
                <Stack spacing={1.5}>
                  {categoryShortcuts.map((shortcut, index) => (
                    <Box
                      key={`${shortcut.key}-${index}`}
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        py: 1.5,
                        px: 2,
                        borderRadius: 2,
                        backgroundColor: theme.palette.mode === 'dark'
                          ? 'rgba(255, 255, 255, 0.05)'
                          : 'rgba(0, 0, 0, 0.02)',
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark'
                            ? 'rgba(255, 255, 255, 0.08)'
                            : 'rgba(0, 0, 0, 0.04)',
                        },
                      }}
                    >
                      <Typography variant="body2" sx={{ flex: 1, fontWeight: 500 }}>
                        {shortcut.description}
                      </Typography>
                      <Chip
                        label={formatKey(shortcut)}
                        size="small"
                        sx={{
                          fontFamily: 'monospace',
                          fontWeight: 600,
                          backgroundColor: theme.palette.mode === 'dark'
                            ? 'rgba(255, 255, 255, 0.1)'
                            : 'rgba(0, 0, 0, 0.08)',
                          border: `1px solid ${theme.palette.divider}`,
                          '& .MuiChip-label': {
                            px: 1.5,
                          },
                        }}
                      />
                    </Box>
                  ))}
                </Stack>
                
                {category !== 'search' && <Divider sx={{ mt: 2 }} />}
              </Box>
            );
          })}
        </Stack>
      </DialogContent>
      
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} variant="contained" sx={{ borderRadius: 2, textTransform: 'none' }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

