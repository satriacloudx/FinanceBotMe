"""
CuanFlow - SQLite Version with Admin Panel
Main Entry Point

Features:
- SQLite database (single file: finance.db)
- No database server needed
- Built-in admin panel (Flask)
- Automatic backup
- User statistics
- Broadcast messages

Perfect for:
- Single-server deployment
- Small to medium scale (1-1000 users)
- Easy backup and portability
- Zero database cost
"""
import asyncio
import logging
from telegram.ext import ApplicationBuilder
from config import config
from database.engine import init_db

# Import handlers (same as other versions)
from handlers import (
    register_start_handlers,
    register_transaction_handlers,
    register_analytics_handlers,
    register_profile_handlers
)
from handlers.admin import register_admin_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

async def main():
    """Main function - Start the bot"""
    try:
        # Validate configuration
        config.validate()
        logger.info("✅ Configuration validated")
        
        # Initialize database BEFORE building application
        logger.info("🚀 Initializing SQLite database...")
        init_db()
        logger.info("✅ Database ready!")
        
        # Build application (without post_init)
        application = (
            ApplicationBuilder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .build()
        )
        
        # Register all handlers
        logger.info("📝 Registering handlers...")
        register_start_handlers(application)
        register_transaction_handlers(application)
        register_analytics_handlers(application)
        register_profile_handlers(application)
        register_admin_handlers(application, config.ADMIN_IDS)
        logger.info("✅ All handlers registered")
        
        if config.ADMIN_IDS:
            logger.info(f"🔐 Admin access enabled for {len(config.ADMIN_IDS)} user(s)")
        else:
            logger.warning("⚠️  No admin IDs configured! Set ADMIN_IDS in .env")
        
        # Start bot
        logger.info("🤖 Starting CuanFlow Bot (SQLite Version)...")
        logger.info(f"🌍 Environment: {config.ENVIRONMENT}")
        logger.info(f"💾 Database: finance.db (SQLite)")
        logger.info(f"🔧 Admin Panel: http://localhost:5000")
        
        await application.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Application crashed: {e}")
