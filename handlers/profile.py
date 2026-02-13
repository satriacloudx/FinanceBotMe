"""
Profile Handler - Switch between Personal & Business mode
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.engine import get_db

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command"""
    user = update.effective_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        if not db_user:
            await update.message.reply_text("❌ User tidak ditemukan. Ketik /start dulu ya!")
            return
        
        current_profile = "👤 Pribadi" if db_user['active_profile'] == "personal" else "🏢 Bisnis"
        
        keyboard = [
            [InlineKeyboardButton("👤 Mode Pribadi", callback_data="profile_personal")],
            [InlineKeyboardButton("🏢 Mode Bisnis", callback_data="profile_business")],
            [InlineKeyboardButton("« Kembali", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"<b>Profile Aktif:</b> {current_profile}\n\n"
            f"Pilih mode yang mau kamu gunakan:\n\n"
            f"👤 <b>Pribadi</b> - Untuk keuangan personal\n"
            f"🏢 <b>Bisnis</b> - Untuk PT/CV/Usaha kamu\n\n"
            f"<i>Data transaksi akan terpisah per profile</i>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def switch_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile switch callback"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    profile_type = query.data.split('_')[1]  # profile_personal or profile_business
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        if not db_user:
            await query.edit_message_text("❌ User tidak ditemukan.")
            return
        
        # Update profile
        new_profile = "personal" if profile_type == 'personal' else "business"
        cursor.execute(
            "UPDATE users SET active_profile = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_profile, db_user['id'])
        )
        
        profile_name = "👤 Pribadi" if new_profile == "personal" else "🏢 Bisnis"
        
        keyboard = [
            [InlineKeyboardButton("💸 Catat Transaksi", callback_data="add_transaction")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Profile berhasil diganti ke <b>{profile_name}</b>!\n\n"
            f"Sekarang semua transaksi akan masuk ke dompet {profile_name.lower()}. "
            f"Siap lanjut? 🚀",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def switch_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile switch menu from callback"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        current_profile = "👤 Pribadi" if db_user['active_profile'] == "personal" else "🏢 Bisnis"
        
        keyboard = [
            [InlineKeyboardButton("👤 Mode Pribadi", callback_data="profile_personal")],
            [InlineKeyboardButton("🏢 Mode Bisnis", callback_data="profile_business")],
            [InlineKeyboardButton("« Kembali", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"<b>Profile Aktif:</b> {current_profile}\n\n"
            f"Pilih mode yang mau kamu gunakan:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

def register_profile_handlers(application):
    """Register all profile-related handlers"""
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CallbackQueryHandler(switch_profile_menu, pattern="^switch_profile$"))
    application.add_handler(CallbackQueryHandler(switch_profile_callback, pattern="^profile_(personal|business)$"))
