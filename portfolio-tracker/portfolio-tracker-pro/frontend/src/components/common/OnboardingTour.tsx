import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Stack,
  IconButton,
  Paper,
  useTheme,
  alpha,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { OnboardingStep } from '../../config/onboardingSteps';

export interface OnboardingTourProps {
  steps: OnboardingStep[];
  open: boolean;
  onClose: () => void;
  onComplete?: () => void;
  storageKey?: string;
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({
  steps,
  open,
  onClose,
  onComplete,
  storageKey = 'onboarding_completed',
}) => {
  const theme = useTheme();
  const [currentStep, setCurrentStep] = useState(0);
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [overlayStyle, setOverlayStyle] = useState<React.CSSProperties>({});
  const overlayRef = useRef<HTMLDivElement>(null);

  const currentStepData = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  // Find and highlight target element
  useEffect(() => {
    if (!open || !currentStepData) {
      return;
    }

    const findElement = (): HTMLElement | null => {
      const target = currentStepData.target;
      
      // If target looks like a CSS selector (starts with [, ., #, or contains special CSS chars), use it directly
      if (target.startsWith('[') || target.startsWith('.') || target.startsWith('#') || 
          target.includes('>') || target.includes(' ') || target.includes(':')) {
        try {
          const bySelector = document.querySelector(target);
          if (bySelector) {
            return bySelector as HTMLElement;
          }
        } catch (error) {
          // Invalid selector, ignore and try other methods
          console.debug('Invalid CSS selector in onboarding step:', target, error);
        }
      }

      // Try data attribute first (for simple string identifiers)
      try {
        const byDataAttr = document.querySelector(`[data-tour="${target}"]`);
        if (byDataAttr) {
          return byDataAttr as HTMLElement;
        }
      } catch (error) {
        // Invalid selector, ignore
      }

      // Try aria-label for simple string matches
      try {
        const byAriaLabel = document.querySelector(`[aria-label="${target}"]`);
        if (byAriaLabel) {
          return byAriaLabel as HTMLElement;
        }
      } catch (error) {
        // Invalid selector, ignore
      }

      return null;
    };

    // Wait a bit for DOM to be ready
    const timeout = setTimeout(() => {
      const element = findElement();
      setTargetElement(element);

      if (element && currentStepData.placement !== 'center') {
        const rect = element.getBoundingClientRect();
        const scrollX = window.scrollX || window.pageXOffset;
        const scrollY = window.scrollY || window.pageYOffset;

        setOverlayStyle({
          position: 'absolute',
          top: `${rect.top + scrollY}px`,
          left: `${rect.left + scrollX}px`,
          width: `${rect.width}px`,
          height: `${rect.height}px`,
          zIndex: 1300,
          pointerEvents: 'none',
        });
      } else {
        setOverlayStyle({});
      }
    }, 100);

    return () => clearTimeout(timeout);
  }, [open, currentStep, currentStepData]);

  const handleNext = () => {
    if (isLastStep) {
      handleComplete();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = () => {
    try {
      localStorage.setItem(storageKey, 'true');
    } catch (error) {
      // localStorage might not be available
      console.debug('Failed to save onboarding completion', error);
    }

    if (onComplete) {
      onComplete();
    }
    onClose();
  };

  // Handle action button click
  const handleAction = () => {
    if (currentStepData?.action) {
      currentStepData.action.onClick();
    }
  };

  // Listen for show shortcuts event
  useEffect(() => {
    const handleShowShortcuts = () => {
      onClose();
      // Dispatch event to show shortcuts dialog
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('command-palette:show-shortcuts'));
      }, 300);
    };

    window.addEventListener('onboarding:show-shortcuts', handleShowShortcuts);
    return () => {
      window.removeEventListener('onboarding:show-shortcuts', handleShowShortcuts);
    };
  }, [onClose]);

  if (!currentStepData) {
    return null;
  }

  const placement = currentStepData.placement || 'bottom';
  const isCenter = placement === 'center';

  return (
    <>
      {/* Overlay for highlighting target element */}
      {!isCenter && targetElement && (
        <Box
          ref={overlayRef}
          sx={{
            ...overlayStyle,
            border: `3px solid ${theme.palette.primary.main}`,
            borderRadius: 2,
            boxShadow: `0 0 0 9999px ${alpha(theme.palette.common.black, 0.5)}`,
            transition: 'all 0.3s ease-in-out',
          }}
        />
      )}

      {/* Tour Dialog */}
      <Dialog
        open={open}
        onClose={handleSkip}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            position: isCenter ? 'relative' : 'absolute',
            ...(placement === 'top' && { bottom: 'auto', top: targetElement ? `${targetElement.getBoundingClientRect().top - 20}px` : '50%' }),
            ...(placement === 'bottom' && { top: 'auto', bottom: targetElement ? `${window.innerHeight - targetElement.getBoundingClientRect().bottom - 20}px` : '50%' }),
            ...(placement === 'left' && { right: 'auto', left: targetElement ? `${targetElement.getBoundingClientRect().left - 20}px` : '50%' }),
            ...(placement === 'right' && { left: 'auto', right: targetElement ? `${window.innerWidth - targetElement.getBoundingClientRect().right - 20}px` : '50%' }),
            ...(isCenter && { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }),
            borderRadius: 3,
            boxShadow: theme.palette.mode === 'dark'
              ? '0 8px 32px rgba(0, 0, 0, 0.4)'
              : '0 8px 32px rgba(0, 0, 0, 0.12)',
            zIndex: 1400,
          },
        }}
      >
        <DialogTitle>
          <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
            <Typography variant="h6" sx={{ fontWeight: 700, flex: 1 }}>
              {currentStepData.title}
            </Typography>
            <IconButton
              onClick={handleSkip}
              size="small"
              sx={{ minWidth: 'auto', p: 1 }}
            >
              <CloseIcon />
            </IconButton>
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Step {currentStep + 1} of {steps.length}
          </Typography>
        </DialogTitle>

        <DialogContent>
          <Typography variant="body1" sx={{ lineHeight: 1.7, mb: currentStepData.action ? 2 : 0 }}>
            {currentStepData.content}
          </Typography>

          {currentStepData.action && (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                mt: 2,
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
                borderColor: theme.palette.primary.main,
              }}
            >
              <Stack direction="row" spacing={2} alignItems="center">
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {currentStepData.action.label}
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={handleAction}
                  sx={{ textTransform: 'none' }}
                >
                  Try it
                </Button>
              </Stack>
            </Paper>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleSkip} sx={{ textTransform: 'none' }}>
            Skip Tour
          </Button>
          <Stack direction="row" spacing={1}>
            <Button
              onClick={handlePrevious}
              disabled={isFirstStep}
              startIcon={<ArrowBackIcon />}
              sx={{ textTransform: 'none' }}
            >
              Previous
            </Button>
            <Button
              onClick={handleNext}
              variant="contained"
              endIcon={isLastStep ? undefined : <ArrowForwardIcon />}
              sx={{ textTransform: 'none' }}
            >
              {isLastStep ? 'Complete' : 'Next'}
            </Button>
          </Stack>
        </DialogActions>
      </Dialog>
    </>
  );
};

/**
 * Hook to check if onboarding has been completed
 */
export const useOnboardingStatus = (storageKey: string = 'onboarding_completed'): boolean => {
  const [completed, setCompleted] = useState<boolean>(() => {
    try {
      return localStorage.getItem(storageKey) === 'true';
    } catch (error) {
      return false;
    }
  });

  return completed;
};

/**
 * Hook to reset onboarding status (for testing or admin purposes)
 */
export const resetOnboarding = (storageKey: string = 'onboarding_completed'): void => {
  try {
    localStorage.removeItem(storageKey);
  } catch (error) {
    console.debug('Failed to reset onboarding status', error);
  }
};

