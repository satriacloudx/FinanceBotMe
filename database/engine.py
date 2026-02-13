"""
SQLite Engine - Native Python sqlite3 (no SQLAlchemy)
Zero dependencies, works with any Python version
"""
import sqlite3
import os
from contextlib import contextmanager

# Database file path
DB_FILE = "finance.db"

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

@contextmanager
def get_db():
    """Context manager for database connection"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                active_profile TEXT DEFAULT 'personal',
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Wallets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_type TEXT NOT NULL,
                name TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'IDR',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                emoji TEXT DEFAULT '💰',
                type TEXT NOT NULL
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                category_id INTEGER,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Broadcast logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                total_users INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL
            )
        """)
        
        # Check if categories exist
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            # Seed categories
            categories = [
                ('Makan', '🍽️', 'expense'),
                ('Transport', '🚗', 'expense'),
                ('Belanja', '🛒', 'expense'),
                ('Tagihan', '📄', 'expense'),
                ('Hiburan', '🎮', 'expense'),
                ('Kesehatan', '🏥', 'expense'),
                ('Pendidikan', '📚', 'expense'),
                ('Investasi', '📈', 'expense'),
                ('Lainnya', '💰', 'expense'),
                ('Gaji', '💵', 'income'),
                ('Bonus', '🎁', 'income'),
                ('Investasi', '📊', 'income'),
                ('Freelance', '💼', 'income'),
                ('Bisnis', '🏢', 'income'),
            ]
            cursor.executemany(
                "INSERT INTO categories (name, emoji, type) VALUES (?, ?, ?)",
                categories
            )
        
        conn.commit()
        print(f"✅ Database initialized: {DB_FILE}")
        
    finally:
        conn.close()

def backup_database(backup_path: str = None):
    """Backup database file"""
    import shutil
    from datetime import datetime
    
    if not os.path.exists(DB_FILE):
        return None
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"finance_backup_{timestamp}.db"
    
    shutil.copy2(DB_FILE, backup_path)
    return backup_path

def get_db_size():
    """Get database file size in MB"""
    if os.path.exists(DB_FILE):
        size_bytes = os.path.getsize(DB_FILE)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    return 0
