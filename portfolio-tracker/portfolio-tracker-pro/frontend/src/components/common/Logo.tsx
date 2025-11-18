import React from 'react';
import { Box, Typography, useTheme, Tooltip } from '@mui/material';

interface LogoProps {
  isMobile?: boolean;
  size?: 'small' | 'medium' | 'large';
  showText?: boolean;
  variant?: 'full' | 'icon-only' | 'text-only';
  animated?: boolean;
  interactive?: boolean;
  inverted?: boolean; // For dark backgrounds (AppBar)
}

export const Logo: React.FC<LogoProps> = ({ 
  isMobile = false, 
  size = 'medium', 
  showText,
  variant = 'full',
  animated = true,
  interactive = true,
  inverted = false
}) => {
  const theme = useTheme();
  const isLight = theme.palette.mode === 'light';
  const iconSize = size === 'small' ? 32 : size === 'large' ? 48 : 40;
  const shouldShowText = showText !== undefined ? showText : !isMobile;
  
  // Determine what to show based on variant
  const showIcon = variant === 'full' || variant === 'icon-only';
  const showBrandName = (variant === 'full' || variant === 'text-only') && shouldShowText;
  
  const logoContent = (
    <Box 
      component="div"
      sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        cursor: interactive ? 'pointer' : 'default',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': interactive ? {
          transform: 'scale(1.02)',
        } : {},
      }}
    >
      {showIcon && (
      <Box
          className="logo-icon-container"
        sx={{
          width: iconSize,
          height: iconSize,
          borderRadius: '12px',
            background: inverted
              ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.1) 100%)'
              : isLight 
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
              : 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
            boxShadow: inverted
              ? 'inset 0 1px 3px rgba(255, 255, 255, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1)'
              : isLight 
              ? '0 2px 8px rgba(102, 126, 234, 0.25)' 
              : '0 4px 16px rgba(102, 126, 234, 0.4)',
          position: 'relative',
            overflow: 'visible',
            backdropFilter: inverted ? 'blur(8px)' : 'none',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '@media (max-width: 600px)': {
              borderRadius: '8px',
          },
        }}
      >
          {/* Port with lighthouse, chart bars, waves and ambient glow */}
        <svg
            width={iconSize * 0.75}
            height={iconSize * 0.75}
            viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ zIndex: 1, position: 'relative' }}
        >
            {/* Define gradients and filters */}
            <defs>
              <linearGradient id={`portGrad1-${inverted ? 'inv' : 'norm'}`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={inverted ? "#FFFFFF" : "#667eea"} stopOpacity={inverted ? "0.9" : "1"} />
                <stop offset="100%" stopColor={inverted ? "#FFFFFF" : "#764ba2"} stopOpacity={inverted ? "0.8" : "1"} />
              </linearGradient>
              <linearGradient id={`portGrad2-${inverted ? 'inv' : 'norm'}`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={inverted ? "#FFFFFF" : "#764ba2"} stopOpacity={inverted ? "0.85" : "1"} />
                <stop offset="100%" stopColor={inverted ? "#FFFFFF" : "#f093fb"} stopOpacity={inverted ? "0.75" : "1"} />
              </linearGradient>
              <linearGradient id={`portGrad3-${inverted ? 'inv' : 'norm'}`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={inverted ? "#FFFFFF" : "#f093fb"} stopOpacity={inverted ? "0.8" : "1"} />
                <stop offset="100%" stopColor={inverted ? "#C7D2FE" : "#4facfe"} stopOpacity={inverted ? "0.7" : "1"} />
              </linearGradient>
              <radialGradient id={`glowGrad-${inverted ? 'inv' : 'norm'}`} cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={inverted ? "#FFFFFF" : "#667eea"} stopOpacity={inverted ? "0.15" : "0.2"} />
                <stop offset="100%" stopColor={inverted ? "#FFFFFF" : "#f093fb"} stopOpacity="0" />
              </radialGradient>
              <filter id={`glow-${inverted ? 'inv' : 'norm'}`}>
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* Ambient glow ring - always pulsing */}
            <circle 
              cx="24" 
              cy="24" 
              r="21" 
              fill={`url(#glowGrad-${inverted ? 'inv' : 'norm'})`}
              className="ambient-glow"
              filter={`url(#glow-${inverted ? 'inv' : 'norm'})`}
              style={{
                animation: animated ? 'ambientGlow 4s ease-in-out infinite' : 'none',
                willChange: 'opacity',
                pointerEvents: 'none',
              }}
            />
            
            {/* Trend line above bars - animated drawing, synchronized with bars */}
            <path 
              d="M13 20 Q21 18 29 16 T37 12" 
              stroke={inverted ? "#FFFFFF" : "#667eea"}
              strokeWidth="2.5" 
              fill="none"
              strokeDasharray="30 30"
              strokeDashoffset="0"
              className="trend-line"
              style={{
                animation: animated ? 'drawLine 2.5s linear infinite' : 'none',
              }}
            />
            
            {/* Chart bars - growing trend (4 bars, bigger) */}
            <rect 
              x="10" 
              y="24" 
              width="6" 
              height="10" 
              fill={`url(#portGrad1-${inverted ? 'inv' : 'norm'})`}
              className="chart-bar-1"
              rx="2"
              style={{
                animation: animated ? 'chartPulse 2.5s ease-in-out infinite 0s' : 'none',
              }}
            />
            <rect 
              x="18" 
              y="20" 
              width="6" 
              height="14" 
              fill={`url(#portGrad2-${inverted ? 'inv' : 'norm'})`}
              className="chart-bar-2"
              rx="2"
              style={{
                animation: animated ? 'chartPulse 2.5s ease-in-out infinite 0.5s' : 'none',
              }}
            />
            <rect 
              x="26" 
              y="16" 
              width="6" 
              height="18" 
              fill={`url(#portGrad3-${inverted ? 'inv' : 'norm'})`}
              className="chart-bar-3"
              rx="2"
              style={{
                animation: animated ? 'chartPulse 2.5s ease-in-out infinite 1s' : 'none',
              }}
            />
            <rect 
              x="34" 
              y="12" 
              width="6" 
              height="22" 
              fill={`url(#portGrad1-${inverted ? 'inv' : 'norm'})`}
              className="chart-bar-4"
              rx="2"
              style={{
                animation: animated ? 'chartPulse 2.5s ease-in-out infinite 1.5s' : 'none',
              }}
            />
            
            {/* Base platform */}
            <rect 
              x="6" 
              y="36" 
              width="36" 
              height="8" 
              fill={`url(#portGrad1-${inverted ? 'inv' : 'norm'})`}
              opacity="0.8"
              rx="2"
            />
            
            {/* Waves - gentle motion */}
            <path 
              d="M6 40 Q12 38 18 40 T30 40 T42 40" 
              stroke={inverted ? "#FFFFFF" : "#f093fb"}
              strokeWidth="2"
              fill="none"
              className="wave-top"
              style={{
                animation: animated ? 'gentleWave 3s ease-in-out infinite 0s' : 'none',
                opacity: 0.8,
              }}
            />
            <path 
              d="M6 42 Q12 40 18 42 T30 42 T42 42" 
              stroke={inverted ? "#FFFFFF" : "#4facfe"}
              strokeWidth="2"
              fill="none"
              className="wave-bottom"
              style={{
                animation: animated ? 'gentleWave 3s ease-in-out infinite 1s' : 'none',
                opacity: 0.6,
              }}
            />
            
            {/* CSS Animations - styles only when needed */}
            {animated && (
              <style>{`
                .chart-bar-1,
                .chart-bar-2,
                .chart-bar-3,
                .chart-bar-4 {
                  transform-origin: bottom;
                }
                ${interactive ? `
                  .logo-icon-container:hover .ambient-glow {
                    opacity: 0.8;
                    animation-duration: 2s;
                  }
                  .logo-icon-container:hover .chart-bar-1,
                  .logo-icon-container:hover .chart-bar-2,
                  .logo-icon-container:hover .chart-bar-3,
                  .logo-icon-container:hover .chart-bar-4 {
                    animation-duration: 1.5s;
                  }
                  .logo-icon-container:hover .wave-top,
                  .logo-icon-container:hover .wave-bottom {
                    animation-duration: 2s;
                  }
                ` : ''}
              `}</style>
            )}
        </svg>
      </Box>
      )}
      
      {showBrandName && (
        <Typography
          variant="h6"
          component="span"
          sx={{
            fontWeight: 700,
            fontSize: size === 'small' ? '1rem' : size === 'large' ? '1.5rem' : '1.25rem',
            color: inverted ? 'white' : 'transparent',
            background: inverted
              ? 'none'
              : isLight
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
            backgroundClip: inverted ? 'initial' : 'text',
            WebkitBackgroundClip: inverted ? 'initial' : 'text',
            WebkitTextFillColor: inverted ? 'white' : 'transparent',
            letterSpacing: '-0.02em',
            fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            textShadow: inverted ? '0 1px 2px rgba(0, 0, 0, 0.1)' : 'none',
          }}
        >
          InsightPort
        </Typography>
      )}
    </Box>
  );

  // If logo is not interactive, don't show tooltip at all
  if (!interactive) {
    return logoContent;
  }

  // If interactive, wrap with tooltip
  return (
    <Tooltip title="Navigate to Dashboard" placement="bottom" arrow>
      {logoContent}
    </Tooltip>
  );
};

export default Logo;
