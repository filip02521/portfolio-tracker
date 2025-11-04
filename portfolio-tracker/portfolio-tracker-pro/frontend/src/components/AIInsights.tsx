import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Paper,
} from '@mui/material';
import { TrendingUp, TrendingDown, AutoGraph } from '@mui/icons-material';
import SimplifiedRecommendationCard from './SimplifiedRecommendationCard';

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
  summary?: {
    key_indicators?: Array<{
      name: string;
      value: number;
      signal: string;
      weight: string;
    }>;
    strengths?: string[];
    concerns?: string[];
  };
  allocation?: {
    current: number;
    target: number;
    difference: number;
  };
}

interface Prediction {
  symbol: string;
  predicted_price: number;
  confidence: number;
  upper_bound: number;
  lower_bound: number;
}

interface RecommendationsResponse {
  recommendations: AIRecommendation[];
  total_rebalance_amount?: number;
  model_used?: string;
  status?: string;
}

const AIInsights: React.FC = () => {
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [sortBy, setSortBy] = useState<'priority' | 'composite_score' | 'signal_strength'>('priority');
  const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  useEffect(() => {
    fetchRecommendations();
  }, [riskTolerance]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/ai/recommendations?risk_tolerance=${riskTolerance}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
      }

      const data: RecommendationsResponse = await response.json();
      
      if (data.recommendations && Array.isArray(data.recommendations)) {
        setRecommendations(data.recommendations);
      } else {
        setRecommendations([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load AI recommendations');
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredAndSortedRecommendations = useMemo(() => {
    let filtered = [...recommendations];

    // Sort by priority first, then by the selected sort option
    filtered.sort((a, b) => {
      // Priority order: high > medium > low
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      const priorityDiff = (priorityOrder[b.priority as keyof typeof priorityOrder] || 1) - 
                          (priorityOrder[a.priority as keyof typeof priorityOrder] || 1);
      
      if (priorityDiff !== 0) {
        return priorityDiff;
      }

      // Then sort by selected criteria
      switch (sortBy) {
        case 'composite_score':
          return (b.composite_score || 0) - (a.composite_score || 0);
        case 'signal_strength':
          return Math.abs(b.signal_strength || 0) - Math.abs(a.signal_strength || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [recommendations, sortBy]);

  const handleExpandCard = (index: number) => {
    setExpandedCard(expandedCard === index ? null : index);
  };

  // Dashboard Summary
  const summary = useMemo(() => {
    const buyCount = recommendations.filter(r => r.action === 'buy').length;
    const sellCount = recommendations.filter(r => r.action === 'sell').length;
    const highPriority = recommendations.filter(r => r.priority === 'high').length;
    const avgConfidence = recommendations.length > 0
      ? recommendations.reduce((sum, r) => sum + (r.confidence || 0), 0) / recommendations.length
      : 0;

    return {
      total: recommendations.length,
      buyCount,
      sellCount,
      highPriority,
      avgConfidence,
    };
  }, [recommendations]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight={600}>
          AI Insights & Recommendations
        </Typography>
        <Typography variant="body1" color="text.secondary">
          AI-powered portfolio analysis and rebalancing recommendations
        </Typography>
      </Box>

      {/* Dashboard Summary */}
      {summary.total > 0 && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Recommendations
                </Typography>
                <Typography variant="h4" fontWeight={600}>
                  {summary.total}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Buy Signals
                </Typography>
                <Typography variant="h4" fontWeight={600} color="success.main">
                  {summary.buyCount}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Sell Signals
                </Typography>
                <Typography variant="h4" fontWeight={600} color="error.main">
                  {summary.sellCount}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  High Priority
                </Typography>
                <Typography variant="h4" fontWeight={600} color="warning.main">
                  {summary.highPriority}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Risk Tolerance</InputLabel>
              <Select
                value={riskTolerance}
                label="Risk Tolerance"
                onChange={(e) => setRiskTolerance(e.target.value as typeof riskTolerance)}
              >
                <MenuItem value="conservative">Conservative</MenuItem>
                <MenuItem value="moderate">Moderate</MenuItem>
                <MenuItem value="aggressive">Aggressive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                label="Sort By"
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              >
                <MenuItem value="priority">Priority</MenuItem>
                <MenuItem value="composite_score">Composite Score</MenuItem>
                <MenuItem value="signal_strength">Signal Strength</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Recommendations List */}
      {filteredAndSortedRecommendations.length === 0 ? (
        <Alert severity="info">
          No recommendations available at this time. Try adjusting your risk tolerance or check back later.
        </Alert>
      ) : (
        <Box>
          {filteredAndSortedRecommendations.map((recommendation, index) => (
            <SimplifiedRecommendationCard
              key={index}
              recommendation={recommendation}
              index={index}
              onExpand={() => handleExpandCard(index)}
            />
          ))}
        </Box>
      )}
    </Container>
  );
};

export default AIInsights;
