import React from 'react';
import { Chip } from '@mui/material';
import { Star } from '@mui/icons-material';

interface PremiumBadgeProps {
  label: string;
  size?: 'small' | 'medium';
}

export const PremiumBadge: React.FC<PremiumBadgeProps> = ({ 
  label, 
  size = 'small' 
}) => {
  return (
    <Chip
      icon={<Star sx={{ color: '#F59E0B !important', fontSize: size === 'small' ? 14 : 16 }} />}
      label={label}
      size={size}
      sx={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(251, 191, 36, 0.2) 100%)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        color: '#FBBF24',
        fontWeight: 600,
        '& .MuiChip-label': {
          color: '#FBBF24'
        },
        '&:hover': {
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(251, 191, 36, 0.3) 100%)',
          borderColor: 'rgba(245, 158, 11, 0.5)'
        }
      }}
    />
  );
};


