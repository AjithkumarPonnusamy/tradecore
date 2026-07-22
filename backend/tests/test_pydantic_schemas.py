"""
Unit Tests for TradeCore Pydantic Schemas across 9 Domain Schemas
"""

import pytest
from datetime import datetime, date
from uuid import uuid4
from app.schemas.schemas import (
    UserResponse, UserOAuthAccountResponse,
    SymbolResponse, MarketDataResponse, MarketCandleResponse,
    TradeResponse, StrategyResponse,
    JournalEntryResponse, TechnicalChecklistResponse,
    BacktestRunResponse, BacktestMetricResponse,
    ResearchNotebookResponse, FactorDataResponse,
    ScannerResultBaseResponse, ScannerSettingsResponse,
    VoiceJournalResponse, AIInsightResponse,
    SystemSettingResponse, AuditLogResponse
)

def test_pydantic_schemas_instantiation():
    user_id = uuid4()
    
    # 1. Identity Schema
    user_resp = UserResponse(
        id=user_id,
        email="trader@tradecore.io",
        full_name="Alpha Trader",
        is_active=True,
        auth_provider="GOOGLE",
        created_at=datetime.now()
    )
    assert user_resp.email == "trader@tradecore.io"

    # 2. Market Schema
    candle_resp = MarketCandleResponse(
        symbol="NIFTY",
        timeframe="5m",
        datetime=datetime.now(),
        open=22000.0,
        high=22050.0,
        low=21980.0,
        close=22040.0,
        volume=1500.0
    )
    assert candle_resp.close == 22040.0

    # 3. Trading Schema
    trade_id = uuid4()
    trade_resp = TradeResponse(
        id=trade_id,
        user_id=user_id,
        trade_date=date.today(),
        market="Indian Equity",
        symbol="RELIANCE",
        direction="BUY",
        entry_price=2500.0,
        quantity=10.0,
        r_multiple=2.5,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert trade_resp.r_multiple == 2.5

    # 4. Journal Schema
    journal_resp = JournalEntryResponse(
        id=uuid4(),
        user_id=user_id,
        entry_date=date.today(),
        title="Weekly Recap",
        content="Followed CPR breakout rules flawlessly.",
        mood_score=9,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert journal_resp.mood_score == 9

    # 5. Backtest Schema
    backtest_resp = BacktestRunResponse(
        id=uuid4(),
        user_id=user_id,
        symbol="NIFTY",
        timeframe="15m",
        start_date=datetime.now(),
        end_date=datetime.now(),
        status="COMPLETED",
        created_at=datetime.now()
    )
    assert backtest_resp.status == "COMPLETED"

    # 6. Research Schema
    factor_resp = FactorDataResponse(
        id=uuid4(),
        symbol="BANKNIFTY",
        factor_name="momentum_rsi_14",
        date=date.today(),
        factor_value=64.5,
        created_at=datetime.now()
    )
    assert factor_resp.factor_value == 64.5

    # 7. Scanner Schema
    scanner_resp = ScannerResultBaseResponse(
        id=uuid4(),
        symbol="INFY",
        market="Indian Equity",
        scanner_name="cpr_narrow",
        timeframe="1d",
        signal_type="BULLISH_BREAKOUT",
        price=1520.0,
        created_at=datetime.now()
    )
    assert scanner_resp.signal_type == "BULLISH_BREAKOUT"

    # 8. AI Schema
    ai_resp = AIInsightResponse(
        id=uuid4(),
        user_id=user_id,
        insight_type="emotion_bias",
        summary="High win rate on morning CPR breakouts.",
        created_at=datetime.now()
    )
    assert ai_resp.insight_type == "emotion_bias"

    # 9. System Schema
    audit_resp = AuditLogResponse(
        id=uuid4(),
        user_id=user_id,
        action="UPDATE_PREFERENCES",
        resource="identity.user_market_preferences",
        created_at=datetime.now()
    )
    assert audit_resp.action == "UPDATE_PREFERENCES"
