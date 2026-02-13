"""
Configuration for SQLite Version
"""
import os
from dotenv import load_dotenv

load_dotenv()

class SQLiteConfig:
    """Configuration for SQLite-based storage"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Database (SQLite - no configuration needed!)
    DATABASE_FILE = "finance.db"
    
    # Admin Panel (Telegram-based)
    # Comma-separated list of admin Telegram IDs
    ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS if id.strip().isdigit()]
    
    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Chart Settings
    CHART_STYLE = "ggplot"
    CHART_DPI = 100
    CHART_FIGSIZE = (10, 6)
    
    # Business Logic
    DEFAULT_CURRENCY = "IDR"
    MAX_TRANSACTION_AMOUNT = 1_000_000_000  # 1 Milyar
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN tidak ditemukan di environment!")
        return True

config = SQLiteConfig()
