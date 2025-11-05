"""
Authentication module for Portfolio Tracker Pro
Handles user registration, login, and JWT token management
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status
from logging_config import get_logger

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default

# Users database file
USERS_DB_FILE = "users.json"

class AuthManager:
    """Manages authentication and user operations"""
    
    def __init__(self):
        """Initialize auth manager"""
        self.logger = get_logger(__name__)
        self.users_db = self._load_users()
        # Seed a demo user in dev if no users exist
        try:
            seed_enabled = os.getenv("SEED_DEMO_USER", "true").lower() == "true"
            if seed_enabled and not self.users_db:
                self.logger.info("Seeding demo user 'demo' for development")
                self.create_user("demo", "demo@example.com", "demo1234")
        except Exception as e:
            self.logger.warning(f"Demo user seed skipped: {e}")
    
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        if os.path.exists(USERS_DB_FILE):
            try:
                with open(USERS_DB_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading users: {e}")
                return {}
        return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        try:
            with open(USERS_DB_FILE, 'w') as f:
                json.dump(self.users_db, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving users: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        # Convert to bytes and truncate to 72 bytes if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Hash and return as string
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Convert to bytes and truncate to 72 bytes if necessary
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    def create_user(self, username: str, email: str, password: str) -> Dict:
        """Create a new user"""
        # Check if user already exists
        if username in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        for user in self.users_db.values():
            if user.get("email") == email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "hashed_password": self.hash_password(password),
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        self.users_db[username] = user_data
        
        if not self._save_users():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save user"
            )
        
        return {
            "username": username,
            "email": email,
            "created_at": user_data["created_at"]
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data"""
        user = self.users_db.get(username)
        
        if not user:
            return None
        
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        if not user.get("is_active", True):
            return None
        
        return {
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    
    def create_access_token(self, username: str) -> str:
        """Create a JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": username,  # subject (user identifier)
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return username"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user data by username"""
        user = self.users_db.get(username)
        if not user:
            return None
        
        return {
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "is_active": user.get("is_active", True)
        }

