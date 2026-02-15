"""
Start Handler - Premium Onboarding & Welcome
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.engine import get_db

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Premium Onboarding"""
    user = update.effective_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Existing user - Premium welcome back
            profile_emoji = "👤" if existing_user['active_profile'] == "personal" else "🏢"
            profile_name = "Personal" if existing_user['active_profile'] == "personal" else "Business"
            
            keyboard = [
                [
                    InlineKeyboardButton("💸 Catat Transaksi", callback_data="add_transaction"),
                    InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")
                ],
                [
                    InlineKeyboardButton("📈 Analytics", callback_data="analytics_menu"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
                ],
                [
                    InlineKeyboardButton(f"{profile_emoji} Switch to {'Business' if existing_user['active_profile'] == 'personal' else 'Personal'}", callback_data="switch_profile")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = (
                f"╔══════════════════════╗\n"
                f"║   💎 <b>CUANFLOW PRO</b> 💎   ║\n"
                f"╚══════════════════════╝\n\n"
                f"👋 Welcome back, <b>{user.first_name}</b>!\n\n"
                f"📱 <b>Active Profile:</b> {profile_emoji} {profile_name}\n"
                f"💰 <b>Status:</b> ✅ Ready to track\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>💡 Quick Actions:</b>\n"
                f"• Type transaction naturally\n"
                f"• Example: <code>Lunch 50k at cafe</code>\n"
                f"• Or use buttons below 👇\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            # New user - Premium onboarding
            cursor.execute(
                "INSERT INTO users (telegram_id, username, full_name, active_profile) VALUES (?, ?, ?, ?)",
                (user.id, user.username, user.first_name or "User", "personal")
            )
            user_id = cursor.lastrowid
            
            # Create default wallets
            cursor.execute(
                "INSERT INTO wallets (user_id, profile_type, name, balance) VALUES (?, ?, ?, ?)",
                (user_id, "personal", "💳 Personal Wallet", 0.0)
            )
            cursor.execute(
                "INSERT INTO wallets (user_id, profile_type, name, balance) VALUES (?, ?, ?, ?)",
                (user_id, "business", "🏢 Business Wallet", 0.0)
            )
            
            keyboard = [
                [InlineKeyboardButton("🚀 Start Tracking Now", callback_data="add_transaction")],
                [InlineKeyboardButton("📖 How It Works", callback_data="help")],
                [InlineKeyboardButton("⚙️ Setup Profile", callback_data="settings_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            onboarding_text = (
                f"╔═══════════════════════╗\n"
                f"║  🎉 <b>WELCOME TO</b> 🎉  ║\n"
                f"║   💎 CUANFLOW PRO 💎   ║\n"
                f"╚═══════════════════════╝\n\n"
                f"Hey <b>{user.first_name}</b>! 👋\n\n"
                f"Your personal AI-powered finance assistant is ready! 🤖✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>🌟 What You Get:</b>\n\n"
                f"💸 <b>Smart Tracking</b>\n"
                f"   → Natural language input\n"
                f"   → Auto-categorization\n"
                f"   → Real-time balance\n\n"
                f"📊 <b>Powerful Analytics</b>\n"
                f"   → Visual dashboards\n"
                f"   → Spending insights\n"
                f"   → Export reports\n\n"
                f"🔄 <b>Dual Mode</b>\n"
                f"   → Personal finances\n"
                f"   → Business accounting\n"
                f"   → Separate tracking\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>💡 Quick Start:</b>\n"
                f"Just type: <code>Coffee 25k</code>\n"
                f"That's it! I'll handle the rest 🎯\n\n"
                f"Ready to take control? 👇"
            )
            
            await update.message.reply_text(
                onboarding_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - Premium help"""
    help_text = (
        f"╔═══════════════════════╗\n"
        f"║   📖 <b>USER GUIDE</b> 📖   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>🎯 How to Use CuanFlow Pro:</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>1️⃣ Natural Input</b>\n"
        f"Just type like you're texting a friend:\n\n"
        f"✅ <code>Lunch 50k at restaurant</code>\n"
        f"✅ <code>Salary 5m received</code>\n"
        f"✅ <code>Gas 100k shell station</code>\n"
        f"✅ <code>Shopping 250k tokopedia</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>2️⃣ Supported Formats</b>\n\n"
        f"💵 <b>Amounts:</b>\n"
        f"• 50k, 50rb, 50ribu → Rp 50,000\n"
        f"• 5m, 5jt, 5juta → Rp 5,000,000\n"
        f"• 2.5m → Rp 2,500,000\n"
        f"• 50000 → Rp 50,000\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>3️⃣ Commands</b>\n\n"
        f"🏠 /start - Main menu\n"
        f"📊 /dashboard - View analytics\n"
        f"👤 /profile - Switch mode\n"
        f"📖 /help - This guide\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>💡 Pro Tips:</b>\n\n"
        f"• Add descriptions for better tracking\n"
        f"• Use Business mode for company expenses\n"
        f"• Check dashboard regularly\n"
        f"• Export reports monthly\n\n"
        f"<b>Need help?</b> Just ask! 💬"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_start")],
        [InlineKeyboardButton("💸 Start Tracking", callback_data="add_transaction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help button callback"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        f"╔═══════════════════════╗\n"
        f"║   📖 <b>QUICK GUIDE</b> 📖   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>💡 How to Track:</b>\n\n"
        f"Just type naturally:\n\n"
        f"✅ <code>Coffee 25k starbucks</code>\n"
        f"✅ <code>Salary 5m</code>\n"
        f"✅ <code>Uber 50k to office</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>🎯 Features:</b>\n\n"
        f"📊 Real-time dashboard\n"
        f"💰 Auto-categorization\n"
        f"📈 Visual analytics\n"
        f"🔄 Dual mode (Personal/Business)\n"
        f"📥 Export reports\n\n"
        f"That's it! Super simple! 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Now", callback_data="add_transaction")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

async def back_to_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to start callback"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        
        profile_emoji = "👤" if db_user['active_profile'] == "personal" else "🏢"
        profile_name = "Personal" if db_user['active_profile'] == "personal" else "Business"
        
        keyboard = [
            [
                InlineKeyboardButton("💸 Catat Transaksi", callback_data="add_transaction"),
                InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")
            ],
            [
                InlineKeyboardButton("📈 Analytics", callback_data="analytics_menu"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
            ],
            [
                InlineKeyboardButton(f"{profile_emoji} Switch Profile", callback_data="switch_profile")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"╔══════════════════════╗\n"
            f"║   💎 <b>CUANFLOW PRO</b> 💎   ║\n"
            f"╚══════════════════════╝\n\n"
            f"👋 <b>{user.first_name}</b>\n\n"
            f"📱 <b>Profile:</b> {profile_emoji} {profile_name}\n"
            f"💰 <b>Status:</b> ✅ Active\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>💡 Quick Actions:</b>\n"
            f"Type: <code>Lunch 50k</code>\n"
            f"Or use buttons below 👇"
        )
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu callback"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("👤 Switch Profile", callback_data="switch_profile")],
        [InlineKeyboardButton("📊 View Stats", callback_data="dashboard")],
        [InlineKeyboardButton("📖 Help Guide", callback_data="help")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        f"╔═══════════════════════╗\n"
        f"║   ⚙️ <b>SETTINGS</b> ⚙️   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>Configure your CuanFlow experience:</b>\n\n"
        f"👤 <b>Profile Management</b>\n"
        f"   Switch between Personal & Business\n\n"
        f"📊 <b>View Statistics</b>\n"
        f"   Check your financial overview\n\n"
        f"📖 <b>Help & Guide</b>\n"
        f"   Learn how to use features\n\n"
        f"Select an option below 👇"
    )
    
    await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')

async def analytics_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle analytics menu callback"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 Full Dashboard", callback_data="dashboard")],
        [InlineKeyboardButton("📈 Monthly Report", callback_data="monthly_report")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    analytics_text = (
        f"╔═══════════════════════╗\n"
        f"║   📈 <b>ANALYTICS</b> 📈   ║\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>View your financial insights:</b>\n\n"
        f"📊 <b>Full Dashboard</b>\n"
        f"   Complete overview with breakdown\n\n"
        f"📈 <b>Monthly Report</b>\n"
        f"   Detailed monthly analysis\n\n"
        f"Select an option below 👇"
    )
    
    await query.edit_message_text(analytics_text, reply_markup=reply_markup, parse_mode='HTML')

async def monthly_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle monthly report callback - redirect to dashboard"""
    query = update.callback_query
    await query.answer("Loading monthly report...")
    
    # Import and call dashboard
    from .analytics import dashboard_callback
    await dashboard_callback(update, context)

def register_start_handlers(application):
    """Register all start-related handlers"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(back_to_start_callback, pattern="^back_to_start$"))
    application.add_handler(CallbackQueryHandler(settings_menu_callback, pattern="^settings_menu$"))
    application.add_handler(CallbackQueryHandler(analytics_menu_callback, pattern="^analytics_menu$"))
    application.add_handler(CallbackQueryHandler(monthly_report_callback, pattern="^monthly_report$"))
