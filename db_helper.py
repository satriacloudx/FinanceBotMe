"""
Database Helper untuk mengelola SQLite Database
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class DBHelper:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Membuat koneksi ke database"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Inisialisasi tabel database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabel Users - Enhanced with subscription
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_start DATE,
                    subscription_end DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabel Transactions - Enhanced
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    category TEXT,
                    amount REAL,
                    description TEXT,
                    mode TEXT DEFAULT 'personal',
                    tags TEXT,
                    is_recurring INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel Debts - Enhanced
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    person_name TEXT,
                    amount REAL,
                    description TEXT,
                    status TEXT DEFAULT 'unpaid',
                    due_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel Budgets - NEW
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    amount REAL,
                    period TEXT DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel Subscription History - NEW
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tier TEXT,
                    amount REAL,
                    payment_method TEXT,
                    payment_proof TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Menambahkan atau update user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding user: {e}")
    
    def update_last_active(self, user_id: int):
        """Update waktu terakhir user aktif"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', 
                         (datetime.now(), user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating last active: {e}")
    
    def add_transaction(self, user_id: int, trans_type: str, category: str, 
                       amount: float, description: str, mode: str = 'personal'):
        """Menambahkan transaksi baru"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, type, category, amount, description, mode)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, trans_type, category, amount, description, mode))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    def get_balance(self, user_id: int, mode: str = 'personal') -> Dict:
        """Mendapatkan saldo dan statistik"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total pemasukan
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE user_id = ? AND type = 'income' AND mode = ?
            ''', (user_id, mode))
            total_income = cursor.fetchone()[0]
            
            # Total pengeluaran
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE user_id = ? AND type = 'expense' AND mode = ?
            ''', (user_id, mode))
            total_expense = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'income': total_income,
                'expense': total_expense,
                'balance': total_income - total_expense
            }
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {'income': 0, 'expense': 0, 'balance': 0}
    
    def get_monthly_balance(self, user_id: int, mode: str = 'personal') -> Dict:
        """Mendapatkan saldo bulan ini"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            current_month = datetime.now().strftime('%Y-%m')
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE user_id = ? AND type = 'income' AND mode = ?
                AND strftime('%Y-%m', created_at) = ?
            ''', (user_id, mode, current_month))
            monthly_income = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE user_id = ? AND type = 'expense' AND mode = ?
                AND strftime('%Y-%m', created_at) = ?
            ''', (user_id, mode, current_month))
            monthly_expense = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'income': monthly_income,
                'expense': monthly_expense,
                'balance': monthly_income - monthly_expense
            }
        except Exception as e:
            logger.error(f"Error getting monthly balance: {e}")
            return {'income': 0, 'expense': 0, 'balance': 0}
    
    def get_transactions_by_category(self, user_id: int, trans_type: str, 
                                    mode: str = 'personal') -> List[Tuple]:
        """Mendapatkan transaksi berdasarkan kategori untuk chart"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND type = ? AND mode = ?
                GROUP BY category
                ORDER BY total DESC
            ''', (user_id, trans_type, mode))
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error getting transactions by category: {e}")
            return []
    
    def get_all_transactions(self, user_id: int, mode: str = 'personal') -> List[Dict]:
        """Mendapatkan semua transaksi user untuk export"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT type, category, amount, description, created_at
                FROM transactions
                WHERE user_id = ? AND mode = ?
                ORDER BY created_at DESC
            ''', (user_id, mode))
            
            columns = ['Tipe', 'Kategori', 'Nominal', 'Deskripsi', 'Tanggal']
            transactions = []
            for row in cursor.fetchall():
                transactions.append(dict(zip(columns, row)))
            
            conn.close()
            return transactions
        except Exception as e:
            logger.error(f"Error getting all transactions: {e}")
            return []
    
    # === DEBT MANAGEMENT ===
    def add_debt(self, user_id: int, debt_type: str, person_name: str, 
                 amount: float, description: str):
        """Menambahkan hutang/piutang"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO debts (user_id, type, person_name, amount, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, debt_type, person_name, amount, description))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding debt: {e}")
            return False
    
    def get_debts(self, user_id: int, status: str = 'unpaid') -> List[Dict]:
        """Mendapatkan daftar hutang/piutang"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, type, person_name, amount, description, created_at
                FROM debts
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            ''', (user_id, status))
            
            debts = []
            for row in cursor.fetchall():
                debts.append({
                    'id': row[0],
                    'type': row[1],
                    'person': row[2],
                    'amount': row[3],
                    'description': row[4],
                    'date': row[5]
                })
            
            conn.close()
            return debts
        except Exception as e:
            logger.error(f"Error getting debts: {e}")
            return []
    
    
    # === SUBSCRIPTION FUNCTIONS ===
    def get_user_subscription(self, user_id: int) -> Dict:
        """Mendapatkan info subscription user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT subscription_tier, subscription_start, subscription_end
                FROM users WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                from datetime import datetime
                tier = result[0] or 'free'
                is_active = True
                
                if result[2]:  # subscription_end exists
                    end_date = datetime.strptime(result[2], '%Y-%m-%d')
                    is_active = datetime.now() < end_date
                
                return {
                    'tier': tier,
                    'start_date': result[1],
                    'end_date': result[2],
                    'is_active': is_active
                }
            return {'tier': 'free', 'is_active': True}
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return {'tier': 'free', 'is_active': True}
    
    def update_subscription(self, user_id: int, tier: str, days: int = 30):
        """Update subscription user"""
        try:
            from datetime import datetime, timedelta
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                UPDATE users 
                SET subscription_tier = ?, subscription_start = ?, subscription_end = ?
                WHERE user_id = ?
            ''', (tier, start_date, end_date, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return False
    
    def get_transaction_count(self, user_id: int) -> int:
        """Mendapatkan jumlah transaksi user (untuk limit check)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting transaction count: {e}")
            return 0
    
    # === ADMIN FUNCTIONS ===
    def get_total_users(self) -> int:
        """Mendapatkan jumlah total user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total users: {e}")
            return 0
    
    def get_total_transactions(self) -> int:
        """Mendapatkan jumlah total transaksi"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total transactions: {e}")
            return 0
    
    def get_active_users_today(self) -> int:
        """Mendapatkan jumlah user aktif hari ini"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(last_active) = ?
            ''', (today,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting active users today: {e}")
            return 0
    
    def get_all_user_ids(self) -> List[int]:
        """Mendapatkan semua user ID untuk broadcast"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            user_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            return user_ids
        except Exception as e:
            logger.error(f"Error getting all user IDs: {e}")
            return []
    
    def get_all_users_info(self) -> List[Dict]:
        """Mendapatkan info semua user untuk export"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, created_at, last_active
                FROM users
                ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'User ID': row[0],
                    'Username': row[1] or 'N/A',
                    'First Name': row[2] or 'N/A',
                    'Last Name': row[3] or 'N/A',
                    'Joined': row[4],
                    'Last Active': row[5]
                })
            
            conn.close()
            return users
        except Exception as e:
            logger.error(f"Error getting all users info: {e}")
            return []
