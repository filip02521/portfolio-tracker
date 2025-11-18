import React, { ReactNode } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';

interface LazyLoadSectionProps {
  children: ReactNode;
  fallback?: ReactNode;
  rootMargin?: string;
  threshold?: number;
  minHeight?: number | string;
}

/**
 * Component that lazy loads its children when it enters the viewport
 * Useful for heavy components or sections that are below the fold
 */
export const LazyLoadSection: React.FC<LazyLoadSectionProps> = ({
  children,
  fallback,
  rootMargin = '100px',
  threshold = 0.1,
  minHeight = 200,
}) => {
  const [ref, isIntersecting] = useIntersectionObserver<HTMLDivElement>({
    rootMargin,
    threshold,
  });

  return (
    <Box ref={ref} sx={{ minHeight }}>
      {isIntersecting ? (
        children
      ) : (
        fallback || (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight,
            }}
          >
            <CircularProgress size={40} />
          </Box>
        )
      )}
    </Box>
  );
};

