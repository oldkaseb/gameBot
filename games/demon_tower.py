# -*- coding: utf-8 -*-
"""games/demon_tower.py — موتور کامل برج شیاطین + دیتابیس + دستور «پنل برج» ویژه مالک در پیوی"""

import json
import math
import os
import random
import string
import time
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, InlineKeyboardButton
)
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from emojis import E
from utils.premium import primary, success, danger, kb

router = Router(name="demon_tower")
OWNER_IDS = {7662192190, 6041119040}
OWNER_USERNAME = "oldkaseb"

# بسته‌های فروشگاه استارز (معقول و به‌صرفه برای بازیکن و سازنده)
STAR_PACKAGES = {
    "pack_1": {"stars": 50,  "coins": 2500,  "xp": 300,  "title": "بسته شکارچی مبتدی (۲,۵۰۰ سکه + ۳ لول)"},
    "pack_2": {"stars": 150, "coins": 9000,  "xp": 1000, "title": "بسته شوالیه خونین (۹,۰۰۰ سکه + ۱۰ لول)"},
    "pack_3": {"stars": 400, "coins": 28000, "xp": 3000, "title": "بسته ارباب برج (۲۸,۰۰۰ سکه + ۳۰ لول)"},
    "pack_4": {"stars": 900, "coins": 75000, "xp": 8000, "title": "بسته امپراتور شیاطین (۷۵,۰۰۰ سکه + ۸۰ لول)"},
}


class TowerAdminStates(StatesGroup):
    set_male_img = State()
    set_female_img = State()
    add_floor = State()
    del_floor = State()
    add_weapon = State()
    del_weapon = State()
    add_armor = State()
    del_armor = State()
    add_gift = State()
    add_popup = State()
    check_user = State()
    charge_user = State()
    ban_user = State()
    voucher_note = State()


# ═══════════════════════════════════════════════════════════
# ۱. راه‌اندازی جداول دیتابیس و مقادیر پیش‌فرض برج شیاطین
# ═══════════════════════════════════════════════════════════

async def ensure_tower_tables():
    await db.ensure_pool()
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dt_config (
                key TEXT PRIMARY KEY,
                val TEXT
            );
            CREATE TABLE IF NOT EXISTS dt_players (
                user_id BIGINT PRIMARY KEY,
                gender TEXT DEFAULT NULL,
                level INT DEFAULT 1,
                xp BIGINT DEFAULT 0,
                coins BIGINT DEFAULT 200,
                bank_coins BIGINT DEFAULT 0,
                bank_last_ts DOUBLE PRECISION DEFAULT 0,
                current_floor INT DEFAULT 1,
                hp INT DEFAULT 120,
                max_hp INT DEFAULT 120,
                humanity INT DEFAULT 100,
                hospital_until DOUBLE PRECISION DEFAULT 0,
                sleep_until DOUBLE PRECISION DEFAULT 0,
                equipped_weapon INT DEFAULT 1,
                equipped_armor INT DEFAULT 0,
                owned_weapons TEXT DEFAULT '[1]',
                owned_armors TEXT DEFAULT '[]',
                inventory TEXT DEFAULT '[]',
                is_banned BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS dt_floors (
                floor_num INT PRIMARY KEY,
                boss_name TEXT,
                photo TEXT,
                description TEXT,
                power_desc TEXT,
                weakness TEXT,
                hp INT,
                atk INT,
                def INT,
                reward_coins INT,
                reward_xp INT,
                drop_item TEXT,
                drop_price INT DEFAULT 50
            );
            CREATE TABLE IF NOT EXISTS dt_items (
                id SERIAL PRIMARY KEY,
                item_type TEXT, -- weapon | armor
                name TEXT,
                photo TEXT,
                price INT DEFAULT 0,
                hp_bonus INT DEFAULT 0,
                atk_bonus INT DEFAULT 0,
                def_bonus INT DEFAULT 0,
                spd_bonus INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS dt_gifts (
                code TEXT PRIMARY KEY,
                coins INT DEFAULT 0,
                xp INT DEFAULT 0,
                max_uses INT DEFAULT 1,
                used_by TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS dt_vouchers (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                user_name TEXT,
                coins_offered BIGINT,
                voucher_type TEXT,
                status TEXT DEFAULT 'pending', -- pending | approved | rejected
                owner_note TEXT DEFAULT '',
                voucher_code TEXT DEFAULT '',
                created_at DOUBLE PRECISION
            );
        """)

        # بررسی و درج سلاح اول رایگان و طبقات اولیه در صورت خالی بودن
        w_count = await conn.fetchval("SELECT COUNT(*) FROM dt_items WHERE item_type='weapon'")
        if not w_count:
            await conn.execute("""
                INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
                VALUES
                ('weapon', 'شمشیر آهنی شکارچی (رایگان)', '', 0, 10, 18, 5, 0),
                ('weapon', 'تیغه خون‌آشام', '', 650, 35, 42, 12, 5),
                ('weapon', 'تبر دوزخی راینو', '', 1800, 80, 95, 25, -5),
                ('armor', 'زره چرمی سایه', '', 400, 50, 0, 22, 10),
                ('armor', 'زره پولادین امپراتور', '', 1400, 140, 10, 60, -5);
            """)

        f_count = await conn.fetchval("SELECT COUNT(*) FROM dt_floors")
        if not f_count:
            await conn.execute("""
                INSERT INTO dt_floors (floor_num, boss_name, photo, description, power_desc, weakness, hp, atk, def, reward_coins, reward_xp, drop_item, drop_price)
                VALUES
                (1, 'نگهبان دروازه خاکستر', '', 'اسکلت غول‌پیکری که ورودی طبقه اول را محافظت می‌کند.', 'ضربه زنجیر آتشین', 'حساس به ضربه سریع', 95, 16, 6, 120, 45, 'گوهر خاکستر', 40),
                (2, 'گرگینه خون‌خوار', '', 'شکارچی شب که در تاریکی طبقه دوم کمین کرده است.', 'پنجه زهرآلود', 'نقطه ضعف: سپر نقره‌ای', 165, 26, 12, 240, 85, 'ناب گرگینه', 85),
                (3, 'ارباب سایه‌های تاریک', '', 'جادوگر سقوط‌کرده با شمشیر نفرین‌شده.', 'جذب روح', 'نقطه ضعف: تیغه خون‌آشام', 270, 40, 20, 450, 150, 'تاج سایه', 160),
                (4, 'اژدهای استخوانی دوزخ', '', 'فرمانروای طبقه چهارم با نفس آتشین.', 'طوفان شعله', 'نقطه ضعف: زره پولادین', 460, 62, 35, 900, 320, 'قلب اژدها', 350);
            """)


async def get_dt_config(key: str, default: str = "") -> str:
    await ensure_tower_tables()
    val = await db.pool.fetchval("SELECT val FROM dt_config WHERE key=$1", key)
    return val if val is not None else default


async def set_dt_config(key: str, val: str):
    await ensure_tower_tables()
    await db.pool.execute(
        "INSERT INTO dt_config (key, val) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET val=$2",
        key, val
    )


# ═══════════════════════════════════════════════════════════
# ۲. توابع هسته و وضعیت بازیکن (Core State & Bank Interest)
# ═══════════════════════════════════════════════════════════

async def get_or_create_player(uid: int) -> dict:
    await ensure_tower_tables()
    now = time.time()
    row = await db.pool.fetchrow("SELECT * FROM dt_players WHERE user_id=$1", uid)
    if not row:
        first_w = await db.pool.fetchval("SELECT id FROM dt_items WHERE item_type='weapon' ORDER BY price ASC, id ASC LIMIT 1") or 1
        await db.pool.execute(
            """INSERT INTO dt_players (user_id, equipped_weapon, owned_weapons, bank_last_ts)
               VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING""",
            uid, first_w, json.dumps([first_w]), now
        )
        row = await db.pool.fetchrow("SELECT * FROM dt_players WHERE user_id=$1", uid)

    p = dict(row)

    # ۱. محاسبه سود ساعتی بانک (۲٪ در هر ساعت کامل)
    if p["bank_coins"] > 0 and p["bank_last_ts"] > 0:
        hours_passed = int((now - p["bank_last_ts"]) // 3600)
        if hours_passed >= 1:
            profit = int(p["bank_coins"] * 0.02 * min(hours_passed, 72))
            if profit > 0:
                p["bank_coins"] += profit
                p["bank_last_ts"] = now
                await db.pool.execute(
                    "UPDATE dt_players SET bank_coins=$1, bank_last_ts=$2 WHERE user_id=$3",
                    p["bank_coins"], now, uid
                )
    else:
        await db.pool.execute("UPDATE dt_players SET bank_last_ts=$1 WHERE user_id=$2", now, uid)

    # ۲. بررسی اتمام زمان بیمارستان یا خواب ۲ روزه انسانیت
    if p["hospital_until"] > 0 and now >= p["hospital_until"]:
        p["hospital_until"] = 0
        p["hp"] = p["max_hp"]
        p["humanity"] = 100
        await db.pool.execute(
            "UPDATE dt_players SET hospital_until=0, hp=max_hp, humanity=100 WHERE user_id=$1", uid
        )

    if p["sleep_until"] > 0 and now >= p["sleep_until"]:
        p["sleep_until"] = 0
        p["humanity"] = 100
        p["hp"] = p["max_hp"]
        await db.pool.execute(
            "UPDATE dt_players SET sleep_until=0, humanity=100, hp=max_hp WHERE user_id=$1", uid
        )

    # ۳. محاسبه آمار کل با احتساب لول، سلاح و زره انتخاب‌شده
    items_rows = await db.pool.fetch("SELECT * FROM dt_items ORDER BY price ASC, id ASC")
    items_map = {r["id"]: dict(r) for r in items_rows}

    w_obj = items_map.get(p["equipped_weapon"], {"hp_bonus": 0, "atk_bonus": 15, "def_bonus": 5, "spd_bonus": 0, "name": "شمشیر پایه"})
    a_obj = items_map.get(p["equipped_armor"], {"hp_bonus": 0, "atk_bonus": 0, "def_bonus": 0, "spd_bonus": 0, "name": "بدون زره"})

    lvl = max(1, int(p["xp"] // 100) + 1)
    calc_max_hp = 100 + (lvl * 20) + w_obj["hp_bonus"] + a_obj["hp_bonus"]
    calc_atk = 15 + (lvl * 6) + w_obj["atk_bonus"] + a_obj["atk_bonus"]
    calc_def = 8 + (lvl * 4) + w_obj["def_bonus"] + a_obj["def_bonus"]
    calc_spd = 10 + (lvl * 2) + w_obj["spd_bonus"] + a_obj["spd_bonus"]

    if lvl != p["level"] or calc_max_hp != p["max_hp"]:
        p["level"] = lvl
        p["max_hp"] = calc_max_hp
        p["hp"] = min(p["hp"], calc_max_hp)
        await db.pool.execute(
            "UPDATE dt_players SET level=$1, max_hp=$2, hp=$3 WHERE user_id=$4",
            lvl, calc_max_hp, p["hp"], uid
        )

    floors = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_floors ORDER BY floor_num ASC")]
    cur_floor_obj = next((f for f in floors if f["floor_num"] == p["current_floor"]), None)
    if not cur_floor_obj and floors:
        cur_floor_obj = floors[-1]

    vouchers = [
        dict(r) for r in await db.pool.fetch(
            "SELECT * FROM dt_vouchers WHERE user_id=$1 ORDER BY id DESC LIMIT 5", uid
        )
    ]

    dev_mode = (await get_dt_config("dev_mode", "0")) == "1"
    male_img = await get_dt_config("male_img", "")
    female_img = await get_dt_config("female_img", "")

    popup_raw = await get_dt_config("active_popup", "")
    popup_data = None
    if popup_raw:
        try:
            pd = json.loads(popup_raw)
            if pd.get("expires_at", 0) > now:
                popup_data = pd
        except Exception:
            pass

    return {
        "dev_mode": dev_mode,
        "is_owner": int(uid) in OWNER_IDS,
        "male_img": male_img,
        "female_img": female_img,
        "popup": popup_data,
        "player": {
            "user_id": p["user_id"],
            "gender": p["gender"],
            "level": p["level"],
            "xp": p["xp"],
            "coins": p["coins"],
            "bank_coins": p["bank_coins"],
            "current_floor": p["current_floor"],
            "hp": p["hp"],
            "max_hp": p["max_hp"],
            "atk": calc_atk,
            "def": calc_def,
            "spd": calc_spd,
            "humanity": p["humanity"],
            "hospital_rem": max(0, int(p["hospital_until"] - now)),
            "sleep_rem": max(0, int(p["sleep_until"] - now)),
            "equipped_weapon": p["equipped_weapon"],
            "equipped_armor": p["equipped_armor"],
            "weapon_name": w_obj["name"],
            "armor_name": a_obj["name"],
            "owned_weapons": json.loads(p["owned_weapons"] or "[1]"),
            "owned_armors": json.loads(p["owned_armors"] or "[]"),
            "inventory": json.loads(p["inventory"] or "[]"),
            "is_banned": p["is_banned"],
        },
        "current_boss": cur_floor_obj,
        "items": list(items_map.values()),
        "vouchers": vouchers,
        "star_packages": [
            {"id": k, **v} for k, v in STAR_PACKAGES.items()
        ],
    }


# ═══════════════════════════════════════════════════════════
# ۳. پردازش اکشن‌های مینی‌اپ برج شیاطین
# ═══════════════════════════════════════════════════════════

async def handle_tower_api_action(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    name = payload.get("name") or "Player"
    action = payload.get("action") or "state"
    now = time.time()

    full_state = await get_tower_safe_state(uid)
    p = full_state["player"]

    if p["is_banned"]:
        return {"ok": False, "error": "⛔ حساب شما در بازی برج شیاطین مسدود شده است.", "state": full_state}

    if full_state["dev_mode"] and not full_state["is_owner"]:
        return {"ok": False, "error": "🛠️ بازی برج شیاطین در حال توسعه و بروزرسانی است (فقط مالک دسترسی دارد).", "state": full_state}

    # ۱. انتخاب جنسیت کاراکتر (فقط یک‌بار و غیرقابل تغییر)
    if action == "choose_gender":
        if p["gender"]:
            return {"ok": False, "error": "کاراکتر شما قبلاً انتخاب شده و غیرقابل تغییر است!", "state": full_state}
        g = payload.get("gender")
        if g not in ("male", "female"):
            return {"ok": False, "error": "انتخاب نامعتبر!", "state": full_state}
        await db.pool.execute("UPDATE dt_players SET gender=$1 WHERE user_id=$2", g, uid)
        return {"ok": True, "msg": "✅ کاراکتر شما برای همیشه ثبت شد!", "state": await get_or_create_player(uid)}

    # ۲. خرید یا تجهیز سلاح و زره
    if action == "buy_or_equip_item":
        item_id = int(payload.get("item_id") or 0)
        item_row = await db.pool.fetchrow("SELECT * FROM dt_items WHERE id=$1", item_id)
        if not item_row:
            return {"ok": False, "error": "آیتم یافت نشد!", "state": full_state}

        itype = item_row["item_type"]
        price = item_row["price"]
        owned_w = p["owned_weapons"]
        owned_a = p["owned_armors"]

        if itype == "weapon":
            if item_id in owned_w:
                await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": f"⚔️ سلاح «{item_row['name']}» برای ورود به مرحله تجهیز شد!", "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": f"سکه کافی ندارید! ({price} سکه نیاز است)", "state": full_state}
            owned_w.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_weapons=$2, equipped_weapon=$3 WHERE user_id=$4",
                price, json.dumps(owned_w), item_id, uid
            )
            return {"ok": True, "msg": f"✅ سلاح «{item_row['name']}» خریداری و تجهیز شد!", "state": await get_or_create_player(uid)}
        else:
            if item_id in owned_a:
                await db.pool.execute("UPDATE dt_players SET equipped_armor=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": f"🛡️ زره «{item_row['name']}» تجهیز شد!", "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": f"سکه کافی ندارید! ({price} سکه نیاز است)", "state": full_state}
            owned_a.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_armors=$2, equipped_armor=$3 WHERE user_id=$4",
                price, json.dumps(owned_a), item_id, uid
            )
            return {"ok": True, "msg": f"✅ زره «{item_row['name']}» خریداری و پوشیده شد!", "state": await get_or_create_player(uid)}

    # ۳. نبرد در طبقه فعلی (با کسر انسانیت و بررسی خواب ۲ روزه یا بیمارستان)
    if action == "battle_floor":
        if not p["gender"]:
            return {"ok": False, "error": "ابتدا از بخش «کاراکتر» جنسیت کاراکتر خود را انتخاب کنید!", "state": full_state}
        if p["sleep_rem"] > 0:
            hrs = round(p["sleep_rem"] / 3600, 1)
            return {"ok": False, "error": f"😴 انسانیت شما به صفر رسیده و کاراکتر در خواب عمیق است ({hrs} ساعت باقی‌مانده).", "state": full_state}
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": f"🏥 شما در بیمارستان بستری هستید ({p['hospital_rem']} ثانیه تا ترخیص).", "state": full_state}
        if p["hp"] <= 10:
            return {"ok": False, "error": "🩸 جان شما بسیار کم است! ابتدا به بیمارستان بروید.", "state": full_state}

        # انتخاب سلاح قبل از ورود به مرحله
        chosen_w = int(payload.get("weapon_id") or p["equipped_weapon"])
        if chosen_w in p["owned_weapons"] and chosen_w != p["equipped_weapon"]:
            await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", chosen_w, uid)
            full_state = await get_or_create_player(uid)
            p = full_state["player"]

        boss = full_state["current_boss"]
        if not boss:
            return {"ok": False, "error": "شما تمام طبقات موجود برج را فتح کرده‌اید!", "state": full_state}

        # محاسبه نبرد بین بازیکن و غول طبقه
        player_dmg = max(8, p["atk"] + int(p["spd"] * 0.4) - int(boss["def"] * 0.5))
        boss_dmg = max(6, boss["atk"] - int(p["def"] * 0.55))
        rounds_to_kill = math.ceil(boss["hp"] / player_dmg)
        total_damage_taken = min(p["hp"], rounds_to_kill * boss_dmg + random.randint(-5, 10))
        total_damage_taken = max(8, total_damage_taken)

        new_hp = max(0, p["hp"] - total_damage_taken)
        new_humanity = max(0, p["humanity"] - random.randint(12, 20))
        sleep_until = (now + 2 * 86400) if new_humanity == 0 else 0

        if new_hp > 0:
            # پیروزی در طبقه -> ارتقای دکمه داینامیک به طبقه بعدی + دریافت غنیمت
            inv = p["inventory"]
            if boss.get("drop_item"):
                inv.append({"name": boss["drop_item"], "price": boss.get("drop_price", 50)})

            await db.pool.execute(
                """UPDATE dt_players
                   SET hp=$1, humanity=$2, sleep_until=$3,
                       coins=coins+$4, xp=xp+$5, current_floor=current_floor+1, inventory=$6
                   WHERE user_id=$7""",
                new_hp, new_humanity, sleep_until,
                boss["reward_coins"], boss["reward_xp"], json.dumps(inv), uid
            )
            msg = (
                f"🏆 طبقه {boss['floor_num']} ({boss['boss_name']}) فتح شد!\n"
                f"🪙 +{boss['reward_coins']} سکه | ⭐ +{boss['reward_xp']} XP\n"
                f"🎁 غنیمت: {boss.get('drop_item') or '—'}\n"
                f"🩸 آسیب دیده‌شده: {total_damage_taken} (انسانیت: {new_humanity}%)"
            )
            if sleep_until > 0:
                msg += "\n⚠️ انسانیت شما به صفر رسید و کاراکتر به مدت ۲ روز به خواب رفت!"
            return {"ok": True, "msg": msg, "state": await get_or_create_player(uid)}
        else:
            await db.pool.execute(
                "UPDATE dt_players SET hp=5, humanity=$1, sleep_until=$2 WHERE user_id=$3",
                new_humanity, sleep_until, uid
            )
            return {
                "ok": False,
                "error": f"💀 در برابر «{boss['boss_name']}» شکست خوردی و مجروح شدی! به بیمارستان مراجعه کن.",
                "state": await get_or_create_player(uid),
            }

    # ۴. بیمارستان (درمان بر حسب میزان آسیب + بازیابی انسانیت)
    if action == "enter_hospital":
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": "شما هم‌اکنون در حال درمان هستید!", "state": full_state}
        missing_hp = max(0, p["max_hp"] - p["hp"])
        missing_hum = max(0, 100 - p["humanity"])
        if missing_hp == 0 and missing_hum == 0:
            return {"ok": False, "error": "جان و انسانیت شما کاملاً پر است!", "state": full_state}

        # زمان درمان بر حسب آسیب (هر امتیاز آسیب = ۲ ثانیه، حداقل ۱۵ ثانیه)
        wait_seconds = max(15, missing_hp * 2 + missing_hum * 2)
        until_ts = now + wait_seconds
        await db.pool.execute("UPDATE dt_players SET hospital_until=$1 WHERE user_id=$2", until_ts, uid)
        return {
            "ok": True,
            "msg": f"🏥 شما در بیمارستان بستری شدید. زمان درمان بر اساس جراحات: {wait_seconds} ثانیه.",
            "state": await get_or_create_player(uid),
        }

    # ۵. فروش غنیمت‌های جنگی در خزانه
    if action == "sell_loot":
        inv = p["inventory"]
        if not inv:
            return {"ok": False, "error": "کیف غنیمت‌های شما خالی است!", "state": full_state}
        total_val = sum(int(x.get("price", 50)) for x in inv)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, inventory='[]' WHERE user_id=$2", total_val, uid
        )
        return {
            "ok": True,
            "msg": f"💰 تمام غنیمت‌ها به مبلغ {total_val} سکه فروخته شد!",
            "state": await get_or_create_player(uid),
        }

    # ۶. سپرده‌گذاری و برداشت از بانک خزانه
    if action == "bank_deposit":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["coins"]:
            return {"ok": False, "error": "مقدار سکه نامعتبر است!", "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins-$1, bank_coins=bank_coins+$1, bank_last_ts=$2 WHERE user_id=$3",
            amt, now, uid
        )
        return {"ok": True, "msg": f"🏦 {amt} سکه در بانک خزانه ذخیره شد (سود ساعتی ۲٪ فعال است).", "state": await get_or_create_player(uid)}

    if action == "bank_withdraw":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["bank_coins"]:
            return {"ok": False, "error": "مقدار برداشت بیشتر از موجودی بانک است!", "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET bank_coins=bank_coins-$1, coins=coins+$1 WHERE user_id=$2",
            amt, uid
        )
        return {"ok": True, "msg": f"🪙 {amt} سکه از بانک به کیف پول منتقل شد.", "state": await get_or_create_player(uid)}

    # ۷. انتقال سکه به کاربر دیگر با دقیقاً ۳ درصد مالیات
    if action == "transfer_coins":
        target_str = str(payload.get("target") or "").strip()
        amt = int(payload.get("amount") or 0)
        if amt < 10:
            return {"ok": False, "error": "حداقل مبلغ انتقال ۱۰ سکه است!", "state": full_state}
        if amt > p["coins"]:
            return {"ok": False, "error": "موجودی سکه شما کافی نیست!", "state": full_state}

        target_uid = None
        if target_str.isdigit():
            target_uid = int(target_str)
        else:
            uname = target_str.lstrip("@").lower()
            row = await db.pool.fetchrow("SELECT user_id FROM users WHERE LOWER(username)=$1", uname)
            if row:
                target_uid = row["user_id"]

        if not target_uid or target_uid == uid:
            return {"ok": False, "error": "کاربر مقصد در ربات یافت نشد!", "state": full_state}

        await get_or_create_player(target_uid)
        tax = max(1, round(amt * 0.03))
        net_amount = amt - tax

        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", amt, uid)
        await db.pool.execute("UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2", net_amount, target_uid)
        return {
            "ok": True,
            "msg": f"✅ مبلغ {amt} سکه ارسال شد.\n📉 کسر ۳٪ مالیات ({tax} سکه) — مبلغ خالص دریافتی: {net_amount} سکه.",
            "state": await get_or_create_player(uid),
        }

    # ۸. خرید بسته سکه و لول با استارز (ساخت لینک فاکتور تلگرام)
    if action == "create_star_invoice":
        pack_id = payload.get("pack_id")
        pack = STAR_PACKAGES.get(pack_id)
        if not pack:
            return {"ok": False, "error": "بسته نامعتبر است!", "state": full_state}

        bot_token = os.environ.get("BOT_TOKEN", "")
        temp_bot = Bot(token=bot_token)
        try:
            invoice_link = await temp_bot.create_invoice_link(
                title=pack["title"],
                description=f"دریافت آنی {pack['coins']:,} سکه و {pack['xp']:,} XP در بازی برج شیاطین",
                payload=f"dtpack_{pack_id}_{uid}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Stars", amount=pack["stars"])],
            )
            return {"ok": True, "invoice_link": invoice_link, "state": full_state}
        except Exception as e:
            return {"ok": False, "error": f"خطا در ساخت درگاه استارز: {e}", "state": full_state}
        finally:
            await temp_bot.session.close()

    # ۹. ثبت کد هدیه
    if action == "redeem_gift":
        code = str(payload.get("code") or "").strip()
        row = await db.pool.fetchrow("SELECT * FROM dt_gifts WHERE code=$1", code)
        if not row:
            return {"ok": False, "error": "❌ کد هدیه نامعتبر یا منقضی است!", "state": full_state}

        used_list = json.loads(row["used_by"] or "[]")
        if uid in used_list:
            return {"ok": False, "error": "⚠️ شما قبلاً از این کد هدیه استفاده کرده‌اید!", "state": full_state}
        if len(used_list) >= row["max_uses"]:
            return {"ok": False, "error": "⚠️ ظرفیت استفاده از این کد هدیه تمام شده است!", "state": full_state}

        used_list.append(uid)
        await db.pool.execute("UPDATE dt_gifts SET used_by=$1 WHERE code=$2", json.dumps(used_list), code)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
            row["coins"], row["xp"], uid
        )
        return {
            "ok": True,
            "msg": f"🎉 کد هدیه اعمال شد! +{row['coins']} سکه و +{row['xp']} XP دریافت کردید.",
            "state": await get_or_create_player(uid),
        }

    # ۱۰. ثبت درخواست ووچر (ارسال به مالک و رفتن به حالت چت در انتظار پاسخ مالک)
    if action == "request_voucher":
        coins_offered = int(payload.get("coins") or 0)
        v_type = str(payload.get("voucher_type") or "ووچر استارز")
        if coins_offered < 100:
            return {"ok": False, "error": "حداقل سکه پیشنهادی برای درخواست ووچر ۱۰۰ سکه است!", "state": full_state}
        if coins_offered > p["coins"]:
            return {"ok": False, "error": "موجودی سکه شما کمتر از مقدار پیشنهادی است!", "state": full_state}

        # کسر امانی سکه تا زمان پاسخ مالک
        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", coins_offered, uid)
        vid = await db.pool.fetchval(
            """INSERT INTO dt_vouchers (user_id, user_name, coins_offered, voucher_type, status, created_at)
               VALUES ($1, $2, $3, $4, 'pending', $5) RETURNING id""",
            uid, name, coins_offered, v_type, now
        )

        # ارسال نوتیفیکیشن به مالک در پیوی ربات
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                for oid in OWNER_IDS:
                    try:
                        await temp_bot.send_message(
                            chat_id=oid,
                            text=(
                                f"🎟️ <b>درخواست ووچر جدید (برج شیاطین #{vid})</b>\n\n"
                                f"👤 کاربر: <b>{name}</b> (<code>{uid}</code>)\n"
                                f"🎁 نوع ووچر: <b>{v_type}</b>\n"
                                f"🪙 سکه پیشنهادی: <b>{coins_offered:,} سکه</b>\n\n"
                                f"وضعیت را انتخاب کنید (امکان ثبت یادداشت برای کاربر وجود دارد):"
                            ),
                            reply_markup=kb([
                                [
                                    success("✅ تایید و صدور کد ووچر", f"dtv_app_{vid}"),
                                    danger("❌ رد درخواست (عودت سکه)", f"dtv_rej_{vid}"),
                                ]
                            ]),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
            finally:
                await temp_bot.session.close()

        return {
            "ok": True,
            "msg": "⏳ درخواست شما ثبت شد و برای مالک ارسال گردید. در انتظار پاسخ مالک...",
            "state": await get_or_create_player(uid),
        }

    return {"ok": True, "state": full_state}


async def get_tower_safe_state(uid: int) -> dict:
    return await get_or_create_player(uid)


# ═══════════════════════════════════════════════════════════
# ۴. هندلر تایید / رد درخواست ووچر توسط مالک + ارسال به پیوی کاربر
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("dtv_app_") | F.data.startswith("dtv_rej_"))
async def cb_owner_voucher_decision(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        await cb.answer("فقط مالک!", show_alert=True)
        return

    parts = cb.data.split("_")
    decision = "approved" if parts[1] == "app" else "rejected"
    vid = int(parts[2])

    await state.set_state(TowerAdminStates.voucher_note)
    await state.update_data(vid=vid, decision=decision)
    await cb.answer()
    await cb.message.reply(
        f"📝 لطفاً یادداشت خود را برای درخواست ووچر #{vid} ({'تایید' if decision=='approved' else 'رد'}) بنویسید:\n"
        f"(اگر یادداشتی ندارید کلمه <code>بدون یادداشت</code> را بفرستید)",
        parse_mode=ParseMode.HTML,
    )


@router.message(StateFilter(TowerAdminStates.voucher_note), F.text)
async def msg_owner_voucher_note(msg: Message, state: FSMContext):
    data = await state.get_data()
    vid = data.get("vid")
    decision = data.get("decision")
    note = msg.text.strip()
    if note == "بدون یادداشت":
        note = ""
    await state.clear()

    await ensure_tower_tables()
    vrow = await db.pool.fetchrow("SELECT * FROM dt_vouchers WHERE id=$1", vid)
    if not vrow:
        await msg.reply("❌ درخواست یافت نشد.")
        return

    target_uid = vrow["user_id"]
    v_code = ""
    if decision == "approved":
        rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        v_code = f"RHINO-VCH-{vid}-{rand_part}"
        await db.pool.execute(
            "UPDATE dt_vouchers SET status='approved', owner_note=$1, voucher_code=$2 WHERE id=$3",
            note, v_code, vid
        )
        # ارسال ۲ پیام مجزا در پیوی کاربر طبق دستور شما
        try:
            voucher_card = (
                f"🎟️ <b>برگه رسمی ووچر برج شیاطین راینو</b>\n\n"
                f"🔹 کد یکتای ووچر: <code>{v_code}</code>\n"
                f"🎁 نوع ووچر: <b>{vrow['voucher_type']}</b>\n"
                f"🪙 سکه پرداخت‌شده: <b>{vrow['coins_offered']:,}</b>\n"
                f"👤 شناسه کاربری: <code>{target_uid}</code>\n"
                + (f"📌 یادداشت مالک: <b>{note}</b>\n" if note else "")
            )
            await msg.bot.send_message(target_uid, voucher_card, parse_mode=ParseMode.HTML)
            await msg.bot.send_message(
                target_uid,
                f"✅ درخواست ووچر شما تایید شد!\n"
                f"👈 <b>برای دریافت هدیه، پیام بالا (حاوی کد ووچر) را برای مالک فوروارد کنید:</b>\n"
                f"🆔 @{OWNER_USERNAME}",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await msg.reply(f"✅ درخواست #{vid} تایید شد و کد ووچر ({v_code}) به پیوی و مینی‌اپ کاربر ارسال گردید.")
    else:
        # در صورت رد شدن، سکه‌های پیشنهادی به حساب بازیکن برمی‌گردد
        await db.pool.execute(
            "UPDATE dt_vouchers SET status='rejected', owner_note=$1 WHERE id=$2",
            note, vid
        )
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2",
            vrow["coins_offered"], target_uid
        )
        try:
            await msg.bot.send_message(
                target_uid,
                f"❌ <b>درخواست ووچر #{vid} شما رد شد</b> و مقدار {vrow['coins_offered']:,} سکه به حساب شما بازگشت.\n"
                + (f"📌 یادداشت مالک: <b>{note}</b>" if note else ""),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await msg.reply(f"❌ درخواست #{vid} رد شد و سکه کاربر عودت داده شد.")


# ═══════════════════════════════════════════════════════════
# ۵. دستور «پنل برج» در پیوی ربات (مدیریت کامل برج شیاطین توسط مالک)
# ═══════════════════════════════════════════════════════════

async def _tower_admin_kb():
    dev_on = (await get_dt_config("dev_mode", "0")) == "1"
    dev_lbl = "🛠️ وضعیت: در حال توسعه (فقط مالک)" if dev_on else "🟢 وضعیت: باز برای همه کاربران"
    return kb([
        [primary("👹 افزودن/ویرایش غول و طبقه", "dtadm:add_floor"),
         danger("🗑️ حذف طبقه", "dtadm:del_floor")],
        [primary("⚔️ افزودن سلاح جدید", "dtadm:add_weapon"),
         danger("🗑️ حذف سلاح", "dtadm:del_weapon")],
        [primary("🛡️ افزودن زره جدید", "dtadm:add_armor"),
         danger("🗑️ حذف زره", "dtadm:del_armor")],
        [primary("🚹 تنظیم عکس کاراکتر مرد", "dtadm:male_img"),
         primary("🚺 تنظیم عکس کاراکتر زن", "dtadm:female_img")],
        [success("🎁 ساخت کد هدیه (سکه/XP)", "dtadm:add_gift"),
         primary("📢 ساخت پاپ‌آپ تبلیغاتی شناور", "dtadm:add_popup")],
        [primary("🔍 بررسی کاربر", "dtadm:check_user"),
         success("⚡ شارژ سکه و XP کاربر", "dtadm:charge_user")],
        [danger("🚫 محروم / آزاد کردن کاربر از برج", "dtadm:ban_user")],
        [success(dev_lbl, "dtadm:toggle_dev")],
    ])


@router.message(Command("tower_panel"))
@router.message(F.text.in_({"پنل برج", "پنل برج شیاطین", "/tower"}))
async def cmd_tower_panel(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return
    await state.clear()
    await ensure_tower_tables()
    floors_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_floors") or 0
    items_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_items") or 0
    players_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_players") or 0

    await msg.answer(
        f"👹 <b>پنل فرماندهی برج شیاطین (Demon Tower)</b>\n\n"
        f"📊 بازیکنان برج: <b>{players_cnt} نفر</b>\n"
        f"🏰 طبقات ثبت‌شده: <b>{floors_cnt} طبقه</b>\n"
        f"⚔️ سلاح‌ها و زره‌ها: <b>{items_cnt} مورد</b>\n\n"
        f"بخش مورد نظر را برای ویرایش انتخاب کنید:",
        reply_markup=await _tower_admin_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "dtadm:toggle_dev")
async def cb_toggle_dev(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        return
    cur = await get_dt_config("dev_mode", "0")
    new_val = "0" if cur == "1" else "1"
    await set_dt_config("dev_mode", new_val)
    await cb.answer("وضعیت بازی تغییر کرد!")
    await cb.message.edit_reply_markup(reply_markup=await _tower_admin_kb())


@router.callback_query(F.data.startswith("dtadm:"))
async def cb_tower_admin_actions(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        return
    act = cb.data.split(":")[1]
    await state.clear()
    await cb.answer()

    if act == "male_img":
        await state.set_state(TowerAdminStates.set_male_img)
        await cb.message.reply("🚹 لینک مستقیم تصویر کاراکتر **مرد** را ارسال کنید:")
    elif act == "female_img":
        await state.set_state(TowerAdminStates.set_female_img)
        await cb.message.reply("🚺 لینک مستقیم تصویر کاراکتر **زن** را ارسال کنید:")
    elif act == "add_floor":
        await state.set_state(TowerAdminStates.add_floor)
        await cb.message.reply(
            "👹 اطلاعات طبقه و غول را در ۱۱ خط یا با جداکننده <code>|</code> بفرستید:\n\n"
            "<code>شماره_طبقه | نام_غول | لینک_عکس | توضیح | قدرت_غول | نقطه_ضعف | جان_HP | حمله_ATK | دفاع_DEF | پاداش_سکه | پاداش_XP | نام_غنیمت | قیمت_فروش_غنیمت</code>\n\n"
            "مثال:\n"
            "<code>5 | غول آتشین | https://.../boss5.png | نگهبان طبقه پنجم | شمشیر گدازه | سپر یخی | 650 | 85 | 40 | 1500 | 500 | یاقوت مذاب | 450</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_floor":
        await state.set_state(TowerAdminStates.del_floor)
        await cb.message.reply("🗑️ شماره طبقه‌ای که می‌خواهید حذف شود را بفرستید:")
    elif act == "add_weapon":
        await state.set_state(TowerAdminStates.add_weapon)
        await cb.message.reply(
            "⚔️ مشخصات سلاح جدید را با جداکننده <code>|</code> بفرستید:\n"
            "<code>نام_سلاح | لینک_عکس | قیمت_سکه | افزایش_جان | افزایش_حمله | افزایش_دفاع | افزایش_سرعت</code>\n\n"
            "مثال:\n"
            "<code>شمشیر اژدها | https://.../w.png | 3000 | 120 | 140 | 30 | 10</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_weapon":
        rows = await db.pool.fetch("SELECT id, name, price FROM dt_items WHERE item_type='weapon' ORDER BY id")
        txt = "\n".join(f"کد <code>{r['id']}</code>: {r['name']} ({r['price']} سکه)" for r in rows)
        await state.set_state(TowerAdminStates.del_weapon)
        await cb.message.reply(f"🗑️ کد سلاح را برای حذف بفرستید:\n\n{txt}", parse_mode=ParseMode.HTML)
    elif act == "add_armor":
        await state.set_state(TowerAdminStates.add_armor)
        await cb.message.reply(
            "🛡️ مشخصات زره جدید را با جداکننده <code>|</code> بفرستید:\n"
            "<code>نام_زره | لینک_عکس | قیمت_سکه | افزایش_جان | افزایش_دفاع | تغییر_سرعت</code>\n\n"
            "مثال:\n"
            "<code>زره الماس | https://.../a.png | 2500 | 200 | 90 | 15</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "del_armor":
        rows = await db.pool.fetch("SELECT id, name, price FROM dt_items WHERE item_type='armor' ORDER BY id")
        txt = "\n".join(f"کد <code>{r['id']}</code>: {r['name']} ({r['price']} سکه)" for r in rows)
        await state.set_state(TowerAdminStates.del_armor)
        await cb.message.reply(f"🗑️ کد زره را برای حذف بفرستید:\n\n{txt}", parse_mode=ParseMode.HTML)
    elif act == "add_gift":
        await state.set_state(TowerAdminStates.add_gift)
        await cb.message.reply(
            "🎁 اطلاعات کد هدیه را با <code>|</code> بفرستید:\n"
            "<code>کد_هدیه | مقدار_سکه | مقدار_XP | تعداد_دفعات_مجاز</code>\n\n"
            "مثال:\n<code>RHINO2026 | 5000 | 500 | 50</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "add_popup":
        await state.set_state(TowerAdminStates.add_popup)
        await cb.message.reply(
            "📢 مشخصات پاپ‌آپ تبلیغاتی شناور در منوی بازی را با <code>|</code> بفرستید:\n"
            "<code>متن_پاپ‌آپ | لینک_عکس_(یا خط تیره -) | متن_دکمه_(یا -) | لینک_دکمه_(یا -) | مدت_ساعت_نمایش</code>\n\n"
            "(برای حذف پاپ‌آپ فعلی کلمه <code>حذف</code> را بفرستید)",
            parse_mode=ParseMode.HTML,
        )
    elif act == "check_user":
        await state.set_state(TowerAdminStates.check_user)
        await cb.message.reply("🔍 آیدی عددی کاربر را برای مشاهده کامل پرونده برج بفرستید:")
    elif act == "charge_user":
        await state.set_state(TowerAdminStates.charge_user)
        await cb.message.reply(
            "⚡ آیدی عددی، سکه و XP را با <code>|</code> بفرستید:\n"
            "<code>آیدی_کاربر | مقدار_سکه_اضافی | مقدار_XP_اضافی</code>\n"
            "مثال: <code>7662192190 | 10000 | 1000</code>",
            parse_mode=ParseMode.HTML,
        )
    elif act == "ban_user":
        await state.set_state(TowerAdminStates.ban_user)
        await cb.message.reply("🚫 آیدی عددی کاربر را بفرستید تا وضعیت مسدودیتش در برج شیاطین تغییر کند:")


@router.message(StateFilter(TowerAdminStates.set_male_img), F.text)
async def st_male_img(msg: Message, state: FSMContext):
    await set_dt_config("male_img", msg.text.strip())
    await state.clear()
    await msg.reply("✅ تصویر کاراکتر مرد ذخیره شد.")


@router.message(StateFilter(TowerAdminStates.set_female_img), F.text)
async def st_female_img(msg: Message, state: FSMContext):
    await set_dt_config("female_img", msg.text.strip())
    await state.clear()
    await msg.reply("✅ تصویر کاراکتر زن ذخیره شد.")


@router.message(StateFilter(TowerAdminStates.add_floor), F.text)
async def st_add_floor(msg: Message, state: FSMContext):
    parts = [x.strip() for x in msg.text.split("|")]
    if len(parts) < 12:
        await msg.reply("❌ تعداد بخش‌ها کامل نیست! طبق فرمت نمونه ارسال کنید.")
        return
    fnum = int(parts[0])
    bname, photo, desc, pdesc, weak = parts[1], parts[2], parts[3], parts[4], parts[5]
    hp, atk, df, rcoins, rxp = int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9]), int(parts[10])
    drop_item = parts[11]
    drop_price = int(parts[12]) if len(parts) > 12 and parts[12].isdigit() else 50
    if photo == "-":
        photo = ""

    await db.pool.execute(
        """INSERT INTO dt_floors (floor_num, boss_name, photo, description, power_desc, weakness, hp, atk, def, reward_coins, reward_xp, drop_item, drop_price)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
           ON CONFLICT (floor_num) DO UPDATE SET
           boss_name=$2, photo=$3, description=$4, power_desc=$5, weakness=$6, hp=$7, atk=$8, def=$9, reward_coins=$10, reward_xp=$11, drop_item=$12, drop_price=$13""",
        fnum, bname, photo, desc, pdesc, weak, hp, atk, df, rcoins, rxp, drop_item, drop_price
    )
    await state.clear()
    await msg.reply(f"✅ طبقه {fnum} ({bname}) با موفقیت ثبت/بروزرسانی شد!")


@router.message(StateFilter(TowerAdminStates.del_floor), F.text)
async def st_del_floor(msg: Message, state: FSMContext):
    if msg.text.strip().isdigit():
        await db.pool.execute("DELETE FROM dt_floors WHERE floor_num=$1", int(msg.text.strip()))
        await state.clear()
        await msg.reply("🗑️ طبقه حذف شد.")


@router.message(StateFilter(TowerAdminStates.add_weapon), F.text)
async def st_add_weapon(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 7:
        await msg.reply("❌ فرمت نادرست است.")
        return
    photo = "" if p[1] == "-" else p[1]
    await db.pool.execute(
        """INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
           VALUES ('weapon', $1, $2, $3, $4, $5, $6, $7)""",
        p[0], photo, int(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6])
    )
    await state.clear()
    await msg.reply(f"⚔️ سلاح «{p[0]}» اضافه شد!")


@router.message(StateFilter(TowerAdminStates.del_weapon), F.text)
@router.message(StateFilter(TowerAdminStates.del_armor), F.text)
async def st_del_item(msg: Message, state: FSMContext):
    if msg.text.strip().isdigit():
        await db.pool.execute("DELETE FROM dt_items WHERE id=$1", int(msg.text.strip()))
        await state.clear()
        await msg.reply("🗑️ آیتم حذف شد.")


@router.message(StateFilter(TowerAdminStates.add_armor), F.text)
async def st_add_armor(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 6:
        await msg.reply("❌ فرمت نادرست است.")
        return
    photo = "" if p[1] == "-" else p[1]
    await db.pool.execute(
        """INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
           VALUES ('armor', $1, $2, $3, $4, 0, $5, $6)""",
        p[0], photo, int(p[2]), int(p[3]), int(p[4]), int(p[5])
    )
    await state.clear()
    await msg.reply(f"🛡️ زره «{p[0]}» اضافه شد!")


@router.message(StateFilter(TowerAdminStates.add_gift), F.text)
async def st_add_gift(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 4:
        await msg.reply("❌ فرمت نادرست است.")
        return
    await db.pool.execute(
        """INSERT INTO dt_gifts (code, coins, xp, max_uses, used_by)
           VALUES ($1, $2, $3, $4, '[]')
           ON CONFLICT (code) DO UPDATE SET coins=$2, xp=$3, max_uses=$4""",
        p[0], int(p[1]), int(p[2]), int(p[3])
    )
    await state.clear()
    await msg.reply(f"🎁 کد هدیه <code>{p[0]}</code> ساخته شد!", parse_mode=ParseMode.HTML)


@router.message(StateFilter(TowerAdminStates.add_popup), F.text)
async def st_add_popup(msg: Message, state: FSMContext):
    if msg.text.strip() == "حذف":
        await set_dt_config("active_popup", "")
        await state.clear()
        await msg.reply("🗑️ پاپ‌آپ تبلیغاتی حذف شد.")
        return
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 5:
        await msg.reply("❌ فرمت نادرست است.")
        return
    hours = float(p[4])
    popup_obj = {
        "text": p[0],
        "photo": "" if p[1] == "-" else p[1],
        "btn_text": "" if p[2] == "-" else p[2],
        "btn_url": "" if p[3] == "-" else p[3],
        "expires_at": time.time() + (hours * 3600),
    }
    await set_dt_config("active_popup", json.dumps(popup_obj))
    await state.clear()
    await msg.reply(f"📢 پاپ‌آپ تبلیغاتی برای مدت {hours} ساعت در منوی برج شیاطین فعال شد!")


@router.message(StateFilter(TowerAdminStates.check_user), F.text)
async def st_check_user(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return
    uid = int(msg.text.strip())
    st = await get_or_create_player(uid)
    p = st["player"]
    await state.clear()
    await msg.reply(
        f"👤 <b>پرونده بازیکن برج شیاطین</b> (<code>{uid}</code>)\n\n"
        f"🔹 جنسیت: {p['gender'] or 'انتخاب نشده'}\n"
        f"⭐ لول: {p['level']} (XP: {p['xp']})\n"
        f"🪙 سکه کیف پول: {p['coins']:,} | 🏦 بانک: {p['bank_coins']:,}\n"
        f"🏰 طبقه فعلی: {p['current_floor']}\n"
        f"❤️ جان: {p['hp']}/{p['max_hp']} | 🧠 انسانیت: {p['humanity']}%\n"
        f"⚔️ سلاح: {p['weapon_name']} | 🛡️ زره: {p['armor_name']}\n"
        f"🚫 مسدود: {'بله' if p['is_banned'] else 'خیر'}",
        parse_mode=ParseMode.HTML,
    )


@router.message(StateFilter(TowerAdminStates.charge_user), F.text)
async def st_charge_user(msg: Message, state: FSMContext):
    p = [x.strip() for x in msg.text.split("|")]
    if len(p) < 3:
        return
    uid, add_c, add_xp = int(p[0]), int(p[1]), int(p[2])
    await get_or_create_player(uid)
    await db.pool.execute(
        "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
        add_c, add_xp, uid
    )
    await state.clear()
    await msg.reply(f"⚡ کاربر <code>{uid}</code> به میزان +{add_c} سکه و +{add_xp} XP شارژ شد!", parse_mode=ParseMode.HTML)


@router.message(StateFilter(TowerAdminStates.ban_user), F.text)
async def st_ban_user(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return
    uid = int(msg.text.strip())
    await get_or_create_player(uid)
    cur = await db.pool.fetchval("SELECT is_banned FROM dt_players WHERE user_id=$1", uid)
    new_b = not bool(cur)
    await db.pool.execute("UPDATE dt_players SET is_banned=$1 WHERE user_id=$2", new_b, uid)
    await state.clear()
    await msg.reply(f"وضعیت مسدودیت کاربر {uid} در برج شیاطین به «{'مسدود' if new_b else 'آزاد'}» تغییر یافت.")
