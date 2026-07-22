import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Time, Numeric, 
    ForeignKey, Table, Index, func, Integer, TypeDecorator, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            from app.core.security import encrypt_value
            return encrypt_value(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            from app.core.security import decrypt_value
            return decrypt_value(value)
        return value

# ==============================================================================
# 1. IDENTITY SCHEMA MODELS
# ==============================================================================
class UserOAuthAccount(Base):
    __tablename__ = "user_oauth_accounts"
    __table_args__ = (
        Index("idx_oauth_user_provider", "user_id", "provider", unique=True),
        {"schema": "identity"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String, default="google", nullable=False, index=True)
    provider_user_id = Column(String, nullable=True, index=True)
    provider_email = Column(String, nullable=True)
    provider_name = Column(String, nullable=True)
    provider_avatar = Column(String, nullable=True)
    
    client_id = Column(String, nullable=True)
    client_secret = Column(EncryptedString, nullable=True)
    access_token = Column(EncryptedString, nullable=True)
    refresh_token = Column(EncryptedString, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    drive_folder_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="oauth_accounts")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    auth_provider = Column(String, default="EMAIL", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    oauth_accounts = relationship("UserOAuthAccount", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    voice_journals = relationship("VoiceJournal", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    backtest_runs = relationship("BacktestRun", back_populates="user", cascade="all, delete-orphan")
    
    def _get_google_oauth(self) -> Optional[UserOAuthAccount]:
        if not self.oauth_accounts:
            return None
        for acc in self.oauth_accounts:
            if acc.provider == "google":
                return acc
        return None

    @property
    def google_account(self) -> Optional[UserOAuthAccount]:
        return self._get_google_oauth()

    @property
    def google_id(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.provider_user_id if acc else None

    @property
    def google_email(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.provider_email if acc else None

    @property
    def google_name(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.provider_name if acc else None

    @property
    def google_avatar(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.provider_avatar if acc else None

    @property
    def google_client_id(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.client_id if acc else None

    @property
    def google_client_secret(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.client_secret if acc else None

    @property
    def google_access_token(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.access_token if acc else None

    @property
    def google_refresh_token(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.refresh_token if acc else None

    @property
    def google_token_expiry(self) -> Optional[datetime]:
        acc = self._get_google_oauth()
        return acc.token_expiry if acc else None

    @property
    def google_drive_folder_id(self) -> Optional[str]:
        acc = self._get_google_oauth()
        return acc.drive_folder_id if acc else None

    def _get_or_create_google_oauth(self) -> UserOAuthAccount:
        acc = self._get_google_oauth()
        if not acc:
            acc = UserOAuthAccount(user=self, provider="google")
        return acc

    @google_access_token.setter
    def google_access_token(self, value: Optional[str]):
        acc = self._get_or_create_google_oauth()
        acc.access_token = value

    @google_refresh_token.setter
    def google_refresh_token(self, value: Optional[str]):
        acc = self._get_or_create_google_oauth()
        acc.refresh_token = value

    @google_token_expiry.setter
    def google_token_expiry(self, value: Optional[datetime]):
        acc = self._get_or_create_google_oauth()
        acc.token_expiry = value

    @google_drive_folder_id.setter
    def google_drive_folder_id(self, value: Optional[str]):
        acc = self._get_or_create_google_oauth()
        acc.drive_folder_id = value

    @google_client_id.setter
    def google_client_id(self, value: Optional[str]):
        acc = self._get_or_create_google_oauth()
        acc.client_id = value

    @google_client_secret.setter
    def google_client_secret(self, value: Optional[str]):
        acc = self._get_or_create_google_oauth()
        acc.client_secret = value

    @property
    def has_google_client_secret(self) -> bool:
        acc = self._get_google_oauth()
        return acc is not None and acc.client_secret is not None and len(acc.client_secret) > 0

    @property
    def google_drive_connected(self) -> bool:
        acc = self._get_google_oauth()
        return acc is not None and acc.access_token is not None and acc.refresh_token is not None


class UserMarketPreferences(Base):
    __tablename__ = "user_market_preferences"
    __table_args__ = {"schema": "identity"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, unique=True)
    favorite_symbols = Column(JSONB, default=[], nullable=False)
    visible_reference_levels = Column(JSONB, default={}, nullable=False)
    dashboard_layout = Column(JSONB, default={}, nullable=False)
    broker_credentials = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


class DashboardPreference(Base):
    __tablename__ = "dashboard_preferences"
    __table_args__ = (
        Index("idx_dash_pref_user_layout", "user_id", "layout_name", unique=True),
        {"schema": "identity"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_symbols = Column(JSONB, default=[], nullable=False)
    widget_visibility = Column(JSONB, default={}, nullable=False)
    widget_order = Column(JSONB, default=[], nullable=False)
    layout_name = Column(String, default="default", nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = {"schema": "identity"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    settings = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="watchlist_items")


# ==============================================================================
# 2. MARKET SCHEMA MODELS (Shared Source of Truth - Decoupled Architecture)
# ==============================================================================
class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = (
        Index("idx_symbols_lookup", "symbol", "exchange"),
        {"schema": "market"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    segment = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    instrument_token = Column(String(100), nullable=True)
    tick_size = Column(Numeric(12, 6), nullable=True)
    lot_size = Column(Integer, nullable=True)
    currency = Column(String(10), default="INR")
    timezone = Column(String(50), nullable=False, default="UTC")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())


class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = (
        Index("idx_market_data_sym_mkt", "symbol", "market", unique=True),
        {"schema": "market"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    live_price = Column(Numeric(precision=18, scale=8), nullable=True)
    trueday_open = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_trueday_open = Column(Numeric(precision=18, scale=8), nullable=True)
    indian_midnight_open = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_high = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_low = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_close = Column(Numeric(precision=18, scale=8), nullable=True)
    current_day_high = Column(Numeric(precision=18, scale=8), nullable=True)
    current_day_low = Column(Numeric(precision=18, scale=8), nullable=True)
    daily_range = Column(Numeric(precision=18, scale=8), nullable=True)
    cpr_levels = Column(JSONB, default={}, nullable=False)
    camarilla_levels = Column(JSONB, default={}, nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    timezone_info = Column(String, nullable=True)


class PivotLevels(Base):
    __tablename__ = "pivot_levels"
    __table_args__ = (
        Index("idx_pivot_levels_sym_mkt_date", "symbol", "market", "date", unique=True),
        {"schema": "market"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    cpr_pivot = Column(Numeric(precision=18, scale=8), nullable=False)
    cpr_tc = Column(Numeric(precision=18, scale=8), nullable=False)
    cpr_bc = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_r1 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_r2 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_r3 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_r4 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_s1 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_s2 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_s3 = Column(Numeric(precision=18, scale=8), nullable=False)
    camarilla_s4 = Column(Numeric(precision=18, scale=8), nullable=False)
    created_at = Column(DateTime, default=func.now())


class MarketCandle(Base):
    __tablename__ = "market_candles"
    __table_args__ = (
        Index("idx_candles_sym_tf_dt", "symbol", "timeframe", "datetime"),
        {"schema": "market"}
    )
    
    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    symbol = Column(String, primary_key=True, index=True, nullable=False)
    timeframe = Column(String, primary_key=True, index=True, nullable=False)
    datetime = Column(DateTime, primary_key=True, index=True, nullable=False)
    open = Column(Numeric(precision=18, scale=8), nullable=False)
    high = Column(Numeric(precision=18, scale=8), nullable=False)
    low = Column(Numeric(precision=18, scale=8), nullable=False)
    close = Column(Numeric(precision=18, scale=8), nullable=False)
    volume = Column(Numeric(precision=18, scale=8), nullable=True, default=0)
    source = Column(String, nullable=False, default="public_feed")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ==============================================================================
# 3. TRADING SCHEMA MODELS
# ==============================================================================
class Strategy(Base):
    __tablename__ = "strategies"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    rules = Column(JSONB, default={}, nullable=False)
    risk_rules = Column(JSONB, default={}, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trades_setup", "setup", postgresql_using="gin"),
        Index("idx_trades_psychology", "psychology", postgresql_using="gin"),
        Index("idx_trades_analytics", "analytics", postgresql_using="gin"),
        Index("idx_trades_tags", "tags", postgresql_using="gin"),
        {"schema": "trading"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("trading.strategies.id", ondelete="SET NULL"), nullable=True, index=True)
    
    trade_date = Column(Date, nullable=False, default=func.current_date(), index=True)
    trade_time = Column(Time, nullable=True)
    market = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)
    status = Column(String, default="OPEN", index=True)
    trading_type = Column(String, nullable=True, index=True)
    segment = Column(String, nullable=True, index=True)
    
    entry_price = Column(Numeric(precision=18, scale=8), nullable=False)
    stop_loss = Column(Numeric(precision=18, scale=8), nullable=True)
    target_price = Column(Numeric(precision=18, scale=8), nullable=True)
    exit_price = Column(Numeric(precision=18, scale=8), nullable=True)
    quantity = Column(Numeric(precision=18, scale=8), nullable=False, default=1.0)
    net_profit = Column(Numeric(precision=18, scale=2), nullable=True)

    r_multiple = Column(Numeric(precision=8, scale=2), nullable=True, index=True)
    holding_minutes = Column(Integer, nullable=True, index=True)
    confidence_rating = Column(Integer, nullable=True, index=True)
    
    setup = Column(JSONB, default={}, nullable=False)
    psychology = Column(JSONB, default={}, nullable=False)
    notes = Column(JSONB, default={}, nullable=False)
    analytics = Column(JSONB, default={}, nullable=False)
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)
    
    tags = Column(ARRAY(String), default=[], nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    images = relationship("TradeImage", back_populates="trade", cascade="all, delete-orphan")
    market_snapshot = relationship("TradeMarketSnapshot", back_populates="trade", uselist=False, cascade="all, delete-orphan")
    voice_journal = relationship("VoiceJournal", back_populates="trade", uselist=False, cascade="all, delete-orphan")


class TradeImage(Base):
    __tablename__ = "trade_images"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trading.trades.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, nullable=False)
    google_file_id = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    extra_data = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    trade = relationship("Trade", back_populates="images")


class TradeMarketSnapshot(Base):
    __tablename__ = "trade_market_snapshot"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trading.trades.id", ondelete="CASCADE"), nullable=False, unique=True)
    symbol = Column(String, nullable=False)
    live_price = Column(Numeric(precision=18, scale=8), nullable=True)
    trueday_open = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_trueday_open = Column(Numeric(precision=18, scale=8), nullable=True)
    indian_midnight_open = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_high = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_low = Column(Numeric(precision=18, scale=8), nullable=True)
    previous_day_close = Column(Numeric(precision=18, scale=8), nullable=True)
    current_day_high = Column(Numeric(precision=18, scale=8), nullable=True)
    current_day_low = Column(Numeric(precision=18, scale=8), nullable=True)
    daily_range = Column(Numeric(precision=18, scale=8), nullable=True)
    cpr_levels = Column(JSONB, default={}, nullable=False)
    camarilla_levels = Column(JSONB, default={}, nullable=False)
    snapshot_at = Column(DateTime, default=func.now())
    
    trade = relationship("Trade", back_populates="market_snapshot")


# ==============================================================================
# 4. JOURNAL SCHEMA MODELS
# ==============================================================================
class TechnicalChecklist(Base):
    __tablename__ = "technical_checklists"
    __table_args__ = {"schema": "journal"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    order_idx = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


class ConfirmationChecklist(Base):
    __tablename__ = "confirmation_checklists"
    __table_args__ = {"schema": "journal"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    order_idx = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = {"schema": "journal"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, default=func.current_date())
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    mood_score = Column(Integer, nullable=True)
    lessons_learned = Column(ARRAY(String), default=[], nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="journal_entries")


# ==============================================================================
# 5. BACKTEST SCHEMA MODELS
# ==============================================================================
class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    __table_args__ = {"schema": "backtest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("trading.strategies.id", ondelete="SET NULL"), nullable=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Numeric(18, 2), default=100000.00, nullable=False)
    parameters = Column(JSONB, default={}, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="backtest_runs")
    strategy = relationship("Strategy")
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")
    metric = relationship("BacktestMetric", back_populates="backtest_run", uselist=False, cascade="all, delete-orphan")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    __table_args__ = {"schema": "backtest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest.backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    direction = Column(String(20), nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    exit_price = Column(Numeric(18, 8), nullable=True)
    quantity = Column(Numeric(18, 8), nullable=False)
    pnl = Column(Numeric(18, 2), nullable=True)
    r_multiple = Column(Numeric(8, 2), nullable=True)

    backtest_run = relationship("BacktestRun", back_populates="trades")


class BacktestMetric(Base):
    __tablename__ = "backtest_metrics"
    __table_args__ = {"schema": "backtest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtest.backtest_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Numeric(5, 2), nullable=True)
    profit_factor = Column(Numeric(8, 2), nullable=True)
    sharpe_ratio = Column(Numeric(8, 2), nullable=True)
    max_drawdown = Column(Numeric(8, 2), nullable=True)
    equity_curve = Column(JSONB, default=[], nullable=False)
    created_at = Column(DateTime, default=func.now())

    backtest_run = relationship("BacktestRun", back_populates="metric")


# ==============================================================================
# 6. RESEARCH SCHEMA MODELS
# ==============================================================================
class ResearchNotebook(Base):
    __tablename__ = "research_notebooks"
    __table_args__ = {"schema": "research"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    notebook_data = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")


class FactorData(Base):
    __tablename__ = "factor_data"
    __table_args__ = (
        Index("idx_factor_sym_name_date", "symbol", "factor_name", "date", unique=True),
        {"schema": "research"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False)
    factor_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    factor_value = Column(Numeric(18, 8), nullable=False)
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())


class CustomStudy(Base):
    __tablename__ = "custom_studies"
    __table_args__ = {"schema": "research"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    study_name = Column(String(255), nullable=False)
    code_content = Column(Text, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")


# ==============================================================================
# 7. SCANNER SCHEMA MODELS
# ==============================================================================
class ScreenerResult(Base):
    __tablename__ = "screener_results"
    __table_args__ = {"schema": "scanner"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    pattern = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    entry_price = Column(Numeric(precision=18, scale=8), nullable=True)
    stop_loss = Column(Numeric(precision=18, scale=8), nullable=True)
    target_price = Column(Numeric(precision=18, scale=8), nullable=True)
    confidence_score = Column(Numeric(precision=5, scale=2), nullable=True)
    scanned_at = Column(DateTime, default=func.now(), index=True)


class ScannerResult(Base):
    __tablename__ = "scanner_results"
    __table_args__ = {"schema": "scanner"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, index=True, nullable=False)
    scanner_name = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    signal_type = Column(String, index=True, nullable=False)
    price = Column(Numeric(precision=18, scale=8), nullable=True)
    confidence_score = Column(Numeric(precision=5, scale=2), nullable=True)
    details = Column(JSONB, default={}, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True, index=True)
    telegram_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)


class ScannerSettings(Base):
    __tablename__ = "scanner_settings"
    __table_args__ = {"schema": "scanner"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled_scanners = Column(JSONB, default={}, nullable=False)
    telegram_bot_token = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    telegram_enabled = Column(Boolean, default=False, nullable=False)
    telegram_alert_types = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


class ScannerTemplate(Base):
    __tablename__ = "scanner_templates"
    __table_args__ = {"schema": "scanner"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    conditions = Column(JSONB, default=[], nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")


# ==============================================================================
# 8. AI SCHEMA MODELS
# ==============================================================================
class VoiceJournal(Base):
    __tablename__ = "voice_journals"
    __table_args__ = {"schema": "ai"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trading.trades.id", ondelete="SET NULL"), nullable=True, index=True)
    audio_url = Column(String, nullable=False)
    transcript = Column(String, nullable=True)
    original_transcript = Column(String, nullable=True)
    corrected_transcript = Column(String, nullable=True)
    ai_summary = Column(JSONB, default={}, nullable=False)
    emotion_tags = Column(JSONB, default=[], nullable=False)
    status = Column(String, default="PROCESSING", nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="voice_journals")
    trade = relationship("Trade", back_populates="voice_journal")


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    messages = Column(JSONB, default=[], nullable=False)
    context_data = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")


class AIInsight(Base):
    __tablename__ = "ai_insights"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_type = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    details = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")


# ==============================================================================
# 9. SYSTEM SCHEMA MODELS
# ==============================================================================
class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = {"schema": "system"}

    key = Column(String(255), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "system"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())


class TaskExecutionLog(Base):
    __tablename__ = "task_execution_logs"
    __table_args__ = {"schema": "system"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default={}, nullable=False)
    created_at = Column(DateTime, default=func.now())


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"
    __table_args__ = {"schema": "system"}

    version = Column(String(100), primary_key=True)
    description = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=func.now())
