"""
Admin Handler - Telegram-based Admin Panel
Only accessible by admin users (configured in .env)

Features:
- User statistics
- Broadcast messages
- Database backup
- View all users
- Transaction analytics
- System monitoring
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from database.engine import SessionLocal, backup_database, get_db_size
from database.models import User, Transaction, Wallet, Category, BroadcastLog
from utils import format_currency, format_date
import os

# Conversation states
BROADCAST_MESSAGE = 1

# Admin IDs (will be loaded from config)
ADMIN_IDS = []

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def admin_only(func):
    """Decorator to restrict access to admins only"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text(
                "⛔ Access Denied\n\n"
                "This command is only available for administrators."
            )
            return
        return await func(update, context)
    return wrapper

async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu - /admin"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "⛔ Access Denied\n\n"
            "You don't have permission to access admin panel."
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup")
        ],
        [
            InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics"),
            InlineKeyboardButton("⚙️ System", callback_data="admin_system")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 <b>Admin Panel</b>\n\n"
        "Welcome to CuanFlow Admin Panel.\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        # Get statistics
        total_users = db.query(User).count()
        total_transactions = db.query(Transaction).count()
        
        # Active users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(User).filter(User.updated_at >= week_ago).count()
        
        # New users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_users_today = db.query(User).filter(User.created_at >= today).count()
        
        # Total transaction amount
        total_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income'
        ).scalar() or 0
        
        total_expense = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense'
        ).scalar() or 0
        
        # Database size
        db_size = get_db_size()
        
        message = (
            "📊 <b>Statistics Dashboard</b>\n\n"
            f"👥 <b>Users:</b>\n"
            f"• Total: {total_users}\n"
            f"• Active (7d): {active_users}\n"
            f"• New today: {new_users_today}\n\n"
            f"💰 <b>Transactions:</b>\n"
            f"• Total: {total_transactions}\n"
            f"• Income: {format_currency(total_income)}\n"
            f"• Expense: {format_currency(total_expense)}\n\n"
            f"💾 <b>Database:</b>\n"
            f"• Size: {db_size} MB\n"
            f"• File: finance.db"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
            [InlineKeyboardButton("« Back to Menu", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    finally:
        db.close()

async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users list"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        # Get recent users
        users = db.query(User).order_by(desc(User.created_at)).limit(20).all()
        
        message = "👥 <b>Recent Users (Last 20)</b>\n\n"
        
        for user in users:
            profile_emoji = "👤" if user.active_profile == "personal" else "🏢"
            message += (
                f"{profile_emoji} <b>{user.full_name}</b>\n"
                f"   ID: <code>{user.telegram_id}</code>\n"
                f"   Username: @{user.username or '-'}\n"
                f"   Joined: {format_date(user.created_at, 'short')}\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("📊 User Stats", callback_data="admin_user_stats")],
            [InlineKeyboardButton("« Back to Menu", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    finally:
        db.close()

async def admin_user_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed user statistics"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        # Profile distribution
        personal_count = db.query(User).filter(User.active_profile == 'personal').count()
        business_count = db.query(User).filter(User.active_profile == 'business').count()
        
        # User growth (last 7 days)
        growth_data = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            count = db.query(User).filter(
                User.created_at >= date_start,
                User.created_at < date_end
            ).count()
            
            growth_data.append(f"{date.strftime('%d %b')}: +{count}")
        
        message = (
            "📊 <b>User Statistics</b>\n\n"
            f"<b>Profile Distribution:</b>\n"
            f"👤 Personal: {personal_count}\n"
            f"🏢 Business: {business_count}\n\n"
            f"<b>Growth (Last 7 Days):</b>\n"
        )
        
        for data in reversed(growth_data):
            message += f"• {data}\n"
        
        keyboard = [
            [InlineKeyboardButton("« Back to Users", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    finally:
        db.close()

async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast conversation"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Send me the message you want to broadcast to all users.\n\n"
        "The message will be sent to ALL registered users.\n\n"
        "Type /cancel to cancel.",
        parse_mode='HTML'
    )
    
    return BROADCAST_MESSAGE

async def admin_broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive broadcast message and confirm"""
    message_text = update.message.text
    
    # Store message in context
    context.user_data['broadcast_message'] = message_text
    
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Send Now", callback_data="admin_broadcast_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin_broadcast_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📢 <b>Confirm Broadcast</b>\n\n"
            f"<b>Message Preview:</b>\n"
            f"{message_text}\n\n"
            f"<b>Recipients:</b> {total_users} users\n\n"
            f"Send this message to all users?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    
    finally:
        db.close()

async def admin_broadcast_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send broadcast"""
    query = update.callback_query
    await query.answer("Sending broadcast...")
    
    message_text = context.user_data.get('broadcast_message')
    if not message_text:
        await query.edit_message_text("❌ Error: Message not found.")
        return
    
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()
        total_users = len(users)
        
        # Create broadcast log
        broadcast_log = BroadcastLog(
            message=message_text,
            total_users=total_users,
            created_by=query.from_user.id
        )
        db.add(broadcast_log)
        db.commit()
        
        # Send to all users
        success_count = 0
        failed_count = 0
        
        await query.edit_message_text(
            f"📤 Sending broadcast to {total_users} users...\n\n"
            f"This may take a few moments."
        )
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📢 <b>Announcement</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {user.telegram_id}: {e}")
        
        # Update broadcast log
        broadcast_log.success_count = success_count
        broadcast_log.failed_count = failed_count
        db.commit()
        
        # Send result
        await query.message.reply_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"📊 <b>Results:</b>\n"
            f"• Total: {total_users}\n"
            f"• Success: {success_count}\n"
            f"• Failed: {failed_count}\n\n"
            f"Broadcast ID: #{broadcast_log.id}",
            parse_mode='HTML'
        )
    
    finally:
        db.close()

async def admin_broadcast_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Broadcast cancelled.\n\n"
        "Use /admin to return to admin menu."
    )

async def admin_backup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create and send database backup"""
    query = update.callback_query
    await query.answer("Creating backup...")
    
    try:
        # Create backup
        backup_path = backup_database()
        
        if backup_path and os.path.exists(backup_path):
            # Get file size
            size_bytes = os.path.getsize(backup_path)
            size_mb = size_bytes / (1024 * 1024)
            
            await query.edit_message_text(
                f"💾 Creating backup...\n\n"
                f"File: {backup_path}\n"
                f"Size: {size_mb:.2f} MB"
            )
            
            # Send file
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=open(backup_path, 'rb'),
                filename=backup_path,
                caption=f"💾 <b>Database Backup</b>\n\n"
                        f"File: {backup_path}\n"
                        f"Size: {size_mb:.2f} MB\n"
                        f"Created: {format_date(datetime.now(), 'long')}",
                parse_mode='HTML'
            )
            
            # Clean up
            os.remove(backup_path)
            
            await query.message.reply_text(
                "✅ Backup sent successfully!\n\n"
                "Use /admin to return to admin menu."
            )
        else:
            await query.edit_message_text(
                "❌ Backup failed: Database file not found."
            )
    
    except Exception as e:
        await query.edit_message_text(
            f"❌ Backup failed: {str(e)}"
        )

async def admin_analytics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics"""
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        # Top categories
        top_categories = db.query(
            Category.name,
            Category.emoji,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).join(
            Transaction
        ).group_by(
            Category.id
        ).order_by(
            desc('count')
        ).limit(5).all()
        
        message = "📈 <b>Analytics</b>\n\n<b>Top Categories:</b>\n\n"
        
        for cat in top_categories:
            message += (
                f"{cat.emoji} <b>{cat.name}</b>\n"
                f"   Transactions: {cat.count}\n"
                f"   Total: {format_currency(cat.total or 0)}\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("« Back to Menu", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    finally:
        db.close()

async def admin_system_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system information"""
    query = update.callback_query
    await query.answer()
    
    import sys
    import platform
    
    db_size = get_db_size()
    
    message = (
        "⚙️ <b>System Information</b>\n\n"
        f"<b>Python:</b> {sys.version.split()[0]}\n"
        f"<b>Platform:</b> {platform.system()} {platform.release()}\n"
        f"<b>Database:</b> SQLite (finance.db)\n"
        f"<b>DB Size:</b> {db_size} MB\n\n"
        f"<b>Bot Status:</b> ✅ Running\n"
        f"<b>Uptime:</b> {format_date(datetime.now(), 'long')}"
    )
    
    keyboard = [
        [InlineKeyboardButton("« Back to Menu", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu from callback"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup")
        ],
        [
            InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics"),
            InlineKeyboardButton("⚙️ System", callback_data="admin_system")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔐 <b>Admin Panel</b>\n\n"
        "Welcome to CuanFlow Admin Panel.\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close admin panel"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Admin panel closed.\n\n"
        "Use /admin to open again."
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    await update.message.reply_text(
        "Operation cancelled.\n\n"
        "Use /admin to return to admin menu."
    )
    return ConversationHandler.END

def register_admin_handlers(application, admin_ids: list):
    """Register all admin-related handlers"""
    global ADMIN_IDS
    ADMIN_IDS = admin_ids
    
    # Admin menu command
    application.add_handler(CommandHandler("admin", admin_menu_command))
    
    # Broadcast conversation handler
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$")],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_receive)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )
    application.add_handler(broadcast_conv)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(admin_users_callback, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(admin_user_stats_callback, pattern="^admin_user_stats$"))
    application.add_handler(CallbackQueryHandler(admin_backup_callback, pattern="^admin_backup$"))
    application.add_handler(CallbackQueryHandler(admin_analytics_callback, pattern="^admin_analytics$"))
    application.add_handler(CallbackQueryHandler(admin_system_callback, pattern="^admin_system$"))
    application.add_handler(CallbackQueryHandler(admin_menu_callback, pattern="^admin_menu$"))
    application.add_handler(CallbackQueryHandler(admin_close_callback, pattern="^admin_close$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_confirm_callback, pattern="^admin_broadcast_confirm$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_cancel_callback, pattern="^admin_broadcast_cancel$"))
