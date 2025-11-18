import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  IconButton,
  Chip
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  CalendarToday
} from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import { SkeletonLoader } from './common/SkeletonLoader';
import { logger } from '../utils/logger';
import { useToast, Toast } from './common/Toast';
import { EmptyState } from './common/EmptyState';
import { ConfettiAnimation } from './common/ConfettiAnimation';

interface Goal {
  id: number;
  title: string;
  type: string;
  target_value?: number;
  target_percentage?: number;
  target_date?: string;
  current_value: number;
  start_value: number;
  progress: number;
  status: string;
  milestones: any[];
}

const Goals: React.FC = () => {
  const { toast, showToast, hideToast } = useToast();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(false);
  const [open, setOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    type: 'value',
    target_value: '',
    target_percentage: '',
    target_date: ''
  });

  const fetchGoals = useCallback(async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getGoals();
      setGoals(data);
    } catch (error: any) {
      logger.error('Error fetching goals:', error);
      showToast(error?.userMessage || 'Failed to load goals', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]); // fetchGoals is memoized with useCallback

  const handleOpen = (goal?: Goal) => {
    if (goal) {
      setEditingGoal(goal);
      setFormData({
        title: goal.title,
        type: goal.type,
        target_value: goal.target_value?.toString() || '',
        target_percentage: goal.target_percentage?.toString() || '',
        target_date: goal.target_date || ''
      });
    } else {
      setEditingGoal(null);
      setFormData({
        title: '',
        type: 'value',
        target_value: '',
        target_percentage: '',
        target_date: ''
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingGoal(null);
  };

  const handleSubmit = async () => {
    try {
      const goalData: any = {
        title: formData.title,
        type: formData.type
      };

      if (formData.type === 'value' && formData.target_value) {
        goalData.target_value = parseFloat(formData.target_value);
      }
      if (formData.type === 'return' && formData.target_percentage) {
        goalData.target_percentage = parseFloat(formData.target_percentage);
      }
      if (formData.target_date) {
        goalData.target_date = formData.target_date;
      }

      if (editingGoal) {
        await portfolioService.updateGoal(editingGoal.id, goalData);
      } else {
        await portfolioService.createGoal(goalData);
      }

      handleClose();
      await fetchGoals();
      
      // Celebration for new/updated goal
      if (!editingGoal) {
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 3000);
        showToast('Goal created successfully! 🎯', 'success');
      } else {
        showToast('Goal updated successfully', 'success');
      }
    } catch (error: any) {
      logger.error('Error saving goal:', error);
      showToast(error?.userMessage || 'Failed to save goal', 'error');
    }
  };

  const handleDelete = async (goalId: number) => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      try {
        await portfolioService.deleteGoal(goalId);
        await fetchGoals();
        showToast('Goal deleted successfully', 'success');
      } catch (error: any) {
        logger.error('Error deleting goal:', error);
        showToast(error?.userMessage || 'Failed to delete goal', 'error');
      }
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 100) return 'success';
    if (progress >= 75) return 'info';
    if (progress >= 50) return 'warning';
    return 'error';
  };

  const getGoalStatus = (goal: Goal) => {
    if (goal.status === 'completed') return { label: 'Completed', color: 'success' as const };
    if (goal.status === 'cancelled') return { label: 'Cancelled', color: 'default' as const };
    return { label: 'Active', color: 'primary' as const };
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <SkeletonLoader type="card" />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Investment Goals
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpen()}
        >
          New Goal
        </Button>
      </Box>

      {goals.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              type="goals"
              actionLabel="Create Your First Goal"
              onAction={() => handleOpen()}
            />
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
          gap: 3 
        }}>
          {goals.map((goal) => {
            const status = getGoalStatus(goal);
            const progressColor = getProgressColor(goal.progress);
            
            return (
              <Box key={goal.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          {goal.title}
                        </Typography>
                        <Chip
                          label={status.label}
                          size="small"
                          color={status.color}
                          sx={{ mr: 1 }}
                        />
                        {goal.type === 'value' && (
                          <Chip
                            label="Value Target"
                            size="small"
                            variant="outlined"
                            sx={{ mr: 1 }}
                          />
                        )}
                        {goal.type === 'return' && (
                          <Chip
                            label="Return Target"
                            size="small"
                            variant="outlined"
                            sx={{ mr: 1 }}
                          />
                        )}
                      </Box>
                      <Box>
                        <IconButton
                          size="small"
                          onClick={() => handleOpen(goal)}
                          sx={{ mr: 1 }}
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(goal.id)}
                          color="error"
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      {goal.type === 'value' && (
                        <>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Target: {formatCurrency(goal.target_value || 0)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Current: {formatCurrency(goal.current_value)}
                          </Typography>
                        </>
                      )}
                      {goal.type === 'return' && (
                        <>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Target Return: {goal.target_percentage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Current Value: {formatCurrency(goal.current_value)}
                          </Typography>
                        </>
                      )}
                    </Box>

                    {goal.target_date && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CalendarToday sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          Target Date: {new Date(goal.target_date).toLocaleDateString()}
                        </Typography>
                      </Box>
                    )}

                    <Box sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          Progress
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {goal.progress.toFixed(1)}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, goal.progress)}
                        color={progressColor}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>

                    {goal.milestones && goal.milestones.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Milestones: {goal.milestones.length}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
            );
          })}
        </Box>
      )}

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingGoal ? 'Edit Goal' : 'Create New Goal'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Goal Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
          />
          
          <TextField
            fullWidth
            select
            label="Goal Type"
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            sx={{ mb: 2 }}
          >
            <MenuItem value="value">Target Portfolio Value</MenuItem>
            <MenuItem value="return">Target Return Percentage</MenuItem>
          </TextField>

          {formData.type === 'value' && (
            <TextField
              fullWidth
              label="Target Value (USD)"
              type="number"
              value={formData.target_value}
              onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}

          {formData.type === 'return' && (
            <TextField
              fullWidth
              label="Target Return (%)"
              type="number"
              value={formData.target_percentage}
              onChange={(e) => setFormData({ ...formData, target_percentage: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}

          <TextField
            fullWidth
            label="Target Date"
            type="date"
            value={formData.target_date}
            onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingGoal ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notifications */}
      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={hideToast}
      />

      {/* Celebration Animation */}
      <ConfettiAnimation 
        active={showConfetti}
        duration={3000}
        onComplete={() => setShowConfetti(false)}
      />
    </Box>
  );
};

export default Goals;

