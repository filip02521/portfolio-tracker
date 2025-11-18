import React, { useState, useCallback } from 'react';
import { Card, CardContent, Typography, Box, LinearProgress, Chip, Tooltip, Button, CircularProgress } from '@mui/material';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import { portfolioService } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { SectionHeader } from '../common/SectionHeader';

interface HealthScoreData {
  health_score: number;
  risk_level: string;
  total_value: number;
  timestamp?: string;
}

const getHealthColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'error';
};

const getHealthLabel = (score: number): string => {
  if (score >= 80) return 'Strong';
  if (score >= 60) return 'Moderate';
  if (score >= 40) return 'Weak';
  return 'Very Weak';
};

const getRiskLevelDescription = (riskLevel: string): string => {
  const descriptions: Record<string, string> = {
    'Low': 'Portfolio shows low risk with good diversification and balanced allocation.',
    'Medium': 'Portfolio has moderate risk. Consider reviewing concentration and diversification.',
    'High': 'Portfolio shows high risk. Review asset concentration and consider rebalancing.',
    'Very High': 'Portfolio has very high risk. Immediate attention recommended for diversification.',
    'Unknown': 'Risk level cannot be determined. More portfolio data may be needed.',
  };
  return descriptions[riskLevel] || 'Risk assessment based on portfolio composition and allocation.';
};

export const HealthScorePanel: React.FC = () => {
  const [data, setData] = useState<HealthScoreData | null>(null);
  const [loading, setLoading] = useState(false); // Changed to false - manual loading only
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await portfolioService.getPortfolioHealth(false);
      setData(response);
    } catch (error) {
      logger.error('Failed to fetch portfolio health score:', error);
      setError('Health score is temporarily unavailable. Core portfolio data is still up to date.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Removed automatic useEffect - now manual only via button

  if (loading) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <SectionHeader
            title="Portfolio Health"
            description="Overall portfolio health score based on diversification, concentration, and allocation balance."
            icon={<HealthAndSafetyIcon />}
            tooltip="Health score (0-100) evaluates portfolio quality based on asset concentration, diversification across sectors/regions, and exchange distribution. Higher scores indicate better portfolio structure."
          />
          <LinearProgress sx={{ mt: 2 }} />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <SectionHeader
            title="Portfolio Health"
            description="Overall portfolio health score based on diversification, concentration, and allocation balance."
            icon={<HealthAndSafetyIcon />}
            tooltip="Health score (0-100) evaluates portfolio quality based on asset concentration, diversification across sectors/regions, and exchange distribution. Higher scores indicate better portfolio structure."
          />
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {error
                ? error
                : 'Click the button below to calculate your portfolio health score.'}
            </Typography>
            <Button
              variant="contained"
              onClick={fetchHealth}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <HealthAndSafetyIcon />}
              sx={{ alignSelf: 'flex-start' }}
            >
              {loading ? 'Calculating...' : 'Calculate Health Score'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const score = Math.max(0, Math.min(100, data.health_score ?? 0));
  const color = getHealthColor(score);
  const label = getHealthLabel(score);
  const riskLevel = data.risk_level || 'Unknown';

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ p: 3.5 }}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <SectionHeader
            title="Portfolio Health"
            description="Overall portfolio health score based on diversification, concentration, and allocation balance."
            icon={<HealthAndSafetyIcon color={color} />}
            tooltip="Health score (0-100) evaluates portfolio quality based on asset concentration, diversification across sectors/regions, and exchange distribution. Higher scores indicate better portfolio structure."
          />
          <Button
            variant="outlined"
            size="small"
            onClick={fetchHealth}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={14} /> : <HealthAndSafetyIcon />}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2.5 }}>
          <Box>
            <Typography variant="h2" sx={{ fontWeight: 700, lineHeight: 1, fontSize: { xs: '2.5rem', md: '3rem' } }}>
              {score}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5, fontWeight: 500 }}>
              / 100 • {label}
            </Typography>
          </Box>
          <Tooltip
            title={`Health score calculation considers: asset concentration (lower is better), diversification across sectors and regions (higher is better), and exchange distribution balance. Current score: ${score}/100 (${label}).`}
            arrow
            placement="left"
          >
            <Box sx={{ width: 200, ml: 2 }}>
              <LinearProgress
                variant="determinate"
                value={score}
                color={color}
                sx={{ height: 12, borderRadius: 6 }}
              />
            </Box>
          </Tooltip>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
            Risk Level:
          </Typography>
          <Tooltip title={getRiskLevelDescription(riskLevel)} arrow>
            <Chip
              label={riskLevel}
              size="medium"
              color={color}
              variant="outlined"
              sx={{ fontWeight: 600, fontSize: '0.875rem' }}
            />
          </Tooltip>
        </Box>

        {data.total_value > 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
            Based on total portfolio value of{' '}
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(data.total_value || 0)}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};


