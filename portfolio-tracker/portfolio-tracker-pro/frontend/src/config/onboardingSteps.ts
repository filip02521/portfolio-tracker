export interface OnboardingStep {
  id: string;
  target: string; // CSS selector or data attribute
  title: string;
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const dashboardOnboardingSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    target: '[aria-label="Dashboard main content"]',
    title: 'Welcome to Portfolio Tracker Pro!',
    content: 'This is your main dashboard where you can see all your portfolio information at a glance. Let\'s take a quick tour of the key features.',
    placement: 'center',
  },
  {
    id: 'status-bar',
    target: '[aria-label*="Global Portfolio"]',
    title: 'Portfolio Status Bar',
    content: 'Here you can see your total portfolio value, daily P/L, and key metrics. Use the refresh button to update data manually, or sync trades from connected exchanges.',
    placement: 'bottom',
  },
  {
    id: 'quick-insights',
    target: '[aria-label="Quick insights"]',
    title: 'Quick Insights',
    content: 'These cards show important metrics at a glance: daily cashflow, top performers, and any data warnings. Click on interactive cards to see more details.',
    placement: 'bottom',
  },
  {
    id: 'portfolio-overview',
    target: '[aria-label*="Portfolio Overview"]',
    title: 'Portfolio Overview',
    content: 'View your portfolio allocation, equity curve, and performance over time. You can filter by asset class (stocks/crypto) and compare with benchmarks like S&P 500 or BTC.',
    placement: 'bottom',
  },
  {
    id: 'asset-details',
    target: '[aria-label="Asset Details"]',
    title: 'Asset Details',
    content: 'Detailed breakdown of all your holdings with performance metrics, trends, and market news. Switch between Stocks and Crypto tabs to view different asset classes.',
    placement: 'bottom',
  },
  {
    id: 'roi-analytics',
    target: '[aria-label="ROI Analytics"]',
    title: 'ROI Analytics',
    content: 'Comprehensive return on investment analysis showing how each asset contributes to your total portfolio return. Use the drill-down feature to explore individual asset performance.',
    placement: 'bottom',
  },
  {
    id: 'filters',
    target: '[aria-label="Dashboard controls and filters"]',
    title: 'Dashboard Filters',
    content: 'Use filters to focus on specific parts of your portfolio. Filter by time range, asset type, sector, region, or view mode (table/cards/chart).',
    placement: 'left',
  },
  {
    id: 'keyboard-shortcuts',
    target: 'body',
    title: 'Keyboard Shortcuts',
    content: 'Press "?" to see all available keyboard shortcuts. Use "r" to refresh, "g" to go to Goals, and "Cmd/Ctrl+K" or "/" to open the command palette for quick navigation.',
    placement: 'center',
    action: {
      label: 'View Shortcuts',
      onClick: () => {
        // This will be handled by the OnboardingTour component
        window.dispatchEvent(new CustomEvent('onboarding:show-shortcuts'));
      },
    },
  },
];

