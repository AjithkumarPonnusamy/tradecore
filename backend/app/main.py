import os
import logging
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.init_db import init_db
from app.core.middleware import RequestIDMiddleware
from app.core.exceptions import register_exception_handlers
from app.api import (
    auth, trades, dashboard, screener, checklists, market, 
    scanners, backtesting, journal, voice_journal, research, system
)
from app.core.database import SessionLocal
from app.models.models import ScannerSettings
from app.api.scanners import execute_scanner_for_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("tradecore")

# Run database table initialization and schema verifications
init_db()

def start_background_scanner():
    def run_loop():
        time.sleep(15)
        logger.info("Automatic Background Scanner thread started.")
        while True:
            try:
                db = SessionLocal()
                try:
                    settings_list = db.query(ScannerSettings).all()
                    for s in settings_list:
                        if s.telegram_enabled:
                            logger.info(f"Running automatic scan for user {s.user_id}...")
                            execute_scanner_for_user(db, s.user_id)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in automatic background scanner loop: {e}")
            
            time.sleep(300)

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_background_scanner()
    logger.info("TradeCore Backend initialized and running across all 9 domain schemas.")
    yield
    logger.info("TradeCore Backend shutting down gracefully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Attach Request ID Middleware for request tracing
app.add_middleware(RequestIDMiddleware)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# Register global exception handlers for standardized error envelopes
register_exception_handlers(app)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3005", "http://127.0.0.1:3000", "http://127.0.0.1:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount local uploads directory to serve screenshots locally
LOCAL_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "local_uploads"
)
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=LOCAL_UPLOAD_DIR), name="uploads")

# Include Routers across all 9 domain schemas
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(trades.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(screener.router, prefix=settings.API_V1_STR)
app.include_router(checklists.router, prefix=settings.API_V1_STR)
app.include_router(market.router, prefix=settings.API_V1_STR)
app.include_router(scanners.router, prefix=settings.API_V1_STR)
app.include_router(backtesting.router, prefix=settings.API_V1_STR)
app.include_router(journal.router, prefix=settings.API_V1_STR)
app.include_router(voice_journal.router, prefix=settings.API_V1_STR)
app.include_router(research.router, prefix=settings.API_V1_STR)
app.include_router(system.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Welcome to TradeCore Trading Platform API",
        "docs": "/docs",
        "schemas": ["identity", "market", "trading", "journal", "backtest", "research", "scanner", "ai", "system"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
