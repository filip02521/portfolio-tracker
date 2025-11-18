import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  AlertTitle,
  Link,
  Container,
} from '@mui/material';
import { Login as LoginIcon } from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import { useNavigate, Link as RouterLink } from 'react-router-dom';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Clear any invalid token on mount to prevent loops
  React.useEffect(() => {
    // Always clear invalid token flags when on login page
    // This ensures clean state after logout
    sessionStorage.removeItem('auth:invalid_token');
    
    // Also clear token if invalid flag was set (defensive cleanup)
    const hasInvalidToken = sessionStorage.getItem('auth:invalid_token');
    if (hasInvalidToken) {
      localStorage.removeItem('authToken');
      sessionStorage.removeItem('auth:invalid_token');
    }
    
    // Don't auto-redirect if token exists - let user decide
    // Auto-redirecting causes loops if token is invalid
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clear any stale flags before login attempt
      sessionStorage.removeItem('auth:invalid_token');
      
      const response = await portfolioService.login(username, password);
      
      // Store token
      localStorage.setItem('authToken', response.access_token);
      
      // Clear any invalid token flags (defensive)
      sessionStorage.removeItem('auth:invalid_token');
      
      // Clear cache asynchronously (don't wait for it)
      portfolioService.clearCache().catch(() => {
        // Ignore errors - not critical for login flow
      });
      
      // Verify token is stored before navigation
      const storedToken = localStorage.getItem('authToken');
      if (!storedToken) {
        throw new Error('Token was not stored correctly');
      }
      
      console.debug('Login: Token stored, navigating to dashboard');
      
      // Small delay to ensure token is set before navigation
      // This prevents race condition where Dashboard might check auth before token is set
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Navigate immediately without full page reload
      navigate('/', { replace: true });
    } catch (err: any) {
      // On error, make sure flags are cleared
      sessionStorage.removeItem('auth:invalid_token');
      localStorage.removeItem('authToken');
      
      setError(err?.userMessage || err?.message || 'Login failed. Please try again.');
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          py: 4,
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 400 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
              <LoginIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
                Welcome Back
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to your InsightPort account
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                <AlertTitle>Error</AlertTitle>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                label="Username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                fullWidth
                required
                sx={{ mb: 2 }}
                autoFocus
              />

              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                required
                sx={{ mb: 3 }}
              />

              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={loading || !username || !password}
                sx={{ mb: 2 }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>

              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{' '}
                  <Link component={RouterLink} to="/register" sx={{ fontWeight: 600 }}>
                    Sign up
                  </Link>
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default Login;


