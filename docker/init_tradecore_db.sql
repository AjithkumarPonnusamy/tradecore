-- PostgreSQL Initialization Script for TradeCore Database
-- Organized into 9 domain schemas with RANGE table partitioning for market.market_candles
-- Enables future decoupling of the 'market' schema without relational/schema redesign

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

--------------------------------------------------------------------------------
-- 1. Create Domain Schemas
--------------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS market;
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS journal;
CREATE SCHEMA IF NOT EXISTS backtest;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS scanner;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS system;

SET search_path TO identity, market, trading, journal, backtest, research, scanner, ai, system, public;

--------------------------------------------------------------------------------
-- 2. IDENTITY SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS identity.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'EMAIL',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON identity.users(email);

CREATE TABLE IF NOT EXISTS identity.user_oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    provider_user_id VARCHAR(255),
    provider_email VARCHAR(255),
    provider_name VARCHAR(255),
    provider_avatar TEXT,
    client_id TEXT,
    client_secret TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMPTZ,
    drive_folder_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_oauth_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_oauth_user_id ON identity.user_oauth_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_provider ON identity.user_oauth_accounts(provider);

CREATE TABLE IF NOT EXISTS identity.user_market_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    favorite_symbols JSONB NOT NULL DEFAULT '[]'::jsonb,
    visible_reference_levels JSONB NOT NULL DEFAULT '{}'::jsonb,
    dashboard_layout JSONB NOT NULL DEFAULT '{}'::jsonb,
    broker_credentials JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS identity.dashboard_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    selected_symbols JSONB NOT NULL DEFAULT '[]'::jsonb,
    widget_visibility JSONB NOT NULL DEFAULT '{}'::jsonb,
    widget_order JSONB NOT NULL DEFAULT '[]'::jsonb,
    layout_name VARCHAR(100) NOT NULL DEFAULT 'default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dash_pref_user_layout UNIQUE (user_id, layout_name)
);

--------------------------------------------------------------------------------
-- 3. MARKET SCHEMA (Shared Source of Truth - Partitioned Time Series)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market.symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(50) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    instrument_token VARCHAR(100),
    tick_size NUMERIC(12, 6),
    lot_size INTEGER,
    currency VARCHAR(10) DEFAULT 'INR',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_market_exchange_symbol_segment UNIQUE (exchange, symbol, segment)
);

CREATE INDEX IF NOT EXISTS idx_symbols_lookup ON market.symbols(symbol, exchange);

CREATE TABLE IF NOT EXISTS market.market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    live_price NUMERIC(18, 8),
    trueday_open NUMERIC(18, 8),
    previous_trueday_open NUMERIC(18, 8),
    indian_midnight_open NUMERIC(18, 8),
    previous_day_high NUMERIC(18, 8),
    previous_day_low NUMERIC(18, 8),
    previous_day_close NUMERIC(18, 8),
    current_day_high NUMERIC(18, 8),
    current_day_low NUMERIC(18, 8),
    daily_range NUMERIC(18, 8),
    cpr_levels JSONB NOT NULL DEFAULT '{}'::jsonb,
    camarilla_levels JSONB NOT NULL DEFAULT '{}'::jsonb,
    timezone_info VARCHAR(50),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_market_data_sym_mkt UNIQUE (symbol, market)
);

-- Partitioned Historical Candle Data (PARTITION BY RANGE on datetime)
CREATE TABLE IF NOT EXISTS market.market_candles (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    open NUMERIC(18, 8) NOT NULL,
    high NUMERIC(18, 8) NOT NULL,
    low NUMERIC(18, 8) NOT NULL,
    close NUMERIC(18, 8) NOT NULL,
    volume NUMERIC(18, 8) DEFAULT 0,
    source VARCHAR(50) NOT NULL DEFAULT 'public_feed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, datetime)
) PARTITION BY RANGE (datetime);

-- Declarative Partition Definitions for Market Candles
CREATE TABLE IF NOT EXISTS market.market_candles_y2022 PARTITION OF market.market_candles
    FOR VALUES FROM ('2022-01-01 00:00:00+00') TO ('2023-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2023 PARTITION OF market.market_candles
    FOR VALUES FROM ('2023-01-01 00:00:00+00') TO ('2024-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2024 PARTITION OF market.market_candles
    FOR VALUES FROM ('2024-01-01 00:00:00+00') TO ('2025-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2025 PARTITION OF market.market_candles
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2026 PARTITION OF market.market_candles
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2027 PARTITION OF market.market_candles
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2028-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_y2028 PARTITION OF market.market_candles
    FOR VALUES FROM ('2028-01-01 00:00:00+00') TO ('2029-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS market.market_candles_default PARTITION OF market.market_candles DEFAULT;

-- Partition Indexing
CREATE INDEX IF NOT EXISTS idx_candles_lookup ON market.market_candles (symbol, timeframe, datetime DESC);

-- Dynamic PL/pgSQL Function to Automatically Provision Annual Candle Partitions
CREATE OR REPLACE FUNCTION market.create_candle_partition_if_not_exists(target_year INT)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_name := 'market_candles_y' || target_year;
    start_date := target_year || '-01-01 00:00:00+00';
    end_date := (target_year + 1) || '-01-01 00:00:00+00';

    IF NOT EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'market' AND c.relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE market.%I PARTITION OF market.market_candles FOR VALUES FROM (%L) TO (%L);',
            partition_name, start_date, end_date
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS market.pivot_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    cpr_pivot NUMERIC(18, 8) NOT NULL,
    cpr_tc NUMERIC(18, 8) NOT NULL,
    cpr_bc NUMERIC(18, 8) NOT NULL,
    camarilla_r1 NUMERIC(18, 8) NOT NULL,
    camarilla_r2 NUMERIC(18, 8) NOT NULL,
    camarilla_r3 NUMERIC(18, 8) NOT NULL,
    camarilla_r4 NUMERIC(18, 8) NOT NULL,
    camarilla_s1 NUMERIC(18, 8) NOT NULL,
    camarilla_s2 NUMERIC(18, 8) NOT NULL,
    camarilla_s3 NUMERIC(18, 8) NOT NULL,
    camarilla_s4 NUMERIC(18, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pivot_levels_sym_mkt_date UNIQUE (symbol, market, date)
);

CREATE TABLE IF NOT EXISTS market.corporate_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    ex_date DATE NOT NULL,
    record_date DATE,
    payment_date DATE,
    ratio_denominator NUMERIC(20, 10),
    ratio_numerator NUMERIC(20, 10),
    amount NUMERIC(20, 10),
    currency VARCHAR(10),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_corp_action UNIQUE (symbol, action_type, ex_date)
);

CREATE TABLE IF NOT EXISTS market.trading_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(50) NOT NULL,
    session_name VARCHAR(50) NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_trading_session UNIQUE (exchange, session_name, day_of_week)
);

CREATE TABLE IF NOT EXISTS market.holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(50),
    holiday_date DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_half_day BOOLEAN NOT NULL DEFAULT FALSE,
    close_time TIME,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_exchange_holiday UNIQUE (exchange, holiday_date)
);

CREATE TABLE IF NOT EXISTS market.metadata (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 4. TRADING SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trading.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES trading.strategies(id) ON DELETE SET NULL,
    trade_date DATE NOT NULL DEFAULT CURRENT_DATE,
    trade_time TIME,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    trading_type VARCHAR(50),
    segment VARCHAR(50),
    entry_price NUMERIC(18, 8) NOT NULL,
    stop_loss NUMERIC(18, 8),
    target_price NUMERIC(18, 8),
    exit_price NUMERIC(18, 8),
    quantity NUMERIC(18, 8) NOT NULL DEFAULT 1.0,
    net_profit NUMERIC(18, 2),
    r_multiple NUMERIC(8, 2),
    holding_minutes INTEGER,
    confidence_rating INTEGER,
    setup JSONB NOT NULL DEFAULT '{}'::jsonb,
    psychology JSONB NOT NULL DEFAULT '{}'::jsonb,
    notes JSONB NOT NULL DEFAULT '{}'::jsonb,
    analytics JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trading.trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_sym_mkt ON trading.trades(symbol, market);
CREATE INDEX IF NOT EXISTS idx_trades_setup ON trading.trades USING GIN (setup);
CREATE INDEX IF NOT EXISTS idx_trades_psychology ON trading.trades USING GIN (psychology);
CREATE INDEX IF NOT EXISTS idx_trades_analytics ON trading.trades USING GIN (analytics);
CREATE INDEX IF NOT EXISTS idx_trades_tags ON trading.trades USING GIN (tags);

CREATE TABLE IF NOT EXISTS trading.trade_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL REFERENCES trading.trades(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    google_file_id VARCHAR(255),
    file_url TEXT,
    caption TEXT,
    extra_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.trade_market_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID UNIQUE NOT NULL REFERENCES trading.trades(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    live_price NUMERIC(18, 8),
    trueday_open NUMERIC(18, 8),
    previous_trueday_open NUMERIC(18, 8),
    indian_midnight_open NUMERIC(18, 8),
    previous_day_high NUMERIC(18, 8),
    previous_day_low NUMERIC(18, 8),
    previous_day_close NUMERIC(18, 8),
    current_day_high NUMERIC(18, 8),
    current_day_low NUMERIC(18, 8),
    daily_range NUMERIC(18, 8),
    cpr_levels JSONB NOT NULL DEFAULT '{}'::jsonb,
    camarilla_levels JSONB NOT NULL DEFAULT '{}'::jsonb,
    snapshot_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 5. JOURNAL SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal.journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    title VARCHAR(255),
    content TEXT,
    mood_score INTEGER,
    lessons_learned TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal.technical_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    order_idx INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal.confirmation_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    order_idx INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal.journal_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    color_code VARCHAR(20) DEFAULT '#3B82F6',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_journal_tag_user UNIQUE (user_id, tag_name)
);

--------------------------------------------------------------------------------
-- 6. BACKTEST SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest.backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES trading.strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital NUMERIC(18, 2) NOT NULL DEFAULT 100000.00,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backtest.backtest_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID NOT NULL REFERENCES backtest.backtest_runs(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    direction VARCHAR(20) NOT NULL,
    entry_price NUMERIC(18, 8) NOT NULL,
    exit_price NUMERIC(18, 8),
    quantity NUMERIC(18, 8) NOT NULL,
    pnl NUMERIC(18, 2),
    r_multiple NUMERIC(8, 2)
);

CREATE TABLE IF NOT EXISTS backtest.backtest_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID UNIQUE NOT NULL REFERENCES backtest.backtest_runs(id) ON DELETE CASCADE,
    total_trades INTEGER NOT NULL DEFAULT 0,
    win_rate NUMERIC(5, 2),
    profit_factor NUMERIC(8, 2),
    sharpe_ratio NUMERIC(8, 2),
    max_drawdown NUMERIC(8, 2),
    equity_curve JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 7. RESEARCH SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research.research_notebooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    notebook_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research.factor_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    factor_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    factor_value NUMERIC(18, 8) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_factor_sym_name_date UNIQUE (symbol, factor_name, date)
);

CREATE TABLE IF NOT EXISTS research.custom_studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    study_name VARCHAR(255) NOT NULL,
    code_content TEXT NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 8. SCANNER SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scanner.screener_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    pattern VARCHAR(100) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    entry_price NUMERIC(18, 8),
    stop_loss NUMERIC(18, 8),
    target_price NUMERIC(18, 8),
    confidence_score NUMERIC(5, 2),
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scanner.scanner_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    scanner_name VARCHAR(100) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    price NUMERIC(18, 8),
    confidence_score NUMERIC(5, 2),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    triggered_at TIMESTAMPTZ,
    telegram_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scanner_res_sym_mkt ON scanner.scanner_results(symbol, market);
CREATE INDEX IF NOT EXISTS idx_scanner_res_trig ON scanner.scanner_results(triggered_at);

CREATE TABLE IF NOT EXISTS scanner.scanner_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    enabled_scanners JSONB NOT NULL DEFAULT '{}'::jsonb,
    telegram_bot_token VARCHAR(255),
    telegram_chat_id VARCHAR(255),
    telegram_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    telegram_alert_types JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scanner.scanner_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 9. AI SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai.voice_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    trade_id UUID REFERENCES trading.trades(id) ON DELETE SET NULL,
    audio_url TEXT NOT NULL,
    transcript TEXT,
    original_transcript TEXT,
    corrected_transcript TEXT,
    ai_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    emotion_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'PROCESSING',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_journals_user ON ai.voice_journals(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_journals_trade ON ai.voice_journals(trade_id);

CREATE TABLE IF NOT EXISTS ai.ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai.ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 10. SYSTEM SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system.system_settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    ip_address VARCHAR(45),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system.task_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system.schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Record Initial Migration Version
INSERT INTO system.schema_migrations (version, description)
VALUES ('1.0.0_multischema_partitioning', 'Initial 9-schema layout with historical market candle partitioning')
ON CONFLICT (version) DO NOTHING;
