import React from 'react';
import { Box, keyframes } from '@mui/material';

const shimmer = keyframes`
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
`;

interface ShimmerEffectProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: number;
  sx?: any;
}

export const ShimmerEffect: React.FC<ShimmerEffectProps> = ({
  width = '100%',
  height = '100%',
  borderRadius = 1,
  sx
}) => {
  return (
    <Box
      sx={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, rgba(51, 65, 85, 0.3) 0%, rgba(37, 99, 235, 0.2) 50%, rgba(51, 65, 85, 0.3) 100%)',
        backgroundSize: '468px 100%',
        animation: `${shimmer} 1.5s ease-in-out infinite`,
        ...sx
      }}
    />
  );
};


