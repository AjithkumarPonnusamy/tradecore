export interface TradeItem {
  id: string;
  user_id: string;
  trade_date: string;
  trade_time?: string;
  market: string;
  symbol: string;
  direction: string;
  status: string;
  trading_type?: string;
  segment?: string;
  entry_price: number;
  stop_loss?: number;
  target_price?: number;
  exit_price?: number;
  quantity: number;
  net_profit?: number;
  r_multiple?: number;
  holding_minutes?: number;
  confidence_rating?: number;
  setup: Record<string, any>;
  psychology: Record<string, any>;
  notes: Record<string, any>;
  analytics: Record<string, any>;
  metadata?: Record<string, any>;
  tags: string[];
  strategy_id?: string;
  created_at: string;
  updated_at: string;
}

export interface TechnicalChecklist {
  id: string;
  name: string;
  is_enabled: boolean;
  order_idx: number;
}

export interface ConfirmationChecklist {
  id: string;
  name: string;
  is_enabled: boolean;
  order_idx: number;
}
