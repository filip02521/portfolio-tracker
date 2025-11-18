"""
Pytest configuration and shared fixtures for all tests
"""
import pytest
import os
import sys
from typing import Generator

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def test_data_dir() -> str:
    """Returns the test data directory path"""
    return os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture
def mock_env_vars(monkeypatch) -> Generator[None, None, None]:
    """Mock environment variables for testing"""
    # Set test environment variables
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    monkeypatch.setenv("SEED_DEMO_USER", "false")  # Don't seed demo user in tests
    
    yield
    
    # Cleanup after test

@pytest.fixture
def temp_users_db(tmp_path, monkeypatch) -> Generator[str, None, None]:
    """Create a temporary users.json file for testing"""
    users_file = tmp_path / "users.json"
    monkeypatch.setenv("USERS_DB_FILE", str(users_file))
    yield str(users_file)
    # Cleanup handled by tmp_path

@pytest.fixture
def temp_transactions_db(tmp_path, monkeypatch) -> Generator[str, None, None]:
    """Create a temporary transaction_history.json file for testing"""
    tx_file = tmp_path / "transaction_history.json"
    monkeypatch.setenv("TRANSACTION_HISTORY_FILE", str(tx_file))
    yield str(tx_file)














