"""
Main Bot File - Telegram Bot Manajemen Keuangan & Bisnis
Modified for Render Web Service with Webhook
"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

from config import (
    BOT_TOKEN, ADMIN_ID, INCOME_CATEGORIES, EXPENSE_CATEGORIES, 
    MODE_PERSONAL, MODE_BUSINESS, SUBSCRIPTION_TIERS
)
from db_helper import DBHelper
from utils import (
    format_currency, generate_pie_chart, generate_bar_chart,
    export_to_csv, export_to_excel, get_current_month_name, validate_amount
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Database
db = DBHelper('finance.db')

# Conversation States
TRANS_TYPE, TRANS_CATEGORY, TRANS_AMOUNT, TRANS_DESC = range(4)
DEBT_TYPE, DEBT_PERSON, DEBT_AMOUNT, DEBT_DESC = range(4, 8)
BROADCAST_MESSAGE = 8

# User data temporary storage
user_data_temp = {}


# ============= HELPER FUNCTIONS =============

def is_admin(user_id: int) -> bool:
    """Check apakah user adalah admin"""
    return user_id == ADMIN_ID


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim main menu dengan inline keyboard - Enhanced UI"""
    user_id = update.effective_user.id
    subscription = db.get_user_subscription(user_id)
    tier = subscription['tier']
    
    # Emoji badge berdasarkan tier
    tier_badge = {
        'free': '🆓',
        'basic': '⭐',
        'premium': '👑'
    }.get(tier, '🆓')
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Tambah Transaksi", callback_data="add_transaction"),
            InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")
        ],
        [
            InlineKeyboardButton("📈 Laporan Visual", callback_data="visual_report"),
            InlineKeyboardButton("📥 Export Data", callback_data="export_menu")
        ],
        [
            InlineKeyboardButton("💼 Mode Bisnis", callback_data="business_menu"),
            InlineKeyboardButton("📋 Riwayat", callback_data="transaction_history")
        ],
        [
            InlineKeyboardButton(f"{tier_badge} Subscription", callback_data="subscription_menu"),
            InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    tier_name = SUBSCRIPTION_TIERS[tier]['name']
    
    text = (
        f"🏦 <b>FinanceHub - Professional Finance Manager</b>\n\n"
        f"{tier_badge} <b>Status:</b> {tier_name} Plan\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Pilih menu di bawah untuk mengelola keuangan Anda:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')


# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user = update.effective_user
    
    # Simpan user ke database
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    db.update_last_active(user.id)
    
    welcome_text = (
        f"👋 Welcome <b>{user.first_name}</b>!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏦 <b>FinanceHub</b>\n"
        "<i>Professional Finance Management Platform</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Your Financial Command Center:</b>\n\n"
        "💰 Track Income & Expenses\n"
        "📊 Real-time Dashboard & Analytics\n"
        "📈 Professional Visual Reports\n"
        "📥 Export to Excel/CSV\n"
        "💼 Business Debt Management\n"
        "👑 Premium Features Available\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <i>Let's take control of your finances!</i>"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='HTML')
    await send_main_menu(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    help_text = (
        "📖 <b>Panduan Penggunaan Bot</b>\n\n"
        "<b>Menu Utama:</b>\n"
        "• <b>Tambah Transaksi</b> - Catat pemasukan/pengeluaran\n"
        "• <b>Dashboard</b> - Lihat ringkasan keuangan\n"
        "• <b>Laporan Visual</b> - Chart pengeluaran\n"
        "• <b>Export Data</b> - Download laporan Excel/CSV\n"
        "• <b>Mode Bisnis</b> - Kelola hutang/piutang\n\n"
        "<b>Tips:</b>\n"
        "💡 Catat transaksi secara rutin\n"
        "💡 Gunakan kategori yang sesuai\n"
        "💡 Review dashboard setiap minggu\n\n"
        "Butuh bantuan? Hubungi admin! 📞"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')


# ============= DASHBOARD & REPORTS =============

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan dashboard keuangan - Enhanced UI"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db.update_last_active(user_id)
    
    # Get balance data
    total_balance = db.get_balance(user_id, MODE_PERSONAL)
    monthly_balance = db.get_monthly_balance(user_id, MODE_PERSONAL)
    subscription = db.get_user_subscription(user_id)
    
    month_name = get_current_month_name()
    tier_badge = "🆓" if subscription['tier'] == 'free' else ("⭐" if subscription['tier'] == 'basic' else "👑")
    
    # Calculate percentages
    if monthly_balance['income'] > 0:
        expense_ratio = (monthly_balance['expense'] / monthly_balance['income']) * 100
    else:
        expense_ratio = 0
    
    # Status indicator
    if expense_ratio > 90:
        status = "🔴 High Spending"
    elif expense_ratio > 70:
        status = "🟡 Moderate"
    else:
        status = "🟢 Healthy"
    
    dashboard_text = (
        f"📊 <b>Financial Dashboard</b> {tier_badge}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>💼 Total Portfolio:</b>\n"
        f"├ 💰 Income: {format_currency(total_balance['income'])}\n"
        f"├ 💸 Expense: {format_currency(total_balance['expense'])}\n"
        f"└ 💎 <b>Balance: {format_currency(total_balance['balance'])}</b>\n\n"
        f"<b>📅 {month_name} Overview:</b>\n"
        f"├ 💰 Income: {format_currency(monthly_balance['income'])}\n"
        f"├ 💸 Expense: {format_currency(monthly_balance['expense'])}\n"
        f"├ 💎 Balance: {format_currency(monthly_balance['balance'])}\n"
        f"└ 📈 Status: {status}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Expense Ratio: {expense_ratio:.1f}%</i>"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(dashboard_text, reply_markup=reply_markup, parse_mode='HTML')


async def show_visual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu laporan visual"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 Chart Pengeluaran (Pie)", callback_data="chart_expense_pie")],
        [InlineKeyboardButton("📈 Chart Pengeluaran (Bar)", callback_data="chart_expense_bar")],
        [InlineKeyboardButton("💰 Chart Pemasukan (Bar)", callback_data="chart_income_bar")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📈 <b>Laporan Visual</b>\n\nPilih jenis chart yang ingin ditampilkan:"
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def generate_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate dan kirim chart"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    chart_type = query.data
    
    await query.edit_message_text("⏳ Sedang membuat chart...")
    
    try:
        if 'expense' in chart_type:
            data = db.get_transactions_by_category(user_id, 'expense', MODE_PERSONAL)
            title = f"Pengeluaran - {get_current_month_name()}"
        else:
            data = db.get_transactions_by_category(user_id, 'income', MODE_PERSONAL)
            title = f"Pemasukan - {get_current_month_name()}"
        
        if not data:
            await query.edit_message_text(
                "❌ Belum ada data transaksi untuk ditampilkan.\n\n"
                "Silakan tambah transaksi terlebih dahulu!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="visual_report")
                ]])
            )
            return
        
        # Generate chart
        if 'pie' in chart_type:
            chart_buffer = generate_pie_chart(data, title)
        else:
            chart_buffer = generate_bar_chart(data, title)
        
        if chart_buffer:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=chart_buffer,
                caption=f"📊 <b>{title}</b>",
                parse_mode='HTML'
            )
            await send_main_menu(update, context)
        else:
            await query.edit_message_text("❌ Gagal membuat chart. Silakan coba lagi.")
    
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        await query.edit_message_text("❌ Terjadi kesalahan saat membuat chart.")


# ============= EXPORT DATA =============

async def show_export_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu export"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📄 Export ke CSV", callback_data="export_csv")],
        [InlineKeyboardButton("📊 Export ke Excel", callback_data="export_excel")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📥 <b>Export Data</b>\n\nPilih format file yang diinginkan:"
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export data transaksi"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    export_type = query.data
    
    await query.edit_message_text("⏳ Sedang menyiapkan file...")
    
    try:
        transactions = db.get_all_transactions(user_id, MODE_PERSONAL)
        
        if not transactions:
            await query.edit_message_text(
                "❌ Belum ada data transaksi untuk di-export.\n\n"
                "Silakan tambah transaksi terlebih dahulu!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="export_menu")
                ]])
            )
            return
        
        if 'csv' in export_type:
            file_buffer = export_to_csv(transactions)
            filename = f"transaksi_{user_id}.csv"
            caption = "📄 Data transaksi Anda (CSV)"
        else:
            file_buffer = export_to_excel(transactions)
            filename = f"transaksi_{user_id}.xlsx"
            caption = "📊 Data transaksi Anda (Excel)"
        
        if file_buffer:
            await context.bot.send_document(
                chat_id=user_id,
                document=file_buffer,
                filename=filename,
                caption=caption
            )
            await send_main_menu(update, context)
        else:
            await query.edit_message_text("❌ Gagal membuat file. Silakan coba lagi.")
    
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await query.edit_message_text("❌ Terjadi kesalahan saat export data.")


# ============= ADD TRANSACTION (CONVERSATION) =============

async def start_add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai conversation untuk menambah transaksi - With subscription check"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check subscription limits
    subscription = db.get_user_subscription(user_id)
    tier = subscription['tier']
    tier_info = SUBSCRIPTION_TIERS[tier]
    
    # Check transaction limit
    if tier_info['max_transactions'] != 'unlimited':
        current_count = db.get_transaction_count(user_id)
        if current_count >= tier_info['max_transactions']:
            text = (
                f"⚠️ <b>Transaction Limit Reached</b>\n\n"
                f"Your {tier_info['name']} plan allows up to "
                f"{tier_info['max_transactions']} transactions.\n\n"
                f"Current: {current_count}/{tier_info['max_transactions']}\n\n"
                f"👑 Upgrade to unlock unlimited transactions!"
            )
            keyboard = [
                [InlineKeyboardButton("👑 Upgrade Now", callback_data="subscription_menu")],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            return ConversationHandler.END
    
    user_data_temp[user_id] = {'mode': MODE_PERSONAL}
    
    keyboard = [
        [InlineKeyboardButton("💰 Pemasukan", callback_data="trans_income")],
        [InlineKeyboardButton("💸 Pengeluaran", callback_data="trans_expense")],
        [InlineKeyboardButton("❌ Batal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💰 <b>Tambah Transaksi</b>\n\nPilih tipe transaksi:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return TRANS_TYPE


async def transaction_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memilih tipe transaksi"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    trans_type = 'income' if 'income' in query.data else 'expense'
    user_data_temp[user_id]['type'] = trans_type
    
    # Pilih kategori berdasarkan tipe
    categories = INCOME_CATEGORIES if trans_type == 'income' else EXPENSE_CATEGORIES
    
    keyboard = []
    for i in range(0, len(categories), 2):
        row = [InlineKeyboardButton(categories[i], callback_data=f"cat_{i}")]
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i + 1], callback_data=f"cat_{i+1}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    type_text = "Pemasukan" if trans_type == 'income' else "Pengeluaran"
    await query.edit_message_text(
        f"📂 <b>Pilih Kategori {type_text}:</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return TRANS_CATEGORY


async def transaction_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memilih kategori"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cat_index = int(query.data.split('_')[1])
    
    trans_type = user_data_temp[user_id]['type']
    categories = INCOME_CATEGORIES if trans_type == 'income' else EXPENSE_CATEGORIES
    category = categories[cat_index]
    
    user_data_temp[user_id]['category'] = category
    
    await query.edit_message_text(
        f"💵 <b>Masukkan Nominal:</b>\n\n"
        f"Kategori: {category}\n\n"
        f"Ketik nominal dalam angka (contoh: 50000)",
        parse_mode='HTML'
    )
    
    return TRANS_AMOUNT


async def transaction_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk input nominal"""
    user_id = update.effective_user.id
    amount_text = update.message.text
    
    # Validasi nominal
    is_valid, amount = validate_amount(amount_text)
    
    if not is_valid:
        await update.message.reply_text(
            "❌ Nominal tidak valid!\n\n"
            "Silakan masukkan angka yang benar (contoh: 50000)"
        )
        return TRANS_AMOUNT
    
    user_data_temp[user_id]['amount'] = amount
    
    await update.message.reply_text(
        f"📝 <b>Masukkan Deskripsi/Catatan:</b>\n\n"
        f"Nominal: {format_currency(amount)}\n\n"
        f"Ketik deskripsi singkat atau ketik /skip untuk melewati",
        parse_mode='HTML'
    )
    
    return TRANS_DESC


async def transaction_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk input deskripsi dan menyimpan transaksi"""
    user_id = update.effective_user.id
    description = update.message.text if update.message.text != '/skip' else '-'
    
    # Ambil data dari temporary storage
    data = user_data_temp[user_id]
    
    # Simpan ke database
    success = db.add_transaction(
        user_id=user_id,
        trans_type=data['type'],
        category=data['category'],
        amount=data['amount'],
        description=description,
        mode=data['mode']
    )
    
    if success:
        type_emoji = "💰" if data['type'] == 'income' else "💸"
        type_text = "Pemasukan" if data['type'] == 'income' else "Pengeluaran"
        
        await update.message.reply_text(
            f"✅ <b>Transaksi Berhasil Disimpan!</b>\n\n"
            f"{type_emoji} Tipe: {type_text}\n"
            f"📂 Kategori: {data['category']}\n"
            f"💵 Nominal: {format_currency(data['amount'])}\n"
            f"📝 Deskripsi: {description}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Gagal menyimpan transaksi. Silakan coba lagi.")
    
    # Clear temporary data
    del user_data_temp[user_id]
    
    # Kembali ke main menu
    await send_main_menu(update, context)
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation handler"""
    user_id = update.effective_user.id
    if user_id in user_data_temp:
        del user_data_temp[user_id]
    
    await send_main_menu(update, context)
    return ConversationHandler.END


# ============= BUSINESS MODE (DEBT MANAGEMENT) =============

async def show_business_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu bisnis"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Tambah Hutang/Piutang", callback_data="add_debt")],
        [InlineKeyboardButton("📋 Lihat Daftar", callback_data="view_debts")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💼 <b>Mode Bisnis</b>\n\n"
        "Kelola hutang dan piutang bisnis Anda:"
    )
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def start_add_debt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai conversation untuk menambah hutang/piutang"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data_temp[user_id] = {}
    
    keyboard = [
        [InlineKeyboardButton("💳 Hutang (Saya Berhutang)", callback_data="debt_hutang")],
        [InlineKeyboardButton("💰 Piutang (Saya Menagih)", callback_data="debt_piutang")],
        [InlineKeyboardButton("❌ Batal", callback_data="business_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💼 <b>Tambah Hutang/Piutang</b>\n\nPilih tipe:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return DEBT_TYPE


async def debt_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memilih tipe hutang/piutang"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    debt_type = 'hutang' if 'hutang' in query.data else 'piutang'
    user_data_temp[user_id]['type'] = debt_type
    
    type_text = "berhutang kepada" if debt_type == 'hutang' else "memiliki piutang dari"
    
    await query.edit_message_text(
        f"👤 <b>Nama Orang/Pihak:</b>\n\n"
        f"Anda {type_text} siapa?\n\n"
        f"Ketik nama orang atau perusahaan:",
        parse_mode='HTML'
    )
    
    return DEBT_PERSON


async def debt_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk input nama orang"""
    user_id = update.effective_user.id
    person_name = update.message.text
    
    user_data_temp[user_id]['person'] = person_name
    
    await update.message.reply_text(
        f"💵 <b>Masukkan Nominal:</b>\n\n"
        f"Ketik nominal dalam angka (contoh: 1000000)",
        parse_mode='HTML'
    )
    
    return DEBT_AMOUNT


async def debt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk input nominal hutang/piutang"""
    user_id = update.effective_user.id
    amount_text = update.message.text
    
    # Validasi nominal
    is_valid, amount = validate_amount(amount_text)
    
    if not is_valid:
        await update.message.reply_text(
            "❌ Nominal tidak valid!\n\n"
            "Silakan masukkan angka yang benar (contoh: 1000000)"
        )
        return DEBT_AMOUNT
    
    user_data_temp[user_id]['amount'] = amount
    
    await update.message.reply_text(
        f"📝 <b>Masukkan Keterangan:</b>\n\n"
        f"Nominal: {format_currency(amount)}\n\n"
        f"Ketik keterangan atau ketik /skip untuk melewati",
        parse_mode='HTML'
    )
    
    return DEBT_DESC


async def debt_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk input deskripsi dan menyimpan hutang/piutang"""
    user_id = update.effective_user.id
    description = update.message.text if update.message.text != '/skip' else '-'
    
    # Ambil data dari temporary storage
    data = user_data_temp[user_id]
    
    # Simpan ke database
    success = db.add_debt(
        user_id=user_id,
        debt_type=data['type'],
        person_name=data['person'],
        amount=data['amount'],
        description=description
    )
    
    if success:
        type_emoji = "💳" if data['type'] == 'hutang' else "💰"
        type_text = "Hutang" if data['type'] == 'hutang' else "Piutang"
        
        await update.message.reply_text(
            f"✅ <b>{type_text} Berhasil Dicatat!</b>\n\n"
            f"{type_emoji} Tipe: {type_text}\n"
            f"👤 Nama: {data['person']}\n"
            f"💵 Nominal: {format_currency(data['amount'])}\n"
            f"📝 Keterangan: {description}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Gagal menyimpan data. Silakan coba lagi.")
    
    # Clear temporary data
    del user_data_temp[user_id]
    
    # Kembali ke business menu
    keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu Bisnis", callback_data="business_menu")]]
    await update.message.reply_text(
        "Pilih menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def view_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan daftar hutang/piutang"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    debts = db.get_debts(user_id)
    
    if not debts:
        text = "📋 <b>Daftar Hutang/Piutang</b>\n\n❌ Belum ada data."
    else:
        text = "📋 <b>Daftar Hutang/Piutang</b>\n" + "="*30 + "\n\n"
        
        for debt in debts:
            emoji = "💳" if debt['type'] == 'hutang' else "💰"
            type_text = "Hutang" if debt['type'] == 'hutang' else "Piutang"
            
            text += (
                f"{emoji} <b>{type_text}</b>\n"
                f"👤 {debt['person']}\n"
                f"💵 {format_currency(debt['amount'])}\n"
                f"📝 {debt['description']}\n"
                f"📅 {debt['date'][:10]}\n\n"
            )
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="business_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


# ============= ADMIN PANEL =============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /admin - HANYA UNTUK ADMIN"""
    user_id = update.effective_user.id
    
    # Security check
    if not is_admin(user_id):
        # Jangan respon apa-apa untuk non-admin (silent rejection)
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 Backup Database", callback_data="admin_backup")],
        [InlineKeyboardButton("👥 User List", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔐 <b>ADMIN PANEL</b>\n"
        "="*30 + "\n\n"
        "Selamat datang, Admin!\n"
        "Pilih menu di bawah:"
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan statistik sistem"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    total_users = db.get_total_users()
    total_transactions = db.get_total_transactions()
    active_today = db.get_active_users_today()
    
    stats_text = (
        "📊 <b>System Statistics</b>\n"
        "="*30 + "\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"💳 Total Transactions: <b>{total_transactions}</b>\n"
        f"✅ Active Today: <b>{active_today}</b>\n\n"
        f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='HTML')


async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim backup database ke admin"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text("⏳ Preparing database backup...")
    
    try:
        # Kirim file database
        with open('finance.db', 'rb') as db_file:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=db_file,
                filename=f"backup_finance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                caption="💾 <b>Database Backup</b>\n\nSimpan file ini dengan aman!",
                parse_mode='HTML'
            )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(
            "✅ Backup berhasil dikirim!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    except Exception as e:
        logger.error(f"Error sending backup: {e}")
        await query.edit_message_text("❌ Gagal mengirim backup database.")


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim daftar user ke admin"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text("⏳ Preparing user list...")
    
    try:
        users = db.get_all_users_info()
        
        if not users:
            await query.edit_message_text("❌ Belum ada user terdaftar.")
            return
        
        # Export ke CSV
        csv_buffer = export_to_csv(users)
        
        if csv_buffer:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=csv_buffer,
                filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
                caption=f"👥 <b>User List</b>\n\nTotal: {len(users)} users",
                parse_mode='HTML'
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
            await query.edit_message_text(
                "✅ User list berhasil dikirim!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❌ Gagal membuat user list.")
    
    except Exception as e:
        logger.error(f"Error sending user list: {e}")
        await query.edit_message_text("❌ Terjadi kesalahan.")


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai broadcast message"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Ketik pesan yang ingin dikirim ke semua user:\n\n"
        "⚠️ Pesan akan dikirim ke SEMUA user!\n"
        "Ketik /cancel untuk membatalkan.",
        parse_mode='HTML'
    )
    
    return BROADCAST_MESSAGE


async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim broadcast message ke semua user"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    message = update.message.text
    user_ids = db.get_all_user_ids()
    
    await update.message.reply_text(
        f"📤 Mengirim broadcast ke {len(user_ids)} users...\n"
        "Mohon tunggu..."
    )
    
    success_count = 0
    fail_count = 0
    
    broadcast_text = f"📢 <b>Pengumuman dari Admin</b>\n\n{message}"
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode='HTML'
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            fail_count += 1
    
    result_text = (
        f"✅ <b>Broadcast Selesai!</b>\n\n"
        f"✅ Berhasil: {success_count}\n"
        f"❌ Gagal: {fail_count}"
    )
    
    await update.message.reply_text(result_text, parse_mode='HTML')
    
    return ConversationHandler.END


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback untuk kembali ke admin panel"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 Backup Database", callback_data="admin_backup")],
        [InlineKeyboardButton("👥 User List", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔐 <b>ADMIN PANEL</b>\n"
        "="*30 + "\n\n"
        "Pilih menu:"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def admin_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menutup admin panel"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    await query.edit_message_text("🔐 Admin panel ditutup.")




# ============= SUBSCRIPTION MENU =============

async def show_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu subscription dengan pricing"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    subscription = db.get_user_subscription(user_id)
    current_tier = subscription['tier']
    
    # Build subscription info text
    text = (
        "👑 <b>FinanceHub Subscription Plans</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for tier_key, tier_info in SUBSCRIPTION_TIERS.items():
        badge = "🆓" if tier_key == 'free' else ("⭐" if tier_key == 'basic' else "👑")
        is_current = " ✅ <i>(Current Plan)</i>" if tier_key == current_tier else ""
        
        text += f"{badge} <b>{tier_info['name']} Plan</b>{is_current}\n"
        
        if tier_info['price'] > 0:
            text += f"💰 Rp {tier_info['price']:,}/bulan\n"
        else:
            text += f"💰 FREE\n"
        
        text += f"\n<b>Features:</b>\n"
        for feature in tier_info['features']:
            text += f"  ✓ {feature}\n"
        
        text += "\n"
    
    text += (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Upgrade untuk unlock semua fitur premium!</i>"
    )
    
    keyboard = []
    
    # Show upgrade buttons if not premium
    if current_tier != 'premium':
        if current_tier == 'free':
            keyboard.append([
                InlineKeyboardButton("⭐ Upgrade ke Basic", callback_data="upgrade_basic"),
                InlineKeyboardButton("👑 Upgrade ke Premium", callback_data="upgrade_premium")
            ])
        elif current_tier == 'basic':
            keyboard.append([
                InlineKeyboardButton("👑 Upgrade ke Premium", callback_data="upgrade_premium")
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def show_upgrade_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan informasi upgrade dan cara pembayaran"""
    query = update.callback_query
    await query.answer()
    
    tier = 'basic' if 'basic' in query.data else 'premium'
    tier_info = SUBSCRIPTION_TIERS[tier]
    badge = "⭐" if tier == 'basic' else "👑"
    
    text = (
        f"{badge} <b>Upgrade ke {tier_info['name']} Plan</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Harga:</b> Rp {tier_info['price']:,}/bulan\n\n"
        f"<b>✨ Fitur yang Anda dapatkan:</b>\n"
    )
    
    for feature in tier_info['features']:
        text += f"  ✓ {feature}\n"
    
    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>📱 Cara Pembayaran:</b>\n\n"
        f"1️⃣ Transfer ke rekening:\n"
        f"   <code>BCA: 1234567890</code>\n"
        f"   <code>a.n. FinanceHub</code>\n\n"
        f"2️⃣ Kirim bukti transfer ke admin\n"
        f"3️⃣ Tunggu konfirmasi (max 1x24 jam)\n"
        f"4️⃣ Akun Anda akan di-upgrade!\n\n"
        f"💡 <i>Hubungi admin untuk proses lebih cepat</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/youradmin")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="subscription_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


async def show_transaction_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan riwayat transaksi terbaru"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    transactions = db.get_all_transactions(user_id, MODE_PERSONAL)
    
    if not transactions:
        text = (
            "📋 <b>Riwayat Transaksi</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ Belum ada transaksi.\n\n"
            "Mulai catat transaksi Anda sekarang!"
        )
    else:
        text = (
            "📋 <b>Riwayat Transaksi Terbaru</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # Show last 10 transactions
        for i, trans in enumerate(transactions[:10], 1):
            emoji = "💰" if trans['Tipe'] == 'income' else "💸"
            text += (
                f"{i}. {emoji} <b>{trans['Kategori']}</b>\n"
                f"   {format_currency(trans['Nominal'])}\n"
                f"   📝 {trans['Deskripsi']}\n"
                f"   📅 {trans['Tanggal'][:10]}\n\n"
            )
        
        if len(transactions) > 10:
            text += f"<i>... dan {len(transactions) - 10} transaksi lainnya</i>\n\n"
        
        text += "💡 <i>Export untuk melihat semua transaksi</i>"
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


# ============= CALLBACK QUERY ROUTER =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router untuk semua callback query"""
    query = update.callback_query
    data = query.data
    
    # Update last active
    db.update_last_active(update.effective_user.id)
    
    # Route berdasarkan callback data
    if data == "main_menu":
        await send_main_menu(update, context)
    elif data == "dashboard":
        await show_dashboard(update, context)
    elif data == "visual_report":
        await show_visual_report(update, context)
    elif data.startswith("chart_"):
        await generate_chart(update, context)
    elif data == "export_menu":
        await show_export_menu(update, context)
    elif data.startswith("export_"):
        await export_data(update, context)
    elif data == "business_menu":
        await show_business_menu(update, context)
    elif data == "view_debts":
        await view_debts(update, context)
    elif data == "subscription_menu":
        await show_subscription_menu(update, context)
    elif data.startswith("upgrade_"):
        await show_upgrade_info(update, context)
    elif data == "transaction_history":
        await show_transaction_history(update, context)
    elif data == "help":
        await help_command(update, context)
    elif data == "admin_panel":
        await admin_panel_callback(update, context)
    elif data == "admin_stats":
        await admin_stats(update, context)
    elif data == "admin_backup":
        await admin_backup(update, context)
    elif data == "admin_users":
        await admin_users(update, context)
    elif data == "admin_close":
        await admin_close(update, context)


# ============= MAIN FUNCTION =============

def main():
    """Main function untuk menjalankan bot dengan webhook (Web Service)"""
    
    # Validasi TOKEN dan ADMIN_ID
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ BOT_TOKEN belum diset! Set environment variable BOT_TOKEN")
        return
    
    if ADMIN_ID == 0:
        logger.warning("⚠️ ADMIN_ID belum diset! Admin panel tidak akan berfungsi.")
    
    # Build application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Conversation handler untuk Add Transaction
    trans_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_transaction, pattern="^add_transaction$")],
        states={
            TRANS_TYPE: [CallbackQueryHandler(transaction_type, pattern="^trans_")],
            TRANS_CATEGORY: [CallbackQueryHandler(transaction_category, pattern="^cat_")],
            TRANS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, transaction_amount)],
            TRANS_DESC: [MessageHandler(filters.TEXT, transaction_description)]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^main_menu$"),
            CommandHandler("cancel", cancel_conversation)
        ],
        per_message=False
    )
    application.add_handler(trans_conv_handler)
    
    # Conversation handler untuk Add Debt
    debt_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_debt, pattern="^add_debt$")],
        states={
            DEBT_TYPE: [CallbackQueryHandler(debt_type, pattern="^debt_")],
            DEBT_PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_person)],
            DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_amount)],
            DEBT_DESC: [MessageHandler(filters.TEXT, debt_description)]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^business_menu$"),
            CommandHandler("cancel", cancel_conversation)
        ],
        per_message=False
    )
    application.add_handler(debt_conv_handler)
    
    # Conversation handler untuk Broadcast (Admin only)
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$")],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False
    )
    application.add_handler(broadcast_conv_handler)
    
    # Callback query handler (harus di akhir)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Get webhook URL from environment or construct from Render
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        # Construct from Render service URL
        render_service_url = os.getenv('RENDER_EXTERNAL_URL')
        if render_service_url:
            webhook_url = f"{render_service_url}/{BOT_TOKEN}"
        else:
            logger.error("❌ WEBHOOK_URL or RENDER_EXTERNAL_URL not set!")
            return
    
    # Get port from environment (Render provides this)
    port = int(os.getenv('PORT', 10000))
    
    # Start bot with webhook
    logger.info("🚀 Starting bot with webhook...")
    logger.info(f"📊 Database: {db.db_path}")
    logger.info(f"👤 Admin ID: {ADMIN_ID if ADMIN_ID != 0 else 'Not set'}")
    logger.info(f"🌐 Webhook URL: {webhook_url}")
    logger.info(f"🔌 Port: {port}")
    
    # Run webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == '__main__':
    main()
