"""
Admin Handler - Telegram-based Admin Panel
Native SQLite version (no SQLAlchemy)
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from datetime import datetime, timedelta
from database.engine import get_db, backup_database, get_db_size
from utils.formatter import format_currency, format_date
import os

# Conversation states
BROADCAST_MESSAGE = 1

# Admin IDs
ADMIN_IDS = []

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

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
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]
        
        # Active users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM users WHERE updated_at >= ?", (week_ago,))
        active_users = cursor.fetchone()[0]
        
        # New users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (today,))
        new_users_today = cursor.fetchone()[0]
        
        # Total transaction amount
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
        total_income = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
        total_expense = cursor.fetchone()[0] or 0
        
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

async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users list"""
    query = update.callback_query
    await query.answer()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get recent users
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 20")
        users = cursor.fetchall()
        
        message = "👥 <b>Recent Users (Last 20)</b>\n\n"
        
        for user in users:
            profile_emoji = "👤" if user['active_profile'] == "personal" else "🏢"
            message += (
                f"{profile_emoji} <b>{user['full_name']}</b>\n"
                f"   ID: <code>{user['telegram_id']}</code>\n"
                f"   Username: @{user['username'] or '-'}\n"
                f"   Joined: {format_date(datetime.fromisoformat(user['created_at']), 'short')}\n\n"
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
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
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

async def admin_broadcast_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send broadcast"""
    query = update.callback_query
    await query.answer("Sending broadcast...")
    
    message_text = context.user_data.get('broadcast_message')
    if not message_text:
        await query.edit_message_text("❌ Error: Message not found.")
        return
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT telegram_id FROM users")
        users = cursor.fetchall()
        total_users = len(users)
        
        # Create broadcast log
        cursor.execute(
            "INSERT INTO broadcast_logs (message, total_users, created_by) VALUES (?, ?, ?)",
            (message_text, total_users, query.from_user.id)
        )
        broadcast_id = cursor.lastrowid
        
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
                    chat_id=user['telegram_id'],
                    text=f"📢 <b>Announcement</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {user['telegram_id']}: {e}")
        
        # Update broadcast log
        cursor.execute(
            "UPDATE broadcast_logs SET success_count = ?, failed_count = ? WHERE id = ?",
            (success_count, failed_count, broadcast_id)
        )
        
        # Send result
        await query.message.reply_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"📊 <b>Results:</b>\n"
            f"• Total: {total_users}\n"
            f"• Success: {success_count}\n"
            f"• Failed: {failed_count}\n\n"
            f"Broadcast ID: #{broadcast_id}",
            parse_mode='HTML'
        )

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
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Top categories
        cursor.execute("""
            SELECT c.name, c.emoji, COUNT(t.id) as count, SUM(t.amount) as total
            FROM categories c
            LEFT JOIN transactions t ON c.id = t.category_id
            GROUP BY c.id
            ORDER BY count DESC
            LIMIT 5
        """)
        top_categories = cursor.fetchall()
        
        message = "📈 <b>Analytics</b>\n\n<b>Top Categories:</b>\n\n"
        
        for cat in top_categories:
            if cat['count'] > 0:
                message += (
                    f"{cat['emoji']} <b>{cat['name']}</b>\n"
                    f"   Transactions: {cat['count']}\n"
                    f"   Total: {format_currency(cat['total'] or 0)}\n\n"
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
        f"<b>Time:</b> {format_date(datetime.now(), 'long')}"
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
    application.add_handler(CallbackQueryHandler(admin_backup_callback, pattern="^admin_backup$"))
    application.add_handler(CallbackQueryHandler(admin_analytics_callback, pattern="^admin_analytics$"))
    application.add_handler(CallbackQueryHandler(admin_system_callback, pattern="^admin_system$"))
    application.add_handler(CallbackQueryHandler(admin_menu_callback, pattern="^admin_menu$"))
    application.add_handler(CallbackQueryHandler(admin_close_callback, pattern="^admin_close$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_confirm_callback, pattern="^admin_broadcast_confirm$"))
    application.add_handler(CallbackQueryHandler(admin_broadcast_cancel_callback, pattern="^admin_broadcast_cancel$"))
