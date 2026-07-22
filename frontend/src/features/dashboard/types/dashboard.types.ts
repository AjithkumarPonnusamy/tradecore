export interface DashboardMetrics {
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  wins: number;
  losses: number;
  avg_r: number;
  profit_factor: number;
  expectancy: number;
  max_drawdown: number;
  consecutive_wins: number;
  consecutive_losses: number;
  best_strategy?: string | null;
  best_timeframe?: string | null;
  best_session?: string | null;
  best_market?: string | null;
  charts: {
    equity_curve: Array<{ trade_number: number; date: string; equity: number; pnl: number }>;
    monthly_pnl: Record<string, number>;
    strategy_pnl: Record<string, number>;
    daywise_pnl: Record<string, number>;
    hourwise_pnl: Record<string, number>;
    r_distribution: Record<string, number>;
    psychology_pnl: Record<string, number>;
  };
  category_analytics: {
    market_segment: Record<string, any>;
    trading_style: Record<string, any>;
    direction: Record<string, any>;
    strategy: Record<string, any>;
  };
  db_connected: boolean;
  db_name: string;
  db_last_sync: string;
}

export interface WatchlistDbItem {
  id: string;
  symbol: string;
  market: string;
  position: number;
  settings: Record<string, any>;
}

export interface MarketSnapshotItem {
  symbol: string;
  market: string;
  live_price: number;
  change_pct: number;
  current_day_high: number;
  current_day_low: number;
  previous_day_close: number;
  cpr_levels: Record<string, any>;
  camarilla_levels: Record<string, any>;
  sparkline_points: string;
  status: "LIVE" | "DELAYED" | "OFFLINE";
}
