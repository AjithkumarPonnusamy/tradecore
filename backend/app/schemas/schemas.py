from pydantic import BaseModel, EmailStr, ConfigDict, Field, AliasChoices, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from uuid import UUID

class ORMProxy:
    def __init__(self, obj):
        self._obj = obj
    def __getattr__(self, name):
        if name == "metadata":
            return getattr(self._obj, "metadata_", None)
        return getattr(self._obj, name)

# ==========================================
# 1. IDENTITY SCHEMAS
# ==========================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOAuthAccountResponse(BaseModel):
    id: UUID
    provider: str
    provider_user_id: Optional[str] = None
    provider_email: Optional[str] = None
    provider_name: Optional[str] = None
    provider_avatar: Optional[str] = None
    drive_folder_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    google_client_id: Optional[str] = None
    has_google_client_secret: bool = False
    google_email: Optional[str] = None
    google_name: Optional[str] = None
    google_avatar: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    google_drive_folder_id: Optional[str] = None
    google_drive_connected: bool = False
    auth_provider: str = "EMAIL"
    oauth_accounts: List[UserOAuthAccountResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_email: Optional[str] = None
    google_name: Optional[str] = None
    google_avatar: Optional[str] = None
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    google_drive_folder_id: Optional[str] = None
    google_auth_code: Optional[str] = None
    auth_provider: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[UUID] = None

class UserMarketPreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    favorite_symbols: List[str]
    visible_reference_levels: Dict[str, Any]
    dashboard_layout: Dict[str, Any]
    broker_credentials: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserMarketPreferencesUpdate(BaseModel):
    favorite_symbols: Optional[List[str]] = None
    visible_reference_levels: Optional[Dict[str, Any]] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    broker_credentials: Optional[Dict[str, Any]] = None

class DashboardPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    selected_symbols: List[str]
    widget_visibility: Dict[str, bool]
    widget_order: List[str]
    layout_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardPreferenceUpdate(BaseModel):
    selected_symbols: Optional[List[str]] = None
    widget_visibility: Optional[Dict[str, bool]] = None
    widget_order: Optional[List[str]] = None
    layout_name: Optional[str] = None

class WatchlistBase(BaseModel):
    symbol: str
    market: str
    position: Optional[int] = 0
    settings: Dict[str, Any] = Field(default_factory=dict)

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistUpdate(BaseModel):
    symbol: Optional[str] = None
    market: Optional[str] = None
    position: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class WatchlistResponse(WatchlistBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 2. MARKET SCHEMAS
# ==========================================

class SymbolResponse(BaseModel):
    id: UUID
    exchange: str
    segment: str
    symbol: str
    instrument_token: Optional[str] = None
    tick_size: Optional[float] = None
    lot_size: Optional[int] = None
    currency: str = "INR"
    timezone: str = "UTC"
    active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MarketDataResponse(BaseModel):
    id: UUID
    symbol: str
    market: str
    live_price: Optional[float] = None
    trueday_open: Optional[float] = None
    previous_trueday_open: Optional[float] = None
    indian_midnight_open: Optional[float] = None
    previous_day_high: Optional[float] = None
    previous_day_low: Optional[float] = None
    previous_day_close: Optional[float] = None
    current_day_high: Optional[float] = None
    current_day_low: Optional[float] = None
    daily_range: Optional[float] = None
    cpr_levels: Dict[str, Any] = {}
    camarilla_levels: Dict[str, Any] = {}
    last_updated: datetime
    timezone_info: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PivotLevelsResponse(BaseModel):
    id: UUID
    symbol: str
    market: str
    date: date
    cpr_pivot: float
    cpr_tc: float
    cpr_bc: float
    camarilla_r1: float
    camarilla_r2: float
    camarilla_r3: float
    camarilla_r4: float
    camarilla_s1: float
    camarilla_s2: float
    camarilla_s3: float
    camarilla_s4: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MarketCandleResponse(BaseModel):
    symbol: str
    timeframe: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = 0
    source: str = "public_feed"

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 3. TRADING SCHEMAS
# ==========================================

class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    rules: Dict[str, Any] = Field(default_factory=dict)
    risk_rules: Dict[str, Any] = Field(default_factory=dict)

class StrategyCreate(StrategyBase):
    pass

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    risk_rules: Optional[Dict[str, Any]] = None

class StrategyResponse(StrategyBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TradeBase(BaseModel):
    trade_date: date
    trade_time: Optional[time] = None
    market: str
    symbol: str = Field(..., validation_alias=AliasChoices("symbol", "instrument"))
    direction: str
    status: str = "OPEN"
    
    entry_price: float
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    exit_price: Optional[float] = None
    quantity: float = 1.0
    net_profit: Optional[float] = None

    r_multiple: Optional[float] = None
    holding_minutes: Optional[int] = None
    confidence_rating: Optional[int] = None
    
    setup: Dict[str, Any] = Field(default_factory=dict)
    psychology: Dict[str, Any] = Field(default_factory=dict)
    notes: Dict[str, Any] = Field(default_factory=dict)
    analytics: Dict[str, Any] = Field(default_factory=dict)
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata",
        serialization_alias="metadata"
    )
    
    tags: List[str] = Field(default_factory=list)
    strategy_id: Optional[UUID] = None
    trading_type: Optional[str] = Field(None, validation_alias=AliasChoices("trading_type", "tradingType"))
    segment: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def preprocess_orm(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return ORMProxy(data)
        return data

class TradeCreate(TradeBase):
    pass

class TradeUpdate(BaseModel):
    trade_date: Optional[date] = None
    trade_time: Optional[time] = None
    market: Optional[str] = None
    symbol: Optional[str] = Field(None, validation_alias=AliasChoices("symbol", "instrument"))
    direction: Optional[str] = None
    status: Optional[str] = None
    
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    exit_price: Optional[float] = None
    quantity: Optional[float] = None
    net_profit: Optional[float] = None
    
    setup: Optional[Dict[str, Any]] = None
    psychology: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None
    analytics: Optional[Dict[str, Any]] = None
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata"
    )
    
    tags: Optional[List[str]] = None
    strategy_id: Optional[UUID] = None
    trading_type: Optional[str] = Field(None, validation_alias=AliasChoices("trading_type", "tradingType"))
    segment: Optional[str] = None

class TradeImageResponse(BaseModel):
    id: UUID
    trade_id: UUID
    category: str
    google_file_id: Optional[str] = None
    file_url: Optional[str] = None
    caption: Optional[str] = None
    extra_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TradeMarketSnapshotResponse(BaseModel):
    id: UUID
    trade_id: UUID
    symbol: str
    live_price: Optional[float] = None
    trueday_open: Optional[float] = None
    previous_trueday_open: Optional[float] = None
    indian_midnight_open: Optional[float] = None
    previous_day_high: Optional[float] = None
    previous_day_low: Optional[float] = None
    previous_day_close: Optional[float] = None
    current_day_high: Optional[float] = None
    current_day_low: Optional[float] = None
    daily_range: Optional[float] = None
    cpr_levels: Dict[str, Any] = {}
    camarilla_levels: Dict[str, Any] = {}
    snapshot_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TradeResponse(TradeBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    images: List[TradeImageResponse] = []
    market_snapshot: Optional[TradeMarketSnapshotResponse] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

# ==========================================
# 4. JOURNAL SCHEMAS
# ==========================================

class TechnicalChecklistBase(BaseModel):
    name: str
    is_enabled: bool = True
    order_idx: int = 0

class TechnicalChecklistCreate(TechnicalChecklistBase):
    pass

class TechnicalChecklistUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    order_idx: Optional[int] = None

class TechnicalChecklistResponse(TechnicalChecklistBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConfirmationChecklistBase(BaseModel):
    name: str
    is_enabled: bool = True
    order_idx: int = 0

class ConfirmationChecklistCreate(ConfirmationChecklistBase):
    pass

class ConfirmationChecklistUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    order_idx: Optional[int] = None

class ConfirmationChecklistResponse(ConfirmationChecklistBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JournalEntryBase(BaseModel):
    entry_date: date
    title: Optional[str] = None
    content: Optional[str] = None
    mood_score: Optional[int] = None
    lessons_learned: List[str] = Field(default_factory=list)

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood_score: Optional[int] = None
    lessons_learned: Optional[List[str]] = None

class JournalEntryResponse(JournalEntryBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 5. BACKTEST SCHEMAS
# ==========================================

class BacktestRunBase(BaseModel):
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.00
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BacktestRunCreate(BacktestRunBase):
    strategy_id: Optional[UUID] = None

class BacktestRunUpdate(BaseModel):
    status: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class BacktestTradeResponse(BaseModel):
    id: UUID
    backtest_id: UUID
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    pnl: Optional[float] = None
    r_multiple: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class BacktestMetricResponse(BaseModel):
    id: UUID
    backtest_id: UUID
    total_trades: int
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    equity_curve: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BacktestRunResponse(BacktestRunBase):
    id: UUID
    user_id: UUID
    strategy_id: Optional[UUID] = None
    status: str
    created_at: datetime
    trades: List[BacktestTradeResponse] = []
    metric: Optional[BacktestMetricResponse] = None

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 6. RESEARCH SCHEMAS
# ==========================================

class ResearchNotebookBase(BaseModel):
    title: str
    description: Optional[str] = None
    notebook_data: Dict[str, Any] = Field(default_factory=dict)

class ResearchNotebookCreate(ResearchNotebookBase):
    pass

class ResearchNotebookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    notebook_data: Optional[Dict[str, Any]] = None

class ResearchNotebookResponse(ResearchNotebookBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FactorDataResponse(BaseModel):
    id: UUID
    symbol: str
    factor_name: str
    date: date
    factor_value: float
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CustomStudyResponse(BaseModel):
    id: UUID
    user_id: UUID
    study_name: str
    code_content: str
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 7. SCANNER SCHEMAS
# ==========================================

class ScreenerResultResponse(BaseModel):
    id: UUID
    symbol: str
    market: str
    pattern: str
    timeframe: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    confidence_score: Optional[float] = None
    scanned_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScannerResultBaseResponse(BaseModel):
    id: UUID
    symbol: str
    market: str
    scanner_name: str
    timeframe: str
    signal_type: str
    price: Optional[float] = None
    confidence_score: Optional[float] = None
    details: Dict[str, Any] = {}
    triggered_at: Optional[datetime] = None
    telegram_sent: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScannerSettingsResponse(BaseModel):
    id: UUID
    user_id: UUID
    enabled_scanners: Dict[str, Any]
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: bool = False
    telegram_alert_types: Dict[str, bool] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScannerSettingsUpdate(BaseModel):
    enabled_scanners: Optional[Dict[str, Any]] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_alert_types: Optional[Dict[str, bool]] = None

class ScannerTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: Any = []

class ScannerTemplateCreate(ScannerTemplateBase):
    pass

class ScannerTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Any] = None

class ScannerTemplateResponse(ScannerTemplateBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 8. AI SCHEMAS
# ==========================================

class VoiceJournalResponse(BaseModel):
    id: UUID
    user_id: UUID
    trade_id: Optional[UUID] = None
    audio_url: str
    transcript: Optional[str] = None
    original_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    ai_summary: Dict[str, Any] = {}
    emotion_tags: List[Any] = []
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VoiceJournalUpdate(BaseModel):
    transcript: Optional[str] = None
    original_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    ai_summary: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class AIConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    messages: List[Dict[str, Any]] = []
    context_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AIInsightResponse(BaseModel):
    id: UUID
    user_id: UUID
    insight_type: str
    summary: str
    details: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 9. SYSTEM SCHEMAS & DASHBOARD AGGREGATES
# ==========================================

class SystemSettingResponse(BaseModel):
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource: Optional[str] = None
    ip_address: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TaskExecutionLogResponse(BaseModel):
    id: UUID
    task_name: str
    status: str
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class DashboardMetricsResponse(BaseModel):
    total_pnl: float
    win_rate: float
    total_trades: int
    wins: int
    losses: int
    avg_r: float
    profit_factor: float
    expectancy: float
    max_drawdown: float
    consecutive_wins: int
    consecutive_losses: int
    best_strategy: Optional[str] = None
    best_timeframe: Optional[str] = None
    best_session: Optional[str] = None
    best_market: Optional[str] = None
    charts: Dict[str, Any] = Field(default_factory=dict)
    category_analytics: Dict[str, Any] = Field(default_factory=dict)
    db_connected: bool = True
    db_name: str = "PostgreSQL"
    db_last_sync: str = "Just now"
