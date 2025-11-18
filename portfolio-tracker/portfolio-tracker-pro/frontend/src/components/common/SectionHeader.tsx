import React from 'react';
import { Box, Typography, Stack, Tooltip, IconButton } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

export interface SectionHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  tooltip?: string;
  variant?: 'h4' | 'h5' | 'h6';
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  description,
  icon,
  tooltip,
  variant = 'h5',
}) => {
  return (
    <Box sx={{ mb: 2.5 }}>
      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: description ? 1 : 0 }}>
        {icon && (
          <Box sx={{ display: 'flex', alignItems: 'center', color: 'primary.main' }}>
            {icon}
          </Box>
        )}
        <Typography
          variant={variant}
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            flex: 1,
          }}
        >
          {title}
        </Typography>
        {tooltip && (
          <Tooltip title={tooltip} arrow placement="top">
            <IconButton size="small" sx={{ color: 'text.secondary', p: 0.5 }}>
              <InfoOutlinedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Stack>
      {description && (
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            lineHeight: 1.6,
            maxWidth: '80ch',
          }}
        >
          {description}
        </Typography>
      )}
    </Box>
  );
};

