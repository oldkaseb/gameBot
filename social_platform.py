# -*- coding: utf-8 -*-
"""social_platform.py — موتور کامل اتاق‌های صوتی (سبک SUGO)، پروفایل کاربری، اشتراک‌های VIP و فروشگاه گیفت/کاور"""

import json
import os
import time
from aiogram import Bot
from aiogram.types import LabeledPrice
from database import db

OWNER_IDS = {7662192190, 6041119040}

# ─── تعریف سطوح اشتراک (Pro, Plus, Ultra) ───
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
        "stars": 100,
        "coins": 5000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": False,
        "ghost_join": False,
        "perks": [
            "نشان اختصاصی 🥈 PRO جلوی نام",
            "🔒 قابلیت قفل کردن و رمزگذاری اتاق صوتی",
            "🎨 باز شدن رنگ‌های طلایی و نقره‌ای کارت پروفایل",
        ],
    },
    "plus": {
        "id": "plus",
        "title": "اشتراک پلاس (PLUS)",
        "badge": "🥇 PLUS",
        "stars": 250,
        "coins": 12000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": True,
        "ghost_join": False,
        "perks": [
            "نشان اختصاصی 🥇 PLUS جلوی نام",
            "🕵️ بازدید مخفی پروفایل دیگران (ثبت نشدن در لیست بازدیدکنندگان)",
            "🔒 قفل اتاق صوتی + تمام رنگ‌های طلایی، نقره‌ای و نئونی پروفایل",
        ],
    },
    "ultra": {
        "id": "ultra",
        "title": "اشتراک الترا (ULTRA)",
        "badge": "💎 ULTRA",
        "stars": 500,
        "coins": 25000,
        "days": 30,
        "can_lock_room": True,
        "stealth_visit": True,
        "ghost_join": True,
        "perks": [
            "نشان لوکس 💎 ULTRA جلوی نام",
            "👻 ورود روح (Ghost Mode) به اتاق‌های صوتی بدون دیده‌شدن در لیست حاضرین",
            "🕵️ بازدید مخفی پروفایل + باز شدن تمام تم‌ها و رنگ‌های سلطنتی کارت پروفایل",
        ],
    },
}

# ─── رنگ‌ها و تم‌های کارت پروفایل (مشابه تلگرام) ───
PROFILE_THEMES = [
    {"id": "slate",   "title": "سرمه‌ای کلاسیک", "tier": "free",  "css": "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"},
    {"id": "blue",    "title": "آبی تلگرامی",    "tier": "free",  "css": "linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%)"},
    {"id": "emerald", "title": "سبز زمردی",      "tier": "free",  "css": "linear-gradient(135deg, #047857 0%, #064e3b 100%)"},
    {"id": "purple",  "title": "بنفش شب",        "tier": "free",  "css": "linear-gradient(135deg, #6d28d9 0%, #3b0764 100%)"},
    {"id": "rose",    "title": "سرخ تیره",       "tier": "free",  "css": "linear-gradient(135deg, #be123c 0%, #4c0519 100%)"},
    {"id": "silver",  "title": "نقره‌ای متالیک (PRO)", "tier": "pro", "css": "linear-gradient(135deg, #94a3b8 0%, #475569 50%, #1e293b 100%)"},
    {"id": "gold",    "title": "طلایی سلطنتی (PRO)",  "tier": "pro", "css": "linear-gradient(135deg, #f59e0b 0%, #b45309 55%, #451a03 100%)"},
    {"id": "neon",    "title": "نئون سایبرپانک (PLUS)","tier": "plus","css": "linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #06b6d4 100%)"},
    {"id": "aurora",  "title": "شفق قطبی (PLUS)",     "tier": "plus","css": "linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #6366f1 100%)"},
    {"id": "royal",   "title": "امپراتور الماس (ULTRA)","tier": "ultra","css": "linear-gradient(135deg, #fbbf24 0%, #e11d48 45%, #4c1d95 100%)"},
    {"id": "abyss",   "title": "کهکشان تاریک (ULTRA)", "tier": "ultra","css": "radial-gradient(circle at top right, #c084fc, #3b0764 55%, #090514 100%)"},
]

TIER_RANK = {"free": 0, "pro": 1, "plus": 2, "ultra": 3}

# وضعیت زنده اتاق‌های صوتی در حافظه (صندلی‌ها، چت، حاضرین و حالت روح)
live_rooms_runtime: dict[int, dict] = {}


async def ensure_social_tables():
    await db.ensure_pool()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sp_profiles (
                user_id BIGINT PRIMARY KEY,
                display_name TEXT DEFAULT '',
                username TEXT DEFAULT '',
                photo TEXT DEFAULT '',
                bio TEXT DEFAULT 'به پروفایل من در راینو خوش آمدید!',
                card_theme TEXT DEFAULT 'purple',
                avatar_ring_id INT DEFAULT 0,
                sub_tier TEXT DEFAULT 'free',
                sub_expires_at DOUBLE PRECISION DEFAULT 0,
                stealth_mode BOOLEAN DEFAULT TRUE,
                ghost_mode BOOLEAN DEFAULT TRUE,
                owned_rings TEXT DEFAULT '[]',
                gifts_received INT DEFAULT 0,
                visitors_log TEXT DEFAULT '[]'
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

        cnt = await conn.fetchval("SELECT COUNT(*) FROM sp_store_items")
        if not cnt:
            await conn.execute("""
                INSERT INTO sp_store_items (category, name, icon, photo, ring_css, price_coins, price_stars)
                VALUES
                ('ring', 'حلقه طلایی امپراتور', '👑', '', '0 0 0 3px #fbbf24, 0 0 16px #f59e0b', 1500, 45),
                ('ring', 'حلقه نئون سایبر', '⚡', '', '0 0 0 3px #06b6d4, 0 0 18px #ec4899', 2200, 65),
                ('ring', 'حلقه آتش دوزخی', '🔥', '', '0 0 0 3px #ef4444, 0 0 20px #dc2626', 3000, 85),
                ('ring', 'حلقه الماس سلطنتی', '💎', '', '0 0 0 3.5px #e879f9, 0 0 24px #a855f7', 5000, 140),
                ('gift', 'شاخه گل رز', '🌹', '', '', 100, 5),
                ('gift', 'تاج پادشاهی', '👑', '', '', 1000, 35),
                ('gift', 'موشک طلایی', '🚀', '', '', 2500, 75),
                ('gift', 'ابرماشین نئونی', '🏎️', '', '', 6000, 180);
            """)


def _get_live_room_state(room_id: int, mic_count: int) -> dict:
    if room_id not in live_rooms_runtime:
        live_rooms_runtime[room_id] = {
            "seats": {},          # seat_idx (str) -> {uid, name, photo, badge, ring_css, muted, locked}
            "locked_seats": [],   # list of locked seat indices
            "members": {},        # uid -> {uid, name, photo, badge, is_ghost, last_seen}
            "chats": [
                {"sys": True, "text": "Welcome to the chat room! Please keep the chat friendly and respectful."},
            ],
            "music_playing": False,
            "music_title": "Rhino Chill Beats 🎵",
            "pk_active": False,
            "pk_score_a": 0,
            "pk_score_b": 0,
        }
    st = live_rooms_runtime[room_id]
    # پاکسازی اعضایی که بیش از ۶۰ ثانیه پینگ نداشته‌اند
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
            """INSERT INTO sp_profiles (user_id, display_name, username, photo)
               VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING""",
            uid, name or f"User {uid}", username, photo
        )
        row = await db.pool.fetchrow("SELECT * FROM sp_profiles WHERE user_id=$1", uid)
    else:
        if (name and name != row["display_name"]) or (photo and photo != row["photo"]):
            await db.pool.execute(
                "UPDATE sp_profiles SET display_name=$1, username=$2, photo=$3 WHERE user_id=$4",
                name or row["display_name"], username or row["username"], photo or row["photo"], uid
            )
            row = await db.pool.fetchrow("SELECT * FROM sp_profiles WHERE user_id=$1", uid)

    prof = dict(row)
    # بررسی انقضای اشتراک
    if prof["sub_tier"] != "free" and prof["sub_expires_at"] > 0 and now > prof["sub_expires_at"]:
        prof["sub_tier"] = "free"
        prof["sub_expires_at"] = 0
        await db.pool.execute("UPDATE sp_profiles SET sub_tier='free', sub_expires_at=0 WHERE user_id=$1", uid)

    # خواندن موجودی سکه از جدول برج شیاطین برای یکپارچگی کیف پول کل مینی‌اپ
    coins = await db.pool.fetchval("SELECT coins FROM dt_players WHERE user_id=$1", uid)
    if coins is None:
        coins = 200

    tier_info = SUB_TIERS.get(prof["sub_tier"], SUB_TIERS["free"])
    ring_css = ""
    if prof["avatar_ring_id"]:
        r_row = await db.pool.fetchrow("SELECT ring_css, photo FROM sp_store_items WHERE id=$1", prof["avatar_ring_id"])
        if r_row:
            ring_css = r_row["ring_css"] or ""

    room_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
    my_room = dict(room_row) if room_row else None
    if my_room:
        rt = _get_live_room_state(my_room["room_id"], my_room["mic_count"])
        my_room["online_count"] = sum(1 for m in rt["members"].values() if not m.get("is_ghost"))

    return {
        "user_id": prof["user_id"],
        "display_name": prof["display_name"] or name or f"User {uid}",
        "username": prof["username"] or username,
        "photo": prof["photo"] or photo,
        "bio": prof["bio"],
        "card_theme": prof["card_theme"] or "purple",
        "avatar_ring_id": prof["avatar_ring_id"],
        "ring_css": ring_css,
        "sub_tier": prof["sub_tier"],
        "sub_badge": tier_info["badge"],
        "sub_expires_rem_days": max(0, round((prof["sub_expires_at"] - now) / 86400, 1)) if prof["sub_expires_at"] > now else 0,
        "can_lock_room": tier_info["can_lock_room"] or (int(uid) in OWNER_IDS),
        "can_stealth_visit": tier_info["stealth_visit"] or (int(uid) in OWNER_IDS),
        "can_ghost_join": tier_info["ghost_join"] or (int(uid) in OWNER_IDS),
        "stealth_mode": bool(prof["stealth_mode"]),
        "ghost_mode": bool(prof["ghost_mode"]),
        "owned_rings": json.loads(prof["owned_rings"] or "[]"),
        "gifts_received": prof["gifts_received"],
        "visitors_log": json.loads(prof["visitors_log"] or "[]"),
        "coins": int(coins),
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


async def handle_social_api(payload: dict) -> dict:
    await ensure_social_tables()
    uid = int(payload.get("uid") or 0)
    name = str(payload.get("name") or "Player").strip()
    username = str(payload.get("username") or "").strip()
    photo = str(payload.get("photo") or "").strip()
    action = str(payload.get("action") or "state").strip()
    now = time.time()

    my_prof = await get_or_create_sp_profile(uid, name, username, photo)
    msg_out = ""

    # ─── ۱. مشاهده پروفایل کاربر دیگر (با پشتیبانی از بازدید مخفی اشتراک Plus/Ultra) ───
    if action == "view_profile":
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
            "state": await _collect_social_state(uid, my_prof),
        }

    # ─── ۲. ویرایش پروفایل، بیوگرافی، رنگ کارت و سوییچ حالت مخفی/روح ───
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
                "error": f"🔒 این رنگ کارت مخصوص اشتراک «{theme_obj['tier'].upper()}» به بالاست!",
                "state": await _collect_social_state(uid, my_prof),
            }

        await db.pool.execute(
            """UPDATE sp_profiles
               SET display_name=$1, bio=$2, card_theme=$3, stealth_mode=$4, ghost_mode=$5
               WHERE user_id=$6""",
            new_name, new_bio, new_theme, stealth_on, ghost_on, uid
        )
        my_prof = await get_or_create_sp_profile(uid)
        msg_out = "✅ پروفایل و رنگ کارت شما با موفقیت ذخیره شد!"

    # ─── ۳. ساخت یا ویرایش اتاق صوتی شخصی (هر کاربر یک اتاق که در پروفایلش هم نمایش داده می‌شود) ───
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
                "error": "🔒 قفل کردن اتاق صوتی فقط مخصوص مشترکین «PRO»، «PLUS» و «ULTRA» است! از فروشگاه اشتراک تهیه کنید.",
                "state": await _collect_social_state(uid, my_prof),
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

        my_prof = await get_or_create_sp_profile(uid)
        room_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE owner_id=$1", uid)
        return {
            "ok": True,
            "msg": "✅ تنظیمات اتاق صوتی شما ذخیره شد!",
            "active_room": _format_room_dict(room_row, uid),
            "state": await _collect_social_state(uid, my_prof),
        }

    # ─── ۴. ورود به اتاق صوتی (با پشتیبانی از قفل اتاق و Ghost Mode اشتراک Ultra) ───
    elif action == "join_room":
        room_id = int(payload.get("room_id") or 0)
        entered_pin = str(payload.get("pin_code") or "").strip()
        r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
        if not r_row:
            return {"ok": False, "error": "اتاق صوتی مورد نظر یافت نشد!", "state": await _collect_social_state(uid, my_prof)}

        is_room_owner = (int(r_row["owner_id"]) == uid) or (uid in OWNER_IDS)
        is_ghost_entry = bool(my_prof["can_ghost_join"] and my_prof["ghost_mode"] and not is_room_owner)

        if r_row["is_locked"] and not is_room_owner and not is_ghost_entry:
            if r_row["pin_code"] and entered_pin != r_row["pin_code"]:
                return {
                    "ok": False,
                    "need_pin": True,
                    "room_id": room_id,
                    "error": "🔒 این اتاق صوتی توسط مالک قفل شده است! رمز ورود را وارد کنید:",
                    "state": await _collect_social_state(uid, my_prof),
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
            "state": await _collect_social_state(uid, my_prof),
        }

    # ─── ۵. عملیات داخل اتاق صوتی (نشستن روی مایک، قفل مایک، چت، تغییر تعداد مایک، پاکسازی چت، موزیک، خروج) ───
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

        if op == "take_seat":
            seat_idx = str(payload.get("seat_idx") or "1")
            if int(seat_idx) in rt["locked_seats"] and not is_room_owner:
                return {"ok": False, "error": "🔒 این میکروفون توسط مالک اتاق قفل شده است!", "active_room": _format_room_dict(r_row, uid)}
            if r_row["auto_lock_mics"] and not is_room_owner:
                return {"ok": False, "error": "🔒 قفل خودکار میکروفون‌ها در این اتاق فعال است!", "active_room": _format_room_dict(r_row, uid)}

            # حذف از صندلی قبلی اگر نشسته بود
            for k, v in list(rt["seats"].items()):
                if v and int(v.get("uid", 0)) == uid:
                    rt["seats"].pop(k, None)

            cur_occupant = rt["seats"].get(seat_idx)
            if cur_occupant and int(cur_occupant.get("uid", 0)) != uid and not is_room_owner:
                return {"ok": False, "error": "این صندلی پر است!", "active_room": _format_room_dict(r_row, uid)}

            # اگر در حالت روح بود و روی مایک نشست، از حالت روح خارج می‌شود تا روی استیج دیده شود
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
                return {"ok": False, "error": f"سکه کافی ندارید! ({g_row['price_coins']} سکه نیاز است)"}

            await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", g_row["price_coins"], uid)
            await db.pool.execute("UPDATE sp_voice_rooms SET total_gifts=total_gifts+$1, level=1+CAST((total_gifts+$1)/2000 AS INT) WHERE room_id=$2", g_row["price_coins"], room_id)
            await db.pool.execute("UPDATE sp_profiles SET gifts_received=gifts_received+1 WHERE user_id=$1", r_row["owner_id"])

            rt["chats"].append({
                "sys": True,
                "gift": True,
                "text": f"🎁 {my_prof['display_name']} هدیه «{g_row['icon']} {g_row['name']}» ({g_row['price_coins']} 🪙) در اتاق فرستاد!",
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
            return {"ok": True, "left": True, "state": await _collect_social_state(uid, await get_or_create_sp_profile(uid))}

        # عملیات‌های مدیریتی مالک اتاق (مشابه پنل Room Management در اسکرین‌شات‌ها)
        elif is_room_owner:
            if op == "change_layout":
                mc = int(payload.get("mic_count") or 8)
                mm = str(payload.get("mic_mode") or "normal")
                await db.pool.execute("UPDATE sp_voice_rooms SET mic_count=$1, mic_mode=$2 WHERE room_id=$3", mc, mm, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)
                rt["chats"].append({"sys": True, "text": f"🎛️ چیدمان اتاق به حالت «{mc} Mic ({mm.upper()})» تغییر یافت."})

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
                rt["chats"].append({"sys": True, "text": "⚔️ رقابت گروهی PK در اتاق آغاز شد!" if rt["pk_active"] else "🏁 رقابت PK پایان یافت."})

            elif op == "change_bg":
                bg = str(payload.get("bg_theme") or "lighthouse")
                await db.pool.execute("UPDATE sp_voice_rooms SET bg_theme=$1 WHERE room_id=$2", bg, room_id)
                r_row = await db.pool.fetchrow("SELECT * FROM sp_voice_rooms WHERE room_id=$1", room_id)

        return {
            "ok": True,
            "active_room": _format_room_dict(r_row, uid),
            "state": await _collect_social_state(uid, await get_or_create_sp_profile(uid)),
        }

    # ─── ۶. خرید اشتراک Pro / Plus / Ultra (با سکه یا Telegram Stars) ───
    elif action == "buy_subscription":
        tier_id = str(payload.get("tier_id") or "pro").lower()
        pay_method = str(payload.get("pay_method") or "stars")  # stars | coins
        tier = SUB_TIERS.get(tier_id)
        if not tier or tier_id == "free":
            return {"ok": False, "error": "اشتراک نامعتبر است!"}

        if pay_method == "coins":
            if my_prof["coins"] < tier["coins"]:
                return {"ok": False, "error": f"سکه کافی ندارید! ({tier['coins']:,} سکه نیاز است)", "state": await _collect_social_state(uid, my_prof)}
            await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", tier["coins"], uid)
            exp_ts = max(now, time.time()) + (tier["days"] * 86400)
            await db.pool.execute("UPDATE sp_profiles SET sub_tier=$1, sub_expires_at=$2 WHERE user_id=$3", tier_id, exp_ts, uid)
            my_prof = await get_or_create_sp_profile(uid)
            return {
                "ok": True,
                "msg": f"🎉 تبریک! «{tier['title']}» به مدت ۳۰ روز برای شما فعال شد!",
                "state": await _collect_social_state(uid, my_prof),
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
                return {"ok": True, "invoice_link": inv_link, "state": await _collect_social_state(uid, my_prof)}
            except Exception as e:
                return {"ok": False, "error": str(e), "state": await _collect_social_state(uid, my_prof)}
            finally:
                await temp_bot.session.close()

    # ─── ۷. خرید یا تجهیز حلقه/کاور دور آواتار از فروشگاه ───
    elif action == "buy_or_equip_ring":
        ring_id = int(payload.get("ring_id") or 0)
        if ring_id == 0:
            await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=0 WHERE user_id=$1", uid)
            my_prof = await get_or_create_sp_profile(uid)
            return {"ok": True, "msg": "حلقه دور پروفایل برداشته شد.", "state": await _collect_social_state(uid, my_prof)}

        r_row = await db.pool.fetchrow("SELECT * FROM sp_store_items WHERE id=$1 AND category='ring'", ring_id)
        if not r_row:
            return {"ok": False, "error": "حلقه مورد نظر یافت نشد!"}

        owned = my_prof["owned_rings"]
        if ring_id in owned:
            await db.pool.execute("UPDATE sp_profiles SET avatar_ring_id=$1 WHERE user_id=$2", ring_id, uid)
            my_prof = await get_or_create_sp_profile(uid)
            return {"ok": True, "msg": f"✅ «{r_row['name']}» روی آواتار شما فعال شد!", "state": await _collect_social_state(uid, my_prof)}

        if my_prof["coins"] < r_row["price_coins"]:
            return {"ok": False, "error": f"سکه کافی ندارید! ({r_row['price_coins']:,} سکه نیاز است)", "state": await _collect_social_state(uid, my_prof)}

        owned.append(ring_id)
        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", r_row["price_coins"], uid)
        await db.pool.execute(
            "UPDATE sp_profiles SET owned_rings=$1, avatar_ring_id=$2 WHERE user_id=$3",
            json.dumps(owned), ring_id, uid
        )
        my_prof = await get_or_create_sp_profile(uid)
        return {"ok": True, "msg": f"🎉 «{r_row['name']}» خریداری و دور پروفایل شما قرار گرفت!", "state": await _collect_social_state(uid, my_prof)}

    return {"ok": True, "msg": msg_out, "state": await _collect_social_state(uid, my_prof)}


async def _collect_social_state(uid: int, my_prof: dict) -> dict:
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
    }
