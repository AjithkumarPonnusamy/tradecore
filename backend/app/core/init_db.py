import logging
from sqlalchemy import text
from app.core.database import engine, Base

logger = logging.getLogger(__name__)

def init_db():
    """
    Initializes database tables, runs light migration column checks,
    and ensures required performance indices exist.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
        
        with engine.connect() as conn:
            # Check trades table
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='trades';"))
            columns = [row[0] for row in res.fetchall()]
            
            if "trading_type" not in columns:
                conn.execute(text("ALTER TABLE trades ADD COLUMN trading_type VARCHAR;"))
                conn.commit()
                logger.info("Migrated: Added 'trading_type' column to trades table.")
                
            if "segment" not in columns:
                conn.execute(text("ALTER TABLE trades ADD COLUMN segment VARCHAR;"))
                conn.commit()
                logger.info("Migrated: Added 'segment' column to trades table.")
                
            # Check user_market_preferences table
            res_prefs = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='user_market_preferences';"))
            prefs_cols = [row[0] for row in res_prefs.fetchall()]
            if "broker_credentials" not in prefs_cols:
                conn.execute(text("ALTER TABLE user_market_preferences ADD COLUMN broker_credentials JSONB DEFAULT '{}'::jsonb NOT NULL;"))
                conn.commit()
                logger.info("Migrated: Added 'broker_credentials' column to user_market_preferences table.")
                
            # Check users table
            res_users = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users';"))
            users_cols = [row[0] for row in res_users.fetchall()]
            user_columns_to_add = [
                ("google_client_id", "VARCHAR"),
                ("google_client_secret", "VARCHAR"),
                ("google_email", "VARCHAR"),
                ("google_name", "VARCHAR"),
                ("google_avatar", "VARCHAR"),
                ("google_access_token", "VARCHAR"),
                ("google_refresh_token", "VARCHAR"),
                ("google_token_expiry", "TIMESTAMP"),
                ("google_drive_folder_id", "VARCHAR"),
            ]
            for col_name, col_type in user_columns_to_add:
                if col_name not in users_cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                    conn.commit()
                    logger.info(f"Migrated: Added '{col_name}' column to users table.")

            if "auth_provider" not in users_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR NOT NULL DEFAULT 'EMAIL';"))
                conn.commit()
                logger.info("Migrated: Added 'auth_provider' column to users table.")
                
            # Check scanner_settings table
            res_scan_settings = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scanner_settings';"))
            scan_settings_cols = [row[0] for row in res_scan_settings.fetchall()]
            scanner_columns_to_add = [
                ("telegram_bot_token", "VARCHAR"),
                ("telegram_chat_id", "VARCHAR"),
            ]
            for col_name, col_type in scanner_columns_to_add:
                if col_name not in scan_settings_cols:
                    conn.execute(text(f"ALTER TABLE scanner_settings ADD COLUMN {col_name} {col_type};"))
                    conn.commit()
                    logger.info(f"Migrated: Added '{col_name}' column to scanner_settings table.")

            if "telegram_enabled" not in scan_settings_cols:
                conn.execute(text("ALTER TABLE scanner_settings ADD COLUMN telegram_enabled BOOLEAN DEFAULT FALSE NOT NULL;"))
                conn.commit()
                logger.info("Migrated: Added 'telegram_enabled' column to scanner_settings table.")

            if "telegram_alert_types" not in scan_settings_cols:
                conn.execute(text("ALTER TABLE scanner_settings ADD COLUMN telegram_alert_types JSONB DEFAULT '{}'::jsonb NOT NULL;"))
                conn.commit()
                logger.info("Migrated: Added 'telegram_alert_types' column to scanner_settings table.")
                
            # Check scanner_results table
            res_scan_results = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scanner_results';"))
            scan_results_cols = [row[0] for row in res_scan_results.fetchall()]
            if "triggered_at" not in scan_results_cols:
                conn.execute(text("ALTER TABLE scanner_results ADD COLUMN triggered_at TIMESTAMPTZ;"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scanner_results_triggered_at ON scanner_results(triggered_at);"))
                conn.commit()
                logger.info("Migrated: Added 'triggered_at' column to scanner_results table.")
            if "telegram_sent" not in scan_results_cols:
                conn.execute(text("ALTER TABLE scanner_results ADD COLUMN telegram_sent BOOLEAN NOT NULL DEFAULT FALSE;"))
                conn.commit()
                logger.info("Migrated: Added 'telegram_sent' column to scanner_results table.")

            # Check voice_journals table
            res_voice_journals = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='voice_journals';"))
            voice_journals_cols = [row[0] for row in res_voice_journals.fetchall()]
            if "original_transcript" not in voice_journals_cols:
                conn.execute(text("ALTER TABLE voice_journals ADD COLUMN original_transcript VARCHAR;"))
                conn.commit()
                logger.info("Migrated: Added 'original_transcript' column to voice_journals table.")
            if "corrected_transcript" not in voice_journals_cols:
                conn.execute(text("ALTER TABLE voice_journals ADD COLUMN corrected_transcript VARCHAR;"))
                conn.commit()
                logger.info("Migrated: Added 'corrected_transcript' column to voice_journals table.")

            # Check watchlist table
            res_watchlist = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='watchlist';"))
            watchlist_cols = [row[0] for row in res_watchlist.fetchall()]
            if "position" not in watchlist_cols:
                conn.execute(text("ALTER TABLE watchlist ADD COLUMN position INTEGER DEFAULT 0 NOT NULL;"))
                conn.commit()
                logger.info("Migrated: Added 'position' column to watchlist table.")

            # Create required performance indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_trade_date ON trades(trade_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trade_images_trade_id ON trade_images(trade_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_technical_checklists_user_id ON technical_checklists(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_confirmation_checklists_user_id ON confirmation_checklists(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scanner_settings_user_id ON scanner_settings(user_id);"))
            conn.commit()

            # Create dashboard_preferences table manually if not existing
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dashboard_preferences (
                    id UUID PRIMARY KEY,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    selected_symbols JSONB DEFAULT '[]'::jsonb NOT NULL,
                    widget_visibility JSONB DEFAULT '{}'::jsonb NOT NULL,
                    widget_order JSONB DEFAULT '[]'::jsonb NOT NULL,
                    layout_name VARCHAR DEFAULT 'default' NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_dash_pref_user_layout ON dashboard_preferences(user_id, layout_name);"))
            conn.commit()
            logger.info("Database indexes and table migrations completed successfully.")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise e
