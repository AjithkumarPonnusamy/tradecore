import os
from sqlalchemy import create_engine, text

db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:ak@localhost:5432/tradecore")
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT symbol, market, live_price, previous_day_high, previous_day_low, previous_day_close, cpr_levels, camarilla_levels FROM market_data"))
    for row in result:
        print("---")
        print("Symbol:", row[0])
        print("Market:", row[1])
        print("Live Price:", row[2])
        print("Prev High:", row[3])
        print("Prev Low:", row[4])
        print("Prev Close:", row[5])
        print("CPR Levels:", row[6])
        print("Camarilla Levels:", row[7])
