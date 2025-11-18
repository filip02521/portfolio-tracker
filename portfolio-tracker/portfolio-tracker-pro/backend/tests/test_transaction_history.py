"""
Tests for transaction history module
"""
import pytest
import json
from transaction_history import TransactionHistory
import os

class TestTransactionHistory:
    """Test suite for TransactionHistory"""
    
    def test_add_transaction(self, tmp_path):
        """Test adding a transaction"""
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))
        
        tx = tx_history.add_transaction(
            exchange="binance",
            asset="BTC",
            amount=0.5,
            price_usd=50000,
            transaction_type="buy",
            date="2024-01-01T00:00:00Z"
        )
        
        assert tx is not None
        assert tx["exchange"] == "binance"
        assert tx["asset"] == "BTC"
        assert tx["amount"] == 0.5
        assert tx["price_usd"] == 50000
        assert tx["type"] == "buy"
        assert "id" in tx
    
    def test_get_all_transactions(self, tmp_path):
        """Test getting all transactions"""
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))
        
        # Add multiple transactions
        tx_history.add_transaction("binance", "BTC", 0.5, 50000, "buy")
        tx_history.add_transaction("binance", "ETH", 2.0, 3000, "buy")
        
        all_tx = tx_history.get_all_transactions()
        assert len(all_tx) == 2
    
    def test_delete_transaction(self, tmp_path):
        """Test deleting a transaction"""
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))
        
        tx1 = tx_history.add_transaction("binance", "BTC", 0.5, 50000, "buy")
        tx2 = tx_history.add_transaction("binance", "ETH", 2.0, 3000, "buy")
        
        tx_history.delete_transaction(tx1["id"])
        
        all_tx = tx_history.get_all_transactions()
        assert len(all_tx) == 1
        assert all_tx[0]["id"] == tx2["id"]
    
    def test_update_transaction(self, tmp_path):
        """Test updating a transaction"""
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))
        
        tx = tx_history.add_transaction("binance", "BTC", 0.5, 50000, "buy")
        
        success = tx_history.update_transaction(tx["id"], amount=0.75, price_usd=55000)
        assert success is True
        
        updated_tx = tx_history.get_all_transactions()[0]
        assert updated_tx["amount"] == 0.75
        assert updated_tx["price_usd"] == 55000
        assert updated_tx["value_usd"] == 0.75 * 55000
    
    def test_get_transactions_for_asset(self, tmp_path):
        """Test getting transactions for specific asset"""
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))
        
        tx_history.add_transaction("binance", "BTC", 0.5, 50000, "buy")
        tx_history.add_transaction("binance", "ETH", 2.0, 3000, "buy")
        tx_history.add_transaction("binance", "BTC", 0.2, 52000, "sell")
        
        btc_txs = tx_history.get_transactions_for_asset("binance", "BTC")
        assert len(btc_txs) == 2
        assert all(tx["asset"] == "BTC" for tx in btc_txs)

    def test_add_transaction_normalizes_fields(self, tmp_path):
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))

        tx = tx_history.add_transaction(
            exchange="Binance",
            asset="eth",
            amount=1.25,
            price_usd=1800.12,
            transaction_type="BUY",
            commission=-0.0,
            commission_currency="usd",
            isin="us0378331005",
            asset_name=" Ethereum  "
        )

        assert tx["exchange"] == "Binance"
        assert tx["asset"] == "ETH"
        assert tx["type"] == "buy"
        assert tx["commission"] == 0.0
        assert tx["commission_currency"] == "usd"
        assert tx["isin"] == "US0378331005"
        assert tx["asset_name"] == "Ethereum"

    def test_add_transaction_rejects_invalid_values(self, tmp_path):
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))

        with pytest.raises(ValueError):
            tx_history.add_transaction("binance", "BTC", 0, 10000, "buy")
        with pytest.raises(ValueError):
            tx_history.add_transaction("binance", "BTC", 1, -10000, "buy")
        with pytest.raises(ValueError):
            tx_history.add_transaction("binance", "BTC", 1, 10000, "hold")

    def test_transaction_ids_remain_unique_after_deletes(self, tmp_path):
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))

        tx1 = tx_history.add_transaction("binance", "BTC", 0.5, 50000, "buy")
        tx2 = tx_history.add_transaction("binance", "ETH", 2.0, 3000, "buy")
        tx3 = tx_history.add_transaction("binance", "SOL", 10, 20, "buy")

        tx_history.delete_transaction(tx2["id"])
        tx4 = tx_history.add_transaction("binance", "ADA", 100, 0.25, "buy")

        ids = {tx["id"] for tx in tx_history.get_all_transactions()}
        assert len(ids) == 3
        assert tx1["id"] in ids
        assert tx3["id"] in ids
        assert tx4["id"] in ids
        assert tx4["id"] > max(tx1["id"], tx3["id"])

    def test_build_transaction_key_normalizes_input(self, tmp_path):
        tx_file = tmp_path / "transaction_history.json"
        tx_history = TransactionHistory(str(tx_file))

        key = tx_history.build_transaction_key(
            exchange="Binance",
            asset="eth",
            transaction_type="BUY",
            amount=1.234567890123,
            price_usd=987.6543210987,
            date="2024-01-01T10:00:00Z",
        )

        assert key[0] == "binance"
        assert key[1] == "ETH"
        assert key[2] == "buy"
        assert key[3] == round(1.234567890123, 8)
        assert key[4] == round(987.6543210987, 8)
        assert key[5] == "2024-01-01"










