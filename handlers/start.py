"""
Start Handler - Onboarding & Welcome
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.engine import SessionLocal
from database.models import User, Wallet

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Onboarding"""
    user = update.effective_user
    
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if existing_user:
            # Existing user
            keyboard = [
                [InlineKeyboardButton("💸 Catat Transaksi", callback_data="add_transaction")],
                [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
                [InlineKeyboardButton("👤 Ganti Profile", callback_data="switch_profile")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Halo lagi, {user.first_name}! 👋\n\n"
                f"Siap bantu kelola keuangan kamu hari ini. Mau ngapain?\n\n"
                f"💡 <i>Tips: Langsung ketik aja transaksinya, misal:</i>\n"
                f"<code>Makan siang 50rb di warteg</code>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # New user - Create account
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                full_name=user.first_name or "User",
                active_profile="personal"
            )
            db.add(new_user)
            db.flush()
            
            # Create default wallets
            personal_wallet = Wallet(
                user_id=new_user.id,
                profile_type="personal",
                name="Dompet Pribadi"
            )
            business_wallet = Wallet(
                user_id=new_user.id,
                profile_type="business",
                name="Bisnis"
            )
            db.add_all([personal_wallet, business_wallet])
            db.commit()
            
            keyboard = [
                [InlineKeyboardButton("🚀 Mulai Catat Transaksi", callback_data="add_transaction")],
                [InlineKeyboardButton("📖 Panduan Singkat", callback_data="help")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎉 Selamat datang di <b>CuanFlow</b>, {user.first_name}!\n\n"
                f"Asisten keuangan pintar yang bikin hidup kamu lebih teratur. "
                f"Gak perlu ribet, tinggal chat aja kayak ngobrol sama temen! 💬\n\n"
                f"<b>Contoh:</b>\n"
                f"• <code>Makan siang 50rb</code>\n"
                f"• <code>Gaji 5jt</code>\n"
                f"• <code>Bensin 100k</code>\n\n"
                f"Udah siap? Yuk mulai! 🚀",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 <b>Panduan CuanFlow</b>\n\n"
        "<b>Cara Pakai:</b>\n"
        "1️⃣ Langsung ketik transaksi kamu (gak perlu command)\n"
        "   Contoh: <code>Makan siang 50rb di warteg</code>\n\n"
        "2️⃣ Bot otomatis deteksi jumlah & kategori\n\n"
        "3️⃣ Lihat dashboard kapan aja dengan /dashboard\n\n"
        "<b>Format yang Didukung:</b>\n"
        "• 50rb, 50k, 50ribu → Rp 50.000\n"
        "• 5jt, 5juta → Rp 5.000.000\n"
        "• 50000 → Rp 50.000\n\n"
        "<b>Commands:</b>\n"
        "/start - Menu utama\n"
        "/dashboard - Lihat ringkasan keuangan\n"
        "/export - Download laporan Excel\n"
        "/profile - Ganti mode Pribadi/Bisnis\n\n"
        "Ada pertanyaan? Langsung chat aja! 😊"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help button callback"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "📖 <b>Panduan Singkat</b>\n\n"
        "Tinggal ketik transaksi kamu kayak ngobrol biasa:\n\n"
        "✅ <code>Makan siang 50rb</code>\n"
        "✅ <code>Gaji 5jt masuk</code>\n"
        "✅ <code>Bensin 100k</code>\n\n"
        "Bot bakal otomatis ngerti jumlah dan kategorinya! 🤖✨"
    )
    
    await query.edit_message_text(help_text, parse_mode='HTML')

def register_start_handlers(application):
    """Register all start-related handlers"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
