import { TimeRange } from '../../theme/dashboardTokens';
import { AssetSource } from '../../services/portfolioService';

export interface KPIItem {
  id: string;
  label: string;
  value: string;
  secondary?: string;
  delta?: number;
  deltaLabel?: string;
  trend?: number[];
}

export interface SummaryModule {
  id: string;
  title: string;
  value: string;
  changePercent: number;
  changeLabel: string;
  trend: number[];
  accent: 'stocks' | 'crypto';
}

export interface AllocationSlice {
  label: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

export interface AllocationBreakdownData {
  all: AllocationSlice[];
  byAssetClass: AllocationSlice[];
}

export interface BenchmarkOption {
  id: string;
  label: string;
  color: string;
  active: boolean;
}

export interface EquityCurvePoint {
  date: string;
  value: number;
  stocks?: number;
  crypto?: number;
  benchmarkValues?: Record<string, number>;
}

export interface EquityComparisonSummary {
  label: string;
  currentValue: number;
  previousValue: number;
  deltaValue: number;
  deltaPercent: number;
  formattedDeltaValue: string;
  formattedDeltaPercent: string;
}

export interface EquityCurveConfig {
  points: EquityCurvePoint[];
  benchmarks: BenchmarkOption[];
  filter: 'total' | 'stocks' | 'crypto';
  previousPoints?: EquityCurvePoint[];
  comparison?: EquityComparisonSummary | null;
}

export interface HeatmapCell {
  id: string;
  label: string;
  value: number;
  trend: number[];
  riskScore?: number;
  volatility?: number;
  allocation?: number;
  type?: string;
}

export interface HoldingRow {
  symbol: string;
  exchange: string;
  position: string;
  avgPrice: string;
  currentPrice: string;
  value: string;
  plPercent: number;
  plValue: string;
  plValueRaw: number;
  roi: number;
  lastUpdated: string;
  sources?: AssetSource[];
  sourceCount?: number;
  exchangeList?: string[];
}

export interface TrendBar {
  label: string;
  roi: number;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  timestamp: string;
  url?: string;
  summary?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  symbol?: string;
}

export interface AssetTabData {
  heatmap: HeatmapCell[];
  holdings: HoldingRow[];
  trends: TrendBar[];
  news?: NewsItem[];
}

export interface WatchItem {
  id: string;
  label: string;
  symbol: string;
  price: string;
  change24h: number;
  volume: string;
  alertActive: boolean;
}

export interface RecentAlert {
  id: string;
  message: string;
  status: 'new' | 'acknowledged' | 'resolved';
  timestamp: string;
}

export interface RoiContribution {
  asset: string;
  contribution: number;
  color: string;
}

export interface TopMover {
  asset: string;
  value: string;
  percent: number;
  direction: 'up' | 'down';
}

export interface ForecastInsight {
  symbol: string;
  horizon: string;
  expectedReturn: number;
  confidence: number;
  narrative: string;
}

export interface DrilldownMetrics {
  beta: number;
  volatility: number;
  sharpe: number;
}

export interface DrilldownPoint {
  date: string;
  value: number;
}

export interface DrilldownData {
  symbol: string;
  roiTimeline: DrilldownPoint[];
  candlestick?: Array<{ time: string; open: number; high: number; low: number; close: number }>;
  metrics: DrilldownMetrics;
}

export interface RoiAnalyticsData {
  globalPL: number;
  contributions: RoiContribution[];
  topGainers: TopMover[];
  topLosers: TopMover[];
  drilldownOptions: string[];
  selectedDrilldown: string;
  drilldown: DrilldownData;
  forecast?: ForecastInsight[];
  notice?: string;
  sampleCount?: number;
}

export interface FiltersState {
  assetType: string[];
  sector: string[];
  region: string[];
  tags: string[];
  stablecoinsOnly: boolean;
  viewMode: 'table' | 'cards' | 'chart';
  timeRange: TimeRange;
}


