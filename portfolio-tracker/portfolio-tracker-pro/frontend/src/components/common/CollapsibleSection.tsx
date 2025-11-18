import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Card,
  CardContent,
} from '@mui/material';
import { ExpandMore } from '@mui/icons-material';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  storageKey?: string; // Key for localStorage persistence
  sx?: any;
}

export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  children,
  defaultExpanded = false,
  storageKey,
  sx
}) => {
  // Load initial state from localStorage if storageKey is provided
  const [expanded, setExpanded] = useState<boolean>(() => {
    if (storageKey) {
      try {
        const stored = localStorage.getItem(storageKey);
        if (stored !== null) {
          return stored === 'true';
        }
      } catch (error) {
        // localStorage might not be available
        console.debug('Failed to load collapsible section state', error);
      }
    }
    return defaultExpanded;
  });

  // Save state to localStorage when it changes
  useEffect(() => {
    if (storageKey) {
      try {
        localStorage.setItem(storageKey, expanded.toString());
      } catch (error) {
        console.debug('Failed to save collapsible section state', error);
      }
    }
  }, [expanded, storageKey]);

  return (
    <Card sx={{ mb: 2, ...sx }}>
      <CardContent sx={{ p: 0 }}>
        <Box
          onClick={() => setExpanded(!expanded)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 3,
            cursor: 'pointer',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.02)',
            },
            transition: 'background-color 0.2s ease-in-out',
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
          <IconButton
            size="small"
            sx={{
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease-in-out',
            }}
          >
            <ExpandMore />
          </IconButton>
        </Box>
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box sx={{ px: 3, pb: 3 }}>
            {children}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};


