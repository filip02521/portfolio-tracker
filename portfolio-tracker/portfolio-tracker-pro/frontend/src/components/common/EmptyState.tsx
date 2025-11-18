import React, { useEffect, useState } from 'react';
import { Box, Typography, Button, keyframes } from '@mui/material';
import { 
  Inbox, 
  TrendingUp, 
  AccountBalance, 
  Assessment,
  Category 
} from '@mui/icons-material';

interface EmptyStateProps {
  type: 'portfolio' | 'transactions' | 'goals' | 'analytics' | 'insights' | 'performance';
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyStateConfig: Record<string, { icon: React.ReactNode; defaultTitle: string; defaultMessage: string }> = {
  portfolio: {
    icon: <AccountBalance sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Assets Found',
    defaultMessage: 'Your portfolio is empty. Connect your exchange accounts to start tracking your investments.'
  },
  transactions: {
    icon: <TrendingUp sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Transactions Yet',
    defaultMessage: 'Start tracking your investments by adding your first transaction.'
  },
  goals: {
    icon: <Assessment sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Goals Set',
    defaultMessage: 'Create investment goals to track your progress and stay motivated.'
  },
  analytics: {
    icon: <Category sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Data Available',
    defaultMessage: 'Add some transactions to see analytics and insights.'
  },
  insights: {
    icon: <Inbox sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Insights Yet',
    defaultMessage: 'We need some portfolio data to generate insights. Add your assets first.'
  },
  performance: {
    icon: <TrendingUp sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.5 }} />,
    defaultTitle: 'No Performance Data',
    defaultMessage: 'Performance history will appear after you add transactions and the system tracks your portfolio over time.'
  }
};

const floatAnimation = keyframes`
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
`;

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const EmptyState: React.FC<EmptyStateProps> = ({
  type,
  title,
  message,
  actionLabel,
  onAction
}) => {
  const config = EmptyStateConfig[type] || EmptyStateConfig.insights;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      py: 8,
      px: 3,
      textAlign: 'center'
    }}>
      <Box 
        sx={{ 
          mb: 3,
          animation: mounted ? `${floatAnimation} 3s ease-in-out infinite` : 'none',
        }}
      >
        <Box
          sx={{
            display: 'inline-block',
            p: 3,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
            border: '1px solid rgba(37, 99, 235, 0.2)',
          }}
        >
          {config.icon}
        </Box>
      </Box>
      <Typography 
        variant="h5" 
        sx={{ 
          fontWeight: 600, 
          mb: 1,
          animation: mounted ? `${fadeInUp} 0.6s ease-out` : 'none',
        }}
      >
        {title || config.defaultTitle}
      </Typography>
      <Typography 
        variant="body1" 
        color="text.secondary" 
        sx={{ 
          mb: 3, 
          maxWidth: 400,
          animation: mounted ? `${fadeInUp} 0.6s ease-out 0.2s both` : 'none',
        }}
      >
        {message || config.defaultMessage}
      </Typography>
      {onAction && actionLabel && (
        <Button 
          variant="contained" 
          onClick={onAction}
          sx={{
            animation: mounted ? `${fadeInUp} 0.6s ease-out 0.4s both` : 'none',
            mt: 1
          }}
        >
          {actionLabel}
        </Button>
      )}
    </Box>
  );
};

