"""
Analytics Handler - Dashboard, Charts, and Excel Export
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta
from database.engine import SessionLocal
from database.models import User, Wallet, Transaction, Category
from utils.formatter import format_currency, format_date
from utils.chart_generator import generate_expense_chart
import pandas as pd
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
        
        # Generate chart if there are expenses
        chart_file = None
        if expense_by_category:
            chart_file = generate_expense_chart(expense_by_category, f"chart_{user.id}.png")
        
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
            [InlineKeyboardButton("📥 Export Excel", callback_data="export_excel")],
            [InlineKeyboardButton("➕ Catat Transaksi", callback_data="add_transaction")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send chart if available
        if chart_file and os.path.exists(chart_file):
            await update.message.reply_photo(
                photo=open(chart_file, 'rb'),
                caption=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            os.remove(chart_file)  # Clean up
        else:
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

async def export_excel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export transactions to Excel"""
    query = update.callback_query
    await query.answer("⏳ Generating Excel file...")
    
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
        ).order_by(Transaction.transaction_date.desc()).all()
        
        if not transactions:
            await query.edit_message_text("❌ Belum ada transaksi untuk di-export.")
            return
        
        # Prepare data for Excel
        data = []
        for t in transactions:
            data.append({
                'Tanggal': format_date(t.transaction_date, 'medium'),
                'Tipe': 'Pemasukan' if t.type == 'income' else 'Pengeluaran',
                'Kategori': t.category.name if t.category else '-',
                'Jumlah': t.amount,
                'Keterangan': t.description or '-'
            })
        
        df = pd.DataFrame(data)
        
        # Generate filename
        profile_name = "Pribadi" if db_user.active_profile == "personal" else "Bisnis"
        filename = f"CuanFlow_{profile_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Save to Excel
        df.to_excel(filename, index=False, sheet_name='Transaksi')
        
        # Send file
        await query.message.reply_document(
            document=open(filename, 'rb'),
            filename=filename,
            caption=f"📥 <b>Laporan Keuangan {profile_name}</b>\n\n"
                    f"Total transaksi: {len(transactions)}\n"
                    f"Generated: {format_date(datetime.now(), 'long')}",
            parse_mode='HTML'
        )
        
        # Clean up
        os.remove(filename)
        
        await query.edit_message_text("✅ File Excel berhasil dikirim!")
    
    finally:
        db.close()

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command"""
    await update.message.reply_text("⏳ Sedang generate laporan Excel...")
    
    # Reuse the export logic
    fake_query = type('obj', (object,), {
        'from_user': update.effective_user,
        'message': update.message,
        'answer': lambda x: None,
        'edit_message_text': lambda x: None
    })()
    
    await export_excel_callback(fake_query, context)

def register_analytics_handlers(application):
    """Register all analytics-related handlers"""
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"))
    application.add_handler(CallbackQueryHandler(export_excel_callback, pattern="^export_excel$"))
