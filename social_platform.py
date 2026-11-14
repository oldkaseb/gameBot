# -*- coding: utf-8 -*-
"""social_platform.py — هسته مرکزی پلتفرم راینو: کیف پول (استارز/سکه)، کازینو، اتاق‌های صوتی، پروفایل، فروشگاه VIP و پنل مدیریت کل"""

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
STARS_TO_COINS_RATE = 100  # هر ۱ استارز = ۱۰۰ سکه

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
        "perks": [
            "نشان اختصاصی 🥈 PRO جلوی نام در کل پلتفرم",
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
        "perks": [
            "نشان اختصاصی 🥇 PLUS جلوی نام در کل پلتفرم",
            "🕵️ بازدید مخفی پروفایل دیگران (ثبت نشدن در لیست بازدیدکنندگان)",
            "🔒 قفل اتاق صوتی + رنگ‌های طلایی، نقره‌ای و نئونی پروفایل",
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
        "perks": [
            "نشان لوکس 💎 ULTRA جلوی نام در کل پلتفرم",
            "👻 ورود روح (Ghost Mode) به اتاق‌های صوتی بدون دیده‌شدن در لیست حاضرین",
            "🕵️ بازدید مخفی پروفایل + تمام تم‌ها و رنگ‌های سلطنتی کارت پروفایل",
        ],
    },
}

PROFILE_THEMES = [
    {"id": "slate",   "title": "سرمه‌ای کلاسیک", "tier": "free",  "css": "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"},
    {"id": "blue",    "title": "آبی تلگرامی",    "tier": "free",  "css": "linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%)"},
    {"id": "emerald", "title": "سبز زمردی",      "tier": "free",  "css": "linear-gradient(135deg, #047857 0%, #064e3b 100%)"},
    {"id": "purple",  "title": "بنفش شب",        "tier": "free",  "css": "linear-gradient(135deg, #6d28d9 0%, #3b0764 100%)"},
    {"id": "rose",    "title": "سرخ تیره",       "tier": "free",  "css": "linear-gradient(135deg, #be123c 0%, #4c0519 100%)"},
    {"id": "silver",  "title": "نقره‌ای متالیک (PRO)",   "tier": "pro",   "css": "linear-gradient(135deg, #cbd5e1 0%, #475569 55%, #0f172a 100%)"},
    {"id": "gold",    "title": "طلایی سلطنتی (PRO)",    "tier": "pro",   "css": "linear-gradient(135deg, #fbbf24 0%, #b45309 55%, #451a03 100%)"},
    {"id": "neon",    "title": "نئون سایبرپانک (PLUS)",  "tier": "plus",  "css": "linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #06b6d4 100%)"},
    {"id": "aurora",  "title": "شفق قطبی (PLUS)",       "tier": "plus",  "css": "linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #6366f1 100%)"},
    {"id": "royal",   "title": "امپراتور الماس (ULTRA)", "tier": "ultra", "css": "linear-gradient(135deg, #fbbf24 0%, #e11d48 45%, #4c1d95 100%)"},
    {"id": "abyss",   "title": "کهکشان تاریک (ULTRA)",   "tier": "ultra", "css": "radial-gradient(circle at top right, #c084fc, #3b0764 55%, #090514 100%)"},
]

TIER_RANK = {"free": 0, "pro": 1, "plus": 2, "ultra": 3}

live_rooms_runtime: dict[int, dict] = {}
bombs_sessions: dict[int, dict] = {}
recent_big_wins: list[dict] = [
    {"name": "RHINO VIP", "game": "CRASH", "win": 14500, "mult": "4.5x", "time": "1m ago"},
    {"name": "KING_77",   "game": "BOMBS", "win": 8200,  "mult": "3.2x", "time": "2m ago"},
    {"name": "SARA_PRO",  "game": "PICKAXE", "win": 6000, "mult": "6.0x", "time": "3m ago"},
]


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
                card_theme TEXT DEFAULT 'purple',
                avatar_ring_id INT DEFAULT 0,
                sub_tier TEXT DEFAULT 'free',
                sub_expires_at DOUBLE PRECISION DEFAULT 0,
                stealth_mode BOOLEAN DEFAULT TRUE,
                ghost_mode BOOLEAN DEFAULT TRUE,
                owned_rings TEXT DEFAULT '[]',
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
                ring_css TEXT DEFAULT '',
                price_coins INT DEFAULT 500,
                price_stars INT DEFAULT 25
            );
        """)

        # اطمینان از وجود ستون‌های جدید در صورت ساخته شدن جدول در نسخه قبلی
        for col_sql in (
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS coins BIGINT DEFAULT 1000",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS stars_balance BIGINT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS xp BIGINT DEFAULT 0",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS level INT DEFAULT 1",
            "ALTER TABLE sp_profiles ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
        ):
            try:
                await conn.execute(col_sql)
            except Exception:
                pass

        cnt = await conn.fetchval("SELECT COUNT(*) FROM sp_store_items")
        if not cnt:
            await conn.execute("""
                INSERT INTO sp_store_items (category, name, icon, photo, ring_css, price_coins, price_stars)
                VALUES
                ('ring', 'حلقه طلایی امپراتور', '👑', '', '0 0 0 3.5px #fbbf24, 0 0 18px #f59e0b', 1500, 15),
                ('ring', 'حلقه نئون سایبرپانک', '⚡', '', '0 0 0 3.5px #06b6d4, 0 0 20px #ec4899', 2500, 25),
                ('ring', 'حلقه آتش دوزخی', '🔥', '', '0 0 0 3.5px #ef4444, 0 0 22px #dc2626', 3500, 35),
                ('ring', 'حلقه الماس بنفش', '💎', '', '0 0 0 4px #e879f9, 0 0 25px #a855f7', 5000, 50),
                ('ring', 'حلقه زمرد نئونی', '🟢', '', '0 0 0 3.5px #10b981, 0 0 20px #059669', 2000, 20),
                ('gift', 'شاخه گل رز', '🌹', '', '', 100, 2),
                ('gift', 'تاج پادشاهی', '👑', '', '', 1000, 10),
                ('gift', 'موشک طلایی', '🚀', '', '', 2500, 25),
                ('gift', 'ابرماشین نئونی', '🏎️', '', '', 6000, 60);
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


def _get_live_room_state(room_id: int, mic_count: int) -> dict:
    if room_id not in live_rooms_runtime:
        live_rooms_runtime[room_id] = {
            "seats": {},
            "locked_seats": [],
            "members": {},
            "chats": [
                {"sys": True, "text": "به اتاق صوتی خوش آمدید! لطفاً قوانین و احترام متقابل را رعایت کنید."},
            ],
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
    ring_name = ""
    if prof.get("avatar_ring_id"):
        r_row = await db.pool.fetchrow("SELECT name, ring_css FROM sp_store_items WHERE id=$1", int(prof["avatar_ring_id"]))
        if r_row:
            ring_css = r_row["ring_css"] or ""
            ring_name = r_row["name"] or ""

    room_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
    my_room = dict(room_row) if room_row else None
    if my_room:
        rt = _get_live_room_state(my_room["room_id"], my_room["mic_count"])
        my_room["online_count"] = max(1, sum(1 for m in rt["members"].values() if not m.get("is_ghost")))

    lvl = max(1, int((prof.get("xp") or 0) // 200) + 1)

    return {
        "user_id": prof["user_id"],
        "display_name": prof["display_name"] or name or f"User {uid}",
        "username": prof["username"] or username,
        "photo": prof["photo"] or photo,
        "bio": prof["bio"],
        "coins": int(prof.get("coins") or 0),
        "stars_balance": int(prof.get("stars_balance") or 0),
        "xp": int(prof.get("xp") or 0),
        "level": lvl,
        "card_theme": prof["card_theme"] or "purple",
        "avatar_ring_id": int(prof.get("avatar_ring_id") or 0),
        "ring_css": ring_css,
        "ring_name": ring_name,
        "sub_tier": prof["sub_tier"],
        "sub_title": tier_info["title"],
        "sub_badge": tier_info["badge"],
        "sub_expires_rem_days": max(0, round((prof["sub_expires_at"] - now) / 86400, 1)) if prof["sub_expires_at"] > now else 0,
        "can_lock_room": tier_info["can_lock_room"] or (int(uid) in OWNER_IDS),
        "can_stealth_visit": tier_info["stealth_visit"] or (int(uid) in OWNER_IDS),
        "can_ghost_join": tier_info["ghost_join"] or (int(uid) in OWNER_IDS),
        "stealth_mode": bool(prof["stealth_mode"]),
        "ghost_mode": bool(prof["ghost_mode"]),
        "owned_rings": [int(x) for x in json.loads(prof["owned_rings"] or "[]")],
        "gifts_received": int(prof.get("gifts_received") or 0),
        "visitors_log": json.loads(prof["visitors_log"] or "[]"),
        "is_banned": bool(prof.get("is_banned", False)),
        "room": my_room,
    }


def _format_room_dict(r_row: dict, viewer_uid: int = 0) -> dict:
    r = dict(r_row)
    rt = _get_live_room_state(r["room_id"], r["mic_count"])
    visible_members = [m for m in rt["members"].values() if not m.get("is_ghost")]
    ghost_count = sum(1 for m in rt["members"].values() if m.get("is_ghost"))
    return {
        **r,
        "pin_code": r["pin_code"] if int(viewer_uid) == int(r["owner_id"]) or int(viewer_uid) in OWNER_IDS else "",
        "online_count": max(1, len(visible_members)),
        "visible_members": visible_members[:30],
        "ghost_count": ghost_count if int(viewer_uid) in OWNER_IDS else 0,
        "seats": rt["seats"],
        "locked_seats": rt["locked_seats"],
        "chats": rt["chats"][-25:],
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
                description=f"شارژ کیف پول به مقدار {total_stars} استارز (معادل {total_stars * STARS_TO_COINS_RATE:,} سکه)",
                payload=f"sptopup_{total_stars}_{uid}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Stars", amount=pack["stars"])],
            )
            return {"ok": True, "invoice_link": inv_link, "state": await _collect_social_state(uid)}
        except Exception as e:
            return {"ok": False, "error": str(e), "state": await _collect_social_state(uid)}
        finally:
            await temp_bot.session.close()

    elif action == "convert_stars_to_coins":
        stars_amt = int(payload.get("stars") or 0)
        if stars_amt <= 0:
            return {"ok": False, "error": "تعداد استارز برای تبدیل را وارد کنید!", "state": await _collect_social_state(uid)}
        if my_prof["stars_balance"] < stars_amt:
            return {
                "ok": False,
                "error": f"موجودی استارز کیف پول شما کافی نیست! (موجودی فعلی: {my_prof['stars_balance']} ⭐ — ابتدا کیف پول را شارژ کنید)",
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

        # الف) بازی BOMBS (مین‌روب ۲۵ خانه‌ای کازینو)
        if game == "bombs":
            if sub_op == "start":
                mines_cnt = int(payload.get("mines") or 5)
                mines_cnt = max(1, min(15, mines_cnt))
                if bet < 10 or bet > my_prof["coins"]:
                    return {"ok": False, "error": "موجودی سکه کافی نیست یا مبلغ شرط نامعتبر است!", "state": await _collect_social_state(uid)}
                await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)
                bombs_pos = random.sample(range(25), mines_cnt)
                bombs_sessions[uid] = {
                    "bet": bet,
                    "mines_count": mines_cnt,
                    "bombs": bombs_pos,
                    "revealed": [],
                    "mult": 1.0,
                    "active": True,
                    "game_over": False,
                    "won": False,
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
                await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1, xp=xp+15 WHERE user_id=$2", win_amt, uid)
                _record_big_win(my_prof["display_name"], "BOMBS", win_amt, f"{sess['mult']}x")
                return {
                    "ok": True,
                    "msg": f"🎉 برداشت موفق! +{win_amt:,} سکه (ضریب {sess['mult']}x) به کیف پول شما اضافه شد!",
                    "bombs_state": {"active": False, "game_over": True, "won": True, "bombs": sess["bombs"], "revealed": sess["revealed"], "mult": sess["mult"]},
                    "state": await _collect_social_state(uid),
                }

        # ب) بازی CRASH (موشک انفجار با ضریب هدف)
        elif game == "crash":
            target_mult = float(payload.get("target_mult") or 2.0)
            target_mult = max(1.1, min(100.0, round(target_mult, 2)))
            if bet < 10 or bet > my_prof["coins"]:
                return {"ok": False, "error": "موجودی سکه کافی نیست یا مبلغ شرط نامعتبر است!", "state": await _collect_social_state(uid)}

            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)
            r_val = random.random()
            if r_val < 0.06:
                crash_point = 1.00
            else:
                crash_point = round(min(100.0, max(1.01, 0.97 / (1.0 - r_val))), 2)

            won = crash_point >= target_mult
            win_amt = int(bet * target_mult) if won else 0
            if won:
                await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1, xp=xp+20 WHERE user_id=$2", win_amt, uid)
                _record_big_win(my_prof["display_name"], "CRASH", win_amt, f"{target_mult}x")

            return {
                "ok": True,
                "crash_result": {
                    "won": won,
                    "crash_point": crash_point,
                    "target_mult": target_mult,
                    "bet": bet,
                    "win_amt": win_amt,
                },
                "msg": f"🚀 موشک تا {crash_point}x بالا رفت! برنده +{win_amt:,} سکه شدید!" if won else f"💥 موشک در ضریب {crash_point}x منفجر شد!",
                "state": await _collect_social_state(uid),
            }

        # ج) بازی HELL PICKAXE و ROYAL SLOT
        elif game in ("pickaxe", "slot"):
            if bet < 10 or bet > my_prof["coins"]:
                return {"ok": False, "error": "موجودی سکه کافی نیست!", "state": await _collect_social_state(uid)}
            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", bet, uid)

            if game == "pickaxe":
                mult = random.choices([0, 0.5, 1.5, 2.0, 3.5, 6.0, 12.0], weights=[40, 20, 18, 11, 6, 3.5, 1.5])[0]
                icons = {0: "🪨 سنگ پوچ", 0.5: "🥉 مس", 1.5: "🥈 نقره", 2.0: "🥇 طلا", 3.5: "💎 یاقوت", 6.0: "🔥 کریستال دوزخی", 12.0: "👑 گنج امپراتور"}
                win_amt = int(bet * mult)
                if win_amt > 0:
                    await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1, xp=xp+10 WHERE user_id=$2", win_amt, uid)
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
                    await db.pool.execute("UPDATE sp_profiles SET coins=coins+$1, xp=xp+12 WHERE user_id=$2", win_amt, uid)
                    _record_big_win(my_prof["display_name"], "SLOT", win_amt, f"{mult}x")
                return {
                    "ok": win_amt > 0,
                    "slot_result": {"reels": reels, "mult": mult, "win_amt": win_amt},
                    "msg": f"🎰 [ {' | '.join(reels)} ] — {'برنده +' + f'{win_amt:,} سکه (' + str(mult) + 'x)!' if win_amt else 'پوچ! دوباره امتحان کن'}",
                    "state": await _collect_social_state(uid),
                }

    # ─── ۳. مشاهده پروفایل کاربر دیگر (با پشتیبانی از بازدید مخفی اشتراک Plus/Ultra) ───
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

    # ─── ۴. ویرایش پروفایل، رنگ کارت و حالت‌های مخفی/روح ───
    elif action == "save_profile":
        new_name = str(payload.get("display_name") or my_prof["display_name"]).strip()[:32]
        new_bio = str(payload.get("bio") or my_prof["bio"]).strip()[:160]
        new_theme = str(payload.get("card_theme") or my_prof["card_theme"]).strip()
        stealth_on = bool(payload.get("stealth_mode", my_prof["stealth_mode"]))
        ghost_on = bool(payload.get("ghost_mode", my_prof["ghost_mode"]))

        theme_obj = next((t for t in PROFILE_THEMES if t["id"] == new_theme), PROFILE_THEMES[0])
        req_rank = TIER_RANK.get(theme_obj["tier"], 0)
        my_rank = TIER_RANK.get(my_prof["sub_tier"], 0)
        if req_rank > my_rank and uid not in OWNER_IDS:
            return {
                "ok": False,
                "error": f"🔒 رنگ کارت «{theme_obj['title']}» مخصوص اشتراک «{theme_obj['tier'].upper()}» به بالاست! از فروشگاه اشتراک تهیه کنید.",
                "state": await _collect_social_state(uid),
            }

        await db.pool.execute(
            """UPDATE sp_profiles
               SET display_name=$1, bio=$2, card_theme=$3, stealth_mode=$4, ghost_mode=$5
               WHERE user_id=$6""",
            new_name, new_bio, new_theme, stealth_on, ghost_on, uid
        )
        msg_out = "✅ پروفایل و رنگ کارت شما با موفقیت ذخیره شد!"

    # ─── ۵. ساخت و ویرایش اتاق صوتی شخصی ───
    elif action == "save_my_room":
        title = str(payload.get("title") or f"اتاق {my_prof['display_name']}").strip()[:45]
        desc = str(payload.get("description") or "به اتاق صوتی من خوش آمدید!").strip()[:180]
        welcome = str(payload.get("welcome_msg") or "خوش آمدید!").strip()[:140]
        cat = str(payload.get("category") or "Friendship").strip()
        r_photo = str(payload.get("room_photo") or "").strip()
        mic_count = int(payload.get("mic_count") or 8)
        if mic_count not in (1, 2, 6, 8, 10, 11, 12, 14, 15, 17, 20, 24, 30, 36):
            mic_count = 8
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

    # ─── ۶. ورود به اتاق صوتی (با پشتیبانی از قفل اتاق و Ghost Mode اشتراک Ultra) ───
    elif action == "join_room":
        room_id = int(payload.get("room_id") or 0)
        entered_pin = str(payload.get("pin_code") or "").strip()
        r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
        if not r_row:
            return {"ok": False, "error": "اتاق صوتی مورد نظر یافت نشد!", "state": await _collect_social_state(uid)}

        is_room_owner = (int(r_row["owner_id"]) == uid) or (uid in OWNER_IDS)
        is_ghost_entry = bool(my_prof["can_ghost_join"] and my_prof["ghost_mode"] and not is_room_owner)

        if r_row["is_locked"] and not is_room_owner and not is_ghost_entry:
            if r_row["pin_code"] and entered_pin != r_row["pin_code"]:
                return {
                    "ok": False,
                    "need_pin": True,
                    "room_id": room_id,
                    "error": "🔒 این اتاق صوتی قفل است! رمز ورود را وارد کنید:",
                    "state": await _collect_social_state(uid),
                }

        rt = _get_live_room_state(room_id, r_row["mic_count"])
        was_already_in = uid in rt["members"]
        rt["members"][uid] = {
            "uid": uid,
            "name": my_prof["display_name"],
            "photo": my_prof["photo"],
            "badge": my_prof["sub_badge"],
            "ring_css": my_prof["ring_css"],
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

    # ─── ۷. عملیات داخل اتاق صوتی ───
    elif action == "room_op":
        room_id = int(payload.get("room_id") or 0)
        op = str(payload.get("op") or "ping")
        r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
        if not r_row:
            return {"ok": False, "error": "اتاق یافت نشد!"}

        rt = _get_live_room_state(room_id, r_row["mic_count"])
        is_room_owner = (int(r_row["owner_id"]) == uid) or (uid in OWNER_IDS)

        if uid in rt["members"]:
            rt["members"][uid]["last_seen"] = now
            rt["members"][uid]["ring_css"] = my_prof["ring_css"]
            rt["members"][uid]["badge"] = my_prof["sub_badge"]

        if op == "take_seat":
            seat_idx = str(payload.get("seat_idx") or "1")
            if int(seat_idx) in rt["locked_seats"] and not is_room_owner:
                return {"ok": False, "error": "🔒 این میکروفون قفل شده است!", "active_room": _format_room_dict(r_row, uid)}
            if r_row["auto_lock_mics"] and not is_room_owner:
                return {"ok": False, "error": "🔒 قفل خودکار میکروفون‌ها در این اتاق فعال است!", "active_room": _format_room_dict(r_row, uid)}

            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)

            cur_occupant = rt["seats"].get(seat_idx)
            if cur_occupant and int(cur_occupant.get("uid", 0)) != uid and not is_room_owner:
                return {"ok": False, "error": "این صندلی پر است!", "active_room": _format_room_dict(r_row, uid)}

            if uid in rt["members"]:
                rt["members"][uid]["is_ghost"] = False

            rt["seats"][seat_idx] = {
                "uid": uid,
                "name": my_prof["display_name"],
                "photo": my_prof["photo"],
                "badge": my_prof["sub_badge"],
                "ring_css": my_prof["ring_css"],
                "muted": False,
            }

        elif op == "leave_seat":
            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)

        elif op == "toggle_my_mic":
            for k, v in rt["seats"].items():
                if v and int(v.get("uid", 0)) == uid:
                    v["muted"] = not bool(v.get("muted"))

        elif op == "chat":
            txt = str(payload.get("text") or "").strip()[:120]
            if txt:
                rt["chats"].append({
                    "sys": False,
                    "uid": uid,
                    "name": my_prof["display_name"],
                    "badge": my_prof["sub_badge"],
                    "text": txt,
                })

        elif op == "send_gift":
            gift_id = int(payload.get("gift_id") or 0)
            g_row = await db.pool.fetchrow("SELECT * FROM sp_store_items WHERE id=$1 AND category='gift'", gift_id)
            if not g_row:
                return {"ok": False, "error": "گیفت یافت نشد!"}
            if my_prof["coins"] < g_row["price_coins"]:
                return {"ok": False, "error": f"سکه کافی ندارید! ({g_row['price_coins']:,} سکه نیاز است)"}

            await db.pool.execute("UPDATE sp_profiles SET coins=coins-$1 WHERE user_id=$2", g_row["price_coins"], uid)
            await db.pool.execute("UPDATE sp_voice_rooms SET total_gifts=total_gifts+$1, level=1+CAST((total_gifts+$1)/2000 AS INT) WHERE room_id=$2", g_row["price_coins"], room_id)
            await db.pool.execute("UPDATE sp_profiles SET gifts_received=gifts_received+1, coins=coins+$1 WHERE user_id=$2", int(g_row["price_coins"] * 0.4), r_row["owner_id"])

            rt["chats"].append({
                "sys": True,
                "gift": True,
                "text": f"🎁 {my_prof['display_name']} {my_prof['sub_badge']} هدیه «{g_row['icon']} {g_row['name']}» ({g_row['price_coins']:,} 🪙) ارسال کرد!",
            })
            if rt["pk_active"]:
                if len(rt["chats"]) % 2 == 0:
                    rt["pk_score_a"] += g_row["price_coins"]
                else:
                    rt["pk_score_b"] += g_row["price_coins"]
            r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

        elif op == "leave_room":
            rt["members"].pop(uid, None)
            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)
            return {"ok": True, "left": True, "state": await _collect_social_state(uid)}

        elif is_room_owner:
            if op == "change_layout":
                mc = int(payload.get("mic_count") or 8)
                mm = str(payload.get("mic_mode") or "normal")
                await db.pool.execute("UPDATE sp_voice_rooms SET mic_count=$1, mic_mode=$2 WHERE room_id=$3", mc, mm, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
                rt["chats"].append({"sys": True, "text": f"🎛️ چیدمان اتاق به «{mc} Mic ({mm.upper()})» تغییر یافت."})

            elif op == "toggle_lock_room":
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

            elif op == "toggle_seat_lock":
                s_idx = int(payload.get("seat_idx") or 1)
                if s_idx in rt["locked_seats"]:
                    rt["locked_seats"].remove(s_idx)
                else:
                    rt["locked_seats"].append(s_idx)

            elif op == "clear_chat":
                rt["chats"] = [{"sys": True, "text": "🧹 تاریخچه چت اتاق توسط مالک پاکسازی شد."}]

            elif op == "toggle_music":
                rt["music_playing"] = not rt["music_playing"]

            elif op == "toggle_pk":
                rt["pk_active"] = not rt["pk_active"]
                rt["pk_score_a"] = 0
                rt["pk_score_b"] = 0
                rt["chats"].append({"sys": True, "text": "⚔️ رقابت PK در اتاق آغاز شد!" if rt["pk_active"] else "🏁 رقابت PK پایان یافت."})

            elif op == "change_bg":
                bg = str(payload.get("bg_theme") or "lighthouse")
                await db.pool.execute("UPDATE sp_voice_rooms SET bg_theme=$1 WHERE room_id=$2", bg, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

        return {
            "ok": True,
            "active_room": _format_room_dict(r_row, uid),
            "state": await _collect_social_state(uid),
        }

    # ─── ۸. خرید قطعی اشتراک Pro / Plus / Ultra (با سکه، موجودی استارز کیف پول، یا پرداخت مستقیم استارز) ───
    elif action == "buy_subscription":
        tier_id = str(payload.get("tier_id") or "pro").lower()
        pay_method = str(payload.get("pay_method") or "coins")  # coins | wallet_stars | direct_stars
        tier = SUB_TIERS.get(tier_id)
        if not tier or tier_id == "free":
            return {"ok": False, "error": "اشتراک نامعتبر است!", "state": await _collect_social_state(uid)}

        exp_ts = now + (tier["days"] * 86400)

        if pay_method == "coins":
            if my_prof["coins"] < tier["coins"]:
                return {
                    "ok": False,
                    "error": f"موجودی سکه کافی نیست! ({tier['coins']:,} سکه نیاز است — موجودی شما: {my_prof['coins']:,} 🪙)",
                    "state": await _collect_social_state(uid),
                }
            await db.pool.execute(
                "UPDATE sp_profiles SET coins=coins-$1, sub_tier=$2, sub_expires_at=$3 WHERE user_id=$4",
                tier["coins"], tier_id, exp_ts, uid
            )
            return {
                "ok": True,
                "msg": f"🎉 تبریک! «{tier['title']}» با نشان {tier['badge']} به مدت ۳۰ روز برای شما فعال شد!",
                "state": await _collect_social_state(uid),
            }

        elif pay_method == "wallet_stars":
            if my_prof["stars_balance"] < tier["stars"]:
                return {
                    "ok": False,
                    "error": f"موجودی استارز کیف پول کافی نیست! ({tier['stars']} ⭐ نیاز است — ابتدا کیف پول را شارژ کنید)",
                    "state": await _collect_social_state(uid),
                }
            await db.pool.execute(
                "UPDATE sp_profiles SET stars_balance=stars_balance-$1, sub_tier=$2, sub_expires_at=$3 WHERE user_id=$4",
                tier["stars"], tier_id, exp_ts, uid
            )
            return {
                "ok": True,
                "msg": f"🎉 تبریک! «{tier['title']}» با نشان {tier['badge']} فعال شد!",
                "state": await _collect_social_state(uid),
            }

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

    # ─── ۹. خرید و تجهیز قطعی حلقه دور آواتار (Ring) ───
    elif action == "buy_or_equip_ring":
        ring_id = int(payload.get("ring_id") or 0)
        if ring_id == 0:
            await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=0 WHERE user_id=$1", uid)
            return {"ok": True, "msg": "حلقه دور پروفایل برداشته شد.", "state": await _collect_social_state(uid)}

        r_row = await db.pool.fetchrow("SELECT * FROM sp_store_items WHERE id=$1 AND category='ring'", ring_id)
        if not r_row:
            return {"ok": False, "error": "حلقه مورد نظر یافت نشد!", "state": await _collect_social_state(uid)}

        owned = [int(x) for x in my_prof["owned_rings"]]
        if ring_id in owned:
            await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=$1 WHERE user_id=$2", ring_id, uid)
            # بروزرسانی فوری حلقه در اتاق صوتی در صورت حضور
            for rm in live_rooms_runtime.values():
                if uid in rm["members"]:
                    rm["members"][uid]["ring_css"] = r_row["ring_css"]
                for s in rm["seats"].values():
                    if s and int(s.get("uid", 0)) == uid:
                        s["ring_css"] = r_row["ring_css"]
            return {"ok": True, "msg": f"✅ «{r_row['name']}» دور آواتار شما فعال شد!", "state": await _collect_social_state(uid)}

        if my_prof["coins"] < r_row["price_coins"]:
            return {
                "ok": False,
                "error": f"موجودی سکه کافی نیست! ({r_row['price_coins']:,} 🪙 نیاز است — از کیف پول استارز را به سکه تبدیل کنید)",
                "state": await _collect_social_state(uid),
            }

        owned.append(ring_id)
        await db.pool.execute(
            "UPDATE sp_profiles SET coins=coins-$1, owned_rings=$2, avatar_ring_id=$3 WHERE user_id=$4",
            r_row["price_coins"], json.dumps(owned), ring_id, uid
        )
        for rm in live_rooms_runtime.values():
            if uid in rm["members"]:
                rm["members"][uid]["ring_css"] = r_row["ring_css"]
            for s in rm["seats"].values():
                if s and int(s.get("uid", 0)) == uid:
                    s["ring_css"] = r_row["ring_css"]
        return {
            "ok": True,
            "msg": f"🎉 «{r_row['name']}» خریداری شد و هم‌اکنون دور آواتار شما قرار گرفت!",
            "state": await _collect_social_state(uid),
        }

    return {"ok": True, "msg": msg_out, "state": await _collect_social_state(uid)}


async def _collect_social_state(uid: int) -> dict:
    my_prof = await get_or_create_sp_profile(uid)
    rooms_rows = await db.pool.fetch("SELECT * FROM sp_voice_rooms ORDER BY total_gifts DESC, room_id DESC LIMIT 40")
    rooms_list = [_format_room_dict(r, uid) for r in rooms_rows]
    store_rows = await db.pool.fetch("SELECT * FROM sp_store_items ORDER BY category, price_coins ASC")
    store_items = [dict(r) for r in store_rows]

    return {
        "me": my_prof,
        "rooms": rooms_list,
        "store_items": store_items,
        "sub_tiers": list(SUB_TIERS.values()),
        "profile_themes": PROFILE_THEMES,
        "topup_packs": STAR_TOPUP_PACKS,
        "rate": STARS_TO_COINS_RATE,
        "big_wins": recent_big_wins[:8],
    }


# ═══════════════════════════════════════════════════════════════════════════
# پنل مدیریت کل پلتفرم راینو (مستقل از برج شیاطین)
# ═══════════════════════════════════════════════════════════════════════════
async def handle_platform_admin_api(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    if uid not in OWNER_IDS:
        return {"ok": False, "error": "⛔ دسترسی غیرمجاز! فقط مالک ربات دسترسی دارد."}

    await ensure_social_tables()
    action = str(payload.get("action") or "state")
    msg_out = ""

    if action == "save_ui_asset":
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
                    text=(
                        "📝 <b>ربات آماده دریافت پیام همگانی شماست!</b>\n\n"
                        "لطفاً همین الان پیام مورد نظر خود را (شامل هرگونه <b>ایموجی پریمیوم تلگرام</b>، عکس، ویدیو یا متن) در همین پیوی بفرستید:"
                    ),
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
        prof["is_bot_admin"] = bool(u_main["is_admin"]) if u_main else False
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

    elif action == "save_store_item":
        cat = str(payload.get("category") or "gift")
        name = str(payload.get("name") or "آیتم جدید").strip()
        icon = str(payload.get("icon") or "🎁").strip()
        ring_css = str(payload.get("ring_css") or "0 0 0 3.5px #fbbf24, 0 0 18px #f59e0b").strip() if cat == "ring" else ""
        p_coins = int(payload.get("price_coins") or 1000)
        p_stars = int(payload.get("price_stars") or 20)
        await db.pool.execute(
            "INSERT INTO sp_store_items (category, name, icon, ring_css, price_coins, price_stars) VALUES ($1,$2,$3,$4,$5,$6)",
            cat, name, icon, ring_css, p_coins, p_stars
        )
        msg_out = f"✅ آیتم «{name}» به فروشگاه اضافه شد!"

    elif action == "delete_store_item":
        item_id = int(payload.get("item_id") or 0)
        await db.pool.execute("DELETE FROM sp_store_items WHERE id=$1", item_id)
        msg_out = "🗑️ آیتم از فروشگاه حذف شد."

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

    return {"ok": True, "msg": msg_out, "admin_data": await _collect_platform_admin_state()}


async def _collect_platform_admin_state() -> dict:
    users_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
    groups_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
    rooms_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM sp_voice_rooms") or 0
    vip_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM sp_profiles WHERE sub_tier != 'free'") or 0

    ui_assets_raw = await get_sp_config("ui_assets", "{}")
    try:
        ui_assets = json.loads(ui_assets_raw)
    except Exception:
        ui_assets = {}

    bc_draft_raw = await get_sp_config("bc_draft", "")
    bc_draft = json.loads(bc_draft_raw) if bc_draft_raw else None

    forced_channels = [dict(r) for r in await db.pool.fetch("SELECT chat_id, title, username FROM forced_channels")]
    groups_list = [dict(r) for r in await db.pool.fetch("SELECT chat_id, title FROM groups LIMIT 50")]
    store_items = [dict(r) for r in await db.pool.fetch("SELECT * FROM sp_store_items ORDER BY id DESC")]

    u_rows = await db.pool.fetch("""
        SELECT
            u.user_id, u.first_name, u.username, u.language,
            u.is_banned AS global_banned, u.is_admin AS is_bot_admin,
            COALESCE(sp.coins, 1000) AS coins,
            COALESCE(sp.stars_balance, 0) AS stars_balance,
            COALESCE(sp.sub_tier, 'free') AS sub_tier
        FROM users u
        LEFT JOIN sp_profiles sp ON u.user_id = sp.user_id
        ORDER BY u.user_id DESC LIMIT 200
    """)

    return {
        "bot_stats": {"users": users_cnt, "groups": groups_cnt, "rooms": rooms_cnt, "vips": vip_cnt},
        "ui_assets": ui_assets,
        "bc_draft": bc_draft,
        "forced_channels": forced_channels,
        "groups_list": groups_list,
        "store_items": store_items,
        "users_list": [dict(r) for r in u_rows],
    }
