import React from 'react';
import { Box, Skeleton, Card, CardContent } from '@mui/material';
import { ShimmerEffect } from './ShimmerEffect';

interface SkeletonLoaderProps {
  type?: 'dashboard' | 'portfolio' | 'table' | 'card' | 'watchlist-row';
  rows?: number;
  count?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ type = 'dashboard', rows = 3, count }) => {
  // If count is provided, render that many card skeletons
  if (count) {
    return (
      <Box>
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} sx={{ position: 'relative', overflow: 'hidden', mb: 3 }}>
            <CardContent>
              <Skeleton variant="text" width="60%" height={24} />
              <Skeleton variant="text" width="40%" height={20} sx={{ mt: 2 }} />
              <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
            </CardContent>
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                overflow: 'hidden',
                pointerEvents: 'none'
              }}
            >
              <ShimmerEffect />
            </Box>
          </Card>
        ))}
      </Box>
    );
  }
  if (type === 'dashboard') {
    return (
      <Box>
        {/* Hero Stats Skeleton */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} sx={{ position: 'relative', overflow: 'hidden' }}>
              <CardContent>
                <Skeleton variant="text" width="40%" height={24} />
                <Skeleton variant="text" width="60%" height={32} sx={{ mt: 1 }} />
                <Skeleton variant="text" width="30%" height={20} sx={{ mt: 1 }} />
              </CardContent>
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  overflow: 'hidden',
                  pointerEvents: 'none'
                }}
              >
                <ShimmerEffect />
              </Box>
            </Card>
          ))}
        </Box>

        {/* Chart Skeleton */}
        <Card sx={{ mb: 4, position: 'relative', overflow: 'hidden' }}>
          <CardContent>
            <Skeleton variant="text" width="30%" height={32} sx={{ mb: 3 }} />
            <Skeleton variant="rectangular" height={400} />
          </CardContent>
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              overflow: 'hidden',
              pointerEvents: 'none'
            }}
          >
            <ShimmerEffect />
          </Box>
        </Card>

        {/* Cards Skeleton */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
          {[1, 2].map((i) => (
            <Card key={i} sx={{ position: 'relative', overflow: 'hidden' }}>
              <CardContent>
                <Skeleton variant="text" width="50%" height={24} sx={{ mb: 2 }} />
                <Skeleton variant="text" width="80%" height={20} />
                <Skeleton variant="text" width="60%" height={20} />
                <Skeleton variant="text" width="70%" height={20} />
              </CardContent>
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  overflow: 'hidden',
                  pointerEvents: 'none'
                }}
              >
                <ShimmerEffect />
              </Box>
            </Card>
          ))}
        </Box>
      </Box>
    );
  }

  if (type === 'card') {
    return (
      <Card sx={{ position: 'relative', overflow: 'hidden' }}>
        <CardContent>
          <Skeleton variant="text" width="60%" height={24} />
          <Skeleton variant="text" width="40%" height={20} sx={{ mt: 2 }} />
          <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
        </CardContent>
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: 'hidden',
            pointerEvents: 'none'
          }}
        >
          <ShimmerEffect />
        </Box>
      </Card>
    );
  }

  if (type === 'table') {
    return (
      <Card sx={{ position: 'relative', overflow: 'hidden' }}>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          {[1, 2, 3, 4, 5].map((i) => (
            <Box key={i} sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Skeleton variant="rectangular" width="100%" height={56} />
            </Box>
          ))}
        </CardContent>
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: 'hidden',
            pointerEvents: 'none'
          }}
        >
          <ShimmerEffect />
        </Box>
      </Card>
    );
  }

  if (type === 'watchlist-row') {
    return (
      <Box>
        {[...Array(rows)].map((_, i) => (
          <Box key={i} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2, borderRadius: 2, border: '1px solid', borderColor: 'divider', mb: 1.5 }}>
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width={80} height={20} />
              <Skeleton variant="text" width={120} height={16} />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mr: 2 }}>
              <Skeleton variant="text" width={90} height={22} />
              <Skeleton variant="rectangular" width={80} height={24} />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Skeleton variant="circular" width={24} height={24} />
              <Skeleton variant="circular" width={24} height={24} />
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  return null;
};

