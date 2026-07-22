import sys
from datetime import datetime, timezone
sys.path.append(r'c:\Users\AJITHKUMAR\Desktop\tradecore\backend')

from app.services.market_data import PublicMarketDataService
from zoneinfo import ZoneInfo

service = PublicMarketDataService()
print("\nFetching EURUSD candles from TradingView...")
candles = service.get_historical_candles("EURUSD", "Forex", timeframe="1d", period="5d")
if candles:
    latest = candles[-1]
    print("Latest candle:", latest)
    
    # Simulate backend triggers mapping to string representation
    trigger_dt = datetime.fromisoformat(latest["time"])
    ist_str = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    ny_str = trigger_dt.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Target IST: {ist_str}")
    print(f"Target NY : {ny_str}")
    
    # Check that trigger time is in the past compared to current time (with a 24h buffer for active daily candles)
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    trigger_ist = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata"))
    print(f"Current Time (IST): {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")
    from datetime import timedelta
    print(f"Trigger Time is in the past: {trigger_ist < now_ist}")
    assert trigger_ist < now_ist + timedelta(days=1), "Trigger time should be in the past or correspond to the current active daily candle!"
else:
    print("Failed to fetch candles.")
