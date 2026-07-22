from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Search path configuring resolution across all 9 domain schemas (no spaces after commas for CLI option compliance)
SEARCH_PATH = "identity,market,trading,journal,backtest,research,scanner,ai,system,public"

# Create high-performance database engine with connection pooling and schema search_path
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=25,
    max_overflow=15,
    pool_recycle=1800,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={"options": f"-c search_path={SEARCH_PATH}"}
)

# Create session maker with autoflush=False for batch execution efficiency
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Database session generator dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
