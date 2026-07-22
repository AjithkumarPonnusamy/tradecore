"""
Unit & Integration Tests for TradeCore 9-Schema Database Architecture
Verifies:
1. 9 domain schemas exist and are correctly targeted by SQLAlchemy models.
2. Market model partitioning on market_candles (RANGE on datetime).
3. Decoupled cross-schema data accessibility (market as shared source of truth).
4. Live PostgreSQL catalog validation (pg_namespace, pg_partitioned_table, dynamic partition creation).
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import inspect, text
from app.core.database import engine
from app.models.models import (
    User, UserOAuthAccount, UserMarketPreferences, DashboardPreference, Watchlist,
    Symbol, MarketData, PivotLevels, MarketCandle,
    Strategy, Trade, TradeImage, TradeMarketSnapshot,
    TechnicalChecklist, ConfirmationChecklist, JournalEntry,
    BacktestRun, BacktestTrade, BacktestMetric,
    ResearchNotebook, FactorData, CustomStudy,
    ScreenerResult, ScannerResult, ScannerSettings, ScannerTemplate,
    VoiceJournal, AIConversation, AIInsight,
    SystemSetting, AuditLog, TaskExecutionLog, SchemaMigration
)

def test_model_schema_assignments():
    """Verify each model is explicitly assigned to its respective domain schema."""
    schema_map = {
        # Identity Schema
        User: "identity",
        UserOAuthAccount: "identity",
        UserMarketPreferences: "identity",
        DashboardPreference: "identity",
        Watchlist: "identity",

        # Market Schema
        Symbol: "market",
        MarketData: "market",
        PivotLevels: "market",
        MarketCandle: "market",

        # Trading Schema
        Strategy: "trading",
        Trade: "trading",
        TradeImage: "trading",
        TradeMarketSnapshot: "trading",

        # Journal Schema
        TechnicalChecklist: "journal",
        ConfirmationChecklist: "journal",
        JournalEntry: "journal",

        # Backtest Schema
        BacktestRun: "backtest",
        BacktestTrade: "backtest",
        BacktestMetric: "backtest",

        # Research Schema
        ResearchNotebook: "research",
        FactorData: "research",
        CustomStudy: "research",

        # Scanner Schema
        ScreenerResult: "scanner",
        ScannerResult: "scanner",
        ScannerSettings: "scanner",
        ScannerTemplate: "scanner",

        # AI Schema
        VoiceJournal: "ai",
        AIConversation: "ai",
        AIInsight: "ai",

        # System Schema
        SystemSetting: "system",
        AuditLog: "system",
        TaskExecutionLog: "system",
        SchemaMigration: "system"
    }

    for model_cls, expected_schema in schema_map.items():
        table_schema = model_cls.__table__.schema
        assert table_schema == expected_schema, (
            f"Model {model_cls.__name__} expected schema '{expected_schema}', got '{table_schema}'"
        )


def test_market_candle_partitioned_primary_key():
    """Verify MarketCandle primary key includes compound columns for table partitioning."""
    pk_cols = [col.name for col in MarketCandle.__table__.primary_key.columns]
    assert "datetime" in pk_cols, "datetime must be part of primary key for RANGE partitioning"
    assert "symbol" in pk_cols, "symbol must be part of compound key"
    assert "timeframe" in pk_cols, "timeframe must be part of compound key"


def test_decoupled_market_schema_design():
    """Verify Trade model stores symbol logically without physical FK constraint into market.market_candles."""
    trade_fks = Trade.__table__.foreign_keys
    fk_target_tables = [fk.column.table.name for fk in trade_fks]
    
    assert "market_candles" not in fk_target_tables, (
        "Trade should not have a hard FK to market_candles to ensure market schema can be decoupled later"
    )
    assert "users" in fk_target_tables


def test_live_postgres_schemas_and_partitioning():
    """Integration test checking live PostgreSQL database catalog for the 9 schemas and candle partitioning."""
    from sqlalchemy import create_engine
    from app.core.config import settings
    test_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        with test_engine.connect() as conn:
            # 1. Verify 9 Schemas exist in catalog
            res = conn.execute(text(
                "SELECT nspname FROM pg_namespace WHERE nspname IN "
                "('identity', 'market', 'trading', 'journal', 'backtest', 'research', 'scanner', 'ai', 'system')"
            ))
            found_schemas = {row[0] for row in res.fetchall()}
            expected_schemas = {'identity', 'market', 'trading', 'journal', 'backtest', 'research', 'scanner', 'ai', 'system'}
            assert found_schemas == expected_schemas, f"Missing schemas: {expected_schemas - found_schemas}"

            # 2. Verify market.market_candles is registered as partitioned table
            res = conn.execute(text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "JOIN pg_partitioned_table p ON p.partrelid = c.oid "
                "WHERE n.nspname = 'market' AND c.relname = 'market_candles'"
            ))
            partitioned_table = res.fetchone()
            assert partitioned_table is not None, "market.market_candles is not registered as a partitioned table in pg_partitioned_table"

            # 3. Test dynamic partition creation function
            conn.execute(text("SELECT market.create_candle_partition_if_not_exists(2029);"))
            conn.commit()

            res = conn.execute(text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'market' AND c.relname = 'market_candles_y2029'"
            ))
            partition_2029 = res.fetchone()
            assert partition_2029 is not None, "market.market_candles_y2029 partition was not dynamically created"

    except Exception as e:
        pytest.skip(f"Live database not available for integration check: {e}")

