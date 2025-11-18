import React, { useState } from 'react';
import {
  Box,
  Fab,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
} from '@mui/material';
import {
  Add,
  Notifications,
  TrendingUp,
  Assessment,
  GetApp,
  Settings,
  Close,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface QuickActionsToolbarProps {
  newAlertsCount?: number;
}

export const QuickActionsToolbar: React.FC<QuickActionsToolbarProps> = ({
  newAlertsCount = 0
}) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action: string) => {
    handleClose();
    switch (action) {
      case 'add-transaction':
        navigate('/transactions', { state: { openDialog: true } });
        break;
      case 'set-alert':
        navigate('/price-alerts');
        break;
      case 'view-analytics':
        navigate('/analytics');
        break;
      case 'export-pdf':
        // Trigger PDF export via portfolioService
        navigate('/portfolio');
        setTimeout(() => {
          const exportButton = document.querySelector('[aria-label*="Export"]') as HTMLElement;
          if (exportButton) exportButton.click();
        }, 100);
        break;
      case 'settings':
        navigate('/settings');
        break;
      default:
        break;
    }
  };

  return (
    <>
      <Tooltip title="Quick Actions" placement="left">
        <Fab
          color="primary"
          aria-label="quick actions"
          onClick={handleClick}
          sx={{
            position: 'fixed',
            bottom: { xs: 24, md: 32 },
            right: { xs: 24, md: 32 },
            zIndex: 1000,
            boxShadow: '0 8px 24px rgba(37, 99, 235, 0.3)',
            background: 'linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%)',
              transform: 'scale(1.1)',
              boxShadow: '0 12px 32px rgba(37, 99, 235, 0.4)',
            },
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          {open ? <Close /> : <Add />}
        </Fab>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            mt: -2,
            minWidth: 240,
            borderRadius: 3,
            background: 'rgba(30, 41, 59, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          },
        }}
      >
        <MenuItem onClick={() => handleAction('add-transaction')}>
          <ListItemIcon>
            <Add sx={{ color: 'primary.main' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Add Transaction"
            secondary="Record new trade"
          />
        </MenuItem>

        <MenuItem onClick={() => handleAction('set-alert')}>
          <ListItemIcon>
            <Badge badgeContent={newAlertsCount > 0 ? newAlertsCount : undefined} color="error">
              <Notifications sx={{ color: 'warning.main' }} />
            </Badge>
          </ListItemIcon>
          <ListItemText 
            primary="Set Price Alert"
            secondary="Get notified on price changes"
          />
        </MenuItem>

        <Divider sx={{ my: 1, bgcolor: 'rgba(255, 255, 255, 0.1)' }} />

        <MenuItem onClick={() => handleAction('view-analytics')}>
          <ListItemIcon>
            <TrendingUp sx={{ color: 'info.main' }} />
          </ListItemIcon>
          <ListItemText 
            primary="View Analytics"
            secondary="Performance insights"
          />
        </MenuItem>

        <MenuItem onClick={() => handleAction('export-pdf')}>
          <ListItemIcon>
            <GetApp sx={{ color: 'success.main' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Export PDF Report"
            secondary="Download portfolio report"
          />
        </MenuItem>

        <Divider sx={{ my: 1, bgcolor: 'rgba(255, 255, 255, 0.1)' }} />

        <MenuItem onClick={() => handleAction('settings')}>
          <ListItemIcon>
            <Settings sx={{ color: 'text.secondary' }} />
          </ListItemIcon>
          <ListItemText 
            primary="Settings"
            secondary="Configure your account"
          />
        </MenuItem>
      </Menu>
    </>
  );
};

