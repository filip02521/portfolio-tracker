export const dashboardPalette = {
  dark: {
    background: '#0F172A',
    surface: '#1E293B',
    elevated: '#1E293B',
    border: 'rgba(148, 163, 184, 0.16)',
    textPrimary: '#E2E8F0',
    textSecondary: '#94A3B8',
  },
  light: {
    background: '#F8FAFC',
    surface: '#FFFFFF',
    elevated: '#FFFFFF',
    border: 'rgba(15, 23, 42, 0.08)',
    textPrimary: '#111827',
    textSecondary: '#475569',
  },
  primary: '#2563EB',
  accent: {
    positive: '#22C55E',
    negative: '#EF4444',
    warning: '#F59E0B',
  },
  cryptoAccent: '#7C3AED',
  stocksAccent: '#2563EB',
};

export const dashboardGradients = {
  positive: 'linear-gradient(135deg, rgba(37, 99, 235, 0.56) 0%, rgba(37, 99, 235, 0.12) 100%)',
  negative: 'linear-gradient(135deg, rgba(239, 68, 68, 0.56) 0%, rgba(239, 68, 68, 0.12) 100%)',
  neutral: 'linear-gradient(135deg, rgba(15, 23, 42, 0.4) 0%, rgba(15, 23, 42, 0.1) 100%)',
};

export const dashboardLayout = {
  sectionGap: { xs: 3, md: 4 },
  cardRadius: 20,
  chipRadius: 16,
  headerHeight: { xs: 72, md: 88 },
  maxContentWidth: 1480,
};

export const timeRangeOptions = ['24h', '7d', 'MTD', 'YTD', 'Max'] as const;

export type TimeRange = (typeof timeRangeOptions)[number];


