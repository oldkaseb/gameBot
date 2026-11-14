# -*- coding: utf-8 -*-
"""social_platform.py — موتور کامل پلتفرم اجتماعی راینو:
- لول ثروت (Wealth) و لول جذابیت (Charm) تا ۵۰
- لول اتاق صوتی تا ۵۰ (شروع لول ۲ از ۲۰,۰۰۰ سکه) + باز شدن تعداد مایک با لول روم
- ارسال گیفت به یک یا چند شخص مشخص + انیمیشن تمام‌صفحه + شناورسازی گیفت‌های دریافتی روی کارت پروفایل
- مدیریت ادمین‌های روم + پاپ‌آپ صندلی (قفل/باز کردن، نشستن، دعوت کاربر به مایک) + لیست شنوندگان بدون مایک
- چت خصوصی (PV) داخل مینی‌اپ با پشتیبانی از ویس، پس‌زمینه سفارشی، پک ایموجی پریمیوم و لول ارتباط
- سیستم روابط: ۱ ازدواج (Marriage) + تا ۵ رفیق (Bestie) + خط رابط متحرک روی مایک‌های مجاور بدون تداخل چپ و راست
- پروکسی رندر ایموجی‌های پریمیوم تلگرام (getCustomEmojiStickers) و دستور «ریست لول و موجودی»
"""

import asyncio
import json
import os
import random
import time
from aiogram import Bot
from aiogram.types import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from database import db
from utils.premium import primary, success, danger, kb

OWNER_IDS = {7662192190, 6041119040}
STARS_TO_COINS_RATE = 100

STAR_TOPUP_PACKS = [
    {"id": "topup_50",   "stars": 50,   "bonus_stars": 0,   "title": "شارژ ۵۰ استارز (۵,۰۰۰ سکه)"},
    {"id": "topup_150",  "stars": 150,  "bonus_stars": 15,  "title": "شارژ ۱۵۰ استارز (+۱۵ هدیه)"},
    {"id": "topup_400",  "stars": 400,  "bonus_stars": 50,  "title": "شارژ ۴۰۰ استارز (+۵۰ هدیه)"},
    {"id": "topup_1000", "stars": 1000, "bonus_stars": 150, "title": "شارژ ۱۰۰۰ استارز (+۱۵۰ هدیه)"},
]

SUB_TIERS = {
    "free": {
        "id": "free",
        "title": "کاربر عادی (Free)",
        "badge": "",
        "stars": 0,
        "coins": 0,
        "days": 0,
        "can_lock_room": False,
        "stealth_visit": False,
        "ghost_join": False,
        "custom_badge_allowed": False,
        "perks": ["ساخت اتاق صوتی عمومی", "رنگ‌های ساده کارت پروفایل"],
    },
    "pro": {
        "id": "pro",
        "title": "اشتراک پرو (PRO)",
        "badge": "🥈 PRO",
        "stars": 80,
        "coins": 8000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": False,
        "ghost_join": False,
        "custom_badge_allowed": True,
        "perks": [
            "✨ قابلیت ست کردن ایموجی پریمیوم متحرک دلخواه جلوی نام",
            "🔒 قابلیت قفل کردن و رمزگذاری اتاق صوتی",
            "🎨 باز شدن رنگ‌های طلایی و نقره‌ای کارت پروفایل",
        ],
    },
    "plus": {
        "id": "plus",
        "title": "اشتراک پلاس (PLUS)",
        "badge": "🥇 PLUS",
        "stars": 180,
        "coins": 18000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": True,
        "ghost_join": False,
        "custom_badge_allowed": True,
        "perks": [
            "✨ قابلیت ست کردن ایموجی پریمیوم متحرک دلخواه جلوی نام",
            "🕵️ بازدید مخفی پروفایل دیگران (ثبت نشدن در لیست بازدیدکنندگان)",
            "🔒 قفل اتاق صوتی + رنگ‌های نئونی و شفق قطبی پروفایل",
        ],
    },
    "ultra": {
        "id": "ultra",
        "title": "اشتراک الترا (ULTRA)",
        "badge": "💎 ULTRA",
        "stars": 350,
        "coins": 35000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": True,
        "ghost_join": True,
        "custom_badge_allowed": True,
        "perks": [
            "✨ قابلیت ست کردن ایموجی پریمیوم متحرک دلخواه جلوی نام",
            "👻 ورود روح (Ghost Mode) به اتاق‌های صوتی باز بدون دیده‌شدن",
            "🕵️ بازدید مخفی پروفایل + ۶ تم اشرافی و کهکشانی انحصاری ULTRA",
        ],
    },
}

# ─── تم‌ها و رنگ‌های کارت پروفایل (به همراه رنگ‌های خاص اشتراک ULTRA) ───
PROFILE_THEMES = [
    {"id": "slate",       "title": "سرمه‌ای کلاسیک",          "tier": "free",  "glow": "#64748b", "css": "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"},
    {"id": "blue",        "title": "آبی تلگرامی",             "tier": "free",  "glow": "#60a5fa", "css": "linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%)"},
    {"id": "emerald",     "title": "سبز زمردی",               "tier": "free",  "glow": "#34d399", "css": "linear-gradient(135deg, #047857 0%, #064e3b 100%)"},
    {"id": "purple",      "title": "بنفش شب",                 "tier": "free",  "glow": "#c084fc", "css": "linear-gradient(135deg, #6d28d9 0%, #3b0764 100%)"},
    {"id": "rose",        "title": "سرخ تیره",                "tier": "free",  "glow": "#fb7185", "css": "linear-gradient(135deg, #be123c 0%, #4c0519 100%)"},
    {"id": "silver",      "title": "نقره‌ای متالیک (PRO)",    "tier": "pro",   "glow": "#f8fafc", "css": "linear-gradient(135deg, #cbd5e1 0%, #475569 55%, #0f172a 100%)"},
    {"id": "gold",        "title": "طلایی سلطنتی (PRO)",      "tier": "pro",   "glow": "#fde047", "css": "linear-gradient(135deg, #fbbf24 0%, #b45309 55%, #451a03 100%)"},
    {"id": "neon",        "title": "نئون سایبرپانک (PLUS)",   "tier": "plus",  "glow": "#22d3ee", "css": "linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #06b6d4 100%)"},
    {"id": "aurora",      "title": "شفق قطبی (PLUS)",         "tier": "plus",  "glow": "#34d399", "css": "linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #6366f1 100%)"},
    {"id": "royal",       "title": "امپراتور الماس (ULTRA)",   "tier": "ultra", "glow": "#fef08a", "css": "linear-gradient(135deg, #fbbf24 0%, #e11d48 45%, #4c1d95 100%)"},
    {"id": "abyss",       "title": "کهکشان تاریک (ULTRA)",     "tier": "ultra", "glow": "#e879f9", "css": "radial-gradient(circle at top right, #c084fc, #3b0764 55%, #090514 100%)"},
    {"id": "blood_moon",  "title": "ماه خونین دوزخی (ULTRA)",  "tier": "ultra", "glow": "#ff4d6d", "css": "radial-gradient(circle at 20% 20%, #ff0a54 0%, #7209b7 55%, #10002b 100%)"},
    {"id": "emerald_vip", "title": "زمرد امپراتوری (ULTRA)",   "tier": "ultra", "glow": "#6ee7b7", "css": "linear-gradient(135deg, #a7f3d0 0%, #059669 35%, #064e3b 75%, #022c22 100%)"},
    {"id": "supernova",   "title": "ابرنواختر طلایی (ULTRA)",  "tier": "ultra", "glow": "#fde68a", "css": "radial-gradient(circle at 80% 15%, #fde047 0%, #ea580c 42%, #7c2d12 75%, #090514 100%)"},
    {"id": "holo_matrix", "title": "ماتریکس هولوگرام (ULTRA)", "tier": "ultra", "glow": "#67e8f9", "css": "linear-gradient(135deg, #00f5d4 0%, #7b2cbf 48%, #ff007f 100%)"},
]

TIER_RANK = {"free": 0, "pro": 1, "plus": 2, "ultra": 3}

live_rooms_runtime: dict[int, dict] = {}
bombs_sessions: dict[int, dict] = {}
emoji_file_cache: dict[str, tuple[bytes, str]] = {}

recent_big_wins: list[dict] = [
    {"name": "RHINO VIP", "game": "CRASH", "win": 14500, "mult": "4.5x", "time": "1m ago"},
    {"name": "KING_77",   "game": "BOMBS", "win": 8200,  "mult": "3.2x", "time": "2m ago"},
    {"name": "SARA_PRO",  "game": "PICKAXE", "win": 6000, "mult": "6.0x", "time": "3m ago"},
]


# ─── توابع محاسبه لول ثروت، جذابیت و لول اتاق صوتی (تا لول ۵۰) ───
def calc_user_level_50(points: int) -> tuple[int, int, int]:
    """محاسبه لول کاربر از ۱ تا ۵۰ بر اساس امتیاز (سکه ارسالی برای ثروت / سکه دریافتی برای جذابیت)"""
    pts = max(0, int(points or 0))
    lvl = 1
    for l in range(2, 51):
        req = 500 * (l - 1) * l // 2
        if pts >= req:
            lvl = l
        else:
            prev_req = 500 * (l - 2) * (l - 1) // 2
            pct = min(100, int(((pts - prev_req) / max(1, req - prev_req)) * 100))
            return lvl, pct, req
    return 50, 100, 500 * 49 * 50 // 2


def calc_room_level_50(total_gifts: int) -> tuple[int, int, int]:
    """
    لول اتاق صوتی از ۱ تا ۵۰:
    - لول ۲ دقیقاً با ۲۰,۰۰۰ سکه باز می‌شود.
    - هر لول بعدی افزایش تصاعدی دارد: req(L) = 20000 * L * (L - 1) // 2
      (لول ۲: ۲۰,۰۰۰ | لول ۳: ۶۰,۰۰۰ | لول ۴: ۱۲۰,۰۰۰ | ... تا لول ۵۰)
    """
    pts = max(0, int(total_gifts or 0))
    lvl = 1
    for l in range(2, 51):
        req = 20000 * l * (l - 1) // 2
        if pts >= req:
            lvl = l
        else:
            prev_req = 20000 * (l - 1) * (l - 2) // 2
            pct = min(100, int(((pts - prev_req) / max(1, req - prev_req)) * 100))
            return lvl, pct, req
    return 50, 100, 20000 * 50 * 49 // 2


def max_mics_for_room_level(room_lvl: int) -> int:
    """هر چقدر لول‌های بیشتری در روم باز شود، سقف تعداد مایک‌های قابل انتخاب بیشتر می‌شود"""
    if room_lvl >= 40:
        return 36
    if room_lvl >= 30:
        return 30
    if room_lvl >= 20:
        return 24
    if room_lvl >= 12:
        return 20
    if room_lvl >= 8:
        return 17
    if room_lvl >= 5:
        return 15
    if room_lvl >= 3:
        return 12
    if room_lvl >= 2:
        return 10
    return 8


def allowed_mic_options_for_level(room_lvl: int) -> list[int]:
    limit = max_mics_for_room_level(room_lvl)
    all_opts = [1, 2, 6, 8, 10, 12, 15, 17, 20, 24, 30, 36]
    return [x for x in all_opts if x <= limit]


async def ensure_social_tables():
    await db.ensure_pool()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dt_config (
                key TEXT PRIMARY KEY,
                val TEXT
            );

            CREATE TABLE IF NOT EXISTS sp_profiles (
                user_id BIGINT PRIMARY KEY,
                display_name TEXT DEFAULT '',
                username TEXT DEFAULT '',
                photo TEXT DEFAULT '',
                bio TEXT DEFAULT 'به پروفایل من در راینو خوش آمدید!',
                coins BIGINT DEFAULT 1000,
                stars_balance BIGINT DEFAULT 0,
                xp BIGINT DEFAULT 0,
                level INT DEFAULT 1,
                wealth_pts BIGINT DEFAULT 0,
                charm_pts BIGINT DEFAULT 0,
                card_theme TEXT DEFAULT 'purple',
                avatar_ring_id INT DEFAULT 0,
                sub_tier TEXT DEFAULT 'free',
                sub_expires_at DOUBLE PRECISION DEFAULT 0,
                custom_badge_emoji_id TEXT DEFAULT '',
                custom_badge_icon TEXT DEFAULT '',
                stealth_mode BOOLEAN DEFAULT TRUE,
                ghost_mode BOOLEAN DEFAULT TRUE,
                owned_rings TEXT DEFAULT '[]',
                owned_rel_links TEXT DEFAULT '[]',
                active_marriage_link_id INT DEFAULT 0,
                active_bestie_link_id INT DEFAULT 0,
                received_gifts_inv TEXT DEFAULT '[]',
                 showcased_gifts TEXT DEFAULT '[]',
                gifts_received INT DEFAULT 0,
                visitors_log TEXT DEFAULT '[]',
                is_banned BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS sp_voice_rooms (
                room_id SERIAL PRIMARY KEY,
                owner_id BIGINT UNIQUE,
                title TEXT DEFAULT 'اتاق گفتگوی صوتی',
                photo TEXT DEFAULT '',
                description TEXT DEFAULT 'به اتاق صوتی خوش آمدید! به قوانین احترام بگذارید.',
                welcome_msg TEXT DEFAULT 'خوش آمدید! روی صندلی‌های خالی بزنید تا میکروفون بگیرید.',
                category TEXT DEFAULT 'Friendship',
                mic_count INT DEFAULT 8,
                mic_mode TEXT DEFAULT 'normal',
                bg_theme TEXT DEFAULT 'lighthouse',
                is_locked BOOLEAN DEFAULT FALSE,
                pin_code TEXT DEFAULT '',
                auto_lock_mics BOOLEAN DEFAULT FALSE,
                room_mute BOOLEAN DEFAULT FALSE,
                admins_list TEXT DEFAULT '[]',
                level INT DEFAULT 1,
                total_gifts BIGINT DEFAULT 0,
                created_at DOUBLE PRECISION DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sp_store_items (
                id SERIAL PRIMARY KEY,
                category TEXT,
                name TEXT,
                icon TEXT DEFAULT '🎁',
                photo TEXT DEFAULT '',
                custom_emoji_id TEXT DEFAULT '',
                ring_css TEXT DEFAULT '',
                price_coins INT DEFAULT 500,
                price_stars INT DEFAULT 25
            );

            CREATE TABLE IF NOT EXISTS sp_relationships (
                id SERIAL PRIMARY KEY,
                user_a BIGINT,
                user_b BIGINT,
                rel_type TEXT DEFAULT 'none',
                affinity_pts BIGINT DEFAULT 0,
                affinity_level INT DEFAULT 1,
                status TEXT DEFAULT 'active',
                requested_by BIGINT DEFAULT 0,
                pending_type TEXT DEFAULT '',
                chat_bg TEXT DEFAULT '',
                updated_at DOUBLE PRECISION DEFAULT 0,
                UNIQUE(user_a, user_b)
            );

            CREATE TABLE IF NOT EXISTS sp_pm_messages (
                id SERIAL PRIMARY KEY,
                sender_id BIGINT,
                receiver_id BIGINT,
                msg_type TEXT DEFAULT 'text',
                text TEXT DEFAULT '',
                voice_data TEXT DEFAULT '',
                created_at DOUBLE PRECISION DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS sp_user_music (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                file_id TEXT,
                title TEXT DEFAULT 'موزیک من',
                duration INT DEFAULT 0
            );
        """)

        alter_queries = [
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS coins BIGINT DEFAULT 1000",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS stars_balance BIGINT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS wealth_pts BIGINT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS charm_pts BIGINT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS custom_badge_emoji_id TEXT DEFAULT ''",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS custom_badge_icon TEXT DEFAULT ''",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS owned_rel_links TEXT DEFAULT '[]'",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS active_marriage_link_id INT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS active_bestie_link_id INT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS received_gifts_inv TEXT DEFAULT '[]'",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS showcased_gifts TEXT DEFAULT '[]'",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
            "ALTER TABLE sp_voice_rooms ADD COLUMN IF NOT EXISTS admins_list TEXT DEFAULT '[]'",
            "ALTER TABLE sp_store_items ADD COLUMN IF NOT EXISTS photo TEXT DEFAULT ''",
            "ALTER TABLE sp_store_items ADD COLUMN IF NOT EXISTS custom_emoji_id TEXT DEFAULT ''",
            "ALTER TABLE sp_store_items ADD COLUMN IF NOT EXISTS ring_css TEXT DEFAULT ''",
        ]
        for q in alter_queries:
            try:
                await conn.execute(q)
            except Exception:
                pass

        cnt = await conn.fetchval("SELECT COUNT(*) FROM sp_store_items")
        if not cnt:
            await conn.execute("""
                INSERT INTO sp_store_items (category, name, icon, photo, custom_emoji_id, ring_css, price_coins, price_stars)
                VALUES
                ('ring', 'حلقه طلایی امپراتور', '👑', '', '', '0 0 0 3.5px #fbbf24, 0 0 18px #f59e0b', 1500, 15),
                ('ring', 'حلقه نئون سایبرپانک', '⚡', '', '', '0 0 0 3.5px #06b6d4, 0 0 20px #ec4899', 2500, 25),
                ('ring', 'حلقه آتش دوزخی', '🔥', '', '', '0 0 0 3.5px #ef4444, 0 0 22px #dc2626', 3500, 35),
                ('ring', 'حلقه الماس بنفش', '💎', '', '', '0 0 0 4px #e879f9, 0 0 25px #a855f7', 5000, 50),
                ('gift', 'شاخه گل رز', '🌹', '', '', '', 200, 2),
                ('gift', 'تاج پادشاهی', '👑', '', '', '', 1000, 10),
                ('gift', 'موشک طلایی', '🚀', '', '', '', 3000, 30),
                ('gift', 'قصر الماس', '🏰', '', '', '', 10000, 100),
                ('rel_marriage', 'پیوند حلقه الماس (ازدواج)', '💍', '', '', '#ec4899', 5000, 50),
                ('rel_marriage', 'پیوند ققنوس آتشین (ازدواج)', '❤️‍🔥', '', '', '#f43f5e', 12000, 120),
                ('rel_bestie', 'پیوند صاعقه نئون (رفاقت)', '⚡', '', '', '#06b6d4', 3000, 30),
                ('rel_bestie', 'پیوند تاج برادری (رفاقت)', '🛡️', '', '', '#10b981', 7000, 70);
            """)


async def get_sp_config(key: str, default: str = "") -> str:
    await ensure_social_tables()
    val = await db.pool.fetchval("SELECT val FROM dt_config WHERE key=$1", key)
    return val if val is not None else default


async def set_sp_config(key: str, val: str):
    await ensure_social_tables()
    await db.pool.execute(
        "INSERT INTO dt_config (key, val) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET val=$2",
        key, val
    )


async def reset_all_levels_and_balances():
    """صفر کردن کامل دیتابیس روم‌ها، موجودی سکه‌ها/استارزها و لول‌های تمام کاربران"""
    await ensure_social_tables()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            UPDATE sp_profiles
            SET coins = 0,
                stars_balance = 0,
                xp = 0,
                level = 1,
                wealth_pts = 0,
                charm_pts = 0,
                gifts_received = 0,
                received_gifts_inv = '[]',
                showcased_gifts = '[]';
        """)
        await conn.execute("DELETE FROM sp_voice_rooms;")
        await conn.execute("UPDATE sp_relationships SET affinity_pts = 0, affinity_level = 1;")
    live_rooms_runtime.clear()
    bombs_sessions.clear()


async def fetch_tg_custom_emoji_bytes(custom_emoji_id: str) -> tuple[bytes | None, str]:
    """دریافت تصویر/انیمیشن ایموجی پریمیوم تلگرام برای نمایش در مینی‌اپ"""
    cid = str(custom_emoji_id or "").strip()
    if not cid or not cid.isdigit():
        return None, "image/webp"
    if cid in emoji_file_cache:
        return emoji_file_cache[cid]

    bot_token = os.environ.get("BOT_TOKEN", "")
    if not bot_token:
        return None, "image/webp"

    temp_bot = Bot(token=bot_token)
    try:
        stickers = await temp_bot.get_custom_emoji_stickers(custom_emoji_ids=[cid])
        if not stickers:
            return None, "image/webp"
        st = stickers[0]
        target_file_id = st.thumbnail.file_id if (st.is_animated or st.is_video) and st.thumbnail else st.file_id
        file_obj = await temp_bot.get_file(target_file_id)
        bio = await temp_bot.download_file(file_obj.file_path)
        raw_bytes = bio.read()
        mime = "image/webp"
        if file_obj.file_path.endswith(".png"):
            mime = "image/png"
        elif file_obj.file_path.endswith(".jpg") or file_obj.file_path.endswith(".jpeg"):
            mime = "image/jpeg"
        emoji_file_cache[cid] = (raw_bytes, mime)
        return raw_bytes, mime
    except Exception:
        return None, "image/webp"
    finally:
        await temp_bot.session.close()


def _pair_key(u1: int, u2: int) -> tuple[int, int]:
    return (min(int(u1), int(u2)), max(int(u1), int(u2)))


async def _add_affinity(u1: int, u2: int, pts: int):
    if int(u1) == int(u2) or int(u1) <= 0 or int(u2) <= 0:
        return
    a, b = _pair_key(u1, u2)
    row = await db.pool.fetchrow("SELECT * FROM sp_relationships WHERE user_a=$1 AND user_b=$2", a, b)
    now = time.time()
    if not row:
        new_lvl = max(1, min(50, 1 + pts // 150))
        await db.pool.execute(
            """INSERT INTO sp_relationships (user_a, user_b, rel_type, affinity_pts, affinity_level, updated_at)
               VALUES ($1, $2, 'none', $3, $4, $5) ON CONFLICT DO NOTHING""",
            a, b, pts, new_lvl, now
        )
    else:
        total = int(row["affinity_pts"] or 0) + pts
        new_lvl = max(1, min(50, 1 + total // 150))
        await db.pool.execute(
            "UPDATE sp_relationships SET affinity_pts=$1, affinity_level=$2, updated_at=$3 WHERE id=$4",
            total, new_lvl, now, row["id"]
        )


async def _get_user_relationships(uid: int) -> dict:
    rows = await db.pool.fetch(
        "SELECT * FROM sp_relationships WHERE (user_a=$1 OR user_b=$1) AND (rel_type != 'none' OR pending_type != '' OR affinity_pts > 0) ORDER BY affinity_pts DESC LIMIT 30",
        int(uid)
    )
    marriage = None
    besties = []
    pending_requests = []
    all_bonds = {}

    for r in rows:
        other_uid = int(r["user_b"]) if int(r["user_a"]) == int(uid) else int(r["user_a"])
        p_row = await db.pool.fetchrow(
            "SELECT display_name, photo, sub_tier, custom_badge_emoji_id, custom_badge_icon FROM sp_profiles WHERE user_id=$1",
            other_uid
        )
        other_name = (p_row["display_name"] if p_row else "") or f"User {other_uid}"
        other_photo = (p_row["photo"] if p_row else "") or ""

        info = {
            "rel_id": r["id"],
            "partner_uid": other_uid,
            "partner_name": other_name,
            "partner_photo": other_photo,
            "rel_type": r["rel_type"],
            "affinity_pts": int(r["affinity_pts"] or 0),
            "affinity_level": int(r["affinity_level"] or 1),
            "pending_type": r["pending_type"] or "",
            "requested_by": int(r["requested_by"] or 0),
            "chat_bg": r["chat_bg"] or "",
        }
        if r["rel_type"] in ("marriage", "bestie"):
            all_bonds[str(other_uid)] = r["rel_type"]
        if r["rel_type"] == "marriage":
            marriage = info
        elif r["rel_type"] == "bestie":
            besties.append(info)
        if r["pending_type"]:
            pending_requests.append(info)

    return {
        "marriage": marriage,
        "besties": besties[:5],
        "pending": pending_requests,
        "bonds_map": all_bonds,
    }


def _get_live_room_state(room_id: int, mic_count: int) -> dict:
    if room_id not in live_rooms_runtime:
        live_rooms_runtime[room_id] = {
            "seats": {},
            "locked_seats": [],
            "members": {},
            "chats": [
                {"sys": True, "text": "به اتاق صوتی خوش آمدید! لطفاً قوانین و احترام متقابل را رعایت کنید."},
            ],
            "gift_fx": None,
            "mic_invites": {},
            "music_playing": False,
            "music_title": "Rhino Chill Beats 🎵",
            "pk_active": False,
            "pk_score_a": 0,
            "pk_score_b": 0,
        }
    st = live_rooms_runtime[room_id]
    now = time.time()
    dead = [u for u, m in st["members"].items() if now - m.get("last_seen", 0) > 65]
    for u in dead:
        st["members"].pop(u, None)
        for s_idx, s_val in list(st["seats"].items()):
            if s_val and int(s_val.get("uid", 0)) == int(u):
                st["seats"].pop(s_idx, None)
    if st.get("gift_fx") and now - st["gift_fx"].get("ts", 0) > 6.5:
        st["gift_fx"] = None
    return st


async def get_or_create_sp_profile(uid: int, name: str = "", username: str = "", photo: str = "") -> dict:
    await ensure_social_tables()
    now = time.time()
    row = await db.pool.fetchrow("SELECT * FROM sp_profiles WHERE user_id=$1", uid)
    if not row:
        await db.pool.execute(
            """INSERT INTO sp_profiles (user_id, display_name, username, photo, coins, stars_balance)
               VALUES ($1, $2, $3, $4, 1000, 0) ON CONFLICT DO NOTHING""",
            uid, name or f"User {uid}", username, photo
        )
        row = await db.pool.fetchrow("SELECT * FROM sp_profiles WHERE user_id=$1", uid)
    else:
        upd_name = name if (name and not row["display_name"]) else row["display_name"]
        upd_photo = photo if photo else row["photo"]
        upd_user = username if username else row["username"]
        if upd_name != row["display_name"] or upd_photo != row["photo"] or upd_user != row["username"]:
            await db.pool.execute(
                "UPDATE sp_profiles SET display_name=$1, username=$2, photo=$3 WHERE user_id=$4",
                upd_name, upd_user, upd_photo, uid
            )
            row = await db.pool.fetchrow("SELECT * FROM sp_profiles WHERE user_id=$1", uid)

    prof = dict(row)
    if prof["sub_tier"] != "free" and prof["sub_expires_at"] > 0 and now > prof["sub_expires_at"]:
        prof["sub_tier"] = "free"
        prof["sub_expires_at"] = 0
        await db.pool.execute("UPDATE sp_profiles SET sub_tier='free', sub_expires_at=0 WHERE user_id=$1", uid)

    tier_info = SUB_TIERS.get(prof["sub_tier"], SUB_TIERS["free"])

    ring_css = ""
    ring_photo = ""
    ring_name = ""
    if prof.get("avatar_ring_id"):
        r_row = await db.pool.fetchrow(
            "SELECT name, ring_css, photo FROM sp_store_items WHERE id=$1",
            int(prof["avatar_ring_id"]),
        )
        if r_row:
            ring_css = r_row["ring_css"] or ""
            ring_photo = r_row["photo"] or ""
            ring_name = r_row["name"] or ""

    # ایموجی‌های خط رابط ازدواج و رفاقت کاربر
    def_m_emoji = await get_sp_config("default_marriage_emoji_id", "")
    def_m_icon = await get_sp_config("default_marriage_icon", "💍")
    def_b_emoji = await get_sp_config("default_bestie_emoji_id", "")
    def_b_icon = await get_sp_config("default_bestie_icon", "⚡")

    m_link_emoji, m_link_icon, m_link_color = def_m_emoji, def_m_icon, "#ec4899"
    if prof.get("active_marriage_link_id"):
        ml = await db.pool.fetchrow("SELECT icon, custom_emoji_id, ring_css FROM sp_store_items WHERE id=$1", int(prof["active_marriage_link_id"]))
        if ml:
            m_link_emoji = ml["custom_emoji_id"] or def_m_emoji
            m_link_icon = ml["icon"] or def_m_icon
            m_link_color = ml["ring_css"] or "#ec4899"

    b_link_emoji, b_link_icon, b_link_color = def_b_emoji, def_b_icon, "#06b6d4"
    if prof.get("active_bestie_link_id"):
        bl = await db.pool.fetchrow("SELECT icon, custom_emoji_id, ring_css FROM sp_store_items WHERE id=$1", int(prof["active_bestie_link_id"]))
        if bl:
            b_link_emoji = bl["custom_emoji_id"] or def_b_emoji
            b_link_icon = bl["icon"] or def_b_icon
            b_link_color = bl["ring_css"] or "#06b6d4"

    wealth_lvl, wealth_pct, wealth_next = calc_user_level_50(int(prof.get("wealth_pts") or 0))
    charm_lvl, charm_pct, charm_next = calc_user_level_50(int(prof.get("charm_pts") or 0))

    room_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
    my_room = None
    if room_row:
        my_room = _format_room_dict(room_row, uid)

    rels = await _get_user_relationships(uid)

    custom_emoji_id = prof.get("custom_badge_emoji_id") or ""
    custom_icon = prof.get("custom_badge_icon") or ""
    effective_badge = tier_info["badge"]
    if tier_info["custom_badge_allowed"] and custom_icon:
        effective_badge = f"{custom_icon} {prof['sub_tier'].upper()}"

    return {
        "user_id": prof["user_id"],
        "display_name": prof["display_name"] or name or f"User {uid}",
        "username": prof["username"] or username,
        "photo": prof["photo"] or photo,
        "bio": prof["bio"],
        "coins": int(prof.get("coins") or 0),
        "stars_balance": int(prof.get("stars_balance") or 0),
        "wealth_pts": int(prof.get("wealth_pts") or 0),
        "wealth_level": wealth_lvl,
        "wealth_pct": wealth_pct,
        "wealth_next": wealth_next,
        "charm_pts": int(prof.get("charm_pts") or 0),
        "charm_level": charm_lvl,
        "charm_pct": charm_pct,
        "charm_next": charm_next,
        "level": max(wealth_lvl, charm_lvl),
        "card_theme": prof["card_theme"] or "purple",
        "avatar_ring_id": int(prof.get("avatar_ring_id") or 0),
        "ring_css": ring_css,
        "ring_photo": ring_photo,
        "ring_name": ring_name,
        "sub_tier": prof["sub_tier"],
        "sub_title": tier_info["title"],
        "sub_badge": effective_badge,
        "custom_badge_emoji_id": custom_emoji_id if tier_info["custom_badge_allowed"] else "",
        "custom_badge_icon": custom_icon,
        "sub_expires_rem_days": max(0, round((prof["sub_expires_at"] - now) / 86400, 1)) if prof["sub_expires_at"] > now else 0,
        "can_lock_room": tier_info["can_lock_room"] or (int(uid) in OWNER_IDS),
        "can_stealth_visit": tier_info["stealth_visit"] or (int(uid) in OWNER_IDS),
        "can_ghost_join": tier_info["ghost_join"] or (int(uid) in OWNER_IDS),
        "stealth_mode": bool(prof["stealth_mode"]),
        "ghost_mode": bool(prof["ghost_mode"]),
        "owned_rings": [int(x) for x in json.loads(prof["owned_rings"] or "[]")],
        "owned_rel_links": [int(x) for x in json.loads(prof.get("owned_rel_links") or "[]")],
        "active_marriage_link_id": int(prof.get("active_marriage_link_id") or 0),
        "active_bestie_link_id": int(prof.get("active_bestie_link_id") or 0),
        "marriage_link": {"emoji_id": m_link_emoji, "icon": m_link_icon, "color": m_link_color},
        "bestie_link": {"emoji_id": b_link_emoji, "icon": b_link_icon, "color": b_link_color},
        "received_gifts_inv": json.loads(prof.get("received_gifts_inv") or "[]"),
        "showcased_gifts": json.loads(prof.get("showcased_gifts") or "[]"),
        "gifts_received": int(prof.get("gifts_received") or 0),
        "visitors_log": json.loads(prof["visitors_log"] or "[]"),
        "relationships": rels,
        "is_banned": bool(prof.get("is_banned", False)),
        "room": my_room,
    }


def _format_room_dict(r_row: dict, viewer_uid: int = 0) -> dict:
    r = dict(r_row)
    room_lvl, room_pct, room_next_coins = calc_room_level_50(int(r.get("total_gifts") or 0))
    r["level"] = room_lvl
    r["level_pct"] = room_pct
    r["next_level_coins"] = room_next_coins
    r["max_allowed_mics"] = max_mics_for_room_level(room_lvl)
    r["allowed_mic_list"] = allowed_mic_options_for_level(room_lvl)

    admins_list = [int(x) for x in json.loads(r.get("admins_list") or "[]")]
    r["admins_list"] = admins_list

    rt = _get_live_room_state(r["room_id"], r["mic_count"])
    visible_members = [m for m in rt["members"].values() if not m.get("is_ghost")]
    seated_uids = {int(s.get("uid", 0)) for s in rt["seats"].values() if s}
    unseated_listeners = [m for m in visible_members if int(m.get("uid", 0)) not in seated_uids]

    is_owner_or_admin = (int(viewer_uid) == int(r["owner_id"])) or (int(viewer_uid) in admins_list) or (int(viewer_uid) in OWNER_IDS)
    my_invite_seat = rt.get("mic_invites", {}).pop(int(viewer_uid), None) if viewer_uid else None

    return {
        **r,
        "is_room_admin": is_owner_or_admin,
        "pin_code": r["pin_code"] if is_owner_or_admin else "",
        "online_count": max(1, len(visible_members)),
        "visible_members": visible_members[:40],
        "unseated_listeners": unseated_listeners[:35],
        "seats": rt["seats"],
        "locked_seats": rt["locked_seats"],
        "chats": rt["chats"][-25:],
        "gift_fx": rt.get("gift_fx"),
        "my_mic_invite": my_invite_seat,
        "music_playing": rt["music_playing"],
        "music_title": rt["music_title"],
        "pk_active": rt["pk_active"],
        "pk_score_a": rt["pk_score_a"],
        "pk_score_b": rt["pk_score_b"],
    }


def _record_big_win(player_name: str, game_name: str, win_coins: int, mult_str: str):
    if win_coins >= 200:
        recent_big_wins.insert(0, {
            "name": player_name[:12],
            "game": game_name,
            "win": win_coins,
            "mult": mult_str,
            "time": "Just now",
        })
        del recent_big_wins[10:]


async def handle_social_api(payload: dict) -> dict:
    await ensure_social_tables()
    uid = int(payload.get("uid") or 0)
    name = str(payload.get("name") or "Player").strip()
    username = str(payload.get("username") or "").strip()
    photo = str(payload.get("photo") or "").strip()
    action = str(payload.get("action") or "state").strip()
    now = time.time()

    my_prof = await get_or_create_sp_profile(uid, name, username, photo)
    if my_prof["is_banned"] and uid not in OWNER_IDS:
        return {"ok": False, "error": "⛔ حساب کاربری شما در پلتفرم مسدود شده است."}

    msg_out = ""

    # ─── ۱. کیف پول: شارژ استارز و تبدیل استارز به سکه ───
    if action == "create_topup_invoice":
        pack_id = str(payload.get("pack_id") or "topup_50")
        pack = next((p for p in STAR_TOPUP_PACKS if p["id"] == pack_id), STAR_TOPUP_PACKS[0])
        total_stars = pack["stars"] + pack["bonus_stars"]
        bot_token = os.environ.get("BOT_TOKEN", "")
        temp_bot = Bot(token=bot_token)
        try:
            inv_link = await temp_bot.create_invoice_link(
                title=pack["title"],
                description=f"شارژ کیف پول به مقدار {total_stars} استارز",
                payload=f"sptopup_{total_stars}_{uid}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Stars", amount=int(pack["stars"]))],
            )
            return {"ok": True, "invoice_link": inv_link, "state": await _collect_social_state(uid)}
        except Exception as e:
            return {"ok": False, "error": f"خطای درگاه تلگرام: {str(e)}", "state": await _collect_social_state(uid)}
        finally:
            await temp_bot.session.close()

    elif action == "get_my_playlist":
        rows = await db.pool.fetch("SELECT * FROM sp_user_music WHERE user_id=$1 ORDER BY id DESC", uid)
        return {"ok": True, "playlist": [dict(r) for r in rows], "state": await _collect_social_state(uid)}

    elif action == "delete_my_music":
        m_id = int(payload.get("music_id") or 0)
        await db.pool.execute("DELETE FROM sp_user_music WHERE id=$1 AND user_id=$2", m_id, uid)
        rows = await db.pool.fetch("SELECT * FROM sp_user_music WHERE user_id=$1 ORDER BY id DESC", uid)
        return {"ok": True, "playlist": [dict(r) for r in rows], "state": await _collect_social_state(uid)}
    elif action == "convert_stars_to_coins":
        stars_amt = int(payload.get("stars") or 0)
        if stars_amt <= 0:
            return {"ok": False, "error": "تعداد استارز برای تبدیل را وارد کنید!", "state": await _collect_social_state(uid)}
        if my_prof["stars_balance"] < stars_amt:
            return {
                "ok": False,
                "error": f"موجودی استارز کیف پول شما کافی نیست! (موجودی فعلی: {my_prof['stars_balance']} ⭐)",
                "state": await _collect_social_state(uid),
            }
        coins_added = stars_amt * STARS_TO_COINS_RATE
        await db.pool.execute(
            "UPDATE sp_profiles SET stars_balance=stars_balance-$1, coins=coins+$2 WHERE user_id=$3",
            stars_amt, coins_added, uid
        )
        msg_out = f"⚡ {stars_amt} استارز با موفقیت به +{coins_added:,} سکه 🪙 تبدیل شد!"

    # ─── ۲. بازی‌های کازینویی (CRASH, BOMBS, HELL PICKAXE, SLOT) ───
    elif action == "casino_play":
        game = str(payload.get("game") or "crash")
        sub_op = str(payload.get("sub_op") or "bet")
        bet = int(payload.get("bet") or 100)

        if game == "bombs":
            if sub_op == "start":
                mines_cnt = max(1, min(15, int(payload.get("mines") or 5)))
                if bet < 10 or bet > my_prof["coins"]:
                    return {"ok": False, "error": "موجودی سکه کافی نیست یا مبلغ شرط نامعتبر است!", "state": await _collect_social_state(uid)}
                await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)
                bombs_pos = random.sample(range(25), mines_cnt)
                bombs_sessions[uid] = {
                    "bet": bet, "mines_count": mines_cnt, "bombs": bombs_pos,
                    "revealed": [], "mult": 1.0, "active": True, "game_over": False, "won": False,
                }
                return {
                    "ok": True,
                    "bombs_state": {"active": True, "bet": bet, "mines_count": mines_cnt, "revealed": [], "mult": 1.0, "potential_win": bet},
                    "state": await _collect_social_state(uid),
                }

            elif sub_op == "pick":
                sess = bombs_sessions.get(uid)
                cell = int(payload.get("cell") or 0)
                if not sess or not sess.get("active"):
                    return {"ok": False, "error": "ابتدا شرط ببندید و بازی را شروع کنید!", "state": await _collect_social_state(uid)}
                if cell in sess["revealed"]:
                    return {"ok": True, "state": await _collect_social_state(uid)}

                if cell in sess["bombs"]:
                    sess["active"] = False
                    sess["game_over"] = True
                    return {
                        "ok": False,
                        "error": f"💥 بوووم! روی بمب رفتی و {sess['bet']:,} سکه باختی!",
                        "bombs_state": {
                            "active": False, "game_over": True, "won": False,
                            "bombs": sess["bombs"], "revealed": sess["revealed"] + [cell], "mult": 0
                        },
                        "state": await _collect_social_state(uid),
                    }
                else:
                    sess["revealed"].append(cell)
                    safe_left = 25 - sess["mines_count"] - len(sess["revealed"]) + 1
                    total_left = 25 - len(sess["revealed"]) + 1
                    step_factor = (total_left / max(1, safe_left)) * 0.96
                    sess["mult"] = round(sess["mult"] * max(1.12, step_factor), 2)
                    pot_win = int(sess["bet"] * sess["mult"])
                    return {
                        "ok": True,
                        "bombs_state": {
                            "active": True, "bet": sess["bet"], "mines_count": sess["mines_count"],
                            "revealed": sess["revealed"], "mult": sess["mult"], "potential_win": pot_win
                        },
                        "state": await _collect_social_state(uid),
                    }

            elif sub_op == "cashout":
                sess = bombs_sessions.get(uid)
                if not sess or not sess.get("active") or not sess["revealed"]:
                    return {"ok": False, "error": "حداقل یک خانه امن را باز کنید!", "state": await _collect_social_state(uid)}
                sess["active"] = False
                win_amt = int(sess["bet"] * sess["mult"])
                await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1 WHERE user_id=$2", win_amt, uid)
                _record_big_win(my_prof["display_name"], "BOMBS", win_amt, f"{sess['mult']}x")
                return {
                    "ok": True,
                    "msg": f"🎉 برداشت موفق! +{win_amt:,} سکه (ضریب {sess['mult']}x) به کیف پول شما اضافه شد!",
                    "bombs_state": {"active": False, "game_over": True, "won": True, "bombs": sess["bombs"], "revealed": sess["revealed"], "mult": sess["mult"]},
                    "state": await _collect_social_state(uid),
                }

        elif game == "crash":
            target_mult = max(1.1, min(100.0, round(float(payload.get("target_mult") or 2.0), 2)))
            if bet < 10 or bet > my_prof["coins"]:
                return {"ok": False, "error": "موجودی سکه کافی نیست یا مبلغ شرط نامعتبر است!", "state": await _collect_social_state(uid)}

            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)
            r_val = random.random()
            crash_point = 1.00 if r_val < 0.06 else round(min(100.0, max(1.01, 0.97 / (1.0 - r_val))), 2)
            won = crash_point >= target_mult
            win_amt = int(bet * target_mult) if won else 0
            if won:
                await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1 WHERE user_id=$2", win_amt, uid)
                _record_big_win(my_prof["display_name"], "CRASH", win_amt, f"{target_mult}x")

            return {
                "ok": True,
                "crash_result": {"won": won, "crash_point": crash_point, "target_mult": target_mult, "bet": bet, "win_amt": win_amt},
                "msg": f"🚀 موشک تا {crash_point}x بالا رفت! برنده +{win_amt:,} سکه شدید!" if won else f"💥 موشک در ضریب {crash_point}x منفجر شد!",
                "state": await _collect_social_state(uid),
            }

        elif game in ("pickaxe", "slot"):
            if bet < 10 or bet > my_prof["coins"]:
                return {"ok": False, "error": "موجودی سکه کافی نیست!", "state": await _collect_social_state(uid)}
            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)

            if game == "pickaxe":
                mult = random.choices([0, 0.5, 1.5, 2.0, 3.5, 6.0, 12.0], weights=[40, 20, 18, 11, 6, 3.5, 1.5])[0]
                icons = {0: "🪨 سنگ پوچ", 0.5: "🥉 مس", 1.5: "🥈 نقره", 2.0: "🥇 طلا", 3.5: "💎 یاقوت", 6.0: "🔥 کریستال دوزخی", 12.0: "👑 گنج امپراتور"}
                win_amt = int(bet * mult)
                if win_amt > 0:
                    await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1 WHERE user_id=$2", win_amt, uid)
                    _record_big_win(my_prof["display_name"], "PICKAXE", win_amt, f"{mult}x")
                return {
                    "ok": win_amt >= bet,
                    "pickaxe_result": {"mult": mult, "loot": icons[mult], "win_amt": win_amt},
                    "msg": f"⛏️ سنگ شکسته شد: {icons[mult]} ({mult}x) — دریافتی: {win_amt:,} سکه!",
                    "state": await _collect_social_state(uid),
                }
            else:
                syms = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
                reels = [random.choice(syms) for _ in range(3)]
                if reels[0] == reels[1] == reels[2]:
                    mult = 15.0 if reels[0] == "7️⃣" else (8.0 if reels[0] == "💎" else 5.0)
                elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
                    mult = 2.0
                else:
                    mult = 0.0
                win_amt = int(bet * mult)
                if win_amt > 0:
                    await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1 WHERE user_id=$2", win_amt, uid)
                    _record_big_win(my_prof["display_name"], "SLOT", win_amt, f"{mult}x")
                return {
                    "ok": win_amt > 0,
                    "slot_result": {"reels": reels, "mult": mult, "win_amt": win_amt},
                    "msg": f"🎰 [ {' | '.join(reels)} ] — {'برنده +' + f'{win_amt:,} سکه (' + str(mult) + 'x)!' if win_amt else 'پوچ! دوباره امتحان کن'}",
                    "state": await _collect_social_state(uid),
                }

    # ─── ۳. مشاهده پروفایل کاربر دیگر ───
    elif action == "view_profile":
        target_uid = int(payload.get("target_uid") or uid)
        target_prof = await get_or_create_sp_profile(target_uid)
        if target_uid != uid:
            is_stealth = my_prof["can_stealth_visit"] and my_prof["stealth_mode"]
            if not is_stealth:
                vis = target_prof["visitors_log"]
                vis = [v for v in vis if int(v.get("uid", 0)) != uid]
                vis.insert(0, {
                    "uid": uid,
                    "name": my_prof["display_name"],
                    "photo": my_prof["photo"],
                    "ring_photo": my_prof["ring_photo"],
                    "ring_css": my_prof["ring_css"],
                    "badge": my_prof["sub_badge"],
                    "time": time.strftime("%H:%M"),
                })
                vis = vis[:25]
                await db.pool.execute(
                    "UPDATE sp_profiles SET visitors_log=$1 WHERE user_id=$2",
                    json.dumps(vis), target_uid
                )
                target_prof["visitors_log"] = vis
        return {
            "ok": True,
            "viewed_profile": target_prof,
            "state": await _collect_social_state(uid),
        }

    # ─── ۴. ویرایش پروفایل، ایموجی پریمیوم جلوی اسم، رنگ کارت و گیفت‌های شناور روی کارت ───
    elif action == "save_profile":
        new_name = str(payload.get("display_name") or my_prof["display_name"]).strip()[:32]
        new_bio = str(payload.get("bio") or my_prof["bio"]).strip()[:160]
        new_theme = str(payload.get("card_theme") or my_prof["card_theme"]).strip()
        stealth_on = bool(payload.get("stealth_mode", my_prof["stealth_mode"]))
        ghost_on = bool(payload.get("ghost_mode", my_prof["ghost_mode"]))
        badge_emoji_id = str(payload.get("custom_badge_emoji_id", my_prof["custom_badge_emoji_id"])).strip()
        badge_icon = str(payload.get("custom_badge_icon", my_prof["custom_badge_icon"])).strip()[:8]
        showcased = payload.get("showcased_gifts")
        if not isinstance(showcased, list):
            showcased = my_prof["showcased_gifts"]
        showcased = [int(x) for x in showcased[:8]]

        theme_obj = next((t for t in PROFILE_THEMES if t["id"] == new_theme), PROFILE_THEMES[0])
        req_rank = TIER_RANK.get(theme_obj["tier"], 0)
        my_rank = TIER_RANK.get(my_prof["sub_tier"], 0)
        if req_rank > my_rank and uid not in OWNER_IDS:
            return {
                "ok": False,
                "error": f"🔒 رنگ کارت «{theme_obj['title']}» مخصوص اشتراک «{theme_obj['tier'].upper()}» به بالاست!",
                "state": await _collect_social_state(uid),
            }

        await db.pool.execute(
            """UPDATE sp_profiles
               SET display_name=$1, bio=$2, card_theme=$3, stealth_mode=$4, ghost_mode=$5,
                   custom_badge_emoji_id=$6, custom_badge_icon=$7, showcased_gifts=$8
               WHERE user_id=$9""",
            new_name, new_bio, new_theme, stealth_on, ghost_on, badge_emoji_id, badge_icon, json.dumps(showcased), uid
        )
        msg_out = "✅ پروفایل، ایموجی VIP و گیفت‌های شناور کارت شما ذخیره شد!"

    elif action == "arm_user_badge_capture":
        if my_prof["sub_tier"] == "free" and uid not in OWNER_IDS:
            return {"ok": False, "error": "🔒 ست کردن ایموجی پریمیوم متحرک جلوی نام مخصوص مشترکین PRO، PLUS و ULTRA است!", "state": await _collect_social_state(uid)}
        await set_sp_config(f"user_emoji_wait_{uid}", "badge")
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                await temp_bot.send_message(
                    chat_id=uid,
                    text="✨ <b>ست کردن ایموجی پریمیوم جلوی نام:</b>\n\nلطفاً همین الان یک پیام حاوی <b>ایموجی پریمیوم متحرک تلگرام</b> مورد نظرتان در همین پیوی بفرستید تا جلوی نام شما در کل مینی‌اپ قرار بگیرد:",
                    parse_mode=ParseMode.HTML,
                )
            finally:
                await temp_bot.session.close()
        return {"ok": True, "msg": "📩 ربات در پیوی آماده دریافت ایموجی پریمیوم شماست!", "state": await _collect_social_state(uid)}

    # ─── ۵. ساخت و ویرایش اتاق صوتی شخصی (با محدودیت تعداد مایک بر اساس لول روم) ───
    elif action == "save_my_room":
        title = str(payload.get("title") or f"اتاق {my_prof['display_name']}").strip()[:45]
        desc = str(payload.get("description") or "به اتاق صوتی من خوش آمدید!").strip()[:180]
        welcome = str(payload.get("welcome_msg") or "خوش آمدید!").strip()[:140]
        cat = str(payload.get("category") or "Friendship").strip()
        r_photo = str(payload.get("room_photo") or "").strip()
        mic_count = int(payload.get("mic_count") or 8)
        mic_mode = str(payload.get("mic_mode") or "normal").strip()
        bg_theme = str(payload.get("bg_theme") or "lighthouse").strip()
        want_lock = bool(payload.get("is_locked", False))
        pin_code = str(payload.get("pin_code") or "").strip()[:12]

        if want_lock and not my_prof["can_lock_room"]:
            return {
                "ok": False,
                "error": "🔒 قفل کردن اتاق صوتی فقط مخصوص مشترکین «PRO»، «PLUS» و «ULTRA» است!",
                "state": await _collect_social_state(uid),
            }

        existing = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
        cur_total_gifts = int(existing["total_gifts"] or 0) if existing else 0
        rm_lvl, _, _ = calc_room_level_50(cur_total_gifts)
        max_mics = max_mics_for_room_level(rm_lvl)
        if mic_count > max_mics and uid not in OWNER_IDS:
            return {
                "ok": False,
                "error": f"🔒 چیدمان {mic_count} مایک نیاز به لول روم بالاتر دارد! (لول فعلی روم شما: Lv.{rm_lvl} — حداکثر مایک مجاز: {max_mics})",
                "state": await _collect_social_state(uid),
            }

        if not existing:
            await db.pool.execute(
                """INSERT INTO sp_voice_rooms
                   (owner_id, title, photo, description, welcome_msg, category, mic_count, mic_mode, bg_theme, is_locked, pin_code, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)""",
                uid, title, r_photo or my_prof["photo"], desc, welcome, cat, mic_count, mic_mode, bg_theme, want_lock, pin_code, now
            )
        else:
            final_photo = r_photo if r_photo else existing["photo"]
            await db.pool.execute(
                """UPDATE sp_voice_rooms
                   SET title=$1, photo=$2, description=$3, welcome_msg=$4, category=$5,
                       mic_count=$6, mic_mode=$7, bg_theme=$8, is_locked=$9, pin_code=$10
                   WHERE owner_id=$11""",
                title, final_photo, desc, welcome, cat, mic_count, mic_mode, bg_theme, want_lock, pin_code, uid
            )

        room_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
        return {
            "ok": True,
            "msg": "✅ تنظیمات اتاق صوتی شما ذخیره شد!",
            "active_room": _format_room_dict(room_row, uid),
            "state": await _collect_social_state(uid),
        }

    # ─── ۶. ورود به اتاق صوتی (مسدود بودن ورود روح به روم قفل برای غیر مالک ربات) ───
    elif action == "join_room":
        room_id = int(payload.get("room_id") or 0)
        entered_pin = str(payload.get("pin_code") or "").strip()
        r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
        if not r_row:
            return {"ok": False, "error": "اتاق صوتی مورد نظر یافت نشد!", "state": await _collect_social_state(uid)}

        admins_list = [int(x) for x in json.loads(r_row["admins_list"] or "[]")]
        is_room_staff = (int(r_row["owner_id"]) == uid) or (uid in admins_list) or (uid in OWNER_IDS)
        is_bot_owner = uid in OWNER_IDS

        # وقتی روم قفل است، حالت روح نمی‌تواند بدون رمز وارد شود مگر اینکه مالک اصلی ربات باشد
        if r_row["is_locked"] and not is_room_staff and not is_bot_owner:
            if not entered_pin or (r_row["pin_code"] and entered_pin != r_row["pin_code"]):
                return {
                    "ok": False,
                    "need_pin": True,
                    "room_id": room_id,
                    "error": "🔒 این اتاق صوتی قفل است! (حالت روح در اتاق‌های قفل‌شده کار نمی‌کند). رمز ورود را وارد کنید:",
                    "state": await _collect_social_state(uid),
                }

        is_ghost_entry = bool(
            my_prof["can_ghost_join"]
            and my_prof["ghost_mode"]
            and int(r_row["owner_id"]) != uid
            and (not r_row["is_locked"] or is_bot_owner)
        )

        rt = _get_live_room_state(room_id, r_row["mic_count"])
        was_already_in = uid in rt["members"]
        rt["members"][uid] = {
            "uid": uid,
            "name": my_prof["display_name"],
            "photo": my_prof["photo"],
            "badge": my_prof["sub_badge"],
            "badge_emoji_id": my_prof["custom_badge_emoji_id"],
            "ring_css": my_prof["ring_css"],
            "ring_photo": my_prof["ring_photo"],
            "wealth_level": my_prof["wealth_level"],
            "charm_level": my_prof["charm_level"],
            "bonds": my_prof["relationships"]["bonds_map"],
            "marriage_link": my_prof["marriage_link"],
            "bestie_link": my_prof["bestie_link"],
            "speaking": False,
            "is_ghost": is_ghost_entry,
            "last_seen": now,
        }
        if not was_already_in and not is_ghost_entry:
            rt["chats"].append({
                "sys": True,
                "text": f"👋 {my_prof['display_name']} {my_prof['sub_badge']} وارد اتاق شد.",
            })

        return {
            "ok": True,
            "ghost_active": is_ghost_entry,
            "active_room": _format_room_dict(r_row, uid),
            "state": await _collect_social_state(uid),
        }

    # ─── ۷. عملیات داخل اتاق صوتی (صندلی، ادمین‌ها، دعوت به مایک، گیفت به اشخاص مشخص، امواج صحبت) ───
    elif action == "room_op":
        room_id = int(payload.get("room_id") or 0)
        op = str(payload.get("op") or "ping")
        r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
        if not r_row:
            return {"ok": False, "error": "اتاق یافت نشد!"}

        rt = _get_live_room_state(room_id, r_row["mic_count"])
        admins_list = [int(x) for x in json.loads(r_row["admins_list"] or "[]")]
        is_room_owner = (int(r_row["owner_id"]) == uid) or (uid in OWNER_IDS)
        is_room_admin = is_room_owner or (uid in admins_list)

        if uid in rt["members"]:
            rt["members"][uid]["last_seen"] = now
            rt["members"][uid]["ring_css"] = my_prof["ring_css"]
            rt["members"][uid]["ring_photo"] = my_prof["ring_photo"]
            rt["members"][uid]["badge"] = my_prof["sub_badge"]
            rt["members"][uid]["badge_emoji_id"] = my_prof["custom_badge_emoji_id"]
            rt["members"][uid]["bonds"] = my_prof["relationships"]["bonds_map"]
            rt["members"][uid]["marriage_link"] = my_prof["marriage_link"]
            rt["members"][uid]["bestie_link"] = my_prof["bestie_link"]

        if op == "take_seat":
            seat_idx = str(payload.get("seat_idx") or "1")
            if int(seat_idx) in rt["locked_seats"] and not is_room_admin:
                return {"ok": False, "error": "🔒 این میکروفون قفل شده است!", "active_room": _format_room_dict(r_row, uid)}
            if r_row["auto_lock_mics"] and not is_room_admin:
                return {"ok": False, "error": "🔒 قفل خودکار میکروفون‌ها در این اتاق فعال است!", "active_room": _format_room_dict(r_row, uid)}

            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)

            cur_occupant = rt["seats"].get(seat_idx)
            if cur_occupant and int(cur_occupant.get("uid", 0)) != uid and not is_room_admin:
                return {"ok": False, "error": "این صندلی پر است!", "active_room": _format_room_dict(r_row, uid)}

            if uid in rt["members"]:
                rt["members"][uid]["is_ghost"] = False

            rt["seats"][seat_idx] = {
                "uid": uid,
                "name": my_prof["display_name"],
                "photo": my_prof["photo"],
                "badge": my_prof["sub_badge"],
                "badge_emoji_id": my_prof["custom_badge_emoji_id"],
                "ring_css": my_prof["ring_css"],
                "ring_photo": my_prof["ring_photo"],
                "bonds": my_prof["relationships"]["bonds_map"],
                "marriage_link": my_prof["marriage_link"],
                "bestie_link": my_prof["bestie_link"],
                "muted": False,
                "speaking": True,
            }

        elif op == "leave_seat":
            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)

        elif op == "toggle_my_mic":
            for k, v in rt["seats"].items():
                if v and int(v.get("uid", 0)) == uid:
                    v["muted"] = not bool(v.get("muted"))
                    v["speaking"] = not v["muted"]

        elif op == "chat":
            txt = str(payload.get("text") or "").strip()[:120]
            if txt:
                rt["chats"].append({
                    "sys": False,
                    "uid": uid,
                    "name": my_prof["display_name"],
                    "badge": my_prof["sub_badge"],
                    "badge_emoji_id": my_prof["custom_badge_emoji_id"],
                    "text": txt,
                })
                # افزایش امتیاز ارتباط با افراد حاضر در اتاق
                for m_uid in list(rt["members"].keys())[:8]:
                    if int(m_uid) != uid:
                        await _add_affinity(uid, int(m_uid), 2)

        # ─── ارسال گیفت به شخص یا اشخاص مشخص در روم + افزایش لول ثروت، جذابیت و لول روم ───
        elif op == "send_gift":
            gift_id = int(payload.get("gift_id") or 0)
            rec_uids_raw = payload.get("recipient_uids") or []
            if not isinstance(rec_uids_raw, list) or not rec_uids_raw:
                rec_uids = [int(r_row["owner_id"])]
            else:
                rec_uids = [int(x) for x in rec_uids_raw if int(x) > 0]
            if not rec_uids:
                rec_uids = [int(r_row["owner_id"])]

            g_row = await db.pool.fetchrow("SELECT * FROM sp_store_items WHERE id=$1 AND category='gift'", gift_id)
            if not g_row:
                return {"ok": False, "error": "گیفت یافت نشد!"}

            unit_price = int(g_row["price_coins"] or 100)
            total_cost = unit_price * len(rec_uids)
            if my_prof["coins"] < total_cost:
                return {"ok": False, "error": f"سکه کافی ندارید! ({total_cost:,} 🪙 برای {len(rec_uids)} نفر نیاز است)"}

            # کسر سکه و افزایش لول ثروت (Wealth) فرستنده
            await db.pool.execute(
                "UPDATE sp_profiles SET coins=coins-$1, wealth_pts=wealth_pts+$1 WHERE user_id=$2",
                total_cost, uid
            )

            rec_names = []
            for target_u in rec_uids:
                t_prof = await get_or_create_sp_profile(target_u)
                rec_names.append(t_prof["display_name"])
                inv = t_prof["received_gifts_inv"]
                found = False
                for item in inv:
                    if int(item.get("id", 0)) == gift_id:
                        item["count"] = int(item.get("count", 1)) + 1
                        found = True
                        break
                if not found:
                    inv.append({
                        "id": gift_id,
                        "name": g_row["name"],
                        "icon": g_row["icon"],
                        "photo": g_row["photo"] or "",
                        "custom_emoji_id": g_row["custom_emoji_id"] or "",
                        "count": 1,
                    })
                # افزایش لول جذابیت (Charm) گیرنده و ثبت گیفت در کلکسیون پروفایلش
                await db.pool.execute(
                    """UPDATE sp_profiles
                       SET gifts_received=gifts_received+1,
                           charm_pts=charm_pts+$1,
                           coins=coins+$2,
                           received_gifts_inv=$3
                       WHERE user_id=$4""",
                    unit_price, int(unit_price * 0.35), json.dumps(inv), target_u
                )
                await _add_affinity(uid, target_u, max(15, unit_price // 20))

            # افزایش مجموع گیفت‌های روم و محاسبه لول جدید روم (تا ۵۰)
            new_room_total = int(r_row["total_gifts"] or 0) + total_cost
            new_rm_lvl, _, _ = calc_room_level_50(new_room_total)
            await db.pool.execute(
                "UPDATE sp_voice_rooms SET total_gifts=$1, level=$2 WHERE room_id=$3",
                new_room_total, new_rm_lvl, room_id
            )

            # ثبت افکت تمام‌صفحه گیفت با اوپاسیتی ملایم در وسط روم برای چند ثانیه
            rt["gift_fx"] = {
                "id": f"gfx_{int(now*1000)}",
                "ts": now,
                "sender": my_prof["display_name"],
                "recipients": "، ".join(rec_names),
                "gift_name": g_row["name"],
                "icon": g_row["icon"],
                "photo": g_row["photo"] or "",
                "custom_emoji_id": g_row["custom_emoji_id"] or "",
                "coins": total_cost,
            }

            rt["chats"].append({
                "sys": True,
                "gift": True,
                "text": f"🎁 {my_prof['display_name']} هدیه «{g_row['icon']} {g_row['name']}» ({total_cost:,} 🪙) به {', '.join(rec_names)} تقدیم کرد!",
            })
            if rt["pk_active"]:
                if len(rt["chats"]) % 2 == 0:
                    rt["pk_score_a"] += total_cost
                else:
                    rt["pk_score_b"] += total_cost
            r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

        elif op == "leave_room":
            rt["members"].pop(uid, None)
            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)
            return {"ok": True, "left": True, "state": await _collect_social_state(uid)}

        # عملیات‌های مدیریتی مالک و ادمین‌های روم
        elif is_room_admin:
            if op == "change_layout":
                mc = int(payload.get("mic_count") or 8)
                mm = str(payload.get("mic_mode") or "normal")
                rm_lvl, _, _ = calc_room_level_50(int(r_row["total_gifts"] or 0))
                max_mics = max_mics_for_room_level(rm_lvl)
                if mc > max_mics and uid not in OWNER_IDS:
                    return {
                        "ok": False,
                        "error": f"🔒 چیدمان {mc} مایک در لول فعلی اتاق (Lv.{rm_lvl}) قفل است! با ارسال گیفت لول اتاق را بالا ببرید.",
                        "active_room": _format_room_dict(r_row, uid),
                    }
                await db.pool.execute("UPDATE sp_voice_rooms SET mic_count=$1, mic_mode=$2 WHERE room_id=$3", mc, mm, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
                rt["chats"].append({"sys": True, "text": f"🎛️ چیدمان اتاق به «{mc} Mic ({mm.upper()})» تغییر یافت."})

            elif op == "toggle_seat_lock":
                s_idx = int(payload.get("seat_idx") or 1)
                if s_idx in rt["locked_seats"]:
                    rt["locked_seats"].remove(s_idx)
                else:
                    rt["locked_seats"].append(s_idx)

            elif op == "invite_to_seat":
                target_u = int(payload.get("target_uid") or 0)
                s_idx = str(payload.get("seat_idx") or "1")
                if target_u > 0:
                    rt.setdefault("mic_invites", {})[target_u] = s_idx
                    t_name = rt["members"].get(target_u, {}).get("name") or f"User {target_u}"
                    rt["chats"].append({"sys": True, "text": f"🎙️ {t_name} توسط مدیر اتاق به میکروفون شماره {s_idx} دعوت شد."})

            elif op == "kick_from_seat":
                s_idx = str(payload.get("seat_idx") or "1")
                rt["seats"].pop(s_idx, None)

            elif op == "set_room_admin" and is_room_owner:
                target_u = int(payload.get("target_uid") or 0)
                if target_u and target_u != int(r_row["owner_id"]):
                    if target_u in admins_list:
                        admins_list.remove(target_u)
                        act_str = "از لیست ادمین‌های اتاق عزل شد"
                    else:
                        admins_list.append(target_u)
                        act_str = "به عنوان ادمین اتاق منصوب شد"
                    await db.pool.execute("UPDATE sp_voice_rooms SET admins_list=$1 WHERE room_id=$2", json.dumps(admins_list), room_id)
                    r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
                    rt["chats"].append({"sys": True, "text": f"🛡️ کاربر {target_u} {act_str}."})

            elif op == "toggle_lock_room" and is_room_owner:
                if not my_prof["can_lock_room"]:
                    return {"ok": False, "error": "🔒 قفل کردن اتاق مخصوص اشتراک PRO به بالاست!", "active_room": _format_room_dict(r_row, uid)}
                new_lock = not bool(r_row["is_locked"])
                pin = str(payload.get("pin_code") or r_row["pin_code"] or "1234").strip()
                await db.pool.execute("UPDATE sp_voice_rooms SET is_locked=$1, pin_code=$2 WHERE room_id=$3", new_lock, pin, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
                rt["chats"].append({"sys": True, "text": f"🔒 اتاق توسط مالک {'قفل شد' if new_lock else 'باز شد'}."})

            elif op == "toggle_auto_lock_mics":
                new_al = not bool(r_row["auto_lock_mics"])
                await db.pool.execute("UPDATE sp_voice_rooms SET auto_lock_mics=$1 WHERE room_id=$2", new_al, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

            elif op == "clear_chat":
                rt["chats"] = [{"sys": True, "text": "🧹 تاریخچه چت اتاق پاکسازی شد."}]

            elif op == "toggle_music":
                rt["music_playing"] = not rt["music_playing"]

            elif op == "toggle_pk":
                rt["pk_active"] = not rt["pk_active"]
                rt["pk_score_a"] = 0
                rt["pk_score_b"] = 0
                rt["chats"].append({"sys": True, "text": "⚔️ رقابت PK آغاز شد!" if rt["pk_active"] else "🏁 رقابت PK پایان یافت."})

            elif op == "change_bg":
                bg = str(payload.get("bg_theme") or "lighthouse")
                await db.pool.execute("UPDATE sp_voice_rooms SET bg_theme=$1 WHERE room_id=$2", bg, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

        return {
            "ok": True,
            "active_room": _format_room_dict(r_row, uid),
            "state": await _collect_social_state(uid),
        }

    # ─── ۸. چت خصوصی (PV) داخل مینی‌اپ با پشتیبانی از ویس، پس‌زمینه و ایموجی پریمیوم ───
    elif action == "pm_op":
        sub_op = str(payload.get("op") or "load")
        peer_uid = int(payload.get("peer_uid") or 0)
        if peer_uid <= 0:
            return {"ok": False, "error": "مخاطب نامعتبر است!"}

        a, b = _pair_key(uid, peer_uid)
        if sub_op == "send":
            msg_type = str(payload.get("msg_type") or "text")
            txt = str(payload.get("text") or "").strip()[:300]
            voice_data = str(payload.get("voice_data") or "").strip()
            if txt or voice_data:
                await db.pool.execute(
                    """INSERT INTO sp_pm_messages (sender_id, receiver_id, msg_type, text, voice_data, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    uid, peer_uid, msg_type, txt, voice_data, now
                )
                await _add_affinity(uid, peer_uid, 5)

        elif sub_op == "set_bg":
            bg_val = str(payload.get("chat_bg") or "").strip()
            await _add_affinity(uid, peer_uid, 1)
            await db.pool.execute(
                "UPDATE sp_relationships SET chat_bg=$1 WHERE user_a=$2 AND user_b=$3",
                bg_val, a, b
            )

        peer_prof = await get_or_create_sp_profile(peer_uid)
        rel_row = await db.pool.fetchrow("SELECT * FROM sp_relationships WHERE user_a=$1 AND user_b=$2", a, b)
        msgs_rows = await db.pool.fetch(
            """SELECT id, sender_id, receiver_id, msg_type, text, voice_data, created_at
               FROM sp_pm_messages
               WHERE (sender_id=$1 AND receiver_id=$2) OR (sender_id=$2 AND receiver_id=$1)
               ORDER BY id DESC LIMIT 35""",
            uid, peer_uid
        )
        msgs_list = [
            {
                "id": r["id"],
                "sender_id": r["sender_id"],
                "msg_type": r["msg_type"],
                "text": r["text"],
                "voice_data": r["voice_data"],
                "time": time.strftime("%H:%M", time.localtime(r["created_at"] or now)),
            }
            for r in reversed(msgs_rows)
        ]

        return {
            "ok": True,
            "pm_chat": {
                "peer": peer_prof,
                "messages": msgs_list,
                "affinity_level": int(rel_row["affinity_level"] or 1) if rel_row else 1,
                "affinity_pts": int(rel_row["affinity_pts"] or 0) if rel_row else 0,
                "rel_type": rel_row["rel_type"] if rel_row else "none",
                "chat_bg": rel_row["chat_bg"] if rel_row else "",
            },
            "state": await _collect_social_state(uid),
        }

    # ─── ۹. سیستم روابط: درخواست و تایید ازدواج (۱ نفر) یا رفاقت (تا ۵ نفر) ───
    elif action == "rel_op":
        op = str(payload.get("op") or "propose")
        target_uid = int(payload.get("target_uid") or 0)
        rel_kind = str(payload.get("rel_type") or "bestie")  # marriage | bestie
        cost = 5000 if rel_kind == "marriage" else 2000

        if target_uid <= 0 or target_uid == uid:
            return {"ok": False, "error": "کاربر انتخاب‌شده نامعتبر است!"}

        a, b = _pair_key(uid, target_uid)
        my_rels = my_prof["relationships"]
        target_prof = await get_or_create_sp_profile(target_uid)
        target_rels = target_prof["relationships"]

        if op == "propose":
            if rel_kind == "marriage":
                if my_rels["marriage"]:
                    return {"ok": False, "error": "💍 شما در حال حاضر یک پارتنر ازدواج دارید! (سقف ازدواج: ۱ نفر)"}
                if target_rels["marriage"]:
                    return {"ok": False, "error": "💍 کاربر مقابل در حال حاضر ازدواج کرده است!"}
            else:
                if len(my_rels["besties"]) >= 5:
                    return {"ok": False, "error": "⚡ لیست رفقای صمیمی شما پر است! (حداکثر ۵ رفیق)"}
                if len(target_rels["besties"]) >= 5:
                    return {"ok": False, "error": "⚡ لیست رفقای صمیمی کاربر مقابل پر است!"}

            if my_prof["coins"] < cost:
                return {"ok": False, "error": f"برای ثبت پیشنهاد {rel_kind} به {cost:,} 🪙 سکه نیاز دارید!"}

            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", cost, uid)
            await _add_affinity(uid, target_uid, 50)
            await db.pool.execute(
                "UPDATE sp_relationships SET pending_type=$1, requested_by=$2, updated_at=$3 WHERE user_a=$4 AND user_b=$5",
                rel_kind, uid, now, a, b
            )
            msg_out = f"💌 پیشنهاد «{'ازدواج 💍' if rel_kind=='marriage' else 'رفاقت صمیمی ⚡'}» برای {target_prof['display_name']} ارسال شد!"

        elif op == "respond":
            accept = bool(payload.get("accept", True))
            row = await db.pool.fetchrow("SELECT * FROM sp_relationships WHERE user_a=$1 AND user_b=$2", a, b)
            if not row or not row["pending_type"]:
                return {"ok": False, "error": "درخواست فعالی یافت نشد!"}
            p_type = row["pending_type"]
            if accept:
                await db.pool.execute(
                    "UPDATE sp_relationships SET rel_type=$1, pending_type='', requested_by=0, affinity_pts=affinity_pts+200 WHERE id=$2",
                    p_type, row["id"]
                )
                msg_out = f"🎉 تبریک! رابطه «{'ازدواج 💍' if p_type=='marriage' else 'رفاقت ⚡'}» شما رسمی شد!"
            else:
                await db.pool.execute("UPDATE sp_relationships SET pending_type='', requested_by=0 WHERE id=$1", row["id"])
                msg_out = "درخواست رابطه رد شد."

        elif op == "break":
            await db.pool.execute(
                "UPDATE sp_relationships SET rel_type='none', pending_type='', requested_by=0 WHERE user_a=$1 AND user_b=$2",
                a, b
            )
            msg_out = "رابطه پایان یافت."

        return {"ok": True, "msg": msg_out, "state": await _collect_social_state(uid)}

    # ─── ۱۰. خرید اشتراک، حلقه دور پروفایل و خط رابط ازدواج/رفاقت ───
    elif action == "buy_subscription":
        tier_id = str(payload.get("tier_id") or "pro").lower()
        pay_method = str(payload.get("pay_method") or "coins")
        tier = SUB_TIERS.get(tier_id)
        if not tier or tier_id == "free":
            return {"ok": False, "error": "اشتراک نامعتبر است!", "state": await _collect_social_state(uid)}

        exp_ts = now + (tier["days"] * 86400)
        if pay_method == "coins":
            if my_prof["coins"] < tier["coins"]:
                return {"ok": False, "error": f"موجودی سکه کافی نیست! ({tier['coins']:,} 🪙 نیاز است)", "state": await _collect_social_state(uid)}
            await db.pool.execute(
                "UPDATE sp_profiles SET coins=coins-$1, sub_tier=$2, sub_expires_at=$3 WHERE user_id=$4",
                tier["coins"], tier_id, exp_ts, uid
            )
            return {"ok": True, "msg": f"🎉 تبریک! «{tier['title']}» فعال شد!", "state": await _collect_social_state(uid)}
        else:
            bot_token = os.environ.get("BOT_TOKEN", "")
            temp_bot = Bot(token=bot_token)
            try:
                inv_link = await temp_bot.create_invoice_link(
                    title=tier["title"],
                    description=" | ".join(tier["perks"]),
                    payload=f"spsub_{tier_id}_{uid}",
                    provider_token="",
                    currency="XTR",
                    prices=[LabeledPrice(label=tier["title"], amount=tier["stars"])],
                )
                return {"ok": True, "invoice_link": inv_link, "state": await _collect_social_state(uid)}
            except Exception as e:
                return {"ok": False, "error": str(e), "state": await _collect_social_state(uid)}
            finally:
                await temp_bot.session.close()

    elif action == "buy_or_equip_ring":
        ring_id = int(payload.get("ring_id") or 0)
        if ring_id == 0:
            await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=0 WHERE user_id=$1", uid)
            return {"ok": True, "msg": "حلقه دور پروفایل برداشته شد.", "state": await _collect_social_state(uid)}

        r_row = await db.pool.fetchrow("SELECT * FROM sp_store_items WHERE id=$1", ring_id)
        if not r_row:
            return {"ok": False, "error": "آیتم مورد نظر یافت نشد!", "state": await _collect_social_state(uid)}

        cat = r_row["category"]
        if cat == "ring":
            owned = [int(x) for x in my_prof["owned_rings"]]
            if ring_id not in owned:
                if my_prof["coins"] < r_row["price_coins"]:
                    return {"ok": False, "error": f"موجودی سکه کافی نیست! ({r_row['price_coins']:,} 🪙 نیاز است)", "state": await _collect_social_state(uid)}
                owned.append(ring_id)
                await db.pool.execute(
                    "UPDATE sp_profiles SET coins=coins-$1, owned_rings=$2, avatar_ring_id=$3 WHERE user_id=$4",
                    r_row["price_coins"], json.dumps(owned), ring_id, uid
                )
            else:
                await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=$1 WHERE user_id=$2", ring_id, uid)
            return {"ok": True, "msg": f"✅ قاب «{r_row['name']}» دور آواتار شما فعال شد!", "state": await _collect_social_state(uid)}

        elif cat in ("rel_marriage", "rel_bestie"):
            owned_links = [int(x) for x in my_prof["owned_rel_links"]]
            col_name = "active_marriage_link_id" if cat == "rel_marriage" else "active_bestie_link_id"
            if ring_id not in owned_links:
                if my_prof["coins"] < r_row["price_coins"]:
                    return {"ok": False, "error": f"موجودی سکه کافی نیست! ({r_row['price_coins']:,} 🪙 نیاز است)", "state": await _collect_social_state(uid)}
                owned_links.append(ring_id)
                await db.pool.execute(
                    f"UPDATE sp_profiles SET coins=coins-$1, owned_rel_links=$2, {col_name}=$3 WHERE user_id=$4",
                    r_row["price_coins"], json.dumps(owned_links), ring_id, uid
                )
            else:
                await db.pool.execute(f"UPDATE sp_profiles SET {col_name}=$1 WHERE user_id=$2", ring_id, uid)
            return {"ok": True, "msg": f"✅ خط رابط «{r_row['name']}» فعال شد!", "state": await _collect_social_state(uid)}

    return {"ok": True, "msg": msg_out, "state": await _collect_social_state(uid)}


async def _collect_social_state(uid: int) -> dict:
    my_prof = await get_or_create_sp_profile(uid)
    rooms_rows = await db.pool.fetch("SELECT * FROM sp_voice_rooms ORDER BY total_gifts DESC, room_id DESC LIMIT 40")
    rooms_list = [_format_room_dict(r, uid) for r in rooms_rows]
    store_rows = await db.pool.fetch("SELECT * FROM sp_store_items ORDER BY id DESC")
    store_items = [dict(r) for r in store_rows]

    chat_emojis_raw = await get_sp_config("chat_emoji_packs", "[]")
    try:
        chat_emojis = json.loads(chat_emojis_raw)
    except Exception:
        chat_emojis = []

    inbox_rows = await db.pool.fetch("""
        SELECT DISTINCT CASE WHEN sender_id=$1 THEN receiver_id ELSE sender_id END AS peer_id
        FROM sp_pm_messages
        WHERE sender_id=$1 OR receiver_id=$1
        LIMIT 20
    """, int(uid))
    inbox_peers = []
    for ir in inbox_rows:
        p_id = int(ir["peer_id"])
        p_row = await db.pool.fetchrow("SELECT user_id, display_name, photo, sub_tier FROM sp_profiles WHERE user_id=$1", p_id)
        if p_row:
            inbox_peers.append(dict(p_row))

    return {
        "me": my_prof,
        "rooms": rooms_list,
        "store_items": store_items,
        "sub_tiers": list(SUB_TIERS.values()),
        "profile_themes": PROFILE_THEMES,
        "topup_packs": STAR_TOPUP_PACKS,
        "rate": STARS_TO_COINS_RATE,
        "big_wins": recent_big_wins[:8],
        "chat_emojis": chat_emojis,
        "inbox_peers": inbox_peers,
    }


# ═══════════════════════════════════════════════════════════════════════════
# پنل مدیریت کل پلتفرم راینو (با پشتیبانی از ایموجی پریمیوم گیفت/روابط و ریست کلی)
# ═══════════════════════════════════════════════════════════════════════════
async def handle_platform_admin_api(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    if uid not in OWNER_IDS:
        return {"ok": False, "error": "⛔ دسترسی غیرمجاز! فقط مالک ربات دسترسی دارد."}

    await ensure_social_tables()
    action = str(payload.get("action") or "state")
    msg_out = ""

    if action == "reset_all_platform":
        await reset_all_levels_and_balances()
        msg_out = "♻️ تمام موجودی‌های سکه/استارز، لول‌های ثروت و جذابیت کاربران و دیتابیس اتاق‌های صوتی صفر و ریست شدند!"

    elif action == "save_ui_asset":
        asset_key = str(payload.get("asset_key") or "").strip()
        photo_data = str(payload.get("photo") or "").strip()
        if asset_key and photo_data:
            raw_assets = await get_sp_config("ui_assets", "{}")
            try:
                assets_map = json.loads(raw_assets)
            except Exception:
                assets_map = {}
            assets_map[asset_key] = photo_data
            await set_sp_config("ui_assets", json.dumps(assets_map))
            msg_out = f"✅ تصویر «{asset_key}» با موفقیت ذخیره شد!"
        else:
            return {"ok": False, "error": "⚠️ ابتدا فایل تصویر را انتخاب کنید.", "admin_data": await _collect_platform_admin_state()}

    elif action == "delete_ui_asset":
        asset_key = str(payload.get("asset_key") or "").strip()
        raw_assets = await get_sp_config("ui_assets", "{}")
        try:
            assets_map = json.loads(raw_assets)
        except Exception:
            assets_map = {}
        assets_map.pop(asset_key, None)
        await set_sp_config("ui_assets", json.dumps(assets_map))
        msg_out = f"🗑️ تصویر «{asset_key}» به حالت پیش‌فرض بازگشت."

    elif action == "save_store_item":
        cat = str(payload.get("category") or "ring")
        name = str(payload.get("name") or "آیتم جدید").strip()
        icon = str(payload.get("icon") or "⭕").strip()
        photo = str(payload.get("photo") or "").strip()
        custom_emoji_id = str(payload.get("custom_emoji_id") or "").strip()
        ring_css = str(payload.get("ring_css") or "").strip()
        p_coins = int(payload.get("price_coins") or 1500)
        p_stars = int(payload.get("price_stars") or 20)
        await db.pool.execute(
            """INSERT INTO sp_store_items (category, name, icon, photo, custom_emoji_id, ring_css, price_coins, price_stars)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
            cat, name, icon, photo, custom_emoji_id, ring_css, p_coins, p_stars
        )
        msg_out = f"✅ آیتم «{name}» به فروشگاه اضافه شد و هم‌اکنون برای همه قابل خرید است!"

    elif action == "delete_store_item":
        item_id = int(payload.get("item_id") or 0)
        await db.pool.execute("DELETE FROM sp_store_items WHERE id=$1", item_id)
        msg_out = "🗑️ آیتم از فروشگاه حذف شد."

    elif action == "save_default_rel_emojis":
        m_eid = str(payload.get("marriage_emoji_id") or "").strip()
        m_ico = str(payload.get("marriage_icon") or "💍").strip()
        b_eid = str(payload.get("bestie_emoji_id") or "").strip()
        b_ico = str(payload.get("bestie_icon") or "⚡").strip()
        await set_sp_config("default_marriage_emoji_id", m_eid)
        await set_sp_config("default_marriage_icon", m_ico)
        await set_sp_config("default_bestie_emoji_id", b_eid)
        await set_sp_config("default_bestie_icon", b_ico)
        msg_out = "✅ ایموجی‌های پیش‌فرض خط رابط ازدواج و رفاقت ذخیره شدند!"

    elif action == "add_chat_emoji_pack":
        eid = str(payload.get("custom_emoji_id") or "").strip()
        ico = str(payload.get("icon") or "✨").strip()
        raw = await get_sp_config("chat_emoji_packs", "[]")
        try:
            packs = json.loads(raw)
        except Exception:
            packs = []
        if eid or ico:
            packs.append({"id": eid, "icon": ico})
            await set_sp_config("chat_emoji_packs", json.dumps(packs[-40:]))
            msg_out = "✅ ایموجی متحرک به کیبورد چت اضافه شد!"

    elif action == "clear_chat_emoji_packs":
        await set_sp_config("chat_emoji_packs", "[]")
        msg_out = "🗑️ کیبورد ایموجی‌های چت پاکسازی شد."

    elif action == "arm_admin_emoji_capture":
        cap_mode = str(payload.get("cap_mode") or "gift")  # gift | chat_pack | rel_marriage | rel_bestie
        await set_sp_config(f"user_emoji_wait_{uid}", f"adm_{cap_mode}")
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                await temp_bot.send_message(
                    chat_id=uid,
                    text=(
                        f"✨ <b>دریافت ایموجی پریمیوم متحرک ({cap_mode}):</b>\n\n"
                        f"لطفاً همین الان یک یا چند <b>ایموجی پریمیوم متحرک تلگرام</b> در همین پیوی بفرستید تا آیدی و انیمیشن آن‌ها ثبت شود:"
                    ),
                    parse_mode=ParseMode.HTML,
                )
            finally:
                await temp_bot.session.close()
        return {"ok": True, "msg": "📩 در پیوی ربات ایموجی پریمیوم را بفرستید!", "admin_data": await _collect_platform_admin_state()}

    elif action == "bot_add_channel":
        chat_id = str(payload.get("chat_id") or "").strip()
        title = str(payload.get("title") or chat_id).strip()
        username = str(payload.get("username") or "").strip().lstrip("@")
        if not username and chat_id.startswith("@"):
            username = chat_id.lstrip("@")
        if chat_id:
            try:
                await db.add_channel(chat_id, title, username)
            except Exception:
                await db.pool.execute(
                    "INSERT INTO forced_channels (chat_id, title, username) VALUES ($1, $2, $3) ON CONFLICT (chat_id) DO UPDATE SET title=$2, username=$3",
                    chat_id, title, username
                )
            msg_out = f"✅ کانال «{title}» به قفل اجباری اضافه شد."

    elif action == "bot_del_channel":
        chat_id = str(payload.get("chat_id") or "").strip()
        try:
            await db.remove_channel(chat_id)
        except Exception:
            await db.pool.execute("DELETE FROM forced_channels WHERE chat_id=$1", chat_id)
        msg_out = "🗑️ کانال حذف شد."

    elif action == "bot_arm_bc_capture":
        await set_sp_config(f"bc_waiting_{uid}", "1")
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                await temp_bot.send_message(
                    chat_id=uid,
                    text="📝 <b>ربات آماده دریافت پیام همگانی شماست!</b>\n\nپیام خود را در همین پیوی بفرستید:",
                    reply_markup=kb([[danger("❌ انصراف", "adm:cancel_bc_capture")]]),
                    parse_mode=ParseMode.HTML,
                )
            finally:
                await temp_bot.session.close()
        return {"ok": True, "msg": "📩 ربات در پیوی آماده دریافت پیام شماست!", "admin_data": await _collect_platform_admin_state()}

    elif action == "bot_clear_bc_draft":
        await set_sp_config("bc_draft", "")
        msg_out = "🗑️ پیش‌نویس پیام همگانی پاک شد."

    elif action == "bot_broadcast":
        draft_raw = await get_sp_config("bc_draft", "")
        target_type = str(payload.get("target_type") or "users")
        btn_text = str(payload.get("btn_text") or "").strip()
        btn_url = str(payload.get("btn_url") or "").strip()
        if not draft_raw:
            return {"ok": False, "error": "⚠️ ابتدا پیام خود را در پیوی ثبت کنید!", "admin_data": await _collect_platform_admin_state()}

        draft = json.loads(draft_raw)
        rows = await db.pool.fetch("SELECT chat_id AS id FROM groups" if target_type == "groups" else "SELECT user_id AS id FROM users")
        target_ids = [r["id"] for r in rows]

        bot_token = os.environ.get("BOT_TOKEN", "")
        sent_ok, sent_fail = 0, 0
        if bot_token and target_ids:
            try:
                from main import EmojiBot
                temp_bot = EmojiBot(token=bot_token)
            except Exception:
                temp_bot = Bot(token=bot_token)
            markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_text, url=btn_url)]]) if (btn_text and btn_url) else None
            try:
                for tid in target_ids:
                    try:
                        if draft.get("has_shortcode"):
                            await temp_bot.send_message(tid, draft["raw_html"], reply_markup=markup, parse_mode=ParseMode.HTML)
                        else:
                            await temp_bot.copy_message(tid, draft["src_chat_id"], draft["src_msg_id"], reply_markup=markup)
                        sent_ok += 1
                    except Exception:
                        sent_fail += 1
                    await asyncio.sleep(0.035)
            finally:
                await temp_bot.session.close()
        msg_out = f"🏁 ارسال همگانی تمام شد!\n✅ موفق: {sent_ok} | ❌ ناموفق: {sent_fail}"

    elif action == "Lookup_user":
        t_uid = int(payload.get("target_uid") or 0)
        prof = await get_or_create_sp_profile(t_uid)
        u_main = await db.get_user(t_uid)
        prof["global_banned"] = bool(u_main["is_banned"]) if u_main else prof["is_banned"]
        prof["is_bot_admin"] = await db.is_admin(t_uid)
        return {"ok": True, "looked_up": prof, "admin_data": await _collect_platform_admin_state()}

    elif action == "charge_user":
        t_uid = int(payload.get("target_uid") or 0)
        add_c = int(payload.get("add_coins") or 0)
        add_s = int(payload.get("add_stars") or 0)
        set_tier = str(payload.get("set_tier") or "").strip()
        await get_or_create_sp_profile(t_uid)
        await db.pool.execute(
            "UPDATE sp_profiles SET coins=coins+$1, stars_balance=stars_balance+$2 WHERE user_id=$3",
            add_c, add_s, t_uid
        )
        if set_tier in ("free", "pro", "plus", "ultra"):
            exp = (time.time() + 30 * 86400) if set_tier != "free" else 0
            await db.pool.execute("UPDATE sp_profiles SET sub_tier=$1, sub_expires_at=$2 WHERE user_id=$3", set_tier, exp, t_uid)
        prof = await get_or_create_sp_profile(t_uid)
        return {
            "ok": True,
            "msg": f"✅ حساب {t_uid} بروزرسانی شد (+{add_c} سکه | +{add_s} استارز | اشتراک: {prof['sub_tier'].upper()})",
            "looked_up": prof,
            "admin_data": await _collect_platform_admin_state(),
        }

    elif action == "bot_global_ban":
        t_uid = int(payload.get("target_id") or 0)
        ban_st = bool(payload.get("ban"))
        await db.pool.execute("UPDATE users SET is_banned=$1 WHERE user_id=$2", ban_st, t_uid)
        await db.pool.execute("UPDATE sp_profiles SET is_banned=$1 WHERE user_id=$2", ban_st, t_uid)
        prof = await get_or_create_sp_profile(t_uid)
        prof["global_banned"] = ban_st
        return {"ok": True, "msg": f"وضعیت مسدودیت {t_uid} تغییر کرد.", "looked_up": prof, "admin_data": await _collect_platform_admin_state()}

    elif action == "bot_group_link":
        chat_id = int(payload.get("chat_id") or 0)
        bot_token = os.environ.get("BOT_TOKEN", "")
        if chat_id and bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                link_obj = await temp_bot.create_chat_invite_link(chat_id)
                return {"ok": True, "msg": f"🔗 لینک گروه:\n{link_obj.invite_link}", "admin_data": await _collect_platform_admin_state()}
            except Exception as e:
                return {"ok": False, "error": str(e), "admin_data": await _collect_platform_admin_state()}
            finally:
                await temp_bot.session.close()

    elif action == "bot_leave_group":
        chat_id = int(payload.get("chat_id") or 0)
        bot_token = os.environ.get("BOT_TOKEN", "")
        if chat_id and bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                await temp_bot.leave_chat(chat_id)
            except Exception:
                pass
            finally:
                await temp_bot.session.close()
            await db.pool.execute("DELETE FROM groups WHERE chat_id=$1", chat_id)
            msg_out = f"🚪 ربات از گروه {chat_id} خارج شد."

    return {
        "ok": True,
        "msg": msg_out,
        "admin_data": await _collect_platform_admin_state(),
        "state": await _collect_social_state(uid),
    }


async def _collect_platform_admin_state() -> dict:
    await ensure_social_tables()
    users_cnt, groups_cnt, rooms_cnt, vip_cnt = 0, 0, 0, 0
    try:
        users_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
        groups_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
        rooms_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM sp_voice_rooms") or 0
        vip_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM sp_profiles WHERE sub_tier != 'free'") or 0
    except Exception:
        pass

    ui_assets = {}
    try:
        ui_assets_raw = await get_sp_config("ui_assets", "{}")
        if ui_assets_raw:
            ui_assets = json.loads(ui_assets_raw)
    except Exception:
        pass

    bc_draft = None
    try:
        bc_draft_raw = await get_sp_config("bc_draft", "")
        if bc_draft_raw:
            bc_draft = json.loads(bc_draft_raw)
    except Exception:
        pass

    forced_channels, groups_list, store_items, users_list = [], [], [], []
    try:
        forced_channels = [dict(r) for r in await db.pool.fetch("SELECT chat_id, title, username FROM forced_channels")]
    except Exception:
        pass
    try:
        groups_list = [dict(r) for r in await db.pool.fetch("SELECT chat_id, title FROM groups LIMIT 50")]
    except Exception:
        pass
    try:
        store_items = [dict(r) for r in await db.pool.fetch("SELECT * FROM sp_store_items ORDER BY id DESC")]
    except Exception:
        pass
    try:
        u_rows = await db.pool.fetch("""
            SELECT
                u.user_id, u.first_name, u.username, u.language,
                u.is_banned AS global_banned,
                EXISTS (
                    SELECT 1 FROM admins a WHERE a.user_id = u.user_id
                    ) AS is_bot_admin,
                COALESCE(sp.coins, 1000) AS coins,
                COALESCE(sp.stars_balance, 0) AS stars_balance,
                COALESCE(sp.sub_tier, 'free') AS sub_tier
            FROM users u
            LEFT JOIN sp_profiles sp ON u.user_id = sp.user_id
            ORDER BY u.user_id DESC LIMIT 200
        """)
        users_list = [dict(r) for r in u_rows]
    except Exception:
        pass

    last_captured_emoji = await get_sp_config("last_captured_emoji_id", "")
    last_captured_icon = await get_sp_config("last_captured_emoji_icon", "🎁")
    def_m_eid = await get_sp_config("default_marriage_emoji_id", "")
    def_m_ico = await get_sp_config("default_marriage_icon", "💍")
    def_b_eid = await get_sp_config("default_bestie_emoji_id", "")
    def_b_ico = await get_sp_config("default_bestie_icon", "⚡")

    return {
        "bot_stats": {"users": users_cnt, "groups": groups_cnt, "rooms": rooms_cnt, "vips": vip_cnt},
        "ui_assets": ui_assets,
        "bc_draft": bc_draft,
        "forced_channels": forced_channels,
        "groups_list": groups_list,
        "store_items": store_items,
        "users_list": users_list,
        "last_captured_emoji_id": last_captured_emoji,
        "last_captured_emoji_icon": last_captured_icon,
        "default_marriage_emoji_id": def_m_eid,
        "default_marriage_icon": def_m_ico,
        "default_bestie_emoji_id": def_b_eid,
        "default_bestie_icon": def_b_ico,
    }
