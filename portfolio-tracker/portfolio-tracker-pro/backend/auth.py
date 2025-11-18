"""
Authentication module for Portfolio Tracker Pro
Handles user registration, login, and JWT token management
Now uses SQLite database instead of JSON file
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status
from logging_config import get_logger
from database import get_db

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default

class AuthManager:
    """Manages authentication and user operations"""
    
    def __init__(self):
        """Initialize auth manager"""
        self.logger = get_logger(__name__)
        # Seed a demo user in dev if no users exist
        try:
            seed_enabled = os.getenv("SEED_DEMO_USER", "true").lower() == "true"
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                count = cursor.fetchone()[0]
                if seed_enabled and count == 0:
                    self.logger.info("Seeding demo user 'demo' for development")
                    try:
                        self.create_user("demo", "demo@example.com", "demo1234")
                    except HTTPException:
                        # User might already exist
                        pass
        except Exception as e:
            self.logger.warning(f"Demo user seed skipped: {e}")
    
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
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            
            # Check if email already exists
            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user
            now = datetime.utcnow().isoformat()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, self.hash_password(password), 1, now, now))
            conn.commit()
        
        return {
            "username": username,
            "email": email,
            "created_at": now
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, password_hash, is_active, created_at FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            if not self.verify_password(password, row['password_hash']):
                return None
            
            if not row['is_active']:
                return None
            
            return {
                "username": row['username'],
                "email": row['email'],
                "created_at": row['created_at']
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
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email, is_active, created_at FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "username": row['username'],
                "email": row['email'],
                "created_at": row['created_at'],
                "is_active": bool(row['is_active'])
            }
    
    def update_user(self, username: str, updates: Dict) -> Optional[Dict]:
        """Update user data"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if not cursor.fetchone():
                return None
            
            # Build update query
            update_fields = []
            update_values = []
            
            if "email" in updates:
                # Check if email is already taken by another user
                cursor.execute('SELECT username FROM users WHERE email = ? AND username != ?', (updates["email"], username))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
                update_fields.append("email = ?")
                update_values.append(updates["email"])
            
            if "password" in updates:
                update_fields.append("password_hash = ?")
                update_values.append(self.hash_password(updates["password"]))
            
            if "is_active" in updates:
                update_fields.append("is_active = ?")
                update_values.append(1 if updates["is_active"] else 0)
            
            if update_fields:
                update_fields.append("updated_at = ?")
                update_values.append(datetime.utcnow().isoformat())
                update_values.append(username)
                
                cursor.execute(f'''
                    UPDATE users SET {', '.join(update_fields)}
                    WHERE username = ?
                ''', update_values)
                conn.commit()
        
        return self.get_user(username)
