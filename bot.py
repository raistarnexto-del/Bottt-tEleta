#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║                    XLERO SHOP V7 ULTIMATE                        ║
║                   Professional Telegram Bot                       ║
║                      8000+ Lines Edition                          ║
╠══════════════════════════════════════════════════════════════════╣
║  Features:                                                        ║
║  • Advanced AI Customer Support                                   ║
║  • Smart Payment Verification (Vodafone/USDT/InstaPay)           ║
║  • Real-time Blockchain Verification                              ║
║  • Intelligent Fraud Detection                                    ║
║  • Multi-level User System                                        ║
║  • Advanced Admin Dashboard                                       ║
║  • Promotional Posts System                                       ║
║  • YouTube Video Ads Support                                      ║
║  • Triple Balance Verification                                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import logging
import time
import random
import requests
import hashlib
import sqlite3
import json
import re
import base64
import io
import threading
import asyncio
import secrets
import html
import string
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import traceback

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputMediaPhoto, BotCommand, ChatPermissions,
    InputMediaVideo, InputMediaDocument
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError, BadRequest, Forbidden

# ══════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ══════════════════════════════════════════════════════════════════

class ColoredFormatter(logging.Formatter):
    """Custom colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging():
    """Initialize advanced logging system"""
    logger = logging.getLogger('XLERO')
    logger.setLevel(logging.DEBUG)
    
    # File handler with rotation
    file_handler = logging.FileHandler(
        'xlero_bot.log', 
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ══════════════════════════════════════════════════════════════════
# ENUMS AND CONSTANTS
# ══════════════════════════════════════════════════════════════════

class PaymentMethod(Enum):
    VODAFONE = "vodafone"
    USDT = "usdt"
    INSTAPAY = "instapay"
    BANK = "bank"
    UNKNOWN = "unknown"

class PaymentStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class TicketStatus(Enum):
    OPEN = "open"
    PENDING_USER = "pending_user"
    PENDING_ADMIN = "pending_admin"
    RESOLVED = "resolved"
    CLOSED = "closed"

class UserLevel(Enum):
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    LEGENDARY = 5
    IMPERIAL = 6

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROMO = "promo"
    ORDER = "order"
    DEPOSIT = "deposit"
    LEVEL_UP = "level_up"

# ══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════

@dataclass
class BotConfiguration:
    """Main bot configuration"""
    
    # Bot credentials
    BOT_TOKEN: str = '8359845352:AAEw1whUiOmnOBzUvOiIlUSdu0l6Opoc07g'
    
    # AI Configuration
    HF_API_TOKEN: str = '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'
    HF_API_URL: str = 'https://router.huggingface.co/v1/chat/completions'
    AI_MODEL: str = 'google/gemma-3-27b-it'
    AI_VISION_MODEL: str = 'google/gemma-3-27b-it'
    AI_MAX_TOKENS: int = 1000
    AI_TEMPERATURE: float = 0.7
    AI_TIMEOUT: int = 60
    
    # Telegram IDs
    ADMIN_IDS: List[int] = field(default_factory=lambda: [7384284034])
    CHANNEL_ID: str = '-1002904714010'
    GROUP_ID: str = '-1002904714010'
    
    # Payment Configuration
    VODAFONE_NUMBER: str = '01034573708'
    VODAFONE_NAME: str = 'م*** ع** السلام'
    USDT_WALLET: str = '0x8E00A980274Cfb22798290586d97F7D185E3092D'
    USDT_NETWORK: str = 'BSC (BEP20)'
    
    # Blockchain API
    BSCSCAN_API_KEY: str = 'D8JX395ZQ8D95NIY15H5NYUNVD3KPVVDWN'
    USDT_CONTRACT: str = '0x55d398326f99059fF775485246999027B3197955'
    BSCSCAN_URL: str = 'https://api.bscscan.com/api'
    
    # Financial Settings
    USDT_TO_EGP_RATE: float = 50.0
    MIN_DEPOSIT: float = 25.0
    MAX_DEPOSIT: float = 50000.0
    DEPOSIT_FEE_PERCENT: float = 2.0
    DEPOSIT_FEE_MAX: float = 5.0
    AUTO_APPROVE_THRESHOLD: float = 30.0
    MIN_WITHDRAWAL: float = 50.0
    
    # Bonuses and Rewards
    WELCOME_BONUS: float = 5.0
    REFERRAL_BONUS: float = 4.0
    REFERRAL_ORDER_BONUS: float = 5.0
    DAILY_BASE_REWARD: float = 1.0
    MAX_DAILY_STREAK_BONUS: int = 3
    
    # Promotional Settings
    PROMO_INTERVAL_SECONDS: int = 3600  # 1 hour
    FAKE_POSTS_INTERVAL: int = 1800     # 30 minutes
    
    # Security Settings
    MAX_FAILED_ATTEMPTS: int = 5
    BAN_DURATION_HOURS: int = 24
    SESSION_TIMEOUT_MINUTES: int = 10
    RATE_LIMIT_MESSAGES: int = 30
    RATE_LIMIT_SECONDS: int = 60
    
    # System Settings
    DATABASE_PATH: str = 'xlero_v7_database.db'
    CACHE_TTL_SECONDS: int = 300
    MAX_CONCURRENT_REQUESTS: int = 100
    
    # UI Settings
    ITEMS_PER_PAGE: int = 10
    MAX_MESSAGE_LENGTH: int = 4000


class BotState:
    """Runtime bot state"""
    
    def __init__(self):
        self.bot_username: Optional[str] = None
        self.bot_id: Optional[int] = None
        self.start_time: datetime = datetime.now()
        self.fake_users_count: int = 17399
        self.is_maintenance: bool = False
        self.maintenance_message: str = ""
        self.active_sessions: Dict[int, datetime] = {}
        self.rate_limits: Dict[int, List[datetime]] = defaultdict(list)
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.pending_broadcasts: List[Dict] = []
        self.ai_requests_count: int = 0
        self.total_messages_processed: int = 0
        
    def increment_fake_users(self, min_val: int = 1, max_val: int = 5):
        """Increment fake users counter"""
        self.fake_users_count += random.randint(min_val, max_val)
        return self.fake_users_count
    
    def get_uptime(self) -> str:
        """Get bot uptime as formatted string"""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=Config.RATE_LIMIT_SECONDS)
        
        # Clean old entries
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id] if t > cutoff
        ]
        
        if len(self.rate_limits[user_id]) >= Config.RATE_LIMIT_MESSAGES:
            return True
        
        self.rate_limits[user_id].append(now)
        return False
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=Config.CACHE_TTL_SECONDS):
                return value
            del self.cache[key]
        return None
    
    def set_cached(self, key: str, value: Any):
        """Set cached value"""
        self.cache[key] = (value, datetime.now())


# Global instances
Config = BotConfiguration()
state = BotState()
db_lock = threading.Lock()

# ══════════════════════════════════════════════════════════════════
# FAKE EGYPTIAN NAMES GENERATOR
# ══════════════════════════════════════════════════════════════════

class EgyptianNameGenerator:
    """Generate realistic Egyptian names for fake posts"""
    
    FIRST_NAMES_MALE = [
        'محمد', 'أحمد', 'محمود', 'علي', 'عمر', 'يوسف', 'حسن', 'إبراهيم',
        'عبدالله', 'عبدالرحمن', 'خالد', 'مصطفى', 'كريم', 'ياسر', 'طارق',
        'سامي', 'هاني', 'وليد', 'رامي', 'شريف', 'باسم', 'عماد', 'أيمن',
        'حازم', 'سيف', 'مروان', 'فادي', 'تامر', 'هشام', 'أسامة',
        'زياد', 'آدم', 'يزيد', 'مالك', 'نور', 'جمال', 'صلاح', 'أمير'
    ]
    
    FIRST_NAMES_FEMALE = [
        'فاطمة', 'مريم', 'نور', 'سارة', 'ياسمين', 'هبة', 'رنا', 'دينا',
        'منى', 'هدى', 'سلمى', 'ريم', 'لمى', 'جنى', 'روان', 'ملك',
        'نورهان', 'إسراء', 'آية', 'شيماء', 'بسمة', 'أميرة', 'رانيا'
    ]
    
    LAST_NAMES = [
        'السيد', 'الشريف', 'عبدالواحد', 'المصري', 'الحسيني', 'العربي',
        'الجوهري', 'الفقي', 'النجار', 'الحداد', 'البنا', 'الشرقاوي',
        'المنوفي', 'الغريب', 'حسين', 'سالم', 'إسماعيل', 'رمضان',
        'عيد', 'فوزي', 'صبحي', 'زكي', 'فهمي', 'رشدي', 'حلمي',
        'شوقي', 'توفيق', 'نصر', 'سعيد', 'عطية', 'بدوي', 'جابر'
    ]
    
    @classmethod
    def generate(cls, gender: str = None) -> str:
        """Generate a random Egyptian name"""
        if gender is None:
            gender = random.choice(['male', 'female'])
        
        if gender == 'male':
            first = random.choice(cls.FIRST_NAMES_MALE)
        else:
            first = random.choice(cls.FIRST_NAMES_FEMALE)
        
        last = random.choice(cls.LAST_NAMES)
        return f"{first} {last}"
    
    @classmethod
    def generate_male(cls) -> str:
        return cls.generate('male')
    
    @classmethod
    def generate_female(cls) -> str:
        return cls.generate('female')


# ══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_number(num: float, decimals: int = 0) -> str:
    """Format number with thousand separators"""
    if decimals == 0:
        return f"{int(num):,}"
    return f"{num:,.{decimals}f}"


def format_currency(amount: float, currency: str = "ج.م") -> str:
    """Format currency amount"""
    return f"{format_number(amount)} {currency}"


def generate_order_id() -> str:
    """Generate unique order ID"""
    timestamp = int(time.time()) % 100000
    random_part = random.randint(100, 999)
    return f"XL{timestamp}{random_part}"


def generate_reference() -> str:
    """Generate transaction reference"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_time_ago(dt: datetime) -> str:
    """Get human readable time ago string"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return "الآن"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"منذ {minutes} دقيقة"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"منذ {hours} ساعة"
    else:
        days = seconds // 86400
        return f"منذ {days} يوم"


def validate_player_id(player_id: str, game: str = None) -> Tuple[bool, str]:
    """Validate player ID format"""
    if not player_id:
        return False, "المعرف فارغ"
    
    if not player_id.isdigit():
        return False, "المعرف يجب أن يحتوي على أرقام فقط"
    
    if len(player_id) < 5:
        return False, "المعرف قصير جداً (5 أرقام على الأقل)"
    
    if len(player_id) > 15:
        return False, "المعرف طويل جداً (15 رقم كحد أقصى)"
    
    return True, "صحيح"


def validate_txid(txid: str) -> Tuple[bool, str]:
    """Validate blockchain transaction ID"""
    if not txid:
        return False, "TXID فارغ"
    
    # BSC/ETH transaction hash format
    if re.match(r'^0x[a-fA-F0-9]{64}$', txid):
        return True, "صحيح"
    
    return False, "TXID غير صحيح - يجب أن يبدأ بـ 0x ويتكون من 66 حرف"


def calculate_deposit_fee(amount: float) -> Tuple[float, float]:
    """Calculate deposit fee and final amount"""
    fee = min(amount * Config.DEPOSIT_FEE_PERCENT / 100, Config.DEPOSIT_FEE_MAX)
    final_amount = round(amount - fee, 2)
    return fee, final_amount


def calculate_cashback(amount: float, base_percent: float, level_bonus: float = 0) -> float:
    """Calculate cashback amount"""
    total_percent = base_percent + level_bonus
    return round(amount * total_percent / 100, 2)


# ══════════════════════════════════════════════════════════════════
# DECORATORS
# ══════════════════════════════════════════════════════════════════

def admin_only(func):
    """Decorator to restrict function to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            if update.callback_query:
                await update.callback_query.answer("⛔ غير مصرح لك", show_alert=True)
            else:
                await update.message.reply_text("⛔ هذا الأمر للمديرين فقط")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def rate_limited(func):
    """Decorator to apply rate limiting"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Admins are exempt from rate limiting
        if user_id in Config.ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        if state.check_rate_limit(user_id):
            if update.callback_query:
                await update.callback_query.answer(
                    "⚠️ أنت ترسل طلبات كثيرة، انتظر قليلاً",
                    show_alert=True
                )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper


def maintenance_check(func):
    """Decorator to check maintenance mode"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if state.is_maintenance and user_id not in Config.ADMIN_IDS:
            msg = state.maintenance_message or "🔧 البوت تحت الصيانة حالياً، عد لاحقاً"
            if update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            elif update.message:
                await update.message.reply_text(msg)
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper


def log_action(action_name: str):
    """Decorator to log user actions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else None
            logger.info(f"Action: {action_name} | User: {user_id}")
            state.total_messages_processed += 1
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def error_handler_decorator(func):
    """Decorator to handle errors gracefully"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            try:
                if update.callback_query:
                    await update.callback_query.answer("❌ حدث خطأ", show_alert=True)
                elif update.message:
                    await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
            except:
                pass
    return wrapper
    # ══════════════════════════════════════════════════════════════════
# DATABASE SYSTEM
# ══════════════════════════════════════════════════════════════════

class DatabaseManager:
    """Advanced database manager with connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = Config.DATABASE_PATH
        self._local = threading.local()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self._local.connection = conn
        return self._local.connection
    
    def execute(
        self, 
        query: str, 
        params: tuple = (), 
        fetch_one: bool = False, 
        fetch_all: bool = False
    ) -> Any:
        """Execute database query with automatic error handling"""
        with db_lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                elif fetch_all:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    conn.commit()
                    return cursor.lastrowid
                    
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}\nQuery: {query[:200]}")
                if conn:
                    conn.rollback()
                raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets"""
        with db_lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            except sqlite3.Error as e:
                logger.error(f"Database executemany error: {e}")
                conn.rollback()
                raise
    
    def transaction(self, queries: List[Tuple[str, tuple]]) -> bool:
        """Execute multiple queries in a transaction"""
        with db_lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                for query, params in queries:
                    cursor.execute(query, params)
                conn.commit()
                return True
            except sqlite3.Error as e:
                logger.error(f"Transaction error: {e}")
                conn.rollback()
                return False
    
    def initialize(self):
        """Initialize all database tables"""
        tables = self._get_table_definitions()
        for table_sql in tables:
            self.execute(table_sql)
        
        indexes = self._get_index_definitions()
        for index_sql in indexes:
            self.execute(index_sql)
        
        self._init_default_config()
        self._init_user_levels()
        
        # Initialize products if empty
        product_count = self.execute(
            "SELECT COUNT(*) as c FROM products",
            fetch_one=True
        )['c']
        
        if product_count == 0:
            self._init_products()
        
        logger.info("✅ Database initialized successfully")
    
    def _get_table_definitions(self) -> List[str]:
        """Get all table creation SQL statements"""
        return [
            # Users table
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0,
                pending_balance REAL DEFAULT 0,
                points INTEGER DEFAULT 0,
                spent REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                successful_orders INTEGER DEFAULT 0,
                total_deposits REAL DEFAULT 0,
                deposit_count INTEGER DEFAULT 0,
                referrer_id INTEGER,
                referral_earnings REAL DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                trust_score INTEGER DEFAULT 50,
                vip_status INTEGER DEFAULT 0,
                vip_expires TEXT,
                cashback_total REAL DEFAULT 0,
                banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                ban_until TEXT,
                banned_by INTEGER,
                warnings INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                last_failed_attempt TEXT,
                join_date TEXT,
                last_active TEXT,
                last_order TEXT,
                last_deposit TEXT,
                language TEXT DEFAULT 'ar',
                timezone TEXT DEFAULT 'Africa/Cairo',
                notifications_enabled INTEGER DEFAULT 1,
                email_notifications INTEGER DEFAULT 0,
                email TEXT,
                phone TEXT,
                notes TEXT,
                tags TEXT,
                metadata TEXT
            )""",
            
            # Transactions table
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category TEXT,
                reference TEXT,
                description TEXT,
                fee REAL DEFAULT 0,
                balance_before REAL,
                balance_after REAL,
                status TEXT DEFAULT 'completed',
                related_id INTEGER,
                related_type TEXT,
                metadata TEXT,
                ip_hash TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Deposits table with enhanced fields
            """CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                amount_after_fee REAL,
                payment_method TEXT NOT NULL,
                payment_details TEXT,
                image_hash TEXT,
                image_file_id TEXT,
                txid TEXT,
                reference_number TEXT,
                sender_name TEXT,
                sender_phone TEXT,
                status TEXT DEFAULT 'pending',
                ai_analysis TEXT,
                ai_confidence REAL,
                ai_detected_amount REAL,
                ai_detected_phone TEXT,
                ai_detected_type TEXT,
                risk_score INTEGER DEFAULT 0,
                risk_factors TEXT,
                verification_method TEXT,
                verification_attempts INTEGER DEFAULT 0,
                admin_notes TEXT,
                reviewed_by INTEGER,
                reviewed_at TEXT,
                rejection_reason TEXT,
                auto_approved INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Orders table with enhanced tracking
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                product_key TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER DEFAULT 1,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                original_price REAL,
                discount_amount REAL DEFAULT 0,
                discount_code TEXT,
                discount_type TEXT,
                cashback_amount REAL DEFAULT 0,
                cashback_percent REAL DEFAULT 0,
                input_data TEXT,
                delivery_data TEXT,
                delivery_method TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                is_urgent INTEGER DEFAULT 0,
                notes TEXT,
                admin_notes TEXT,
                internal_notes TEXT,
                processed_by INTEGER,
                processing_started TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                completed_at TEXT,
                cancelled_at TEXT,
                cancel_reason TEXT,
                refund_amount REAL,
                refund_reason TEXT,
                rating INTEGER,
                rating_comment TEXT,
                rated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Products table with full features
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subcategory TEXT,
                item_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_en TEXT,
                short_name TEXT,
                description TEXT,
                description_en TEXT,
                instructions TEXT,
                price REAL NOT NULL,
                original_price REAL,
                cost REAL DEFAULT 0,
                profit_margin REAL,
                min_price REAL,
                max_price REAL,
                currency TEXT DEFAULT 'EGP',
                required_fields TEXT,
                optional_fields TEXT,
                field_validations TEXT,
                delivery_time TEXT DEFAULT 'فوري',
                delivery_method TEXT DEFAULT 'auto',
                stock INTEGER DEFAULT -1,
                reserved_stock INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 1,
                max_quantity INTEGER DEFAULT 10,
                bulk_discounts TEXT,
                cashback_percent REAL DEFAULT 3,
                points_earned INTEGER DEFAULT 0,
                is_featured INTEGER DEFAULT 0,
                is_new INTEGER DEFAULT 0,
                is_hot INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                requires_verification INTEGER DEFAULT 0,
                age_restricted INTEGER DEFAULT 0,
                region_restrictions TEXT,
                sold_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 5.0,
                rating_count INTEGER DEFAULT 0,
                tags TEXT,
                seo_keywords TEXT,
                image_url TEXT,
                icon TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                created_by INTEGER,
                metadata TEXT
            )""",
            
            # Coupons table
            """CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                description TEXT,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_purchase REAL DEFAULT 0,
                max_discount REAL,
                usage_count INTEGER DEFAULT 0,
                max_usage INTEGER,
                max_per_user INTEGER DEFAULT 1,
                applicable_categories TEXT,
                applicable_products TEXT,
                excluded_products TEXT,
                user_restrictions TEXT,
                level_required INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 1,
                starts_at TEXT,
                expires_at TEXT,
                created_by INTEGER,
                created_at TEXT,
                updated_at TEXT
            )""",
            
            # Coupon usage tracking
            """CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                coupon_code TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                order_id TEXT,
                original_amount REAL,
                discount_amount REAL,
                used_at TEXT NOT NULL,
                FOREIGN KEY (coupon_id) REFERENCES coupons(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Support tickets
            """CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE,
                user_id INTEGER NOT NULL,
                subject TEXT,
                category TEXT DEFAULT 'general',
                subcategory TEXT,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'open',
                assigned_to INTEGER,
                related_order TEXT,
                related_deposit INTEGER,
                tags TEXT,
                first_response_at TEXT,
                last_activity TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                resolved_at TEXT,
                closed_at TEXT,
                closed_by INTEGER,
                close_reason TEXT,
                satisfaction_rating INTEGER,
                satisfaction_comment TEXT,
                is_escalated INTEGER DEFAULT 0,
                escalated_to INTEGER,
                escalated_at TEXT,
                sla_deadline TEXT,
                sla_breached INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Ticket messages
            """CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id INTEGER,
                sender_name TEXT,
                message TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                attachment_type TEXT,
                attachment_id TEXT,
                attachment_url TEXT,
                is_internal INTEGER DEFAULT 0,
                is_auto_reply INTEGER DEFAULT 0,
                ai_generated INTEGER DEFAULT 0,
                ai_confidence REAL,
                is_read INTEGER DEFAULT 0,
                read_at TEXT,
                edited INTEGER DEFAULT 0,
                edited_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )""",
            
            # Daily rewards
            """CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER PRIMARY KEY,
                last_claim_date TEXT,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                total_claimed REAL DEFAULT 0,
                total_claims INTEGER DEFAULT 0,
                bonus_multiplier REAL DEFAULT 1.0,
                last_bonus_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Referrals
            """CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                referral_code TEXT,
                bonus_amount REAL,
                order_bonus REAL DEFAULT 0,
                total_earnings REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                level INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                activated_at TEXT,
                first_order_at TEXT,
                last_activity TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users(id),
                FOREIGN KEY (referred_id) REFERENCES users(id)
            )""",
            
            # Image hashes for duplicate detection
            """CREATE TABLE IF NOT EXISTS image_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT NOT NULL,
                phash TEXT,
                user_id INTEGER NOT NULL,
                type TEXT,
                amount REAL,
                file_id TEXT,
                status TEXT DEFAULT 'used',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Used transaction IDs
            """CREATE TABLE IF NOT EXISTS used_txids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txid TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL,
                amount_usd REAL,
                network TEXT,
                verified INTEGER DEFAULT 1,
                block_number INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Pending user inputs
            """CREATE TABLE IF NOT EXISTS pending_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_subtype TEXT,
                item_key TEXT,
                current_step INTEGER DEFAULT 0,
                total_steps INTEGER,
                collected_data TEXT DEFAULT '{}',
                validation_errors TEXT,
                coupon_code TEXT,
                session_id TEXT,
                context_data TEXT,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Notifications
            """CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                type TEXT DEFAULT 'info',
                category TEXT,
                action_type TEXT,
                action_data TEXT,
                action_url TEXT,
                image_url TEXT,
                priority INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                read_at TEXT,
                is_dismissed INTEGER DEFAULT 0,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Promotional posts
            """CREATE TABLE IF NOT EXISTS promo_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                chat_id TEXT,
                content TEXT,
                content_type TEXT DEFAULT 'text',
                media_url TEXT,
                media_file_id TEXT,
                post_type TEXT,
                template_used TEXT,
                ai_generated INTEGER DEFAULT 0,
                engagement_clicks INTEGER DEFAULT 0,
                engagement_views INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                scheduled_at TEXT,
                posted_at TEXT,
                expires_at TEXT,
                created_by INTEGER,
                created_at TEXT NOT NULL
            )""",
            
            # Custom announcements
            """CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                media_type TEXT,
                media_url TEXT,
                media_file_id TEXT,
                youtube_url TEXT,
                button_text TEXT,
                button_url TEXT,
                target_audience TEXT DEFAULT 'all',
                target_levels TEXT,
                is_active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                starts_at TEXT,
                expires_at TEXT,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )""",
            
            # Activity logs
            """CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                action_type TEXT,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_hash TEXT,
                user_agent TEXT,
                session_id TEXT,
                created_at TEXT NOT NULL
            )""",
            
            # Security logs
            """CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                category TEXT,
                details TEXT,
                evidence TEXT,
                ip_hash TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_by INTEGER,
                resolved_at TEXT,
                resolution_notes TEXT,
                created_at TEXT NOT NULL
            )""",
            
            # Fraud records
            """CREATE TABLE IF NOT EXISTS fraud_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT,
                severity INTEGER DEFAULT 1,
                description TEXT,
                evidence TEXT,
                related_ids TEXT,
                action_taken TEXT,
                auto_action INTEGER DEFAULT 0,
                reviewed_by INTEGER,
                reviewed_at TEXT,
                is_confirmed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Flash sales
            """CREATE TABLE IF NOT EXISTS flash_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                product_key TEXT NOT NULL,
                discount_percent REAL NOT NULL,
                discount_amount REAL,
                original_price REAL,
                sale_price REAL,
                max_orders INTEGER,
                current_orders INTEGER DEFAULT 0,
                max_per_user INTEGER DEFAULT 1,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                notify_users INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT,
                updated_at TEXT
            )""",
            
            # Gift cards
            """CREATE TABLE IF NOT EXISTS gift_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                balance REAL,
                currency TEXT DEFAULT 'EGP',
                card_type TEXT DEFAULT 'standard',
                created_by INTEGER,
                purchased_by INTEGER,
                used_by INTEGER,
                recipient_name TEXT,
                recipient_message TEXT,
                is_active INTEGER DEFAULT 1,
                is_redeemed INTEGER DEFAULT 0,
                expires_at TEXT,
                created_at TEXT,
                redeemed_at TEXT,
                last_used_at TEXT
            )""",
            
            # Achievements
            """CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                achievement_name TEXT,
                category TEXT,
                progress INTEGER DEFAULT 0,
                target INTEGER DEFAULT 1,
                completed INTEGER DEFAULT 0,
                reward_type TEXT,
                reward_amount REAL,
                reward_claimed INTEGER DEFAULT 0,
                completed_at TEXT,
                claimed_at TEXT,
                UNIQUE(user_id, achievement_key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Bot configuration
            """CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                value_type TEXT DEFAULT 'string',
                category TEXT,
                description TEXT,
                is_public INTEGER DEFAULT 0,
                updated_by INTEGER,
                updated_at TEXT,
                created_at TEXT
            )""",
            
            # User levels definition
            """CREATE TABLE IF NOT EXISTS user_levels (
                level INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT,
                badge TEXT,
                color TEXT,
                min_spent REAL NOT NULL,
                min_orders INTEGER DEFAULT 0,
                cashback_bonus REAL DEFAULT 0,
                daily_bonus REAL DEFAULT 0,
                referral_bonus REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                priority_support INTEGER DEFAULT 0,
                exclusive_offers INTEGER DEFAULT 0,
                early_access INTEGER DEFAULT 0,
                custom_badge INTEGER DEFAULT 0,
                perks TEXT
            )""",
            
            # AI conversation history for support
            """CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens_used INTEGER,
                model_used TEXT,
                response_time REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )""",
            
            # Scheduled tasks
            """CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                task_data TEXT,
                scheduled_for TEXT NOT NULL,
                executed INTEGER DEFAULT 0,
                executed_at TEXT,
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT NOT NULL
            )""",
            
            # Analytics events
            """CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_name TEXT,
                user_id INTEGER,
                session_id TEXT,
                properties TEXT,
                created_at TEXT NOT NULL
            )"""
        ]
    
    def _get_index_definitions(self) -> List[str]:
        """Get all index creation SQL statements"""
        return [
            # Users indexes
            "CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned)",
            "CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_level ON users(level)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_join_date ON users(join_date)",
            
            # Orders indexes
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_key)",
            
            # Deposits indexes
            "CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status)",
            "CREATE INDEX IF NOT EXISTS idx_deposits_user ON deposits(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_deposits_date ON deposits(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_deposits_method ON deposits(payment_method)",
            
            # Transactions indexes
            "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_at)",
            
            # Tickets indexes
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(assigned_to)",
            
            # Notifications indexes
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
            
            # Activity logs indexes
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_logs(created_at)",
            
            # Security logs indexes
            "CREATE INDEX IF NOT EXISTS idx_security_severity ON security_logs(severity)",
            "CREATE INDEX IF NOT EXISTS idx_security_resolved ON security_logs(resolved)",
            
            # Image hashes indexes
            "CREATE INDEX IF NOT EXISTS idx_image_hash ON image_hashes(hash)",
            "CREATE INDEX IF NOT EXISTS idx_image_user ON image_hashes(user_id)",
            
            # Promo posts indexes
            "CREATE INDEX IF NOT EXISTS idx_promo_date ON promo_posts(created_at)",
            
            # AI conversations indexes
            "CREATE INDEX IF NOT EXISTS idx_ai_conv_user ON ai_conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_ai_conv_session ON ai_conversations(session_id)"
        ]
    
    def _init_default_config(self):
        """Initialize default configuration values"""
        defaults = {
            # Financial settings
            'deposit_fee_percent': (Config.DEPOSIT_FEE_PERCENT, 'float', 'financial', 'نسبة عمولة الإيداع'),
            'deposit_fee_max': (Config.DEPOSIT_FEE_MAX, 'float', 'financial', 'الحد الأقصى لعمولة الإيداع'),
            'min_deposit': (Config.MIN_DEPOSIT, 'float', 'financial', 'الحد الأدنى للإيداع'),
            'max_deposit': (Config.MAX_DEPOSIT, 'float', 'financial', 'الحد الأقصى للإيداع'),
            'auto_approve_threshold': (Config.AUTO_APPROVE_THRESHOLD, 'float', 'financial', 'حد الموافقة التلقائية'),
            'min_withdrawal': (Config.MIN_WITHDRAWAL, 'float', 'financial', 'الحد الأدنى للسحب'),
            'usdt_rate': (Config.USDT_TO_EGP_RATE, 'float', 'financial', 'سعر USDT بالجنيه'),
            
            # Bonus settings
            'welcome_bonus': (Config.WELCOME_BONUS, 'float', 'bonuses', 'مكافأة الترحيب'),
            'referral_bonus': (Config.REFERRAL_BONUS, 'float', 'bonuses', 'مكافأة الإحالة'),
            'referral_order_bonus': (Config.REFERRAL_ORDER_BONUS, 'float', 'bonuses', 'مكافأة أول طلب للمُحال'),
            'daily_base_reward': (Config.DAILY_BASE_REWARD, 'float', 'bonuses', 'المكافأة اليومية'),
            
            # System settings
            'maintenance_mode': (False, 'bool', 'system', 'وضع الصيانة'),
            'maintenance_message': ('', 'string', 'system', 'رسالة الصيانة'),
            'promo_interval': (Config.PROMO_INTERVAL_SECONDS, 'int', 'system', 'فاصل الإعلانات بالثواني'),
            'fake_posts_interval': (Config.FAKE_POSTS_INTERVAL, 'int', 'system', 'فاصل المنشورات الوهمية'),
            
            # AI settings
            'ai_support_enabled': (True, 'bool', 'ai', 'تفعيل الدعم بالذكاء الاصطناعي'),
            'ai_auto_reply': (True, 'bool', 'ai', 'الرد التلقائي بالذكاء الاصطناعي'),
            'ai_confidence_threshold': (0.7, 'float', 'ai', 'حد ثقة الذكاء الاصطناعي'),
        }
        
        now = datetime.now().isoformat()
        for key, (value, value_type, category, desc) in defaults.items():
            existing = self.execute(
                "SELECT 1 FROM bot_config WHERE key=?",
                (key,),
                fetch_one=True
            )
            if not existing:
                self.execute(
                    """INSERT INTO bot_config
                       (key, value, value_type, category, description, created_at, updated_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (key, json.dumps(value), value_type, category, desc, now, now)
                )
    
    def _init_user_levels(self):
        """Initialize user levels"""
        levels = [
            (1, 'برونزي', 'Bronze', '🥉', '#CD7F32', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (2, 'فضي', 'Silver', '🥈', '#C0C0C0', 500, 3, 0.5, 1, 0.5, 2, 0, 0, 0, 0),
            (3, 'ذهبي', 'Gold', '🥇', '#FFD700', 2000, 10, 1.0, 2, 1.0, 5, 1, 0, 0, 0),
            (4, 'بلاتيني', 'Platinum', '💎', '#E5E4E2', 5000, 25, 1.5, 3, 1.5, 7, 1, 1, 0, 0),
            (5, 'أسطوري', 'Legendary', '👑', '#9400D3', 15000, 50, 2.0, 5, 2.0, 10, 1, 1, 1, 0),
            (6, 'إمبراطوري', 'Imperial', '🏆', '#FF4500', 50000, 100, 3.0, 10, 3.0, 15, 1, 1, 1, 1),
        ]
        
        for level_data in levels:
            self.execute(
                """INSERT OR REPLACE INTO user_levels
                   (level, name, name_en, badge, color, min_spent, min_orders,
                    cashback_bonus, daily_bonus, referral_bonus, discount_percent,
                    priority_support, exclusive_offers, early_access, custom_badge)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                level_data
            )
    
    def _init_products(self):
        """Initialize default products"""
        now = datetime.now().isoformat()
        
        products = [
            # Free Fire
            ('freefire', 'diamonds', 'ff_100', '💎 100 جوهرة', '100 Diamonds', 
             'شحن 100 جوهرة فري فاير فوري ومضمون', 53, 60, 45, '["player_id"]', 3, '💎', 1),
            ('freefire', 'diamonds', 'ff_210', '💎 210 جوهرة', '210 Diamonds',
             'شحن 210 جوهرة فري فاير فوري ومضمون', 106, 120, 90, '["player_id"]', 3, '💎', 1),
            ('freefire', 'diamonds', 'ff_530', '💎 530 جوهرة', '530 Diamonds',
             'شحن 530 جوهرة فري فاير فوري ومضمون', 265, 300, 225, '["player_id"]', 3, '💎', 1),
            ('freefire', 'diamonds', 'ff_1060', '💎 1060 جوهرة', '1060 Diamonds',
             'شحن 1060 جوهرة فري فاير فوري ومضمون', 530, 600, 450, '["player_id"]', 4, '💎', 1),
            ('freefire', 'diamonds', 'ff_2180', '💎 2180 جوهرة', '2180 Diamonds',
             'شحن 2180 جوهرة فري فاير فوري ومضمون', 1060, 1200, 900, '["player_id"]', 4, '💎', 1),
            ('freefire', 'diamonds', 'ff_5600', '💎 5600 جوهرة', '5600 Diamonds',
             'شحن 5600 جوهرة فري فاير - أفضل قيمة!', 2650, 3000, 2250, '["player_id"]', 5, '💎', 1),
            
            # PUBG Mobile
            ('pubg', 'uc', 'pubg_60', '🔫 60 UC', '60 UC',
             'شحن 60 UC ببجي موبايل فوري', 49, 55, 42, '["pubg_id"]', 3, '🔫', 1),
            ('pubg', 'uc', 'pubg_325', '🔫 325 UC', '325 UC',
             'شحن 325 UC ببجي موبايل فوري', 249, 280, 210, '["pubg_id"]', 3, '🔫', 1),
            ('pubg', 'uc', 'pubg_660', '🔫 660 UC', '660 UC',
             'شحن 660 UC ببجي موبايل فوري', 495, 560, 420, '["pubg_id"]', 4, '🔫', 1),
            ('pubg', 'uc', 'pubg_1800', '🔫 1800 UC', '1800 UC',
             'شحن 1800 UC ببجي موبايل فوري', 1320, 1500, 1120, '["pubg_id"]', 4, '🔫', 1),
            ('pubg', 'uc', 'pubg_8100', '🔫 8100 UC', '8100 UC',
             'شحن 8100 UC ببجي موبايل - عرض خاص!', 5940, 6750, 5040, '["pubg_id"]', 5, '🔫', 1),
            
            # Mobile Legends
            ('mlbb', 'diamonds', 'ml_86', '💠 86 ماسة', '86 Diamonds',
             'شحن 86 ماسة موبايل ليجندز', 49, 55, 42, '["ml_id","zone_id"]', 2, '💠', 1),
            ('mlbb', 'diamonds', 'ml_172', '💠 172 ماسة', '172 Diamonds',
             'شحن 172 ماسة موبايل ليجندز', 98, 110, 84, '["ml_id","zone_id"]', 2, '💠', 1),
            ('mlbb', 'diamonds', 'ml_257', '💠 257 ماسة', '257 Diamonds',
             'شحن 257 ماسة موبايل ليجندز', 147, 165, 126, '["ml_id","zone_id"]', 3, '💠', 1),
            ('mlbb', 'diamonds', 'ml_706', '💠 706 ماسة', '706 Diamonds',
             'شحن 706 ماسة موبايل ليجندز', 392, 440, 336, '["ml_id","zone_id"]', 4, '💠', 1),
            ('mlbb', 'diamonds', 'ml_2195', '💠 2195 ماسة', '2195 Diamonds',
             'شحن 2195 ماسة موبايل ليجندز - عرض مميز!', 1176, 1320, 1008, '["ml_id","zone_id"]', 5, '💠', 1),
            
            # Steam
            ('steam', 'wallet', 'steam_5', '🎮 ستيم $5', 'Steam $5',
             'بطاقة ستيم 5 دولار أمريكي', 280, 320, 250, None, 2, '🎮', 0),
            ('steam', 'wallet', 'steam_10', '🎮 ستيم $10', 'Steam $10',
             'بطاقة ستيم 10 دولار أمريكي', 560, 640, 500, None, 2, '🎮', 0),
            ('steam', 'wallet', 'steam_20', '🎮 ستيم $20', 'Steam $20',
             'بطاقة ستيم 20 دولار أمريكي', 1120, 1280, 1000, None, 3, '🎮', 0),
            ('steam', 'wallet', 'steam_50', '🎮 ستيم $50', 'Steam $50',
             'بطاقة ستيم 50 دولار أمريكي', 2800, 3200, 2500, None, 4, '🎮', 0),
            
            # Google Play
            ('googleplay', 'cards', 'google_5', '📱 جوجل $5', 'Google Play $5',
             'بطاقة جوجل بلاي 5 دولار', 290, 330, 260, None, 2, '📱', 0),
            ('googleplay', 'cards', 'google_10', '📱 جوجل $10', 'Google Play $10',
             'بطاقة جوجل بلاي 10 دولار', 580, 660, 520, None, 2, '📱', 0),
            ('googleplay', 'cards', 'google_25', '📱 جوجل $25', 'Google Play $25',
             'بطاقة جوجل بلاي 25 دولار', 1450, 1650, 1300, None, 3, '📱', 0),
            
            # iTunes
            ('itunes', 'cards', 'itunes_10', '🍎 آيتونز $10', 'iTunes $10',
             'بطاقة آيتونز 10 دولار', 600, 680, 540, None, 2, '🍎', 0),
            ('itunes', 'cards', 'itunes_25', '🍎 آيتونز $25', 'iTunes $25',
             'بطاقة آيتونز 25 دولار', 1500, 1700, 1350, None, 3, '🍎', 0),
            
            # PlayStation
            ('playstation', 'cards', 'psn_10', '🎮 PSN $10', 'PlayStation $10',
             'بطاقة بلايستيشن 10 دولار', 580, 660, 520, None, 2, '🎮', 0),
            ('playstation', 'cards', 'psn_25', '🎮 PSN $25', 'PlayStation $25',
             'بطاقة بلايستيشن 25 دولار', 1450, 1650, 1300, None, 3, '🎮', 0),
            ('playstation', 'cards', 'psn_50', '🎮 PSN $50', 'PlayStation $50',
             'بطاقة بلايستيشن 50 دولار', 2900, 3300, 2600, None, 4, '🎮', 0),
        ]
        
        for p in products:
            self.execute(
                """INSERT OR IGNORE INTO products 
                   (category, subcategory, item_key, name, name_en, description,
                    price, original_price, cost, required_fields, cashback_percent,
                    icon, is_active, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*p, now)
            )
        
        logger.info(f"✅ Initialized {len(products)} products")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        result = self.execute(
            "SELECT value, value_type FROM bot_config WHERE key=?",
            (key,),
            fetch_one=True
        )
        
        if not result:
            return default
        
        try:
            value = json.loads(result['value'])
            return value
        except:
            return result['value']
    
    def set_config(self, key: str, value: Any, updated_by: int = None):
        """Set configuration value"""
        self.execute(
            """UPDATE bot_config SET value=?, updated_by=?, updated_at=?
               WHERE key=?""",
            (json.dumps(value), updated_by, datetime.now().isoformat(), key)
        )


# Global database instance
db = DatabaseManager()
# ══════════════════════════════════════════════════════════════════
# AI SERVICE - ADVANCED INTELLIGENT SUPPORT
# ══════════════════════════════════════════════════════════════════

class AIService:
    """Advanced AI service for customer support and image analysis"""
    
    # System prompts for different contexts
    SUPPORT_SYSTEM_PROMPT = """أنت مساعد دعم فني ذكي لمتجر "XLERO SHOP" لشحن الألعاب والبطاقات الرقمية.

معلومات المتجر:
- الاسم: XLERO SHOP
- التخصص: شحن ألعاب (فري فاير، ببجي، موبايل ليجندز) وبطاقات رقمية (ستيم، جوجل بلاي، آيتونز، بلايستيشن)
- طرق الدفع: فودافون كاش ({vodafone_number})، USDT (BEP20)
- مميزات: تسليم فوري، ضمان كامل، كاش باك، نظام مستويات

قواعد الرد:
1. كن ودوداً ومحترفاً دائماً
2. أجب بالعربية الفصحى البسيطة
3. إذا كان السؤال عن مشكلة تقنية أو طلب معين، اطلب رقم الطلب
4. إذا كان السؤال خارج نطاق المتجر، وجه المستخدم بلطف
5. استخدم الإيموجي بشكل معتدل
6. إذا لم تستطع المساعدة، أخبر المستخدم أن الإدارة ستتواصل معه

أنت تستطيع المساعدة في:
- الاستفسار عن المنتجات والأسعار
- شرح طرق الدفع والشحن
- حل مشاكل الطلبات البسيطة
- شرح نظام المكافآت والإحالات
- الإجابة عن الأسئلة الشائعة

لا تستطيع:
- إلغاء أو تعديل الطلبات (يحتاج الإدارة)
- استرداد الأموال (يحتاج الإدارة)
- تغيير بيانات المستخدم (يحتاج الإدارة)
- الوعد بخصومات غير موجودة"""

    PAYMENT_ANALYSIS_PROMPT = """أنت خبير في تحليل إيصالات الدفع الإلكتروني في مصر.

مهمتك: تحليل صورة إيصال الدفع واستخراج المعلومات بدقة عالية.

أنواع الإيصالات المدعومة:
1. فودافون كاش (Vodafone Cash):
   - شعار فودافون الأحمر
   - عبارة "تم التحويل بنجاح" أو "Transfer Successful"
   - رقم المستلم
   - المبلغ المحول
   - رقم المعاملة (Transaction ID)
   - التاريخ والوقت

2. USDT/تيثر:
   - Transaction Hash يبدأ بـ 0x
   - المبلغ بـ USDT
   - الشبكة (BSC/BEP20/ERC20/TRC20)
   - حالة المعاملة

3. إنستا باي (InstaPay):
   - شعار إنستا باي
   - رقم المرجع
   - المبلغ
   - اسم المستلم

علامات الإيصال الصحيح:
- وضوح الصورة
- ظهور كل البيانات المطلوبة
- عدم وجود تعديلات واضحة
- التاريخ حديث

علامات الإيصال المشبوه:
- صورة ضبابية أو معدلة
- أرقام غير واضحة
- تناقض في البيانات
- تاريخ قديم جداً"""

    @staticmethod
    def _call_api(
        messages: List[Dict],
        max_tokens: int = 500,
        temperature: float = 0.7,
        timeout: int = 60
    ) -> Optional[str]:
        """Call AI API with error handling"""
        try:
            headers = {
                'Authorization': f'Bearer {Config.HF_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': Config.AI_MODEL,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            
            response = requests.post(
                Config.HF_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            state.ai_requests_count += 1
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"AI API error: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.Timeout:
            logger.error("AI API timeout")
            return None
        except Exception as e:
            logger.error(f"AI API exception: {e}")
            return None
    
    @staticmethod
    def _call_vision_api(
        prompt: str,
        image_base64: str,
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> Optional[str]:
        """Call AI Vision API for image analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {Config.HF_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            messages = [{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{image_base64}'
                        }
                    }
                ]
            }]
            
            payload = {
                'model': Config.AI_VISION_MODEL,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            
            response = requests.post(
                Config.HF_API_URL,
                headers=headers,
                json=payload,
                timeout=90
            )
            
            state.ai_requests_count += 1
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"Vision API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Vision API exception: {e}")
            return None
    
    @classmethod
    def get_support_response(
        cls,
        user_message: str,
        user_info: Dict,
        conversation_history: List[Dict] = None
    ) -> Tuple[str, bool, float]:
        """
        Get AI support response
        Returns: (response, should_escalate, confidence)
        """
        try:
            # Build system prompt with context
            system_prompt = cls.SUPPORT_SYSTEM_PROMPT.format(
                vodafone_number=Config.VODAFONE_NUMBER
            )
            
            # Add user context
            user_context = f"""
معلومات المستخدم الحالي:
- الاسم: {user_info.get('first_name', 'مستخدم')}
- الرصيد: {user_info.get('balance', 0):.0f} ج.م
- عدد الطلبات: {user_info.get('total_orders', 0)}
- المستوى: {user_info.get('level', 1)}
"""
            
            messages = [
                {'role': 'system', 'content': system_prompt + user_context}
            ]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Add current message
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            # Get AI response
            response = cls._call_api(
                messages,
                max_tokens=400,
                temperature=0.7
            )
            
            if not response:
                return (
                    "عذراً، لم أستطع معالجة طلبك حالياً. سيتواصل معك فريق الدعم قريباً. 🙏",
                    True,
                    0.0
                )
            
            # Analyze if escalation is needed
            escalation_keywords = [
                'استرداد', 'رد المبلغ', 'إلغاء الطلب', 'مشكلة كبيرة',
                'لم يصل', 'نصب', 'احتيال', 'شكوى', 'المدير',
                'تحويل خاطئ', 'حساب خاطئ'
            ]
            
            should_escalate = any(
                keyword in user_message.lower() 
                for keyword in escalation_keywords
            )
            
            # Estimate confidence based on response
            confidence = 0.85
            if 'لست متأكد' in response or 'الإدارة' in response:
                confidence = 0.5
                should_escalate = True
            
            return response, should_escalate, confidence
            
        except Exception as e:
            logger.error(f"Support response error: {e}")
            return (
                "حدث خطأ، سيتواصل معك فريق الدعم. 🙏",
                True,
                0.0
            )
    
    @classmethod
    def should_ai_respond(cls, message: str, ticket_context: Dict = None) -> Tuple[bool, str]:
        """
        Determine if AI should respond or escalate to admin
        Returns: (should_ai_respond, reason)
        """
        # Simple questions AI can handle
        simple_patterns = [
            r'كيف (اشحن|أشحن|الشحن)',
            r'(سعر|اسعار|أسعار)',
            r'(طريقة|طرق) (الدفع|الشحن)',
            r'كم (سعر|يكلف|تكلفة)',
            r'هل (يوجد|عندكم|متوفر)',
            r'ما هو (الرصيد|رصيدي)',
            r'(شرح|اشرح|وضح)',
            r'(مرحبا|السلام عليكم|هاي|هلا)',
            r'(شكرا|شكراً|ممتاز|تمام)',
        ]
        
        # Complex issues requiring admin
        complex_patterns = [
            r'(طلب|اوردر|order).*(مشكلة|لم يصل|خطأ)',
            r'(استرداد|رد المبلغ|refund)',
            r'(تحويل|حوالة).*(خاطئ|غلط)',
            r'(اتصل|كلم).*(المدير|الإدارة|admin)',
            r'(شكوى|complain)',
            r'(ساعات|أيام) ولم',
            r'فلوسي (ضاعت|راحت)',
        ]
        
        message_lower = message.lower()
        
        # Check for complex patterns first
        for pattern in complex_patterns:
            if re.search(pattern, message_lower):
                return False, "يحتاج مراجعة الإدارة"
        
        # Check for simple patterns
        for pattern in simple_patterns:
            if re.search(pattern, message_lower):
                return True, "سؤال بسيط"
        
        # Default: let AI try but mark for review
        return True, "سيتم المراجعة"
    
    @classmethod
    def detect_payment_type(cls, image_base64: str) -> Tuple[PaymentMethod, float]:
        """
        Detect payment type from image
        Returns: (payment_method, confidence)
        """
        prompt = """حدد نوع إيصال الدفع في هذه الصورة.

أجب بسطر واحد فقط يحتوي على:
TYPE: [النوع] | CONFIDENCE: [نسبة الثقة من 0 إلى 1]

الأنواع المتاحة:
- VODAFONE: إيصال فودافون كاش (يحتوي شعار فودافون أو كلمة Vodafone أو فودافون)
- USDT: معاملة USDT/تيثر/عملة رقمية (يحتوي 0x أو transaction hash)
- INSTAPAY: إيصال إنستا باي
- BANK: تحويل بنكي
- UNKNOWN: غير واضح أو ليس إيصال دفع

مثال الإجابة:
TYPE: VODAFONE | CONFIDENCE: 0.95"""

        result = cls._call_vision_api(prompt, image_base64, max_tokens=50)
        
        if result:
            result_upper = result.upper()
            
            # Parse response
            confidence = 0.5
            conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', result_upper)
            if conf_match:
                try:
                    confidence = float(conf_match.group(1))
                except:
                    pass
            
            if 'VODAFONE' in result_upper:
                return PaymentMethod.VODAFONE, confidence
            elif 'USDT' in result_upper:
                return PaymentMethod.USDT, confidence
            elif 'INSTAPAY' in result_upper:
                return PaymentMethod.INSTAPAY, confidence
            elif 'BANK' in result_upper:
                return PaymentMethod.BANK, confidence
        
        return PaymentMethod.UNKNOWN, 0.0
    
    @classmethod
    def analyze_vodafone_receipt(
        cls,
        image_base64: str,
        expected_phone: str
    ) -> Dict[str, Any]:
        """
        Analyze Vodafone Cash receipt with enhanced detection
        """
        prompt = f"""حلل إيصال فودافون كاش في هذه الصورة بدقة عالية.

المطلوب التحقق منه:
- رقم المستلم المتوقع: {expected_phone}

استخرج المعلومات التالية:
1. هل هذا إيصال فودافون كاش صحيح؟
2. المبلغ المحول (رقم فقط)
3. رقم المستلم
4. هل الرقم يطابق المتوقع؟
5. رقم المعاملة (Transaction ID) إن وجد
6. التاريخ إن وجد
7. نسبة الثقة في التحليل

علامات إيصال فودافون كاش الصحيح:
- شعار Vodafone أو فودافون
- عبارة "تم التحويل بنجاح" أو "Transfer Successful" أو "تم تحويل مبلغ"
- ظهور المبلغ بوضوح
- ظهور رقم المستلم
- رقم معاملة

أجب بـ JSON فقط بالتنسيق التالي:
{{
    "is_valid": true/false,
    "is_vodafone": true/false,
    "amount": الرقم أو 0,
    "receiver_phone": "الرقم أو null",
    "phone_matches": true/false,
    "transaction_id": "الرقم أو null",
    "date": "التاريخ أو null",
    "confidence": 0.0 إلى 1.0,
    "error": "رسالة الخطأ أو null",
    "details": "تفاصيل إضافية"
}}"""

        result = cls._call_vision_api(prompt, image_base64, max_tokens=300)
        
        default_response = {
            'is_valid': False,
            'is_vodafone': False,
            'amount': 0,
            'receiver_phone': None,
            'phone_matches': False,
            'transaction_id': None,
            'date': None,
            'confidence': 0.0,
            'error': 'فشل تحليل الصورة',
            'details': None
        }
        
        if not result:
            return default_response
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Validate phone match
                if data.get('receiver_phone'):
                    phone = str(data['receiver_phone']).replace(' ', '')
                    # Check if phone contains expected number
                    data['phone_matches'] = (
                        expected_phone in phone or 
                        phone in expected_phone or
                        phone[-8:] == expected_phone[-8:]
                    )
                
                # Overall validity
                data['is_valid'] = (
                    data.get('is_vodafone', False) and
                    data.get('phone_matches', False) and
                    data.get('amount', 0) > 0 and
                    data.get('confidence', 0) >= 0.6
                )
                
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in vodafone analysis: {e}")
        
        return default_response
    
    @classmethod
    def analyze_usdt_transaction(cls, image_base64: str) -> Dict[str, Any]:
        """
        Analyze USDT transaction image
        """
        prompt = """حلل صورة معاملة USDT/تيثر واستخرج المعلومات التالية:

1. Transaction Hash (TXID) - يبدأ بـ 0x ويتكون من 66 حرف
2. المبلغ بـ USDT
3. حالة المعاملة (Success/Completed/Confirmed/Pending/Failed)
4. الشبكة (BSC/BEP20/ERC20/TRC20)
5. عنوان المستلم إن ظهر
6. التاريخ والوقت إن ظهر

أجب بـ JSON فقط:
{
    "txid": "0x..." أو null,
    "amount": الرقم أو 0,
    "status": "success/pending/failed/unknown",
    "network": "BSC/ETH/TRC20/unknown",
    "to_address": "العنوان أو null",
    "timestamp": "التاريخ أو null",
    "confidence": 0.0 إلى 1.0,
    "error": null أو "رسالة الخطأ"
}"""

        result = cls._call_vision_api(prompt, image_base64, max_tokens=250)
        
        default_response = {
            'txid': None,
            'amount': 0,
            'status': 'unknown',
            'network': 'unknown',
            'to_address': None,
            'timestamp': None,
            'confidence': 0.0,
            'error': 'فشل تحليل الصورة'
        }
        
        if not result:
            return default_response
        
        try:
            json_match = re.search(r'\{[^{}]*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Validate TXID format
                txid = data.get('txid', '')
                if txid and not re.match(r'^0x[a-fA-F0-9]{64}$', str(txid)):
                    # Try to extract valid txid
                    txid_match = re.search(r'0x[a-fA-F0-9]{64}', str(txid))
                    data['txid'] = txid_match.group() if txid_match else None
                
                return data
                
        except json.JSONDecodeError:
            pass
        
        return default_response
    
    @classmethod
    def generate_promotional_post(cls, post_type: str = 'general') -> str:
        """
        Generate AI-powered promotional post
        """
        users_count = state.increment_fake_users()
        
        themes = {
            'general': [
                'عرض خاص', 'خصم حصري', 'فرصة ذهبية', 'صفقة اليوم',
                'عرض لفترة محدودة', 'أسعار مخفضة'
            ],
            'games': [
                'للجيمرز فقط', 'عشاق الألعاب', 'شحن سريع', 'أرخص سعر'
            ],
            'weekend': [
                'عروض نهاية الأسبوع', 'خصم الجمعة', 'عرض السبت'
            ]
        }
        
        games = ['فري فاير', 'ببجي موبايل', 'موبايل ليجندز', 'ستيم', 'جوجل بلاي']
        
        prompt = f"""اكتب إعلان ترويجي مميز وفريد بالعربية لمتجر "XLERO SHOP".

📌 معلومات المتجر:
- متخصص في شحن الألعاب: {', '.join(random.sample(games, 3))}
- البطاقات الرقمية: ستيم، جوجل بلاي، آيتونز، بلايستيشن
- خصومات تصل لـ 25%
- تسليم فوري خلال دقائق
- دفع عبر: فودافون كاش، USDT
- عدد العملاء: أكثر من {users_count:,}
- ضمان 100%

📌 الموضوع: {random.choice(themes.get(post_type, themes['general']))}

📌 متطلبات:
1. استخدم إيموجي جذابة ومتنوعة
2. اجعله مختلف وإبداعي
3. أضف إحساس بالعجلة
4. اختم بدعوة للعمل
5. الطول: 150-250 كلمة
6. لا تستخدم روابط

اكتب الإعلان الآن:"""

        result = cls._call_api(
            [{'role': 'user', 'content': prompt}],
            max_tokens=500,
            temperature=0.95
        )
        
        if result and len(result) > 100:
            return result
        
        # Fallback templates
        return cls._get_fallback_promo(users_count)
    
    @classmethod
    def _get_fallback_promo(cls, users_count: int) -> str:
        """Get fallback promotional post"""
        templates = [
            f"""🔥🔥🔥 *XLERO SHOP* 🔥🔥🔥

⚡ أقوى عروض شحن الألعاب! ⚡

💎 شحن فوري لجميع ألعابك المفضلة!
🎮 فري فاير • ببجي • موبايل ليجندز

━━━━━━━━━━━━━━━━━━

🏆 *لماذا نحن الأفضل؟*

✅ أسعار أقل بـ 25%
✅ تسليم فوري
✅ ضمان 100%
✅ دعم 24/7

━━━━━━━━━━━━━━━━━━

📱 فودافون كاش | 💎 USDT

👥 +{users_count:,} عميل سعيد!

🚀 *ابدأ الآن!* 🚀""",

            f"""⭐ *عرض لا يُفوَّت!* ⭐

🎮 يا جيمرز! الفرصة وصلت!

💰 خصومات خرافية على كل الشحنات!
⚡ تسليم فوري مضمون!

━━━━━━━━━━━━━━━━━━

🔥 *المتاح:*
💎 فري فاير - أرخص سعر
🔫 ببجي UC - فوري
⚔️ موبايل ليجندز - مضمون
🎮 ستيم - أصلي 100%

━━━━━━━━━━━━━━━━━━

👥 +{users_count:,} يثقون بنا!

🔥 *XLERO - الأفضل دائماً!* 🔥""",

            f"""💥 *مفاجأة XLERO!* 💥

🎯 أفضل أسعار الشحن في مصر!

*XLERO SHOP* يقدم:
💎 شحن جميع الألعاب
⚡ تسليم خلال دقائق
💰 أسعار لا تُقارن
🛡️ ضمان كامل

━━━━━━━━━━━━━━━━━━

📱 ادفع بسهولة:
• فودافون كاش
• USDT

👥 {users_count:,}+ عميل!

🚀 *اشحن الآن!* 🚀"""
        ]
        
        return random.choice(templates)
    
    @classmethod
    def generate_fake_deposit_post(cls) -> str:
        """Generate fake deposit celebration post"""
        name = EgyptianNameGenerator.generate_male()
        amount = random.choice([
            100, 150, 200, 250, 300, 500, 750, 1000, 
            1500, 2000, 3000, 5000, 7500, 10000
        ])
        
        # Add some randomness to amount
        amount += random.randint(-20, 50)
        
        templates = [
            f"""💰 *إيداع جديد!*

👤 {name}
💵 أودع *{amount:,} ج.م*

مبارك! 🎉✨""",

            f"""✅ *تم الإيداع بنجاح!*

🏆 {name}
💳 {amount:,} ج.م

شكراً لثقتك! 🙏""",

            f"""🔥 *عملية إيداع*

👤 {name}
💰 +{amount:,} ج.م

أهلاً بك في XLERO! 🚀"""
        ]
        
        return random.choice(templates)
    
    @classmethod
    def generate_fake_referral_post(cls) -> str:
        """Generate fake referral celebration post"""
        name = EgyptianNameGenerator.generate()
        count = random.randint(5, 200)
        
        templates = [
            f"""👥 *إحالات ناجحة!*

🏆 {name}
👫 دعا *{count}* شخص

مبارك عليك! 🎉🩵""",

            f"""🌟 *نجم الإحالات!*

👤 {name}
✨ {count} إحالة ناجحة

استمر! 💪🔥""",

            f"""🎊 *تهانينا!*

{name}
دعا {count} صديق للمتجر!

أنت رائع! 🏆"""
        ]
        
        return random.choice(templates)


# ══════════════════════════════════════════════════════════════════
# BLOCKCHAIN VERIFICATION SERVICE
# ══════════════════════════════════════════════════════════════════

class BlockchainVerifier:
    """BSC/Ethereum blockchain transaction verifier"""
    
    BSCSCAN_URL = "https://api.bscscan.com/api"
    
    # USDT Contract addresses
    CONTRACTS = {
        'BSC': '0x55d398326f99059fF775485246999027B3197955',  # USDT on BSC
        'ETH': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT on ETH
    }
    
    # Transfer event signature
    TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    
    @classmethod
    def verify_transaction(
        cls,
        txid: str,
        expected_wallet: str,
        expected_amount: float = None
    ) -> Dict[str, Any]:
        """
        Verify BSC transaction on blockchain
        Triple verification:
        1. Transaction exists and successful
        2. Correct recipient
        3. Amount matches (if provided)
        """
        result = {
            'valid': False,
            'verified': False,
            'amount': 0,
            'amount_usd': 0,
            'from_address': None,
            'to_address': None,
            'block_number': None,
            'timestamp': None,
            'confirmations': 0,
            'error': None,
            'verification_steps': []
        }
        
        # Step 1: Validate TXID format
        if not cls._validate_txid(txid):
            result['error'] = 'TXID غير صحيح - يجب أن يبدأ بـ 0x ويتكون من 66 حرف'
            result['verification_steps'].append('❌ تنسيق TXID غير صحيح')
            return result
        
        result['verification_steps'].append('✅ تنسيق TXID صحيح')
        
        # Step 2: Check if TXID already used
        if cls._is_txid_used(txid):
            result['error'] = 'هذا TXID مستخدم من قبل!'
            result['verification_steps'].append('❌ TXID مستخدم مسبقاً')
            return result
        
        result['verification_steps'].append('✅ TXID لم يُستخدم من قبل')
        
        # Step 3: Get transaction receipt from blockchain
        try:
            receipt = cls._get_transaction_receipt(txid)
            
            if not receipt:
                result['error'] = 'المعاملة غير موجودة أو لم يتم تأكيدها بعد'
                result['verification_steps'].append('❌ المعاملة غير موجودة')
                return result
            
            result['verification_steps'].append('✅ المعاملة موجودة')
            
            # Step 4: Check transaction status
            if receipt.get('status') != '0x1':
                result['error'] = 'المعاملة فاشلة على البلوكتشين'
                result['verification_steps'].append('❌ المعاملة فاشلة')
                return result
            
            result['verification_steps'].append('✅ المعاملة ناجحة')
            result['block_number'] = int(receipt.get('blockNumber', '0x0'), 16)
            
            # Step 5: Find USDT transfer in logs
            transfer_info = cls._find_usdt_transfer(
                receipt.get('logs', []),
                expected_wallet
            )
            
            if not transfer_info['found']:
                result['error'] = transfer_info.get('error', 'لم يتم العثور على تحويل USDT للمحفظة المطلوبة')
                result['verification_steps'].append('❌ ' + result['error'])
                return result
            
            result['verification_steps'].append('✅ تحويل USDT للمحفظة الصحيحة')
            
            result['valid'] = True
            result['verified'] = True
            result['amount'] = transfer_info['amount']
            result['amount_usd'] = transfer_info['amount']
            result['from_address'] = transfer_info['from_address']
            result['to_address'] = transfer_info['to_address']
            
            # Step 6: Verify amount if expected
            if expected_amount:
                amount_diff = abs(result['amount'] - expected_amount)
                if amount_diff > 0.5:  # Allow 0.5 USDT tolerance
                    result['verification_steps'].append(
                        f'⚠️ المبلغ مختلف: متوقع {expected_amount}, فعلي {result["amount"]}'
                    )
                else:
                    result['verification_steps'].append('✅ المبلغ متطابق')
            
            # Get confirmations
            result['confirmations'] = cls._get_confirmations(result['block_number'])
            result['verification_steps'].append(f'✅ {result["confirmations"]} تأكيد')
            
            return result
            
        except requests.Timeout:
            result['error'] = 'انتهت مهلة الاتصال بالبلوكتشين'
            result['verification_steps'].append('❌ انتهت المهلة')
            return result
            
        except Exception as e:
            logger.error(f"Blockchain verification error: {e}")
            result['error'] = 'خطأ في التحقق من البلوكتشين'
            result['verification_steps'].append('❌ خطأ في التحقق')
            return result
    
    @classmethod
    def _validate_txid(cls, txid: str) -> bool:
        """Validate transaction ID format"""
        if not txid:
            return False
        return bool(re.match(r'^0x[a-fA-F0-9]{64}$', txid))
    
    @classmethod
    def _is_txid_used(cls, txid: str) -> bool:
        """Check if TXID was already used"""
        result = db.execute(
            "SELECT 1 FROM used_txids WHERE txid=?",
            (txid.lower(),),
            fetch_one=True
        )
        return result is not None
    
    @classmethod
    def mark_txid_used(
        cls,
        txid: str,
        user_id: int,
        amount: float,
        network: str = 'BSC'
    ):
        """Mark TXID as used"""
        db.execute(
            """INSERT OR IGNORE INTO used_txids
               (txid, user_id, amount, amount_usd, network, created_at)
               VALUES(?,?,?,?,?,?)""",
            (txid.lower(), user_id, amount, amount, network, datetime.now().isoformat())
        )
    
    @classmethod
    def _get_transaction_receipt(cls, txid: str) -> Optional[Dict]:
        """Get transaction receipt from BSCScan API"""
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionReceipt',
            'txhash': txid,
            'apikey': Config.BSCSCAN_API_KEY
        }
        
        response = requests.get(cls.BSCSCAN_URL, params=params, timeout=30)
        data = response.json()
        
        return data.get('result')
    
    @classmethod
    def _find_usdt_transfer(
        cls,
        logs: List[Dict],
        expected_wallet: str
    ) -> Dict[str, Any]:
        """Find USDT transfer in transaction logs"""
        result = {
            'found': False,
            'amount': 0,
            'from_address': None,
            'to_address': None,
            'error': None
        }
        
        expected_wallet_lower = expected_wallet.lower()
        
        for log in logs:
            contract = log.get('address', '').lower()
            
            # Check if this is USDT contract
            if contract != Config.USDT_CONTRACT.lower():
                continue
            
            topics = log.get('topics', [])
            
            # Check for Transfer event
            if len(topics) >= 3 and topics[0] == cls.TRANSFER_TOPIC:
                # Extract addresses from topics
                from_address = '0x' + topics[1][-40:]
                to_address = '0x' + topics[2][-40:]
                
                # Check if recipient matches
                if to_address.lower() == expected_wallet_lower:
                    # Extract amount from data
                    amount_hex = log.get('data', '0x0')
                    amount_wei = int(amount_hex, 16)
                    amount_usdt = amount_wei / (10 ** 18)  # USDT has 18 decimals on BSC
                    
                    result['found'] = True
                    result['amount'] = amount_usdt
                    result['from_address'] = from_address
                    result['to_address'] = to_address
                    return result
        
        result['error'] = 'لم يتم العثور على تحويل USDT للعنوان المطلوب'
        return result
    
    @classmethod
    def _get_confirmations(cls, block_number: int) -> int:
        """Get number of confirmations for a block"""
        try:
            params = {
                'module': 'proxy',
                'action': 'eth_blockNumber',
                'apikey': Config.BSCSCAN_API_KEY
            }
            
            response = requests.get(cls.BSCSCAN_URL, params=params, timeout=10)
            data = response.json()
            
            current_block = int(data.get('result', '0x0'), 16)
            return max(0, current_block - block_number)
            
        except:
            return 0


# ══════════════════════════════════════════════════════════════════
# PAYMENT PROCESSOR
# ══════════════════════════════════════════════════════════════════

class PaymentProcessor:
    """Unified payment processing system"""
    
    @classmethod
    async def process_payment_image(
        cls,
        user: Dict,
        image_bytes: bytes,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """
        Process payment image with full verification
        Returns processing result
        """
        result = {
            'success': False,
            'payment_type': None,
            'amount': 0,
            'final_amount': 0,
            'fee': 0,
            'auto_approved': False,
            'needs_review': True,
            'deposit_id': None,
            'message': '',
            'details': {}
        }
        
        try:
            # Calculate image hash for duplicate detection
            image_hash = hashlib.sha256(image_bytes).hexdigest()
            image_b64 = base64.b64encode(image_bytes).decode()
            
            # Check for duplicate image
            existing = db.execute(
                "SELECT * FROM image_hashes WHERE hash=?",
                (image_hash,),
                fetch_one=True
            )
            
            if existing:
                result['message'] = '🚫 هذه الصورة مستخدمة من قبل!'
                
                # Log fraud attempt
                db.execute(
                    """INSERT INTO fraud_records
                       (user_id, type, description, evidence, created_at)
                       VALUES(?,?,?,?,?)""",
                    (
                        user['id'],
                        'duplicate_image',
                        'محاولة استخدام صورة مكررة',
                        json.dumps({'hash': image_hash[:32], 'original_user': existing['user_id']}),
                        datetime.now().isoformat()
                    )
                )
                return result
            
            # Detect payment type
            payment_type, type_confidence = AIService.detect_payment_type(image_b64)
            result['payment_type'] = payment_type.value
            result['details']['type_confidence'] = type_confidence
            
            logger.info(f"Payment type detected: {payment_type.value} ({type_confidence:.0%})")
            
            # Process based on type
            if payment_type == PaymentMethod.VODAFONE:
                return await cls._process_vodafone(
                    user, image_bytes, image_b64, image_hash, result, context
                )
            elif payment_type == PaymentMethod.USDT:
                return await cls._process_usdt(
                    user, image_bytes, image_b64, image_hash, result, context
                )
            elif payment_type == PaymentMethod.INSTAPAY:
                result['message'] = '📱 إنستا باي قيد التطوير حالياً. استخدم فودافون كاش أو USDT.'
                return result
            else:
                result['message'] = '''❓ *لم نتمكن من التعرف على نوع الدفع*

━━━━━━━━━━━━━━━━━━━━━

📌 *الطرق المدعومة:*
• 📱 فودافون كاش
• 💎 USDT (BEP20)

━━━━━━━━━━━━━━━━━━━━━

💡 تأكد من إرسال صورة واضحة للإيصال'''
                return result
                
        except Exception as e:
            logger.error(f"Payment processing error: {e}", exc_info=True)
            result['message'] = '❌ حدث خطأ أثناء معالجة الصورة'
            return result
    
    @classmethod
    async def _process_vodafone(
        cls,
        user: Dict,
        image_bytes: bytes,
        image_b64: str,
        image_hash: str,
        result: Dict,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict:
        """Process Vodafone Cash payment"""
        
        # Analyze receipt with AI
        analysis = AIService.analyze_vodafone_receipt(
            image_b64,
            Config.VODAFONE_NUMBER
        )
        
        result['details']['ai_analysis'] = analysis
        logger.info(f"Vodafone analysis: {analysis}")
        
        # Validation checks
        if not analysis.get('is_vodafone'):
            result['message'] = '❌ هذا ليس إيصال فودافون كاش صحيح'
            return result
        
        if not analysis.get('phone_matches'):
            result['message'] = f'''❌ *رقم المستلم غير صحيح*

الرقم المتوقع: `{Config.VODAFONE_NUMBER}`
الرقم في الإيصال: `{analysis.get('receiver_phone', 'غير واضح')}`

تأكد من التحويل للرقم الصحيح.'''
            return result
        
        amount = analysis.get('amount', 0)
        
        if amount <= 0:
            result['message'] = '❌ لم نتمكن من قراءة المبلغ من الإيصال'
            return result
        
        if amount < Config.MIN_DEPOSIT:
            result['message'] = f'❌ الحد الأدنى للإيداع {Config.MIN_DEPOSIT:.0f}ج'
            return result
        
        if amount > Config.MAX_DEPOSIT:
            result['message'] = f'❌ الحد الأقصى للإيداع {Config.MAX_DEPOSIT:.0f}ج'
            return result
        
        # Calculate fees
        fee, final_amount = calculate_deposit_fee(amount)
        confidence = analysis.get('confidence', 0)
        
        result['amount'] = amount
        result['final_amount'] = final_amount
        result['fee'] = fee
        
        # Save image hash
        db.execute(
            """INSERT INTO image_hashes
               (hash, user_id, type, amount, created_at)
               VALUES(?,?,?,?,?)""",
            (image_hash, user['id'], 'vodafone', amount, datetime.now().isoformat())
        )
        
        # Determine if auto-approve
        auto_approve = (
            amount <= Config.AUTO_APPROVE_THRESHOLD and
            confidence >= 0.8 and
            user.get('trust_score', 50) >= 40
        )
        
        result['auto_approved'] = auto_approve
        result['needs_review'] = not auto_approve
        
        now = datetime.now().isoformat()
        
        if auto_approve:
            # Create approved deposit
            dep_id = db.execute(
                """INSERT INTO deposits
                   (user_id, amount, amount_after_fee, payment_method,
                    image_hash, status, ai_analysis, ai_confidence,
                    ai_detected_amount, auto_approved, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    user['id'], amount, final_amount, 'vodafone',
                    image_hash, 'approved', json.dumps(analysis),
                    confidence, amount, 1, now
                )
            )
            
            result['deposit_id'] = dep_id
            
            # Add balance
            new_balance = UserManager.update_balance(
                user['id'],
                final_amount,
                'deposit',
                f'VF_{dep_id}',
                f'إيداع فودافون #{dep_id}',
                fee
            )
            
            result['success'] = True
            result['message'] = f'''✅ *تم إيداع رصيدك بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

💵 المبلغ: {amount:.0f}ج
💸 العمولة: {fee:.1f}ج
💰 الصافي: *{final_amount:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك الجديد: *{new_balance:.0f}ج*'''

            # Notify admins
            await cls._notify_admins_deposit(
                context, user, dep_id, amount, final_amount,
                'vodafone', auto_approved=True, confidence=confidence
            )
            
        else:
            # Create pending deposit for review
            dep_id = db.execute(
                """INSERT INTO deposits
                   (user_id, amount, amount_after_fee, payment_method,
                    image_hash, status, ai_analysis, ai_confidence,
                    ai_detected_amount, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    user['id'], amount, final_amount, 'vodafone',
                    image_hash, 'pending', json.dumps(analysis),
                    confidence, amount, now
                )
            )
            
            result['deposit_id'] = dep_id
            result['success'] = True
            
            result['message'] = f'''⏳ *جاري مراجعة الإيداع*
━━━━━━━━━━━━━━━━━━━━━

💵 المبلغ: *{amount:.0f}ج*
🆔 رقم الطلب: #{dep_id}

━━━━━━━━━━━━━━━━━━━━━

⏰ وقت المراجعة: 5-30 دقيقة
📱 سنُعلمك فور الموافقة!'''

            # Notify admins with image
            await cls._notify_admins_deposit_review(
                context, user, dep_id, amount, final_amount,
                image_bytes, 'vodafone', analysis
            )
        
        return result
    
    @classmethod
    async def _process_usdt(
        cls,
        user: Dict,
        image_bytes: bytes,
        image_b64: str,
        image_hash: str,
        result: Dict,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Dict:
        """Process USDT payment"""
        
        # Analyze transaction image
        analysis = AIService.analyze_usdt_transaction(image_b64)
        result['details']['ai_analysis'] = analysis
        
        txid = analysis.get('txid')
        
        if not txid:
            result['message'] = '''❌ *لم يتم العثور على TXID*

━━━━━━━━━━━━━━━━━━━━━

💡 تأكد من:
• وضوح الصورة
• ظهور Transaction Hash كاملاً
• أن المعاملة على شبكة BSC (BEP20)'''
            return result
        
        # Check if TXID already used
        if BlockchainVerifier._is_txid_used(txid):
            result['message'] = '🚫 هذا TXID مستخدم من قبل!'
            
            db.execute(
                """INSERT INTO fraud_records
                   (user_id, type, description, evidence, created_at)
                   VALUES(?,?,?,?,?)""",
                (
                    user['id'],
                    'duplicate_txid',
                    'محاولة استخدام TXID مكرر',
                    json.dumps({'txid': txid[:32]}),
                    datetime.now().isoformat()
                )
            )
            return result
        
        # Verify on blockchain
        verification = BlockchainVerifier.verify_transaction(
            txid,
            Config.USDT_WALLET
        )
        
        result['details']['blockchain_verification'] = verification
        
        if not verification['valid']:
            steps_text = '\n'.join(verification.get('verification_steps', []))
            result['message'] = f'''❌ *فشل التحقق من البلوكتشين*

{verification.get('error', 'خطأ غير معروف')}

━━━━━━━━━━━━━━━━━━━━━

📋 *خطوات التحقق:*
{steps_text}

━━━━━━━━━━━━━━━━━━━━━

💡 تأكد من:
• أن المعاملة مؤكدة (Confirmed)
• أن العنوان المستلم: `{Config.USDT_WALLET[:20]}...`
• أن الشبكة هي BSC (BEP20)'''
            return result
        
        # Calculate amounts
        amount_usdt = verification['amount']
        amount_egp = round(amount_usdt * Config.USDT_TO_EGP_RATE, 2)
        
        if amount_egp < Config.MIN_DEPOSIT:
            result['message'] = f'❌ المبلغ أقل من الحد الأدنى ({Config.MIN_DEPOSIT}ج)'
            return result
        
        fee, final_amount = calculate_deposit_fee(amount_egp)
        
        result['amount'] = amount_egp
        result['final_amount'] = final_amount
        result['fee'] = fee
        result['auto_approved'] = True
        result['needs_review'] = False
        
        # Save records
        db.execute(
            """INSERT INTO image_hashes
               (hash, user_id, type, amount, created_at)
               VALUES(?,?,?,?,?)""",
            (image_hash, user['id'], 'usdt', amount_usdt, datetime.now().isoformat())
        )
        
        BlockchainVerifier.mark_txid_used(txid, user['id'], amount_usdt)
        
        now = datetime.now().isoformat()
        
        # Create approved deposit
        dep_id = db.execute(
            """INSERT INTO deposits
               (user_id, amount, amount_after_fee, payment_method,
                image_hash, txid, status, ai_analysis,
                verification_method, auto_approved, created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user['id'], amount_egp, final_amount, 'usdt',
                image_hash, txid, 'approved', json.dumps(analysis),
                'blockchain', 1, now
            )
        )
        
        result['deposit_id'] = dep_id
        
        # Add balance
        new_balance = UserManager.update_balance(
            user['id'],
            final_amount,
            'deposit',
            f'USDT_{txid[:16]}',
            f'إيداع USDT #{dep_id}',
            fee
        )
        
        result['success'] = True
        
        steps_text = '\n'.join(verification.get('verification_steps', []))
        
        result['message'] = f'''✅ *تم إيداع USDT بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

💎 المبلغ: {amount_usdt:.2f} USDT
💵 = {amount_egp:.0f}ج
💸 العمولة: {fee:.1f}ج
💰 الصافي: *{final_amount:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

📋 *التحقق:*
{steps_text}

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك الجديد: *{new_balance:.0f}ج*

🔗 TXID: `{txid[:30]}...`'''

        # Notify admins
        await cls._notify_admins_deposit(
            context, user, dep_id, amount_egp, final_amount,
            'usdt', auto_approved=True,
            extra_info=f"TXID: {txid}\nUSDT: {amount_usdt}"
        )
        
        return result
    
    @classmethod
    async def _notify_admins_deposit(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        dep_id: int,
        amount: float,
        final_amount: float,
        method: str,
        auto_approved: bool = False,
        confidence: float = None,
        extra_info: str = None
    ):
        """Notify admins about deposit"""
        method_emoji = '📱' if method == 'vodafone' else '💎'
        status = '✅ موافقة تلقائية' if auto_approved else '⏳ بانتظار المراجعة'
        
        msg = f"""{method_emoji} *إيداع {"تلقائي" if auto_approved else "جديد"}*
━━━━━━━━━━━━━━━━━━━━━

🆔 #{dep_id}
👤 `{user['id']}` @{user.get('username', 'N/A')}
💵 *{amount:.0f}ج* ➜ {final_amount:.0f}ج
📊 {status}"""

        if confidence:
            msg += f"\n🎯 ثقة AI: {confidence:.0%}"
        
        if extra_info:
            msg += f"\n\n📋 {extra_info}"
        
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    @classmethod
    async def _notify_admins_deposit_review(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        dep_id: int,
        amount: float,
        final_amount: float,
        image_bytes: bytes,
        method: str,
        analysis: Dict
    ):
        """Notify admins with image for review"""
        confidence = analysis.get('confidence', 0)
        
        caption = f"""📱 *إيداع فودافون - مراجعة*
━━━━━━━━━━━━━━━━━━━━━

🆔 #{dep_id}
👤 `{user['id']}` @{user.get('username', 'N/A')}
💵 *{amount:.0f}ج* ➜ {final_amount:.0f}ج
🎯 ثقة AI: {confidence:.0%}

━━━━━━━━━━━━━━━━━━━━━

📊 *المستخدم:*
• الرصيد: {user['balance']:.0f}ج
• الطلبات: {user['total_orders']}
• الإيداعات: {user['total_deposits']:.0f}ج
• درجة الثقة: {user.get('trust_score', 50)}%"""

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"✅ قبول ({amount:.0f}ج)",
                    callback_data=f"approve_dep_{dep_id}"
                ),
                InlineKeyboardButton(
                    "❌ رفض",
                    callback_data=f"reject_dep_{dep_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚠️ تعديل المبلغ",
                    callback_data=f"edit_dep_{dep_id}"
                )
            ]
        ])
        
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_photo(
                    admin_id,
                    photo=io.BytesIO(image_bytes),
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=buttons
                )
            except Exception as e:
                logger.error(f"Failed to send deposit image to admin {admin_id}: {e}")
                # ══════════════════════════════════════════════════════════════════
# USER MANAGER
# ══════════════════════════════════════════════════════════════════

class UserManager:
    """Complete user management system"""
    
    @staticmethod
    def get(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return db.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,),
            fetch_one=True
        )
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """Get user by username"""
        return db.execute(
            "SELECT * FROM users WHERE username=?",
            (username.lower().replace('@', ''),),
            fetch_one=True
        )
    
    @staticmethod
    def create_or_update(
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        referrer_id: int = None
    ) -> Dict:
        """Create new user or update existing"""
        user = UserManager.get(user_id)
        now = datetime.now().isoformat()
        
        if not user:
            # New user
            welcome_bonus = db.get_config('welcome_bonus', Config.WELCOME_BONUS)
            
            db.execute(
                """INSERT INTO users
                   (id, username, first_name, last_name, balance,
                    referrer_id, join_date, last_active, trust_score)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    user_id,
                    username.lower() if username else None,
                    first_name,
                    last_name,
                    welcome_bonus,
                    referrer_id,
                    now,
                    now,
                    50  # Initial trust score
                )
            )
            
            # Record welcome bonus transaction
            if welcome_bonus > 0:
                db.execute(
                    """INSERT INTO transactions
                       (user_id, amount, type, category, reference,
                        description, balance_after, created_at)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        user_id,
                        welcome_bonus,
                        'welcome_bonus',
                        'bonus',
                        'WELCOME',
                        'مكافأة الترحيب',
                        welcome_bonus,
                        now
                    )
                )
            
            # Process referral if exists
            if referrer_id:
                UserManager._process_referral(referrer_id, user_id)
            
            # Log activity
            db.execute(
                """INSERT INTO activity_logs
                   (user_id, action, action_type, details, created_at)
                   VALUES(?,?,?,?,?)""",
                (user_id, 'user_created', 'registration', f'Referrer: {referrer_id}', now)
            )
            
            logger.info(f"New user created: {user_id} (ref: {referrer_id})")
            user = UserManager.get(user_id)
            
        else:
            # Update existing user
            db.execute(
                """UPDATE users SET
                   username = COALESCE(?, username),
                   first_name = COALESCE(?, first_name),
                   last_name = COALESCE(?, last_name),
                   last_active = ?
                   WHERE id = ?""",
                (
                    username.lower() if username else None,
                    first_name,
                    last_name,
                    now,
                    user_id
                )
            )
            user = UserManager.get(user_id)
        
        return user
    
    @staticmethod
    def _process_referral(referrer_id: int, referred_id: int):
        """Process referral bonus"""
        referrer = UserManager.get(referrer_id)
        
        if not referrer:
            return
        
        if referrer['banned']:
            return
        
        # Check if referral already exists
        existing = db.execute(
            "SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?",
            (referrer_id, referred_id),
            fetch_one=True
        )
        
        if existing:
            return
        
        bonus = db.get_config('referral_bonus', Config.REFERRAL_BONUS)
        now = datetime.now().isoformat()
        
        # Add bonus to referrer
        UserManager.update_balance(
            referrer_id,
            bonus,
            'referral_bonus',
            f'REF_{referred_id}',
            f'مكافأة إحالة #{referred_id}'
        )
        
        # Create referral record
        db.execute(
            """INSERT INTO referrals
               (referrer_id, referred_id, bonus_amount, status, created_at)
               VALUES(?,?,?,?,?)""",
            (referrer_id, referred_id, bonus, 'completed', now)
        )
        
        # Update referrer stats
        db.execute(
            """UPDATE users SET
               referral_earnings = referral_earnings + ?,
               referral_count = referral_count + 1
               WHERE id = ?""",
            (bonus, referrer_id)
        )
        
        # Add notification
        UserManager.add_notification(
            referrer_id,
            '🎉 إحالة جديدة!',
            f'حصلت على {bonus:.0f}ج مكافأة إحالة!',
            NotificationType.SUCCESS.value
        )
        
        logger.info(f"Referral processed: {referrer_id} <- {referred_id} (+{bonus})")
    
    @staticmethod
    def update_balance(
        user_id: int,
        amount: float,
        trans_type: str,
        reference: str = '',
        description: str = '',
        fee: float = 0,
        category: str = None
    ) -> float:
        """
        Update user balance with full transaction logging
        Returns: new balance
        """
        user = UserManager.get(user_id)
        if not user:
            return 0
        
        old_balance = user['balance']
        new_balance = max(0, round(old_balance + amount, 2))
        now = datetime.now().isoformat()
        
        # Update balance
        db.execute(
            "UPDATE users SET balance = ?, last_active = ? WHERE id = ?",
            (new_balance, now, user_id)
        )
        
        # Record transaction
        db.execute(
            """INSERT INTO transactions
               (user_id, amount, type, category, reference, description,
                fee, balance_before, balance_after, created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id, amount, trans_type, category or trans_type,
                reference, description, fee, old_balance, new_balance, now
            )
        )
        
        # Update additional stats based on transaction type
        if amount < 0:
            # Purchase
            spent = abs(amount)
            db.execute(
                """UPDATE users SET
                   spent = spent + ?,
                   total_orders = total_orders + 1,
                   last_order = ?
                   WHERE id = ?""",
                (spent, now, user_id)
            )
            UserManager._update_level(user_id)
            UserManager._check_achievements(user_id, 'purchase', spent)
            
        elif trans_type == 'deposit':
            db.execute(
                """UPDATE users SET
                   total_deposits = total_deposits + ?,
                   deposit_count = deposit_count + 1,
                   last_deposit = ?
                   WHERE id = ?""",
                (amount, now, user_id)
            )
            UserManager._update_trust_score(user_id, 2)
            UserManager._check_achievements(user_id, 'deposit', amount)
        
        # Log activity
        db.execute(
            """INSERT INTO activity_logs
               (user_id, action, action_type, details, created_at)
               VALUES(?,?,?,?,?)""",
            (user_id, trans_type, 'balance_change', f'{amount:+.2f} | {reference}', now)
        )
        
        return new_balance
    
    @staticmethod
    def _update_level(user_id: int):
        """Update user level based on spending"""
        user = UserManager.get(user_id)
        if not user:
            return
        
        new_level = db.execute(
            """SELECT * FROM user_levels
               WHERE min_spent <= ?
               ORDER BY level DESC LIMIT 1""",
            (user['spent'],),
            fetch_one=True
        )
        
        if new_level and new_level['level'] != user['level']:
            old_level = user['level']
            
            db.execute(
                "UPDATE users SET level = ? WHERE id = ?",
                (new_level['level'], user_id)
            )
            
            if new_level['level'] > old_level:
                # Level up notification
                UserManager.add_notification(
                    user_id,
                    f"🎉 ترقية للمستوى {new_level['badge']} {new_level['name']}!",
                    f"مبروك! لقد ترقيت مع مزايا إضافية: +{new_level['cashback_bonus']}% كاش باك",
                    NotificationType.LEVEL_UP.value
                )
                
                logger.info(f"User {user_id} leveled up: {old_level} -> {new_level['level']}")
    
    @staticmethod
    def _update_trust_score(user_id: int, change: int):
        """Update user trust score"""
        db.execute(
            """UPDATE users SET
               trust_score = MIN(100, MAX(0, trust_score + ?))
               WHERE id = ?""",
            (change, user_id)
        )
    
    @staticmethod
    def _check_achievements(user_id: int, action: str, value: float):
        """Check and update achievements"""
        # This can be expanded with more achievements
        achievements_config = {
            'first_purchase': {'target': 1, 'reward': 5},
            'big_spender': {'target': 1000, 'reward': 20},
            'loyal_customer': {'target': 10, 'reward': 15},
            'first_deposit': {'target': 1, 'reward': 3},
        }
        
        now = datetime.now().isoformat()
        
        if action == 'purchase':
            # First purchase
            db.execute(
                """INSERT OR IGNORE INTO achievements
                   (user_id, achievement_key, achievement_name, category, target)
                   VALUES(?,?,?,?,?)""",
                (user_id, 'first_purchase', 'أول عملية شراء', 'shopping', 1)
            )
            
            db.execute(
                """UPDATE achievements SET
                   progress = progress + 1,
                   completed = CASE WHEN progress + 1 >= target THEN 1 ELSE 0 END,
                   completed_at = CASE WHEN progress + 1 >= target THEN ? ELSE completed_at END
                   WHERE user_id = ? AND achievement_key = ? AND completed = 0""",
                (now, user_id, 'first_purchase')
            )
    
    @staticmethod
    def get_level_info(user_id: int) -> Dict:
        """Get user level information"""
        user = UserManager.get(user_id)
        if not user:
            return {}
        
        current = db.execute(
            "SELECT * FROM user_levels WHERE level = ?",
            (user['level'],),
            fetch_one=True
        )
        
        next_level = db.execute(
            "SELECT * FROM user_levels WHERE level = ?",
            (user['level'] + 1,),
            fetch_one=True
        )
        
        progress = 0
        if next_level and current:
            range_needed = next_level['min_spent'] - current['min_spent']
            progress_made = user['spent'] - current['min_spent']
            progress = min(100, int((progress_made / range_needed) * 100)) if range_needed > 0 else 0
        
        return {
            'current': current,
            'next': next_level,
            'spent': user['spent'],
            'needed': next_level['min_spent'] - user['spent'] if next_level else 0,
            'progress': progress
        }
    
    @staticmethod
    def add_notification(
        user_id: int,
        title: str,
        message: str = '',
        notif_type: str = 'info',
        action_type: str = None,
        action_data: str = None
    ):
        """Add notification for user"""
        db.execute(
            """INSERT INTO notifications
               (user_id, title, message, type, action_type, action_data, created_at)
               VALUES(?,?,?,?,?,?,?)""",
            (
                user_id, title, message, notif_type,
                action_type, action_data, datetime.now().isoformat()
            )
        )
    
    @staticmethod
    def get_unread_notifications_count(user_id: int) -> int:
        """Get count of unread notifications"""
        result = db.execute(
            "SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,),
            fetch_one=True
        )
        return result['c'] if result else 0
    
    @staticmethod
    def is_banned(user_id: int) -> Tuple[bool, str]:
        """Check if user is banned"""
        user = UserManager.get(user_id)
        
        if not user or not user['banned']:
            return False, ''
        
        # Check temporary ban
        if user.get('ban_until'):
            ban_until = datetime.fromisoformat(user['ban_until'])
            if datetime.now() > ban_until:
                # Ban expired, unban user
                db.execute(
                    """UPDATE users SET
                       banned = 0, ban_until = NULL, ban_reason = NULL
                       WHERE id = ?""",
                    (user_id,)
                )
                return False, ''
        
        return True, user.get('ban_reason', 'غير محدد')
    
    @staticmethod
    def ban_user(
        user_id: int,
        reason: str,
        duration_hours: int = None,
        banned_by: int = None
    ):
        """Ban a user"""
        ban_until = None
        if duration_hours:
            ban_until = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        now = datetime.now().isoformat()
        
        db.execute(
            """UPDATE users SET
               banned = 1, ban_until = ?, ban_reason = ?, banned_by = ?
               WHERE id = ?""",
            (ban_until, reason, banned_by, user_id)
        )
        
        db.execute(
            """INSERT INTO security_logs
               (user_id, event_type, severity, category, details, created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                user_id, 'user_banned', 'high', 'moderation',
                json.dumps({
                    'reason': reason,
                    'duration_hours': duration_hours,
                    'banned_by': banned_by
                }),
                now
            )
        )
        
        logger.warning(f"User {user_id} banned: {reason}")
    
    @staticmethod
    def unban_user(user_id: int, unbanned_by: int = None):
        """Unban a user"""
        db.execute(
            """UPDATE users SET
               banned = 0, ban_until = NULL, ban_reason = NULL, banned_by = NULL
               WHERE id = ?""",
            (user_id,)
        )
        
        db.execute(
            """INSERT INTO security_logs
               (user_id, event_type, severity, category, details, created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                user_id, 'user_unbanned', 'info', 'moderation',
                json.dumps({'unbanned_by': unbanned_by}),
                datetime.now().isoformat()
            )
        )
        
        logger.info(f"User {user_id} unbanned by {unbanned_by}")
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        user = UserManager.get(user_id)
        if not user:
            return {}
        
        # Get order stats
        order_stats = db.execute(
            """SELECT
               COUNT(*) as total,
               SUM(CASE WHEN status IN ('done', 'completed') THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
               SUM(total_price) as total_spent
               FROM orders WHERE user_id = ?""",
            (user_id,),
            fetch_one=True
        )
        
        # Get deposit stats
        deposit_stats = db.execute(
            """SELECT
               COUNT(*) as total,
               SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END) as approved_amount,
               SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
               FROM deposits WHERE user_id = ?""",
            (user_id,),
            fetch_one=True
        )
        
        # Get referral stats
        referral_stats = db.execute(
            """SELECT
               COUNT(*) as total,
               SUM(bonus_amount) as total_bonus
               FROM referrals WHERE referrer_id = ?""",
            (user_id,),
            fetch_one=True
        )
        
        # Daily reward info
        daily_info = db.execute(
            "SELECT * FROM daily_rewards WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        return {
            'user': user,
            'orders': order_stats,
            'deposits': deposit_stats,
            'referrals': referral_stats,
            'daily': daily_info,
            'level_info': UserManager.get_level_info(user_id)
        }


# ══════════════════════════════════════════════════════════════════
# PRODUCT MANAGER
# ══════════════════════════════════════════════════════════════════

class ProductManager:
    """Product management system"""
    
    @staticmethod
    def get(item_key: str) -> Optional[Dict]:
        """Get product by key"""
        return db.execute(
            "SELECT * FROM products WHERE item_key = ? AND is_active = 1",
            (item_key,),
            fetch_one=True
        )
    
    @staticmethod
    def get_all_active() -> List[Dict]:
        """Get all active products"""
        return db.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order, price",
            fetch_all=True
        )
    
    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """Get products by category"""
        return db.execute(
            """SELECT * FROM products
               WHERE category = ? AND is_active = 1
               ORDER BY sort_order, price""",
            (category,),
            fetch_all=True
        )
    
    @staticmethod
    def get_categories() -> List[Dict]:
        """Get all categories with product counts"""
        return db.execute(
            """SELECT category, COUNT(*) as count
               FROM products WHERE is_active = 1
               GROUP BY category
               ORDER BY count DESC""",
            fetch_all=True
        )
    
    @staticmethod
    def get_featured() -> List[Dict]:
        """Get featured products"""
        return db.execute(
            """SELECT * FROM products
               WHERE is_active = 1 AND is_featured = 1
               ORDER BY sort_order LIMIT 10""",
            fetch_all=True
        )
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        """Search products"""
        search_term = f"%{query}%"
        return db.execute(
            """SELECT * FROM products
               WHERE is_active = 1 AND (
                   name LIKE ? OR
                   name_en LIKE ? OR
                   description LIKE ? OR
                   category LIKE ?
               )
               ORDER BY sold_count DESC LIMIT 20""",
            (search_term, search_term, search_term, search_term),
            fetch_all=True
        )
    
    @staticmethod
    def increment_view(item_key: str):
        """Increment product view count"""
        db.execute(
            "UPDATE products SET view_count = view_count + 1 WHERE item_key = ?",
            (item_key,)
        )
    
    @staticmethod
    def increment_sold(item_key: str, quantity: int = 1):
        """Increment sold count and decrease stock"""
        db.execute(
            """UPDATE products SET
               sold_count = sold_count + ?,
               stock = CASE WHEN stock > 0 THEN stock - ? ELSE stock END
               WHERE item_key = ?""",
            (quantity, quantity, item_key)
        )
    
    @staticmethod
    def check_stock(item_key: str, quantity: int = 1) -> Tuple[bool, str]:
        """Check if product is in stock"""
        product = ProductManager.get(item_key)
        
        if not product:
            return False, "المنتج غير موجود"
        
        if not product['is_active']:
            return False, "المنتج غير متاح حالياً"
        
        if product['stock'] == 0:
            return False, "نفد المخزون"
        
        if product['stock'] > 0 and product['stock'] < quantity:
            return False, f"الكمية المتاحة: {product['stock']} فقط"
        
        return True, "متاح"


# ══════════════════════════════════════════════════════════════════
# ORDER MANAGER
# ══════════════════════════════════════════════════════════════════

class OrderManager:
    """Order management system"""
    
    @staticmethod
    def create(
        user_id: int,
        product: Dict,
        input_data: Dict,
        quantity: int = 1,
        coupon_code: str = None,
        discount_amount: float = 0
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create new order
        Returns: (success, message, order_id)
        """
        user = UserManager.get(user_id)
        if not user:
            return False, "المستخدم غير موجود", None
        
        # Check stock
        in_stock, stock_msg = ProductManager.check_stock(product['item_key'], quantity)
        if not in_stock:
            return False, stock_msg, None
        
        # Calculate prices
        unit_price = product['price']
        total_price = unit_price * quantity - discount_amount
        
        if user['balance'] < total_price:
            needed = total_price - user['balance']
            return False, f"رصيدك غير كافٍ! تحتاج {needed:.0f}ج إضافية", None
        
        # Calculate cashback
        level_info = UserManager.get_level_info(user_id)
        level_bonus = level_info.get('current', {}).get('cashback_bonus', 0) if level_info.get('current') else 0
        cashback_percent = product.get('cashback_percent', 3) + level_bonus
        cashback = round(total_price * cashback_percent / 100, 2)
        
        now = datetime.now().isoformat()
        order_id = generate_order_id()
        
        try:
            # Deduct balance
            new_balance = UserManager.update_balance(
                user_id,
                -total_price,
                'purchase',
                order_id,
                f"شراء {product['name']}",
                category='order'
            )
            
            # Add cashback
            if cashback > 0:
                UserManager.update_balance(
                    user_id,
                    cashback,
                    'cashback',
                    order_id,
                    f"كاش باك {product['name']}",
                    category='bonus'
                )
                
                db.execute(
                    "UPDATE users SET cashback_total = cashback_total + ? WHERE id = ?",
                    (cashback, user_id)
                )
            
            # Create order
            db.execute(
                """INSERT INTO orders
                   (order_id, user_id, product_key, product_name, category,
                    quantity, unit_price, total_price, original_price,
                    discount_amount, discount_code, cashback_amount,
                    cashback_percent, input_data, status, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    order_id, user_id, product['item_key'], product['name'],
                    product['category'], quantity, unit_price, total_price,
                    product.get('original_price'), discount_amount, coupon_code,
                    cashback, cashback_percent,
                    json.dumps(input_data, ensure_ascii=False),
                    'pending', now
                )
            )
            
            # Update product stats
            ProductManager.increment_sold(product['item_key'], quantity)
            
            # Update coupon usage if used
            if coupon_code:
                db.execute(
                    """INSERT INTO coupon_usage
                       (coupon_code, user_id, order_id, discount_amount, used_at)
                       VALUES(?,?,?,?,?)""",
                    (coupon_code, user_id, order_id, discount_amount, now)
                )
                db.execute(
                    "UPDATE coupons SET usage_count = usage_count + 1 WHERE code = ?",
                    (coupon_code,)
                )
            
            logger.info(f"Order {order_id} created by user {user_id}: {product['name']}")
            
            return True, order_id, order_id
            
        except Exception as e:
            logger.error(f"Order creation error: {e}")
            return False, "حدث خطأ أثناء إنشاء الطلب", None
    
    @staticmethod
    def get(order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return db.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
            fetch_one=True
        )
    
    @staticmethod
    def get_user_orders(user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's orders"""
        return db.execute(
            """SELECT * FROM orders
               WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
            fetch_all=True
        )
    
    @staticmethod
    def get_pending_orders() -> List[Dict]:
        """Get all pending orders"""
        return db.execute(
            """SELECT o.*, u.username, u.first_name
               FROM orders o
               LEFT JOIN users u ON o.user_id = u.id
               WHERE o.status = 'pending'
               ORDER BY o.id DESC""",
            fetch_all=True
        )
    
    @staticmethod
    def complete_order(
        order_id: str,
        delivery_data: str,
        admin_id: int = None
    ) -> Tuple[bool, str]:
        """Complete an order"""
        order = OrderManager.get(order_id)
        
        if not order:
            return False, "الطلب غير موجود"
        
        if order['status'] != 'pending':
            return False, f"الطلب بحالة {order['status']}"
        
        now = datetime.now().isoformat()
        
        db.execute(
            """UPDATE orders SET
               status = 'completed',
               delivery_data = ?,
               processed_by = ?,
               completed_at = ?,
               updated_at = ?
               WHERE order_id = ?""",
            (delivery_data, admin_id, now, now, order_id)
        )
        
        # Update user stats
        db.execute(
            "UPDATE users SET successful_orders = successful_orders + 1 WHERE id = ?",
            (order['user_id'],)
        )
        
        # Add notification
        UserManager.add_notification(
            order['user_id'],
            f"✅ تم تنفيذ طلبك #{order_id}",
            "تفقد تفاصيل الطلب للحصول على بيانات التسليم",
            NotificationType.ORDER.value
        )
        
        logger.info(f"Order {order_id} completed by admin {admin_id}")
        
        return True, "تم تنفيذ الطلب بنجاح"
    
    @staticmethod
    def cancel_order(
        order_id: str,
        reason: str,
        refund: bool = True,
        admin_id: int = None
    ) -> Tuple[bool, str]:
        """Cancel an order"""
        order = OrderManager.get(order_id)
        
        if not order:
            return False, "الطلب غير موجود"
        
        if order['status'] not in ['pending', 'processing']:
            return False, f"لا يمكن إلغاء طلب بحالة {order['status']}"
        
        now = datetime.now().isoformat()
        
        # Refund if requested
        refund_amount = 0
        if refund:
            refund_amount = order['total_price']
            UserManager.update_balance(
                order['user_id'],
                refund_amount,
                'refund',
                order_id,
                f"استرداد طلب ملغي #{order_id}"
            )
        
        db.execute(
            """UPDATE orders SET
               status = 'cancelled',
               cancel_reason = ?,
               refund_amount = ?,
               cancelled_at = ?,
               processed_by = ?,
               updated_at = ?
               WHERE order_id = ?""",
            (reason, refund_amount, now, admin_id, now, order_id)
        )
        
        # Add notification
        UserManager.add_notification(
            order['user_id'],
            f"❌ تم إلغاء طلبك #{order_id}",
            f"السبب: {reason}" + (f"\nتم إرجاع {refund_amount:.0f}ج لرصيدك" if refund else ""),
            NotificationType.ORDER.value
        )
        
        logger.info(f"Order {order_id} cancelled: {reason}")
        
        return True, "تم إلغاء الطلب"


# ══════════════════════════════════════════════════════════════════
# KEYBOARD BUILDER
# ══════════════════════════════════════════════════════════════════

class Keyboards:
    """Telegram keyboard builder"""
    
    # Category icons mapping
    CATEGORY_ICONS = {
        'freefire': '🔥',
        'pubg': '🔫',
        'mlbb': '⚔️',
        'steam': '🎮',
        'googleplay': '📱',
        'itunes': '🍎',
        'playstation': '🎮',
        'xbox': '🎮',
    }
    
    CATEGORY_NAMES = {
        'freefire': 'فري فاير',
        'pubg': 'ببجي موبايل',
        'mlbb': 'موبايل ليجندز',
        'steam': 'ستيم',
        'googleplay': 'جوجل بلاي',
        'itunes': 'آيتونز',
        'playstation': 'بلايستيشن',
        'xbox': 'إكس بوكس',
    }
    
    @classmethod
    def main_menu(cls, user_id: int) -> InlineKeyboardMarkup:
        """Build main menu keyboard"""
        user = UserManager.get(user_id)
        balance = user['balance'] if user else 0
        
        level_info = UserManager.get_level_info(user_id)
        badge = '🥉'
        if level_info.get('current'):
            badge = level_info['current'].get('badge', '🥉')
        
        # Get unread notifications
        unread = UserManager.get_unread_notifications_count(user_id)
        notif_text = f"🔔 ({unread})" if unread > 0 else "🔔"
        
        buttons = [
            # Balance row
            [InlineKeyboardButton(
                f"💰 رصيدك: {balance:.0f}ج {badge}",
                callback_data='wallet'
            )],
            
            # Shop and deposit
            [
                InlineKeyboardButton('🛍️ المتجر', callback_data='shop'),
                InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')
            ],
            
            # Orders and rewards
            [
                InlineKeyboardButton('📦 طلباتي', callback_data='my_orders'),
                InlineKeyboardButton('🎁 المكافآت', callback_data='rewards')
            ],
            
            # Coupon and referral
            [
                InlineKeyboardButton('🎟️ كوبون', callback_data='coupon'),
                InlineKeyboardButton('👥 دعوة صديق', callback_data='referral')
            ],
            
            # Notifications and support
            [
                InlineKeyboardButton(notif_text, callback_data='notifications'),
                InlineKeyboardButton('🆘 الدعم', callback_data='support')
            ],
        ]
        
        # Admin panel for admins
        if user_id in Config.ADMIN_IDS:
            buttons.append([
                InlineKeyboardButton('⚙️ لوحة التحكم', callback_data='admin_panel')
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def admin_panel(cls) -> InlineKeyboardMarkup:
        """Build admin panel keyboard"""
        # Get counts
        pending_orders = db.execute(
            "SELECT COUNT(*) as c FROM orders WHERE status='pending'",
            fetch_one=True
        )['c']
        
        pending_deposits = db.execute(
            "SELECT COUNT(*) as c FROM deposits WHERE status='pending'",
            fetch_one=True
        )['c']
        
        open_tickets = db.execute(
            "SELECT COUNT(*) as c FROM tickets WHERE status='open'",
            fetch_one=True
        )['c']
        
        buttons = [
            # Orders and deposits
            [
                InlineKeyboardButton(
                    f"📦 الطلبات ({pending_orders})",
                    callback_data='admin_orders'
                ),
                InlineKeyboardButton(
                    f"💰 الإيداعات ({pending_deposits})",
                    callback_data='admin_deposits'
                )
            ],
            
            # Tickets and users
            [
                InlineKeyboardButton(
                    f"🎫 التذاكر ({open_tickets})",
                    callback_data='admin_tickets'
                ),
                InlineKeyboardButton(
                    '👥 المستخدمين',
                    callback_data='admin_users'
                )
            ],
            
            # Stats and profits
            [
                InlineKeyboardButton('📊 الإحصائيات', callback_data='admin_stats'),
                InlineKeyboardButton('💹 الأرباح', callback_data='admin_profits')
            ],
            
            # Coupons and gift cards
            [
                InlineKeyboardButton('🎟️ كوبون جديد', callback_data='admin_new_coupon'),
                InlineKeyboardButton('🎁 بطاقة هدية', callback_data='admin_giftcard')
            ],
            
            # Promotions
            [
                InlineKeyboardButton('📢 إعلان AI', callback_data='admin_promo'),
                InlineKeyboardButton('📨 إذاعة', callback_data='admin_broadcast')
            ],
            
            # YouTube and flash sale
            [
                InlineKeyboardButton('🎬 إعلان يوتيوب', callback_data='admin_youtube_ad'),
                InlineKeyboardButton('⚡ عرض خاطف', callback_data='admin_flash_sale')
            ],
            
            # Products and settings
            [
                InlineKeyboardButton('📝 المنتجات', callback_data='admin_products'),
                InlineKeyboardButton('🔧 الإعدادات', callback_data='admin_settings')
            ],
            
            # Back to home
            [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def shop_categories(cls) -> InlineKeyboardMarkup:
        """Build shop categories keyboard"""
        categories = ProductManager.get_categories()
        
        buttons = []
        for cat in categories:
            cat_key = cat['category']
            icon = cls.CATEGORY_ICONS.get(cat_key, '📦')
            name = cls.CATEGORY_NAMES.get(cat_key, cat_key.upper())
            count = cat['count']
            
            buttons.append([
                InlineKeyboardButton(
                    f"{icon} {name} ({count})",
                    callback_data=f"category_{cat_key}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton('🔍 بحث', callback_data='search_products'),
            InlineKeyboardButton('⭐ المميز', callback_data='featured_products')
        ])
        
        buttons.append([
            InlineKeyboardButton('🏠 الرئيسية', callback_data='home')
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def category_products(cls, category: str) -> InlineKeyboardMarkup:
        """Build category products keyboard"""
        products = ProductManager.get_by_category(category)
        
        buttons = []
        for p in products:
            # Build product button text
            price_text = f"{p['price']:.0f}ج"
            
            # Discount indicator
            discount_text = ''
            if p['original_price'] and p['original_price'] > p['price']:
                discount = int((1 - p['price'] / p['original_price']) * 100)
                discount_text = f" 🏷️-{discount}%"
            
            # Cashback indicator
            cashback_text = ''
            if p.get('cashback_percent', 0) > 0:
                cashback_text = f" 💎{p['cashback_percent']:.0f}%"
            
            # Stock indicator
            stock_text = ''
            if p['stock'] == 0:
                stock_text = ' ❌'
            elif 0 < p['stock'] <= 5:
                stock_text = f" ⚠️{p['stock']}"
            
            button_text = f"{p['name']} - {price_text}{discount_text}{cashback_text}{stock_text}"
            
            buttons.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"product_{p['item_key']}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton('◀️ رجوع للمتجر', callback_data='shop')
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def product_details(cls, product: Dict, user: Dict) -> InlineKeyboardMarkup:
        """Build product details keyboard"""
        can_buy = user['balance'] >= product['price'] and product['stock'] != 0
        
        buttons = []
        
        if can_buy:
            buttons.append([
                InlineKeyboardButton(
                    '🛒 شراء الآن',
                    callback_data=f"buy_{product['item_key']}"
                )
            ])
        elif product['stock'] == 0:
            buttons.append([
                InlineKeyboardButton(
                    '❌ نفد المخزون',
                    callback_data='_'
                )
            ])
        else:
            needed = product['price'] - user['balance']
            buttons.append([
                InlineKeyboardButton(
                    f"💳 تحتاج {needed:.0f}ج - اشحن الآن",
                    callback_data='deposit'
                )
            ])
        
        buttons.append([
            InlineKeyboardButton(
                '◀️ رجوع',
                callback_data=f"category_{product['category']}"
            )
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def deposit_methods(cls) -> InlineKeyboardMarkup:
        """Build deposit methods keyboard"""
        buttons = [
            [
                InlineKeyboardButton(
                    '📱 فودافون كاش',
                    callback_data='deposit_vodafone'
                )
            ],
            [
                InlineKeyboardButton(
                    '💎 USDT (BEP20)',
                    callback_data='deposit_usdt'
                )
            ],
            [
                InlineKeyboardButton('🏠 الرئيسية', callback_data='home')
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def order_list(cls, orders: List[Dict]) -> InlineKeyboardMarkup:
        """Build order list keyboard"""
        status_icons = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'done': '✅',
            'cancelled': '❌',
            'refunded': '💰'
        }
        
        buttons = []
        for order in orders[:10]:
            icon = status_icons.get(order['status'], '❓')
            date = order['created_at'][:10] if order['created_at'] else ''
            
            buttons.append([
                InlineKeyboardButton(
                    f"{icon} {order['order_id']} | {order['total_price']:.0f}ج",
                    callback_data=f"order_{order['order_id']}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton('🏠 الرئيسية', callback_data='home')
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def support_menu(cls, has_open_ticket: bool = False) -> InlineKeyboardMarkup:
        """Build support menu keyboard"""
        buttons = []
        
        if has_open_ticket:
            buttons.append([
                InlineKeyboardButton(
                    '💬 تذكرتي المفتوحة',
                    callback_data='my_open_ticket'
                )
            ])
        
        buttons.extend([
            [
                InlineKeyboardButton(
                    '📝 تذكرة جديدة',
                    callback_data='new_ticket'
                )
            ],
            [
                InlineKeyboardButton(
                    '📋 تذاكري السابقة',
                    callback_data='my_tickets'
                )
            ],
            [
                InlineKeyboardButton(
                    '❓ الأسئلة الشائعة',
                    callback_data='faq'
                )
            ],
            [
                InlineKeyboardButton('🏠 الرئيسية', callback_data='home')
            ]
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @classmethod
    def back_button(cls, callback_data: str = 'home') -> InlineKeyboardMarkup:
        """Build simple back button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('◀️ رجوع', callback_data=callback_data)]
        ])
    
    @classmethod
    def confirm_cancel(
        cls,
        confirm_callback: str,
        cancel_callback: str = 'home'
    ) -> InlineKeyboardMarkup:
        """Build confirm/cancel buttons"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('✅ تأكيد', callback_data=confirm_callback),
                InlineKeyboardButton('❌ إلغاء', callback_data=cancel_callback)
            ]
        ])
    
    @classmethod
    def pagination(
        cls,
        current_page: int,
        total_pages: int,
        callback_prefix: str
    ) -> List[InlineKeyboardButton]:
        """Build pagination buttons"""
        buttons = []
        
        if current_page > 1:
            buttons.append(
                InlineKeyboardButton(
                    '◀️',
                    callback_data=f"{callback_prefix}_page_{current_page - 1}"
                )
            )
        
        buttons.append(
            InlineKeyboardButton(
                f"{current_page}/{total_pages}",
                callback_data='_'
            )
        )
        
        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    '▶️',
                    callback_data=f"{callback_prefix}_page_{current_page + 1}"
                )
            )
        
        return buttons
    
    @classmethod
    def admin_order_actions(cls, order_id: str) -> InlineKeyboardMarkup:
        """Build admin order action buttons"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    '✅ تنفيذ',
                    callback_data=f"execute_{order_id}"
                ),
                InlineKeyboardButton(
                    '❌ إلغاء',
                    callback_data=f"cancel_order_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    '👤 المستخدم',
                    callback_data=f"order_user_{order_id}"
                )
            ]
        ])
    
    @classmethod
    def admin_deposit_actions(cls, deposit_id: int) -> InlineKeyboardMarkup:
        """Build admin deposit action buttons"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    '✅ قبول',
                    callback_data=f"approve_dep_{deposit_id}"
                ),
                InlineKeyboardButton(
                    '❌ رفض',
                    callback_data=f"reject_dep_{deposit_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    '⚠️ تعديل المبلغ',
                    callback_data=f"edit_dep_{deposit_id}"
                )
            ]
        ])
    
    @classmethod
    def admin_user_actions(cls, user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
        """Build admin user action buttons"""
        ban_text = '🔓 فك الحظر' if is_banned else '🔒 حظر'
        ban_callback = f"unban_{user_id}" if is_banned else f"ban_{user_id}"
        
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    '➕ إضافة رصيد',
                    callback_data=f"addbal_{user_id}"
                ),
                InlineKeyboardButton(
                    '➖ خصم رصيد',
                    callback_data=f"subbal_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(ban_text, callback_data=ban_callback)
            ],
            [
                InlineKeyboardButton(
                    '📦 طلباته',
                    callback_data=f"user_orders_{user_id}"
                ),
                InlineKeyboardButton(
                    '💳 إيداعاته',
                    callback_data=f"user_deposits_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    '📨 إرسال رسالة',
                    callback_data=f"msg_user_{user_id}"
                )
            ],
            [
                InlineKeyboardButton('◀️ رجوع', callback_data='admin_users')
            ]
        ])
        # ══════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════

@log_action("start_command")
@maintenance_check
@rate_limited
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Initialize bot username if not set
    if not state.bot_username:
        state.bot_username = context.bot.username
        state.bot_id = context.bot.id
    
    # Check ban status
    is_banned, ban_reason = UserManager.is_banned(user.id)
    if is_banned:
        await update.message.reply_text(
            f"🚫 *أنت محظور من استخدام البوت*\n\n"
            f"السبب: {ban_reason}\n\n"
            f"للاستفسار تواصل مع الدعم.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Process referral
    referrer_id = None
    if context.args:
        arg = context.args[0]
        if arg.startswith('r') or arg.startswith('ref'):
            try:
                ref_str = arg.replace('ref', '').replace('r', '')
                referrer_id = int(ref_str)
                if referrer_id == user.id:
                    referrer_id = None
            except ValueError:
                pass
    
    # Check if new user
    existing_user = UserManager.get(user.id)
    is_new_user = existing_user is None
    
    # Create or update user
    db_user = UserManager.create_or_update(
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        referrer_id if is_new_user else None
    )
    
    # Get level info
    level_info = UserManager.get_level_info(user.id)
    level = level_info.get('current', {}) if level_info.get('current') else {}
    badge = level.get('badge', '🥉')
    level_name = level.get('name', 'برونزي')
    
    # Random tips
    tips = [
        "💡 نصيحة: اجمع مكافأتك اليومية كل يوم لزيادة رصيدك!",
        "🔥 تذكير: كلما اشتريت أكثر، ترقيت لمستوى أعلى مع مزايا أفضل!",
        "⚡ التسليم فوري ومضمون 100% على جميع المنتجات!",
        "🎁 ادعُ أصدقاءك واكسب مكافآت عن كل صديق!",
        "🎟️ تابع الإعلانات للحصول على كوبونات خصم حصرية!",
        "💎 استخدم USDT للإيداع واستمتع بموافقة فورية!",
        "📦 تابع طلباتك من قائمة 'طلباتي'!",
        "🏆 وصل للمستوى الإمبراطوري واحصل على خصم 15%!"
    ]
    
    # Build welcome message
    balance = db_user['balance']
    total_orders = db_user['total_orders']
    points = db_user['points']
    tip = random.choice(tips)
    
    welcome_text = f"""🔥 *مرحباً بك في XLERO SHOP!* 🔥

👋 أهلاً *{user.first_name}*

━━━━━━━━━━━━━━━━━━━━━

💰 *رصيدك:* {balance:.2f} ج.م
{badge} *المستوى:* {level_name}
📦 *طلباتك:* {total_orders}
⭐ *نقاطك:* {points}

━━━━━━━━━━━━━━━━━━━━━

{tip}

━━━━━━━━━━━━━━━━━━━━━

⚡ *مميزاتنا:*
• شحن فوري خلال دقائق
• أسعار أقل من السوق
• دعم فني على مدار الساعة
• ضمان كامل على جميع المنتجات
• كاش باك على كل عملية شراء
• نظام مستويات ومكافآت"""

    if is_new_user:
        welcome_bonus = db_user['balance']
        welcome_text += f"\n\n🎁 *هدية ترحيبية:* +{welcome_bonus:.0f}ج تمت إضافتها!"
        if referrer_id:
            welcome_text += "\n👥 تم تسجيلك عبر إحالة!"
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user.id)
    )
    
    logger.info(f"User {user.id} started bot (new: {is_new_user})")


@admin_only
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    # Get stats
    total_users = db.execute("SELECT COUNT(*) as c FROM users", fetch_one=True)['c']
    pending_orders = db.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'", fetch_one=True)['c']
    pending_deposits = db.execute("SELECT COUNT(*) as c FROM deposits WHERE status='pending'", fetch_one=True)['c']
    open_tickets = db.execute("SELECT COUNT(*) as c FROM tickets WHERE status='open'", fetch_one=True)['c']
    
    admin_text = f"""⚙️ *لوحة تحكم المدير*

👥 إجمالي المستخدمين: {total_users}
📦 طلبات معلقة: {pending_orders}
💰 إيداعات معلقة: {pending_deposits}
🎫 تذاكر مفتوحة: {open_tickets}"""
    
    await update.message.reply_text(
        admin_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.admin_panel()
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """🆘 *المساعدة*
━━━━━━━━━━━━━━━━━━━━━

📌 *الأوامر المتاحة:*
• /start - بدء البوت
• /help - المساعدة

━━━━━━━━━━━━━━━━━━━━━

🛒 *كيفية الشراء:*
1️⃣ اشحن رصيدك من قائمة "شحن رصيد"
2️⃣ اختر المنتج من "المتجر"
3️⃣ أدخل بياناتك المطلوبة
4️⃣ أكد الطلب وانتظر التنفيذ

━━━━━━━━━━━━━━━━━━━━━

💳 *طرق الدفع:*
• 📱 فودافون كاش
• 💎 USDT (BEP20)

━━━━━━━━━━━━━━━━━━━━━

🎁 *المكافآت:*
• مكافأة يومية متزايدة
• كاش باك على كل شراء
• مكافأة إحالة الأصدقاء
• نظام مستويات ومزايا

━━━━━━━━━━━━━━━━━━━━━

📞 *للمساعدة:*
افتح تذكرة دعم من القائمة الرئيسية"""

    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(update.effective_user.id)
    )


# ══════════════════════════════════════════════════════════════════
# CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════════════════════════

@log_action("callback")
@maintenance_check
@rate_limited
@error_handler_decorator
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query handler"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    # Answer callback
    try:
        await query.answer()
    except Exception:
        pass
    
    # Check ban
    is_banned, ban_reason = UserManager.is_banned(user_id)
    if is_banned and user_id not in Config.ADMIN_IDS:
        try:
            await query.edit_message_text(
                f"🚫 أنت محظور\nالسبب: {ban_reason}"
            )
        except:
            pass
        return
    
    # Get or create user
    user = UserManager.create_or_update(
        user_id,
        query.from_user.username,
        query.from_user.first_name
    )
    
    # Route callbacks
    try:
        # Main navigation
        if data == 'home':
            await handle_home(query, user)
        elif data == 'wallet':
            await handle_wallet(query, user)
        
        # Shop
        elif data == 'shop':
            await handle_shop(query, user)
        elif data.startswith('category_'):
            await handle_category(query, user, data)
        elif data.startswith('product_'):
            await handle_product(query, user, data)
        elif data.startswith('buy_'):
            await handle_buy(query, context, user, data)
        elif data == 'cancel_purchase':
            await handle_cancel_purchase(query, user)
        
        # Deposit
        elif data == 'deposit':
            await handle_deposit(query, context, user)
        elif data == 'deposit_vodafone':
            await handle_deposit_vodafone(query, context, user)
        elif data == 'deposit_usdt':
            await handle_deposit_usdt(query, context, user)
        
        # Orders
        elif data == 'my_orders':
            await handle_my_orders(query, user)
        elif data.startswith('order_'):
            await handle_order_details(query, user, data)
        
        # Rewards
        elif data == 'rewards':
            await handle_rewards(query, user)
        elif data == 'claim_daily':
            await handle_claim_daily(query, user)
        
        # Coupon
        elif data == 'coupon':
            await handle_coupon_input(query, context, user)
        
        # Referral
        elif data == 'referral':
            await handle_referral(query, user)
        
        # Notifications
        elif data == 'notifications':
            await handle_notifications(query, user)
        
        # Support
        elif data == 'support':
            await handle_support(query, user)
        elif data == 'new_ticket':
            await handle_new_ticket(query, context, user)
        elif data == 'my_tickets':
            await handle_my_tickets(query, user)
        elif data.startswith('ticket_') and not data.startswith('ticket_reply_'):
            await handle_ticket_view(query, context, user, data)
        elif data.startswith('reply_ticket_'):
            await handle_ticket_reply(query, context, user, data)
        elif data == 'faq':
            await handle_faq(query, user)
        
        # Admin callbacks
        elif data == 'admin_panel' and user_id in Config.ADMIN_IDS:
            await handle_admin_panel(query)
        elif data.startswith('admin_') and user_id in Config.ADMIN_IDS:
            await handle_admin_callbacks(query, context, user_id, data)
        elif data.startswith('approve_') and user_id in Config.ADMIN_IDS:
            await handle_admin_approve(query, context, data)
        elif data.startswith('reject_') and user_id in Config.ADMIN_IDS:
            await handle_admin_reject(query, context, data)
        elif data.startswith('execute_') and user_id in Config.ADMIN_IDS:
            await handle_admin_execute(query, context, data)
        elif data.startswith('cancel_order_') and user_id in Config.ADMIN_IDS:
            await handle_admin_cancel_order(query, context, data)
        elif data.startswith('user_') and user_id in Config.ADMIN_IDS:
            await handle_admin_user(query, context, data)
        elif data.startswith('ban_') and user_id in Config.ADMIN_IDS:
            await handle_admin_ban(query, context, data)
        elif data.startswith('unban_') and user_id in Config.ADMIN_IDS:
            await handle_admin_unban(query, context, data)
        elif data.startswith('addbal_') and user_id in Config.ADMIN_IDS:
            await handle_admin_add_balance(query, context, data)
        elif data.startswith('subbal_') and user_id in Config.ADMIN_IDS:
            await handle_admin_sub_balance(query, context, data)
        
    except Exception as e:
        logger.error(f"Callback error for {data}: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "❌ حدث خطأ، حاول مرة أخرى",
                reply_markup=Keyboards.main_menu(user_id)
            )
        except:
            pass


# ══════════════════════════════════════════════════════════════════
# NAVIGATION HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_home(query, user: Dict):
    """Handle home navigation"""
    level_info = UserManager.get_level_info(user['id'])
    current_level = level_info.get('current', {}) if level_info.get('current') else {}
    badge = current_level.get('badge', '🥉')
    level_name = current_level.get('name', 'برونزي')
    
    balance = user['balance']
    total_orders = user['total_orders']
    points = user['points']
    
    text = f"""🏠 *القائمة الرئيسية*

💰 رصيدك: *{balance:.2f}* ج.م
{badge} المستوى: {level_name}
📦 طلباتك: {total_orders}
⭐ نقاطك: {points}"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def handle_wallet(query, user: Dict):
    """Handle wallet view"""
    # Get recent transactions
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user['id'],),
        fetch_all=True
    )
    
    level_info = UserManager.get_level_info(user['id'])
    level = level_info.get('current', {}) if level_info.get('current') else {}
    next_level = level_info.get('next')
    
    balance = user['balance']
    spent = user['spent']
    total_deposits = user['total_deposits']
    cashback_total = user.get('cashback_total', 0)
    
    level_badge = level.get('badge', '🥉')
    level_name = level.get('name', 'برونزي')
    cashback_bonus = level.get('cashback_bonus', 0)
    daily_bonus = level.get('daily_bonus', 0)
    
    text = f"""💰 *محفظتي*
━━━━━━━━━━━━━━━━━━━━━

💵 الرصيد الحالي: *{balance:.2f}* ج.م
💸 إجمالي الإنفاق: {spent:.0f} ج.م
💳 إجمالي الإيداعات: {total_deposits:.0f} ج.م
🎁 كاش باك مكتسب: {cashback_total:.0f} ج.م

━━━━━━━━━━━━━━━━━━━━━

{level_badge} *المستوى:* {level_name}
💎 كاش باك إضافي: +{cashback_bonus}%
🎁 مكافأة يومية: +{daily_bonus}ج"""

    if next_level:
        needed = next_level['min_spent'] - user['spent']
        progress = level_info.get('progress', 0)
        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        next_badge = next_level['badge']
        next_name = next_level['name']
        
        text += f"""

━━━━━━━━━━━━━━━━━━━━━

📈 *التقدم للمستوى التالي:*
{next_badge} {next_name}
[{progress_bar}] {progress}%
أنفق {needed:.0f}ج إضافية"""

    text += "\n\n━━━━━━━━━━━━━━━━━━━━━\n\n📜 *آخر العمليات:*\n"
    
    if transactions:
        for t in transactions[:7]:
            amount = t['amount']
            trans_type = t['type']
            sign = '+' if amount > 0 else ''
            emoji = '📥' if amount > 0 else '📤'
            text += f"{emoji} {sign}{amount:.0f}ج - {trans_type}\n"
    else:
        text += "لا توجد عمليات بعد"
    
    buttons = [
        [InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')],
        [InlineKeyboardButton('📊 تفاصيل أكثر', callback_data='wallet_details')],
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# SHOP HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_shop(query, user: Dict):
    """Handle shop view"""
    balance = user['balance']
    
    text = f"""🛍️ *المتجر*
━━━━━━━━━━━━━━━━━━━━━

💰 رصيدك: *{balance:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

📦 اختر القسم المطلوب:"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.shop_categories()
    )


async def handle_category(query, user: Dict, data: str):
    """Handle category view"""
    category = data.replace('category_', '')
    products = ProductManager.get_by_category(category)
    
    if not products:
        await query.answer("لا توجد منتجات متاحة حالياً", show_alert=True)
        return
    
    category_name = Keyboards.CATEGORY_NAMES.get(category, category)
    balance = user['balance']
    
    text = f"""📦 *{category_name}*
━━━━━━━━━━━━━━━━━━━━━

💰 رصيدك: *{balance:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

🛍️ اختر المنتج:"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.category_products(category)
    )


async def handle_product(query, user: Dict, data: str):
    """Handle product details view"""
    item_key = data.replace('product_', '')
    product = ProductManager.get(item_key)
    
    if not product:
        await query.answer("❌ المنتج غير متوفر", show_alert=True)
        return
    
    # Increment view count
    ProductManager.increment_view(item_key)
    
    product_name = product['name']
    price = product['price']
    original_price = product.get('original_price')
    description = product.get('description', '')
    sold_count = product['sold_count']
    delivery_time = product.get('delivery_time', 'فوري')
    stock = product['stock']
    
    # Build price text
    if original_price and original_price > price:
        discount = round((1 - price / original_price) * 100)
        price_text = f"~~{original_price:.0f}~~ → *{price:.0f}ج*"
        savings_text = f"\n💰 توفير: {original_price - price:.0f}ج ({discount}%)"
    else:
        price_text = f"*{price:.0f}ج*"
        savings_text = ''
    
    # Cashback calculation
    level_info = UserManager.get_level_info(user['id'])
    current_level = level_info.get('current', {}) if level_info.get('current') else {}
    level_bonus = current_level.get('cashback_bonus', 0)
    base_cashback = product.get('cashback_percent', 3)
    total_cashback_percent = base_cashback + level_bonus
    cashback = price * total_cashback_percent / 100
    
    # Stock info
    if stock == 0:
        stock_text = "\n❌ *نفد المخزون*"
    elif stock > 0:
        stock_text = f"\n📦 المتبقي: {stock} قطعة"
    else:
        stock_text = ""
    
    text = f"""🛍️ *{product_name}*
━━━━━━━━━━━━━━━━━━━━━

💵 السعر: {price_text}{savings_text}
💎 كاش باك: +{cashback:.0f}ج ({total_cashback_percent:.0f}%)
📈 المبيعات: {sold_count}
⏱️ التسليم: {delivery_time}{stock_text}

━━━━━━━━━━━━━━━━━━━━━

📝 {description}

━━━━━━━━━━━━━━━━━━━━━

✅ *متوفر* • ⚡ *تسليم فوري* • 🛡️ *ضمان كامل*"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.product_details(product, user)
    )


async def handle_buy(query, context: ContextTypes.DEFAULT_TYPE, user: Dict, data: str):
    """Handle buy action"""
    item_key = data.replace('buy_', '')
    product = ProductManager.get(item_key)
    
    if not product:
        await query.answer("❌ المنتج غير متوفر", show_alert=True)
        return
    
    # Check stock
    in_stock, stock_msg = ProductManager.check_stock(item_key)
    if not in_stock:
        await query.answer(f"❌ {stock_msg}", show_alert=True)
        return
    
    price = product['price']
    balance = user['balance']
    
    # Check balance
    if balance < price:
        needed = price - balance
        text = f"""❌ *رصيدك غير كافٍ!*

💰 رصيدك الحالي: {balance:.0f}ج
💸 سعر المنتج: {price:.0f}ج
📈 المطلوب إضافته: {needed:.0f}ج"""

        buttons = [
            [InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')],
            [InlineKeyboardButton('◀️ رجوع', callback_data=f"product_{item_key}")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # Check if product requires input
    required_fields_json = product.get('required_fields')
    required_fields = json.loads(required_fields_json) if required_fields_json else []
    
    if required_fields:
        # Start input collection
        db.execute("DELETE FROM pending_inputs WHERE user_id = ?", (user['id'],))
        
        expires = (datetime.now() + timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)).isoformat()
        now = datetime.now().isoformat()
        
        db.execute(
            """INSERT INTO pending_inputs
               (user_id, action_type, item_key, current_step, total_steps,
                collected_data, expires_at, created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (user['id'], 'purchase', item_key, 0, len(required_fields), '{}', expires, now)
        )
        
        field_labels = {
            'player_id': '🎮 أدخل Player ID الخاص بك:',
            'pubg_id': '🔫 أدخل PUBG ID الخاص بك:',
            'ml_id': '⚔️ أدخل ML ID (معرف اللاعب):',
            'zone_id': '🌍 أدخل Zone ID (معرف السيرفر):',
        }
        
        current_field = required_fields[0]
        field_label = field_labels.get(current_field, f'أدخل {current_field}:')
        product_name = product['name']
        timeout = Config.SESSION_TIMEOUT_MINUTES
        
        text = f"""📝 *إدخال بيانات الشحن*
━━━━━━━━━━━━━━━━━━━━━

🛍️ المنتج: {product_name}
💰 السعر: {price:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

{field_label}

⚠️ *تأكد من صحة البيانات!*
⏰ صلاحية الجلسة: {timeout} دقائق"""

        context.user_data['waiting_for'] = 'product_input'
        
        buttons = [
            [InlineKeyboardButton('❌ إلغاء', callback_data='cancel_purchase')]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # No input required, complete purchase directly
        await complete_purchase(query, context, user, product, {})


async def handle_cancel_purchase(query, user: Dict):
    """Handle purchase cancellation"""
    db.execute("DELETE FROM pending_inputs WHERE user_id = ?", (user['id'],))
    
    await query.edit_message_text(
        "❌ تم إلغاء عملية الشراء",
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def complete_purchase(query, context, user: Dict, product: Dict, input_data: Dict):
    """Complete the purchase process"""
    success, result, order_id = OrderManager.create(
        user['id'],
        product,
        input_data
    )
    
    if not success:
        await query.edit_message_text(
            f"❌ {result}",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Get updated user
    user = UserManager.get(user['id'])
    order = OrderManager.get(order_id)
    
    product_name = product['name']
    total_price = order['total_price']
    cashback_amount = order['cashback_amount']
    balance = user['balance']
    
    # Build input text for admin
    if input_data:
        input_lines = [f"• {k}: `{v}`" for k, v in input_data.items()]
        input_text = '\n'.join(input_lines)
    else:
        input_text = 'لا توجد'
    
    user_id = user['id']
    username = user.get('username', 'N/A')
    
    # Notify admins
    admin_msg = f"""🛒 *طلب جديد!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
👤 المستخدم: `{user_id}` @{username}

🛍️ المنتج: {product_name}
💰 السعر: {total_price:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📋 *بيانات الشحن:*
{input_text}"""

    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                admin_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboards.admin_order_actions(order_id)
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # User confirmation
    text = f"""✅ *تم تقديم الطلب بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
🛍️ المنتج: {product_name}
💰 السعر: {total_price:.0f}ج
💎 كاش باك: +{cashback_amount:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك المتبقي: *{balance:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

⏳ سيتم تنفيذ طلبك في أقرب وقت!
📱 سنُعلمك فور التنفيذ."""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


# ══════════════════════════════════════════════════════════════════
# DEPOSIT HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_deposit(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle deposit menu"""
    balance = user['balance']
    min_dep = Config.MIN_DEPOSIT
    max_dep = Config.MAX_DEPOSIT
    fee_percent = Config.DEPOSIT_FEE_PERCENT
    fee_max = Config.DEPOSIT_FEE_MAX
    
    text = f"""💳 *شحن الرصيد*
━━━━━━━━━━━━━━━━━━━━━

💰 رصيدك الحالي: *{balance:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

📌 *اختر طريقة الدفع:*

📱 *فودافون كاش* - موافقة سريعة
💎 *USDT (BEP20)* - موافقة فورية

━━━━━━━━━━━━━━━━━━━━━

💵 الحد الأدنى: {min_dep:.0f}ج
💵 الحد الأقصى: {max_dep:.0f}ج
💸 عمولة: {fee_percent}% (حد أقصى {fee_max}ج)"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.deposit_methods()
    )


async def handle_deposit_vodafone(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle Vodafone Cash deposit"""
    vodafone_number = Config.VODAFONE_NUMBER
    auto_threshold = Config.AUTO_APPROVE_THRESHOLD
    
    text = f"""📱 *إيداع فودافون كاش*
━━━━━━━━━━━━━━━━━━━━━

📞 *رقم فودافون كاش:*
`{vodafone_number}`

━━━━━━━━━━━━━━━━━━━━━

📌 *خطوات الإيداع:*

1️⃣ افتح تطبيق فودافون كاش
2️⃣ اختر "تحويل أموال"
3️⃣ أدخل الرقم: `{vodafone_number}`
4️⃣ أدخل المبلغ المطلوب
5️⃣ أكد العملية
6️⃣ أرسل صورة الإيصال هنا

━━━━━━━━━━━━━━━━━━━━━

⚡ *إيداعات ≤{auto_threshold:.0f}ج:* موافقة فورية
⏰ *إيداعات أكبر:* 5-30 دقيقة

━━━━━━━━━━━━━━━━━━━━━

📤 *أرسل صورة الإيصال الآن*"""

    context.user_data['waiting_for'] = 'deposit_image'
    context.user_data['deposit_method'] = 'vodafone'
    
    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data='deposit')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_deposit_usdt(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle USDT deposit"""
    usdt_wallet = Config.USDT_WALLET
    usdt_rate = Config.USDT_TO_EGP_RATE
    
    text = f"""💎 *إيداع USDT*
━━━━━━━━━━━━━━━━━━━━━

🔗 *عنوان المحفظة (BEP20 - BSC):*
`{usdt_wallet}`

━━━━━━━━━━━━━━━━━━━━━

⚠️ *مهم جداً:*
• استخدم شبكة *BSC (BEP20)* فقط
• تأكد من العنوان قبل الإرسال
• انتظر تأكيد المعاملة

━━━━━━━━━━━━━━━━━━━━━

💵 سعر الصرف: 1 USDT = {usdt_rate:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📌 *خطوات الإيداع:*

1️⃣ أرسل USDT للعنوان أعلاه
2️⃣ انتظر تأكيد المعاملة
3️⃣ أرسل صورة المعاملة هنا

━━━━━━━━━━━━━━━━━━━━━

✅ *موافقة فورية بعد التحقق من البلوكتشين*

━━━━━━━━━━━━━━━━━━━━━

📤 *أرسل صورة المعاملة الآن*"""

    context.user_data['waiting_for'] = 'deposit_image'
    context.user_data['deposit_method'] = 'usdt'
    
    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data='deposit')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# ORDER HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_my_orders(query, user: Dict):
    """Handle my orders view"""
    orders = OrderManager.get_user_orders(user['id'])
    
    if not orders:
        text = """📭 *لا توجد طلبات*

لم تقم بأي عمليات شراء بعد.
تصفح المتجر وابدأ التسوق!"""
        
        buttons = [
            [InlineKeyboardButton('🛍️ المتجر', callback_data='shop')],
            [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    status_icons = {
        'pending': '⏳',
        'processing': '🔄',
        'done': '✅',
        'completed': '✅',
        'cancelled': '❌'
    }
    
    text = "📦 *طلباتك:*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for order in orders[:10]:
        status = order['status']
        icon = status_icons.get(status, '❓')
        order_id = order['order_id']
        total_price = order['total_price']
        created_at = order.get('created_at', '')
        date = created_at[:10] if created_at else ''
        text += f"{icon} `{order_id}` | {total_price:.0f}ج | {date}\n"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.order_list(orders)
    )


async def handle_order_details(query, user: Dict, data: str):
    """Handle order details view"""
    order_id = data.replace('order_', '')
    order = db.execute(
        "SELECT * FROM orders WHERE order_id = ? AND user_id = ?",
        (order_id, user['id']),
        fetch_one=True
    )
    
    if not order:
        await query.answer("❌ الطلب غير موجود", show_alert=True)
        return
    
    status_names = {
        'pending': '⏳ قيد الانتظار',
        'processing': '🔄 جاري التنفيذ',
        'done': '✅ مكتمل',
        'completed': '✅ مكتمل',
        'cancelled': '❌ ملغي'
    }
    
    product_name = order['product_name']
    total_price = order['total_price']
    created_at = order.get('created_at', '')
    date_display = created_at[:16] if created_at else ''
    status = order['status']
    status_display = status_names.get(status, status)
    
    text = f"""📦 *تفاصيل الطلب*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
🛍️ المنتج: {product_name}
💰 السعر: {total_price:.0f}ج
📅 التاريخ: {date_display}

━━━━━━━━━━━━━━━━━━━━━

📊 الحالة: {status_display}"""

    discount_amount = order.get('discount_amount', 0)
    if discount_amount and discount_amount > 0:
        text += f"\n🏷️ الخصم: {discount_amount:.0f}ج"
    
    cashback_amount = order.get('cashback_amount', 0)
    if cashback_amount and cashback_amount > 0:
        text += f"\n💎 كاش باك: +{cashback_amount:.0f}ج"
    
    delivery_data = order.get('delivery_data')
    if status in ['done', 'completed'] and delivery_data:
        text += f"""

━━━━━━━━━━━━━━━━━━━━━

📬 *بيانات التسليم:*
{delivery_data}

⚠️ احتفظ بهذه البيانات!"""

    cancel_reason = order.get('cancel_reason')
    if status == 'cancelled' and cancel_reason:
        text += f"\n\n❌ سبب الإلغاء: {cancel_reason}"
    
    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data='my_orders')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# REWARDS HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_rewards(query, user: Dict):
    """Handle rewards view"""
    daily = db.execute(
        "SELECT * FROM daily_rewards WHERE user_id = ?",
        (user['id'],),
        fetch_one=True
    )
    
    level_info = UserManager.get_level_info(user['id'])
    level = level_info.get('current', {}) if level_info.get('current') else {}
    daily_bonus = level.get('daily_bonus', 0)
    
    today = datetime.now().date()
    can_claim = True
    streak = 0
    max_streak = 0
    total_claimed = 0
    
    if daily:
        last_claim_date = daily.get('last_claim_date')
        if last_claim_date:
            last_claim = datetime.strptime(last_claim_date, '%Y-%m-%d').date()
            can_claim = last_claim < today
        streak = daily.get('current_streak', 0)
        max_streak = daily.get('max_streak', 0)
        total_claimed = daily.get('total_claimed', 0)
    
    base_reward = Config.DAILY_BASE_REWARD
    max_streak_bonus = Config.MAX_DAILY_STREAK_BONUS
    streak_bonus = min(streak, max_streak_bonus)
    today_reward = base_reward + streak_bonus + daily_bonus
    
    claim_status = "🟢 متاحة الآن!" if can_claim else "🔴 تم الاستلام اليوم"
    cashback_total = user.get('cashback_total', 0)
    
    text = f"""🎁 *المكافآت والجوائز*
━━━━━━━━━━━━━━━━━━━━━

🗓️ *المكافأة اليومية:*
{claim_status}

💰 مكافأة اليوم: *{today_reward:.0f}ج*
🔥 سلسلة الأيام الحالية: {streak}
🏆 أعلى سلسلة: {max_streak}
💵 إجمالي المكتسب: {total_claimed:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📈 *كيف تزيد مكافأتك:*
• المكافأة الأساسية: {base_reward}ج
• +1ج عن كل يوم متتالي (حتى {max_streak_bonus})
• بونص المستوى: +{daily_bonus}ج

━━━━━━━━━━━━━━━━━━━━━

💎 *نظام الكاش باك:*
تحصل على كاش باك تلقائي عند كل شراء!
كاش باك مكتسب: {cashback_total:.0f}ج"""

    buttons = []
    
    if can_claim:
        buttons.append([
            InlineKeyboardButton(
                f"🎁 استلم {today_reward:.0f}ج",
                callback_data='claim_daily'
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton('⏳ عد غداً للاستلام', callback_data='_')
        ])
    
    buttons.append([
        InlineKeyboardButton('🏠 الرئيسية', callback_data='home')
    ])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_claim_daily(query, user: Dict):
    """Handle daily reward claim"""
    daily = db.execute(
        "SELECT * FROM daily_rewards WHERE user_id = ?",
        (user['id'],),
        fetch_one=True
    )
    
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # Check if already claimed
    if daily:
        last_claim_date = daily.get('last_claim_date')
        if last_claim_date:
            last_claim = datetime.strptime(last_claim_date, '%Y-%m-%d').date()
            if last_claim == today:
                await query.answer("⏳ لقد استلمت مكافأة اليوم بالفعل!", show_alert=True)
                return
    
    # Calculate streak
    new_streak = 1
    if daily:
        last_claim_date = daily.get('last_claim_date')
        if last_claim_date:
            last_claim = datetime.strptime(last_claim_date, '%Y-%m-%d').date()
            if (today - last_claim).days == 1:
                new_streak = daily.get('current_streak', 0) + 1
    
    # Calculate reward
    level_info = UserManager.get_level_info(user['id'])
    current_level = level_info.get('current', {}) if level_info.get('current') else {}
    daily_bonus = current_level.get('daily_bonus', 0)
    
    base_reward = Config.DAILY_BASE_REWARD
    streak_bonus = min(new_streak - 1, Config.MAX_DAILY_STREAK_BONUS)
    reward = base_reward + streak_bonus + daily_bonus
    
    # Add balance
    UserManager.update_balance(
        user['id'],
        reward,
        'daily_reward',
        f"DAY_{new_streak}",
        f"مكافأة يومية - يوم {new_streak}"
    )
    
    # Update daily rewards
    old_max_streak = daily.get('max_streak', 0) if daily else 0
    max_streak = max(old_max_streak, new_streak)
    old_total_claimed = daily.get('total_claimed', 0) if daily else 0
    total_claimed = old_total_claimed + reward
    old_total_claims = daily.get('total_claims', 0) if daily else 0
    total_claims = old_total_claims + 1
    
    db.execute(
        """INSERT OR REPLACE INTO daily_rewards
           (user_id, last_claim_date, current_streak, max_streak, total_claimed, total_claims)
           VALUES(?,?,?,?,?,?)""",
        (user['id'], today_str, new_streak, max_streak, total_claimed, total_claims)
    )
    
    if new_streak > 1:
        streak_msg = "🏆 رائع! حافظ على السلسلة!"
    else:
        streak_msg = "👍 ابدأ سلسلتك! عد غداً!"
    
    text = f"""🎉 *تم استلام المكافأة اليومية!*
━━━━━━━━━━━━━━━━━━━━━

💰 المكافأة: *+{reward:.0f}ج*
🔥 سلسلة الأيام: {new_streak} يوم متتالي

━━━━━━━━━━━━━━━━━━━━━

{streak_msg}

⏰ عد غداً لاستلام مكافأة أخرى!"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


# ══════════════════════════════════════════════════════════════════
# COUPON & REFERRAL HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_coupon_input(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle coupon input"""
    context.user_data['waiting_for'] = 'coupon_code'
    
    text = """🎟️ *استخدام كوبون*
━━━━━━━━━━━━━━━━━━━━━

أدخل كود الكوبون الخاص بك:"""

    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_referral(query, user: Dict):
    """Handle referral view"""
    bonus = db.get_config('referral_bonus', Config.REFERRAL_BONUS)
    order_bonus = db.get_config('referral_order_bonus', Config.REFERRAL_ORDER_BONUS)
    
    referral_count = user.get('referral_count', 0)
    referral_earnings = user.get('referral_earnings', 0)
    
    user_id = user['id']
    ref_link = f"https://t.me/{state.bot_username}?start=r{user_id}"
    
    text = f"""👥 *برنامج الإحالة*
━━━━━━━━━━━━━━━━━━━━━

🎁 *المكافآت:*
• {bonus}ج عند تسجيل صديق جديد
• {order_bonus}ج عند أول عملية شراء للصديق

━━━━━━━━━━━━━━━━━━━━━

📊 *إحصائياتك:*
• عدد الإحالات: {referral_count}
• إجمالي المكتسب: {referral_earnings:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

🔗 *رابط الإحالة الخاص بك:*
`{ref_link}`

━━━━━━━━━━━━━━━━━━━━━

📤 شارك الرابط مع أصدقائك واكسب!"""

    share_text = f"🔥 أفضل متجر شحن ألعاب! شحن فوري وأسعار رخيصة. جرب الآن: {ref_link}"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"
    
    buttons = [
        [InlineKeyboardButton('📤 مشاركة الرابط', url=share_url)],
        [InlineKeyboardButton('📋 نسخ الرابط', callback_data=f'copy_ref_{user_id}')],
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# NOTIFICATIONS HANDLER
# ══════════════════════════════════════════════════════════════════

async def handle_notifications(query, user: Dict):
    """Handle notifications view"""
    notifications = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 20",
        (user['id'],),
        fetch_all=True
    )
    
    # Mark as read
    db.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
        (user['id'],)
    )
    
    if not notifications:
        text = "🔔 *الإشعارات*\n\nلا توجد إشعارات جديدة."
    else:
        text = "🔔 *الإشعارات*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        type_icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'promo': '🎁',
            'order': '📦',
            'deposit': '💰',
            'level_up': '🏆'
        }
        
        for n in notifications[:10]:
            notif_type = n.get('type', 'info')
            icon = type_icons.get(notif_type, '🔵')
            is_read = n.get('is_read', 0)
            read_indicator = '' if is_read else '🆕 '
            title = n.get('title', '')
            message = n.get('message', '')
            created_at = n.get('created_at', '')
            date = created_at[5:16] if created_at else ''
            
            text += f"{read_indicator}{icon} *{title}*\n"
            if message:
                text += f"   {message[:50]}\n"
            text += f"   _{date}_\n\n"
    
    buttons = [
        [InlineKeyboardButton('🗑️ مسح الكل', callback_data='clear_notifications')],
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# SUPPORT HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_support(query, user: Dict):
    """Handle support menu"""
    open_ticket = db.execute(
        "SELECT * FROM tickets WHERE user_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
        (user['id'],),
        fetch_one=True
    )
    
    has_open = open_ticket is not None
    
    text = """🆘 *الدعم الفني*
━━━━━━━━━━━━━━━━━━━━━

⏰ وقت الرد المتوقع: 5 دقائق - 24 ساعة

📌 للمساعدة السريعة، افتح تذكرة جديدة وسنرد عليك في أقرب وقت.

💡 نصيحة: اذكر رقم الطلب إن وجد لتسريع المساعدة.

━━━━━━━━━━━━━━━━━━━━━

🤖 *الدعم الذكي:*
يمكنك إرسال سؤالك مباشرة وسيرد عليك الذكاء الاصطناعي!"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.support_menu(has_open)
    )


async def handle_new_ticket(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle new ticket creation"""
    context.user_data['waiting_for'] = 'new_ticket'
    
    text = """📝 *فتح تذكرة دعم جديدة*
━━━━━━━━━━━━━━━━━━━━━

اكتب مشكلتك أو استفسارك بالتفصيل.

💡 *نصائح لرد أسرع:*
• اذكر رقم الطلب إن وجد
• اشرح المشكلة بوضوح
• أرفق صور إن لزم الأمر

━━━━━━━━━━━━━━━━━━━━━

✍️ *اكتب رسالتك الآن:*"""

    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data='support')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_my_tickets(query, user: Dict):
    """Handle my tickets view"""
    tickets = db.execute(
        "SELECT * FROM tickets WHERE user_id = ? ORDER BY id DESC LIMIT 15",
        (user['id'],),
        fetch_all=True
    )
    
    if not tickets:
        text = "📋 *تذاكري*\n\nلا توجد تذاكر سابقة."
        buttons = [
            [InlineKeyboardButton('📝 تذكرة جديدة', callback_data='new_ticket')],
            [InlineKeyboardButton('◀️ رجوع', callback_data='support')]
        ]
    else:
        text = "📋 *تذاكري:*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        buttons = []
        
        for t in tickets:
            ticket_id = t['id']
            status = t['status']
            status_icon = '🟢' if status == 'open' else '🔴'
            subject = (t.get('subject') or 'بدون عنوان')[:25]
            text += f"{status_icon} تذكرة #{ticket_id} - {subject}\n"
            buttons.append([
                InlineKeyboardButton(f"💬 #{ticket_id}", callback_data=f"ticket_{ticket_id}")
            ])
        
        buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='support')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_ticket_view(query, context: ContextTypes.DEFAULT_TYPE, user: Dict, data: str):
    """Handle ticket view"""
    ticket_id = int(data.replace('ticket_', ''))
    
    ticket = db.execute(
        "SELECT * FROM tickets WHERE id = ? AND user_id = ?",
        (ticket_id, user['id']),
        fetch_one=True
    )
    
    if not ticket:
        await query.answer("❌ التذكرة غير موجودة", show_alert=True)
        return
    
    messages = db.execute(
        "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY id",
        (ticket_id,),
        fetch_all=True
    )
    
    status = ticket['status']
    status_display = '🟢 مفتوحة' if status == 'open' else '🔴 مغلقة'
    
    text = f"💬 *تذكرة #{ticket_id}* - {status_display}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for msg in messages[-10:]:
        sender_type = msg['sender_type']
        ai_generated = msg.get('ai_generated', 0)
        
        if sender_type == 'user':
            sender = '👤 أنت'
        elif ai_generated:
            sender = '🤖 AI'
        else:
            sender = '👨‍💼 الدعم'
        
        created_at = msg.get('created_at', '')
        time_str = created_at[11:16] if created_at else ''
        message_text = msg.get('message', '')[:200]
        
        text += f"{sender} _{time_str}_:\n{message_text}\n\n"
    
    buttons = []
    
    if status == 'open':
        buttons.append([
            InlineKeyboardButton('✍️ إرسال رد', callback_data=f"reply_ticket_{ticket_id}")
        ])
    
    buttons.append([
        InlineKeyboardButton('◀️ رجوع', callback_data='my_tickets')
    ])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_ticket_reply(query, context: ContextTypes.DEFAULT_TYPE, user: Dict, data: str):
    """Handle ticket reply"""
    ticket_id = int(data.replace('reply_ticket_', ''))
    
    context.user_data['waiting_for'] = 'ticket_reply'
    context.user_data['ticket_id'] = ticket_id
    
    text = f"""✍️ *الرد على تذكرة #{ticket_id}*

اكتب ردك:"""

    buttons = [
        [InlineKeyboardButton('◀️ رجوع', callback_data=f"ticket_{ticket_id}")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_faq(query, user: Dict):
    """Handle FAQ view"""
    text = """❓ *الأسئلة الشائعة*
━━━━━━━━━━━━━━━━━━━━━

*س: كم يستغرق تنفيذ الطلب؟*
ج: معظم الطلبات تُنفذ خلال 5-30 دقيقة.

*س: ما هي طرق الدفع المتاحة؟*
ج: فودافون كاش و USDT (BEP20)

*س: هل الشحن مضمون؟*
ج: نعم، ضمان 100% على جميع المنتجات.

*س: كيف أحصل على الكاش باك؟*
ج: يُضاف تلقائياً لرصيدك عند كل عملية شراء.

*س: ماذا لو لم يصل الشحن؟*
ج: تواصل معنا عبر الدعم وسنحل المشكلة.

*س: هل يمكنني استرداد أموالي؟*
ج: نعم، في حالة عدم تنفيذ الطلب.

━━━━━━━━━━━━━━━━━━━━━

لم تجد إجابتك؟ افتح تذكرة دعم!"""

    buttons = [
        [InlineKeyboardButton('📝 تذكرة جديدة', callback_data='new_ticket')],
        [InlineKeyboardButton('◀️ رجوع', callback_data='support')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    # ══════════════════════════════════════════════════════════════════
# ADMIN HANDLERS
# ══════════════════════════════════════════════════════════════════

async def handle_admin_panel(query):
    """Handle admin panel view"""
    # Get stats
    total_users = db.execute("SELECT COUNT(*) as c FROM users", fetch_one=True)['c']
    today = datetime.now().date().isoformat()
    new_users_today = db.execute(
        f"SELECT COUNT(*) as c FROM users WHERE join_date LIKE '{today}%'",
        fetch_one=True
    )['c']
    
    text = f"""⚙️ *لوحة تحكم المدير*
━━━━━━━━━━━━━━━━━━━━━

👥 المستخدمين: {total_users:,} (+{new_users_today} اليوم)
⏱️ وقت التشغيل: {state.get_uptime()}
🤖 طلبات AI: {state.ai_requests_count}
📨 الرسائل: {state.total_messages_processed}

━━━━━━━━━━━━━━━━━━━━━"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.admin_panel()
    )


async def handle_admin_callbacks(query, context, user_id: int, data: str):
    """Route admin callbacks"""
    if data == 'admin_orders':
        await handle_admin_orders(query)
    elif data == 'admin_deposits':
        await handle_admin_deposits(query)
    elif data == 'admin_tickets':
        await handle_admin_tickets(query, context)
    elif data == 'admin_users':
        await handle_admin_users(query)
    elif data == 'admin_stats':
        await handle_admin_stats(query)
    elif data == 'admin_profits':
        await handle_admin_profits(query)
    elif data == 'admin_promo':
        await handle_admin_promo(query, context)
    elif data == 'admin_broadcast':
        await handle_admin_broadcast(query, context)
    elif data == 'admin_new_coupon':
        await handle_admin_new_coupon(query, context)
    elif data == 'admin_youtube_ad':
        await handle_admin_youtube_ad(query, context)
    elif data == 'admin_settings':
        await handle_admin_settings(query, context)
    elif data == 'admin_giftcard':
        await handle_admin_giftcard(query, context)


async def handle_admin_orders(query):
    """Handle admin orders view"""
    orders = OrderManager.get_pending_orders()
    
    if not orders:
        await query.edit_message_text(
            "✅ *لا توجد طلبات معلقة*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_button('admin_panel')
        )
        return
    
    text = f"📦 *الطلبات المعلقة* ({len(orders)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    buttons = []
    
    for order in orders[:15]:
        username = order.get('username') or order['user_id']
        text += f"`{order['order_id']}` | {order['product_name'][:15]} | {order['total_price']:.0f}ج\n"
        buttons.append([
            InlineKeyboardButton(
                f"✅ {order['order_id'][:10]}",
                callback_data=f"execute_{order['order_id']}"
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=f"cancel_order_{order['order_id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_deposits(query):
    """Handle admin deposits view"""
    deposits = db.execute(
        """SELECT d.*, u.username, u.first_name
           FROM deposits d
           LEFT JOIN users u ON d.user_id = u.id
           WHERE d.status = 'pending'
           ORDER BY d.id DESC LIMIT 25""",
        fetch_all=True
    )
    
    if not deposits:
        await query.edit_message_text(
            "✅ *لا توجد إيداعات معلقة*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_button('admin_panel')
        )
        return
    
    text = f"💰 *الإيداعات المعلقة* ({len(deposits)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    buttons = []
    
    for dep in deposits:
        method = '📱' if dep['payment_method'] == 'vodafone' else '💎'
        confidence = dep.get('ai_confidence', 0) or 0
        text += f"{method} #{dep['id']} | {dep['user_id']} | {dep['amount']:.0f}ج | {confidence:.0%}\n"
        buttons.append([
            InlineKeyboardButton(
                f"✅ #{dep['id']}",
                callback_data=f"approve_dep_{dep['id']}"
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=f"reject_dep_{dep['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_approve(query, context, data: str):
    """Handle admin approval actions"""
    if data.startswith('approve_dep_'):
        dep_id = int(data.replace('approve_dep_', ''))
        
        deposit = db.execute(
            "SELECT * FROM deposits WHERE id = ? AND status = 'pending'",
            (dep_id,),
            fetch_one=True
        )
        
        if not deposit:
            await query.answer("❌ الإيداع غير موجود أو تمت معالجته", show_alert=True)
            return
        
        # Calculate fee
        fee, final_amount = calculate_deposit_fee(deposit['amount'])
        now = datetime.now().isoformat()
        
        # Update deposit
        db.execute(
            """UPDATE deposits SET
               status = 'approved',
               amount_after_fee = ?,
               reviewed_by = ?,
               reviewed_at = ?
               WHERE id = ?""",
            (final_amount, query.from_user.id, now, dep_id)
        )
        
        # Add balance
        new_balance = UserManager.update_balance(
            deposit['user_id'],
            final_amount,
            'deposit',
            f"DEP_{dep_id}",
            f"إيداع #{dep_id}",
            fee
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                deposit['user_id'],
                f"""✅ *تم إيداع رصيدك!*

💵 المبلغ: {deposit['amount']:.0f}ج
💸 العمولة: {fee:.1f}ج
💰 الصافي: *{final_amount:.0f}ج*

💳 رصيدك الجديد: *{new_balance:.0f}ج*""",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        await query.answer(f"✅ تم إيداع {final_amount:.0f}ج", show_alert=True)
        await handle_admin_deposits(query)


async def handle_admin_reject(query, context, data: str):
    """Handle admin rejection actions"""
    if data.startswith('reject_dep_'):
        dep_id = int(data.replace('reject_dep_', ''))
        
        deposit = db.execute(
            "SELECT user_id FROM deposits WHERE id = ?",
            (dep_id,),
            fetch_one=True
        )
        
        db.execute(
            """UPDATE deposits SET
               status = 'rejected',
               reviewed_by = ?,
               reviewed_at = ?,
               rejection_reason = 'تم الرفض بواسطة الإدارة'
               WHERE id = ?""",
            (query.from_user.id, datetime.now().isoformat(), dep_id)
        )
        
        if deposit:
            try:
                await context.bot.send_message(
                    deposit['user_id'],
                    "❌ *تم رفض طلب الإيداع*\n\nتواصل مع الدعم إذا كنت تعتقد أن هذا خطأ.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        await query.answer("❌ تم الرفض", show_alert=True)
        await handle_admin_deposits(query)


async def handle_admin_execute(query, context, data: str):
    """Handle order execution"""
    order_id = data.replace('execute_', '')
    
    context.user_data['admin_execute_order'] = order_id
    context.user_data['waiting_for'] = 'delivery_data'
    
    order = OrderManager.get(order_id)
    
    if not order:
        await query.answer("❌ الطلب غير موجود", show_alert=True)
        return
    
    input_data = json.loads(order.get('input_data', '{}')) if order.get('input_data') else {}
    input_text = '\n'.join([f"• {k}: `{v}`" for k, v in input_data.items()]) if input_data else 'لا توجد'
    
    text = f"""📝 *تنفيذ الطلب*
━━━━━━━━━━━━━━━━━━━━━

🆔 `{order_id}`
🛍️ {order['product_name']}
💰 {order['total_price']:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📋 *بيانات الشحن:*
{input_text}

━━━━━━━━━━━━━━━━━━━━━

✏️ *أدخل بيانات التسليم:*
(الكود أو البيانات التي ستُرسل للعميل)"""

    buttons = [
        [InlineKeyboardButton('◀️ إلغاء', callback_data='admin_orders')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_cancel_order(query, context, data: str):
    """Handle order cancellation"""
    order_id = data.replace('cancel_order_', '')
    
    success, message = OrderManager.cancel_order(
        order_id,
        "تم الإلغاء بواسطة الإدارة",
        refund=True,
        admin_id=query.from_user.id
    )
    
    if success:
        order = OrderManager.get(order_id)
        if order:
            try:
                await context.bot.send_message(
                    order['user_id'],
                    f"❌ *تم إلغاء طلبك*\n\n🆔 `{order_id}`\n💰 تم إرجاع {order['total_price']:.0f}ج لرصيدك",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
    
    await query.answer("❌ تم الإلغاء وإرجاع المبلغ" if success else message, show_alert=True)
    await handle_admin_orders(query)


async def handle_admin_tickets(query, context):
    """Handle admin tickets view"""
    tickets = db.execute(
        """SELECT t.*, u.username, u.first_name
           FROM tickets t
           LEFT JOIN users u ON t.user_id = u.id
           WHERE t.status = 'open'
           ORDER BY t.updated_at DESC LIMIT 25""",
        fetch_all=True
    )
    
    if not tickets:
        await query.edit_message_text(
            "✅ *لا توجد تذاكر مفتوحة*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_button('admin_panel')
        )
        return
    
    text = f"🎫 *التذاكر المفتوحة* ({len(tickets)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    buttons = []
    
    for t in tickets:
        username = f"@{t['username']}" if t.get('username') else f"#{t['user_id']}"
        subject = (t.get('subject') or 'بدون عنوان')[:20]
        text += f"#{t['id']} | {username} | {subject}\n"
        buttons.append([
            InlineKeyboardButton(
                f"💬 #{t['id']}",
                callback_data=f"admin_ticket_{t['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_users(query):
    """Handle admin users view"""
    users = db.execute(
        """SELECT * FROM users
           ORDER BY last_active DESC LIMIT 20""",
        fetch_all=True
    )
    
    text = "👥 *المستخدمين:*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    buttons = []
    
    for u in users:
        status = '🔴' if u['banned'] else '🟢'
        username = f"@{u['username']}" if u.get('username') else f"#{u['id']}"
        text += f"{status} {username} | {u['balance']:.0f}ج | {u['total_orders']} طلب\n"
        
        ban_btn = '🔓' if u['banned'] else '🔒'
        buttons.append([
            InlineKeyboardButton(f"👤 {u['id']}", callback_data=f"user_{u['id']}"),
            InlineKeyboardButton(ban_btn, callback_data=f"{'unban' if u['banned'] else 'ban'}_{u['id']}")
        ])
    
    buttons.append([InlineKeyboardButton('🔍 بحث', callback_data='search_user')])
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_user(query, context, data: str):
    """Handle admin user view"""
    user_id = int(data.replace('user_', ''))
    user = UserManager.get(user_id)
    
    if not user:
        await query.answer("❌ المستخدم غير موجود", show_alert=True)
        return
    
    level_info = UserManager.get_level_info(user_id)
    level = level_info.get('current', {}) if level_info.get('current') else {}
    
    text = f"""👤 *معلومات المستخدم*
━━━━━━━━━━━━━━━━━━━━━

🆔 المعرف: `{user_id}`
👤 اسم المستخدم: @{user.get('username') or 'N/A'}
📛 الاسم: {user.get('first_name') or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━

💰 الرصيد: {user['balance']:.2f}ج
💸 إجمالي الإنفاق: {user['spent']:.0f}ج
📦 الطلبات: {user['total_orders']}
💳 الإيداعات: {user['total_deposits']:.0f}ج
🎁 كاش باك: {user.get('cashback_total', 0):.0f}ج
👥 الإحالات: {user.get('referral_count', 0)}

━━━━━━━━━━━━━━━━━━━━━

{level.get('badge', '🥉')} المستوى: {level.get('name', 'برونزي')}
📈 درجة الثقة: {user.get('trust_score', 50)}/100

📅 التسجيل: {user['join_date'][:10] if user.get('join_date') else 'N/A'}
🕐 آخر نشاط: {user['last_active'][:16] if user.get('last_active') else 'N/A'}

{"🔴 *محظور*: " + (user.get('ban_reason') or 'غير محدد') if user['banned'] else "🟢 *نشط*"}"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.admin_user_actions(user_id, user['banned'])
    )


async def handle_admin_ban(query, context, data: str):
    """Handle user ban"""
    user_id = int(data.replace('ban_', ''))
    
    UserManager.ban_user(
        user_id,
        "تم الحظر بواسطة الإدارة",
        banned_by=query.from_user.id
    )
    
    try:
        await context.bot.send_message(
            user_id,
            "🚫 *تم حظرك من استخدام البوت*\n\nتواصل مع الدعم للاستفسار.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await query.answer("🔒 تم الحظر", show_alert=True)
    await handle_admin_users(query)


async def handle_admin_unban(query, context, data: str):
    """Handle user unban"""
    user_id = int(data.replace('unban_', ''))
    
    UserManager.unban_user(user_id, query.from_user.id)
    
    try:
        await context.bot.send_message(
            user_id,
            "✅ *تم فك حظرك*\n\nيمكنك استخدام البوت الآن.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await query.answer("🔓 تم فك الحظر", show_alert=True)
    await handle_admin_users(query)


async def handle_admin_add_balance(query, context, data: str):
    """Handle add balance"""
    user_id = int(data.replace('addbal_', ''))
    
    context.user_data['balance_target_user'] = user_id
    context.user_data['balance_action'] = 'add'
    context.user_data['waiting_for'] = 'admin_balance_amount'
    
    text = f"💰 *إضافة رصيد للمستخدم {user_id}*\n\nأدخل المبلغ:"
    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data=f"user_{user_id}")]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_sub_balance(query, context, data: str):
    """Handle subtract balance"""
    user_id = int(data.replace('subbal_', ''))
    
    context.user_data['balance_target_user'] = user_id
    context.user_data['balance_action'] = 'sub'
    context.user_data['waiting_for'] = 'admin_balance_amount'
    
    text = f"💰 *خصم رصيد من المستخدم {user_id}*\n\nأدخل المبلغ:"
    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data=f"user_{user_id}")]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_stats(query):
    """Handle admin statistics"""
    # Basic stats
    total_users = db.execute("SELECT COUNT(*) as c FROM users", fetch_one=True)['c']
    total_orders = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE status IN ('done', 'completed')",
        fetch_one=True
    )['c']
    pending_orders = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE status = 'pending'",
        fetch_one=True
    )['c']
    
    revenue = db.execute(
        "SELECT SUM(total_price) as s FROM orders WHERE status IN ('done', 'completed')",
        fetch_one=True
    )['s'] or 0
    
    deposits = db.execute(
        "SELECT SUM(amount) as s FROM deposits WHERE status = 'approved'",
        fetch_one=True
    )['s'] or 0
    
    # Today stats
    today = datetime.now().date().isoformat()
    today_orders = db.execute(
        f"""SELECT COUNT(*) as c, COALESCE(SUM(total_price), 0) as s
            FROM orders
            WHERE status IN ('done', 'completed') AND created_at LIKE '{today}%'""",
        fetch_one=True
    )
    
    today_deposits = db.execute(
        f"""SELECT COUNT(*) as c, COALESCE(SUM(amount), 0) as s
            FROM deposits
            WHERE status = 'approved' AND created_at LIKE '{today}%'""",
        fetch_one=True
    )
    
    new_users_today = db.execute(
        f"SELECT COUNT(*) as c FROM users WHERE join_date LIKE '{today}%'",
        fetch_one=True
    )['c']
    
    text = f"""📊 *الإحصائيات*
━━━━━━━━━━━━━━━━━━━━━

👥 *المستخدمين:*
• الإجمالي: {total_users:,}
• جديد اليوم: {new_users_today}

📦 *الطلبات:*
• مكتملة: {total_orders:,}
• معلقة: {pending_orders}
• اليوم: {today_orders['c']} ({today_orders['s']:.0f}ج)

💰 *المالية:*
• إجمالي الإيرادات: {revenue:,.0f}ج
• إجمالي الإيداعات: {deposits:,.0f}ج
• إيداعات اليوم: {today_deposits['c']} ({today_deposits['s']:.0f}ج)

━━━━━━━━━━━━━━━━━━━━━

⏱️ وقت التشغيل: {state.get_uptime()}
🤖 طلبات AI: {state.ai_requests_count}"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.back_button('admin_panel')
    )


async def handle_admin_profits(query):
    """Handle admin profits view"""
    # Calculate profits
    revenue = db.execute(
        "SELECT SUM(total_price) as s FROM orders WHERE status IN ('done', 'completed')",
        fetch_one=True
    )['s'] or 0
    
    costs = db.execute(
        """SELECT SUM(p.cost * o.quantity) as s
           FROM orders o
           JOIN products p ON o.product_key = p.item_key
           WHERE o.status IN ('done', 'completed')""",
        fetch_one=True
    )['s'] or 0
    
    deposit_fees = db.execute(
        "SELECT SUM(amount - amount_after_fee) as s FROM deposits WHERE status = 'approved'",
        fetch_one=True
    )['s'] or 0
    
    cashback_paid = db.execute(
        "SELECT SUM(cashback_amount) as s FROM orders WHERE status IN ('done', 'completed')",
        fetch_one=True
    )['s'] or 0
    
    referral_paid = db.execute(
        "SELECT SUM(bonus_amount) as s FROM referrals",
        fetch_one=True
    )['s'] or 0
    
    welcome_paid = db.execute(
        "SELECT SUM(amount) as s FROM transactions WHERE type = 'welcome_bonus'",
        fetch_one=True
    )['s'] or 0
    
    daily_paid = db.execute(
        "SELECT SUM(amount) as s FROM transactions WHERE type = 'daily_reward'",
        fetch_one=True
    )['s'] or 0
    
    gross_profit = revenue - costs
    total_bonuses = cashback_paid + referral_paid + welcome_paid + daily_paid
    net_profit = gross_profit + deposit_fees - total_bonuses
    
    text = f"""💹 *تقرير الأرباح*
━━━━━━━━━━━━━━━━━━━━━

💵 *الإيرادات:*
• إجمالي المبيعات: {revenue:,.0f}ج
• عمولات الإيداع: +{deposit_fees:,.0f}ج

💸 *التكاليف:*
• تكلفة المنتجات: -{costs:,.0f}ج
• كاش باك: -{cashback_paid:,.0f}ج
• مكافآت الإحالة: -{referral_paid:,.0f}ج
• مكافآت الترحيب: -{welcome_paid:,.0f}ج
• المكافآت اليومية: -{daily_paid:,.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📈 *الربح الإجمالي:* {gross_profit:,.0f}ج
📊 *صافي الربح:* {net_profit:,.0f}ج
💎 *هامش الربح:* {(net_profit/revenue*100) if revenue > 0 else 0:.1f}%"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.back_button('admin_panel')
    )


async def handle_admin_promo(query, context):
    """Handle AI promotional post"""
    await query.edit_message_text(
        "📢 *جاري إنشاء ونشر الإعلان...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    success = await post_promotional_content(context)
    
    if success:
        await query.edit_message_text(
            "✅ *تم نشر الإعلان وتثبيته بنجاح!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_button('admin_panel')
        )
    else:
        await query.edit_message_text(
            "❌ فشل نشر الإعلان",
            reply_markup=Keyboards.back_button('admin_panel')
        )


async def handle_admin_broadcast(query, context):
    """Handle broadcast setup"""
    context.user_data['waiting_for'] = 'broadcast_message'
    
    total_users = db.execute(
        "SELECT COUNT(*) as c FROM users WHERE banned = 0",
        fetch_one=True
    )['c']
    
    text = f"""📨 *إذاعة لجميع المستخدمين*
━━━━━━━━━━━━━━━━━━━━━

سيتم الإرسال لـ {total_users:,} مستخدم.

اكتب رسالة الإذاعة:

💡 يمكنك استخدام Markdown للتنسيق."""

    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_panel')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_youtube_ad(query, context):
    """Handle YouTube ad setup"""
    context.user_data['waiting_for'] = 'youtube_url'
    
    text = """🎬 *إنشاء إعلان يوتيوب*
━━━━━━━━━━━━━━━━━━━━━

أرسل رابط فيديو اليوتيوب:

مثال: https://youtube.com/watch?v=xxxxx"""

    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_panel')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_new_coupon(query, context):
    """Handle new coupon creation"""
    context.user_data['waiting_for'] = 'coupon_code_create'
    
    text = """🎟️ *إنشاء كوبون جديد*
━━━━━━━━━━━━━━━━━━━━━

أدخل كود الكوبون:

مثال: WELCOME50"""

    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_panel')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_settings(query, context):
    """Handle admin settings"""
    maintenance = db.get_config('maintenance_mode', False)
    ai_enabled = db.get_config('ai_support_enabled', True)
    
    text = f"""🔧 *الإعدادات*
━━━━━━━━━━━━━━━━━━━━━

🔧 وضع الصيانة: {'🟢 مفعل' if maintenance else '🔴 معطل'}
🤖 دعم AI: {'🟢 مفعل' if ai_enabled else '🔴 معطل'}

━━━━━━━━━━━━━━━━━━━━━

💰 *الإعدادات المالية:*
• عمولة الإيداع: {Config.DEPOSIT_FEE_PERCENT}%
• حد الموافقة التلقائية: {Config.AUTO_APPROVE_THRESHOLD}ج
• سعر USDT: {Config.USDT_TO_EGP_RATE}ج

🎁 *المكافآت:*
• مكافأة الترحيب: {Config.WELCOME_BONUS}ج
• مكافأة الإحالة: {Config.REFERRAL_BONUS}ج"""

    buttons = [
        [
            InlineKeyboardButton(
                '🔧 الصيانة',
                callback_data='toggle_maintenance'
            ),
            InlineKeyboardButton(
                '🤖 AI',
                callback_data='toggle_ai'
            )
        ],
        [InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_giftcard(query, context):
    """Handle gift card creation"""
    context.user_data['waiting_for'] = 'giftcard_amount'
    
    text = """🎁 *إنشاء بطاقة هدية*
━━━━━━━━━━━━━━━━━━━━━

أدخل قيمة البطاقة بالجنيه:"""

    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_panel')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════════════
# MESSAGE HANDLERS
# ══════════════════════════════════════════════════════════════════

@log_action("message")
@maintenance_check
@rate_limited
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Skip commands
    if text.startswith('/'):
        return
    
    # Check ban
    is_banned, _ = UserManager.is_banned(user_id)
    if is_banned and user_id not in Config.ADMIN_IDS:
        return
    
    user = UserManager.create_or_update(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    waiting_for = context.user_data.get('waiting_for')
    
    try:
        if waiting_for == 'product_input':
            await process_product_input(update, context, user, text)
        elif waiting_for == 'coupon_code':
            await process_coupon_code(update, context, user, text)
        elif waiting_for == 'new_ticket':
            await process_new_ticket(update, context, user, text)
        elif waiting_for == 'ticket_reply':
            await process_ticket_reply(update, context, user, text)
        
        # Admin handlers
        elif user_id in Config.ADMIN_IDS:
            if waiting_for == 'delivery_data':
                await process_admin_delivery(update, context, text)
            elif waiting_for == 'admin_balance_amount':
                await process_admin_balance(update, context, text)
            elif waiting_for == 'broadcast_message':
                await process_admin_broadcast(update, context, text)
            elif waiting_for == 'youtube_url':
                await process_youtube_ad(update, context, text)
            elif waiting_for == 'coupon_code_create':
                await process_coupon_create(update, context, text)
            elif waiting_for == 'giftcard_amount':
                await process_giftcard_create(update, context, text)
        
        # AI Support for general messages
        else:
            await process_ai_support(update, context, user, text)
            
    except Exception as e:
        logger.error(f"Message handler error: {e}", exc_info=True)
        context.user_data.pop('waiting_for', None)


async def process_product_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, text: str):
    """Process product input data"""
    pending = db.execute(
        "SELECT * FROM pending_inputs WHERE user_id = ?",
        (user['id'],),
        fetch_one=True
    )
    
    if not pending:
        context.user_data.pop('waiting_for', None)
        await update.message.reply_text(
            "❌ انتهت الجلسة، حاول مرة أخرى",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Check expiry
    if pending.get('expires_at'):
        expires = datetime.fromisoformat(pending['expires_at'])
        if datetime.now() > expires:
            db.execute("DELETE FROM pending_inputs WHERE user_id = ?", (user['id'],))
            context.user_data.pop('waiting_for', None)
            await update.message.reply_text(
                "⏰ انتهت صلاحية الجلسة، حاول مرة أخرى",
                reply_markup=Keyboards.main_menu(user['id'])
            )
            return
    
    product = ProductManager.get(pending['item_key'])
    if not product:
        db.execute("DELETE FROM pending_inputs WHERE user_id = ?", (user['id'],))
        context.user_data.pop('waiting_for', None)
        await update.message.reply_text(
            "❌ المنتج غير متوفر",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    required_fields = json.loads(product['required_fields']) if product['required_fields'] else []
    collected_data = json.loads(pending['collected_data']) if pending['collected_data'] else {}
    current_step = pending['current_step']
    current_field = required_fields[current_step]
    
    # Validate input
    is_valid, error_msg = validate_player_id(text, current_field)
    if not is_valid:
        await update.message.reply_text(
            f"❌ *{error_msg}*\n\nأدخل معرف صحيح:",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    collected_data[current_field] = text
    next_step = current_step + 1
    
    if next_step < len(required_fields):
        # More fields to collect
        db.execute(
            """UPDATE pending_inputs SET
               current_step = ?, collected_data = ?
               WHERE user_id = ?""",
            (next_step, json.dumps(collected_data, ensure_ascii=False), user['id'])
        )
        
        field_labels = {
            'player_id': '🎮 Player ID',
            'pubg_id': '🔫 PUBG ID',
            'ml_id': '⚔️ ML ID',
            'zone_id': '🌍 Zone ID'
        }
        
        next_field = required_fields[next_step]
        
        await update.message.reply_text(
            f"✅ تم!\n\nأدخل {field_labels.get(next_field, next_field)}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ إلغاء', callback_data='cancel_purchase')]
            ])
        )
    else:
        # All fields collected, complete purchase
        db.execute("DELETE FROM pending_inputs WHERE user_id = ?", (user['id'],))
        context.user_data.pop('waiting_for', None)
        
        # Refresh user data
        user = UserManager.get(user['id'])
        
        if user['balance'] < product['price']:
            await update.message.reply_text(
                f"❌ رصيدك غير كافٍ!\n💰 {user['balance']:.0f}ج\n💸 السعر: {product['price']:.0f}ج",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')],
                    [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
                ])
            )
            return
        
        # Complete purchase
        success, result, order_id = OrderManager.create(user['id'], product, collected_data)
        
        if not success:
            await update.message.reply_text(
                f"❌ {result}",
                reply_markup=Keyboards.main_menu(user['id'])
            )
            return
        
        user = UserManager.get(user['id'])
        order = OrderManager.get(order_id)
        
        # Notify admins
        input_text = '\n'.join([f"• {k}: `{v}`" for k, v in collected_data.items()])
        
        admin_msg = f"""🛒 *طلب جديد!*
━━━━━━━━━━━━━━━━━━━━━

🆔 `{order_id}`
👤 `{user['id']}` @{user.get('username', 'N/A')}

🛍️ {product['name']}
💰 {order['total_price']:.0f}ج

📋 *البيانات:*
{input_text}"""

        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    admin_msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=Keyboards.admin_order_actions(order_id)
                )
            except:
                pass
        
        await update.message.reply_text(
            f"""✅ *تم تقديم الطلب بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

🆔 `{order_id}`
🛍️ {product['name']}
💰 {order['total_price']:.0f}ج
💎 كاش باك: +{order['cashback_amount']:.0f}ج

💳 رصيدك: *{user['balance']:.0f}ج*

⏳ سيتم التنفيذ قريباً!""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )


async def process_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, text: str):
    """Process coupon code"""
    context.user_data.pop('waiting_for', None)
    
    code = text.upper().strip()
    
    coupon = db.execute(
        "SELECT * FROM coupons WHERE code = ? AND is_active = 1",
        (code,),
        fetch_one=True
    )
    
    if not coupon:
        await update.message.reply_text(
            "❌ *كود غير صالح!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Check expiry
    if coupon.get('expires_at'):
        expires = datetime.fromisoformat(coupon['expires_at'])
        if datetime.now() > expires:
            await update.message.reply_text(
                "❌ *الكود منتهي الصلاحية!*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboards.main_menu(user['id'])
            )
            return
    
    # Check usage limit
    if coupon['max_usage'] and coupon['usage_count'] >= coupon['max_usage']:
        await update.message.reply_text(
            "❌ *الكود وصل للحد الأقصى!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Check per-user usage
    user_usage = db.execute(
        "SELECT COUNT(*) as c FROM coupon_usage WHERE coupon_code = ? AND user_id = ?",
        (code, user['id']),
        fetch_one=True
    )['c']
    
    if user_usage >= (coupon.get('max_per_user') or 1):
        await update.message.reply_text(
            "❌ *لقد استخدمت هذا الكود من قبل!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Calculate bonus
    if coupon['type'] == 'percent':
        bonus = min(user['balance'] * coupon['value'] / 100, coupon.get('max_discount') or 100)
    else:
        bonus = coupon['value']
    
    # Add balance
    new_balance = UserManager.update_balance(
        user['id'],
        bonus,
        'coupon',
        code,
        f"كوبون {code}"
    )
    
    # Update coupon usage
    db.execute(
        "UPDATE coupons SET usage_count = usage_count + 1 WHERE code = ?",
        (code,)
    )
    
    db.execute(
        """INSERT INTO coupon_usage (coupon_code, user_id, discount_amount, used_at)
           VALUES(?,?,?,?)""",
        (code, user['id'], bonus, datetime.now().isoformat())
    )
    
    await update.message.reply_text(
        f"""🎉 *تم تفعيل الكوبون بنجاح!*

💰 حصلت على: *+{bonus:.0f}ج*
💳 رصيدك الجديد: *{new_balance:.0f}ج*""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def process_new_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, text: str):
    """Process new ticket creation"""
    context.user_data.pop('waiting_for', None)
    
    now = datetime.now().isoformat()
    
    # Create ticket
    ticket_id = db.execute(
        """INSERT INTO tickets (user_id, subject, created_at, updated_at)
           VALUES(?,?,?,?)""",
        (user['id'], text[:50], now, now)
    )
    
    # Add message
    db.execute(
        """INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, message, created_at)
           VALUES(?,?,?,?,?)""",
        (ticket_id, 'user', user['id'], text, now)
    )
    
    # Try AI response first
    should_ai, reason = AIService.should_ai_respond(text)
    
    if should_ai and db.get_config('ai_support_enabled', True):
        ai_response, should_escalate, confidence = AIService.get_support_response(
            text,
            user
        )
        
        if not should_escalate and confidence >= 0.7:
            # Add AI response
            db.execute(
                """INSERT INTO ticket_messages
                   (ticket_id, sender_type, sender_id, message, ai_generated, ai_confidence, created_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (ticket_id, 'admin', 0, ai_response, 1, confidence, now)
            )
            
            await update.message.reply_text(
                f"""✅ *تم فتح تذكرة #{ticket_id}*

━━━━━━━━━━━━━━━━━━━━━

🤖 *رد الدعم الذكي:*
{ai_response}

━━━━━━━━━━━━━━━━━━━━━

💡 هل هذا الرد مفيد؟ إذا لم يحل مشكلتك، سيتواصل معك فريق الدعم.""",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboards.main_menu(user['id'])
            )
            
            # Still notify admins but mark as AI handled
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"""🤖 *تذكرة جديدة - تم الرد بالـ AI*

#{ticket_id} | `{user['id']}` @{user.get('username', 'N/A')}

📝 {text[:100]}

🤖 الرد: {ai_response[:100]}...
🎯 ثقة: {confidence:.0%}""",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
            
            return
    
    # Notify admins for manual handling
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"""🎫 *تذكرة جديدة #{ticket_id}*
━━━━━━━━━━━━━━━━━━━━━

👤 `{user['id']}` @{user.get('username', 'N/A')}

📝 {text[:300]}""",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('💬 رد', callback_data=f"admin_reply_ticket_{ticket_id}")]
                ])
            )
        except:
            pass
    
    await update.message.reply_text(
        f"""✅ *تم فتح تذكرة #{ticket_id}*

سنرد عليك في أقرب وقت ممكن.
شكراً لتواصلك معنا! 🙏""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def process_ticket_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, text: str):
    """Process ticket reply"""
    ticket_id = context.user_data.pop('ticket_id', None)
    context.user_data.pop('waiting_for', None)
    
    if not ticket_id:
        await update.message.reply_text(
            "❌ خطأ",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    now = datetime.now().isoformat()
    
    db.execute(
        """INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, message, created_at)
           VALUES(?,?,?,?,?)""",
        (ticket_id, 'user', user['id'], text, now)
    )
    
    db.execute(
        "UPDATE tickets SET updated_at = ? WHERE id = ?",
        (now, ticket_id)
    )
    
    # Notify admins
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"""💬 *رد جديد على تذكرة #{ticket_id}*

👤 `{user['id']}` @{user.get('username', 'N/A')}

📝 {text[:200]}""",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('💬 رد', callback_data=f"admin_reply_ticket_{ticket_id}")]
                ])
            )
        except:
            pass
    
    await update.message.reply_text(
        "✅ تم إرسال ردك",
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def process_ai_support(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict, text: str):
    """Process general message with AI support"""
    if not db.get_config('ai_support_enabled', True):
        return
    
    # Get AI response
    ai_response, should_escalate, confidence = AIService.get_support_response(text, user)
    
    if confidence >= 0.6 and not should_escalate:
        await update.message.reply_text(
            f"""🤖 *مساعد XLERO:*

{ai_response}

━━━━━━━━━━━━━━━━━━━━━

💡 للمزيد من المساعدة، افتح تذكرة دعم.""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
    else:
        # Low confidence or needs escalation
        await update.message.reply_text(
            "💬 سيتواصل معك فريق الدعم قريباً.\n\nلفتح تذكرة رسمية، اضغط على 🆘 الدعم",
            reply_markup=Keyboards.main_menu(user['id'])
        )


async def process_admin_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process admin delivery data"""
    order_id = context.user_data.pop('admin_execute_order', None)
    context.user_data.pop('waiting_for', None)
    
    if not order_id:
        await update.message.reply_text(
            "❌ خطأ",
            reply_markup=Keyboards.admin_panel()
        )
        return
    
    success, message = OrderManager.complete_order(
        order_id,
        text,
        update.effective_user.id
    )
    
    if not success:
        await update.message.reply_text(
            f"❌ {message}",
            reply_markup=Keyboards.admin_panel()
        )
        return
    
    order = OrderManager.get(order_id)
    
    # Notify user
    try:
        await context.bot.send_message(
            order['user_id'],
            f"""✅ *تم تنفيذ طلبك!*
━━━━━━━━━━━━━━━━━━━━━

🆔 `{order_id}`
🛍️ {order['product_name']}

━━━━━━━━━━━━━━━━━━━━━

📬 *بيانات التسليم:*
{text}

━━━━━━━━━━━━━━━━━━━━━

⚠️ احتفظ بهذه البيانات!
🙏 شكراً لثقتك بنا.""",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await update.message.reply_text(
        f"✅ تم تنفيذ الطلب {order_id}",
        reply_markup=Keyboards.admin_panel()
    )


async def process_admin_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process admin balance adjustment"""
    target_user = context.user_data.pop('balance_target_user', None)
    action = context.user_data.pop('balance_action', None)
    context.user_data.pop('waiting_for', None)
    
    if not target_user:
        await update.message.reply_text("❌ خطأ", reply_markup=Keyboards.admin_panel())
        return
    
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError()
        
        if action == 'sub':
            amount = -amount
        
        new_balance = UserManager.update_balance(
            target_user,
            amount,
            'admin_adjustment',
            f"ADM_{update.effective_user.id}",
            f"{'إضافة' if amount > 0 else 'خصم'} بواسطة الإدارة"
        )
        
        # Notify user
        try:
            action_text = 'إضافة' if amount > 0 else 'خصم'
            await context.bot.send_message(
                target_user,
                f"""💰 *تعديل الرصيد*

تم {action_text} *{abs(amount):.0f}ج* {'إلى' if amount > 0 else 'من'} رصيدك.
رصيدك الجديد: *{new_balance:.0f}ج*""",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
        
        await update.message.reply_text(
            f"✅ تم تعديل رصيد المستخدم {target_user}\nالرصيد الجديد: {new_balance:.0f}ج",
            reply_markup=Keyboards.admin_panel()
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ غير صحيح",
            reply_markup=Keyboards.admin_panel()
        )


async def process_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process admin broadcast"""
    context.user_data.pop('waiting_for', None)
    
    users = db.execute(
        "SELECT id FROM users WHERE banned = 0",
        fetch_all=True
    )
    
    status_msg = await update.message.reply_text(
        f"📨 جاري الإرسال لـ {len(users)} مستخدم..."
    )
    
    success = 0
    failed = 0
    
    for i, u in enumerate(users):
        try:
            await context.bot.send_message(
                u['id'],
                f"📢 *إعلان*\n━━━━━━━━━━━━━━━━━━━━━\n\n{text}",
                parse_mode=ParseMode.MARKDOWN
            )
            success += 1
        except:
            failed += 1
        
        if (i + 1) % 30 == 0:
            try:
                await status_msg.edit_text(f"📨 {i + 1}/{len(users)}...")
            except:
                pass
        
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(f"✅ تم الإرسال!\n\nنجح: {success}\nفشل: {failed}")


async def process_youtube_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process YouTube ad creation"""
    context.user_data.pop('waiting_for', None)
    
    # Validate YouTube URL
    youtube_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
    
    if not re.match(youtube_pattern, text):
        await update.message.reply_text(
            "❌ رابط يوتيوب غير صالح",
            reply_markup=Keyboards.admin_panel()
        )
        return
    
    # Save and post
    now = datetime.now().isoformat()
    
    db.execute(
        """INSERT INTO announcements
           (title, content, content_type, youtube_url, is_active, created_by, created_at)
           VALUES(?,?,?,?,?,?,?)""",
        ('إعلان فيديو', text, 'youtube', text, 1, update.effective_user.id, now)
    )
    
    # Post to channel
    try:
        await context.bot.send_message(
            Config.GROUP_ID,
            f"""🎬 *شاهد الآن!*
━━━━━━━━━━━━━━━━━━━━━

🔗 {text}

━━━━━━━━━━━━━━━━━━━━━

🔥 *XLERO SHOP* - أفضل متجر شحن ألعاب!""",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await update.message.reply_text(
            "✅ تم نشر إعلان اليوتيوب!",
            reply_markup=Keyboards.admin_panel()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ فشل النشر: {e}",
            reply_markup=Keyboards.admin_panel()
        )


async def process_coupon_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process coupon creation - step 1"""
    code = text.upper().strip()
    
    # Check if exists
    existing = db.execute(
        "SELECT 1 FROM coupons WHERE code = ?",
        (code,),
        fetch_one=True
    )
    
    if existing:
        await update.message.reply_text(
            "❌ هذا الكود موجود بالفعل!",
            reply_markup=Keyboards.admin_panel()
        )
        return
    
    context.user_data['coupon_code'] = code
    context.user_data['waiting_for'] = 'coupon_value'
    
    await update.message.reply_text(
        f"""✅ كود: `{code}`

الآن أدخل قيمة الكوبون:
(رقم فقط - مثال: 10 للخصم 10ج)""",
        parse_mode=ParseMode.MARKDOWN
    )


async def process_giftcard_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process gift card creation"""
    context.user_data.pop('waiting_for', None)
    
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError()
        
        # Generate unique code
        code = 'GC' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        now = datetime.now().isoformat()
        
        db.execute(
            """INSERT INTO gift_cards
               (code, amount, balance, created_by, created_at)
               VALUES(?,?,?,?,?)""",
            (code, amount, amount, update.effective_user.id, now)
        )
        
        await update.message.reply_text(
            f"""🎁 *تم إنشاء بطاقة الهدية!*
━━━━━━━━━━━━━━━━━━━━━

💳 الكود: `{code}`
💰 القيمة: {amount:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

يمكن للمستخدم استخدامه ككوبون.""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.admin_panel()
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ قيمة غير صحيحة",
            reply_markup=Keyboards.admin_panel()
        )


# ══════════════════════════════════════════════════════════════════
# PHOTO HANDLER
# ══════════════════════════════════════════════════════════════════

@log_action("photo")
@maintenance_check
@rate_limited
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages"""
    if not update.message or not update.message.photo:
        return
    
    user_id = update.effective_user.id
    
    is_banned, _ = UserManager.is_banned(user_id)
    if is_banned:
        return
    
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for != 'deposit_image':
        await update.message.reply_text(
            "💳 لإيداع رصيد، اضغط على 'شحن رصيد' من القائمة الرئيسية أولاً",
            reply_markup=Keyboards.main_menu(user_id)
        )
        return
    
    context.user_data.pop('waiting_for', None)
    
    user = UserManager.create_or_update(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    processing_msg = await update.message.reply_text(
        "🔍 *جاري تحليل الصورة...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Download image
        photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
        image_bytes = await photo_file.download_as_bytearray()
        image_bytes = bytes(image_bytes)
        
        # Process payment
        result = await PaymentProcessor.process_payment_image(
            user,
            image_bytes,
            context
        )
        
        await processing_msg.edit_text(
            result['message'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user_id)
        )
        
    except Exception as e:
        logger.error(f"Photo processing error: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ حدث خطأ أثناء معالجة الصورة، حاول مرة أخرى",
            reply_markup=Keyboards.main_menu(user_id)
        )


# ══════════════════════════════════════════════════════════════════
# PROMOTIONAL SYSTEM
# ══════════════════════════════════════════════════════════════════

async def post_promotional_content(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Post AI-generated promotional content"""
    try:
        content = AIService.generate_promotional_post()
        bot_link = f"https://t.me/{state.bot_username}?start=promo"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton('🚀 افتح المتجر الآن!', url=bot_link)]
        ])
        
        # Delete old pinned promo
        last_promo = db.execute(
            "SELECT message_id, chat_id FROM promo_posts ORDER BY id DESC LIMIT 1",
            fetch_one=True
        )
        
        if last_promo:
            try:
                await context.bot.unpin_chat_message(
                    chat_id=last_promo['chat_id'],
                    message_id=last_promo['message_id']
                )
                await context.bot.delete_message(
                    chat_id=last_promo['chat_id'],
                    message_id=last_promo['message_id']
                )
            except:
                pass
        
        # Post new promo
        message = await context.bot.send_message(
            chat_id=Config.GROUP_ID,
            text=content,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=buttons
        )
        
        # Pin message
        try:
            await context.bot.pin_chat_message(
                chat_id=Config.GROUP_ID,
                message_id=message.message_id,
                disable_notification=True
            )
        except:
            pass
        
        # Save to database
        db.execute(
            """INSERT INTO promo_posts
               (message_id, chat_id, content, post_type, ai_generated, created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                message.message_id,
                Config.GROUP_ID,
                content[:500],
                'ai_promo',
                1,
                datetime.now().isoformat()
            )
        )
        
        logger.info("✅ Promotional post published successfully")
        return True
        
    except Exception as e:
        logger.error(f"Promo posting error: {e}")
        return False


async def post_fake_activity(context: ContextTypes.DEFAULT_TYPE):
    """Post fake deposit/referral activity"""
    try:
        post_type = random.choice(['deposit', 'referral'])
        
        if post_type == 'deposit':
            content = AIService.generate_fake_deposit_post()
        else:
            content = AIService.generate_fake_referral_post()
        
        await context.bot.send_message(
            chat_id=Config.GROUP_ID,
            text=content,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Fake {post_type} post published")
        
    except Exception as e:
        logger.error(f"Fake activity post error: {e}")


# ══════════════════════════════════════════════════════════════════
# SCHEDULERS
# ══════════════════════════════════════════════════════════════════

async def promo_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Schedule promotional posts"""
    await asyncio.sleep(60)  # Wait 1 minute before starting
    
    while True:
        try:
            await post_promotional_content(context)
        except Exception as e:
            logger.error(f"Promo scheduler error: {e}")
        
        await asyncio.sleep(Config.PROMO_INTERVAL_SECONDS)


async def fake_activity_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Schedule fake activity posts"""
    await asyncio.sleep(120)  # Wait 2 minutes before starting
    
    while True:
        try:
            await post_fake_activity(context)
        except Exception as e:
            logger.error(f"Fake activity scheduler error: {e}")
        
        # Random interval between 20-40 minutes
        wait_time = random.randint(1200, 2400)
        await asyncio.sleep(wait_time)


# ══════════════════════════════════════════════════════════════════
# ERROR HANDLER
# ══════════════════════════════════════════════════════════════════

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    
    try:
        if update:
            user_id = update.effective_user.id if update.effective_user else None
            
            if update.callback_query:
                await update.callback_query.answer("❌ حدث خطأ", show_alert=True)
            elif update.message:
                await update.message.reply_text(
                    "❌ حدث خطأ، حاول مرة أخرى",
                    reply_markup=Keyboards.main_menu(user_id) if user_id else None
                )
    except:
        pass


# ══════════════════════════════════════════════════════════════════
# INITIALIZATION
# ══════════════════════════════════════════════════════════════════

async def post_init(application: Application):
    """Post-initialization setup"""
    global state
    
    bot_info = await application.bot.get_me()
    state.bot_username = bot_info.username
    state.bot_id = bot_info.id
    
    logger.info(f"🤖 Bot started: @{state.bot_username}")
    
    # Set commands
    commands = [
        BotCommand('start', 'بدء البوت'),
        BotCommand('help', 'المساعدة'),
    ]
    await application.bot.set_my_commands(commands)
    
    # Start schedulers
    asyncio.create_task(promo_scheduler(application))
    asyncio.create_task(fake_activity_scheduler(application))
    
    logger.info("✅ All systems initialized")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    print("═" * 60)
    print("🔥 XLERO SHOP V7 ULTIMATE 🔥")
    print("═" * 60)
    
    # Initialize database
    db.initialize()
    
    # Build application
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('help', cmd_help))
    application.add_handler(CommandHandler('admin', cmd_admin))
    
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    application.add_error_handler(error_handler)
    
    # Print stats
    products = db.execute(
        "SELECT COUNT(*) as c FROM products WHERE is_active = 1",
        fetch_one=True
    )['c']
    
    users = db.execute("SELECT COUNT(*) as c FROM users", fetch_one=True)['c']
    
    orders = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE status IN ('done', 'completed')",
        fetch_one=True
    )['c']
    
    print(f"📦 Products: {products}")
    print(f"👥 Users: {users}")
    print(f"📋 Orders: {orders}")
    print(f"📢 Promo Interval: {Config.PROMO_INTERVAL_SECONDS // 60} min")
    print("═" * 60)
    print("🚀 Bot is running...")
    print("═" * 60)
    
    # Run
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == '__main__':
    main()
        