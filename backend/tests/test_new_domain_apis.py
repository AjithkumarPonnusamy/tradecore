"""
Unit tests for new Research and System domain API handlers
"""

import pytest
from app.main import root

def test_root_endpoint_schemas():
    data = root()
    assert data["status"] == "online"
    assert "schemas" in data
    assert len(data["schemas"]) == 9
    assert "identity" in data["schemas"]
    assert "market" in data["schemas"]
    assert "research" in data["schemas"]
    assert "system" in data["schemas"]
