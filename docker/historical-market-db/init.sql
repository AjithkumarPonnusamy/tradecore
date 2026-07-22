-- Historical Market Database Initialization Script
-- Targets PostgreSQL 16 with TimescaleDB

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create dedicated schema
CREATE SCHEMA IF NOT EXISTS market_data;

-- Set search path to ensure schema-local resolution
SET search_path TO market_data, public;

--------------------------------------------------------------------------------
-- 1. Table: symbols
--------------------------------------------------------------------------------
CREATE TABLE market_data.symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(50) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    instrument_token VARCHAR(100),
    tick_size NUMERIC(12, 6),
    lot_size INTEGER,
    currency VARCHAR(10),
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_exchange_symbol_segment UNIQUE (exchange, symbol, segment)
);

COMMENT ON TABLE market_data.symbols IS 'Master table storing all security listings, tickers, and tokens across exchanges.';
COMMENT ON COLUMN market_data.symbols.id IS 'Unique identifier (UUID) for the symbol.';
COMMENT ON COLUMN market_data.symbols.exchange IS 'Trading exchange identifier (e.g., NYSE, NASDAQ, NSE, BSE, BINANCE, CME).';
COMMENT ON COLUMN market_data.symbols.segment IS 'Asset segment/class (e.g., EQUITY, FUTURES, OPTIONS, FOREX, CRYPTO, COMMODITIES, INDICES).';
COMMENT ON COLUMN market_data.symbols.symbol IS 'The market ticker or symbol name (e.g., AAPL, BTCUSDT, INFY).';
COMMENT ON COLUMN market_data.symbols.instrument_token IS 'Broker or provider-specific numeric/alphanumeric identifier.';
COMMENT ON COLUMN market_data.symbols.tick_size IS 'Minimum price movement/increment size (e.g., 0.05).';
COMMENT ON COLUMN market_data.symbols.lot_size IS 'Standard transaction unit or multiplier (e.g., 1, 50, 75).';
COMMENT ON COLUMN market_data.symbols.currency IS 'Denomination currency of the symbol (e.g., USD, INR, EUR).';
COMMENT ON COLUMN market_data.symbols.timezone IS 'Home exchange timezone (e.g., America/New_York, Asia/Kolkata).';
COMMENT ON COLUMN market_data.symbols.active IS 'Indicates if the symbol is actively trading or tracked.';

--------------------------------------------------------------------------------
-- 2. Table: candles (Hypertable)
--------------------------------------------------------------------------------
CREATE TABLE market_data.candles (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES market_data.symbols(id) ON DELETE CASCADE,
    timeframe VARCHAR(5) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(20, 10) NOT NULL,
    high NUMERIC(20, 10) NOT NULL,
    low NUMERIC(20, 10) NOT NULL,
    close NUMERIC(20, 10) NOT NULL,
    volume NUMERIC(24, 10) NOT NULL DEFAULT 0,
    open_interest NUMERIC(24, 10) DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol_id, timeframe, timestamp),
    CONSTRAINT chk_timeframe CHECK (timeframe IN ('1m', '3m', '5m', '10m', '15m', '30m', '45m', '1h', '2h', '4h', '1d', '1w', '1M'))
);

COMMENT ON TABLE market_data.candles IS 'OHLCV data stored as a TimescaleDB hypertable for high-performance time-series queries.';
COMMENT ON COLUMN market_data.candles.id IS 'Internal unique tracker identifier.';
COMMENT ON COLUMN market_data.candles.symbol_id IS 'Foreign key referencing the symbols table.';
COMMENT ON COLUMN market_data.candles.timeframe IS 'Candle duration (e.g., 1m, 5m, 1h, 1d).';
COMMENT ON COLUMN market_data.candles.timestamp IS 'The beginning timestamp of the candle period.';
COMMENT ON COLUMN market_data.candles.open IS 'Opening price of the asset during this candle interval.';
COMMENT ON COLUMN market_data.candles.high IS 'Highest price reached during the interval.';
COMMENT ON COLUMN market_data.candles.low IS 'Lowest price reached during the interval.';
COMMENT ON COLUMN market_data.candles.close IS 'Closing price of the asset during this candle interval.';
COMMENT ON COLUMN market_data.candles.volume IS 'Volume traded during the interval.';
COMMENT ON COLUMN market_data.candles.open_interest IS 'Outstanding derivative contracts (applicable for futures/options).';

--------------------------------------------------------------------------------
-- 3. Convert candles into hypertable
--------------------------------------------------------------------------------
-- Converts candles table to a hypertable partitioned by the timestamp column.
-- Uses standard 7-day chunk intervals which is ideal for high frequency minute-level data.
SELECT create_hypertable('market_data.candles', 'timestamp', chunk_time_interval => INTERVAL '7 days');

-- Create an index optimized for symbol query patterns, ordered by timestamp descending for historical analysis
CREATE INDEX idx_candles_query ON market_data.candles (symbol_id, timeframe, timestamp DESC);

--------------------------------------------------------------------------------
-- 4. Table: corporate_actions
--------------------------------------------------------------------------------
CREATE TABLE market_data.corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES market_data.symbols(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    ex_date DATE NOT NULL,
    record_date DATE,
    payment_date DATE,
    ratio_announced_denominator NUMERIC(20, 10),
    ratio_announced_numerator NUMERIC(20, 10),
    amount NUMERIC(20, 10),
    currency VARCHAR(10),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_corporate_action UNIQUE (symbol_id, action_type, ex_date),
    CONSTRAINT chk_action_type CHECK (action_type IN ('DIVIDEND', 'SPLIT', 'BONUS', 'RIGHTS', 'SPINOFF', 'MERGER'))
);

COMMENT ON TABLE market_data.corporate_actions IS 'Tracks stock splits, dividends, rights, and mergers to support price adjustment calculations.';
COMMENT ON COLUMN market_data.corporate_actions.action_type IS 'Type of corporate action (e.g. DIVIDEND, SPLIT, BONUS).';
COMMENT ON COLUMN market_data.corporate_actions.ex_date IS 'The ex-distribution date.';
COMMENT ON COLUMN market_data.corporate_actions.ratio_announced_denominator IS 'Denominator for splits/bonus issues (e.g. 1 in 2-for-1 split).';
COMMENT ON COLUMN market_data.corporate_actions.ratio_announced_numerator IS 'Numerator for splits/bonus issues (e.g. 2 in 2-for-1 split).';
COMMENT ON COLUMN market_data.corporate_actions.amount IS 'Cash dividend amount per share (if applicable).';

--------------------------------------------------------------------------------
-- 5. Table: trading_sessions
--------------------------------------------------------------------------------
CREATE TABLE market_data.trading_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID REFERENCES market_data.symbols(id) ON DELETE CASCADE,
    exchange VARCHAR(50),
    session_name VARCHAR(50) NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_session_target CHECK (
        (symbol_id IS NOT NULL AND exchange IS NULL) OR 
        (symbol_id IS NULL AND exchange IS NOT NULL)
    ),
    CONSTRAINT chk_times CHECK (start_time < end_time),
    CONSTRAINT uq_trading_session_symbol UNIQUE (symbol_id, session_name, day_of_week),
    CONSTRAINT uq_trading_session_exchange UNIQUE (exchange, session_name, day_of_week)
);

COMMENT ON TABLE market_data.trading_sessions IS 'Stores regular and pre/post-market trading session times mapped by weekday (1=Monday, 7=Sunday).';
COMMENT ON COLUMN market_data.trading_sessions.session_name IS 'Name of the trading session (e.g. PRE_MARKET, REGULAR, POST_MARKET).';
COMMENT ON COLUMN market_data.trading_sessions.day_of_week IS 'Day index: 1 (Monday) to 7 (Sunday).';

--------------------------------------------------------------------------------
-- 6. Table: holidays
--------------------------------------------------------------------------------
CREATE TABLE market_data.holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(50),
    holiday_date DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_half_day BOOLEAN NOT NULL DEFAULT FALSE,
    close_time TIME,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_exchange_holiday UNIQUE (exchange, holiday_date)
);

COMMENT ON TABLE market_data.holidays IS 'Tracks dates when exchanges are closed or operate under reduced hours.';
COMMENT ON COLUMN market_data.holidays.exchange IS 'Exchange identifier. If NULL, holiday applies globally to all exchanges.';

--------------------------------------------------------------------------------
-- 7. Table: metadata
--------------------------------------------------------------------------------
CREATE TABLE market_data.metadata (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE market_data.metadata IS 'Flexible key-value registry for ingestion states, offsets, schema versioning, or vendor synchronization.';
