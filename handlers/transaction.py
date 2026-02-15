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
        keyboard = [
            [InlineKeyboardButton("📖 See Examples", callback_data="help")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "║   ⚠️ <b>PARSE ERROR</b> ⚠️   ║\n"
            "╚═══════════════════════╝\n\n"
            "Hmm, I couldn't find an amount in your message.\n\n"
            "<b>💡 Try these formats:</b>\n\n"
            "✅ <code>Lunch 50k at cafe</code>\n"
            "✅ <code>Salary 5m received</code>\n"
            "✅ <code>Gas 100k shell</code>\n\n"
            "Need help? Check examples below 👇",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    amount = parsed['amount']
    category_name = parsed['category']
    description = parsed['description']
    
    # Premium confirmation UI
    keyboard = [
        [
            InlineKeyboardButton("💸 Expense", callback_data=f"tx_expense_{amount}_{category_name}_{description}"),
            InlineKeyboardButton("💰 Income", callback_data=f"tx_income_{amount}_{category_name}_{description}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    confirmation_text = (
        f"╔═══════════════════════╗\n"
        f"║   ✅ <b>PARSED</b> ✅   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>Transaction Details:</b>\n\n"
        f"💵 <b>Amount:</b>\n"
        f"   {format_currency(amount)}\n\n"
        f"📁 <b>Category:</b>\n"
        f"   {category_name}\n\n"
        f"📝 <b>Description:</b>\n"
        f"   {description}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Is this an expense or income?</b>\n"
        f"Select below 👇"
    )
    
    await update.message.reply_text(
        confirmation_text,
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
        
        # Success message with premium UI
        profile_name = "Personal" if db_user['active_profile'] == "personal" else "Business"
        profile_emoji = "👤" if db_user['active_profile'] == "personal" else "🏢"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 View Dashboard", callback_data="dashboard"),
                InlineKeyboardButton("➕ Add More", callback_data="add_transaction")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        success_text = (
            f"╔═══════════════════════╗\n"
            f"║   ✅ <b>SAVED</b> ✅   ║\n"
            f"╚═══════════════════════╝\n\n"
            f"{emoji} <b>Transaction Recorded!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 <b>Amount:</b> {format_currency(amount)}\n"
            f"📁 <b>Category:</b> {category_name}\n"
            f"📝 <b>Note:</b> {description}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{profile_emoji} <b>Profile:</b> {profile_name}\n"
            f"💰 <b>New Balance:</b> {format_currency(new_balance)}\n\n"
            f"<b>Keep tracking! 🚀</b>"
        )
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def add_transaction_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show add transaction instructions"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📖 See Examples", callback_data="help")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "╔═══════════════════════╗\n"
        "║   💸 <b>NEW TRANSACTION</b> 💸   ║\n"
        "╚═══════════════════════╝\n\n"
        "<b>Just type naturally!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💡 Examples:</b>\n\n"
        "✅ <code>Lunch 50k at restaurant</code>\n"
        "✅ <code>Salary 5m received</code>\n"
        "✅ <code>Gas 100k shell station</code>\n"
        "✅ <code>Shopping 250k tokopedia</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>I'll automatically detect:</b>\n"
        "• Amount (50k, 5m, etc.)\n"
        "• Category (Food, Transport, etc.)\n"
        "• Description\n\n"
        "<b>Type your transaction now! 🚀</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")],
        [InlineKeyboardButton("💸 Try Again", callback_data="add_transaction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "╔═══════════════════════╗\n"
        "║   ❌ <b>CANCELLED</b> ❌   ║\n"
        "╚═══════════════════════╝\n\n"
        "<b>Transaction cancelled.</b>\n\n"
        "No worries! You can:\n"
        "• Try adding another transaction\n"
        "• Return to main menu\n\n"
        "What would you like to do? 👇",
        reply_markup=reply_markup,
        parse_mode='HTML'
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
