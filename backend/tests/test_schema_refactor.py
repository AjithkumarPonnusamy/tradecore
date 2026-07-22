"""
Unit tests verifying the schema refactoring:
1. UserOAuthAccount separation and dynamic backward-compatible properties on User model.
2. Normalized Trade columns (r_multiple, holding_minutes, confidence_rating).
"""

import pytest
from datetime import datetime, timezone
from app.models.models import User, UserOAuthAccount, Trade, Strategy


class TestUserOAuthAccountRefactoring:
    def test_user_oauth_account_creation_and_properties(self):
        user = User(
            email="trader_oauth@tradecore.io",
            full_name="Jane Trader",
            auth_provider="GOOGLE"
        )
        
        # Test backward-compatible getter before OAuth account exists
        assert user.google_account is None
        assert user.google_access_token is None
        assert user.google_drive_connected is False
        assert user.has_google_client_secret is False
        
        # Add OAuth account via helper setter
        user.google_access_token = "mock_access_token_123"
        user.google_refresh_token = "mock_refresh_token_456"
        user.google_client_id = "client_id_789"
        user.google_client_secret = "secret_abc"
        user.google_drive_folder_id = "folder_xyz"
        
        # Verify OAuth account relationship was populated
        assert len(user.oauth_accounts) == 1
        oauth_acc = user.oauth_accounts[0]
        assert oauth_acc.provider == "google"
        assert oauth_acc.access_token == "mock_access_token_123"
        assert oauth_acc.refresh_token == "mock_refresh_token_456"
        
        # Verify dynamic property getters match
        assert user.google_access_token == "mock_access_token_123"
        assert user.google_refresh_token == "mock_refresh_token_456"
        assert user.google_client_id == "client_id_789"
        assert user.google_client_secret == "secret_abc"
        assert user.google_drive_folder_id == "folder_xyz"
        assert user.google_drive_connected is True
        assert user.has_google_client_secret is True


class TestTradeNormalizationRefactoring:
    def test_trade_normalized_fields(self):
        trade = Trade(
            market="Forex",
            symbol="XAUUSD",
            direction="BUY",
            entry_price=2000.50,
            quantity=1.0,
            r_multiple=2.5,
            holding_minutes=45,
            confidence_rating=8
        )
        
        assert trade.r_multiple == 2.5
        assert trade.holding_minutes == 45
        assert trade.confidence_rating == 8
        assert trade.symbol == "XAUUSD"
