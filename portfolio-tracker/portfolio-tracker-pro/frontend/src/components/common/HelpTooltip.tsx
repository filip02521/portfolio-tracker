import React from 'react';
import { Tooltip, IconButton } from '@mui/material';
import { HelpOutline } from '@mui/icons-material';

interface HelpTooltipProps {
  title: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'small' | 'medium';
}

export const HelpTooltip: React.FC<HelpTooltipProps> = ({ 
  title, 
  placement = 'top',
  size = 'small'
}) => {
  return (
    <Tooltip title={title} placement={placement} arrow>
      <IconButton 
        size={size} 
        sx={{ 
          padding: 0.5,
          opacity: 0.6,
          '&:hover': { opacity: 1 }
        }}
      >
        <HelpOutline fontSize={size} />
      </IconButton>
    </Tooltip>
  );
};


