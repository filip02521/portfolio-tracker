import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  LinearProgress,
  CircularProgress,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  ExpandMore,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';

interface KeyIndicator {
  name: string;
  value: number;
  signal: string;
  weight: string;
}

interface RecommendationSummary {
  key_indicators?: KeyIndicator[];
  strengths?: string[];
  concerns?: string[];
  timeframe?: string;
}

interface AIRecommendation {
  asset?: string;
  symbol?: string;
  action: string;
  priority: string;
  reason: string;
  signal_strength?: number;
  confidence?: number;
  buy_score?: number;
  sell_score?: number;
  composite_score?: number;
  summary?: RecommendationSummary;
  allocation?: {
    current: number;
    target: number;
    difference: number;
  };
  metrics?: any;
}

interface SimplifiedRecommendationCardProps {
  recommendation: AIRecommendation;
  index: number;
  onExpand: () => void;
}

const SimplifiedRecommendationCard: React.FC<SimplifiedRecommendationCardProps> = ({
  recommendation,
  index,
  onExpand,
}) => {
  const theme = useTheme();
  const compositeScore = recommendation.composite_score || 50;
  const signalStrength = recommendation.signal_strength || 0;
  const confidence = recommendation.confidence || 0;
  
  // Gauge color based on score
  const getGaugeColor = (score: number) => {
    if (score >= 70) return theme.palette.success.main;
    if (score >= 40) return theme.palette.warning.main;
    return theme.palette.error.main;
  };
  
  // Normalize indicator value to 0-100 for progress bar
  const normalizeIndicatorValue = (ind: KeyIndicator): number => {
    switch (ind.name) {
      case 'RSI':
        return ind.value; // RSI is already 0-100
      case 'MACD':
        return Math.min(100, Math.max(0, (ind.value + 10) * 5)); // Normalize MACD
      case 'MA Cross':
        return Math.min(100, Math.max(0, ind.value + 50)); // Normalize percentage
      case 'Bollinger':
        return ind.value; // Already 0-100
      default:
        return Math.abs(ind.value) % 100;
    }
  };
  
  const getSignalColor = (signal: string) => {
    if (signal === 'bullish' || signal === 'buy') return theme.palette.success.main;
    if (signal === 'bearish' || signal === 'sell') return theme.palette.error.main;
    return theme.palette.grey[500];
  };
  
  // Indicator explanations for tooltips
  const indicatorExplanations: Record<string, string> = {
    'RSI': 'Relative Strength Index (0-100). <30 = oversold (buy signal), >70 = overbought (sell signal). Measures momentum.',
    'MACD': 'Moving Average Convergence Divergence. Crossover indicates strong trend change. Bullish crossover = buy, bearish = sell.',
    'Bollinger': 'Bollinger Bands position (0-100%). <20% = oversold (buy), >80% = overbought (sell). Shows volatility and price extremes.',
    'MA Cross': 'Golden Cross (MA50 > MA200) = bullish, Death Cross (MA50 < MA200) = bearish. Long-term trend indicator.',
    'Stochastic': 'Stochastic Oscillator (0-100). <20 = oversold, >80 = overbought. Measures momentum relative to price range.',
    'Williams %R': 'Williams %R (-100 to 0). < -80 = oversold (buy), > -20 = overbought (sell). Similar to Stochastic.',
    'MFI': 'Money Flow Index (0-100). <20 = oversold, >80 = overbought. RSI-like but includes volume data.',
    'CCI': 'Commodity Channel Index. >150 = strong bullish, < -150 = strong bearish. Measures deviation from average price.',
    'ADX': 'Average Directional Index. >25 = strong trend. Combined with DI+/- direction shows trend strength and direction.',
    'VWAP': 'Volume Weighted Average Price. Price above VWAP = bullish, below = bearish. Important institutional price level.',
    'CMF': 'Chaikin Money Flow. >0.1 = accumulation (buy), < -0.1 = distribution (sell). Measures money flow volume.',
    'OBV': 'On-Balance Volume. Increasing trend = bullish, decreasing = bearish. Measures volume flow.',
    'Support/Resistance': 'Price near support = potential buy, near resistance = potential sell. Historical price levels.',
    'Volume Profile': 'Price below VAL (Value Area Low) = buy, above VAH (Value Area High) = sell. Shows high-volume price zones.',
  };
  
  const actionColor = recommendation.action === 'buy' ? 'success' : 'error';
  const priorityColor = 
    recommendation.priority === 'high' ? 'error' :
    recommendation.priority === 'medium' ? 'warning' : 'default';
  
  return (
    <Card
      sx={{
        mb: 2,
        borderLeft: 4,
        borderLeftColor: recommendation.action === 'buy' 
          ? (recommendation.priority === 'high' ? theme.palette.success.main : theme.palette.success.light)
          : (recommendation.priority === 'high' ? theme.palette.error.main : theme.palette.error.light),
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: 4,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <CardContent>
        {/* Header: Symbol + Action + Priority */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {recommendation.action === 'buy' ? (
              <TrendingUp color="success" />
            ) : (
              <TrendingDown color="error" />
            )}
            <Typography variant="h6" fontWeight={600}>
              {recommendation.asset || recommendation.symbol}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={recommendation.action.toUpperCase()}
              color={actionColor}
              size="small"
              sx={{ fontWeight: 600 }}
            />
            <Chip
              label={recommendation.priority.toUpperCase()}
              color={priorityColor}
              size="small"
              variant="outlined"
            />
          </Box>
        </Box>
        
        {/* Composite Score Gauge and Quick Stats */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 2 }}>
          {/* Circular Progress Gauge */}
          <Box
            sx={{
              position: 'relative',
              width: 100,
              height: 100,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress
              variant="determinate"
              value={compositeScore}
              size={100}
              thickness={5}
              sx={{
                color: getGaugeColor(compositeScore),
                position: 'absolute',
              }}
            />
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="h5" fontWeight={700} color={getGaugeColor(compositeScore)}>
                {Math.round(compositeScore)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Score
              </Typography>
            </Box>
          </Box>
          
          {/* Quick Stats */}
          <Box sx={{ flex: 1 }}>
            {/* Buy/Sell Scores Bar Chart */}
            {(recommendation.buy_score !== undefined || recommendation.sell_score !== undefined) && (
              <Tooltip title="Buy Score vs Sell Score comparison">
                <Box sx={{ mb: 1.5, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary" fontWeight={600}>
                      Buy / Sell Scores
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'flex-end', height: 40 }}>
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Box
                        sx={{
                          width: '100%',
                          bgcolor: 'success.main',
                          height: `${((recommendation.buy_score || 0) / 100) * 40}px`,
                          borderRadius: '4px 4px 0 0',
                          transition: 'height 0.3s ease',
                        }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                        {Math.round(recommendation.buy_score || 0)}
                      </Typography>
                    </Box>
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Box
                        sx={{
                          width: '100%',
                          bgcolor: 'error.main',
                          height: `${((recommendation.sell_score || 0) / 100) * 40}px`,
                          borderRadius: '4px 4px 0 0',
                          transition: 'height 0.3s ease',
                        }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                        {Math.round(recommendation.sell_score || 0)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Tooltip>
            )}
            
            <Tooltip title="Signal Strength: -100 (strong sell) to +100 (strong buy)">
              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Signal
                  </Typography>
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    color={signalStrength > 0 ? 'success.main' : signalStrength < 0 ? 'error.main' : 'text.secondary'}
                  >
                    {signalStrength > 0 ? '+' : ''}{signalStrength.toFixed(0)}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.abs(signalStrength)}
                  sx={{
                    height: 6,
                    borderRadius: 1,
                    bgcolor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: signalStrength > 0 ? 'success.main' : 'error.main',
                    },
                  }}
                />
              </Box>
            </Tooltip>
            
            <Tooltip title="Confidence in this recommendation">
              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Confidence
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {(confidence * 100).toFixed(0)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={confidence * 100}
                  sx={{ height: 6, borderRadius: 1 }}
                  color={confidence > 0.7 ? 'success' : confidence > 0.4 ? 'warning' : 'error'}
                />
              </Box>
            </Tooltip>
            
            {recommendation.allocation && (
              <Tooltip title="Allocation drift from target">
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      Allocation Drift
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {(recommendation.allocation.difference * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(100, Math.abs(recommendation.allocation.difference) * 1000)}
                    sx={{ height: 6, borderRadius: 1 }}
                    color="warning"
                  />
                </Box>
              </Tooltip>
            )}
          </Box>
        </Box>
        
        {/* Key Indicators (3-5 najważniejszych) */}
        {recommendation.summary?.key_indicators && recommendation.summary.key_indicators.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ mb: 1, display: 'block' }}>
              Key Indicators
            </Typography>
            {recommendation.summary.key_indicators.slice(0, 5).map((ind, idx) => {
              const normalizedValue = normalizeIndicatorValue(ind);
              const signalColor = getSignalColor(ind.signal);
              const explanation = indicatorExplanations[ind.name] || `${ind.name} indicator`;
              
              return (
                <Tooltip 
                  key={idx}
                  title={explanation}
                  arrow
                  placement="top"
                >
                  <Box sx={{ mb: 1.5, cursor: 'help' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="body2" fontWeight={500}>
                        {ind.name}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color={signalColor}
                        >
                          {ind.value.toFixed(2)}
                        </Typography>
                        <Chip
                          label={ind.signal}
                          size="small"
                          sx={{
                            height: 18,
                            fontSize: '0.65rem',
                            bgcolor: signalColor,
                            color: 'white',
                          }}
                        />
                      </Box>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={normalizedValue}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          background: `linear-gradient(90deg, ${signalColor}22 0%, ${signalColor} 100%)`,
                          borderRadius: 1,
                        },
                      }}
                    />
                  </Box>
                </Tooltip>
              );
            })}
          </Box>
        )}
        
        {/* Strengths and Concerns */}
        {(recommendation.summary?.strengths?.length || recommendation.summary?.concerns?.length) && (
          <Box sx={{ mb: 2 }}>
            {recommendation.summary?.strengths && recommendation.summary.strengths.length > 0 && (
              <Box sx={{ mb: 1 }}>
                {recommendation.summary.strengths.slice(0, 2).map((strength, idx) => (
                  <Chip
                    key={idx}
                    label={`+ ${strength}`}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ mr: 0.5, mb: 0.5, fontSize: '0.7rem' }}
                  />
                ))}
              </Box>
            )}
            {recommendation.summary?.concerns && recommendation.summary.concerns.length > 0 && (
              <Box>
                {recommendation.summary.concerns.slice(0, 2).map((concern, idx) => (
                  <Chip
                    key={idx}
                    label={`! ${concern}`}
                    size="small"
                    color="warning"
                    variant="outlined"
                    sx={{ mr: 0.5, mb: 0.5, fontSize: '0.7rem' }}
                  />
                ))}
              </Box>
            )}
          </Box>
        )}
        
        {/* Reason */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, fontStyle: 'italic' }}
        >
          {recommendation.reason}
        </Typography>
        
        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            size="medium"
            color={actionColor}
            fullWidth
            sx={{ fontWeight: 600 }}
          >
            {recommendation.action === 'buy' ? 'Buy' : 'Sell'}
            {recommendation.allocation &&
              ` ${(Math.abs(recommendation.allocation.difference) * 100).toFixed(1)}%`}
          </Button>
          <Tooltip title="View detailed analysis">
            <IconButton
              onClick={onExpand}
              size="small"
              sx={{
                border: 1,
                borderColor: 'divider',
              }}
            >
              <ExpandMore />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SimplifiedRecommendationCard;
