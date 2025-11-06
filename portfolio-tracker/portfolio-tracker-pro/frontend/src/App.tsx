import React, { useState, Suspense, lazy, useMemo } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  ThemeProvider,
  CssBaseline,
  Button,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  ListSubheader,
  Divider,
  useMediaQuery,
  useTheme,
  CircularProgress,
  Tooltip,
  Menu,
  MenuItem,
  Avatar,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import DashboardIcon from '@mui/icons-material/SpaceDashboard';
import PortfolioIcon from '@mui/icons-material/AccountBalanceWallet';
import TransactionsIcon from '@mui/icons-material/CompareArrows';
import AnalyticsIcon from '@mui/icons-material/QueryStats';
import AlertsIcon from '@mui/icons-material/NotificationsActive';
import RiskIcon from '@mui/icons-material/Security';
import GoalsIcon from '@mui/icons-material/Flag';
import TaxIcon from '@mui/icons-material/ReceiptLong';
import SettingsIcon from '@mui/icons-material/Settings';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AssessmentIcon from '@mui/icons-material/Assessment';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { portfolioService } from './services/portfolioService';
import ProtectedRoute from './components/ProtectedRoute';
import { Logo } from './components/common/Logo';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { createAppTheme } from './theme/themeConfig';

// Lazy load components for better performance
const Dashboard = lazy(() => import('./components/Dashboard'));
const Portfolio = lazy(() => import('./components/Portfolio'));
const Transactions = lazy(() => import('./components/Transactions'));
const Analytics = lazy(() => import('./components/Analytics'));
const PriceAlerts = lazy(() => import('./components/PriceAlerts'));
const RiskManagement = lazy(() => import('./components/RiskManagement'));
const Settings = lazy(() => import('./components/Settings'));
const Goals = lazy(() => import('./components/Goals'));
const TaxOptimizer = lazy(() => import('./components/TaxOptimizer'));
const AdminMetrics = lazy(() => import('./components/AdminMetrics'));
const AIInsights = lazy(() => import('./components/AIInsights'));
const ConfluenceStrategyDashboard = lazy(() => import('./components/ConfluenceStrategyDashboard'));
const FundamentalScreening = lazy(() => import('./components/FundamentalScreening'));
const Login = lazy(() => import('./components/Login'));
const Register = lazy(() => import('./components/Register'));

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <Box sx={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    minHeight: '50vh' 
  }}>
    <CircularProgress />
  </Box>
);

// Color mode context type
type ColorMode = 'light' | 'dark';

// Navigation component with mobile drawer
interface NavigationProps {
  toggleColorMode: () => void;
}

const Navigation: React.FC<NavigationProps> = ({ toggleColorMode }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [userData, setUserData] = useState<{username?: string, email?: string} | null>(null);
  const location = useLocation();
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isAuthenticated = portfolioService.isAuthenticated();
  const isDarkMode = theme.palette.mode === 'dark';

  // Fetch user data on mount
  React.useEffect(() => {
    if (isAuthenticated) {
      portfolioService.getCurrentUser()
        .then(data => {
          setUserData({ username: data?.username, email: data?.email });
        })
        .catch(() => {
          // Silent fail - user data not critical for navigation
        });
    }
  }, [isAuthenticated]);

  const handleLogout = async () => {
    await portfolioService.logout();
    navigate('/login');
  };

  const menuSections = [
    {
      title: 'Przegląd',
      items: [
        { text: 'Dashboard', path: '/', icon: <DashboardIcon /> },
      ],
    },
    {
      title: 'Portfel',
      items: [
        { text: 'Portfolio', path: '/portfolio', icon: <PortfolioIcon /> },
        { text: 'Transactions', path: '/transactions', icon: <TransactionsIcon /> },
      ],
    },
    {
      title: 'Analiza',
      items: [
        { text: 'Analytics', path: '/analytics', icon: <AnalyticsIcon /> },
        { text: 'Risk Management', path: '/risk-management', icon: <RiskIcon /> },
        { text: 'Price Alerts', path: '/price-alerts', icon: <AlertsIcon /> },
        { text: 'AI Insights', path: '/ai-insights', icon: <AutoAwesomeIcon /> },
        { text: 'Confluence Strategy', path: '/strategy/confluence', icon: <TrendingUpIcon /> },
      ],
    },
    {
      title: 'Planowanie',
      items: [
        { text: 'Goals', path: '/goals', icon: <GoalsIcon /> },
        { text: 'Tax Optimizer', path: '/tax-optimizer', icon: <TaxIcon /> },
      ],
    },
    {
      title: 'Ustawienia',
      items: [
        { text: 'Settings', path: '/settings', icon: <SettingsIcon /> },
      ],
    },
  ];

  const primaryDesktopItems = [
    { text: 'Dashboard', path: '/' },
    { text: 'Portfolio', path: '/portfolio' },
    { text: 'Analytics', path: '/analytics' },
    { text: 'Goals', path: '/goals' },
  ];

  const secondaryDesktopItems = [
    { text: 'Transactions', path: '/transactions', icon: <TransactionsIcon /> },
    { text: 'Risk Management', path: '/risk-management', icon: <RiskIcon /> },
    { text: 'Price Alerts', path: '/price-alerts', icon: <AlertsIcon /> },
    { text: 'AI Insights', path: '/ai-insights', icon: <AutoAwesomeIcon /> },
    { text: 'Confluence Strategy', path: '/strategy/confluence', icon: <TrendingUpIcon /> },
    null, // Divider
    { text: 'Tax Optimizer', path: '/tax-optimizer', icon: <TaxIcon /> },
    null, // Divider
    { text: 'Settings', path: '/settings', icon: <SettingsIcon /> },
    { text: 'Admin Metrics', path: '/admin/metrics' },
  ];

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center', pt: 3, pb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <Logo size="small" interactive={false} />
      </Box>
      {userData && isAuthenticated && (
        <Box sx={{ px: 3, mb: 3, display: 'flex', alignItems: 'center', gap: 1.5, justifyContent: 'center' }}>
          <Avatar sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}>
            {userData.username?.charAt(0).toUpperCase() || 'U'}
          </Avatar>
          <Box sx={{ textAlign: 'left' }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {userData.username || 'User'}
            </Typography>
            {userData.email && (
              <Typography variant="caption" color="text.secondary">
                {userData.email}
              </Typography>
            )}
          </Box>
        </Box>
      )}
      <List
        sx={{ textAlign: 'left' }}
      >
        {menuSections.map((section, sectionIndex) => (
          <React.Fragment key={section.title}>
            <ListSubheader disableSticky sx={{ bgcolor: 'transparent', color: 'text.secondary', fontWeight: 600, px: 3 }}>
              {section.title}
            </ListSubheader>
            {section.items.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={location.pathname === item.path}
                  sx={{ 
                    py: 1.5,
                    px: 3,
                    '&.Mui-selected': { 
                      backgroundColor: isDarkMode ? 'rgba(37, 99, 235, 0.16)' : 'rgba(37, 99, 235, 0.12)',
                      borderLeft: '3px solid',
                      borderLeftColor: 'primary.main'
                    },
                    '&:hover': {
                      backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)'
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40, color: 'text.secondary' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} primaryTypographyProps={{ fontSize: '0.9375rem' }} />
                </ListItemButton>
              </ListItem>
            ))}
            {sectionIndex < menuSections.length - 1 && (
              <Divider sx={{ my: 2, mx: 3, borderColor: isDarkMode ? 'rgba(148,163,184,0.16)' : 'rgba(148,163,184,0.2)' }} />
            )}
          </React.Fragment>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ 
                mr: 2,
                width: { xs: 48, sm: 48 },
                height: { xs: 48, sm: 48 },
                padding: 1
              }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Box sx={{ flexGrow: isMobile ? 0 : 1, display: 'flex', alignItems: 'center' }}>
            <Logo isMobile={isMobile} size={isMobile ? 'small' : 'medium'} inverted={isAuthenticated} interactive={false} />
          </Box>
          {!isMobile && isAuthenticated && (
            <Box sx={{ display: 'flex', gap: 1, ml: 2, alignItems: 'center' }}>
              {primaryDesktopItems.map((item) => (
                <Button
                  key={item.text}
                  color="inherit"
                  component={Link}
                  to={item.path}
                  sx={{
                    textTransform: 'none',
                    fontWeight: location.pathname === item.path ? 700 : 500,
                    backgroundColor: location.pathname === item.path ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                    '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' },
                    borderRadius: '10px',
                  }}
                >
                  {item.text}
                </Button>
              ))}
              <Tooltip title="Więcej">
                <IconButton color="inherit" onClick={(e) => setAnchorEl(e.currentTarget)}>
                  <MoreVertIcon />
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={() => setAnchorEl(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                sx={{
                  '& .MuiPaper-root': {
                    borderRadius: '12px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
                    border: `1px solid ${theme.palette.divider}`,
                    mt: 1,
                  },
                }}
              >
                {secondaryDesktopItems.map((item, idx) => {
                  if (!item) {
                    return <Divider key={`divider-${idx}`} sx={{ my: 0.5 }} />;
                  }
                  return (
                    <MenuItem
                      key={item.text}
                      onClick={() => { setAnchorEl(null); navigate(item.path); }}
                      selected={location.pathname === item.path}
                      sx={{
                        py: 1.5,
                        px: 2,
                        '&.Mui-selected': {
                          backgroundColor: theme.palette.mode === 'light' 
                            ? 'rgba(37, 99, 235, 0.08)' 
                            : 'rgba(37, 99, 235, 0.2)',
                          '&:hover': {
                            backgroundColor: theme.palette.mode === 'light' 
                              ? 'rgba(37, 99, 235, 0.12)' 
                              : 'rgba(37, 99, 235, 0.25)',
                          },
                        },
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'light' 
                            ? 'rgba(37, 99, 235, 0.04)' 
                            : 'rgba(255, 255, 255, 0.05)',
                        },
                      }}
                    >
                      {item.icon && (
                        <ListItemIcon sx={{ minWidth: 40 }}>
                          {item.icon}
                        </ListItemIcon>
                      )}
                      <ListItemText 
                        primary={item.text} 
                        primaryTypographyProps={{ 
                          fontSize: '0.9375rem',
                          fontWeight: location.pathname === item.path ? 600 : 400,
                        }}
                      />
                    </MenuItem>
                  );
                })}
              </Menu>
              <Tooltip title={userData?.username || 'User'}>
                <IconButton
                  onClick={(e) => setUserMenuAnchor(e.currentTarget)}
                  sx={{ 
                    border: '2px solid',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    '&:hover': { borderColor: 'rgba(255, 255, 255, 0.5)' }
                  }}
                >
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }}>
                    {userData?.username?.charAt(0).toUpperCase() || 'U'}
                  </Avatar>
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={() => setUserMenuAnchor(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              >
                <MenuItem disabled>
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {userData?.username || 'User'}
                    </Typography>
                    {userData?.email && (
                      <Typography variant="caption" color="text.secondary">
                        {userData.email}
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => { setUserMenuAnchor(null); navigate('/settings'); }}>
                  <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                  <ListItemText>Settings</ListItemText>
                </MenuItem>
                <Divider />
                <MenuItem 
                  onClick={async () => { 
                    setUserMenuAnchor(null); 
                    await handleLogout(); 
                  }}
                  sx={{ 
                    '&:hover': { 
                      bgcolor: 'rgba(220, 38, 38, 0.1)',
                      '& .MuiListItemIcon-root': { color: 'error.main' },
                      '& .MuiListItemText-primary': { color: 'error.main' }
                    }
                  }}
                >
                  <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
                  <ListItemText>Logout</ListItemText>
                </MenuItem>
              </Menu>
              <Tooltip title={isDarkMode ? 'Light mode' : 'Dark mode'}>
                <IconButton 
                  color="inherit" 
                  onClick={toggleColorMode}
                  sx={{ 
                    border: '2px solid',
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    ml: 2,
                    '&:hover': { borderColor: 'rgba(255, 255, 255, 0.5)' }
                  }}
                >
                  {isDarkMode ? <Brightness7Icon /> : <Brightness4Icon />}
                </IconButton>
              </Tooltip>
            </Box>
          )}
          {!isMobile && !isAuthenticated && (
            <Box sx={{ display: 'flex', gap: 2, ml: 2 }}>
              <Tooltip title={isDarkMode ? 'Light mode' : 'Dark mode'}>
                <IconButton 
                  color="inherit" 
                  onClick={toggleColorMode}
                  sx={{ mr: 1 }}
                >
                  {isDarkMode ? <Brightness7Icon /> : <Brightness4Icon />}
                </IconButton>
              </Tooltip>
              <Button 
                color="inherit" 
                component={Link} 
                to="/login"
                sx={{ textTransform: 'none' }}
              >
                Login
              </Button>
              <Button 
                color="inherit" 
                component={Link} 
                to="/register"
                variant="outlined"
                sx={{ textTransform: 'none', borderColor: 'rgba(255, 255, 255, 0.3)' }}
              >
                Register
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
          sx: {
            backdropFilter: isDarkMode ? 'blur(8px)' : 'blur(4px)',
            backgroundColor: isDarkMode ? 'rgba(0, 0, 0, 0.5)' : 'rgba(255, 255, 255, 0.3)'
          }
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: 280,
            background: isDarkMode 
              ? 'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)' 
              : 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
            borderRight: `1px solid ${theme.palette.divider}`,
            boxShadow: isDarkMode 
              ? '8px 0 32px rgba(0, 0, 0, 0.3)' 
              : '8px 0 32px rgba(0, 0, 0, 0.1)',
          },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};

function App() {
  const [mode, setMode] = useState<ColorMode>('light');
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  const toggleColorMode = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navigation toggleColorMode={toggleColorMode} />

          {/* Main Content */}
          <Container 
            maxWidth="xl" 
            sx={{ 
              flexGrow: 1, 
              py: { xs: 2, sm: 3, md: 4 },
              px: { xs: 1, sm: 2, md: 3 }
            }}
          >
            <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route 
                    path="/" 
                    element={
                      <ProtectedRoute>
                        <ErrorBoundary>
                          <Dashboard />
                        </ErrorBoundary>
                      </ProtectedRoute>
                    } 
                  />
                <Route 
                  path="/portfolio" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <Portfolio />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/transactions" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <Transactions />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/analytics" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <Analytics />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/price-alerts" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <PriceAlerts />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/risk-management" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <RiskManagement />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/settings" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <Settings />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/goals" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <Goals />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/tax-optimizer" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <TaxOptimizer />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/ai-insights" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <AIInsights />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/strategy/confluence" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <ConfluenceStrategyDashboard />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/admin/metrics" 
                  element={
                    <ProtectedRoute>
                      <ErrorBoundary>
                        <AdminMetrics />
                      </ErrorBoundary>
                    </ProtectedRoute>
                  } 
                />
              </Routes>
            </Suspense>
            </ErrorBoundary>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;