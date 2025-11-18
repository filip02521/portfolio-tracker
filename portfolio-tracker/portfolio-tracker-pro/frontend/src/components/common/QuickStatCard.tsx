import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { TrendIndicator } from './TrendIndicator';

interface QuickStatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'error' | 'warning';
  onClick?: () => void;
}

export const QuickStatCard: React.FC<QuickStatCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  color = 'primary',
  onClick
}) => {
  return (
    <Card 
      onClick={onClick}
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: 4
        } : {},
        border: '1px solid',
        borderColor: 'divider',
        height: '100%'
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
            {title}
          </Typography>
          {icon && (
            <Box sx={{ color: `${color}.main` }}>
              {icon}
            </Box>
          )}
        </Box>
        
        <Typography 
          variant="h4" 
          sx={{ 
            fontWeight: 700, 
            mb: change !== undefined ? 1 : 0,
            color: `${color}.main`
          }}
        >
          {typeof value === 'number' ? value.toLocaleString() : value}
        </Typography>

        {change !== undefined && (
          <TrendIndicator
            value={change}
            showIcon
            showPercent
            label={changeLabel}
            size="small"
          />
        )}
      </CardContent>
    </Card>
  );
};


