import React, { useEffect, useState } from 'react';
import { Box, keyframes } from '@mui/material';

const confettiFall = keyframes`
  0% {
    transform: translateY(-100vh) rotateZ(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotateZ(720deg);
    opacity: 0;
  }
`;

interface ConfettiAnimationProps {
  active: boolean;
  duration?: number;
  onComplete?: () => void;
}

export const ConfettiAnimation: React.FC<ConfettiAnimationProps> = ({
  active,
  duration = 3000,
  onComplete
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (active) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onComplete?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [active, duration, onComplete]);

  if (!visible) return null;

  const confettiCount = 50;
  const colors = ['#10B981', '#F59E0B', '#3B82F6', '#EF4444', '#8B5CF6'];

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 9999,
        overflow: 'hidden',
      }}
    >
      {Array.from({ length: confettiCount }).map((_, i) => {
        const left = `${(i * 100) / confettiCount}%`;
        const delay = Math.random() * 0.5;
        const duration = 2 + Math.random() * 2;
        const color = colors[Math.floor(Math.random() * colors.length)];

        return (
          <Box
            key={i}
            sx={{
              position: 'absolute',
              left,
              top: '-10px',
              width: 8,
              height: 8,
              backgroundColor: color,
              borderRadius: '50%',
              animation: `${confettiFall} ${duration}s linear ${delay}s forwards`,
            }}
          />
        );
      })}
    </Box>
  );
};


