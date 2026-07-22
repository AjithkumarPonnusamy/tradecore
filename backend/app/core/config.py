import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "TradeCore"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    # Default to local PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/tradecore"
    
    # Redis Cache Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT & Security Settings
    JWT_SECRET: str = ""
    JWT_SECRET_KEY: str = "super_secret_key_change_me_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ENCRYPTION_KEY: str = ""
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_CALLBACK_URL: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    
    # Google Drive Settings
    GOOGLE_DRIVE_FOLDER_NAME: str = "Trade Journal"
    GOOGLE_DRIVE_FOLDER_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_CREDENTIALS_FILE: str = "google_credentials.json"
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""

    # Self-Hosted LLM & Whisper Settings
    LLM_API_BASE: str = "http://host.docker.internal:11434/v1"
    LLM_MODEL: str = "llama3"
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    AI_SERVICE_URL: str = "http://ai-service:8001"
    
    # Admin / System Configs
    ADMIN_AVAILABLE_SYMBOLS: list[str] = [
        "XAUUSD", "GBPUSD", "EURUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
        "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCAP", "SENSEX",
        "BTCUSD", "ETHUSD",
        "NASDAQ", "SPX500",
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"
    ]
    
    ADMIN_DEFAULT_WIDGETS: list[str] = [
        "marketDashboard", "livePriceFeed", "sessionMetrics", "institutionalLevels",
        "cprLevels", "camarillaLevels", "analyticsOverview", "tradePerformance",
        "aiInsights", "watchlist", "telegramAlerts", "economicCalendar", "voiceJournalSummary"
    ]
    
    ADMIN_DEFAULT_WIDGET_VISIBILITY: dict[str, bool] = {
        "marketDashboard": True,
        "livePriceFeed": True,
        "sessionMetrics": True,
        "institutionalLevels": True,
        "cprLevels": True,
        "camarillaLevels": True,
        "analyticsOverview": True,
        "tradePerformance": True,
        "aiInsights": True,
        "watchlist": True,
        "telegramAlerts": True,
        "economicCalendar": True,
        "voiceJournalSummary": True
    }
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if self.JWT_SECRET:
            self.JWT_SECRET_KEY = self.JWT_SECRET
        if self.GOOGLE_CALLBACK_URL:
            self.GOOGLE_REDIRECT_URI = self.GOOGLE_CALLBACK_URL
        if self.JWT_SECRET_KEY == "super_secret_key_change_me_in_production_1234567890":
            import warnings
            warnings.warn("Using default insecure JWT_SECRET_KEY. Ensure JWT_SECRET_KEY is set in environment for production deployments.")

settings = Settings()
