"""
Configuration file untuk Telegram Bot Manajemen Keuangan
Simpan TOKEN dan ADMIN_ID di environment variables untuk keamanan
"""
import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Ganti dengan Telegram User ID Admin

# Database Configuration
DB_PATH = os.getenv('DB_PATH', 'finance.db')

# Categories - Expanded & Professional
INCOME_CATEGORIES = [
    '💰 Gaji/Salary', 
    '💼 Bisnis/Business', 
    '📈 Investasi/Investment',
    '🎁 Hadiah/Gift', 
    '🏆 Bonus/Commission',
    '🏠 Sewa/Rental Income',
    '💵 Freelance/Project',
    '🔄 Lainnya/Others'
]

EXPENSE_CATEGORIES = [
    '🍔 Makanan & Minuman', 
    '🚗 Transportasi', 
    '🏠 Rumah & Utilitas',
    '🎮 Hiburan & Rekreasi', 
    '👔 Belanja & Fashion', 
    '💊 Kesehatan & Medis',
    '📚 Pendidikan & Kursus', 
    '🏢 Operasional Bisnis', 
    '👥 Gaji Karyawan',
    '📱 Komunikasi & Internet',
    '🎯 Marketing & Iklan',
    '🔧 Maintenance & Repair',
    '💳 Cicilan & Hutang',
    '🎁 Hadiah & Donasi',
    '💼 Pajak & Asuransi',
    '🔄 Lainnya'
]

# Subscription Tiers
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'max_transactions': 50,
        'max_categories': 5,
        'export_limit': 10,
        'chart_types': ['pie'],
        'features': ['Basic Dashboard', 'Simple Reports', 'Limited Export']
    },
    'basic': {
        'name': 'Basic',
        'price': 29000,  # IDR per month
        'max_transactions': 500,
        'max_categories': 'unlimited',
        'export_limit': 100,
        'chart_types': ['pie', 'bar', 'line'],
        'features': ['Advanced Dashboard', 'All Chart Types', 'Unlimited Export', 'Priority Support']
    },
    'premium': {
        'name': 'Premium',
        'price': 79000,  # IDR per month
        'max_transactions': 'unlimited',
        'max_categories': 'unlimited',
        'export_limit': 'unlimited',
        'chart_types': ['pie', 'bar', 'line', 'trend'],
        'features': [
            'All Basic Features',
            'Unlimited Transactions',
            'Advanced Analytics',
            'Budget Planning',
            'Recurring Transactions',
            'Multi-Currency Support',
            'Custom Categories',
            'API Access',
            'Priority Support 24/7'
        ]
    }
}

# Mode Types
MODE_PERSONAL = 'personal'
MODE_BUSINESS = 'business'
