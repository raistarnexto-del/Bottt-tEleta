#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║                    XLERO SHOP V6 ULTIMATE                    ║
║                  نظام متجر شحن ألعاب متكامل                    ║
║                     Developed with ❤️                        ║
╚══════════════════════════════════════════════════════════════╝
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
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, List, Tuple

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto,
    BotCommand
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from telegram.constants import ParseMode, ChatAction

# ══════════════════════════════════════════════════════════════
#                         LOGGING SETUP
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('xlero_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('XLERO')

# ══════════════════════════════════════════════════════════════
#                       CONFIGURATION
# ══════════════════════════════════════════════════════════════
class Config:
    """Bot Configuration"""
    # Telegram Bot
    BOT_TOKEN = '8359845352:AAEw1whUiOmnOBzUvOiIlUSdu0l6Opoc07g'
    
    # AI API
    HF_API_TOKEN = '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'
    HF_API_URL = 'https://router.huggingface.co/v1/chat/completions'
    AI_MODEL = 'google/gemma-3-27b-it'
    
    # Admin & Channels
    ADMIN_IDS = [7384284034]
    CHANNEL_ID = '-1002904714010'
    GROUP_ID = '-1002904714010'
    
    # Payment
    VODAFONE_NUMBER = '01034573708'
    USDT_WALLET = '0x8E00A980274Cfb22798290586d97F7D185E3092D'
    BSCSCAN_API_KEY = 'D8JX395ZQ8D95NIY15H5NYUNVD3KPVVDWN'
    USDT_CONTRACT = '0x55d398326f99059fF775485246999027B3197955'
    
    # Settings
    MANUAL_VERIFY_THRESHOLD = 30
    USDT_TO_EGP_RATE = 50
    PROMO_INTERVAL_SECONDS = 900
    MIN_DEPOSIT = 25
    MAX_DEPOSIT = 50000
    DEPOSIT_FEE_PERCENT = 2
    DEPOSIT_FEE_MAX = 5
    WELCOME_BONUS = 5
    REFERRAL_BONUS = 4
    DAILY_BASE_REWARD = 1
    MAX_DAILY_STREAK_BONUS = 3
    
    # Database
    DATABASE_PATH = 'xlero_database.db'

# ══════════════════════════════════════════════════════════════
#                      GLOBAL VARIABLES
# ══════════════════════════════════════════════════════════════
class BotState:
    """Global bot state"""
    bot_username: str = None
    fake_users_count: int = 17399
    is_maintenance: bool = False
    
state = BotState()
db_lock = threading.Lock()

# ══════════════════════════════════════════════════════════════
#                       DATABASE LAYER
# ══════════════════════════════════════════════════════════════
class Database:
    """Database operations handler"""
    
    @staticmethod
    def execute(query: str, params: tuple = (), fetch_one: bool = False, 
                fetch_all: bool = False) -> Any:
        """Execute database query with thread safety"""
        with db_lock:
            conn = None
            try:
                conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
                conn.row_factory = sqlite3.Row
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
                logger.error(f"Database error: {e}")
                if conn:
                    conn.rollback()
                return None
            finally:
                if conn:
                    conn.close()
    
    @staticmethod
    def initialize():
        """Initialize all database tables"""
        tables = [
            # Users table
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0,
                points INTEGER DEFAULT 0,
                spent REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                total_deposits REAL DEFAULT 0,
                referrer_id INTEGER,
                referral_earnings REAL DEFAULT 0,
                level INTEGER DEFAULT 1,
                trust_score INTEGER DEFAULT 50,
                vip_status INTEGER DEFAULT 0,
                cashback_total REAL DEFAULT 0,
                banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                ban_until TEXT,
                warnings INTEGER DEFAULT 0,
                join_date TEXT,
                last_active TEXT,
                language TEXT DEFAULT 'ar',
                notifications_enabled INTEGER DEFAULT 1
            )''',
            
            # Transactions table
            '''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                reference TEXT,
                description TEXT,
                fee REAL DEFAULT 0,
                balance_before REAL,
                balance_after REAL,
                status TEXT DEFAULT 'completed',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Deposits table
            '''CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                amount_after_fee REAL,
                payment_method TEXT NOT NULL,
                image_hash TEXT,
                txid TEXT,
                reference_number TEXT,
                status TEXT DEFAULT 'pending',
                ai_analysis TEXT,
                ai_confidence REAL,
                risk_score INTEGER DEFAULT 0,
                admin_notes TEXT,
                reviewed_by INTEGER,
                reviewed_at TEXT,
                rejection_reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Orders table
            '''CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                product_key TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                discount_code TEXT,
                cashback_amount REAL DEFAULT 0,
                input_data TEXT,
                delivery_data TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                notes TEXT,
                admin_notes TEXT,
                processed_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                completed_at TEXT,
                cancelled_at TEXT,
                cancel_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Products table
            '''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subcategory TEXT,
                item_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_en TEXT,
                description TEXT,
                price REAL NOT NULL,
                original_price REAL,
                cost REAL DEFAULT 0,
                profit_margin REAL,
                required_fields TEXT,
                delivery_time TEXT DEFAULT 'فوري',
                stock INTEGER DEFAULT -1,
                min_quantity INTEGER DEFAULT 1,
                max_quantity INTEGER DEFAULT 10,
                cashback_percent REAL DEFAULT 3,
                is_featured INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                sold_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 5.0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )''',
            
            # Coupons table
            '''CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_purchase REAL DEFAULT 0,
                max_discount REAL,
                usage_count INTEGER DEFAULT 0,
                max_usage INTEGER,
                max_per_user INTEGER DEFAULT 1,
                applicable_categories TEXT,
                applicable_products TEXT,
                is_active INTEGER DEFAULT 1,
                starts_at TEXT,
                expires_at TEXT,
                created_by INTEGER,
                created_at TEXT
            )''',
            
            # Coupon usage table
            '''CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_code TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                order_id TEXT,
                discount_amount REAL,
                used_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Support tickets table
            '''CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT,
                category TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'open',
                assigned_to INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                closed_at TEXT,
                closed_by INTEGER,
                satisfaction_rating INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Ticket messages table
            '''CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id INTEGER,
                message TEXT NOT NULL,
                attachment_type TEXT,
                attachment_id TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )''',
            
            # Daily rewards table
            '''CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id INTEGER PRIMARY KEY,
                last_claim_date TEXT,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                total_claimed REAL DEFAULT 0,
                total_claims INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Referrals table
            '''CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                bonus_amount REAL,
                order_bonus REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                activated_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users(id),
                FOREIGN KEY (referred_id) REFERENCES users(id)
            )''',
            
            # Image hashes table (fraud prevention)
            '''CREATE TABLE IF NOT EXISTS image_hashes (
                hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type TEXT,
                amount REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Used TXIDs table (fraud prevention)
            '''CREATE TABLE IF NOT EXISTS used_txids (
                txid TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL,
                verified INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Pending inputs table
            '''CREATE TABLE IF NOT EXISTS pending_inputs (
                user_id INTEGER PRIMARY KEY,
                action_type TEXT NOT NULL,
                item_key TEXT,
                current_step INTEGER DEFAULT 0,
                collected_data TEXT DEFAULT '{}',
                coupon_code TEXT,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Notifications table
            '''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                type TEXT DEFAULT 'info',
                action_url TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Promo posts table
            '''CREATE TABLE IF NOT EXISTS promo_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                chat_id TEXT,
                content TEXT,
                type TEXT,
                engagement_clicks INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )''',
            
            # Activity logs table
            '''CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_hash TEXT,
                created_at TEXT NOT NULL
            )''',
            
            # Security logs table
            '''CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                details TEXT,
                resolved INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )''',
            
            # Fraud records table
            '''CREATE TABLE IF NOT EXISTS fraud_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                severity INTEGER DEFAULT 1,
                description TEXT,
                evidence TEXT,
                action_taken TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Flash sales table
            '''CREATE TABLE IF NOT EXISTS flash_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_key TEXT NOT NULL,
                discount_percent REAL NOT NULL,
                original_price REAL,
                sale_price REAL,
                max_orders INTEGER,
                current_orders INTEGER DEFAULT 0,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT
            )''',
            
            # Gift cards table
            '''CREATE TABLE IF NOT EXISTS gift_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                balance REAL,
                created_by INTEGER,
                used_by INTEGER,
                is_active INTEGER DEFAULT 1,
                expires_at TEXT,
                created_at TEXT,
                used_at TEXT
            )''',
            
            # User achievements table
            '''CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                reward_claimed INTEGER DEFAULT 0,
                completed_at TEXT,
                UNIQUE(user_id, achievement_key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''',
            
            # Bot configuration table
            '''CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_by INTEGER,
                updated_at TEXT
            )''',
            
            # User levels table
            '''CREATE TABLE IF NOT EXISTS user_levels (
                level INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT,
                badge TEXT,
                min_spent REAL NOT NULL,
                cashback_bonus REAL DEFAULT 0,
                daily_bonus REAL DEFAULT 0,
                priority_support INTEGER DEFAULT 0,
                exclusive_offers INTEGER DEFAULT 0
            )'''
        ]
        
        # Create all tables
        for table_sql in tables:
            Database.execute(table_sql)
        
        # Create indexes for better performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned)',
            'CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id)',
            'CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)',
            'CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status)',
            'CREATE INDEX IF NOT EXISTS idx_deposits_user ON deposits(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)',
            'CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id)',
        ]
        
        for index_sql in indexes:
            Database.execute(index_sql)
        
        # Initialize default configurations
        Database._init_default_config()
        
        # Initialize user levels
        Database._init_user_levels()
        
        # Initialize products if empty
        if Database.execute('SELECT COUNT(*) as c FROM products', fetch_one=True)['c'] == 0:
            Database._init_products()
        
        logger.info("✅ Database initialized successfully")
    
    @staticmethod
    def _init_default_config():
        """Initialize default bot configuration"""
        defaults = {
            'deposit_fee_percent': (Config.DEPOSIT_FEE_PERCENT, 'نسبة عمولة الإيداع'),
            'deposit_fee_max': (Config.DEPOSIT_FEE_MAX, 'الحد الأقصى لعمولة الإيداع'),
            'welcome_bonus': (Config.WELCOME_BONUS, 'مكافأة الترحيب للمستخدمين الجدد'),
            'referral_bonus': (Config.REFERRAL_BONUS, 'مكافأة الإحالة'),
            'referral_order_bonus': (5, 'مكافأة أول طلب للمُحال'),
            'daily_base_reward': (Config.DAILY_BASE_REWARD, 'المكافأة اليومية الأساسية'),
            'maintenance_mode': (False, 'وضع الصيانة'),
            'min_withdrawal': (50, 'الحد الأدنى للسحب'),
            'auto_approve_threshold': (Config.MANUAL_VERIFY_THRESHOLD, 'حد الموافقة التلقائية'),
        }
        
        for key, (value, desc) in defaults.items():
            existing = Database.execute('SELECT 1 FROM bot_config WHERE key=?', (key,), fetch_one=True)
            if not existing:
                Database.execute(
                    'INSERT INTO bot_config(key, value, description, updated_at) VALUES(?,?,?,?)',
                    (key, json.dumps(value), desc, datetime.now().isoformat())
                )
    
    @staticmethod
    def _init_user_levels():
        """Initialize user level system"""
        levels = [
            (1, 'برونزي', 'Bronze', '🥉', 0, 0, 0, 0, 0),
            (2, 'فضي', 'Silver', '🥈', 500, 0.5, 1, 0, 0),
            (3, 'ذهبي', 'Gold', '🥇', 2000, 1.0, 2, 1, 0),
            (4, 'بلاتيني', 'Platinum', '💎', 5000, 1.5, 3, 1, 1),
            (5, 'أسطوري', 'Legendary', '👑', 15000, 2.0, 5, 1, 1),
            (6, 'إمبراطوري', 'Imperial', '🏆', 50000, 3.0, 10, 1, 1),
        ]
        
        for level_data in levels:
            Database.execute(
                '''INSERT OR IGNORE INTO user_levels
                   (level, name, name_en, badge, min_spent, cashback_bonus, daily_bonus, priority_support, exclusive_offers)
                   VALUES(?,?,?,?,?,?,?,?,?)''',
                level_data
            )
    
    @staticmethod
    def _init_products():
        """Initialize default products"""
        products = [
            # Free Fire
            ('freefire', 'diamonds', 'ff_100', '💎 100 جوهرة', '100 Diamonds', 'شحن 100 جوهرة فري فاير', 53, 60, 45, '["player_id"]', 3),
            ('freefire', 'diamonds', 'ff_210', '💎 210 جوهرة', '210 Diamonds', 'شحن 210 جوهرة فري فاير', 106, 120, 90, '["player_id"]', 3),
            ('freefire', 'diamonds', 'ff_530', '💎 530 جوهرة', '530 Diamonds', 'شحن 530 جوهرة فري فاير', 265, 300, 225, '["player_id"]', 3),
            ('freefire', 'diamonds', 'ff_1060', '💎 1060 جوهرة', '1060 Diamonds', 'شحن 1060 جوهرة فري فاير', 530, 600, 450, '["player_id"]', 4),
            ('freefire', 'diamonds', 'ff_2180', '💎 2180 جوهرة', '2180 Diamonds', 'شحن 2180 جوهرة فري فاير', 1060, 1200, 900, '["player_id"]', 4),
            ('freefire', 'diamonds', 'ff_5600', '💎 5600 جوهرة', '5600 Diamonds', 'شحن 5600 جوهرة فري فاير', 2650, 3000, 2250, '["player_id"]', 5),
            
            # PUBG Mobile
            ('pubg', 'uc', 'pubg_60', '🔫 60 UC', '60 UC', 'شحن 60 UC ببجي موبايل', 49, 55, 42, '["pubg_id"]', 3),
            ('pubg', 'uc', 'pubg_325', '🔫 325 UC', '325 UC', 'شحن 325 UC ببجي موبايل', 249, 280, 210, '["pubg_id"]', 3),
            ('pubg', 'uc', 'pubg_660', '🔫 660 UC', '660 UC', 'شحن 660 UC ببجي موبايل', 495, 560, 420, '["pubg_id"]', 4),
            ('pubg', 'uc', 'pubg_1800', '🔫 1800 UC', '1800 UC', 'شحن 1800 UC ببجي موبايل', 1320, 1500, 1120, '["pubg_id"]', 4),
            ('pubg', 'uc', 'pubg_8100', '🔫 8100 UC', '8100 UC', 'شحن 8100 UC ببجي موبايل', 5940, 6750, 5040, '["pubg_id"]', 5),
            
            # Mobile Legends
            ('mlbb', 'diamonds', 'ml_86', '💠 86 ماسة', '86 Diamonds', 'شحن 86 ماسة موبايل ليجندز', 49, 55, 42, '["ml_id","zone_id"]', 2),
            ('mlbb', 'diamonds', 'ml_172', '💠 172 ماسة', '172 Diamonds', 'شحن 172 ماسة موبايل ليجندز', 98, 110, 84, '["ml_id","zone_id"]', 2),
            ('mlbb', 'diamonds', 'ml_257', '💠 257 ماسة', '257 Diamonds', 'شحن 257 ماسة موبايل ليجندز', 147, 165, 126, '["ml_id","zone_id"]', 3),
            ('mlbb', 'diamonds', 'ml_344', '💠 344 ماسة', '344 Diamonds', 'شحن 344 ماسة موبايل ليجندز', 196, 220, 168, '["ml_id","zone_id"]', 3),
            ('mlbb', 'diamonds', 'ml_706', '💠 706 ماسة', '706 Diamonds', 'شحن 706 ماسة موبايل ليجندز', 392, 440, 336, '["ml_id","zone_id"]', 4),
            ('mlbb', 'diamonds', 'ml_2195', '💠 2195 ماسة', '2195 Diamonds', 'شحن 2195 ماسة موبايل ليجندز', 1176, 1320, 1008, '["ml_id","zone_id"]', 5),
            
            # Steam Cards
            ('steam', 'cards', 'steam_5', '🎮 ستيم $5', 'Steam $5', 'بطاقة ستيم 5 دولار أمريكي', 280, 320, 250, None, 2),
            ('steam', 'cards', 'steam_10', '🎮 ستيم $10', 'Steam $10', 'بطاقة ستيم 10 دولار أمريكي', 560, 640, 500, None, 2),
            ('steam', 'cards', 'steam_20', '🎮 ستيم $20', 'Steam $20', 'بطاقة ستيم 20 دولار أمريكي', 1120, 1280, 1000, None, 3),
            ('steam', 'cards', 'steam_50', '🎮 ستيم $50', 'Steam $50', 'بطاقة ستيم 50 دولار أمريكي', 2800, 3200, 2500, None, 4),
            ('steam', 'cards', 'steam_100', '🎮 ستيم $100', 'Steam $100', 'بطاقة ستيم 100 دولار أمريكي', 5600, 6400, 5000, None, 5),
            
            # Google Play
            ('googleplay', 'cards', 'google_5', '📱 جوجل $5', 'Google Play $5', 'بطاقة جوجل بلاي 5 دولار', 290, 330, 260, None, 2),
            ('googleplay', 'cards', 'google_10', '📱 جوجل $10', 'Google Play $10', 'بطاقة جوجل بلاي 10 دولار', 580, 660, 520, None, 2),
            ('googleplay', 'cards', 'google_25', '📱 جوجل $25', 'Google Play $25', 'بطاقة جوجل بلاي 25 دولار', 1450, 1650, 1300, None, 3),
            ('googleplay', 'cards', 'google_50', '📱 جوجل $50', 'Google Play $50', 'بطاقة جوجل بلاي 50 دولار', 2900, 3300, 2600, None, 4),
            
            # iTunes
            ('itunes', 'cards', 'itunes_5', '🍎 آيتونز $5', 'iTunes $5', 'بطاقة آيتونز 5 دولار', 300, 340, 270, None, 2),
            ('itunes', 'cards', 'itunes_10', '🍎 آيتونز $10', 'iTunes $10', 'بطاقة آيتونز 10 دولار', 600, 680, 540, None, 2),
            ('itunes', 'cards', 'itunes_25', '🍎 آيتونز $25', 'iTunes $25', 'بطاقة آيتونز 25 دولار', 1500, 1700, 1350, None, 3),
            ('itunes', 'cards', 'itunes_50', '🍎 آيتونز $50', 'iTunes $50', 'بطاقة آيتونز 50 دولار', 3000, 3400, 2700, None, 4),
            
            # PlayStation
            ('playstation', 'cards', 'psn_10', '🎮 PSN $10', 'PlayStation $10', 'بطاقة بلايستيشن 10 دولار', 580, 660, 520, None, 2),
            ('playstation', 'cards', 'psn_25', '🎮 PSN $25', 'PlayStation $25', 'بطاقة بلايستيشن 25 دولار', 1450, 1650, 1300, None, 3),
            ('playstation', 'cards', 'psn_50', '🎮 PSN $50', 'PlayStation $50', 'بطاقة بلايستيشن 50 دولار', 2900, 3300, 2600, None, 4),
            
            # Xbox
            ('xbox', 'cards', 'xbox_10', '🎮 Xbox $10', 'Xbox $10', 'بطاقة إكس بوكس 10 دولار', 580, 660, 520, None, 2),
            ('xbox', 'cards', 'xbox_25', '🎮 Xbox $25', 'Xbox $25', 'بطاقة إكس بوكس 25 دولار', 1450, 1650, 1300, None, 3),
            ('xbox', 'cards', 'xbox_50', '🎮 Xbox $50', 'Xbox $50', 'بطاقة إكس بوكس 50 دولار', 2900, 3300, 2600, None, 4),
        ]
        
        now = datetime.now().isoformat()
        for p in products:
            Database.execute(
                '''INSERT OR IGNORE INTO products 
                   (category, subcategory, item_key, name, name_en, description, price, original_price, cost, required_fields, cashback_percent, created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                (*p, now)
            )
        
        logger.info(f"✅ Initialized {len(products)} products")

# ══════════════════════════════════════════════════════════════
#                         AI SERVICE
# ══════════════════════════════════════════════════════════════
class AIService:
    """AI-powered features"""
    
    @staticmethod
    def _call_api(messages: list, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """Make API call to HuggingFace"""
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
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                logger.error(f"AI API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"AI API exception: {e}")
            return None
    
    @staticmethod
    def _call_vision_api(prompt: str, image_base64: str, max_tokens: int = 300) -> Optional[str]:
        """Make vision API call"""
        try:
            headers = {
                'Authorization': f'Bearer {Config.HF_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            messages = [{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}}
                ]
            }]
            
            payload = {
                'model': Config.AI_MODEL,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': 0.1
            }
            
            response = requests.post(
                Config.HF_API_URL,
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            return None
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return None
    
    @staticmethod
    def generate_promotional_post() -> str:
        """Generate unique promotional content"""
        global state
        state.fake_users_count += random.randint(1, 5)
        users_count = state.fake_users_count
        
        themes = [
            "عرض خاص جداً", "صفقة العمر", "خصم ناري", "فرصة ذهبية",
            "عرض لن يتكرر", "تخفيضات مجنونة", "أسعار خيالية", "عرض حصري",
            "فلاش سيل", "عروض نهاية الأسبوع", "مفاجأة اليوم"
        ]
        
        styles = [
            "اسأل أسئلة تفاعلية", "اروِ قصة قصيرة مشوقة", "استخدم المقارنات",
            "ركز على المشاعر", "استخدم الأرقام والإحصائيات", "خاطب الجيمرز مباشرة"
        ]
        
        games = ["فري فاير", "ببجي موبايل", "موبايل ليجندز", "ستيم", "جوجل بلاي", "آيتونز"]
        
        prompt = f"""أنت خبير تسويق محترف ومبدع جداً. اكتب إعلان ترويجي مميز وفريد بالعربية لمتجر "XLERO SHOP" لشحن الألعاب.

📌 معلومات المتجر:
- الألعاب: {', '.join(random.sample(games, 4))}
- خصومات تصل لـ 25%
- تسليم فوري خلال دقائق
- دفع عبر: فودافون كاش، USDT
- عدد العملاء: أكثر من {users_count:,}
- ضمان 100%

📌 متطلبات الإعلان:
1. الموضوع الرئيسي: {random.choice(themes)}
2. الأسلوب: {random.choice(styles)}
3. استخدم إيموجي متنوعة وجذابة بكثرة
4. اجعل هناك إحساس بالعجلة والندرة
5. اختم بدعوة قوية للعمل
6. اجعله مختلف تماماً ومبتكر
7. الطول: 150-250 كلمة

اكتب إعلاناً إبداعياً الآن:"""

        result = AIService._call_api(
            [{'role': 'user', 'content': prompt}],
            max_tokens=500,
            temperature=0.95
        )
        
        if result and len(result) > 100:
            return result
        
        # Fallback templates
        templates = [
            f"""🔥🔥🔥 *XLERO SHOP* 🔥🔥🔥

⚡ هل أنت جاهز للعب؟ ⚡

💎 شحن فوري لجميع ألعابك المفضلة!
🎮 فري فاير • ببجي • موبايل ليجندز • ستيم

━━━━━━━━━━━━━━━━━━

🏆 لماذا نحن الأفضل؟

✅ أسعار أقل من السوق بـ 25%
✅ تسليم فوري خلال دقائق
✅ ضمان كامل 100%
✅ دعم فني 24/7
✅ طرق دفع متنوعة

━━━━━━━━━━━━━━━━━━

📱 فودافون كاش
💎 USDT

👥 انضم لأكثر من {users_count:,} عميل سعيد!

🚀 *ابدأ الآن!* 🚀""",

            f"""⭐ *عرض لا يُفوَّت!* ⭐

🎮 يا جيمرز! الفرصة اللي بتدوروا عليها وصلت!

💰 خصومات خرافية على كل الشحنات!
⚡ تسليم فوري مضمون!
🛡️ ضمان كامل!

━━━━━━━━━━━━━━━━━━

🔥 *المتاح الآن:*

💎 فري فاير - أرخص سعر
🔫 ببجي UC - تسليم فوري  
⚔️ موبايل ليجندز - ضمان
🎮 بطاقات ستيم - أصلية 100%
📱 جوجل بلاي - سريع
🍎 آيتونز - مضمون

━━━━━━━━━━━━━━━━━━

👥 +{users_count:,} عميل يثقون بنا!

🔥 *XLERO SHOP - الأفضل دائماً!* 🔥""",

            f"""💥 *مفاجأة XLERO!* 💥

هل تبحث عن أفضل أسعار الشحن؟ 🤔

🎯 وجدت المكان الصحيح!

*XLERO SHOP* يقدم لك:

💎 شحن جميع الألعاب
⚡ تسليم خلال دقائق
💰 أسعار تحطم المنافسة
🛡️ ضمان كامل

━━━━━━━━━━━━━━━━━━

🎮 *الألعاب المتاحة:*
• Free Fire 💎
• PUBG Mobile 🔫
• Mobile Legends ⚔️
• Steam 🎮
• Google Play 📱
• iTunes 🍎
• PlayStation 🎮
• Xbox 🎮

━━━━━━━━━━━━━━━━━━

📱 ادفع بسهولة:
• فودافون كاش
• USDT

👥 {users_count:,}+ عميل سعيد!

🚀 *اشحن الآن!* 🚀"""
        ]
        
        return random.choice(templates)
    
    @staticmethod
    def detect_payment_type(image_base64: str) -> str:
        """Detect payment type from image"""
        prompt = """حدد نوع الدفع في هذه الصورة. أجب بكلمة واحدة فقط:
- VODAFONE: إذا كانت إيصال فودافون كاش
- USDT: إذا كانت معاملة USDT/تيثر
- INSTAPAY: إذا كانت إنستا باي
- BANK: إذا كانت تحويل بنكي
- INVALID: إذا لم تكن صورة دفع

الإجابة:"""
        
        result = AIService._call_vision_api(prompt, image_base64, 10)
        
        if result:
            result = result.upper().strip()
            if 'VODAFONE' in result:
                return 'VODAFONE'
            elif 'USDT' in result:
                return 'USDT'
            elif 'INSTAPAY' in result:
                return 'INSTAPAY'
            elif 'BANK' in result:
                return 'BANK'
        
        return 'UNKNOWN'
    
    @staticmethod
    def analyze_vodafone_receipt(image_base64: str, expected_phone: str) -> Dict:
        """Analyze Vodafone Cash receipt"""
        prompt = f"""أنت خبير في تحليل إيصالات الدفع الإلكتروني. حلل هذه الصورة بدقة عالية.

المطلوب:
1. هل هذه صورة إيصال فودافون كاش حقيقي وصالح؟
2. ما هو المبلغ المحول؟ (رقم فقط بدون عملة)
3. هل الرقم المستلم هو {expected_phone} أو يحتوي عليه؟
4. هل الإيصال يبدو حديث؟

علامات إيصال فودافون كاش الصحيح:
- شعار Vodafone أو فودافون
- عبارة "تم التحويل بنجاح" أو "Transfer Successful"
- المبلغ واضح
- رقم المستلم ظاهر

أجب بـ JSON فقط بهذا الشكل:
{{"is_valid": true, "amount": 100, "phone_correct": true, "confidence": 0.95, "error": null}}

أو إذا غير صالح:
{{"is_valid": false, "amount": 0, "phone_correct": false, "confidence": 0.1, "error": "السبب"}}"""

        result = AIService._call_vision_api(prompt, image_base64, 200)
        
        if result:
            try:
                # Extract JSON
                json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return {
                        'valid': data.get('is_valid', False) and data.get('phone_correct', False),
                        'amount': float(data.get('amount', 0)),
                        'confidence': float(data.get('confidence', 0)),
                        'error': data.get('error'),
                        'raw_response': data
                    }
            except json.JSONDecodeError:
                pass
        
        return {
            'valid': False,
            'amount': 0,
            'confidence': 0,
            'error': 'فشل تحليل الصورة'
        }
    
    @staticmethod
    def analyze_usdt_transaction(image_base64: str) -> Dict:
        """Analyze USDT transaction screenshot"""
        prompt = """حلل صورة معاملة USDT/تيثر واستخرج المعلومات التالية:

1. Transaction Hash/TXID (يبدأ بـ 0x ويتكون من 66 حرف)
2. المبلغ بـ USDT
3. حالة المعاملة (Success/Completed/Confirmed)
4. الشبكة (BSC/BEP20/ERC20/TRC20)

أجب بـ JSON فقط:
{"txid": "0x...", "amount": 50.0, "status": "success", "network": "BSC", "confidence": 0.9}

إذا لم تجد المعلومات:
{"txid": null, "amount": 0, "status": "unknown", "network": "unknown", "confidence": 0}"""

        result = AIService._call_vision_api(prompt, image_base64, 200)
        
        if result:
            try:
                json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    txid = data.get('txid', '')
                    
                    # Validate TXID format
                    if txid and not re.match(r'^0x[a-fA-F0-9]{64}$', str(txid)):
                        # Try to extract from string
                        txid_match = re.search(r'0x[a-fA-F0-9]{64}', str(txid))
                        txid = txid_match.group() if txid_match else None
                    
                    return {
                        'txid': txid,
                        'amount': float(data.get('amount', 0)),
                        'status': data.get('status', 'unknown'),
                        'network': data.get('network', 'unknown'),
                        'confidence': float(data.get('confidence', 0))
                    }
            except:
                pass
        
        return {
            'txid': None,
            'amount': 0,
            'status': 'unknown',
            'network': 'unknown',
            'confidence': 0
        }

# ══════════════════════════════════════════════════════════════
#                      BSCSCAN API
# ══════════════════════════════════════════════════════════════
class BSCScanAPI:
    """BSCScan blockchain verification"""
    
    BASE_URL = "https://api.bscscan.com/api"
    
    @staticmethod
    def verify_transaction(txid: str, expected_wallet: str) -> Dict:
        """Verify USDT transaction on BSC"""
        try:
            if not re.match(r'^0x[a-fA-F0-9]{64}$', txid):
                return {'valid': False, 'error': 'TXID غير صحيح'}
            
            params = {
                'module': 'proxy',
                'action': 'eth_getTransactionReceipt',
                'txhash': txid,
                'apikey': Config.BSCSCAN_API_KEY
            }
            
            response = requests.get(BSCScanAPI.BASE_URL, params=params, timeout=30)
            data = response.json()
            
            if not data.get('result'):
                return {'valid': False, 'error': 'المعاملة غير موجودة أو غير مؤكدة'}
            
            receipt = data['result']
            
            if receipt.get('status') != '0x1':
                return {'valid': False, 'error': 'المعاملة فاشلة'}
            
            # Check logs for USDT transfer
            for log in receipt.get('logs', []):
                contract = log.get('address', '').lower()
                
                if contract == Config.USDT_CONTRACT.lower():
                    topics = log.get('topics', [])
                    
                    # Transfer event signature
                    if len(topics) >= 3 and topics[0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                        to_address = '0x' + topics[2][-40:]
                        
                        if to_address.lower() == expected_wallet.lower():
                            amount_hex = log.get('data', '0x0')
                            amount_wei = int(amount_hex, 16)
                            amount_usdt = amount_wei / (10 ** 18)
                            
                            return {
                                'valid': True,
                                'amount': amount_usdt,
                                'from_address': '0x' + topics[1][-40:],
                                'to_address': to_address,
                                'block_number': int(receipt.get('blockNumber', '0x0'), 16)
                            }
            
            return {'valid': False, 'error': 'لم يتم العثور على تحويل USDT للمحفظة المطلوبة'}
            
        except requests.Timeout:
            return {'valid': False, 'error': 'انتهى وقت الاتصال'}
        except Exception as e:
            logger.error(f"BSCScan error: {e}")
            return {'valid': False, 'error': 'خطأ في التحقق من البلوكتشين'}
    
    @staticmethod
    def is_txid_used(txid: str) -> bool:
        """Check if TXID was already used"""
        result = Database.execute(
            'SELECT 1 FROM used_txids WHERE txid=?',
            (txid.lower(),),
            fetch_one=True
        )
        return result is not None
    
    @staticmethod
    def mark_txid_used(txid: str, user_id: int, amount: float):
        """Mark TXID as used"""
        Database.execute(
            'INSERT OR IGNORE INTO used_txids(txid, user_id, amount, created_at) VALUES(?,?,?,?)',
            (txid.lower(), user_id, amount, datetime.now().isoformat())
        )

# ══════════════════════════════════════════════════════════════
#                     USER MANAGEMENT
# ══════════════════════════════════════════════════════════════
class UserManager:
    """User management operations"""
    
    @staticmethod
    def get(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return Database.execute(
            'SELECT * FROM users WHERE id=?',
            (user_id,),
            fetch_one=True
        )
    
    @staticmethod
    def create_or_update(user_id: int, username: str = None, first_name: str = None, 
                         last_name: str = None, referrer_id: int = None) -> Dict:
        """Create or update user"""
        user = UserManager.get(user_id)
        now = datetime.now().isoformat()
        
        if not user:
            # Create new user
            welcome_bonus = UserManager._get_config('welcome_bonus', Config.WELCOME_BONUS)
            
            Database.execute(
                '''INSERT INTO users(id, username, first_name, last_name, balance, 
                   referrer_id, join_date, last_active)
                   VALUES(?,?,?,?,?,?,?,?)''',
                (user_id, username, first_name, last_name, welcome_bonus, 
                 referrer_id, now, now)
            )
            
            # Log welcome bonus transaction
            if welcome_bonus > 0:
                Database.execute(
                    '''INSERT INTO transactions(user_id, amount, type, reference, 
                       description, balance_after, created_at)
                       VALUES(?,?,?,?,?,?,?)''',
                    (user_id, welcome_bonus, 'welcome_bonus', 'WELCOME', 
                     'مكافأة الترحيب', welcome_bonus, now)
                )
            
            # Handle referral
            if referrer_id:
                UserManager._process_referral(referrer_id, user_id)
            
            logger.info(f"New user created: {user_id}")
            user = UserManager.get(user_id)
        else:
            # Update existing user
            Database.execute(
                '''UPDATE users SET username=COALESCE(?,username), 
                   first_name=COALESCE(?,first_name), 
                   last_name=COALESCE(?,last_name),
                   last_active=? WHERE id=?''',
                (username, first_name, last_name, now, user_id)
            )
            user = UserManager.get(user_id)
        
        return user
    
    @staticmethod
    def _get_config(key: str, default: Any = None) -> Any:
        """Get configuration value"""
        result = Database.execute(
            'SELECT value FROM bot_config WHERE key=?',
            (key,),
            fetch_one=True
        )
        return json.loads(result['value']) if result else default
    
    @staticmethod
    def _process_referral(referrer_id: int, referred_id: int):
        """Process referral bonus"""
        referrer = UserManager.get(referrer_id)
        if not referrer or referrer['banned']:
            return
        
        bonus = UserManager._get_config('referral_bonus', Config.REFERRAL_BONUS)
        
        # Add bonus to referrer
        UserManager.update_balance(referrer_id, bonus, 'referral_bonus', 
                                   f'REF_{referred_id}', f'مكافأة إحالة #{referred_id}')
        
        # Record referral
        Database.execute(
            '''INSERT INTO referrals(referrer_id, referred_id, bonus_amount, 
               status, created_at) VALUES(?,?,?,?,?)''',
            (referrer_id, referred_id, bonus, 'completed', datetime.now().isoformat())
        )
        
        # Update referrer stats
        Database.execute(
            'UPDATE users SET referral_earnings=referral_earnings+? WHERE id=?',
            (bonus, referrer_id)
        )
    
    @staticmethod
    def update_balance(user_id: int, amount: float, trans_type: str, 
                       reference: str = '', description: str = '', 
                       fee: float = 0) -> float:
        """Update user balance with transaction logging"""
        user = UserManager.get(user_id)
        if not user:
            return 0
        
        old_balance = user['balance']
        new_balance = max(0, round(old_balance + amount, 2))
        
        # Update balance
        Database.execute(
            'UPDATE users SET balance=? WHERE id=?',
            (new_balance, user_id)
        )
        
        # Log transaction
        Database.execute(
            '''INSERT INTO transactions(user_id, amount, type, reference, 
               description, fee, balance_before, balance_after, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)''',
            (user_id, amount, trans_type, reference, description, fee,
             old_balance, new_balance, datetime.now().isoformat())
        )
        
        # Update stats based on transaction type
        if amount < 0:
            Database.execute(
                'UPDATE users SET spent=spent+?, total_orders=total_orders+1 WHERE id=?',
                (abs(amount), user_id)
            )
            UserManager._update_level(user_id)
        elif trans_type == 'deposit':
            Database.execute(
                'UPDATE users SET total_deposits=total_deposits+? WHERE id=?',
                (amount, user_id)
            )
        
        # Log activity
        Database.execute(
            'INSERT INTO activity_logs(user_id, action, details, created_at) VALUES(?,?,?,?)',
            (user_id, trans_type, f'{amount:+.2f} | {reference}', datetime.now().isoformat())
        )
        
        return new_balance
    
    @staticmethod
    def _update_level(user_id: int):
        """Update user level based on spending"""
        user = UserManager.get(user_id)
        if not user:
            return
        
        new_level = Database.execute(
            'SELECT * FROM user_levels WHERE min_spent <= ? ORDER BY level DESC LIMIT 1',
            (user['spent'],),
            fetch_one=True
        )
        
        if new_level and new_level['level'] != user['level']:
            old_level = user['level']
            Database.execute(
                'UPDATE users SET level=? WHERE id=?',
                (new_level['level'], user_id)
            )
            
            if new_level['level'] > old_level:
                # Send level up notification
                UserManager.add_notification(
                    user_id,
                    f"🎉 ترقية للمستوى {new_level['badge']} {new_level['name']}!",
                    f"مبروك! لقد ترقيت لمستوى أعلى مع مزايا إضافية!",
                    'level_up'
                )
    
    @staticmethod
    def get_level_info(user_id: int) -> Dict:
        """Get user level details"""
        user = UserManager.get(user_id)
        if not user:
            return {}
        
        current = Database.execute(
            'SELECT * FROM user_levels WHERE level=?',
            (user['level'],),
            fetch_one=True
        )
        
        next_level = Database.execute(
            'SELECT * FROM user_levels WHERE level=?',
            (user['level'] + 1,),
            fetch_one=True
        )
        
        return {
            'current': current,
            'next': next_level,
            'spent': user['spent'],
            'needed': (next_level['min_spent'] - user['spent']) if next_level else 0
        }
    
    @staticmethod
    def add_notification(user_id: int, title: str, message: str = '', 
                        notif_type: str = 'info'):
        """Add notification for user"""
        Database.execute(
            '''INSERT INTO notifications(user_id, title, message, type, created_at)
               VALUES(?,?,?,?,?)''',
            (user_id, title, message, notif_type, datetime.now().isoformat())
        )
    
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
                # Auto-unban
                Database.execute(
                    'UPDATE users SET banned=0, ban_until=NULL, ban_reason=NULL WHERE id=?',
                    (user_id,)
                )
                return False, ''
        
        return True, user.get('ban_reason', 'غير محدد')
    
    @staticmethod
    def ban_user(user_id: int, reason: str, duration_hours: int = None, 
                 banned_by: int = None):
        """Ban a user"""
        ban_until = None
        if duration_hours:
            ban_until = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        Database.execute(
            'UPDATE users SET banned=1, ban_until=?, ban_reason=? WHERE id=?',
            (ban_until, reason, user_id)
        )
        
        Database.execute(
            '''INSERT INTO security_logs(user_id, event_type, severity, details, created_at)
               VALUES(?,?,?,?,?)''',
            (user_id, 'user_banned', 'high', 
             f'Reason: {reason}, Duration: {duration_hours}h, By: {banned_by}',
             datetime.now().isoformat())
        )
    
    @staticmethod
    def unban_user(user_id: int, unbanned_by: int = None):
        """Unban a user"""
        Database.execute(
            'UPDATE users SET banned=0, ban_until=NULL, ban_reason=NULL WHERE id=?',
            (user_id,)
        )
        
        Database.execute(
            '''INSERT INTO security_logs(user_id, event_type, severity, details, created_at)
               VALUES(?,?,?,?,?)''',
            (user_id, 'user_unbanned', 'info', f'By: {unbanned_by}',
             datetime.now().isoformat())
        )

# ══════════════════════════════════════════════════════════════
#                    KEYBOARD BUILDERS
# ══════════════════════════════════════════════════════════════
class Keyboards:
    """Keyboard builders"""
    
    @staticmethod
    def main_menu(user_id: int) -> InlineKeyboardMarkup:
        """Build main menu keyboard"""
        user = UserManager.get(user_id)
        balance = user['balance'] if user else 0
        
        level_info = UserManager.get_level_info(user_id)
        badge = level_info.get('current', {}).get('badge', '🥉') if level_info.get('current') else '🥉'
        
        # Check unread notifications
        unread = Database.execute(
            'SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0',
            (user_id,),
            fetch_one=True
        )
        notif_count = unread['c'] if unread else 0
        notif_text = f"🔔 ({notif_count})" if notif_count > 0 else "🔔"
        
        buttons = [
            [InlineKeyboardButton(f"💰 رصيدك: {balance:.0f}ج {badge}", callback_data='wallet')],
            [
                InlineKeyboardButton('🛍️ المتجر', callback_data='shop'),
                InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')
            ],
            [
                InlineKeyboardButton('📦 طلباتي', callback_data='my_orders'),
                InlineKeyboardButton('🎁 المكافآت', callback_data='rewards')
            ],
            [
                InlineKeyboardButton('🎟️ كوبون', callback_data='coupon'),
                InlineKeyboardButton('👥 دعوة صديق', callback_data='referral')
            ],
            [
                InlineKeyboardButton(notif_text, callback_data='notifications'),
                InlineKeyboardButton('🆘 الدعم', callback_data='support')
            ],
        ]
        
        if user_id in Config.ADMIN_IDS:
            buttons.append([InlineKeyboardButton('⚙️ لوحة التحكم', callback_data='admin_panel')])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def admin_panel() -> InlineKeyboardMarkup:
        """Build admin panel keyboard"""
        # Get counts
        pending_orders = Database.execute(
            "SELECT COUNT(*) as c FROM orders WHERE status='pending'",
            fetch_one=True
        )['c']
        
        pending_deposits = Database.execute(
            "SELECT COUNT(*) as c FROM deposits WHERE status='pending'",
            fetch_one=True
        )['c']
        
        open_tickets = Database.execute(
            "SELECT COUNT(*) as c FROM tickets WHERE status='open'",
            fetch_one=True
        )['c']
        
        buttons = [
            [
                InlineKeyboardButton(f"📦 الطلبات ({pending_orders})", callback_data='admin_orders'),
                InlineKeyboardButton(f"💰 الإيداعات ({pending_deposits})", callback_data='admin_deposits')
            ],
            [
                InlineKeyboardButton(f"🎫 التذاكر ({open_tickets})", callback_data='admin_tickets'),
                InlineKeyboardButton('👥 المستخدمين', callback_data='admin_users')
            ],
            [
                InlineKeyboardButton('📊 الإحصائيات', callback_data='admin_stats'),
                InlineKeyboardButton('💹 الأرباح', callback_data='admin_profits')
            ],
            [
                InlineKeyboardButton('🎟️ كوبون جديد', callback_data='admin_new_coupon'),
                InlineKeyboardButton('🎁 بطاقة هدية', callback_data='admin_giftcard')
            ],
            [
                InlineKeyboardButton('📢 إعلان AI', callback_data='admin_promo'),
                InlineKeyboardButton('📨 إذاعة', callback_data='admin_broadcast')
            ],
            [
                InlineKeyboardButton('⚡ عرض خاطف', callback_data='admin_flash_sale'),
                InlineKeyboardButton('🔧 الإعدادات', callback_data='admin_settings')
            ],
            [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def back_button(callback_data: str = 'home') -> InlineKeyboardMarkup:
        """Simple back button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('◀️ رجوع', callback_data=callback_data)]
        ])
    
    @staticmethod
    def confirm_cancel(confirm_callback: str, cancel_callback: str = 'home') -> InlineKeyboardMarkup:
        """Confirm/Cancel buttons"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('✅ تأكيد', callback_data=confirm_callback),
                InlineKeyboardButton('❌ إلغاء', callback_data=cancel_callback)
            ]
        ])

# ══════════════════════════════════════════════════════════════
#                    PROMO SCHEDULER
# ══════════════════════════════════════════════════════════════
async def post_promotional_content(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Post promotional content to group"""
    try:
        content = AIService.generate_promotional_post()
        
        bot_link = f"https://t.me/{state.bot_username}?start=promo"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton('🚀 افتح المتجر الآن!', url=bot_link)]
        ])
        
        # Delete previous pinned promo
        last_promo = Database.execute(
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
        
        # Send new promo
        message = await context.bot.send_message(
            chat_id=Config.GROUP_ID,
            text=content,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=buttons
        )
        
        # Pin the message
        try:
            await context.bot.pin_chat_message(
                chat_id=Config.GROUP_ID,
                message_id=message.message_id,
                disable_notification=True
            )
        except:
            pass
        
        # Save to database
        Database.execute(
            '''INSERT INTO promo_posts(message_id, chat_id, content, type, created_at)
               VALUES(?,?,?,?,?)''',
            (message.message_id, Config.GROUP_ID, content[:500], 'ai_generated',
             datetime.now().isoformat())
        )
        
        logger.info("✅ Promotional post published successfully")
        return True
        
    except Exception as e:
        logger.error(f"Promo posting error: {e}")
        return False


async def promo_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Scheduler for promotional posts"""
    await asyncio.sleep(30)  # Initial delay
    
    while True:
        try:
            await post_promotional_content(context)
        except Exception as e:
            logger.error(f"Promo scheduler error: {e}")
        
        await asyncio.sleep(Config.PROMO_INTERVAL_SECONDS)

# ══════════════════════════════════════════════════════════════
#                     COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    if not state.bot_username:
        state.bot_username = context.bot.username
    
    # Check if banned
    is_banned, ban_reason = UserManager.is_banned(user.id)
    if is_banned:
        await update.message.reply_text(
            f"🚫 *أنت محظور من استخدام البوت*\n\nالسبب: {ban_reason}",
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
            except:
                pass
    
    # Get or create user
    existing_user = UserManager.get(user.id)
    is_new_user = existing_user is None
    
    db_user = UserManager.create_or_update(
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        referrer_id if is_new_user else None
    )
    
    # Get level info
    level_info = UserManager.get_level_info(user.id)
    level = level_info.get('current', {}) if level_info else {}
    badge = level.get('badge', '🥉')
    level_name = level.get('name', 'برونزي')
    
    # Tips
    tips = [
        "💡 نصيحة: اجمع مكافأتك اليومية كل يوم لزيادة رصيدك!",
        "🔥 تذكير: كلما اشتريت أكثر، ترقيت لمستوى أعلى مع مزايا أفضل!",
        "⚡ التسليم فوري ومضمون 100% على جميع المنتجات!",
        "🎁 ادعُ أصدقاءك واكسب 10ج عن كل صديق يسجل!",
        "🎟️ تابع الإعلانات للحصول على كوبونات خصم حصرية!",
        "💎 استخدم USDT للإيداع واستمتع بموافقة فورية!",
    ]
    
    welcome_text = f"""🔥 *مرحباً بك في XLERO SHOP!* 🔥

👋 أهلاً *{user.first_name}*

━━━━━━━━━━━━━━━━━━━━━

💰 *رصيدك:* {db_user['balance']:.2f} ج.م
{badge} *المستوى:* {level_name}
📦 *طلباتك:* {db_user['total_orders']}
⭐ *نقاطك:* {db_user['points']}

━━━━━━━━━━━━━━━━━━━━━

{random.choice(tips)}

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
        welcome_text += f"\n\n🎁 *هدية ترحيبية:* +{welcome_bonus:.0f}ج تمت إضافتها لرصيدك!"
        
        if referrer_id:
            welcome_text += f"\n👥 تم تسجيلك عبر إحالة!"
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user.id)
    )
    
    logger.info(f"User {user.id} started bot (new: {is_new_user})")


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("❌ غير مصرح لك بالوصول")
        return
    
    await update.message.reply_text(
        "⚙️ *لوحة تحكم المدير*",
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

# ══════════════════════════════════════════════════════════════
#                   CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════════════════════
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    # Answer callback to remove loading
    try:
        await query.answer()
    except Exception:
        pass
    
    # Check if banned
    is_banned, ban_reason = UserManager.is_banned(user_id)
    if is_banned and user_id not in Config.ADMIN_IDS:
        try:
            await query.edit_message_text(f"🚫 أنت محظور\nالسبب: {ban_reason}")
        except:
            pass
        return
    
    # Get or create user
    user = UserManager.create_or_update(
        user_id,
        query.from_user.username,
        query.from_user.first_name
    )
    
    try:
        # ══════════════════════════════════════════════════════════
        #                      MAIN NAVIGATION
        # ══════════════════════════════════════════════════════════
        if data == 'home':
            await handle_home(query, user)
        
        elif data == 'wallet':
            await handle_wallet(query, user)
        
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
        
        elif data == 'deposit':
            await handle_deposit(query, context, user)
        
        elif data == 'my_orders':
            await handle_my_orders(query, user)
        
        elif data.startswith('order_'):
            await handle_order_details(query, user, data)
        
        elif data == 'rewards':
            await handle_rewards(query, user)
        
        elif data == 'claim_daily':
            await handle_claim_daily(query, user)
        
        elif data == 'coupon':
            await handle_coupon_input(query, context, user)
        
        elif data == 'referral':
            await handle_referral(query, user)
        
        elif data == 'notifications':
            await handle_notifications(query, user)
        
        elif data == 'support':
            await handle_support(query, user)
        
        elif data == 'new_ticket':
            await handle_new_ticket(query, context, user)
        
        elif data == 'my_tickets':
            await handle_my_tickets(query, user)
        
        elif data.startswith('ticket_'):
            await handle_ticket_view(query, context, user, data)
        
        elif data.startswith('reply_ticket_'):
            await handle_ticket_reply(query, context, user, data)
        
        # ══════════════════════════════════════════════════════════
        #                      ADMIN HANDLERS
        # ══════════════════════════════════════════════════════════
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
        
    except Exception as e:
        logger.error(f"Callback error for {data}: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "❌ حدث خطأ، حاول مرة أخرى",
                reply_markup=Keyboards.main_menu(user_id)
            )
        except:
            pass

# ══════════════════════════════════════════════════════════════
#                    MAIN MENU HANDLERS
# ══════════════════════════════════════════════════════════════
async def handle_home(query, user: Dict):
    """Handle home button"""
    level_info = UserManager.get_level_info(user['id'])
    badge = level_info.get('current', {}).get('badge', '🥉') if level_info.get('current') else '🥉'
    
    text = f"""🏠 *القائمة الرئيسية*

💰 رصيدك: *{user['balance']:.2f}* ج.م
{badge} المستوى: {level_info.get('current', {}).get('name', 'برونزي') if level_info.get('current') else 'برونزي'}
📦 طلباتك: {user['total_orders']}"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def handle_wallet(query, user: Dict):
    """Handle wallet view"""
    # Get recent transactions
    transactions = Database.execute(
        '''SELECT * FROM transactions WHERE user_id=? 
           ORDER BY id DESC LIMIT 10''',
        (user['id'],),
        fetch_all=True
    )
    
    level_info = UserManager.get_level_info(user['id'])
    level = level_info.get('current', {}) if level_info.get('current') else {}
    next_level = level_info.get('next')
    
    text = f"""💰 *محفظتي*
━━━━━━━━━━━━━━━━━━━━━

💵 الرصيد الحالي: *{user['balance']:.2f}* ج.م
💸 إجمالي الإنفاق: {user['spent']:.0f} ج.م
💳 إجمالي الإيداعات: {user['total_deposits']:.0f} ج.م
🎁 كاش باك مكتسب: {user.get('cashback_total', 0):.0f} ج.م

━━━━━━━━━━━━━━━━━━━━━

{level.get('badge', '🥉')} *المستوى:* {level.get('name', 'برونزي')}
💎 كاش باك إضافي: +{level.get('cashback_bonus', 0)}%
🎁 مكافأة يومية: +{level.get('daily_bonus', 0)}ج"""
    
    if next_level:
        needed = next_level['min_spent'] - user['spent']
        text += f"\n\n📈 للترقية لـ {next_level['badge']} {next_level['name']}: أنفق {needed:.0f}ج إضافية"
    
    text += "\n\n━━━━━━━━━━━━━━━━━━━━━\n\n📜 *آخر العمليات:*\n"
    
    if transactions:
        for t in transactions[:7]:
            sign = '+' if t['amount'] > 0 else ''
            emoji = '📥' if t['amount'] > 0 else '📤'
            text += f"{emoji} {sign}{t['amount']:.0f}ج - {t['type']}\n"
    else:
        text += "لا توجد عمليات بعد"
    
    buttons = [
        [InlineKeyboardButton('💳 شحن رصيد', callback_data='deposit')],
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_shop(query, user: Dict):
    """Handle shop view"""
    # Get categories
    categories = Database.execute(
        'SELECT DISTINCT category FROM products WHERE is_active=1',
        fetch_all=True
    )
    
    category_info = {
        'freefire': ('🔥 فري فاير', 'Free Fire'),
        'pubg': ('🔫 ببجي موبايل', 'PUBG Mobile'),
        'mlbb': ('⚔️ موبايل ليجندز', 'Mobile Legends'),
        'steam': ('🎮 ستيم', 'Steam'),
        'googleplay': ('📱 جوجل بلاي', 'Google Play'),
        'itunes': ('🍎 آيتونز', 'iTunes'),
        'playstation': ('🎮 بلايستيشن', 'PlayStation'),
        'xbox': ('🎮 إكس بوكس', 'Xbox'),
    }
    
    buttons = []
    for cat in categories:
        cat_key = cat['category']
        cat_info = category_info.get(cat_key, (cat_key.upper(), cat_key))
        
        count = Database.execute(
            'SELECT COUNT(*) as c FROM products WHERE category=? AND is_active=1',
            (cat_key,),
            fetch_one=True
        )['c']
        
        buttons.append([
            InlineKeyboardButton(f"{cat_info[0]} ({count})", callback_data=f"category_{cat_key}")
        ])
    
    buttons.append([InlineKeyboardButton('🏠 الرئيسية', callback_data='home')])
    
    text = f"""🛍️ *المتجر*
━━━━━━━━━━━━━━━━━━━━━

💰 رصيدك: *{user['balance']:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

📦 اختر القسم المطلوب:"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_category(query, user: Dict, data: str):
    """Handle category view"""
    category = data.replace('category_', '')
    
    products = Database.execute(
        '''SELECT * FROM products WHERE category=? AND is_active=1 
           ORDER BY sort_order, price''',
        (category,),
        fetch_all=True
    )
    
    if not products:
        await query.answer("لا توجد منتجات متاحة حالياً", show_alert=True)
        return
    
    category_names = {
        'freefire': 'فري فاير',
        'pubg': 'ببجي موبايل',
        'mlbb': 'موبايل ليجندز',
        'steam': 'ستيم',
        'googleplay': 'جوجل بلاي',
        'itunes': 'آيتونز',
        'playstation': 'بلايستيشن',
        'xbox': 'إكس بوكس',
    }
    
    buttons = []
    for p in products:
        discount_text = ''
        if p['original_price'] and p['original_price'] > p['price']:
            discount = round((1 - p['price'] / p['original_price']) * 100)
            discount_text = f" 🏷️-{discount}%"
        
        cashback_text = f" 💎{p['cashback_percent']:.0f}%" if p.get('cashback_percent', 0) > 0 else ''
        
        stock_text = ''
        if p['stock'] == 0:
            stock_text = ' ❌'
        elif p['stock'] > 0 and p['stock'] <= 5:
            stock_text = f' ⚠️{p["stock"]}'
        
        buttons.append([
            InlineKeyboardButton(
                f"{p['name']} - {p['price']:.0f}ج{discount_text}{cashback_text}{stock_text}",
                callback_data=f"product_{p['item_key']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع للمتجر', callback_data='shop')])
    
    text = f"""📦 *{category_names.get(category, category)}*
━━━━━━━━━━━━━━━━━━━━━

💰 رصيدك: *{user['balance']:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

🛍️ اختر المنتج:"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_product(query, user: Dict, data: str):
    """Handle product view"""
    item_key = data.replace('product_', '')
    
    product = Database.execute(
        'SELECT * FROM products WHERE item_key=? AND is_active=1',
        (item_key,),
        fetch_one=True
    )
    
    if not product:
        await query.answer("❌ المنتج غير متوفر", show_alert=True)
        return
    
    # Check stock
    if product['stock'] == 0:
        await query.answer("❌ نفد المخزون", show_alert=True)
        return
    
    # Price display
    price_text = f"*{product['price']:.0f}ج*"
    savings_text = ''
    
    if product['original_price'] and product['original_price'] > product['price']:
        discount = round((1 - product['price'] / product['original_price']) * 100)
        price_text = f"~~{product['original_price']:.0f}~~ → *{product['price']:.0f}ج*"
        savings_text = f"\n💰 توفير: {product['original_price'] - product['price']:.0f}ج ({discount}%)"
    
    # Cashback
    cashback = product['price'] * product.get('cashback_percent', 3) / 100
    level_info = UserManager.get_level_info(user['id'])
    level_bonus = level_info.get('current', {}).get('cashback_bonus', 0) if level_info.get('current') else 0
    total_cashback = cashback * (1 + level_bonus / 100)
    
    cashback_text = f"\n💎 كاش باك: +{total_cashback:.0f}ج"
    
    # Stock
    stock_text = ''
    if product['stock'] > 0:
        stock_text = f"\n📦 المتبقي: {product['stock']} قطعة"
    
    text = f"""🛍️ *{product['name']}*
━━━━━━━━━━━━━━━━━━━━━

💵 السعر: {price_text}{savings_text}{cashback_text}
📈 المبيعات: {product['sold_count']}
⏱️ التسليم: {product.get('delivery_time', 'فوري')}{stock_text}

━━━━━━━━━━━━━━━━━━━━━

📝 {product.get('description', '')}

━━━━━━━━━━━━━━━━━━━━━

✅ *متوفر* • ⚡ *تسليم فوري* • 🛡️ *ضمان كامل*"""
    
    # Check if user can buy
    can_buy = user['balance'] >= product['price']
    
    buttons = []
    if can_buy:
        buttons.append([InlineKeyboardButton('🛒 شراء الآن', callback_data=f"buy_{item_key}")])
    else:
        needed = product['price'] - user['balance']
        buttons.append([InlineKeyboardButton(f"💳 تحتاج {needed:.0f}ج - اشحن الآن", callback_data='deposit')])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data=f"category_{product['category']}")])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_buy(query, context: ContextTypes.DEFAULT_TYPE, user: Dict, data: str):
    """Handle buy action"""
    item_key = data.replace('buy_', '')
    
    product = Database.execute(
        'SELECT * FROM products WHERE item_key=? AND is_active=1',
        (item_key,),
        fetch_one=True
    )
    
    if not product:
        await query.answer("❌ المنتج غير متوفر", show_alert=True)
        return
    
    # Check stock
    if product['stock'] == 0:
        await query.answer("❌ نفد المخزون", show_alert=True)
        return
    
    # Check balance
    if user['balance'] < product['price']:
        needed = product['price'] - user['balance']
        text = f"""❌ *رصيدك غير كافٍ!*

💰 رصيدك الحالي: {user['balance']:.0f}ج
💸 سعر المنتج: {product['price']:.0f}ج
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
    required_fields = json.loads(product['required_fields']) if product['required_fields'] else []
    
    if required_fields:
        # Save pending input
        Database.execute('DELETE FROM pending_inputs WHERE user_id=?', (user['id'],))
        
        expires = (datetime.now() + timedelta(minutes=10)).isoformat()
        Database.execute(
            '''INSERT INTO pending_inputs(user_id, action_type, item_key, current_step, 
               collected_data, expires_at, created_at) VALUES(?,?,?,?,?,?,?)''',
            (user['id'], 'purchase', item_key, 0, '{}', expires, datetime.now().isoformat())
        )
        
        field_labels = {
            'player_id': '🎮 أدخل Player ID الخاص بك:',
            'pubg_id': '🔫 أدخل PUBG ID الخاص بك:',
            'ml_id': '⚔️ أدخل ML ID (معرف اللاعب):',
            'zone_id': '🌍 أدخل Zone ID (معرف السيرفر):',
        }
        
        current_field = required_fields[0]
        
        text = f"""📝 *إدخال بيانات الشحن*
━━━━━━━━━━━━━━━━━━━━━

🛍️ المنتج: {product['name']}
💰 السعر: {product['price']:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

{field_labels.get(current_field, f'أدخل {current_field}:')}

⚠️ *تأكد من صحة البيانات!*
⏰ صلاحية الجلسة: 10 دقائق"""
        
        context.user_data['waiting_for'] = 'product_input'
        
        buttons = [[InlineKeyboardButton('❌ إلغاء', callback_data='cancel_purchase')]]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # No input required - proceed to purchase
        await complete_purchase(query, context, user, product, {})


async def handle_cancel_purchase(query, user: Dict):
    """Cancel purchase"""
    Database.execute('DELETE FROM pending_inputs WHERE user_id=?', (user['id'],))
    
    await query.edit_message_text(
        "❌ تم إلغاء عملية الشراء",
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def complete_purchase(query, context, user: Dict, product: Dict, input_data: Dict):
    """Complete the purchase"""
    price = product['price']
    
    # Calculate cashback
    cashback_percent = product.get('cashback_percent', 3)
    level_info = UserManager.get_level_info(user['id'])
    level_bonus = level_info.get('current', {}).get('cashback_bonus', 0) if level_info.get('current') else 0
    total_cashback_percent = cashback_percent + level_bonus
    cashback = price * total_cashback_percent / 100
    
    # Deduct balance
    new_balance = UserManager.update_balance(
        user['id'], -price, 'purchase', 
        product['item_key'], f"شراء {product['name']}"
    )
    
    # Add cashback
    if cashback > 0:
        UserManager.update_balance(
            user['id'], cashback, 'cashback',
            product['item_key'], f"كاش باك {product['name']}"
        )
        Database.execute(
            'UPDATE users SET cashback_total=cashback_total+? WHERE id=?',
            (cashback, user['id'])
        )
    
    # Generate order ID
    order_id = f"XL{int(time.time()) % 100000}{random.randint(100, 999)}"
    
    # Create order
    Database.execute(
        '''INSERT INTO orders(order_id, user_id, product_key, product_name, unit_price,
           total_price, cashback_amount, input_data, created_at) VALUES(?,?,?,?,?,?,?,?,?)''',
        (order_id, user['id'], product['item_key'], product['name'], price,
         price, cashback, json.dumps(input_data, ensure_ascii=False), 
         datetime.now().isoformat())
    )
    
    # Update product stats
    Database.execute(
        'UPDATE products SET sold_count=sold_count+1 WHERE item_key=?',
        (product['item_key'],)
    )
    
    # Update stock if limited
    if product['stock'] > 0:
        Database.execute(
            'UPDATE products SET stock=stock-1 WHERE item_key=?',
            (product['item_key'],)
        )
    
    # Notify admins
    input_text = '\n'.join([f"• {k}: `{v}`" for k, v in input_data.items()]) if input_data else 'لا توجد'
    
    admin_msg = f"""🛒 *طلب جديد!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
👤 المستخدم: `{user['id']}` @{user.get('username', 'N/A')}

🛍️ المنتج: {product['name']}
💰 السعر: {price:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📋 *بيانات الشحن:*
{input_text}"""
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('✅ تنفيذ', callback_data=f"execute_{order_id}"),
            InlineKeyboardButton('❌ إلغاء', callback_data=f"cancel_order_{order_id}")
        ]
    ])
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                admin_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_buttons
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # Success message
    text = f"""✅ *تم تقديم الطلب بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
🛍️ المنتج: {product['name']}
💰 السعر: {price:.0f}ج
💎 كاش باك: +{cashback:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك المتبقي: *{new_balance + cashback:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

⏳ سيتم تنفيذ طلبك في أقرب وقت!
📱 سنُعلمك فور التنفيذ."""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )
    
    logger.info(f"Order {order_id} created by user {user['id']}")


async def handle_deposit(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle deposit request"""
    text = f"""💳 *شحن الرصيد*
━━━━━━━━━━━━━━━━━━━━━

📱 *فودافون كاش:*
`{Config.VODAFONE_NUMBER}`

💎 *USDT (BEP20 - شبكة BSC):*
`{Config.USDT_WALLET}`

━━━━━━━━━━━━━━━━━━━━━

📌 *خطوات الإيداع:*
1️⃣ حوّل المبلغ المطلوب لإحدى الطرق أعلاه
2️⃣ أرسل صورة واضحة للإيصال هنا
3️⃣ سيتم إضافة الرصيد تلقائياً أو بعد المراجعة

━━━━━━━━━━━━━━━━━━━━━

💰 الحد الأدنى: {Config.MIN_DEPOSIT}ج
💰 الحد الأقصى: {Config.MAX_DEPOSIT}ج
💸 عمولة: {Config.DEPOSIT_FEE_PERCENT}% (بحد أقصى {Config.DEPOSIT_FEE_MAX}ج)

━━━━━━━━━━━━━━━━━━━━━

⚡ *إيداعات ≤{Config.MANUAL_VERIFY_THRESHOLD}ج:* موافقة فورية
⏰ *إيداعات أكبر:* 5-30 دقيقة للمراجعة

━━━━━━━━━━━━━━━━━━━━━

📤 *أرسل صورة الإيصال الآن*"""
    
    context.user_data['waiting_for'] = 'deposit_image'
    
    buttons = [[InlineKeyboardButton('◀️ رجوع', callback_data='home')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_my_orders(query, user: Dict):
    """Handle my orders view"""
    orders = Database.execute(
        '''SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 15''',
        (user['id'],),
        fetch_all=True
    )
    
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
    buttons = []
    
    for order in orders:
        icon = status_icons.get(order['status'], '❓')
        date = order['created_at'][:10] if order['created_at'] else ''
        text += f"{icon} `{order['order_id']}` | {order['total_price']:.0f}ج | {date}\n"
        buttons.append([
            InlineKeyboardButton(
                f"📄 {order['order_id']}", 
                callback_data=f"order_{order['order_id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('🏠 الرئيسية', callback_data='home')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_order_details(query, user: Dict, data: str):
    """Handle order details view"""
    order_id = data.replace('order_', '')
    
    order = Database.execute(
        'SELECT * FROM orders WHERE order_id=? AND user_id=?',
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
    
    text = f"""📦 *تفاصيل الطلب*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order['order_id']}`
🛍️ المنتج: {order['product_name']}
💰 السعر: {order['total_price']:.0f}ج
📅 التاريخ: {order['created_at'][:16] if order['created_at'] else ''}

━━━━━━━━━━━━━━━━━━━━━

📊 الحالة: {status_names.get(order['status'], order['status'])}"""
    
    if order.get('discount_amount') and order['discount_amount'] > 0:
        text += f"\n🏷️ الخصم: {order['discount_amount']:.0f}ج"
    
    if order.get('cashback_amount') and order['cashback_amount'] > 0:
        text += f"\n💎 كاش باك: +{order['cashback_amount']:.0f}ج"
    
    if order['status'] in ['done', 'completed'] and order.get('delivery_data'):
        text += f"""

━━━━━━━━━━━━━━━━━━━━━

📬 *بيانات التسليم:*
{order['delivery_data']}

⚠️ احتفظ بهذه البيانات!"""
    
    if order['status'] == 'cancelled' and order.get('cancel_reason'):
        text += f"\n\n❌ سبب الإلغاء: {order['cancel_reason']}"
    
    buttons = [[InlineKeyboardButton('◀️ رجوع', callback_data='my_orders')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_rewards(query, user: Dict):
    """Handle rewards view"""
    # Get daily reward info
    daily = Database.execute(
        'SELECT * FROM daily_rewards WHERE user_id=?',
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
        if daily['last_claim_date']:
            last_claim = datetime.strptime(daily['last_claim_date'], '%Y-%m-%d').date()
            can_claim = last_claim < today
        streak = daily.get('current_streak', 0)
        max_streak = daily.get('max_streak', 0)
        total_claimed = daily.get('total_claimed', 0)
    
    # Calculate today's reward
    base_reward = Config.DAILY_BASE_REWARD
    streak_bonus = min(streak, Config.MAX_DAILY_STREAK_BONUS)
    today_reward = base_reward + streak_bonus + daily_bonus
    
    text = f"""🎁 *المكافآت والجوائز*
━━━━━━━━━━━━━━━━━━━━━

🗓️ *المكافأة اليومية:*
{'🟢 متاحة الآن!' if can_claim else '🔴 تم الاستلام اليوم'}

💰 مكافأة اليوم: *{today_reward:.0f}ج*
🔥 سلسلة الأيام الحالية: {streak}
🏆 أعلى سلسلة: {max_streak}
💵 إجمالي المكتسب: {total_claimed:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📈 *كيف تزيد مكافأتك:*
• المكافأة الأساسية: {base_reward}ج
• +1ج عن كل يوم متتالي (حتى {Config.MAX_DAILY_STREAK_BONUS})
• بونص المستوى: +{daily_bonus}ج

━━━━━━━━━━━━━━━━━━━━━

💎 *نظام الكاش باك:*
تحصل على كاش باك تلقائي عند كل عملية شراء!
كاش باك مكتسب: {user.get('cashback_total', 0):.0f}ج"""
    
    buttons = []
    
    if can_claim:
        buttons.append([InlineKeyboardButton(f"🎁 استلم {today_reward:.0f}ج", callback_data='claim_daily')])
    else:
        buttons.append([InlineKeyboardButton('⏳ عد غداً للاستلام', callback_data='_')])
    
    buttons.append([InlineKeyboardButton('🏠 الرئيسية', callback_data='home')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_claim_daily(query, user: Dict):
    """Handle daily reward claim"""
    # Get daily reward info
    daily = Database.execute(
        'SELECT * FROM daily_rewards WHERE user_id=?',
        (user['id'],),
        fetch_one=True
    )
    
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # Check if already claimed
    if daily and daily['last_claim_date']:
        last_claim = datetime.strptime(daily['last_claim_date'], '%Y-%m-%d').date()
        if last_claim == today:
            await query.answer("⏳ لقد استلمت مكافأة اليوم بالفعل!", show_alert=True)
            return
    
    # Calculate streak
    new_streak = 1
    if daily and daily['last_claim_date']:
        last_claim = datetime.strptime(daily['last_claim_date'], '%Y-%m-%d').date()
        if (today - last_claim).days == 1:
            new_streak = daily.get('current_streak', 0) + 1
    
    # Calculate reward
    level_info = UserManager.get_level_info(user['id'])
    daily_bonus = level_info.get('current', {}).get('daily_bonus', 0) if level_info.get('current') else 0
    
    base_reward = Config.DAILY_BASE_REWARD
    streak_bonus = min(new_streak - 1, Config.MAX_DAILY_STREAK_BONUS)
    reward = base_reward + streak_bonus + daily_bonus
    
    # Add reward
    UserManager.update_balance(
        user['id'], reward, 'daily_reward', 
        f'DAY_{new_streak}', f'مكافأة يومية - يوم {new_streak}'
    )
    
    # Update daily rewards table
    max_streak = max(daily.get('max_streak', 0) if daily else 0, new_streak)
    total_claimed = (daily.get('total_claimed', 0) if daily else 0) + reward
    total_claims = (daily.get('total_claims', 0) if daily else 0) + 1
    
    Database.execute(
        '''INSERT OR REPLACE INTO daily_rewards
           (user_id, last_claim_date, current_streak, max_streak, total_claimed, total_claims)
           VALUES(?,?,?,?,?,?)''',
        (user['id'], today_str, new_streak, max_streak, total_claimed, total_claims)
    )
    
    text = f"""🎉 *تم استلام المكافأة اليومية!*
━━━━━━━━━━━━━━━━━━━━━

💰 المكافأة: *+{reward:.0f}ج*
🔥 سلسلة الأيام: {new_streak} يوم متتالي

━━━━━━━━━━━━━━━━━━━━━

{'🏆 رائع! حافظ على السلسلة للحصول على مكافآت أكبر!' if new_streak > 1 else '👍 ابدأ سلسلتك الآن! عد غداً للمزيد!'}

⏰ عد غداً لاستلام مكافأة أخرى!"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )
    
    logger.info(f"User {user['id']} claimed daily reward: {reward}")


async def handle_coupon_input(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle coupon input"""
    context.user_data['waiting_for'] = 'coupon_code'
    
    text = """🎟️ *استخدام كوبون*
━━━━━━━━━━━━━━━━━━━━━

أدخل كود الكوبون الخاص بك:"""
    
    buttons = [[InlineKeyboardButton('◀️ رجوع', callback_data='home')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_referral(query, user: Dict):
    """Handle referral view"""
    bonus = Config.REFERRAL_BONUS
    
    # Get referral stats
    referral_count = Database.execute(
        'SELECT COUNT(*) as c FROM referrals WHERE referrer_id=?',
        (user['id'],),
        fetch_one=True
    )['c']
    
    referral_earnings = user.get('referral_earnings', 0)
    
    ref_link = f"https://t.me/{state.bot_username}?start=r{user['id']}"
    
    text = f"""👥 *برنامج الإحالة*
━━━━━━━━━━━━━━━━━━━━━

🎁 *المكافآت:*
• {bonus}ج عند تسجيل صديق جديد
• 5ج عند أول عملية شراء للصديق

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
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_notifications(query, user: Dict):
    """Handle notifications view"""
    notifications = Database.execute(
        '''SELECT * FROM notifications WHERE user_id=? 
           ORDER BY id DESC LIMIT 20''',
        (user['id'],),
        fetch_all=True
    )
    
    # Mark as read
    Database.execute(
        'UPDATE notifications SET is_read=1 WHERE user_id=?',
        (user['id'],)
    )
    
    if not notifications:
        text = "🔔 *الإشعارات*\n\nلا توجد إشعارات جديدة."
    else:
        text = "🔔 *الإشعارات*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for n in notifications[:10]:
            icon = '🔵' if not n['is_read'] else '⚪'
            date = n['created_at'][5:16] if n['created_at'] else ''
            text += f"{icon} *{n['title']}*\n   {n.get('message', '')}\n   _{date}_\n\n"
    
    buttons = [[InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_support(query, user: Dict):
    """Handle support menu"""
    # Check for open ticket
    open_ticket = Database.execute(
        "SELECT * FROM tickets WHERE user_id=? AND status='open' ORDER BY id DESC LIMIT 1",
        (user['id'],),
        fetch_one=True
    )
    
    buttons = []
    
    if open_ticket:
        buttons.append([
            InlineKeyboardButton(f"💬 تذكرة #{open_ticket['id']} (مفتوحة)", 
                               callback_data=f"ticket_{open_ticket['id']}")
        ])
    
    buttons.extend([
        [InlineKeyboardButton('📝 تذكرة جديدة', callback_data='new_ticket')],
        [InlineKeyboardButton('📋 تذاكري السابقة', callback_data='my_tickets')],
        [InlineKeyboardButton('🏠 الرئيسية', callback_data='home')]
    ])
    
    text = """🆘 *الدعم الفني*
━━━━━━━━━━━━━━━━━━━━━

⏰ وقت الرد المتوقع: 5 دقائق - 24 ساعة

📌 للمساعدة السريعة، افتح تذكرة جديدة وسنرد عليك في أقرب وقت ممكن.

💡 نصيحة: اذكر رقم الطلب إن وجد لتسريع المساعدة."""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_new_ticket(query, context: ContextTypes.DEFAULT_TYPE, user: Dict):
    """Handle new ticket creation"""
    context.user_data['waiting_for'] = 'new_ticket'
    
    text = """📝 *فتح تذكرة دعم جديدة*
━━━━━━━━━━━━━━━━━━━━━

اكتب مشكلتك أو استفسارك بالتفصيل.

💡 نصائح لرد أسرع:
• اذكر رقم الطلب إن وجد
• اشرح المشكلة بوضوح
• أرفق صور إن لزم الأمر"""
    
    buttons = [[InlineKeyboardButton('◀️ رجوع', callback_data='support')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_my_tickets(query, user: Dict):
    """Handle my tickets view"""
    tickets = Database.execute(
        '''SELECT * FROM tickets WHERE user_id=? ORDER BY id DESC LIMIT 15''',
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
            status = '🟢' if t['status'] == 'open' else '🔴'
            text += f"{status} تذكرة #{t['id']} - {t.get('subject', 'بدون عنوان')[:25]}\n"
            buttons.append([
                InlineKeyboardButton(f"💬 #{t['id']}", callback_data=f"ticket_{t['id']}")
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
    
    ticket = Database.execute(
        'SELECT * FROM tickets WHERE id=? AND user_id=?',
        (ticket_id, user['id']),
        fetch_one=True
    )
    
    if not ticket:
        await query.answer("❌ التذكرة غير موجودة", show_alert=True)
        return
    
    messages = Database.execute(
        '''SELECT * FROM ticket_messages WHERE ticket_id=? ORDER BY id''',
        (ticket_id,),
        fetch_all=True
    )
    
    status = '🟢 مفتوحة' if ticket['status'] == 'open' else '🔴 مغلقة'
    
    text = f"💬 *تذكرة #{ticket_id}* - {status}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for msg in messages[-10:]:
        sender = '👤 أنت' if msg['sender_type'] == 'user' else '👨‍💼 الدعم'
        time_str = msg['created_at'][11:16] if msg['created_at'] else ''
        text += f"{sender} _{time_str}_:\n{msg['message'][:200]}\n\n"
    
    buttons = []
    if ticket['status'] == 'open':
        buttons.append([InlineKeyboardButton('✍️ إرسال رد', callback_data=f"reply_ticket_{ticket_id}")])
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='my_tickets')])
    
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
    
    text = f"✍️ *الرد على تذكرة #{ticket_id}*\n\nاكتب ردك:"
    
    buttons = [[InlineKeyboardButton('◀️ رجوع', callback_data=f"ticket_{ticket_id}")]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ══════════════════════════════════════════════════════════════
#                    ADMIN HANDLERS
# ══════════════════════════════════════════════════════════════
async def handle_admin_panel(query):
    """Handle admin panel"""
    await query.edit_message_text(
        "⚙️ *لوحة تحكم المدير*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.admin_panel()
    )


async def handle_admin_callbacks(query, context, user_id: int, data: str):
    """Handle admin callbacks"""
    
    if data == 'admin_orders':
        await handle_admin_orders(query)
    
    elif data == 'admin_deposits':
        await handle_admin_deposits(query)
    
    elif data == 'admin_tickets':
        await handle_admin_tickets(query)
    
    elif data == 'admin_users':
        await handle_admin_users(query)
    
    elif data == 'admin_stats':
        await handle_admin_stats(query)
    
    elif data == 'admin_promo':
        await handle_admin_promo(query, context)
    
    elif data == 'admin_broadcast':
        await handle_admin_broadcast(query, context)
    
    elif data == 'admin_new_coupon':
        await handle_admin_new_coupon(query, context)


async def handle_admin_orders(query):
    """Handle admin orders view"""
    orders = Database.execute(
        "SELECT * FROM orders WHERE status='pending' ORDER BY id DESC LIMIT 25",
        fetch_all=True
    )
    
    if not orders:
        await query.edit_message_text(
            "✅ *لا توجد طلبات معلقة*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_button('admin_panel')
        )
        return
    
    text = f"📦 *الطلبات المعلقة* ({len(orders)})\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    buttons = []
    
    for order in orders:
        text += f"`{order['order_id']}` | {order['product_name'][:20]} | {order['total_price']:.0f}ج\n"
        buttons.append([
            InlineKeyboardButton(f"✅ {order['order_id'][:10]}", callback_data=f"execute_{order['order_id']}"),
            InlineKeyboardButton('❌', callback_data=f"cancel_order_{order['order_id']}")
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_deposits(query):
    """Handle admin deposits view"""
    deposits = Database.execute(
        "SELECT * FROM deposits WHERE status='pending' ORDER BY id DESC LIMIT 25",
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
        text += f"{method} #{dep['id']} | {dep['user_id']} | {dep['amount']:.0f}ج\n"
        buttons.append([
            InlineKeyboardButton(f"✅ #{dep['id']}", callback_data=f"approve_dep_{dep['id']}"),
            InlineKeyboardButton('❌', callback_data=f"reject_dep_{dep['id']}")
        ])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_approve(query, context, data: str):
    """Handle admin approval"""
    if data.startswith('approve_dep_'):
        dep_id = int(data.replace('approve_dep_', ''))
        
        deposit = Database.execute(
            "SELECT * FROM deposits WHERE id=? AND status='pending'",
            (dep_id,),
            fetch_one=True
        )
        
        if not deposit:
            await query.answer("❌ الإيداع غير موجود أو تمت معالجته", show_alert=True)
            return
        
        # Calculate fee
        fee = min(deposit['amount'] * Config.DEPOSIT_FEE_PERCENT / 100, Config.DEPOSIT_FEE_MAX)
        final_amount = round(deposit['amount'] - fee, 2)
        
        # Update deposit status
        Database.execute(
            "UPDATE deposits SET status='approved', amount_after_fee=?, reviewed_at=? WHERE id=?",
            (final_amount, datetime.now().isoformat(), dep_id)
        )
        
        # Add balance
        new_balance = UserManager.update_balance(
            deposit['user_id'], final_amount, 'deposit',
            f'DEP_{dep_id}', f'إيداع #{dep_id}', fee
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
    """Handle admin rejection"""
    if data.startswith('reject_dep_'):
        dep_id = int(data.replace('reject_dep_', ''))
        
        deposit = Database.execute(
            'SELECT user_id FROM deposits WHERE id=?',
            (dep_id,),
            fetch_one=True
        )
        
        Database.execute(
            "UPDATE deposits SET status='rejected', reviewed_at=? WHERE id=?",
            (datetime.now().isoformat(), dep_id)
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
    
    order = Database.execute(
        'SELECT * FROM orders WHERE order_id=?',
        (order_id,),
        fetch_one=True
    )
    
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

✏️ أدخل بيانات التسليم:"""
    
    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_orders')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_cancel_order(query, context, data: str):
    """Handle order cancellation"""
    order_id = data.replace('cancel_order_', '')
    
    order = Database.execute(
        'SELECT * FROM orders WHERE order_id=?',
        (order_id,),
        fetch_one=True
    )
    
    if not order or order['status'] != 'pending':
        await query.answer("❌ الطلب غير موجود أو تمت معالجته", show_alert=True)
        return
    
    # Cancel order
    Database.execute(
        "UPDATE orders SET status='cancelled', cancel_reason='تم الإلغاء بواسطة الإدارة', cancelled_at=? WHERE order_id=?",
        (datetime.now().isoformat(), order_id)
    )
    
    # Refund
    UserManager.update_balance(
        order['user_id'], order['total_price'], 'refund',
        order_id, f'استرداد طلب ملغي #{order_id}'
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            order['user_id'],
            f"""❌ *تم إلغاء طلبك*

🆔 `{order_id}`
💰 تم إرجاع {order['total_price']:.0f}ج لرصيدك""",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await query.answer("❌ تم الإلغاء وإرجاع المبلغ", show_alert=True)
    await handle_admin_orders(query)


async def handle_admin_tickets(query):
    """Handle admin tickets view"""
    tickets = Database.execute(
        "SELECT * FROM tickets WHERE status='open' ORDER BY updated_at DESC LIMIT 25",
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
        user = UserManager.get(t['user_id'])
        username = f"@{user['username']}" if user and user.get('username') else f"#{t['user_id']}"
        text += f"#{t['id']} | {username}\n"
        buttons.append([InlineKeyboardButton(f"💬 #{t['id']}", callback_data=f"admin_ticket_{t['id']}")])
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_users(query):
    """Handle admin users view"""
    users = Database.execute(
        'SELECT * FROM users ORDER BY last_active DESC LIMIT 20',
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
    
    buttons.append([InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_stats(query):
    """Handle admin stats view"""
    total_users = Database.execute('SELECT COUNT(*) as c FROM users', fetch_one=True)['c']
    total_orders = Database.execute("SELECT COUNT(*) as c FROM orders WHERE status IN ('done','completed')", fetch_one=True)['c']
    pending_orders = Database.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'", fetch_one=True)['c']
    
    revenue = Database.execute(
        "SELECT SUM(total_price) as s FROM orders WHERE status IN ('done','completed')",
        fetch_one=True
    )['s'] or 0
    
    deposits = Database.execute(
        "SELECT SUM(amount) as s FROM deposits WHERE status='approved'",
        fetch_one=True
    )['s'] or 0
    
    today = datetime.now().date().isoformat()
    
    today_orders = Database.execute(
        f"SELECT COUNT(*) as c, SUM(total_price) as s FROM orders WHERE status IN ('done','completed') AND created_at LIKE '{today}%'",
        fetch_one=True
    )
    
    today_deposits = Database.execute(
        f"SELECT COUNT(*) as c, SUM(amount) as s FROM deposits WHERE status='approved' AND created_at LIKE '{today}%'",
        fetch_one=True
    )
    
    new_users_today = Database.execute(
        f"SELECT COUNT(*) as c FROM users WHERE join_date LIKE '{today}%'",
        fetch_one=True
    )['c']
    
    text = f"""📊 *الإحصائيات*
━━━━━━━━━━━━━━━━━━━━━

👥 *المستخدمين:*
• الإجمالي: {total_users}
• جديد اليوم: {new_users_today}

📦 *الطلبات:*
• مكتملة: {total_orders}
• معلقة: {pending_orders}
• اليوم: {today_orders['c']} ({today_orders['s'] or 0:.0f}ج)

💰 *المالية:*
• إجمالي الإيرادات: {revenue:.0f}ج
• إجمالي الإيداعات: {deposits:.0f}ج
• إيداعات اليوم: {today_deposits['c']} ({today_deposits['s'] or 0:.0f}ج)"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.back_button('admin_panel')
    )


async def handle_admin_promo(query, context):
    """Handle admin promo posting"""
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
    """Handle admin broadcast"""
    context.user_data['waiting_for'] = 'broadcast_message'
    
    total_users = Database.execute(
        'SELECT COUNT(*) as c FROM users WHERE banned=0',
        fetch_one=True
    )['c']
    
    text = f"""📨 *إذاعة لجميع المستخدمين*
━━━━━━━━━━━━━━━━━━━━━

سيتم الإرسال لـ {total_users} مستخدم.

اكتب رسالة الإذاعة:"""
    
    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data='admin_panel')]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_new_coupon(query, context):
    """Handle new coupon creation"""
    buttons = [
        [InlineKeyboardButton('💰 مبلغ ثابت', callback_data='coupon_type_fixed')],
        [InlineKeyboardButton('📊 نسبة مئوية', callback_data='coupon_type_percent')],
        [InlineKeyboardButton('◀️ رجوع', callback_data='admin_panel')]
    ]
    
    await query.edit_message_text(
        "🎟️ *إنشاء كوبون جديد*\n\nاختر نوع الكوبون:",
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

━━━━━━━━━━━━━━━━━━━━━

{level.get('badge', '🥉')} المستوى: {level.get('name', 'برونزي')}
📈 درجة الثقة: {user.get('trust_score', 50)}/100

📅 تاريخ التسجيل: {user['join_date'][:10] if user.get('join_date') else 'N/A'}
🕐 آخر نشاط: {user['last_active'][:16] if user.get('last_active') else 'N/A'}

{'🔴 *محظور*: ' + (user.get('ban_reason') or 'غير محدد') if user['banned'] else '🟢 *نشط*'}"""
    
    ban_text = '🔓 فك الحظر' if user['banned'] else '🔒 حظر'
    ban_callback = f"unban_{user_id}" if user['banned'] else f"ban_{user_id}"
    
    buttons = [
        [
            InlineKeyboardButton('➕ إضافة رصيد', callback_data=f"addbal_{user_id}"),
            InlineKeyboardButton('➖ خصم رصيد', callback_data=f"subbal_{user_id}")
        ],
        [InlineKeyboardButton(ban_text, callback_data=ban_callback)],
        [InlineKeyboardButton('📦 طلباته', callback_data=f"user_orders_{user_id}")],
        [InlineKeyboardButton('◀️ رجوع', callback_data='admin_users')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_admin_ban(query, context, data: str):
    """Handle user ban"""
    user_id = int(data.replace('ban_', ''))
    
    UserManager.ban_user(user_id, 'تم الحظر بواسطة الإدارة', None, query.from_user.id)
    
    try:
        await context.bot.send_message(
            user_id,
            "🚫 *تم حظرك من استخدام البوت*\n\nتواصل مع الدعم إذا كنت تعتقد أن هذا خطأ.",
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
    """Handle add balance to user"""
    user_id = int(data.replace('addbal_', '').replace('subbal_', ''))
    action = 'add' if 'addbal_' in data else 'sub'
    
    context.user_data['balance_target_user'] = user_id
    context.user_data['balance_action'] = action
    context.user_data['waiting_for'] = 'admin_balance_amount'
    
    action_text = 'إضافة' if action == 'add' else 'خصم'
    
    text = f"""💰 *{action_text} رصيد للمستخدم {user_id}*

أدخل المبلغ:"""
    
    buttons = [[InlineKeyboardButton('◀️ إلغاء', callback_data=f"user_{user_id}")]]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ══════════════════════════════════════════════════════════════
#                     MESSAGE HANDLER
# ══════════════════════════════════════════════════════════════
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
    
    # Get or create user
    user = UserManager.create_or_update(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    waiting_for = context.user_data.get('waiting_for')
    
    try:
        # ══════════════════════════════════════════════════════════
        #                    PRODUCT INPUT
        # ══════════════════════════════════════════════════════════
        if waiting_for == 'product_input':
            await process_product_input(update, context, user, text)
        
        # ══════════════════════════════════════════════════════════
        #                    COUPON CODE
        # ══════════════════════════════════════════════════════════
        elif waiting_for == 'coupon_code':
            await process_coupon_code(update, context, user, text)
        
        # ══════════════════════════════════════════════════════════
        #                    NEW TICKET
        # ══════════════════════════════════════════════════════════
        elif waiting_for == 'new_ticket':
            await process_new_ticket(update, context, user, text)
        
        # ══════════════════════════════════════════════════════════
        #                    TICKET REPLY
        # ══════════════════════════════════════════════════════════
        elif waiting_for == 'ticket_reply':
            await process_ticket_reply(update, context, user, text)
        
        # ══════════════════════════════════════════════════════════
        #                    ADMIN HANDLERS
        # ══════════════════════════════════════════════════════════
        elif user_id in Config.ADMIN_IDS:
            
            if waiting_for == 'delivery_data':
                await process_admin_delivery(update, context, text)
            
            elif waiting_for == 'admin_balance_amount':
                await process_admin_balance(update, context, text)
            
            elif waiting_for == 'broadcast_message':
                await process_admin_broadcast(update, context, text)
            
            elif waiting_for == 'admin_ticket_reply':
                await process_admin_ticket_reply(update, context, text)
            
            elif text.lower() == '/admin':
                await update.message.reply_text(
                    "⚙️ *لوحة تحكم المدير*",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=Keyboards.admin_panel()
                )
    
    except Exception as e:
        logger.error(f"Message handler error: {e}", exc_info=True)
        context.user_data.pop('waiting_for', None)


async def process_product_input(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                user: Dict, text: str):
    """Process product input data"""
    pending = Database.execute(
        'SELECT * FROM pending_inputs WHERE user_id=?',
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
            Database.execute('DELETE FROM pending_inputs WHERE user_id=?', (user['id'],))
            context.user_data.pop('waiting_for', None)
            await update.message.reply_text(
                "⏰ انتهت صلاحية الجلسة، حاول مرة أخرى",
                reply_markup=Keyboards.main_menu(user['id'])
            )
            return
    
    # Get product
    product = Database.execute(
        'SELECT * FROM products WHERE item_key=? AND is_active=1',
        (pending['item_key'],),
        fetch_one=True
    )
    
    if not product:
        Database.execute('DELETE FROM pending_inputs WHERE user_id=?', (user['id'],))
        context.user_data.pop('waiting_for', None)
        await update.message.reply_text(
            "❌ المنتج غير متوفر",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    required_fields = json.loads(product['required_fields']) if product['required_fields'] else []
    collected_data = json.loads(pending['collected_data']) if pending['collected_data'] else {}
    current_step = pending['current_step']
    
    # Validate input
    current_field = required_fields[current_step]
    
    # Basic validation
    if current_field in ['player_id', 'pubg_id', 'ml_id']:
        if not text.isdigit() or len(text) < 5 or len(text) > 15:
            await update.message.reply_text(
                "❌ *معرف غير صحيح!*\n\nأدخل معرف صحيح (أرقام فقط، 5-15 رقم)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    elif current_field == 'zone_id':
        if not text.isdigit() or len(text) < 3 or len(text) > 6:
            await update.message.reply_text(
                "❌ *Zone ID غير صحيح!*\n\nأدخل Zone ID صحيح (أرقام فقط)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Save input
    collected_data[current_field] = text
    next_step = current_step + 1
    
    if next_step < len(required_fields):
        # More fields needed
        Database.execute(
            'UPDATE pending_inputs SET current_step=?, collected_data=? WHERE user_id=?',
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
        # All fields collected - complete purchase
        Database.execute('DELETE FROM pending_inputs WHERE user_id=?', (user['id'],))
        context.user_data.pop('waiting_for', None)
        
        # Check balance again
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
        await complete_purchase_from_message(update, context, user, product, collected_data)


async def complete_purchase_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                         user: Dict, product: Dict, input_data: Dict):
    """Complete purchase from message handler"""
    price = product['price']
    
    # Calculate cashback
    cashback_percent = product.get('cashback_percent', 3)
    level_info = UserManager.get_level_info(user['id'])
    level_bonus = level_info.get('current', {}).get('cashback_bonus', 0) if level_info.get('current') else 0
    total_cashback_percent = cashback_percent + level_bonus
    cashback = price * total_cashback_percent / 100
    
    # Deduct balance
    new_balance = UserManager.update_balance(
        user['id'], -price, 'purchase',
        product['item_key'], f"شراء {product['name']}"
    )
    
    # Add cashback
    if cashback > 0:
        UserManager.update_balance(
            user['id'], cashback, 'cashback',
            product['item_key'], f"كاش باك {product['name']}"
        )
        Database.execute(
            'UPDATE users SET cashback_total=cashback_total+? WHERE id=?',
            (cashback, user['id'])
        )
    
    # Generate order ID
    order_id = f"XL{int(time.time()) % 100000}{random.randint(100, 999)}"
    
    # Create order
    Database.execute(
        '''INSERT INTO orders(order_id, user_id, product_key, product_name, unit_price,
           total_price, cashback_amount, input_data, created_at) VALUES(?,?,?,?,?,?,?,?,?)''',
        (order_id, user['id'], product['item_key'], product['name'], price,
         price, cashback, json.dumps(input_data, ensure_ascii=False),
         datetime.now().isoformat())
    )
    
    # Update product stats
    Database.execute(
        'UPDATE products SET sold_count=sold_count+1 WHERE item_key=?',
        (product['item_key'],)
    )
    
    if product['stock'] > 0:
        Database.execute(
            'UPDATE products SET stock=stock-1 WHERE item_key=?',
            (product['item_key'],)
        )
    
    # Notify admins
    input_text = '\n'.join([f"• {k}: `{v}`" for k, v in input_data.items()]) if input_data else 'لا توجد'
    
    admin_msg = f"""🛒 *طلب جديد!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
👤 المستخدم: `{user['id']}` @{user.get('username', 'N/A')}

🛍️ المنتج: {product['name']}
💰 السعر: {price:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

📋 *بيانات الشحن:*
{input_text}"""
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('✅ تنفيذ', callback_data=f"execute_{order_id}"),
            InlineKeyboardButton('❌ إلغاء', callback_data=f"cancel_order_{order_id}")
        ]
    ])
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                admin_msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=admin_buttons
            )
        except:
            pass
    
    # Success message
    text = f"""✅ *تم تقديم الطلب بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
🛍️ المنتج: {product['name']}
💰 السعر: {price:.0f}ج
💎 كاش باك: +{cashback:.0f}ج

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك المتبقي: *{new_balance + cashback:.0f}ج*

⏳ سيتم تنفيذ طلبك قريباً!"""
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )
    
    logger.info(f"Order {order_id} created by user {user['id']}")


async def process_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              user: Dict, text: str):
    """Process coupon code"""
    context.user_data.pop('waiting_for', None)
    
    code = text.upper().strip()
    
    coupon = Database.execute(
        'SELECT * FROM coupons WHERE code=? AND is_active=1',
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
    
    # Check max usage
    if coupon['max_usage'] and coupon['usage_count'] >= coupon['max_usage']:
        await update.message.reply_text(
            "❌ *الكود وصل للحد الأقصى للاستخدام!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Check user usage
    user_usage = Database.execute(
        'SELECT COUNT(*) as c FROM coupon_usage WHERE coupon_code=? AND user_id=?',
        (code, user['id']),
        fetch_one=True
    )['c']
    
    max_per_user = coupon.get('max_per_user', 1)
    if user_usage >= max_per_user:
        await update.message.reply_text(
            "❌ *لقد استخدمت هذا الكود من قبل!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Apply coupon
    if coupon['type'] == 'percent':
        bonus = min(user['balance'] * coupon['value'] / 100, coupon.get('max_discount', 100) or 100)
    else:
        bonus = coupon['value']
    
    # Add bonus
    new_balance = UserManager.update_balance(
        user['id'], bonus, 'coupon',
        code, f"كوبون {code}"
    )
    
    # Record usage
    Database.execute('UPDATE coupons SET usage_count=usage_count+1 WHERE code=?', (code,))
    Database.execute(
        'INSERT INTO coupon_usage(coupon_code, user_id, discount_amount, used_at) VALUES(?,?,?,?)',
        (code, user['id'], bonus, datetime.now().isoformat())
    )
    
    await update.message.reply_text(
        f"""🎉 *تم تفعيل الكوبون بنجاح!*

💰 حصلت على: *+{bonus:.0f}ج*
💳 رصيدك الجديد: *{new_balance:.0f}ج*""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )


async def process_new_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user: Dict, text: str):
    """Process new ticket creation"""
    context.user_data.pop('waiting_for', None)
    
    # Create ticket
    ticket_id = Database.execute(
        '''INSERT INTO tickets(user_id, subject, created_at, updated_at) VALUES(?,?,?,?)''',
        (user['id'], text[:50], datetime.now().isoformat(), datetime.now().isoformat())
    )
    
    # Add first message
    Database.execute(
        '''INSERT INTO ticket_messages(ticket_id, sender_type, sender_id, message, created_at)
           VALUES(?,?,?,?,?)''',
        (ticket_id, 'user', user['id'], text, datetime.now().isoformat())
    )
    
    # Notify admins
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"""🎫 *تذكرة جديدة #{ticket_id}*
━━━━━━━━━━━━━━━━━━━━━

👤 المستخدم: `{user['id']}` @{user.get('username', 'N/A')}

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


async def process_ticket_reply(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user: Dict, text: str):
    """Process ticket reply"""
    ticket_id = context.user_data.pop('ticket_id', None)
    context.user_data.pop('waiting_for', None)
    
    if not ticket_id:
        await update.message.reply_text("❌ خطأ", reply_markup=Keyboards.main_menu(user['id']))
        return
    
    # Add message
    Database.execute(
        '''INSERT INTO ticket_messages(ticket_id, sender_type, sender_id, message, created_at)
           VALUES(?,?,?,?,?)''',
        (ticket_id, 'user', user['id'], text, datetime.now().isoformat())
    )
    
    Database.execute(
        'UPDATE tickets SET updated_at=? WHERE id=?',
        (datetime.now().isoformat(), ticket_id)
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


async def process_admin_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process admin delivery data"""
    order_id = context.user_data.pop('admin_execute_order', None)
    context.user_data.pop('waiting_for', None)
    
    if not order_id:
        await update.message.reply_text("❌ خطأ", reply_markup=Keyboards.admin_panel())
        return
    
    order = Database.execute(
        'SELECT * FROM orders WHERE order_id=?',
        (order_id,),
        fetch_one=True
    )
    
    if not order or order['status'] != 'pending':
        await update.message.reply_text("❌ الطلب غير موجود أو تمت معالجته", reply_markup=Keyboards.admin_panel())
        return
    
    # Update order
    Database.execute(
        "UPDATE orders SET status='done', delivery_data=?, completed_at=? WHERE order_id=?",
        (text, datetime.now().isoformat(), order_id)
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            order['user_id'],
            f"""✅ *تم تنفيذ طلبك!*
━━━━━━━━━━━━━━━━━━━━━

🆔 رقم الطلب: `{order_id}`
🛍️ المنتج: {order['product_name']}

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
    
    # Add notification
    UserManager.add_notification(
        order['user_id'],
        f"✅ تم تنفيذ طلبك #{order_id}",
        "تفقد تفاصيل الطلب للحصول على بيانات التسليم",
        'order_completed'
    )
    
    await update.message.reply_text(
        f"✅ تم تنفيذ الطلب {order_id}",
        reply_markup=Keyboards.admin_panel()
    )
    
    logger.info(f"Order {order_id} completed by admin {update.effective_user.id}")


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
            target_user, amount, 'admin_adjustment',
            f'ADM_{update.effective_user.id}',
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
    
    users = Database.execute(
        'SELECT id FROM users WHERE banned=0',
        fetch_all=True
    )
    
    status_msg = await update.message.reply_text(f"📨 جاري الإرسال لـ {len(users)} مستخدم...")
    
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
        
        # Update progress every 30 users
        if (i + 1) % 30 == 0:
            try:
                await status_msg.edit_text(f"📨 {i + 1}/{len(users)}...")
            except:
                pass
        
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(f"✅ تم الإرسال!\n\nنجح: {success}\nفشل: {failed}")

# ══════════════════════════════════════════════════════════════
#                     PHOTO HANDLER
# ══════════════════════════════════════════════════════════════
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages (deposits)"""
    if not update.message or not update.message.photo:
        return
    
    user_id = update.effective_user.id
    
    # Check ban
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
    
    # Get user
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
        image_b64 = base64.b64encode(image_bytes).decode()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        # Check duplicate
        existing = Database.execute(
            'SELECT * FROM image_hashes WHERE hash=?',
            (image_hash,),
            fetch_one=True
        )
        
        if existing:
            await processing_msg.edit_text(
                "🚫 *هذه الصورة مستخدمة من قبل!*\n\nأرسل صورة إيصال جديد.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log fraud attempt
            Database.execute(
                '''INSERT INTO fraud_records(user_id, type, description, created_at)
                   VALUES(?,?,?,?)''',
                (user_id, 'duplicate_image', f'Hash: {image_hash[:16]}', datetime.now().isoformat())
            )
            return
        
        # Detect payment type
        await processing_msg.edit_text(
            "🔍 *جاري التعرف على نوع الدفع...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        payment_type = AIService.detect_payment_type(image_b64)
        logger.info(f"Payment type detected for {user_id}: {payment_type}")
        
        if payment_type == 'VODAFONE':
            await process_vodafone_deposit(processing_msg, context, user, image_bytes, image_b64, image_hash)
        
        elif payment_type == 'USDT':
            await process_usdt_deposit(processing_msg, context, user, image_bytes, image_b64, image_hash)
        
        else:
            await processing_msg.edit_text(
                """❓ *لم نتمكن من التعرف على نوع الدفع*

━━━━━━━━━━━━━━━━━━━━━

📌 *الطرق المدعومة:*
• 📱 فودافون كاش
• 💎 USDT (BEP20)

━━━━━━━━━━━━━━━━━━━━━

أرسل صورة واضحة للإيصال.""",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=Keyboards.main_menu(user_id)
            )
    
    except Exception as e:
        logger.error(f"Photo processing error: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ حدث خطأ أثناء معالجة الصورة، حاول مرة أخرى",
            reply_markup=Keyboards.main_menu(user_id)
        )


async def process_vodafone_deposit(processing_msg, context, user: Dict, 
                                   image_bytes: bytes, image_b64: str, image_hash: str):
    """Process Vodafone Cash deposit"""
    await processing_msg.edit_text(
        "📱 *جاري تحليل إيصال فودافون كاش...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Analyze with AI
    result = AIService.analyze_vodafone_receipt(image_b64, Config.VODAFONE_NUMBER)
    logger.info(f"Vodafone analysis for {user['id']}: {result}")
    
    if not result['valid']:
        error_msg = result.get('error') or 'لم نتمكن من التحقق من الإيصال'
        
        await processing_msg.edit_text(
            f"""❌ *فشل التحقق*

{error_msg}

━━━━━━━━━━━━━━━━━━━━━

💡 *تأكد من:*
• وضوح الصورة
• أن الإيصال يحتوي على رقم المستلم: `{Config.VODAFONE_NUMBER}`
• أن الإيصال حديث""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    amount = result['amount']
    
    # Validate amount
    if amount < Config.MIN_DEPOSIT:
        await processing_msg.edit_text(
            f"❌ الحد الأدنى للإيداع {Config.MIN_DEPOSIT}ج",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    if amount > Config.MAX_DEPOSIT:
        await processing_msg.edit_text(
            f"❌ الحد الأقصى للإيداع {Config.MAX_DEPOSIT}ج",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Save image hash
    Database.execute(
        'INSERT INTO image_hashes(hash, user_id, type, amount, created_at) VALUES(?,?,?,?,?)',
        (image_hash, user['id'], 'vodafone', amount, datetime.now().isoformat())
    )
    
    # Calculate fee
    fee = min(amount * Config.DEPOSIT_FEE_PERCENT / 100, Config.DEPOSIT_FEE_MAX)
    final_amount = round(amount - fee, 2)
    
    # Check if auto-approve
    confidence = result.get('confidence', 0)
    auto_approve = amount <= Config.MANUAL_VERIFY_THRESHOLD and confidence >= 0.8
    
    if auto_approve:
        # Auto approve
        dep_id = Database.execute(
            '''INSERT INTO deposits(user_id, amount, amount_after_fee, payment_method, 
               image_hash, status, ai_analysis, ai_confidence, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)''',
            (user['id'], amount, final_amount, 'vodafone', image_hash, 'approved',
             json.dumps(result), confidence, datetime.now().isoformat())
        )
        
        new_balance = UserManager.update_balance(
            user['id'], final_amount, 'deposit',
            f'VF_{dep_id}', f'إيداع فودافون #{dep_id}', fee
        )
        
        # Notify admins
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"📱 *إيداع تلقائي*\n\n👤 `{user['id']}`\n💵 {amount:.0f}ج ➜ {final_amount:.0f}ج\n🎯 ثقة: {confidence:.0%}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        await processing_msg.edit_text(
            f"""✅ *تم إيداع رصيدك بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

💵 المبلغ: {amount:.0f}ج
💸 العمولة: {fee:.1f}ج
💰 الصافي: *{final_amount:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك الجديد: *{new_balance:.0f}ج*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        
        logger.info(f"Auto-approved deposit {dep_id} for user {user['id']}: {amount}")
    
    else:
        # Manual review required
        dep_id = Database.execute(
            '''INSERT INTO deposits(user_id, amount, amount_after_fee, payment_method, 
               image_hash, status, ai_analysis, ai_confidence, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)''',
            (user['id'], amount, final_amount, 'vodafone', image_hash, 'pending',
             json.dumps(result), confidence, datetime.now().isoformat())
        )
        
        # Notify admins with image
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_photo(
                    admin_id,
                    photo=io.BytesIO(image_bytes),
                    caption=f"""📱 *إيداع فودافون - مراجعة*
━━━━━━━━━━━━━━━━━━━━━

🆔 #{dep_id}
👤 `{user['id']}` @{user.get('username', 'N/A')}
💵 *{amount:.0f}ج*
🎯 ثقة AI: {confidence:.0%}

━━━━━━━━━━━━━━━━━━━━━

📊 *المستخدم:*
• الرصيد: {user['balance']:.0f}ج
• الطلبات: {user['total_orders']}
• الإيداعات: {user['total_deposits']:.0f}ج""",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(f"✅ قبول ({amount:.0f}ج)", callback_data=f"approve_dep_{dep_id}"),
                            InlineKeyboardButton('❌ رفض', callback_data=f"reject_dep_{dep_id}")
                        ]
                    ])
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        await processing_msg.edit_text(
            f"""⏳ *جاري مراجعة الإيداع*
━━━━━━━━━━━━━━━━━━━━━

💵 المبلغ: *{amount:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

⚠️ المبلغ يتجاوز {Config.MANUAL_VERIFY_THRESHOLD}ج أو يحتاج مراجعة.
⏰ وقت المراجعة: 5-30 دقيقة

سنُعلمك فور الموافقة! 🔔""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )


async def process_usdt_deposit(processing_msg, context, user: Dict,
                               image_bytes: bytes, image_b64: str, image_hash: str):
    """Process USDT deposit"""
    await processing_msg.edit_text(
        "💎 *جاري تحليل معاملة USDT...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Analyze with AI
    result = AIService.analyze_usdt_transaction(image_b64)
    logger.info(f"USDT analysis for {user['id']}: {result}")
    
    txid = result.get('txid')
    
    if not txid:
        await processing_msg.edit_text(
            """❌ *لم يتم العثور على TXID صحيح*

━━━━━━━━━━━━━━━━━━━━━

💡 *تأكد من:*
• وضوح الصورة
• ظهور Transaction Hash كاملاً
• أن المعاملة على شبكة BSC (BEP20)""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Check if TXID used
    if BSCScanAPI.is_txid_used(txid):
        await processing_msg.edit_text(
            "🚫 *هذا TXID مستخدم من قبل!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        
        Database.execute(
            '''INSERT INTO fraud_records(user_id, type, description, created_at)
               VALUES(?,?,?,?)''',
            (user['id'], 'duplicate_txid', f'TXID: {txid[:20]}', datetime.now().isoformat())
        )
        return
    
    # Verify on blockchain
    await processing_msg.edit_text(
        "🔗 *جاري التحقق من البلوكتشين...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    verification = BSCScanAPI.verify_transaction(txid, Config.USDT_WALLET)
    
    if not verification['valid']:
        error = verification.get('error', 'فشل التحقق')
        await processing_msg.edit_text(
            f"""❌ *فشل التحقق من البلوكتشين*

{error}

━━━━━━━━━━━━━━━━━━━━━

💡 تأكد من:
• أن المعاملة مؤكدة (Confirmed)
• أن العنوان المستلم صحيح
• أن الشبكة هي BSC (BEP20)""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    amount_usdt = verification['amount']
    amount_egp = round(amount_usdt * Config.USDT_TO_EGP_RATE, 2)
    
    # Validate amount
    if amount_egp < Config.MIN_DEPOSIT:
        await processing_msg.edit_text(
            f"❌ المبلغ أقل من الحد الأدنى ({Config.MIN_DEPOSIT}ج)",
            reply_markup=Keyboards.main_menu(user['id'])
        )
        return
    
    # Save records
    Database.execute(
        'INSERT INTO image_hashes(hash, user_id, type, amount, created_at) VALUES(?,?,?,?,?)',
        (image_hash, user['id'], 'usdt', amount_usdt, datetime.now().isoformat())
    )
    BSCScanAPI.mark_txid_used(txid, user['id'], amount_usdt)
    
    # Calculate fee
    fee = min(amount_egp * Config.DEPOSIT_FEE_PERCENT / 100, Config.DEPOSIT_FEE_MAX)
    final_amount = round(amount_egp - fee, 2)
    
    # Auto approve (blockchain verified)
    dep_id = Database.execute(
        '''INSERT INTO deposits(user_id, amount, amount_after_fee, payment_method, 
           image_hash, txid, status, created_at)
           VALUES(?,?,?,?,?,?,?,?)''',
        (user['id'], amount_egp, final_amount, 'usdt', image_hash, txid, 
         'approved', datetime.now().isoformat())
    )
    
    new_balance = UserManager.update_balance(
        user['id'], final_amount, 'deposit',
        f'USDT_{txid[:16]}', f'إيداع USDT #{dep_id}', fee
    )
    
    # Notify admins
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💎 *إيداع USDT ✓*\n\n👤 `{user['id']}`\n💵 {amount_usdt} USDT = {amount_egp:.0f}ج\n🔗 `{txid[:30]}...`",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    
    await processing_msg.edit_text(
        f"""✅ *تم إيداع USDT بنجاح!*
━━━━━━━━━━━━━━━━━━━━━

💎 المبلغ: {amount_usdt} USDT
💵 = {amount_egp:.0f}ج
💸 العمولة: {fee:.1f}ج
💰 الصافي: *{final_amount:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

💳 رصيدك الجديد: *{new_balance:.0f}ج*

━━━━━━━━━━━━━━━━━━━━━

🔗 TXID: `{txid[:30]}...`""",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboards.main_menu(user['id'])
    )
    
    logger.info(f"USDT deposit {dep_id} for user {user['id']}: {amount_usdt} USDT")

# ══════════════════════════════════════════════════════════════
#                    ERROR HANDLER
# ══════════════════════════════════════════════════════════════
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
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

# ══════════════════════════════════════════════════════════════
#                    STARTUP & MAIN
# ══════════════════════════════════════════════════════════════
async def post_init(application: Application):
    """Post initialization"""
    global state
    
    bot_info = await application.bot.get_me()
    state.bot_username = bot_info.username
    
    logger.info(f"🤖 Bot started: @{state.bot_username}")
    
    # Set bot commands
    commands = [
        BotCommand("start", "بدء البوت"),
        BotCommand("help", "المساعدة"),
    ]
    await application.bot.set_my_commands(commands)
    
    # Start promo scheduler
    asyncio.create_task(promo_scheduler(application))
    
    logger.info("✅ All systems initialized")


def main():
    """Main entry point"""
    print("═" * 60)
    print("🔥 XLERO SHOP V6 ULTIMATE 🔥")
    print("═" * 60)
    
    # Initialize database
    Database.initialize()
    
    # Build application
    application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_error_handler(error_handler)
    
    # Print stats
    products = Database.execute('SELECT COUNT(*) as c FROM products WHERE is_active=1', fetch_one=True)['c']
    users = Database.execute('SELECT COUNT(*) as c FROM users', fetch_one=True)['c']
    orders = Database.execute("SELECT COUNT(*) as c FROM orders WHERE status IN ('done','completed')", fetch_one=True)['c']
    
    print(f"📦 Products: {products}")
    print(f"👥 Users: {users}")
    print(f"📋 Orders: {orders}")
    print(f"📢 Promo Interval: {Config.PROMO_INTERVAL_SECONDS // 60} min")
    print("═" * 60)
    print("🚀 Bot is running...")
    print("═" * 60)
    
    # Run
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()