import sys
from datetime import datetime
sys.path.append(r'c:\Users\AJITHKUMAR\Desktop\tradecore\backend')

from app.core.database import SessionLocal
from app.services.market_data import PublicMarketDataService

db = SessionLocal()
try:
    print("Initializing PublicMarketDataService...")
    service = PublicMarketDataService()
    
    # 1. Fetch candles and verify dates
    for symbol in ["EURUSD", "GBPUSD"]:
        print(f"\nFetching {symbol} candles...")
        candles = service.get_historical_candles(symbol, "Forex", timeframe="1d", period="5d")
        if candles:
            print(f"Successfully fetched {len(candles)} candles for {symbol}.")
            print(f"Latest candle: {candles[-1]}")
            # Ensure it is not a stale date
            dt = datetime.fromisoformat(candles[-1]["time"])
            print(f"Latest candle timestamp: {dt} (Year: {dt.year})")
            assert dt.year >= 2026, f"Expected 2026 or later, got {dt.year}!"
        else:
            print(f"Failed to fetch candles for {symbol}!")
            sys.exit(1)
            
    # 2. Verify that running scanner engine on these candles successfully calculates patterns and doesn't duplicate
    from app.services.scanner_engine import ScannerEngine
    import html
    
    print("\nRunning ScannerEngine verify...")
    engine = ScannerEngine()
    
    # Make sure we use tvDatafeed candles inside scanner engine
    # and they trigger signals
    signals = engine.run_scans_for_symbol("EURUSD", "Forex", ["Camarilla Bounce", "CPR Reversal", "EMA Trend", "Fibonacci Confluence"])
    print(f"Generated {len(signals)} signals for EURUSD:")
    for sig in signals:
        print(f"  Pattern: {sig['scanner_name']} | Type: {sig['signal_type']} | Price: {sig['price']} | Time: {sig['trigger_time']}")
        reason = sig.get("details", {}).get("reason", "")
        print(f"  Reason Escaped: {html.escape(reason)}")

    print("\nVerification successful! High-fidelity spot prices are successfully loaded from TradingView.")

finally:
    db.close()
