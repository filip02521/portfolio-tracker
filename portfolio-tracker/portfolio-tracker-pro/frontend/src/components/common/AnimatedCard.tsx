import React from 'react';
import { Card, CardProps } from '@mui/material';

interface AnimatedCardProps extends CardProps {
  delay?: number;
}

export const AnimatedCard: React.FC<AnimatedCardProps> = ({ 
  children, 
  delay = 0,
  ...props 
}) => {
  const [isVisible, setIsVisible] = React.useState(false);

  // Cap delay at 300ms to avoid cumulative lag
  const cappedDelay = Math.min(delay, 300);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, cappedDelay);

    return () => clearTimeout(timer);
  }, [cappedDelay]);

  return (
    <Card
      {...props}
      sx={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(10px)',
        transition: 'opacity 0.25s ease-in-out, transform 0.25s ease-in-out',
        willChange: isVisible ? 'auto' : 'transform, opacity',
        ...props.sx
      }}
    >
      {children}
    </Card>
  );
};


