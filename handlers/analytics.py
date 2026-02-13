"""
Analytics Handler - Dashboard and Text Reports
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta
from database.engine import SessionLocal
from database.models import User, Wallet, Transaction, Category
from utils.formatter import format_currency, format_date
import os

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dashboard command - Show financial summary"""
    user = update.effective_user
    
    db = SessionLocal()
    try:
        # Get user and wallet
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if not db_user:
            await update.message.reply_text("❌ User tidak ditemukan. Ketik /start dulu!")
            return
        
        wallet = db.query(Wallet).filter(
            Wallet.user_id == db_user.id,
            Wallet.profile_type == db_user.active_profile
        ).first()
        
        # Get this month's transactions
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.transaction_date >= start_of_month
        ).all()
        
        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        # Group by category
        expense_by_category = {}
        for t in transactions:
            if t.type == 'expense' and t.category:
                cat_name = t.category.name
                expense_by_category[cat_name] = expense_by_category.get(cat_name, 0) + t.amount
        
        # Build message
        profile_name = "👤 Pribadi" if db_user.active_profile == "personal" else "🏢 Bisnis"
        month_name = datetime.utcnow().strftime("%B %Y")
        
        message = (
            f"📊 <b>Dashboard {profile_name}</b>\n"
            f"📅 {month_name}\n\n"
            f"💰 <b>Pemasukan:</b> {format_currency(total_income)}\n"
            f"💸 <b>Pengeluaran:</b> {format_currency(total_expense)}\n"
            f"{'➖' * 25}\n"
            f"💼 <b>Saldo Akhir:</b> {format_currency(wallet.balance)}\n\n"
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
    
    finally:
        db.close()

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard callback from inline button"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        wallet = db.query(Wallet).filter(
            Wallet.user_id == db_user.id,
            Wallet.profile_type == db_user.active_profile
        ).first()
        
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.transaction_date >= start_of_month
        ).all()
        
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        profile_name = "👤 Pribadi" if db_user.active_profile == "personal" else "🏢 Bisnis"
        
        message = (
            f"📊 <b>Dashboard {profile_name}</b>\n\n"
            f"💰 Pemasukan: {format_currency(total_income)}\n"
            f"💸 Pengeluaran: {format_currency(total_expense)}\n"
            f"💼 Saldo: {format_currency(wallet.balance)}\n\n"
            f"Ketik /dashboard untuk lihat detail lengkap!"
        )
        
        await query.edit_message_text(message, parse_mode='HTML')
    
    finally:
        db.close()

async def export_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export transactions as text"""
    query = update.callback_query
    await query.answer("⏳ Generating report...")
    
    user = query.from_user
    
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        wallet = db.query(Wallet).filter(
            Wallet.user_id == db_user.id,
            Wallet.profile_type == db_user.active_profile
        ).first()
        
        # Get all transactions
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).order_by(Transaction.transaction_date.desc()).limit(50).all()
        
        if not transactions:
            await query.edit_message_text("❌ Belum ada transaksi.")
            return
        
        # Build text report
        profile_name = "Pribadi" if db_user.active_profile == "personal" else "Bisnis"
        report = f"📊 <b>Laporan Transaksi {profile_name}</b>\n"
        report += f"📅 {datetime.now().strftime('%d %B %Y')}\n\n"
        
        for t in transactions[:20]:  # Show last 20
            emoji = "💰" if t.type == "income" else "💸"
            report += f"{emoji} {format_date(t.transaction_date, 'short')}\n"
            report += f"   {t.category.name if t.category else 'Lainnya'}: {format_currency(t.amount)}\n"
            if t.description:
                report += f"   📝 {t.description}\n"
            report += "\n"
        
        if len(transactions) > 20:
            report += f"<i>... dan {len(transactions) - 20} transaksi lainnya</i>\n"
        
        await query.edit_message_text(report, parse_mode='HTML')
    
    finally:
        db.close()

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
