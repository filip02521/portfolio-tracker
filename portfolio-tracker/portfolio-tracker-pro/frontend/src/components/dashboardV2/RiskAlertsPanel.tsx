import React, { useEffect, useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Collapse,
  IconButton,
  Tooltip,
  Button,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { portfolioService } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { SectionHeader } from '../common/SectionHeader';

interface RiskAlert {
  type: 'critical' | 'warning' | 'info';
  symbol?: string;
  symbols?: string[];
  message: string;
  severity: 'high' | 'medium' | 'low';
  percentage?: number;
  value_usd?: number;
  correlation?: number;
  volatility?: number;
  drawdown_percent?: number;
  max_drawdown_percent?: number;
  recommendation?: string;
}

interface RiskAlertsData {
  concentration: RiskAlert[];
  correlation: RiskAlert[];
  volatility: RiskAlert[];
  drawdown: RiskAlert[];
  timestamp: string;
}

export const RiskAlertsPanel: React.FC = () => {
  const [riskAlerts, setRiskAlerts] = useState<RiskAlertsData | null>(null);
  const [loading, setLoading] = useState(false); // Changed to false - manual loading only
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<{ [key: string]: boolean }>({
    concentration: true,
    correlation: true,
    volatility: true,
    drawdown: true,
  });

  const fetchRiskAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await portfolioService.getRiskAlerts(90, false);
      setRiskAlerts(data);
    } catch (error) {
      logger.error('Failed to fetch risk alerts:', error);
      setError('Risk alerts are temporarily unavailable. Showing base dashboard data only.');
      setRiskAlerts(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Removed automatic useEffect - now manual only via button

  const toggleSection = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined) return 'N/A';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const renderAlertItem = (alert: RiskAlert, index: number) => {
    return (
      <ListItem
        key={index}
        sx={{
          flexDirection: 'column',
          alignItems: 'flex-start',
          py: 1.5,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mb: 1 }}>
          <Tooltip title={`${alert.severity.toUpperCase()} severity: ${alert.severity === 'high' ? 'Requires immediate attention' : alert.severity === 'medium' ? 'Should be reviewed soon' : 'Informational - monitor for changes'}`} arrow>
            <Box sx={{ mr: 1, color: getSeverityColor(alert.severity) + '.main', cursor: 'help' }}>
              {getAlertIcon(alert.type)}
            </Box>
          </Tooltip>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {alert.symbol || (alert.symbols ? alert.symbols.join(' & ') : 'Portfolio')}
                </Typography>
                <Chip
                  label={alert.severity.toUpperCase()}
                  size="small"
                  color={getSeverityColor(alert.severity) as any}
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              </Box>
            }
            secondary={
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {alert.message}
              </Typography>
            }
          />
        </Box>
        {(alert.percentage !== undefined || alert.value_usd !== undefined || 
          alert.correlation !== undefined || alert.volatility !== undefined ||
          alert.drawdown_percent !== undefined) && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1, ml: 4 }}>
            {alert.percentage !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Allocation: {formatPercentage(alert.percentage)}
              </Typography>
            )}
            {alert.value_usd !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Value: {formatCurrency(alert.value_usd)}
              </Typography>
            )}
            {alert.correlation !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Correlation: {alert.correlation.toFixed(3)}
              </Typography>
            )}
            {alert.volatility !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Volatility: {formatPercentage(alert.volatility)}
              </Typography>
            )}
            {alert.drawdown_percent !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Drawdown: {formatPercentage(alert.drawdown_percent)}
                {alert.max_drawdown_percent !== undefined && 
                  ` (Max: ${formatPercentage(alert.max_drawdown_percent)})`}
              </Typography>
            )}
          </Box>
        )}
        {alert.recommendation && (
          <Box sx={{ mt: 1, ml: 4, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">
              💡 {alert.recommendation}
            </Typography>
          </Box>
        )}
      </ListItem>
    );
  };

  if (loading) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <Box sx={{ mb: 3 }}>
            <SectionHeader
              title="Risk Management"
              description="Real-time risk alerts for concentration, correlation, volatility, and drawdown. Expand each section to view detailed alerts and recommendations."
              tooltip="Risk alerts help identify potential portfolio vulnerabilities. Critical alerts (red) require immediate attention, warnings (yellow) suggest review, and info alerts (blue) provide context."
            />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress size={40} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!riskAlerts) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <Box sx={{ mb: 3 }}>
            <SectionHeader
              title="Risk Management"
              description="Real-time risk alerts for concentration, correlation, volatility, and drawdown. Expand each section to view detailed alerts and recommendations."
              tooltip="Risk alerts help identify potential portfolio vulnerabilities. Critical alerts (red) require immediate attention, warnings (yellow) suggest review, and info alerts (blue) provide context."
            />
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {error
                ? error
                : 'Click the button below to analyze portfolio risks.'}
            </Typography>
            <Button
              variant="contained"
              onClick={fetchRiskAlerts}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <WarningIcon />}
              sx={{ alignSelf: 'flex-start' }}
            >
              {loading ? 'Analyzing...' : 'Analyze Risks'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const totalAlerts = 
    riskAlerts.concentration.length +
    riskAlerts.correlation.length +
    riskAlerts.volatility.length +
    riskAlerts.drawdown.length;

  if (totalAlerts === 0) {
    return (
      <Card variant="outlined" sx={{ borderRadius: 2 }}>
        <CardContent sx={{ p: 3.5 }}>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <SectionHeader
              title="Risk Management"
              description="Real-time risk alerts for concentration, correlation, volatility, and drawdown. Expand each section to view detailed alerts and recommendations."
              tooltip="Risk alerts help identify potential portfolio vulnerabilities. Critical alerts (red) require immediate attention, warnings (yellow) suggest review, and info alerts (blue) provide context."
            />
            <Button
              variant="outlined"
              size="small"
              onClick={fetchRiskAlerts}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={14} /> : <WarningIcon />}
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
          </Box>
          <Alert severity="success" icon={<InfoIcon />} sx={{ borderRadius: 2 }}>
            <AlertTitle>No Risk Alerts</AlertTitle>
            Your portfolio shows no significant risk indicators at this time.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const sections = [
    {
      key: 'concentration',
      title: 'Concentration Risk',
      alerts: riskAlerts.concentration,
      icon: <WarningIcon />,
    },
    {
      key: 'correlation',
      title: 'Correlation Risk',
      alerts: riskAlerts.correlation,
      icon: <InfoIcon />,
    },
    {
      key: 'volatility',
      title: 'Volatility Risk',
      alerts: riskAlerts.volatility,
      icon: <WarningIcon />,
    },
    {
      key: 'drawdown',
      title: 'Drawdown Risk',
      alerts: riskAlerts.drawdown,
      icon: <ErrorIcon />,
    },
  ].filter(section => section.alerts.length > 0);

  const categoryDescriptions: Record<string, string> = {
    'concentration': 'Concentration risk occurs when too much of your portfolio is invested in a single asset or asset class. High concentration increases vulnerability to individual asset volatility.',
    'correlation': 'Correlation risk happens when multiple assets move together. High correlation means diversification benefits are reduced, as assets don\'t provide independent risk reduction.',
    'volatility': 'Volatility risk indicates assets with high price swings. While volatility can mean opportunity, excessive volatility increases portfolio risk and potential for large losses.',
    'drawdown': 'Drawdown risk shows periods when portfolio value has declined significantly from previous peaks. Large drawdowns indicate potential overexposure to declining markets.',
  };

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ p: 3.5 }}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <SectionHeader
            title="Risk Management"
            description="Real-time risk alerts for concentration, correlation, volatility, and drawdown. Expand each section to view detailed alerts and recommendations."
            tooltip="Risk alerts help identify potential portfolio vulnerabilities. Critical alerts (red) require immediate attention, warnings (yellow) suggest review, and info alerts (blue) provide context. Click expand/collapse to view details."
          />
          <Button
            variant="outlined"
            size="small"
            onClick={fetchRiskAlerts}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={14} /> : <WarningIcon />}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', mb: 2.5 }}>
          <Chip
            label={`${totalAlerts} Alert${totalAlerts !== 1 ? 's' : ''}`}
            color={totalAlerts > 5 ? 'error' : totalAlerts > 2 ? 'warning' : 'default'}
            size="medium"
            sx={{ fontWeight: 600 }}
          />
        </Box>

        {sections.map(section => (
          <Box key={section.key} sx={{ mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                p: 1,
                borderRadius: 1,
                '&:hover': { bgcolor: 'action.hover' },
              }}
              onClick={() => toggleSection(section.key)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Tooltip title={categoryDescriptions[section.key] || `View ${section.title.toLowerCase()} alerts`} arrow>
                  <Box sx={{ color: 'text.secondary', cursor: 'help' }}>{section.icon}</Box>
                </Tooltip>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {section.title}
                </Typography>
                <Chip
                  label={section.alerts.length}
                  size="small"
                  sx={{ height: 20, fontSize: '0.7rem', fontWeight: 600 }}
                />
              </Box>
              <Tooltip title={expanded[section.key] ? 'Collapse section to hide alerts' : 'Expand section to view all alerts'} arrow>
                <IconButton size="small">
                  {expanded[section.key] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Tooltip>
            </Box>
            <Collapse in={expanded[section.key]}>
              <List sx={{ mt: 1 }}>
                {section.alerts.map((alert, index) => renderAlertItem(alert, index))}
              </List>
            </Collapse>
          </Box>
        ))}
      </CardContent>
    </Card>
  );
};

