import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  AlertTitle,
  LinearProgress,
  Switch,
  FormControlLabel,
  Divider,
  Chip,
  Tabs,
  Tab,
  IconButton,
  MenuItem,
} from '@mui/material';
import {
  VpnKey,
  CheckCircle,
  Error as ErrorIcon,
  Refresh,
  Clear,
  Save,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { portfolioService } from '../services/portfolioService';
import BackupRestore from './BackupRestore';

interface ApiKeysStatus {
  binance: {
    configured: boolean;
    api_key_masked?: string;
  };
  bybit: {
    configured: boolean;
    api_key_masked?: string;
  };
  xtb: {
    configured: boolean;
    username?: string;
  };
  alpha_vantage?: {
    configured: boolean;
    api_key_masked?: string;
  };
  polygon?: {
    configured: boolean;
    api_key_masked?: string;
  };
}

interface AppSettings {
  cache_enabled: boolean;
  auto_refresh_enabled: boolean;
  refresh_interval: number;
  theme: string;
  currency: string;
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [apiKeysStatus, setApiKeysStatus] = useState<ApiKeysStatus | null>(null);
  const [appSettings, setAppSettings] = useState<AppSettings | null>(null);
  
  // Form states for API keys
  const [binanceApiKey, setBinanceApiKey] = useState('');
  const [binanceSecretKey, setBinanceSecretKey] = useState('');
  const [bybitApiKey, setBybitApiKey] = useState('');
  const [bybitSecretKey, setBybitSecretKey] = useState('');
  const [xtbUsername, setXtbUsername] = useState('');
  const [xtbPassword, setXtbPassword] = useState('');
  const [alphaVantageApiKey, setAlphaVantageApiKey] = useState('');
  const [polygonApiKey, setPolygonApiKey] = useState('');
  
  // Visibility toggles
  const [showBinanceKeys, setShowBinanceKeys] = useState(false);
  const [showBybitKeys, setShowBybitKeys] = useState(false);
  const [showXtbPassword, setShowXtbPassword] = useState(false);
  
  // Messages
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const [keysStatus, settings] = await Promise.all([
        portfolioService.getApiKeysStatus(),
        portfolioService.getAppSettings(),
      ]);
      setApiKeysStatus(keysStatus);
      setAppSettings(settings);
    } catch (error: any) {
      setErrorMessage(error?.userMessage || error?.message || 'Failed to load settings');
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKeys = async (exchange: string) => {
    try {
      setSuccessMessage(null);
      setErrorMessage(null);

      let keys: any = {};
      if (exchange === 'binance') {
        if (binanceApiKey) keys.api_key = binanceApiKey;
        if (binanceSecretKey) keys.secret_key = binanceSecretKey;
      } else if (exchange === 'bybit') {
        if (bybitApiKey) keys.api_key = bybitApiKey;
        if (bybitSecretKey) keys.secret_key = bybitSecretKey;
      } else if (exchange === 'xtb') {
        if (xtbUsername) keys.username = xtbUsername;
        if (xtbPassword) keys.password = xtbPassword;
      } else if (exchange === 'alpha_vantage') {
        if (alphaVantageApiKey) keys.api_key = alphaVantageApiKey;
      } else if (exchange === 'polygon') {
        if (polygonApiKey) keys.api_key = polygonApiKey;
      }

      await portfolioService.updateApiKeys(exchange, keys);
      setSuccessMessage(`${exchange.charAt(0).toUpperCase() + exchange.slice(1)} API keys updated successfully!`);
      
      // Clear form fields
      if (exchange === 'binance') {
        setBinanceApiKey('');
        setBinanceSecretKey('');
      } else if (exchange === 'bybit') {
        setBybitApiKey('');
        setBybitSecretKey('');
      } else if (exchange === 'xtb') {
        setXtbUsername('');
        setXtbPassword('');
      } else if (exchange === 'alpha_vantage') {
        setAlphaVantageApiKey('');
      } else if (exchange === 'polygon') {
        setPolygonApiKey('');
      }
      
      // Refresh status
      await fetchSettings();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      setErrorMessage(error?.userMessage || error?.message || `Failed to update ${exchange} API keys`);
      setTimeout(() => setErrorMessage(null), 5000);
    }
  };

  const handleTestConnection = async (exchange: string) => {
    try {
      setTestingConnection(exchange);
      setErrorMessage(null);
      setSuccessMessage(null);
      
      const result = await portfolioService.testConnection(exchange);
      
      if (result.success) {
        setSuccessMessage(`${exchange.charAt(0).toUpperCase() + exchange.slice(1)} connection successful!`);
      } else {
        setErrorMessage(result.error || `Failed to connect to ${exchange}`);
      }
      setTimeout(() => {
        setSuccessMessage(null);
        setErrorMessage(null);
      }, 5000);
    } catch (error: any) {
      setErrorMessage(error?.userMessage || error?.message || `Failed to test ${exchange} connection`);
      setTimeout(() => setErrorMessage(null), 5000);
    } finally {
      setTestingConnection(null);
    }
  };

  const handleUpdateAppSettings = async () => {
    try {
      setSuccessMessage(null);
      setErrorMessage(null);
      
      if (!appSettings) return;
      
      await portfolioService.updateAppSettings({
        cache_enabled: appSettings.cache_enabled,
        auto_refresh_enabled: appSettings.auto_refresh_enabled,
        refresh_interval: appSettings.refresh_interval,
        theme: appSettings.theme,
        currency: appSettings.currency,
      });
      
      setSuccessMessage('Application settings updated successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      setErrorMessage(error?.userMessage || error?.message || 'Failed to update settings');
      setTimeout(() => setErrorMessage(null), 5000);
    }
  };

  const handleClearCache = async () => {
    try {
      setSuccessMessage(null);
      setErrorMessage(null);
      
      await portfolioService.clearCache();
      setSuccessMessage('Cache cleared successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      setErrorMessage(error?.userMessage || error?.message || 'Failed to clear cache');
      setTimeout(() => setErrorMessage(null), 5000);
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h1" sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1
          }}>
            Settings
          </Typography>
          <Typography variant="h5" color="text.secondary">
            Manage your API keys and application preferences
          </Typography>
        </Box>
        <IconButton onClick={fetchSettings} color="primary" size="large">
          <Refresh />
        </IconButton>
      </Box>

      {/* Messages */}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          <AlertTitle>Success</AlertTitle>
          {successMessage}
        </Alert>
      )}
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setErrorMessage(null)}>
          <AlertTitle>Error</AlertTitle>
          {errorMessage}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="API Keys" />
          <Tab label="App Settings" />
          <Tab label="Cache & Data" />
          <Tab label="Backup & Restore" />
        </Tabs>
      </Box>

      {/* Tab 1: API Keys */}
      {tabValue === 0 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
          {/* Binance */}
          <Box>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Binance API
                  </Typography>
                  {apiKeysStatus?.binance.configured ? (
                    <Chip 
                      icon={<CheckCircle />} 
                      label="Configured" 
                      color="success" 
                      size="small" 
                    />
                  ) : (
                    <Chip 
                      icon={<ErrorIcon />} 
                      label="Not Configured" 
                      color="warning" 
                      size="small" 
                    />
                  )}
                </Box>
                {apiKeysStatus?.binance.api_key_masked && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Current API Key: <code>{apiKeysStatus.binance.api_key_masked}</code>
                  </Typography>
                )}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TextField
                    label="API Key"
                    type={showBinanceKeys ? 'text' : 'password'}
                    value={binanceApiKey}
                    onChange={(e) => setBinanceApiKey(e.target.value)}
                    fullWidth
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <IconButton onClick={() => setShowBinanceKeys(!showBinanceKeys)} size="small">
                    {showBinanceKeys ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </Box>
                <TextField
                  label="Secret Key"
                  type={showBinanceKeys ? 'text' : 'password'}
                  value={binanceSecretKey}
                  onChange={(e) => setBinanceSecretKey(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={() => handleSaveApiKeys('binance')}
                    disabled={!binanceApiKey && !binanceSecretKey}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={() => handleTestConnection('binance')}
                    disabled={testingConnection === 'binance' || !apiKeysStatus?.binance.configured}
                  >
                    {testingConnection === 'binance' ? 'Testing...' : 'Test Connection'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Bybit */}
          <Box>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Bybit API
                  </Typography>
                  {apiKeysStatus?.bybit.configured ? (
                    <Chip 
                      icon={<CheckCircle />} 
                      label="Configured" 
                      color="success" 
                      size="small" 
                    />
                  ) : (
                    <Chip 
                      icon={<ErrorIcon />} 
                      label="Not Configured" 
                      color="warning" 
                      size="small" 
                    />
                  )}
                </Box>
                {apiKeysStatus?.bybit.api_key_masked && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Current API Key: <code>{apiKeysStatus.bybit.api_key_masked}</code>
                  </Typography>
                )}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TextField
                    label="API Key"
                    type={showBybitKeys ? 'text' : 'password'}
                    value={bybitApiKey}
                    onChange={(e) => setBybitApiKey(e.target.value)}
                    fullWidth
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <IconButton onClick={() => setShowBybitKeys(!showBybitKeys)} size="small">
                    {showBybitKeys ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </Box>
                <TextField
                  label="Secret Key"
                  type={showBybitKeys ? 'text' : 'password'}
                  value={bybitSecretKey}
                  onChange={(e) => setBybitSecretKey(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={() => handleSaveApiKeys('bybit')}
                    disabled={!bybitApiKey && !bybitSecretKey}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={() => handleTestConnection('bybit')}
                    disabled={testingConnection === 'bybit' || !apiKeysStatus?.bybit.configured}
                  >
                    {testingConnection === 'bybit' ? 'Testing...' : 'Test Connection'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* XTB */}
          <Box>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    XTB API
                  </Typography>
                  {apiKeysStatus?.xtb.configured ? (
                    <Chip 
                      icon={<CheckCircle />} 
                      label="Configured" 
                      color="success" 
                      size="small" 
                    />
                  ) : (
                    <Chip 
                      icon={<ErrorIcon />} 
                      label="Not Configured" 
                      color="warning" 
                      size="small" 
                    />
                  )}
                </Box>
                {apiKeysStatus?.xtb.username && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Current Username: <code>{apiKeysStatus.xtb.username}</code>
                  </Typography>
                )}
                <TextField
                  label="Username"
                  type="text"
                  value={xtbUsername}
                  onChange={(e) => setXtbUsername(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TextField
                    label="Password"
                    type={showXtbPassword ? 'text' : 'password'}
                    value={xtbPassword}
                    onChange={(e) => setXtbPassword(e.target.value)}
                    fullWidth
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <IconButton onClick={() => setShowXtbPassword(!showXtbPassword)} size="small">
                    {showXtbPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={() => handleSaveApiKeys('xtb')}
                    disabled={!xtbUsername && !xtbPassword}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={() => handleTestConnection('xtb')}
                    disabled={testingConnection === 'xtb' || !apiKeysStatus?.xtb.configured}
                  >
                    {testingConnection === 'xtb' ? 'Testing...' : 'Test Connection'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Alpha Vantage */}
          <Box>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Alpha Vantage API
                  </Typography>
                  {apiKeysStatus?.alpha_vantage?.configured ? (
                    <Chip 
                      icon={<CheckCircle />} 
                      label="Configured" 
                      color="success" 
                      size="small" 
                    />
                  ) : (
                    <Chip 
                      icon={<ErrorIcon />} 
                      label="Not Configured" 
                      color="warning" 
                      size="small" 
                    />
                  )}
                </Box>
                {apiKeysStatus?.alpha_vantage?.api_key_masked && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Current API Key: <code>{apiKeysStatus.alpha_vantage.api_key_masked}</code>
                  </Typography>
                )}
                <TextField
                  label="API Key"
                  type="password"
                  value={alphaVantageApiKey}
                  onChange={(e) => setAlphaVantageApiKey(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={() => handleSaveApiKeys('alpha_vantage')}
                    disabled={!alphaVantageApiKey}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={() => handleTestConnection('alpha_vantage')}
                    disabled={testingConnection === 'alpha_vantage' || !apiKeysStatus?.alpha_vantage?.configured}
                  >
                    {testingConnection === 'alpha_vantage' ? 'Testing...' : 'Test Connection'}
                  </Button>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                  Tip: Get a free API key at alphavantage.co and paste it here to enable live stock prices.
                </Typography>
              </CardContent>
            </Card>
          </Box>
          {/* Polygon */}
          <Box>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Polygon.io API
                  </Typography>
                  {apiKeysStatus?.polygon?.configured ? (
                    <Chip 
                      icon={<CheckCircle />} 
                      label="Configured" 
                      color="success" 
                      size="small" 
                    />
                  ) : (
                    <Chip 
                      icon={<ErrorIcon />} 
                      label="Not Configured" 
                      color="warning" 
                      size="small" 
                    />
                  )}
                </Box>
                {apiKeysStatus?.polygon?.api_key_masked && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Current API Key: <code>{apiKeysStatus.polygon.api_key_masked}</code>
                  </Typography>
                )}
                <TextField
                  label="API Key"
                  type="password"
                  value={polygonApiKey}
                  onChange={(e) => setPolygonApiKey(e.target.value)}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Save />}
                    onClick={() => handleSaveApiKeys('polygon')}
                    disabled={!polygonApiKey}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={() => handleTestConnection('polygon')}
                    disabled={testingConnection === 'polygon' || !apiKeysStatus?.polygon?.configured}
                  >
                    {testingConnection === 'polygon' ? 'Testing...' : 'Test Connection'}
                  </Button>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                  Tip: Get an API key at polygon.io to enable fallback real-time prices.
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Tab 2: App Settings */}
      {tabValue === 1 && appSettings && (
        <Box sx={{ maxWidth: { md: '800px' } }}>
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Application Preferences
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={appSettings.cache_enabled}
                        onChange={(e) => setAppSettings({ ...appSettings, cache_enabled: e.target.checked })}
                        color="primary"
                      />
                    }
                    label="Enable Cache"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mt: 0.5 }}>
                    Cache portfolio data to improve performance
                  </Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={appSettings.auto_refresh_enabled}
                        onChange={(e) => setAppSettings({ ...appSettings, auto_refresh_enabled: e.target.checked })}
                        color="primary"
                      />
                    }
                    label="Auto Refresh"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mt: 0.5 }}>
                    Automatically refresh portfolio data
                  </Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                <TextField
                  label="Refresh Interval (seconds)"
                  type="number"
                  value={appSettings.refresh_interval}
                  onChange={(e) => setAppSettings({ ...appSettings, refresh_interval: parseInt(e.target.value) || 30 })}
                  fullWidth
                  size="small"
                  sx={{ mb: 3 }}
                  inputProps={{ min: 10, max: 300 }}
                />

                <TextField
                  label="Default Currency"
                  select
                  value={appSettings.currency}
                  onChange={(e) => setAppSettings({ ...appSettings, currency: e.target.value })}
                  fullWidth
                  size="small"
                  sx={{ mb: 3 }}
                >
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="PLN">PLN</MenuItem>
                  <MenuItem value="EUR">EUR</MenuItem>
                </TextField>

                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleUpdateAppSettings}
                  fullWidth
                  size="large"
                >
                  Save Settings
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Tab 3: Cache & Data */}
      {tabValue === 2 && (
        <Box sx={{ maxWidth: { md: '800px' } }}>
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Cache & Data Management
                </Typography>
                
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Clear cached data to force fresh data fetch from exchanges. This may temporarily slow down the application.
                </Typography>

                <Button
                  variant="outlined"
                  color="warning"
                  startIcon={<Clear />}
                  onClick={handleClearCache}
                  size="large"
                  fullWidth
                >
                  Clear All Cache
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Tab 4: Backup & Restore */}
      {tabValue === 3 && (
        <Box>
          <BackupRestore
            onBackupCreated={() => {
              setSuccessMessage('Backup created successfully!');
              setTimeout(() => setSuccessMessage(null), 3000);
            }}
            onRestoreComplete={() => {
              setSuccessMessage('Backup restored successfully! Please refresh the page.');
              setTimeout(() => setSuccessMessage(null), 5000);
            }}
          />
        </Box>
      )}
    </Box>
  );
};

export default Settings;
