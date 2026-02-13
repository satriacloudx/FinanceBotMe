"""
SQLite Engine - Local file-based database
Perfect for: Single-server deployment, portable, zero-cost

Advantages:
- No database server needed
- Single file (finance.db)
- Easy backup (just copy file)
- Zero configuration
- Perfect for small-medium scale (1-1000 users)

Limitations:
- Single server only (no distributed)
- Write concurrency limited
- Max database size ~140TB (more than enough)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

# Database file path
DB_FILE = "finance.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Create engine with proper SQLite settings
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threading
        "timeout": 30  # 30 second timeout for locks
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from .models import User, Wallet, Transaction, Category
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial categories
    db = SessionLocal()
    try:
        # Check if categories exist
        existing = db.query(Category).first()
        if not existing:
            categories = [
                # Expense categories
                Category(name='Makan', emoji='🍽️', type='expense'),
                Category(name='Transport', emoji='🚗', type='expense'),
                Category(name='Belanja', emoji='🛒', type='expense'),
                Category(name='Tagihan', emoji='📄', type='expense'),
                Category(name='Hiburan', emoji='🎮', type='expense'),
                Category(name='Kesehatan', emoji='🏥', type='expense'),
                Category(name='Pendidikan', emoji='📚', type='expense'),
                Category(name='Investasi', emoji='📈', type='expense'),
                Category(name='Lainnya', emoji='💰', type='expense'),
                
                # Income categories
                Category(name='Gaji', emoji='💵', type='income'),
                Category(name='Bonus', emoji='🎁', type='income'),
                Category(name='Investasi', emoji='📊', type='income'),
                Category(name='Freelance', emoji='💼', type='income'),
                Category(name='Bisnis', emoji='🏢', type='income'),
            ]
            db.add_all(categories)
            db.commit()
            print("✅ Categories seeded!")
    finally:
        db.close()
    
    print(f"✅ Database initialized: {DB_FILE}")

def backup_database(backup_path: str = None):
    """
    Backup database file
    
    Args:
        backup_path: Path for backup file (default: finance_backup_YYYYMMDD_HHMMSS.db)
    """
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
