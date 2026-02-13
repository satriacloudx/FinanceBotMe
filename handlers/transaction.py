"""
Transaction Handler - Smart NLP-based transaction recording
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime
from database.engine import get_db
from utils.parser import parse_transaction
from utils.formatter import format_currency

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language transaction input"""
    user = update.effective_user
    text = update.message.text
    
    # Parse transaction
    parsed = parse_transaction(text)
    
    if not parsed:
        await update.message.reply_text(
            "🤔 Hmm, aku gak nemu angka di pesanmu.\n\n"
            "Coba format kayak gini:\n"
            "• <code>Makan siang 50rb</code>\n"
            "• <code>Gaji 5jt</code>\n"
            "• <code>Bensin 100k</code>",
            parse_mode='HTML'
        )
        return
    
    amount = parsed['amount']
    category_name = parsed['category']
    description = parsed['description']
    
    # Ask user: Income or Expense?
    keyboard = [
        [
            InlineKeyboardButton("💸 Pengeluaran", callback_data=f"tx_expense_{amount}_{category_name}_{description}"),
            InlineKeyboardButton("💰 Pemasukan", callback_data=f"tx_income_{amount}_{category_name}_{description}")
        ],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Oke, aku tangkep:\n\n"
        f"💵 <b>Jumlah:</b> {format_currency(amount)}\n"
        f"📁 <b>Kategori:</b> {category_name}\n"
        f"📝 <b>Keterangan:</b> {description}\n\n"
        f"Ini pemasukan atau pengeluaran?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def save_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save transaction after user confirms type"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data.split('_')
    
    if len(data) < 5:
        await query.edit_message_text("❌ Data tidak valid.")
        return
    
    tx_type = data[1]  # income or expense
    amount = float(data[2])
    category_name = data[3]
    description = '_'.join(data[4:])  # Handle description with underscores
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        if not db_user:
            await query.edit_message_text("❌ User tidak ditemukan. Ketik /start dulu!")
            return
        
        # Get active wallet
        cursor.execute(
            "SELECT * FROM wallets WHERE user_id = ? AND profile_type = ?",
            (db_user['id'], db_user['active_profile'])
        )
        wallet = cursor.fetchone()
        
        # Get or create category
        cursor.execute("SELECT * FROM categories WHERE name = ?", (category_name,))
        category = cursor.fetchone()
        
        if not category:
            cursor.execute(
                "INSERT INTO categories (name, type) VALUES (?, ?)",
                (category_name, tx_type)
            )
            category_id = cursor.lastrowid
        else:
            category_id = category['id']
        
        # Create transaction
        cursor.execute(
            "INSERT INTO transactions (wallet_id, category_id, type, amount, description, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
            (wallet['id'], category_id, tx_type, amount, description, datetime.utcnow())
        )
        
        # Update wallet balance
        if tx_type == 'expense':
            new_balance = wallet['balance'] - amount
            emoji = "💸"
            action = "keluar"
        else:
            new_balance = wallet['balance'] + amount
            emoji = "💰"
            action = "masuk"
        
        cursor.execute(
            "UPDATE wallets SET balance = ? WHERE id = ?",
            (new_balance, wallet['id'])
        )
        
        # Success message
        profile_name = "Pribadi" if db_user['active_profile'] == "personal" else "Bisnis"
        
        keyboard = [
            [InlineKeyboardButton("📊 Lihat Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton("➕ Catat Lagi", callback_data="add_transaction")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Siap Boss! {emoji}\n\n"
            f"{format_currency(amount)} udah dicatet {action} dari dompet <b>{profile_name}</b>.\n\n"
            f"💼 <b>Saldo sekarang:</b> {format_currency(new_balance)}\n\n"
            f"Tetap semangat kelola keuangannya! 🚀",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def add_transaction_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show add transaction instructions"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💸 <b>Catat Transaksi Baru</b>\n\n"
        "Langsung ketik aja transaksinya, contoh:\n\n"
        "• <code>Makan siang 50rb di warteg</code>\n"
        "• <code>Gaji 5jt</code>\n"
        "• <code>Bensin 100k shell</code>\n"
        "• <code>Belanja tokped 250rb</code>\n\n"
        "Aku bakal otomatis deteksi jumlah dan kategorinya! 🤖✨",
        parse_mode='HTML'
    )

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Dibatalkan.\n\n"
        "Kalau mau catat transaksi lagi, tinggal ketik aja! 😊"
    )

def register_transaction_handlers(application):
    """Register all transaction-related handlers"""
    # Text message handler (for NLP parsing)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(save_transaction_callback, pattern="^tx_(income|expense)_"))
    application.add_handler(CallbackQueryHandler(add_transaction_menu, pattern="^add_transaction$"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel$"))
