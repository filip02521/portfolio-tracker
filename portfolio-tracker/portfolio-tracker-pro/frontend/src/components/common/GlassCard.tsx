import React from 'react';
import { Card, CardProps } from '@mui/material';

interface GlassCardProps extends CardProps {
  children: React.ReactNode;
  glowColor?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  glowColor = 'rgba(37, 99, 235, 0.1)',
  ...props
}) => {
  return (
    <Card
      {...props}
      sx={{
        background: 'rgba(30, 41, 59, 0.6)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 3,
        boxShadow: `0 8px 32px 0 rgba(0, 0, 0, 0.37), 0 0 0 1px ${glowColor} inset`,
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: `linear-gradient(90deg, transparent, ${glowColor}, transparent)`,
          opacity: 0.5,
        },
        '&:hover': {
          borderColor: 'rgba(255, 255, 255, 0.2)',
          boxShadow: `0 12px 48px 0 rgba(0, 0, 0, 0.5), 0 0 0 1px ${glowColor} inset`,
          transform: 'translateY(-2px)',
        },
        ...props.sx,
      }}
    >
      {children}
    </Card>
  );
};


