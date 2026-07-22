import sys
sys.path.append(r'c:\Users\AJITHKUMAR\Desktop\tradecore\backend')

from app.core.database import SessionLocal
from app.models.models import UserMarketPreferences

db = SessionLocal()
try:
    prefs = db.query(UserMarketPreferences).filter(UserMarketPreferences.user_id == '46e2cf56-341e-4f7f-8206-53096be0af29').first()
    if prefs:
        print("Favorite Symbols:", prefs.favorite_symbols)
    else:
        print("No preferences found!")
finally:
    db.close()
