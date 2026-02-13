"""
Database Models for SQLite Version
Same structure as PostgreSQL but optimized for SQLite
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from .engine import Base

class ProfileType(enum.Enum):
    """Profile type enumeration"""
    PERSONAL = "personal"
    BUSINESS = "business"

class TransactionType(enum.Enum):
    """Transaction type enumeration"""
    INCOME = "income"
    EXPENSE = "expense"

class User(Base):
    """User model - Telegram users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    active_profile = Column(String, default="personal")  # SQLite doesn't have native Enum
    is_admin = Column(Integer, default=0)  # SQLite uses INTEGER for boolean
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.telegram_id} - {self.full_name}>"

class Wallet(Base):
    """Wallet model - Separate wallets for Personal & Business"""
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="IDR")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Wallet {self.name} - {self.profile_type}>"

class Category(Base):
    """Category model - Predefined categories"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    emoji = Column(String, default="💰")
    type = Column(String, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.emoji} {self.name}>"

class Transaction(Base):
    """Transaction model - Income & Expense records"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.type} {self.amount}>"

class BroadcastLog(Base):
    """Broadcast log - Track broadcast messages"""
    __tablename__ = "broadcast_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    total_users = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=False)  # Admin telegram_id
    
    def __repr__(self):
        return f"<Broadcast {self.id} - {self.success_count}/{self.total_users}>"
