export interface EquityPoint {
  time: string;
  value: number;
}

export interface TradeMark {
  time: string;
  type: string;
  price: number;
}

export interface DrawdownPeriod {
  maxDrawdown: number;
  start: string;
  end: string;
  peakValue: number;
  troughValue: number;
}

export interface PeriodMetrics {
  ic: number;
  rankIc: number;
  sharpe: number;
  winRate: number;
  meanReturn: number;
  nObservations: number;
}

export interface BacktestResult {
  totalObservations: number;
  signalCount: number;
  longCount: number;
  shortCount: number;
  neutralCount: number;
  scoreMin: number;
  scoreMax: number;
  scoreMean: number;
  maxDrawdown: number | null;
  annualReturn: number | null;
  annualVolatility: number | null;
  period5d: PeriodMetrics;
  period10d: PeriodMetrics;
  period20d: PeriodMetrics;
  equityCurve: EquityPoint[];
  benchmarkCurve: EquityPoint[];
  trades: TradeMark[];
  drawdownPeriods: DrawdownPeriod[];
}
