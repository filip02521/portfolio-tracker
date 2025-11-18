"""
Tests for authentication module
"""
import pytest
import os
import json
from auth import AuthManager

class TestAuthManager:
    """Test suite for AuthManager"""
    
    def test_create_user(self, tmp_path, monkeypatch):
        """Test user creation"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        
        user = auth_manager.create_user("testuser", "test@example.com", "password123")
        
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert "created_at" in user
        
        # Check that user was saved to file
        assert users_file.exists()
        with open(users_file, 'r') as f:
            users_data = json.load(f)
            assert "testuser" in users_data
            assert "hashed_password" in users_data["testuser"]
            assert users_data["testuser"]["hashed_password"] != "password123"  # Should be hashed
    
    def test_create_duplicate_user(self, tmp_path, monkeypatch):
        """Test creating a duplicate user fails"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Try to create duplicate
        with pytest.raises(Exception):  # Should raise error
            auth_manager.create_user("testuser", "test2@example.com", "password456")
    
    def test_verify_password(self, tmp_path, monkeypatch):
        """Test password verification"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        # Get hashed password from file
        with open(users_file, 'r') as f:
            users_data = json.load(f)
            hashed_password = users_data["testuser"]["hashed_password"]
        
        # Correct password
        assert auth_manager.verify_password("password123", hashed_password) is True
        
        # Wrong password
        assert auth_manager.verify_password("wrongpassword", hashed_password) is False
    
    def test_create_access_token(self, tmp_path, monkeypatch):
        """Test JWT token generation"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        token = auth_manager.create_access_token("testuser")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self, tmp_path, monkeypatch):
        """Test JWT token verification"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        token = auth_manager.create_access_token("testuser")
        username = auth_manager.verify_token(token)
        
        assert username == "testuser"
        
        # Invalid token
        assert auth_manager.verify_token("invalid.token.here") is None
        
        # Empty token
        assert auth_manager.verify_token("") is None
    
    def test_get_user(self, tmp_path, monkeypatch):
        """Test getting user by username"""
        users_file = tmp_path / "users.json"
        monkeypatch.setattr("auth.USERS_DB_FILE", str(users_file))
        
        auth_manager = AuthManager()
        auth_manager.create_user("testuser", "test@example.com", "password123")
        
        user = auth_manager.get_user("testuser")
        
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        
        # Non-existent user
        assert auth_manager.get_user("nonexistent") is None

