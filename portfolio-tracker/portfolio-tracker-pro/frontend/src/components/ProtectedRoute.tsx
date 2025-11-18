import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { portfolioService } from '../services/portfolioService';

interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  const [isChecking, setIsChecking] = React.useState(true);
  const [shouldRedirect, setShouldRedirect] = React.useState(false);

  // Check authentication status
  React.useEffect(() => {
    // Clear invalid token flags first
    const hasInvalidToken = sessionStorage.getItem('auth:invalid_token');
    if (hasInvalidToken) {
      localStorage.removeItem('authToken');
      sessionStorage.removeItem('auth:invalid_token');
      setShouldRedirect(true);
      setIsChecking(false);
      return;
    }

    // Simple check - just verify token exists
    // If token is invalid, interceptor will handle 401 and redirect
    // Don't make async requests here to prevent loops
    const isAuthenticated = portfolioService.isAuthenticated();
    
    if (!isAuthenticated) {
      setShouldRedirect(true);
    } else {
      setShouldRedirect(false);
    }
    
    setIsChecking(false);
  }, [location.pathname]);

  // Show loading while checking (prevents flash of login page)
  if (isChecking) {
    return null; // or a loading spinner
  }

  if (shouldRedirect) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
};

export default ProtectedRoute;


