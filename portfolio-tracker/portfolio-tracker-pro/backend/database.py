"""
Database initialization and management for Portfolio Tracker
Uses SQLite for simplicity - can be migrated to PostgreSQL later if needed
"""
import sqlite3
import os
import json
from typing import Optional, Dict, Any
from contextlib import contextmanager

DB_PATH = os.getenv('DATABASE_PATH', 'portfolio_tracker.db')

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL,
                asset TEXT NOT NULL,
                amount REAL NOT NULL,
                price_usd REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('buy', 'sell')),
                date TEXT NOT NULL,
                value_usd REAL NOT NULL,
                commission REAL DEFAULT 0.0,
                commission_currency TEXT DEFAULT 'USD',
                isin TEXT,
                asset_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                UNIQUE(exchange, asset, date, type, amount, price_usd)
            )
        ''')
        
        # Watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                categories TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, symbol)
            )
        ''')
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                target_value REAL,
                target_percentage REAL,
                target_date TEXT,
                start_date TEXT NOT NULL,
                start_value REAL NOT NULL,
                current_value REAL NOT NULL,
                progress REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                milestones TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TEXT NOT NULL,
                value_usd REAL NOT NULL,
                value_pln REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_exchange_asset ON transactions(exchange, asset)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_history_user_id ON portfolio_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_history_timestamp ON portfolio_history(timestamp)')
        
        conn.commit()
        print(f"Database initialized at {DB_PATH}")

def migrate_json_to_db(json_file: str = 'transaction_history.json'):
    """Migrate transactions from JSON file to database"""
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}, skipping migration")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we already have transactions
        cursor.execute('SELECT COUNT(*) FROM transactions')
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} transactions, skipping migration")
            return
        
        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                transactions = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return
        
        if not transactions:
            print("JSON file is empty, nothing to migrate")
            return
        
        # Insert transactions
        migrated = 0
        for tx in transactions:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO transactions (
                        id, exchange, asset, amount, price_usd, type, date,
                        value_usd, commission, commission_currency, isin, asset_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx.get('id'),
                    tx.get('exchange'),
                    tx.get('asset'),
                    tx.get('amount'),
                    tx.get('price_usd'),
                    tx.get('type'),
                    tx.get('date'),
                    tx.get('value_usd'),
                    tx.get('commission', 0.0),
                    tx.get('commission_currency', 'USD'),
                    tx.get('isin'),
                    tx.get('asset_name'),
                ))
                if cursor.rowcount > 0:
                    migrated += 1
            except Exception as e:
                print(f"Error migrating transaction {tx.get('id')}: {e}")
                continue
        
        conn.commit()
        print(f"Migrated {migrated} transactions from {json_file} to database")

def migrate_watchlist_to_db(json_file: str = 'watchlist.json'):
    """Migrate watchlist from JSON file to database"""
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}, skipping migration")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we already have watchlist data
        cursor.execute('SELECT COUNT(*) FROM watchlist')
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} watchlist entries, skipping migration")
            return
        
        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                watchlist_data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return
        
        if not watchlist_data:
            print("JSON file is empty, nothing to migrate")
            return
        
        # Insert watchlist entries
        migrated = 0
        for username, user_data in watchlist_data.items():
            if isinstance(user_data, list):
                # Old format: List[str]
                symbols = user_data
                metadata = {symbol: {"categories": [], "tags": []} for symbol in symbols}
            else:
                # New format: Dict with symbols and metadata
                symbols = user_data.get("symbols", [])
                metadata = user_data.get("metadata", {})
            
            for symbol in symbols:
                try:
                    symbol_meta = metadata.get(symbol, {})
                    categories = json.dumps(symbol_meta.get("categories", []))
                    tags = json.dumps(symbol_meta.get("tags", []))
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO watchlist (user_id, symbol, categories, tags)
                        VALUES (?, ?, ?, ?)
                    ''', (username, symbol.upper(), categories, tags))
                    if cursor.rowcount > 0:
                        migrated += 1
                except Exception as e:
                    print(f"Error migrating watchlist entry {username}/{symbol}: {e}")
                    continue
        
        conn.commit()
        print(f"Migrated {migrated} watchlist entries from {json_file} to database")

def migrate_goals_to_db(json_file: str = 'goals.json'):
    """Migrate goals from JSON file to database"""
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}, skipping migration")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we already have goals
        cursor.execute('SELECT COUNT(*) FROM goals')
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} goals, skipping migration")
            return
        
        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                goals = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return
        
        if not goals:
            print("JSON file is empty, nothing to migrate")
            return
        
        # Insert goals
        migrated = 0
        for goal in goals:
            try:
                milestones_json = json.dumps(goal.get('milestones', []))
                cursor.execute('''
                    INSERT OR IGNORE INTO goals (
                        id, user_id, title, type, target_value, target_percentage,
                        target_date, start_date, start_value, current_value,
                        progress, status, milestones, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    goal.get('id'),
                    goal.get('user_id'),
                    goal.get('title'),
                    goal.get('type'),
                    goal.get('target_value'),
                    goal.get('target_percentage'),
                    goal.get('target_date'),
                    goal.get('start_date'),
                    goal.get('start_value'),
                    goal.get('current_value'),
                    goal.get('progress', 0.0),
                    goal.get('status', 'active'),
                    milestones_json,
                    goal.get('created_at'),
                    goal.get('updated_at'),
                ))
                if cursor.rowcount > 0:
                    migrated += 1
            except Exception as e:
                print(f"Error migrating goal {goal.get('id')}: {e}")
                continue
        
        conn.commit()
        print(f"Migrated {migrated} goals from {json_file} to database")

def migrate_portfolio_history_to_db(json_file: str = 'portfolio_history.json'):
    """Migrate portfolio history from JSON file to database"""
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}, skipping migration")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we already have portfolio history
        cursor.execute('SELECT COUNT(*) FROM portfolio_history')
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} portfolio history entries, skipping migration")
            return
        
        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return
        
        if not history:
            print("JSON file is empty, nothing to migrate")
            return
        
        # Insert portfolio history entries
        migrated = 0
        for entry in history:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO portfolio_history (user_id, timestamp, value_usd, value_pln)
                    VALUES (?, ?, ?, ?)
                ''', (
                    None,  # user_id is None for legacy data
                    entry.get('timestamp'),
                    entry.get('value_usd'),
                    entry.get('value_pln'),
                ))
                if cursor.rowcount > 0:
                    migrated += 1
            except Exception as e:
                print(f"Error migrating portfolio history entry: {e}")
                continue
        
        conn.commit()
        print(f"Migrated {migrated} portfolio history entries from {json_file} to database")

def migrate_users_to_db(json_file: str = 'users.json'):
    """Migrate users from JSON file to database"""
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}, skipping migration")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we already have users
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Database already contains {count} users, skipping migration")
            return
        
        # Load JSON file
        try:
            with open(json_file, 'r') as f:
                users = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return
        
        if not users:
            print("JSON file is empty, nothing to migrate")
            return
        
        # Insert users
        migrated = 0
        for username, user_data in users.items():
            try:
                is_active = 1 if user_data.get('is_active', True) else 0
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, email, password_hash, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_data.get('username', username),
                    user_data.get('email'),
                    user_data.get('hashed_password'),
                    is_active,
                    user_data.get('created_at'),
                ))
                if cursor.rowcount > 0:
                    migrated += 1
            except Exception as e:
                print(f"Error migrating user {username}: {e}")
                continue
        
        conn.commit()
        print(f"Migrated {migrated} users from {json_file} to database")

def get_migration_status() -> Dict[str, Any]:
    """Get migration status for all data types"""
    status = {
        'transactions': {'migrated': False, 'count': 0},
        'watchlist': {'migrated': False, 'count': 0},
        'goals': {'migrated': False, 'count': 0},
        'portfolio_history': {'migrated': False, 'count': 0},
        'users': {'migrated': False, 'count': 0},
    }
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check transactions
        cursor.execute('SELECT COUNT(*) FROM transactions')
        status['transactions']['count'] = cursor.fetchone()[0]
        status['transactions']['migrated'] = status['transactions']['count'] > 0
        
        # Check watchlist
        cursor.execute('SELECT COUNT(*) FROM watchlist')
        status['watchlist']['count'] = cursor.fetchone()[0]
        status['watchlist']['migrated'] = status['watchlist']['count'] > 0
        
        # Check goals
        cursor.execute('SELECT COUNT(*) FROM goals')
        status['goals']['count'] = cursor.fetchone()[0]
        status['goals']['migrated'] = status['goals']['count'] > 0
        
        # Check portfolio_history
        cursor.execute('SELECT COUNT(*) FROM portfolio_history')
        status['portfolio_history']['count'] = cursor.fetchone()[0]
        status['portfolio_history']['migrated'] = status['portfolio_history']['count'] > 0
        
        # Check users
        cursor.execute('SELECT COUNT(*) FROM users')
        status['users']['count'] = cursor.fetchone()[0]
        status['users']['migrated'] = status['users']['count'] > 0
    
    # Calculate overall status
    all_migrated = all(s['migrated'] for s in status.values())
    total_items = sum(s['count'] for s in status.values())
    
    return {
        'status': status,
        'all_migrated': all_migrated,
        'total_items': total_items,
        'migration_complete': all_migrated and total_items > 0
    }

def run_all_migrations():
    """Run all data migrations from JSON files to database"""
    print("Starting data migration from JSON files to database...")
    migrate_json_to_db('transaction_history.json')
    migrate_watchlist_to_db('watchlist.json')
    migrate_goals_to_db('goals.json')
    migrate_portfolio_history_to_db('portfolio_history.json')
    migrate_users_to_db('users.json')
    print("Data migration completed!")

def reset_auto_increment():
    """Reset auto-increment to continue from max ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(id) FROM transactions')
        max_id = cursor.fetchone()[0]
        if max_id:
            cursor.execute(f'UPDATE sqlite_sequence SET seq = {max_id} WHERE name = "transactions"')
        conn.commit()

# Initialize database on import
init_database()
# Run migrations on import (will skip if data already exists)
run_all_migrations()

