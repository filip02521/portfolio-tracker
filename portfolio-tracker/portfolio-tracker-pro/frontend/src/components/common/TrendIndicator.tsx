import React from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

interface TrendIndicatorProps {
  value: number;
  showIcon?: boolean;
  showPercent?: boolean;
  label?: string;
  size?: 'small' | 'medium' | 'large';
}

export const TrendIndicator: React.FC<TrendIndicatorProps> = ({
  value,
  showIcon = true,
  showPercent = true,
  label,
  size = 'medium'
}) => {
  const theme = useTheme();
  const isPositive = value > 0;
  const isNegative = value < 0;
  const isZero = value === 0;

  // Use green for positive (wealth), gold/amber for very positive, red only for losses
  const color = isPositive && value > 5 ? theme.palette.warning.main : // Gold for big wins
                isPositive ? theme.palette.success.main : // Green for gains
                isNegative ? theme.palette.error.main : 
                theme.palette.text.secondary;

  const iconSize = size === 'small' ? 16 : size === 'large' ? 24 : 20;
  const textSize = size === 'small' ? 'body2' : size === 'large' ? 'h6' : 'body1';

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {showIcon && (
        <>
          {isPositive && <TrendingUp sx={{ fontSize: iconSize, color }} />}
          {isNegative && <TrendingDown sx={{ fontSize: iconSize, color }} />}
          {isZero && <Remove sx={{ fontSize: iconSize, color }} />}
        </>
      )}
      <Typography 
        variant={textSize} 
        sx={{ 
          color,
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5
        }}
      >
        {label && <span>{label}:</span>}
        {showPercent && (
          <span>{isPositive ? '+' : ''}{value.toFixed(2)}%</span>
        )}
        {!showPercent && (
          <span>{value > 0 ? '+' : ''}{value.toLocaleString()}</span>
        )}
      </Typography>
    </Box>
  );
};

