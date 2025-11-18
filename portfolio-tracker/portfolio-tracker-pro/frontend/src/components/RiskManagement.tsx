import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Alert,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Calculate,
} from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import { logger } from '../utils/logger';
import { useToast, Toast } from './common/Toast';
import { SkeletonLoader } from './common/SkeletonLoader';
import { HelpTooltip } from './common/HelpTooltip';

const RiskManagement: React.FC = () => {
  const { toast, showToast, hideToast } = useToast();
  const [riskAnalysis, setRiskAnalysis] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any[]>([]);
  const [loading, setLoading] = useState(false); // Changed to false - manual loading only
  const [calculating, setCalculating] = useState(false);
  
  // Position size calculator
  const [calcData, setCalcData] = useState({
    portfolioValue: '',
    riskPerTrade: '2.0',
    entryPrice: '',
    stopLossPrice: '',
  });
  const [positionSize, setPositionSize] = useState<any>(null);

  const fetchRiskData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getRiskAnalysis();
      setRiskAnalysis(data.risk_analysis);
      setHeatmap(data.heatmap?.heatmap || []);
    } catch (error: any) {
      logger.error('Error fetching risk data:', error);
      showToast('Failed to load risk analysis', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Removed automatic useEffect - now manual only via button

  const handleCalculatePositionSize = async () => {
    try {
      if (!calcData.portfolioValue || !calcData.entryPrice || !calcData.stopLossPrice) {
        showToast('Please fill in all required fields', 'warning');
        return;
      }

      setCalculating(true);
      const result = await portfolioService.calculatePositionSize(
        parseFloat(calcData.portfolioValue),
        parseFloat(calcData.riskPerTrade),
        parseFloat(calcData.entryPrice),
        parseFloat(calcData.stopLossPrice)
      );
      setPositionSize(result);
    } catch (error: any) {
      logger.error('Error calculating position size:', error);
      showToast('Failed to calculate position size', 'error');
    } finally {
      setCalculating(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 33) return 'success.main';
    if (score < 66) return 'warning.main';
    return 'error.main';
  };

  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'low':
        return 'Low Risk';
      case 'moderate':
        return 'Moderate Risk';
      case 'high':
        return 'High Risk';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return <SkeletonLoader type="dashboard" />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Risk Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyze and manage your portfolio risk
          </Typography>
        </Box>
        {!riskAnalysis && (
          <Button
            variant="contained"
            startIcon={<Calculate />}
            onClick={fetchRiskData}
            disabled={loading}
          >
            Analyze Risk
          </Button>
        )}
        {riskAnalysis && (
          <Button
            variant="outlined"
            startIcon={<Calculate />}
            onClick={fetchRiskData}
            disabled={loading}
          >
            Refresh Analysis
          </Button>
        )}
      </Box>

      {/* Portfolio Risk Score */}
      {riskAnalysis && (
        <Card sx={{ mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Portfolio Risk Analysis
              </Typography>
              <HelpTooltip title="Overall risk score calculated based on concentration, diversification, and volatility" />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 3 }}>
              <Typography 
                variant="h2" 
                sx={{ 
                  fontWeight: 800,
                  color: getRiskColor(riskAnalysis.risk_score)
                }}
              >
                {riskAnalysis.risk_score}
              </Typography>
              <Typography variant="h5" color="text.secondary">
                / 100
              </Typography>
              <Chip 
                label={getRiskLevelText(riskAnalysis.risk_level)}
                color={riskAnalysis.risk_level === 'low' ? 'success' : 
                       riskAnalysis.risk_level === 'moderate' ? 'warning' : 'error'}
                sx={{ ml: 2 }}
              />
            </Box>

            {/* Risk Factors */}
            {riskAnalysis.factors && riskAnalysis.factors.length > 0 && (
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  Risk Factors:
                </Typography>
                {riskAnalysis.factors.map((factor: any, index: number) => (
                  <Alert 
                    key={index}
                    severity={factor.severity === 'high' ? 'error' : 'warning'}
                    variant="outlined"
                    sx={{ mb: 1 }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {factor.message}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {factor.suggestion}
                    </Typography>
                  </Alert>
                ))}
              </Box>
            )}

            {/* Risk Metrics */}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mt: 3 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Max Allocation</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {riskAnalysis.max_allocation?.toFixed(1)}%
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Number of Assets</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {riskAnalysis.num_assets}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Diversification Score</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {riskAnalysis.diversification_score}/100
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Portfolio Heat Map */}
      {heatmap.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Risk Heat Map
              </Typography>
              <HelpTooltip title="Visual representation of risk per asset - red indicates higher risk, green indicates lower risk" />
            </Box>

            <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Asset</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Allocation</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Risk Score</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>P&L %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {heatmap.map((item, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {item.symbol}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {item.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {item.allocation?.toFixed(2)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={item.risk_score?.toFixed(0)}
                          size="small"
                          sx={{
                            bgcolor: item.color === 'green' ? 'success.main' :
                                     item.color === 'yellow' ? 'warning.main' : 'error.main',
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: item.pnl_percent >= 0 ? 'success.main' : 'error.main',
                            fontWeight: 600
                          }}
                        >
                          {item.pnl_percent >= 0 ? '+' : ''}{item.pnl_percent?.toFixed(2)}%
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Position Size Calculator */}
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Position Size Calculator
            </Typography>
            <HelpTooltip title="Calculate optimal position size based on your risk tolerance and stop-loss level" />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3, mb: 3 }}>
            <TextField
              label="Portfolio Value (USD)"
              type="number"
              value={calcData.portfolioValue}
              onChange={(e) => setCalcData({ ...calcData, portfolioValue: e.target.value })}
              fullWidth
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
              }}
            />
            <TextField
              label="Risk Per Trade (%)"
              type="number"
              value={calcData.riskPerTrade}
              onChange={(e) => setCalcData({ ...calcData, riskPerTrade: e.target.value })}
              fullWidth
              InputProps={{
                endAdornment: <Typography sx={{ ml: 1 }}>%</Typography>,
              }}
            />
            <TextField
              label="Entry Price"
              type="number"
              value={calcData.entryPrice}
              onChange={(e) => setCalcData({ ...calcData, entryPrice: e.target.value })}
              fullWidth
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
              }}
            />
            <TextField
              label="Stop-Loss Price"
              type="number"
              value={calcData.stopLossPrice}
              onChange={(e) => setCalcData({ ...calcData, stopLossPrice: e.target.value })}
              fullWidth
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
              }}
            />
          </Box>

          <Button
            variant="contained"
            startIcon={<Calculate />}
            onClick={handleCalculatePositionSize}
            disabled={calculating}
            fullWidth
            sx={{ mb: 3 }}
          >
            {calculating ? 'Calculating...' : 'Calculate Position Size'}
          </Button>

          {positionSize && (
            <Box sx={{ 
              p: 3, 
              bgcolor: 'rgba(37, 99, 235, 0.1)', 
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'primary.main'
            }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Recommended Position
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Position Size</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {positionSize.position_size?.toFixed(4)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Position Value</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    ${positionSize.position_value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Risk Amount</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    ${positionSize.risk_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Price Risk</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    ${positionSize.price_risk?.toFixed(2)}
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      <Toast
        open={toast.open}
        message={toast.message}
        severity={toast.severity}
        onClose={hideToast}
      />
    </Box>
  );
};

export default RiskManagement;


