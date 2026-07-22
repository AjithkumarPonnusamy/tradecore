import re

# Comprehensive map of common speech-to-text mishearings to standard capitalized trading terms
HEURISTIC_CORRECTIONS = {
    # Symbols & Instruments
    r"\bgold\b": "XAUUSD",
    r"\bxau\s*usd\b": "XAUUSD",
    r"\bex\s*au\s*usd\b": "XAUUSD",
    r"\bexauusd\b": "XAUUSD",
    r"\bnifty\s*fifty\b": "NIFTY",
    r"\bnifty\s*50\b": "NIFTY",
    r"\bnifty\b": "NIFTY",
    r"\bbank\s*nifty\b": "BANKNIFTY",
    r"\bbanknifty\b": "BANKNIFTY",
    r"\bfin\s*nifty\b": "FINNIFTY",
    r"\bfinnifty\b": "FINNIFTY",
    r"\beur\s*usd\b": "EURUSD",
    r"\beurusd\b": "EURUSD",
    r"\beuro\s*usd\b": "EURUSD",
    r"\bgbp\s*usd\b": "GBPUSD",
    r"\bgbpusd\b": "GBPUSD",
    r"\bcable\b": "GBPUSD",
    r"\bpound\s*usd\b": "GBPUSD",
    r"\bnasdaq\s*100\b": "NASDAQ",
    r"\bnasdaq\b": "NASDAQ",
    r"\bspx\s*500\b": "SPX",
    r"\bs\s*&\s*p\s*(?:500)?\b": "SPX",
    r"\bs\s*and\s*p\s*(?:500)?\b": "SPX",
    r"\bspx\b": "SPX",
    r"\bbitcoin\b": "BTCUSD",
    
    # Technical Concepts & Indicators
    r"\bcpr\b": "CPR",
    r"\bcentral\s*pivot\s*range\b": "CPR",
    r"\bcamarilla\b": "Camarilla",
    r"\bcam\b": "Camarilla",
    r"\bvwap\b": "VWAP",
    r"\bv\s*wap\b": "VWAP",
    r"\bv-wap\b": "VWAP",
    r"\bema\b": "EMA",
    r"\bexponential\s*moving\s*average\b": "EMA",
    r"\batr\b": "ATR",
    r"\baverage\s*true\s*range\b": "ATR",
    r"\bbreak\s*out\b": "Breakout",
    r"\bbreakout\b": "Breakout",
    r"\bre\s*test\b": "Retest",
    r"\bretest\b": "Retest",
    r"\bsupport\b": "Support",
    r"\bresistance\b": "Resistance",
    r"\bswing\s*high\b": "Swing High",
    r"\bswing\s*low\b": "Swing Low",
    r"\brisk\s*(?:to)?\s*reward\b": "Risk Reward",
    r"\br\s*to\s*r\b": "Risk Reward",
    r"\brr\b": "Risk Reward",
    
    # Trade Variables
    r"\bstop\s*loss\b": "Stop Loss",
    r"\bstop-loss\b": "Stop Loss",
    r"\bstop\s*losses\b": "Stop Loss",
    r"\bsl\b": "Stop Loss",
    r"\btarget\b": "Target",
    r"\bprofit\s*target\b": "Target",
    r"\btp\b": "Target",
    r"\bliquidity\b": "Liquidity",
    r"\bliquidation\b": "Liquidity",
    
    # Directions
    r"\bshort\b": "SELL",
    r"\blong\b": "BUY"
}

def heuristic_correct(transcript: str) -> str:
    """
    Applies regex-based replacement dictionary to clean up trading terms.
    Runs case-insensitively and maps phonetics to strict trading terminology.
    """
    if not transcript:
        return ""
        
    corrected = transcript
    for pattern, replacement in HEURISTIC_CORRECTIONS.items():
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
    return corrected

def heuristic_extract(transcript: str) -> dict:
    """
    Extracts structured trading data using regex and keyword matching when LLMs are unavailable.
    Supports all 13 voice journaling fields.
    """
    transcript_upper = transcript.upper()
    
    # 1. Direction
    direction = None
    if any(w in transcript_upper for w in ["BUY", "BOUGHT", "LONG", "CALL"]):
        direction = "BUY"
    elif any(w in transcript_upper for w in ["SELL", "SOLD", "SHORT", "PUT"]):
        direction = "SELL"
        
    # 2. Symbol / Instrument
    symbol = None
    known_symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "AUDUSD", "NZDUSD", 
                     "NIFTY", "BANKNIFTY", "FINNIFTY", "BTCUSD", "ETHUSD", "NASDAQ", "SPX"]
    for s in known_symbols:
        if s in transcript_upper:
            symbol = s
            break
            
    if not symbol:
        matches = re.findall(r'\b[A-Z]{3,10}\b', transcript)
        for m in matches:
            if m not in ["TODAY", "YESTERDAY", "MARKET", "STOP", "LOSS", "TARGET", "PRICE", "ENTRY", "EXIT", "TRADE", "CPR", "VWAP", "EMA", "ATR"]:
                symbol = m
                break

    # 3. Strategy
    strategy = None
    if "CPR" in transcript_upper:
        strategy = "CPR Reversal" if "BOUNCE" in transcript_upper or "REJECT" in transcript_upper else "CPR Strategy"
    elif "ORB" in transcript_upper or "OPENING RANGE" in transcript_upper:
        strategy = "Opening Range Breakout"
    elif "VWAP" in transcript_upper:
        strategy = "VWAP Pullback"
    elif "ENGULFING" in transcript_upper:
        strategy = "Bullish Engulfing" if direction == "BUY" else "Bearish Engulfing"
    elif "SUPPORT" in transcript_upper or "RESISTANCE" in transcript_upper:
        strategy = "Support/Resistance Bounce"
    else:
        strategy = "Discretionary"

    # 4. Setup
    setup = strategy

    # 5. Market
    market = "Crypto" if symbol and ("BTC" in symbol or "ETH" in symbol) else \
             "Indian Market" if symbol and any(x in symbol for x in ["NIFTY", "BANK", "FIN"]) else \
             "Forex" if symbol and any(x in symbol for x in ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "XAU"]) else \
             "US Market"

    # 6. Prices
    entry_price = None
    stop_loss = None
    target_price = None
    exit_price = None

    def find_number_near(text, keywords, window=50):
        text_lower = text.lower()
        
        # Find first keyword match position
        kw_idx = -1
        matched_kw = ""
        for kw in keywords:
            kw_idx = text_lower.find(kw)
            if kw_idx != -1:
                matched_kw = kw
                break
                
        if kw_idx == -1:
            return None
            
        # Find all numbers (ints/floats) in the text
        matches = list(re.finditer(r'\d+(?:\.\d+)?', text))
        if not matches:
            return None
            
        closest_num = None
        min_distance = float('inf')
        
        for match in matches:
            num_start = match.start()
            num_val = float(match.group())
            
            # Only look for numbers that come after the keyword (standard parameter declaration order)
            if num_start >= kw_idx:
                dist = num_start - (kw_idx + len(matched_kw))
                if dist < min_distance and dist <= window:
                    min_distance = dist
                    closest_num = num_val
                
        return closest_num

    entry_price = find_number_near(transcript, ["entry", "entered at", "entered", "bought at", "bought", "sold at", "sold", "price of"])
    stop_loss = find_number_near(transcript, ["stop loss", "stoploss", "sl", "risk"])
    target_price = find_number_near(transcript, ["target", "tp", "take profit", "profit target"])
    exit_price = find_number_near(transcript, ["exit", "exited at", "closed at", "out at"])

    # 7. Entry Reason & Exit Reason
    entry_reason = "Bounced or broke key level matching setup" if any(x in transcript_upper for x in ["SUPPORT", "RESISTANCE", "CPR", "VWAP", "EMA"]) else None
    exit_reason = "Hit exit criteria or emotional exit" if any(x in transcript_upper for x in ["EXIT", "CLOSE", "OUT", "TARGET", "STOP"]) else None

    # 8. Trade Management
    trade_management = "Held to Target/Stop Loss"
    if any(w in transcript_upper for w in ["TRAIL", "TRAILING", "MOVE STOP", "MOVE SL"]):
        trade_management = "Trailing Stop Loss"
    elif any(w in transcript_upper for w in ["BREAK EVEN", "BREAKEVEN", "BE"]):
        trade_management = "Move to Break-Even"
    elif any(w in transcript_upper for w in ["SCALE OUT", "SCALED OUT", "PARTIAL"]):
        trade_management = "Partial Profit Booking"
    elif any(w in transcript_upper for w in ["EARLY EXIT", "CLOSED EARLY", "BEFORE TARGET"]):
        trade_management = "Manual Early Exit"

    # 9. Emotions
    emotions = []
    emotion_keywords = {
        "Fear": ["FEAR", "AFRAID", "SCARED", "NERVOUS", "PANIC", "WORRIED"],
        "Greed": ["GREED", "WANT MORE", "CHASING"],
        "FOMO": ["FOMO", "MISSED", "FEAR OF MISSING OUT", "JUMPED IN"],
        "Confidence": ["CONFIDENT", "SURE", "CONVICTION", "STRONG"],
        "Patience": ["PATIENT", "WAITED", "WAITING"],
        "Revenge Trading": ["REVENGE", "RECOVER", "GET BACK", "ANGRY"],
        "Hesitation": ["HESITAT", "DOUBT", "UNSURE", "DELAY"],
        "Discipline": ["DISCIPLINE", "FOLLOWED PLAN", "RULE"]
    }
    for emotion, keywords in emotion_keywords.items():
        if any(kw in transcript_upper for kw in keywords):
            emotions.append(emotion)
    if not emotions:
        emotions = ["Hesitation"]

    # 10. Mistakes
    mistakes = []
    if "EARLY" in transcript_upper and "EXIT" in transcript_upper:
        mistakes.append("Early Exit")
    if "CHASE" in transcript_upper or "CHASING" in transcript_upper:
        mistakes.append("Chasing the Market")
    if "WIDE" in transcript_upper and "STOP" in transcript_upper:
        mistakes.append("Too Wide Stop Loss")
    if "REVENGE" in transcript_upper:
        mistakes.append("Revenge Trading")
    if not mistakes:
        mistakes = ["None detected"]

    # 11. Lessons
    lessons = []
    if "PATIENT" in transcript_upper or "WAIT" in transcript_upper:
        lessons.append("Wait for confirmation setups")
    if "PLAN" in transcript_upper:
        lessons.append("Follow the trading plan strictly")
    if "EMOTION" in transcript_upper or "NERVOUS" in transcript_upper:
        lessons.append("Manage emotional reactions during active trades")
    if not lessons:
        lessons = ["Stick to the strategy rules"]

    summary = f"A {direction or ''} trade on {symbol or 'unknown instrument'} using {strategy or 'discretionary'} setup."
    strengths = "Execution matching technical setups" if symbol else "Self-reflection in trading journal"
    lessons_learned = lessons[0] if lessons else "Follow risk management rules"

    return {
        "instrument": symbol,  # fallback compat
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target_price": target_price,  # fallback compat
        "target": target_price,
        "exit_price": exit_price,
        "strategy": strategy,
        "setup": setup,
        "market": market,
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "trade_management": trade_management,
        "emotions": emotions,
        "emotion_confidence": 0.70,
        "mistakes": mistakes,
        "lessons": lessons,
        "lessons_learned": lessons_learned,
        "summary": summary,
        "strengths": strengths
    }
