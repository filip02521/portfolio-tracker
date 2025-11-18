import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  Button,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  Calculate,
  TrendingDown,
  Schedule,
  Lightbulb
} from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import { logger } from '../utils/logger';

const TaxOptimizer: React.FC = () => {
  const [taxCalculation, setTaxCalculation] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [deadline, setDeadline] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [year] = useState(new Date().getFullYear());
  const [additionalLosses, setAdditionalLosses] = useState('');

  const fetchTaxData = useCallback(async () => {
    try {
      setLoading(true);
      
      const [calc, sugg, dl] = await Promise.all([
        portfolioService.getTaxCalculation(year),
        portfolioService.getTaxSuggestions(),
        portfolioService.getTaxDeadline()
      ]);
      
      setTaxCalculation(calc);
      setSuggestions(sugg.suggestions || []);
      setDeadline(dl);
    } catch (error) {
      logger.error('Error fetching tax data:', error);
    } finally {
      setLoading(false);
    }
  }, [year]);

  // Initial fetch on mount
  useEffect(() => {
    fetchTaxData();
  }, [fetchTaxData]);

  const handleScenarioCalculate = async () => {
    try {
      const losses = parseFloat(additionalLosses);
      if (isNaN(losses) || losses <= 0) {
        alert('Please enter a valid loss amount');
        return;
      }
      
      const scenario = await portfolioService.calculateTaxScenario(losses);
      // Display scenario results (could show in a dialog or alert)
      alert(`Tax Savings: ${scenario.tax_savings_pln.toFixed(2)} PLN (${scenario.tax_savings_usd.toFixed(2)} USD)`);
    } catch (error) {
      logger.error('Error calculating scenario:', error);
    }
  };

  const formatCurrency = (value: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading tax data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 4 }}>
        Tax Optimization
      </Typography>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
        gap: 3 
      }}>
        {/* Tax Calculation */}
        <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Calculate sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Tax Calculation {year}
                </Typography>
              </Box>

              {taxCalculation ? (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Realized Gains (USD)
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {formatCurrency(taxCalculation.realized_gains_usd)}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Realized Losses (USD)
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {formatCurrency(taxCalculation.realized_losses_usd)}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Taxable Amount (PLN)
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {formatCurrency(taxCalculation.taxable_amount_pln, 'PLN')}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Estimated Tax to Pay
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700, color: 'error.main' }}>
                      {formatCurrency(taxCalculation.tax_amount_pln, 'PLN')}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ({formatCurrency(taxCalculation.tax_amount_usd)})
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Effective Tax Rate
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {taxCalculation.effective_tax_rate.toFixed(2)}%
                    </Typography>
                  </Box>
                </>
              ) : (
                <Typography color="text.secondary">
                  No tax data available
                </Typography>
              )}
            </CardContent>
          </Card>

        {/* Tax Deadline */}
        <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Schedule sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Tax Deadlines
                </Typography>
              </Box>

              {deadline && (
                <>
                  <Alert 
                    severity={deadline.urgent ? 'error' : deadline.warning ? 'warning' : 'info'}
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="body2">
                      <strong>PIT Deadline:</strong> {new Date(deadline.pit_deadline).toLocaleDateString()}
                    </Typography>
                    <Typography variant="body2">
                      {deadline.days_until_pit_deadline} days remaining
                    </Typography>
                  </Alert>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Year End
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {deadline.days_until_year_end} days until year end
                    </Typography>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>

        {/* Tax-Loss Harvesting Suggestions */}
        <Card sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <TrendingDown sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Tax-Loss Harvesting Suggestions
                </Typography>
              </Box>

              {suggestions.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Asset</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell align="right">Potential Loss (USD)</TableCell>
                        <TableCell align="right">Tax Savings (PLN)</TableCell>
                        <TableCell align="right">Priority</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {suggestions.map((suggestion, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {suggestion.asset}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {suggestion.amount.toFixed(4)}
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(suggestion.potential_loss_usd)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography sx={{ fontWeight: 600, color: 'success.main' }}>
                              {formatCurrency(suggestion.tax_savings_pln, 'PLN')}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={suggestion.priority}
                              size="small"
                              color={suggestion.priority === 'high' ? 'error' : 'warning'}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  No tax-loss harvesting opportunities found at this time.
                </Alert>
              )}
            </CardContent>
          </Card>

        {/* Scenario Calculator */}
        <Card sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Lightbulb sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Scenario Calculator
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
                <TextField
                  label="Additional Losses (USD)"
                  type="number"
                  value={additionalLosses}
                  onChange={(e) => setAdditionalLosses(e.target.value)}
                  sx={{ flexGrow: 1 }}
                  helperText="Enter additional losses to see tax savings"
                />
                <Button
                  variant="contained"
                  onClick={handleScenarioCalculate}
                  disabled={!additionalLosses || parseFloat(additionalLosses) <= 0}
                >
                  Calculate
                </Button>
              </Box>
            </CardContent>
          </Card>
      </Box>
    </Box>
  );
};

export default TaxOptimizer;

