import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AddIcon from '@mui/icons-material/Add';
import NotificationsIcon from '@mui/icons-material/Notifications';
import AssessmentIcon from '@mui/icons-material/Assessment';
import GetAppIcon from '@mui/icons-material/GetApp';
import RefreshIcon from '@mui/icons-material/Refresh';
import SyncIcon from '@mui/icons-material/Sync';
import { searchService, SearchResult } from '../../services/searchService';
import { logger } from '../../utils/logger';

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onAction?: (actionId: string) => void;
}

const getResultIcon = (result: SearchResult): React.ReactNode => {
  if (result.icon) {
    return <Box sx={{ fontSize: '1.25rem' }}>{result.icon}</Box>;
  }

  switch (result.type) {
    case 'asset':
      return <TrendingUpIcon fontSize="small" />;
    case 'action':
      switch (result.id) {
        case 'action-add-transaction':
          return <AddIcon fontSize="small" />;
        case 'action-set-alert':
          return <NotificationsIcon fontSize="small" />;
        case 'action-view-analytics':
          return <AssessmentIcon fontSize="small" />;
        case 'action-export-pdf':
          return <GetAppIcon fontSize="small" />;
        case 'action-refresh':
          return <RefreshIcon fontSize="small" />;
        case 'action-sync-trades':
          return <SyncIcon fontSize="small" />;
        default:
          return <SearchIcon fontSize="small" />;
      }
    case 'page':
      return <SearchIcon fontSize="small" />;
    default:
      return <SearchIcon fontSize="small" />;
  }
};

const getTypeLabel = (type: SearchResult['type']): string => {
  switch (type) {
    case 'asset':
      return 'Asset';
    case 'action':
      return 'Action';
    case 'page':
      return 'Page';
    case 'transaction':
      return 'Transaction';
    default:
      return 'Result';
  }
};

const getTypeColor = (type: SearchResult['type'], theme: any): string => {
  switch (type) {
    case 'asset':
      return theme.palette.success.main;
    case 'action':
      return theme.palette.primary.main;
    case 'page':
      return theme.palette.info.main;
    case 'transaction':
      return theme.palette.warning.main;
    default:
      return theme.palette.text.secondary;
  }
};

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  open,
  onClose,
  onAction,
}) => {
  const theme = useTheme();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Focus input when dialog opens
  useEffect(() => {
    if (open) {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [open]);

  // Perform search with debounce
  useEffect(() => {
    if (!open) {
      return;
    }

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!query || query.trim().length === 0) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const searchResults = await searchService.search(query, { limit: 10 });
        setResults(searchResults);
        setSelectedIndex(0);
      } catch (error) {
        logger.error('Search failed', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200); // 200ms debounce

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query, open]);

  const handleSelect = useCallback((result: SearchResult) => {
    try {
      // Handle navigation for pages
      if (result.type === 'page') {
        const path = result.id.replace('page-', '');
        window.location.href = path;
        onClose();
        return;
      }

      // Handle actions
      if (result.type === 'action') {
        const actionId = result.id.replace('action-', '');
        
        switch (actionId) {
          case 'add-transaction':
            window.location.href = '/transactions';
            // Store state in sessionStorage for dialog opening
            sessionStorage.setItem('transactions:openDialog', 'true');
            break;
          case 'set-alert':
            window.location.href = '/price-alerts';
            break;
          case 'view-analytics':
            window.location.href = '/analytics';
            break;
          case 'export-pdf':
            window.location.href = '/portfolio';
            setTimeout(() => {
              const exportButton = document.querySelector('[aria-label*="Export"]') as HTMLElement;
              if (exportButton) exportButton.click();
            }, 100);
            break;
          case 'refresh':
            // Trigger refresh event
            window.dispatchEvent(new CustomEvent('dashboard:refresh'));
            break;
          case 'sync-trades':
            // Trigger sync event
            window.dispatchEvent(new CustomEvent('dashboard:sync'));
            break;
          default:
            logger.warn('Unknown action', { actionId });
        }
        
        if (onAction) {
          onAction(actionId);
        }
        onClose();
        return;
      }

      // Handle assets
      if (result.type === 'asset') {
        // Navigate to portfolio or focus on asset
        window.location.href = '/portfolio';
        // Could emit an event to focus on the asset
        window.dispatchEvent(new CustomEvent('portfolio:focus-asset', { detail: { symbol: result.title } }));
        onClose();
        return;
      }

      // Execute the result's action
      result.action();
      onClose();
    } catch (error) {
      logger.error('Failed to execute search result action', error);
    }
  }, [onClose, onAction]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    } else if (event.key === 'Escape') {
      event.preventDefault();
      onClose();
    }
  }, [results, selectedIndex, handleSelect, onClose]);

  // Group results by type
  const groupedResults = React.useMemo(() => {
    const groups: Record<SearchResult['type'], SearchResult[]> = {
      action: [],
      asset: [],
      page: [],
      transaction: [],
    };

    results.forEach((result) => {
      groups[result.type].push(result);
    });

    return groups;
  }, [results]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          boxShadow: theme.palette.mode === 'dark'
            ? '0 8px 32px rgba(0, 0, 0, 0.4)'
            : '0 8px 32px rgba(0, 0, 0, 0.12)',
          mt: 8,
        },
      }}
    >
      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ p: 2, pb: 1 }}>
          <TextField
            inputRef={inputRef}
            fullWidth
            placeholder="Search assets, pages, actions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              sx: {
                fontSize: '1rem',
              },
            }}
            autoFocus
            autoComplete="off"
          />
        </Box>

        {loading && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Searching...
            </Typography>
          </Box>
        )}

        {!loading && results.length === 0 && query && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No results found
            </Typography>
          </Box>
        )}

        {!loading && results.length > 0 && (
          <List sx={{ maxHeight: 400, overflow: 'auto', p: 0 }}>
            {Object.entries(groupedResults).map(([type, typeResults]) => {
              if (typeResults.length === 0) {
                return null;
              }

              return (
                <React.Fragment key={type}>
                  {type !== 'action' && <Divider />}
                  {typeResults.map((result, index) => {
                    const globalIndex = results.indexOf(result);
                    const isSelected = globalIndex === selectedIndex;
                    const typeColor = getTypeColor(result.type, theme);

                    return (
                      <ListItem
                        key={result.id}
                        disablePadding
                        sx={{
                          backgroundColor: isSelected
                            ? alpha(typeColor, 0.1)
                            : 'transparent',
                          '&:hover': {
                            backgroundColor: alpha(typeColor, 0.15),
                          },
                        }}
                      >
                        <ListItemButton
                          onClick={() => handleSelect(result)}
                          selected={isSelected}
                          sx={{
                            py: 1.5,
                            px: 2,
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            {getResultIcon(result)}
                          </ListItemIcon>
                          <ListItemText
                            primary={result.title}
                            secondary={result.subtitle}
                            primaryTypographyProps={{
                              sx: { fontWeight: isSelected ? 600 : 500 },
                            }}
                          />
                          <Chip
                            label={getTypeLabel(result.type)}
                            size="small"
                            sx={{
                              height: 20,
                              fontSize: '0.7rem',
                              backgroundColor: alpha(typeColor, 0.1),
                              color: typeColor,
                              fontWeight: 600,
                            }}
                          />
                        </ListItemButton>
                      </ListItem>
                    );
                  })}
                </React.Fragment>
              );
            })}
          </List>
        )}

        {!loading && !query && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Start typing to search...
            </Typography>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

