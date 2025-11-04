import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
} from '@mui/material';
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'priority' | 'composite_score' | 'signal_strength'>('priority');
  const [riskTolerance, setRiskTolerance] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate');
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('authToken');
      if (!token) {
        setError('Authentication required. Please log in.');
        setLoading(false);
        return;
      }
      
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      // Ensure baseUrl doesn't end with /api to avoid double /api/api
      const apiUrl = baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`;
      const response = await fetch(
        `${apiUrl}/ai/recommendations?risk_tolerance=${riskTolerance}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          setError('Authentication failed. Please log in again.');
          return;
        }
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
  }, [riskTolerance]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

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
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 2, 
          mb: 4 
        }}>
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
        </Box>
      )}

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
          gap: 2,
          alignItems: 'center'
        }}>
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
        </Box>
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
