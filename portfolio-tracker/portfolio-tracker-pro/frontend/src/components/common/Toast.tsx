import React, { useEffect } from 'react';
import { Snackbar, Alert, AlertColor } from '@mui/material';

interface ToastProps {
  open: boolean;
  message: string;
  severity?: AlertColor;
  onClose: () => void;
  duration?: number;
}

export const Toast: React.FC<ToastProps> = ({ 
  open, 
  message, 
  severity = 'info', 
  onClose, 
  duration = 3000 
}) => {
  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [open, duration, onClose]);

  return (
    <Snackbar
      open={open}
      autoHideDuration={duration}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert 
        onClose={onClose} 
        severity={severity} 
        variant="filled"
        sx={{ width: '100%' }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
};

// Hook for easy toast management
export const useToast = () => {
  const [toast, setToast] = React.useState<{
    open: boolean;
    message: string;
    severity?: AlertColor;
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  const showToast = (message: string, severity: AlertColor = 'info') => {
    setToast({ open: true, message, severity });
  };

  const hideToast = () => {
    setToast({ ...toast, open: false });
  };

  return { toast, showToast, hideToast };
};


