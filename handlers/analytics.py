"""
Analytics Handler - Dashboard and Text Reports
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta
from database.engine import get_db
from utils.formatter import format_currency, format_date

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dashboard command - Show financial summary"""
    user = update.effective_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user and wallet
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        if not db_user:
            await update.message.reply_text("❌ User tidak ditemukan. Ketik /start dulu!")
            return
        
        cursor.execute(
            "SELECT * FROM wallets WHERE user_id = ? AND profile_type = ?",
            (db_user['id'], db_user['active_profile'])
        )
        wallet = cursor.fetchone()
        
        # Get this month's transactions
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute(
            """SELECT t.*, c.name as category_name, c.emoji as category_emoji
               FROM transactions t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.wallet_id = ? AND t.transaction_date >= ?""",
            (wallet['id'], start_of_month)
        )
        transactions = cursor.fetchall()
        
        # Calculate totals
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        # Group by category
        expense_by_category = {}
        for t in transactions:
            if t['type'] == 'expense' and t['category_name']:
                cat_name = t['category_name']
                expense_by_category[cat_name] = expense_by_category.get(cat_name, 0) + t['amount']
        
        # Build message
        profile_name = "👤 Pribadi" if db_user['active_profile'] == "personal" else "🏢 Bisnis"
        month_name = datetime.utcnow().strftime("%B %Y")
        
        message = (
            f"📊 <b>Dashboard {profile_name}</b>\n"
            f"📅 {month_name}\n\n"
            f"💰 <b>Pemasukan:</b> {format_currency(total_income)}\n"
            f"💸 <b>Pengeluaran:</b> {format_currency(total_expense)}\n"
            f"{'➖' * 25}\n"
            f"💼 <b>Saldo Akhir:</b> {format_currency(wallet['balance'])}\n\n"
        )
        
        if expense_by_category:
            message += "<b>📁 Top Pengeluaran:</b>\n"
            sorted_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:5]
            for cat, amount in sorted_expenses:
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                message += f"• {cat}: {format_currency(amount)} ({percentage:.1f}%)\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Catat Transaksi", callback_data="add_transaction")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard callback from inline button"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        cursor.execute(
            "SELECT * FROM wallets WHERE user_id = ? AND profile_type = ?",
            (db_user['id'], db_user['active_profile'])
        )
        wallet = cursor.fetchone()
        
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute(
            "SELECT * FROM transactions WHERE wallet_id = ? AND transaction_date >= ?",
            (wallet['id'], start_of_month)
        )
        transactions = cursor.fetchall()
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        profile_name = "👤 Pribadi" if db_user['active_profile'] == "personal" else "🏢 Bisnis"
        
        message = (
            f"📊 <b>Dashboard {profile_name}</b>\n\n"
            f"💰 Pemasukan: {format_currency(total_income)}\n"
            f"💸 Pengeluaran: {format_currency(total_expense)}\n"
            f"💼 Saldo: {format_currency(wallet['balance'])}\n\n"
            f"Ketik /dashboard untuk lihat detail lengkap!"
        )
        
        await query.edit_message_text(message, parse_mode='HTML')

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command"""
    await update.message.reply_text(
        "📊 <b>Export Laporan</b>\n\n"
        "Fitur export Excel sementara tidak tersedia.\n"
        "Gunakan /dashboard untuk lihat ringkasan transaksi.",
        parse_mode='HTML'
    )

def register_analytics_handlers(application):
    """Register all analytics-related handlers"""
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"))
