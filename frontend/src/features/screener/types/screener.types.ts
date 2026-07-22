export interface ScreenerSignal {
  id: string;
  symbol: string;
  market: string;
  scanner_name: string;
  timeframe: string;
  signal_type: string;
  price?: number;
  confidence_score?: number;
  details: Record<string, any>;
  triggered_at?: string;
  created_at: string;
}

export interface ScannerTemplate {
  id: string;
  name: string;
  description?: string;
  conditions: Record<string, any>;
  created_at: string;
  updated_at: string;
}
