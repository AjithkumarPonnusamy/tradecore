from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, ScannerSettings, ScannerResult, UserMarketPreferences, ScannerTemplate
from app.schemas.schemas import (
    ScannerSettingsResponse, ScannerSettingsUpdate, ScannerResultBaseResponse,
    ScannerTemplateCreate, ScannerTemplateUpdate, ScannerTemplateResponse
)
from app.services.scanner_engine import ScannerEngine

router = APIRouter(prefix="/scanners", tags=["Market Scanners"])

def matches_alert_preference(scanner_name: str, signal_type: str, prefs: dict) -> bool:
    """
    Checks if a scanner signal matches the user's Telegram Alert preferences.
    """
    if not prefs or not isinstance(prefs, dict):
        return True
        
    scanner_lower = scanner_name.lower()
    signal_lower = signal_type.lower()
    
    # 1. CPR Breakout
    if "cpr breakout" in scanner_lower or ("cpr" in scanner_lower and "breakout" in signal_lower):
        return prefs.get("cpr_breakout", False)
        
    # 2. CPR Reversal
    if "cpr reversal" in scanner_lower or ("cpr" in scanner_lower and ("reversal" in signal_lower or "bounce" in signal_lower or "reject" in signal_lower)):
        return prefs.get("cpr_reversal", False)
        
    # 3. Camarilla Breakout
    if "camarilla breakout" in scanner_lower or ("camarilla" in scanner_lower and "breakout" in signal_lower):
        return prefs.get("camarilla_breakout", False)
        
    # 4. Camarilla Reversal
    if "camarilla bounce" in scanner_lower or "camarilla reversal" in scanner_lower or ("camarilla" in scanner_lower and ("reversal" in signal_lower or "bounce" in signal_lower or "reject" in signal_lower)):
        return prefs.get("camarilla_reversal", False)
        
    # 5. EMA Confirmation
    if "ema trend" in scanner_lower or "ema setup" in scanner_lower or "ema confirmation" in scanner_lower or "ema" in scanner_lower:
        return prefs.get("ema_confirmation", False)
        
    # 6. Daily Buyer Setup
    if "daily buyer" in scanner_lower or "buyer setup" in scanner_lower or "buyer" in signal_lower:
        return prefs.get("daily_buyer_setup", False)
        
    # 7. Daily Seller Setup
    if "daily seller" in scanner_lower or "seller setup" in scanner_lower or "seller" in signal_lower:
        return prefs.get("daily_seller_setup", False)
        
    # 8. Institutional Level Break
    if "institutional" in scanner_lower or "level break" in scanner_lower or "pivot break" in scanner_lower:
        return prefs.get("institutional_level_break", False)
        
    # 9. Custom Alerts
    return prefs.get("custom_alerts", False)

scanner_engine = ScannerEngine()

DEFAULT_SCANNERS = {
    "Forex": [
        "CPR Breakout",
        "CPR Reversal",
        "Camarilla Bounce",
        "Camarilla Breakout",
        "EMA Trend",
        "Fibonacci Confluence"
    ],
    "Indian Market": [
        "Gap Up",
        "Gap Down",
        "CPR Breakout",
        "EMA Setup",
        "Volume Breakout",
        "Momentum Stocks"
    ]
}

def seed_scanner_settings(db: Session, user_id) -> ScannerSettings:
    db_settings = ScannerSettings(
        user_id=user_id,
        enabled_scanners=DEFAULT_SCANNERS,
        telegram_alert_types={
            "cpr_breakout": True,
            "cpr_reversal": True,
            "camarilla_breakout": True,
            "camarilla_reversal": True,
            "ema_confirmation": True,
            "daily_buyer_setup": True,
            "daily_seller_setup": True,
            "institutional_level_break": True,
            "custom_alerts": True
        }
    )
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

@router.get("/settings", response_model=ScannerSettingsResponse)
def get_scanner_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = db.query(ScannerSettings).filter(
        ScannerSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = seed_scanner_settings(db, current_user.id)
        
    return settings

@router.put("/settings", response_model=ScannerSettingsResponse)
def update_scanner_settings(
    settings_in: ScannerSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = db.query(ScannerSettings).filter(
        ScannerSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = seed_scanner_settings(db, current_user.id)
        
    if settings_in.enabled_scanners is not None:
        settings.enabled_scanners = settings_in.enabled_scanners
    if settings_in.telegram_bot_token is not None:
        settings.telegram_bot_token = settings_in.telegram_bot_token
    if settings_in.telegram_chat_id is not None:
        settings.telegram_chat_id = settings_in.telegram_chat_id
    if settings_in.telegram_enabled is not None:
        settings.telegram_enabled = settings_in.telegram_enabled
    if settings_in.telegram_alert_types is not None:
        settings.telegram_alert_types = settings_in.telegram_alert_types
        
    db.commit()
    db.refresh(settings)
    return settings

def execute_scanner_for_user(db: Session, user_id) -> List[ScannerResult]:
    # 1. Get user preferences from the user's Watchlist
    from app.models.models import Watchlist
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    watchlist_items.sort(key=lambda x: (not x.settings.get("pinned", False) if isinstance(x.settings, dict) else True, x.position, x.created_at))
    
    watchlist = []
    symbols_to_scan = []
    for item in watchlist_items:
        s_clean = item.symbol.strip().upper()
        watchlist.append(s_clean)
        symbols_to_scan.append({"symbol": s_clean, "market": item.market})
        
    if not symbols_to_scan:
        return []
        
    # 2. Get user enabled scanners list
    settings = db.query(ScannerSettings).filter(
        ScannerSettings.user_id == user_id
    ).first()
    if not settings:
        settings = seed_scanner_settings(db, user_id)
        
    enabled_list = []
    for mkt_type, list_names in settings.enabled_scanners.items():
        enabled_list.extend(list_names)
        
    results = []
    
    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone, date as date_type
    from sqlalchemy import func as sqlfunc, cast
    from sqlalchemy.types import Date
    import requests
    import html
    
    from concurrent.futures import ThreadPoolExecutor

    def scan_single_item(item):
        try:
            signals = scanner_engine.run_scans_for_symbol(
                item["symbol"], item["market"], enabled_list
            )
            return item, signals, None
        except Exception as e:
            return item, [], e

    with ThreadPoolExecutor(max_workers=min(len(symbols_to_scan), 8)) as executor:
        scan_results = list(executor.map(scan_single_item, symbols_to_scan))

    for item, scan_signals, err in scan_results:
        if err:
            print(f"Error scanning {item['symbol']} in scanners router: {err}")
            continue
        for sig in scan_signals:
            try:
                # --- Resolve trigger timestamp ---
                trigger_val = sig.get("trigger_time")
                trigger_dt = None
                if trigger_val:
                    if isinstance(trigger_val, datetime):
                        trigger_dt = trigger_val
                    elif isinstance(trigger_val, str):
                        try:
                            if trigger_val.endswith("Z"):
                                trigger_val = trigger_val[:-1] + "+00:00"
                            trigger_dt = datetime.fromisoformat(trigger_val)
                        except Exception as e:
                            print(f"Error parsing signal trigger_time {trigger_val}: {e}")
                
                if not trigger_dt:
                    trigger_dt = datetime.now(timezone.utc)
                    
                if trigger_dt.tzinfo is None:
                    trigger_dt = trigger_dt.replace(tzinfo=timezone.utc)
                    
                ist_str = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                ny_str = trigger_dt.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
                
                details_dict = sig.get("details", {})
                if not isinstance(details_dict, dict):
                    details_dict = {"reason": str(details_dict)}
                
                details_dict["time_ist"] = ist_str
                details_dict["time_ny"] = ny_str
 
                # --- Deduplication: check if this signal was already generated today ---
                # A signal is considered the same if it matches on symbol, market, scanner_name,
                # signal_type, AND the date portion of triggered_at (so one alert per signal per day).
                # We fetch all matching results to handle cases where duplicate records already exist historically.
                start_of_day = datetime.combine(trigger_dt.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
                end_of_day = datetime.combine(trigger_dt.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
 
                existing_records = db.query(ScannerResult).filter(
                    ScannerResult.symbol == item["symbol"].upper(),
                    ScannerResult.market == item["market"],
                    ScannerResult.scanner_name == sig["scanner_name"],
                    ScannerResult.signal_type == sig["signal_type"],
                    # Match on range of triggered_at in UTC to allow re-alert next day and avoid local timezone casting mismatch
                    ScannerResult.triggered_at >= start_of_day,
                    ScannerResult.triggered_at <= end_of_day
                ).all()
 
                # Check Watchlist and Alert type preferences server-side
                sym_upper = item["symbol"].upper()
                is_in_watchlist = sym_upper in watchlist
                is_alert_type_enabled = matches_alert_preference(
                    sig["scanner_name"], sig["signal_type"], settings.telegram_alert_types
                )
                
                base_should_send = (
                    settings.telegram_enabled
                    and settings.telegram_bot_token
                    and settings.telegram_chat_id
                    and is_in_watchlist
                    and is_alert_type_enabled
                )

                if existing_records:
                    # Signal was already generated. Check if *any* of the existing records has telegram_sent = True
                    telegram_already_sent = any(r.telegram_sent for r in existing_records)
                    
                    should_send_telegram = base_should_send and not telegram_already_sent
                    if should_send_telegram:
                        is_fx = sym_upper in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"]
                        price_format = f"{float(sig['price']):.4f}" if is_fx else f"{float(sig['price']):.2f}"
                        time_ist_short = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
                        
                        msg = (
                            f"🔔 <b>Trading Alert</b>\n\n"
                            f"<b>Symbol:</b> {sym_upper}\n"
                            f"<b>Setup:</b> {sig['scanner_name']} {sig['signal_type']}\n"
                            f"<b>Price:</b> {price_format}\n"
                            f"<b>Time:</b> {time_ist_short} IST\n\n"
                            f"<a href='http://localhost:3000/dashboard'>Tap to view chart.</a>"
                        )
                        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
                        payload = {
                            "chat_id": settings.telegram_chat_id,
                            "text": msg,
                            "parse_mode": "HTML"
                        }
                        try:
                            res = requests.post(url, json=payload, timeout=8)
                            if res.status_code == 200:
                                # Update all matching records to have telegram_sent = True to remain consistent
                                for r in existing_records:
                                    r.telegram_sent = True
                                    db.add(r)
                                print(f"Telegram sent (delayed): {sym_upper} | {sig['scanner_name']} | {sig['signal_type']}")
                            else:
                                print(f"Failed to send Telegram (delayed), status code: {res.status_code}")
                        except Exception as e:
                            print(f"Error sending Telegram notification (delayed): {e}")
                    results.append(existing_records[0])
                    continue
 
                # --- Send Telegram only if not already sent for this signal today ---
                should_send_telegram = base_should_send
 
                if should_send_telegram:
                    is_fx = sym_upper in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"]
                    price_format = f"{float(sig['price']):.4f}" if is_fx else f"{float(sig['price']):.2f}"
                    time_ist_short = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
                    
                    msg = (
                        f"🔔 <b>Trading Alert</b>\n\n"
                        f"<b>Symbol:</b> {sym_upper}\n"
                        f"<b>Setup:</b> {sig['scanner_name']} {sig['signal_type']}\n"
                        f"<b>Price:</b> {price_format}\n"
                        f"<b>Time:</b> {time_ist_short} IST\n\n"
                        f"<a href='http://localhost:3000/dashboard'>Tap to view chart.</a>"
                    )
                    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
                    payload = {
                        "chat_id": settings.telegram_chat_id,
                        "text": msg,
                        "parse_mode": "HTML"
                    }
                    telegram_sent_success = False
                    try:
                        res = requests.post(url, json=payload, timeout=8)
                        if res.status_code == 200:
                            print(f"Telegram sent: {sym_upper} | {sig['scanner_name']} | {sig['signal_type']}")
                            telegram_sent_success = True
                        else:
                            print(f"Failed to send Telegram, status code: {res.status_code}")
                    except Exception as e:
                        print(f"Error sending Telegram notification: {e}")
                    should_send_telegram = telegram_sent_success
 
                # --- Persist scan result with telegram_sent flag ---
                db_res = ScannerResult(
                    symbol=item["symbol"].upper(),
                    market=item["market"],
                    scanner_name=sig["scanner_name"],
                    timeframe="1d",
                    signal_type=sig["signal_type"],
                    price=sig["price"],
                    confidence_score=sig["confidence_score"],
                    details=details_dict,
                    triggered_at=trigger_dt,
                    telegram_sent=should_send_telegram  # True only on successful dispatch
                )
                db.add(db_res)
                results.append(db_res)
            except Exception as e:
                print(f"Error scanning {item['symbol']} in scanners router: {e}")
            
    # Save all scan results to DB
    try:
        if results:
            db.commit()
            for r in results:
                db.refresh(r)
    except Exception as e:
        db.rollback()
        print(f"Error saving scanner results: {e}")
        
    return results

@router.get("/run", response_model=List[ScannerResultBaseResponse])
def run_scanners(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return execute_scanner_for_user(db, current_user.id)


@router.get("/latest", response_model=List[ScannerResultBaseResponse])
def get_latest_scanners(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models import Watchlist
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    symbols = [item.symbol.upper() for item in watchlist_items]
    if not symbols:
        return []
        
    results = db.query(ScannerResult).filter(
        ScannerResult.symbol.in_(symbols)
    ).order_by(ScannerResult.triggered_at.desc()).limit(20).all()
    
    return results


@router.post("/test-telegram")
def test_telegram_notification(
    config: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    bot_token = config.get("bot_token")
    chat_id = config.get("chat_id")
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="bot_token and chat_id are required")
        
    text = (
        f"🔔 <b>TRADECORE TELEGRAM NOTIFICATION TEST</b> 🔔\n\n"
        f"This is a test notification confirming that your Telegram Bot connection is successfully configured with TradeCore."
    )
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code != 200:
            raise Exception(response.text)
        return {"status": "success", "response": response.json()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Telegram API Error: {str(e)}")


@router.get("/templates", response_model=List[ScannerTemplateResponse])
def list_scanner_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ScannerTemplate).filter(ScannerTemplate.user_id == current_user.id).order_by(ScannerTemplate.created_at.desc()).all()

@router.post("/templates", response_model=ScannerTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_scanner_template(
    template_in: ScannerTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_template = ScannerTemplate(
        user_id=current_user.id,
        name=template_in.name,
        description=template_in.description,
        conditions=template_in.conditions
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/{template_id}", response_model=ScannerTemplateResponse)
def get_scanner_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from uuid import UUID
    template = db.query(ScannerTemplate).filter(
        ScannerTemplate.id == UUID(template_id),
        ScannerTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Scanner template not found")
    return template

@router.put("/templates/{template_id}", response_model=ScannerTemplateResponse)
def update_scanner_template(
    template_id: str,
    template_in: ScannerTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from uuid import UUID
    template = db.query(ScannerTemplate).filter(
        ScannerTemplate.id == UUID(template_id),
        ScannerTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Scanner template not found")
    
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
        
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scanner_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from uuid import UUID
    template = db.query(ScannerTemplate).filter(
        ScannerTemplate.id == UUID(template_id),
        ScannerTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Scanner template not found")
    
    db.delete(template)
    db.commit()
    return None

@router.post("/templates/{template_id}/duplicate", response_model=ScannerTemplateResponse)
def duplicate_scanner_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from uuid import UUID
    template = db.query(ScannerTemplate).filter(
        ScannerTemplate.id == UUID(template_id),
        ScannerTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Scanner template not found")
    
    db_template = ScannerTemplate(
        user_id=current_user.id,
        name=f"{template.name} (Copy)",
        description=template.description,
        conditions=template.conditions
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.post("/templates/{template_id}/run")
def run_custom_scanner_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from uuid import UUID
    import html
    import requests
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    
    template = db.query(ScannerTemplate).filter(
        ScannerTemplate.id == UUID(template_id),
        ScannerTemplate.user_id == current_user.id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Scanner template not found")
        
    # Get user watchlist symbols to scan
    from app.models.models import Watchlist
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    watchlist_items.sort(key=lambda x: (not x.settings.get("pinned", False) if isinstance(x.settings, dict) else True, x.position, x.created_at))
    
    symbols_to_scan = []
    for item in watchlist_items:
        symbols_to_scan.append({"symbol": item.symbol.upper(), "market": item.market})
        
    if not symbols_to_scan:
        return []
        
    # Get user scanner settings for telegram alerts
    settings = db.query(ScannerSettings).filter(
        ScannerSettings.user_id == current_user.id
    ).first()
    
    results = []
    
    for item in symbols_to_scan:
        try:
            eval_res = scanner_engine.evaluate_custom_condition(
                item["symbol"], item["market"], template.conditions
            )
            if eval_res.get("matched", False):
                # We matched! Create a ScannerResult or warning
                trigger_time_val = eval_res.get("time")
                trigger_dt = None
                if trigger_time_val:
                    try:
                        if trigger_time_val.endswith("Z"):
                            trigger_time_val = trigger_time_val[:-1] + "+00:00"
                        trigger_dt = datetime.fromisoformat(trigger_time_val)
                    except:
                        pass
                if not trigger_dt:
                    trigger_dt = datetime.now(timezone.utc)
                    
                if trigger_dt.tzinfo is None:
                    trigger_dt = trigger_dt.replace(tzinfo=timezone.utc)
                    
                ist_str = trigger_dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                ny_str = trigger_dt.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
                
                details_dict = {
                    "reason": eval_res.get("reason", "Condition matches custom scanner setup."),
                    "time_ist": ist_str,
                    "time_ny": ny_str,
                    "rsi": eval_res.get("rsi"),
                    "ema20": eval_res.get("ema20"),
                    "ema50": eval_res.get("ema50"),
                    "cpr": eval_res.get("cpr"),
                    "vwap": eval_res.get("vwap")
                }
                
                # Check for duplication (same symbol, template.name, date)
                start_of_day = datetime.combine(trigger_dt.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
                end_of_day = datetime.combine(trigger_dt.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
                
                existing_records = db.query(ScannerResult).filter(
                    ScannerResult.symbol == item["symbol"].upper(),
                    ScannerResult.market == item["market"],
                    ScannerResult.scanner_name == template.name,
                    ScannerResult.signal_type == "CUSTOM",
                    ScannerResult.triggered_at >= start_of_day,
                    ScannerResult.triggered_at <= end_of_day
                ).all()
                
                if existing_records:
                    results.append(existing_records[0])
                    continue
                    
                # Send telegram if enabled
                telegram_sent_success = False
                if settings and settings.telegram_enabled and settings.telegram_bot_token and settings.telegram_chat_id:
                    reason = details_dict["reason"]
                    reason_escaped = html.escape(reason)
                    msg = (
                        f"🚨 <b>CUSTOM SCANNER TRIGGERED</b> 🚨\n\n"
                        f"<b>Scanner Name:</b> {template.name}\n"
                        f"<b>Symbol:</b> {item['symbol'].upper()}\n"
                        f"<b>Market:</b> {item['market']}\n"
                        f"<b>Trigger Price:</b> {float(eval_res['price']):.4f}\n\n"
                        f"<b>Trigger Time (IST):</b> {ist_str} IST\n"
                        f"<b>Trigger Time (NY):</b> {ny_str} EST\n\n"
                        f"<b>Detailed Analysis:</b> {reason_escaped}"
                    )
                    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
                    payload = {
                        "chat_id": settings.telegram_chat_id,
                        "text": msg,
                        "parse_mode": "HTML"
                    }
                    try:
                        res = requests.post(url, json=payload, timeout=8)
                        if res.status_code == 200:
                            telegram_sent_success = True
                    except Exception as e:
                        print(f"Error sending Telegram notification: {e}")
                        
                db_res = ScannerResult(
                    symbol=item["symbol"].upper(),
                    market=item["market"],
                    scanner_name=template.name,
                    timeframe="1d",
                    signal_type="CUSTOM",
                    price=eval_res["price"],
                    confidence_score=100.0,
                    details=details_dict,
                    triggered_at=trigger_dt,
                    telegram_sent=telegram_sent_success
                )
                db.add(db_res)
                results.append(db_res)
        except Exception as scan_err:
            print(f"Error running custom scan for {item['symbol']}: {scan_err}")
            
    try:
        if results:
            db.commit()
            for r in results:
                try:
                    db.refresh(r)
                except:
                    pass
    except Exception as db_err:
        db.rollback()
        print(f"Error committing custom scanner results: {db_err}")
        
    res_serialized = []
    for r in results:
        res_serialized.append({
            "id": str(r.id) if r.id else "",
            "symbol": r.symbol,
            "market": r.market,
            "scanner_name": r.scanner_name,
            "timeframe": r.timeframe,
            "signal_type": r.signal_type,
            "price": float(r.price) if r.price else None,
            "confidence_score": float(r.confidence_score) if r.confidence_score else None,
            "details": r.details,
            "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
            "telegram_sent": r.telegram_sent,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
        
    return res_serialized

