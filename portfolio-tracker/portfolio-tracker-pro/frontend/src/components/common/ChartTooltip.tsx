import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  valueFormatter?: (value: number) => string;
}

export const ChartTooltip: React.FC<ChartTooltipProps> = ({
  active,
  payload,
  label,
  valueFormatter = (value) => value.toLocaleString()
}) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <Paper
      sx={{
        p: 1.5,
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        boxShadow: 4
      }}
    >
      <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
        {label}
      </Typography>
      {payload.map((entry: any, index: number) => (
        <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: entry.color
            }}
          />
          <Typography variant="body2" color="text.secondary">
            {entry.name}:
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {valueFormatter(entry.value)}
          </Typography>
        </Box>
      ))}
    </Paper>
  );
};


