# -*- coding: utf-8 -*-
"""games/demon_tower.py — موتور برج شیاطین + API پنل مدیریت مینی‌اپی ویژه مالک با آپلود مستقیم تصویر"""

import json
import math
import os
import random
import string
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.enums import ParseMode
from aiogram.filters import Command

from database import db
from emojis import E
from utils.premium import primary, success, danger, kb

router = Router(name="demon_tower")
OWNER_IDS = {7662192190, 6041119040}
OWNER_USERNAME = "oldkaseb"
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

STAR_PACKAGES = {
    "pack_1": {"stars": 50,  "coins": 2500,  "xp": 300,  "title": "Starter Hunter (2,500 Coins + 300 XP)"},
    "pack_2": {"stars": 150, "coins": 9000,  "xp": 1000, "title": "Blood Knight (9,000 Coins + 1,000 XP)"},
    "pack_3": {"stars": 400, "coins": 28000, "xp": 3000, "title": "Tower Lord (28,000 Coins + 3,000 XP)"},
    "pack_4": {"stars": 900, "coins": 75000, "xp": 8000, "title": "Demon Emperor (75,000 Coins + 8,000 XP)"},
}

DT_MESSAGES = {
    "fa": {
        "banned": "⛔ حساب شما در بازی برج شیاطین مسدود شده است.",
        "dev_mode": "🛠️ بازی برج شیاطین در حال توسعه است (فقط مالک دسترسی دارد).",
        "gender_locked": "کاراکتر شما قبلاً انتخاب شده و غیرقابل تغییر است!",
        "gender_saved": "✅ کاراکتر شما برای همیشه ثبت شد!",
        "item_not_found": "آیتم یافت نشد!",
        "equipped": "✅ آیتم «{name}» تجهیز شد!",
        "not_enough_coins": "سکه کافی ندارید! ({price} سکه نیاز است)",
        "bought_equipped": "✅ آیتم «{name}» خریداری و تجهیز شد!",
        "pick_gender_first": "ابتدا از بخش «کاراکتر» جنسیت خود را انتخاب کنید!",
        "sleeping": "😴 انسانیت شما صفر شده و کاراکتر در خواب ۲ روزه است ({hrs} ساعت باقی‌مانده).",
        "in_hospital": "🏥 شما در بیمارستان بستری هستید ({sec} ثانیه تا ترخیص).",
        "low_hp": "🩸 جان شما بسیار کم است! ابتدا به بیمارستان بروید.",
        "all_cleared": "🎉 شما تمام طبقات موجود برج را فتح کرده‌اید!",
        "floor_won": "🏆 طبقه {floor} ({boss}) فتح شد!\n🪙 +{coins} سکه | ⭐ +{xp} XP\n🎁 غنیمت: {drop}\n🩸 آسیب: {dmg} (انسانیت: {hum}%)",
        "sleep_triggered": "\n⚠️ انسانیت شما به صفر رسید و کاراکتر ۲ روز به خواب رفت!",
        "floor_lost": "💀 در برابر «{boss}» شکست خوردی و مجروح شدی! به بیمارستان مراجعه کن.",
        "already_hospital": "شما هم‌اکنون در حال درمان هستید!",
        "full_hp_hum": "جان و انسانیت شما کاملاً پر است!",
        "hospital_entered": "🏥 بستری شدید. زمان درمان بر اساس آسیب: {sec} ثانیه.",
        "empty_loot": "کیف غنیمت‌های شما خالی است!",
        "loot_sold": "💰 تمام غنیمت‌ها به مبلغ {val} سکه فروخته شد!",
        "invalid_amount": "مقدار سکه نامعتبر است!",
        "bank_deposited": "🏦 {amt} سکه در بانک ذخیره شد (سود ساعتی ۲٪ فعال است).",
        "bank_withdrawn": "🪙 {amt} سکه از بانک به کیف پول منتقل شد.",
        "min_transfer": "حداقل مبلغ انتقال ۱۰ سکه است!",
        "user_not_found": "کاربر مقصد در ربات یافت نشد!",
        "transfer_ok": "✅ {amt} سکه ارسال شد.\n📉 کسر ۳٪ مالیات ({tax} سکه) — دریافتی خالص: {net} سکه.",
        "invalid_gift": "❌ کد هدیه نامعتبر یا منقضی است!",
        "gift_used": "⚠️ شما قبلاً از این کد استفاده کرده‌اید!",
        "gift_full": "⚠️ ظرفیت این کد هدیه تمام شده است!",
        "gift_ok": "🎉 کد هدیه اعمال شد! +{coins} سکه و +{xp} XP دریافت کردید.",
        "min_voucher": "حداقل سکه پیشنهادی برای درخواست ووچر ۱۰۰ سکه است!",
        "voucher_sent": "⏳ درخواست ثبت شد و برای مالک ارسال گردید. در انتظار پاسخ مالک...",
    },
    "en": {
        "banned": "⛔ Your Demon Tower account is banned.",
        "dev_mode": "🛠️ Demon Tower is under maintenance (Owner only).",
        "gender_locked": "Character gender is already chosen and cannot be changed!",
        "gender_saved": "✅ Your character has been permanently registered!",
        "item_not_found": "Item not found!",
        "equipped": "✅ '{name}' equipped!",
        "not_enough_coins": "Not enough coins! ({price} required)",
        "bought_equipped": "✅ '{name}' purchased and equipped!",
        "pick_gender_first": "Please select your character gender in 'Character' menu first!",
        "sleeping": "😴 Humanity reached 0! Character is sleeping for 2 days ({hrs}h left).",
        "in_hospital": "🏥 You are recovering in the hospital ({sec}s left).",
        "low_hp": "🩸 Your HP is too low! Visit the hospital first.",
        "all_cleared": "🎉 You have conquered all available floors!",
        "floor_won": "🏆 Floor {floor} ({boss}) Cleared!\n🪙 +{coins} Coins | ⭐ +{xp} XP\n🎁 Loot: {drop}\n🩸 Damage taken: {dmg} (Humanity: {hum}%)",
        "sleep_triggered": "\n⚠️ Humanity hit 0! Your character fell asleep for 2 days!",
        "floor_lost": "💀 Defeated by '{boss}'! Go to the hospital to heal.",
        "already_hospital": "You are already being treated!",
        "full_hp_hum": "Your HP and Humanity are already full!",
        "hospital_entered": "🏥 Admitted to hospital. Recovery time: {sec}s.",
        "empty_loot": "Your loot bag is empty!",
        "loot_sold": "💰 All loot sold for {val} coins!",
        "invalid_amount": "Invalid coin amount!",
        "bank_deposited": "🏦 {amt} coins deposited in bank (2% hourly interest active).",
        "bank_withdrawn": "🪙 {amt} coins withdrawn to wallet.",
        "min_transfer": "Minimum transfer is 10 coins!",
        "user_not_found": "Target user not found in bot!",
        "transfer_ok": "✅ {amt} coins sent.\n📉 3% Tax ({tax} coins) — Net received: {net} coins.",
        "invalid_gift": "❌ Invalid or expired gift code!",
        "gift_used": "⚠️ You already used this gift code!",
        "gift_full": "⚠️ Gift code usage limit reached!",
        "gift_ok": "🎉 Gift redeemed! +{coins} Coins & +{xp} XP added.",
        "min_voucher": "Minimum offer for a voucher is 100 coins!",
        "voucher_sent": "⏳ Request sent to Owner. Waiting for owner response...",
    },
}


def _dt_msg(lang: str, key: str, **kwargs) -> str:
    d = DT_MESSAGES.get(lang, DT_MESSAGES.get("en" if lang != "fa" else "fa", DT_MESSAGES["fa"]))
    txt = d.get(key, DT_MESSAGES["fa"].get(key, key))
    return txt.format(**kwargs) if kwargs else txt


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
                item_type TEXT,
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
                status TEXT DEFAULT 'pending',
                owner_note TEXT DEFAULT '',
                voucher_code TEXT DEFAULT '',
                created_at DOUBLE PRECISION
            );
        """)

        w_count = await conn.fetchval("SELECT COUNT(*) FROM dt_items WHERE item_type='weapon'")
        if not w_count:
            await conn.execute("""
                INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
                VALUES
                ('weapon', 'شمشیر شکارچی (رایگان)', '', 0, 10, 18, 5, 0),
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
                (1, 'نگهبان دروازه خاکستر', '', 'اسکلت غول‌پیکر طبقه اول', 'زنجیر آتشین', 'ضربه سریع', 95, 16, 6, 120, 45, 'گوهر خاکستر', 40),
                (2, 'گرگینه خون‌خوار', '', 'شکارچی شب در طبقه دوم', 'پنجه زهرآلود', 'سپر نقره‌ای', 165, 26, 12, 240, 85, 'ناب گرگینه', 85),
                (3, 'ارباب سایه‌ها', '', 'جادوگر سقوط‌کرده طبقه سوم', 'جذب روح', 'تیغه خون‌آشام', 270, 40, 20, 450, 150, 'تاج سایه', 160),
                (4, 'اژدهای استخوانی', '', 'فرمانروای طبقه چهارم', 'طوفان شعله', 'زره پولادین', 460, 62, 35, 900, 320, 'قلب اژدها', 350);
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
        "star_packages": [{"id": k, **v} for k, v in STAR_PACKAGES.items()],
    }


async def handle_tower_api_action(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    name = payload.get("name") or "Player"
    lang = payload.get("lang") or "fa"
    action = payload.get("action") or "state"
    now = time.time()

    full_state = await get_or_create_player(uid)
    p = full_state["player"]

    if p["is_banned"]:
        return {"ok": False, "error": _dt_msg(lang, "banned"), "state": full_state}

    if full_state["dev_mode"] and not full_state["is_owner"]:
        return {"ok": False, "error": _dt_msg(lang, "dev_mode"), "state": full_state}

    if action == "choose_gender":
        if p["gender"]:
            return {"ok": False, "error": _dt_msg(lang, "gender_locked"), "state": full_state}
        g = payload.get("gender")
        if g not in ("male", "female"):
            return {"ok": False, "error": "Invalid", "state": full_state}
        await db.pool.execute("UPDATE dt_players SET gender=$1 WHERE user_id=$2", g, uid)
        return {"ok": True, "msg": _dt_msg(lang, "gender_saved"), "state": await get_or_create_player(uid)}

    if action == "buy_or_equip_item":
        item_id = int(payload.get("item_id") or 0)
        item_row = await db.pool.fetchrow("SELECT * FROM dt_items WHERE id=$1", item_id)
        if not item_row:
            return {"ok": False, "error": _dt_msg(lang, "item_not_found"), "state": full_state}

        itype = item_row["item_type"]
        price = item_row["price"]
        owned_w = p["owned_weapons"]
        owned_a = p["owned_armors"]

        if itype == "weapon":
            if item_id in owned_w:
                await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_w.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_weapons=$2, equipped_weapon=$3 WHERE user_id=$4",
                price, json.dumps(owned_w), item_id, uid
            )
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
        else:
            if item_id in owned_a:
                await db.pool.execute("UPDATE dt_players SET equipped_armor=$1 WHERE user_id=$2", item_id, uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_a.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_armors=$2, equipped_armor=$3 WHERE user_id=$4",
                price, json.dumps(owned_a), item_id, uid
            )
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": await get_or_create_player(uid)}

    if action == "battle_floor":
        if not p["gender"]:
            return {"ok": False, "error": _dt_msg(lang, "pick_gender_first"), "state": full_state}
        if p["sleep_rem"] > 0:
            hrs = round(p["sleep_rem"] / 3600, 1)
            return {"ok": False, "error": _dt_msg(lang, "sleeping", hrs=hrs), "state": full_state}
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": _dt_msg(lang, "in_hospital", sec=p["hospital_rem"]), "state": full_state}
        if p["hp"] <= 10:
            return {"ok": False, "error": _dt_msg(lang, "low_hp"), "state": full_state}

        chosen_w = int(payload.get("weapon_id") or p["equipped_weapon"])
        if chosen_w in p["owned_weapons"] and chosen_w != p["equipped_weapon"]:
            await db.pool.execute("UPDATE dt_players SET equipped_weapon=$1 WHERE user_id=$2", chosen_w, uid)
            full_state = await get_or_create_player(uid)
            p = full_state["player"]

        boss = full_state["current_boss"]
        if not boss:
            return {"ok": False, "error": _dt_msg(lang, "all_cleared"), "state": full_state}

        player_dmg = max(8, p["atk"] + int(p["spd"] * 0.4) - int(boss["def"] * 0.5))
        boss_dmg = max(6, boss["atk"] - int(p["def"] * 0.55))
        rounds_to_kill = math.ceil(boss["hp"] / player_dmg)
        total_damage_taken = max(8, min(p["hp"], rounds_to_kill * boss_dmg + random.randint(-5, 10)))

        new_hp = max(0, p["hp"] - total_damage_taken)
        new_humanity = max(0, p["humanity"] - random.randint(12, 20))
        sleep_until = (now + 2 * 86400) if new_humanity == 0 else 0

        if new_hp > 0:
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
            msg = _dt_msg(
                lang, "floor_won",
                floor=boss["floor_num"], boss=boss["boss_name"],
                coins=boss["reward_coins"], xp=boss["reward_xp"],
                drop=boss.get("drop_item") or "—", dmg=total_damage_taken, hum=new_humanity
            )
            if sleep_until > 0:
                msg += _dt_msg(lang, "sleep_triggered")
            return {"ok": True, "msg": msg, "state": await get_or_create_player(uid)}
        else:
            await db.pool.execute(
                "UPDATE dt_players SET hp=5, humanity=$1, sleep_until=$2 WHERE user_id=$3",
                new_humanity, sleep_until, uid
            )
            return {
                "ok": False,
                "error": _dt_msg(lang, "floor_lost", boss=boss["boss_name"]),
                "state": await get_or_create_player(uid),
            }

    if action == "enter_hospital":
        if p["hospital_rem"] > 0:
            return {"ok": False, "error": _dt_msg(lang, "already_hospital"), "state": full_state}
        missing_hp = max(0, p["max_hp"] - p["hp"])
        missing_hum = max(0, 100 - p["humanity"])
        if missing_hp == 0 and missing_hum == 0:
            return {"ok": False, "error": _dt_msg(lang, "full_hp_hum"), "state": full_state}

        wait_seconds = max(15, missing_hp * 2 + missing_hum * 2)
        until_ts = now + wait_seconds
        await db.pool.execute("UPDATE dt_players SET hospital_until=$1 WHERE user_id=$2", until_ts, uid)
        return {
            "ok": True,
            "msg": _dt_msg(lang, "hospital_entered", sec=wait_seconds),
            "state": await get_or_create_player(uid),
        }

    if action == "sell_loot":
        inv = p["inventory"]
        if not inv:
            return {"ok": False, "error": _dt_msg(lang, "empty_loot"), "state": full_state}
        total_val = sum(int(x.get("price", 50)) for x in inv)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, inventory='[]' WHERE user_id=$2", total_val, uid
        )
        return {
            "ok": True,
            "msg": _dt_msg(lang, "loot_sold", val=total_val),
            "state": await get_or_create_player(uid),
        }

    if action == "bank_deposit":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "invalid_amount"), "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins-$1, bank_coins=bank_coins+$1, bank_last_ts=$2 WHERE user_id=$3",
            amt, now, uid
        )
        return {"ok": True, "msg": _dt_msg(lang, "bank_deposited", amt=amt), "state": await get_or_create_player(uid)}

    if action == "bank_withdraw":
        amt = int(payload.get("amount") or 0)
        if amt <= 0 or amt > p["bank_coins"]:
            return {"ok": False, "error": _dt_msg(lang, "invalid_amount"), "state": full_state}
        await db.pool.execute(
            "UPDATE dt_players SET bank_coins=bank_coins-$1, coins=coins+$1 WHERE user_id=$2",
            amt, uid
        )
        return {"ok": True, "msg": _dt_msg(lang, "bank_withdrawn", amt=amt), "state": await get_or_create_player(uid)}

    if action == "transfer_coins":
        target_str = str(payload.get("target") or "").strip()
        amt = int(payload.get("amount") or 0)
        if amt < 10:
            return {"ok": False, "error": _dt_msg(lang, "min_transfer"), "state": full_state}
        if amt > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=amt), "state": full_state}

        target_uid = None
        if target_str.isdigit():
            target_uid = int(target_str)
        else:
            uname = target_str.lstrip("@").lower()
            row = await db.pool.fetchrow("SELECT user_id FROM users WHERE LOWER(username)=$1", uname)
            if row:
                target_uid = row["user_id"]

        if not target_uid or target_uid == uid:
            return {"ok": False, "error": _dt_msg(lang, "user_not_found"), "state": full_state}

        await get_or_create_player(target_uid)
        tax = max(1, round(amt * 0.03))
        net_amount = amt - tax

        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", amt, uid)
        await db.pool.execute("UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2", net_amount, target_uid)
        return {
            "ok": True,
            "msg": _dt_msg(lang, "transfer_ok", amt=amt, tax=tax, net=net_amount),
            "state": await get_or_create_player(uid),
        }

    if action == "create_star_invoice":
        pack_id = payload.get("pack_id")
        pack = STAR_PACKAGES.get(pack_id)
        if not pack:
            return {"ok": False, "error": "Invalid Pack", "state": full_state}

        bot_token = os.environ.get("BOT_TOKEN", "")
        temp_bot = Bot(token=bot_token)
        try:
            invoice_link = await temp_bot.create_invoice_link(
                title=pack["title"],
                description=f"+{pack['coins']:,} Coins & +{pack['xp']:,} XP in Demon Tower",
                payload=f"dtpack_{pack_id}_{uid}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Stars", amount=pack["stars"])],
            )
            return {"ok": True, "invoice_link": invoice_link, "state": full_state}
        except Exception as e:
            return {"ok": False, "error": str(e), "state": full_state}
        finally:
            await temp_bot.session.close()

    if action == "redeem_gift":
        code = str(payload.get("code") or "").strip()
        row = await db.pool.fetchrow("SELECT * FROM dt_gifts WHERE code=$1", code)
        if not row:
            return {"ok": False, "error": _dt_msg(lang, "invalid_gift"), "state": full_state}

        used_list = json.loads(row["used_by"] or "[]")
        if uid in used_list:
            return {"ok": False, "error": _dt_msg(lang, "gift_used"), "state": full_state}
        if len(used_list) >= row["max_uses"]:
            return {"ok": False, "error": _dt_msg(lang, "gift_full"), "state": full_state}

        used_list.append(uid)
        await db.pool.execute("UPDATE dt_gifts SET used_by=$1 WHERE code=$2", json.dumps(used_list), code)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
            row["coins"], row["xp"], uid
        )
        return {
            "ok": True,
            "msg": _dt_msg(lang, "gift_ok", coins=row["coins"], xp=row["xp"]),
            "state": await get_or_create_player(uid),
        }

    if action == "request_voucher":
        coins_offered = int(payload.get("coins") or 0)
        v_type = str(payload.get("voucher_type") or "ووچر استارز")
        if coins_offered < 100:
            return {"ok": False, "error": _dt_msg(lang, "min_voucher"), "state": full_state}
        if coins_offered > p["coins"]:
            return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=coins_offered), "state": full_state}

        await db.pool.execute("UPDATE dt_players SET coins=coins-$1 WHERE user_id=$2", coins_offered, uid)
        vid = await db.pool.fetchval(
            """INSERT INTO dt_vouchers (user_id, user_name, coins_offered, voucher_type, status, created_at)
               VALUES ($1, $2, $3, $4, 'pending', $5) RETURNING id""",
            uid, name, coins_offered, v_type, now
        )

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
                                f"از دکمه زیر وارد مینی‌اپ پنل برج شوید و در تب «ووچرها» با یادداشت تایید یا رد کنید:"
                            ),
                            reply_markup=kb([
                                [success("👑 باز کردن مینی‌اپ پنل برج", web_app_url=f"{MINI_APP_URL}/?game=tower_admin&uid={oid}")]
                            ]),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
            finally:
                await temp_bot.session.close()

        return {
            "ok": True,
            "msg": _dt_msg(lang, "voucher_sent"),
            "state": await get_or_create_player(uid),
        }

    return {"ok": True, "state": full_state}


# ═══════════════════════════════════════════════════════════════════════════
# API مخفی مینی‌اپ پنل برج (فقط و فقط برای OWNER_IDS)
# ═══════════════════════════════════════════════════════════════════════════

async def handle_tower_admin_api(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    if uid not in OWNER_IDS:
        return {"ok": False, "error": "⛔ دسترسی غیرمجاز! این پنل فقط مخصوص مالک ربات است."}

    await ensure_tower_tables()
    action = payload.get("action") or "state"
    msg_out = ""

    if action == "toggle_dev":
        cur = await get_dt_config("dev_mode", "0")
        new_val = "0" if cur == "1" else "1"
        await set_dt_config("dev_mode", new_val)
        msg_out = "🛠️ وضعیت بازی به «در حال توسعه» تغییر کرد." if new_val == "1" else "🟢 بازی برای همه کاربران باز شد."

    elif action == "save_gender_imgs":
        male_img = payload.get("male_img")
        female_img = payload.get("female_img")
        if male_img is not None and male_img != "":
            await set_dt_config("male_img", male_img)
        if female_img is not None and female_img != "":
            await set_dt_config("female_img", female_img)
        msg_out = "✅ تصاویر کاراکتر مرد و زن با موفقیت آپلود و ذخیره شدند!"

    elif action == "save_floor":
        fnum = int(payload.get("floor_num") or 1)
        bname = str(payload.get("boss_name") or f"Boss {fnum}").strip()
        photo = str(payload.get("photo") or "").strip()
        desc = str(payload.get("description") or "").strip()
        pdesc = str(payload.get("power_desc") or "").strip()
        weak = str(payload.get("weakness") or "").strip()
        hp = int(payload.get("hp") or 100)
        atk = int(payload.get("atk") or 20)
        df = int(payload.get("def_val") or 10)
        rcoins = int(payload.get("reward_coins") or 100)
        rxp = int(payload.get("reward_xp") or 50)
        drop_item = str(payload.get("drop_item") or "").strip()
        drop_price = int(payload.get("drop_price") or 50)

        # اگر عکس جدیدی آپلود نشده بود، عکس قبلی طبقه حفظ شود
        if not photo:
            old_p = await db.pool.fetchval("SELECT photo FROM dt_floors WHERE floor_num=$1", fnum)
            photo = old_p or ""

        await db.pool.execute(
            """INSERT INTO dt_floors (floor_num, boss_name, photo, description, power_desc, weakness, hp, atk, def, reward_coins, reward_xp, drop_item, drop_price)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
               ON CONFLICT (floor_num) DO UPDATE SET
               boss_name=$2, photo=$3, description=$4, power_desc=$5, weakness=$6, hp=$7, atk=$8, def=$9, reward_coins=$10, reward_xp=$11, drop_item=$12, drop_price=$13""",
            fnum, bname, photo, desc, pdesc, weak, hp, atk, df, rcoins, rxp, drop_item, drop_price
        )
        msg_out = f"✅ طبقه {fnum} ({bname}) با موفقیت ذخیره شد!"

    elif action == "delete_floor":
        fnum = int(payload.get("floor_num") or 0)
        await db.pool.execute("DELETE FROM dt_floors WHERE floor_num=$1", fnum)
        msg_out = f"🗑️ طبقه {fnum} حذف شد."

    elif action == "save_item":
        itype = str(payload.get("item_type") or "weapon")
        name = str(payload.get("name") or "Item").strip()
        photo = str(payload.get("photo") or "").strip()
        price = int(payload.get("price") or 0)
        hp_b = int(payload.get("hp_bonus") or 0)
        atk_b = int(payload.get("atk_bonus") or 0)
        def_b = int(payload.get("def_bonus") or 0)
        spd_b = int(payload.get("spd_bonus") or 0)

        await db.pool.execute(
            """INSERT INTO dt_items (item_type, name, photo, price, hp_bonus, atk_bonus, def_bonus, spd_bonus)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            itype, name, photo, price, hp_b, atk_b, def_b, spd_b
        )
        msg_out = f"✅ {'سلاح' if itype=='weapon' else 'زره'} «{name}» با موفقیت اضافه شد!"

    elif action == "delete_item":
        item_id = int(payload.get("item_id") or 0)
        await db.pool.execute("DELETE FROM dt_items WHERE id=$1", item_id)
        msg_out = "🗑️ آیتم حذف شد."

    elif action == "save_gift":
        code = str(payload.get("code") or "").strip()
        coins = int(payload.get("coins") or 0)
        xp = int(payload.get("xp") or 0)
        max_uses = int(payload.get("max_uses") or 1)
        if code:
            await db.pool.execute(
                """INSERT INTO dt_gifts (code, coins, xp, max_uses, used_by)
                   VALUES ($1, $2, $3, $4, '[]')
                   ON CONFLICT (code) DO UPDATE SET coins=$2, xp=$3, max_uses=$4""",
                code, coins, xp, max_uses
            )
            msg_out = f"🎁 کد هدیه «{code}» ساخته شد!"

    elif action == "delete_gift":
        code = str(payload.get("code") or "").strip()
        await db.pool.execute("DELETE FROM dt_gifts WHERE code=$1", code)
        msg_out = "🗑️ کد هدیه حذف شد."

    elif action == "save_popup":
        if payload.get("clear"):
            await set_dt_config("active_popup", "")
            msg_out = "🗑️ پاپ‌آپ تبلیغاتی غیرفعال شد."
        else:
            hours = float(payload.get("hours") or 24)
            pop_obj = {
                "text": str(payload.get("text") or "").strip(),
                "photo": str(payload.get("photo") or "").strip(),
                "btn_text": str(payload.get("btn_text") or "").strip(),
                "btn_url": str(payload.get("btn_url") or "").strip(),
                "expires_at": time.time() + (hours * 3600),
            }
            await set_dt_config("active_popup", json.dumps(pop_obj))
            msg_out = f"📢 پاپ‌آپ تبلیغاتی برای مدت {hours} ساعت فعال شد!"

    elif action == "Lookup_user":
        t_uid = int(payload.get("target_uid") or 0)
        st = await get_or_create_player(t_uid)
        return {"ok": True, "looked_up": st["player"], "admin_data": await _collect_admin_state()}

    elif action == "charge_user":
        t_uid = int(payload.get("target_uid") or 0)
        add_c = int(payload.get("add_coins") or 0)
        add_x = int(payload.get("add_xp") or 0)
        await get_or_create_player(t_uid)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, xp=xp+$2 WHERE user_id=$3",
            add_c, add_x, t_uid
        )
        st = await get_or_create_player(t_uid)
        return {
            "ok": True,
            "msg": f"⚡ کاربر {t_uid} شارژ شد (+{add_c} سکه | +{add_x} XP)",
            "looked_up": st["player"],
            "admin_data": await _collect_admin_state(),
        }

    elif action == "toggle_ban_user":
        t_uid = int(payload.get("target_uid") or 0)
        await get_or_create_player(t_uid)
        cur = await db.pool.fetchval("SELECT is_banned FROM dt_players WHERE user_id=$1", t_uid)
        new_b = not bool(cur)
        await db.pool.execute("UPDATE dt_players SET is_banned=$1 WHERE user_id=$2", new_b, t_uid)
        st = await get_or_create_player(t_uid)
        return {
            "ok": True,
            "msg": f"وضعیت کاربر {t_uid} به «{'مسدود' if new_b else 'آزاد'}» تغییر یافت.",
            "looked_up": st["player"],
            "admin_data": await _collect_admin_state(),
        }

    elif action == "decide_voucher":
        vid = int(payload.get("voucher_id") or 0)
        decision = str(payload.get("decision") or "approved")
        note = str(payload.get("note") or "").strip()
        vrow = await db.pool.fetchrow("SELECT * FROM dt_vouchers WHERE id=$1", vid)
        if vrow and vrow["status"] == "pending":
            target_uid = vrow["user_id"]
            bot_token = os.environ.get("BOT_TOKEN", "")
            temp_bot = Bot(token=bot_token) if bot_token else None
            try:
                if decision == "approved":
                    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    v_code = f"RHINO-VCH-{vid}-{rand_part}"
                    await db.pool.execute(
                        "UPDATE dt_vouchers SET status='approved', owner_note=$1, voucher_code=$2 WHERE id=$3",
                        note, v_code, vid
                    )
                    if temp_bot:
                        voucher_card = (
                            f"🎟️ <b>برگه رسمی ووچر برج شیاطین راینو</b>\n\n"
                            f"🔹 کد یکتای ووچر: <code>{v_code}</code>\n"
                            f"🎁 نوع ووچر: <b>{vrow['voucher_type']}</b>\n"
                            f"🪙 سکه پرداخت‌شده: <b>{vrow['coins_offered']:,}</b>\n"
                            f"👤 شناسه کاربری: <code>{target_uid}</code>\n"
                            + (f"📌 یادداشت مالک: <b>{note}</b>\n" if note else "")
                        )
                        await temp_bot.send_message(target_uid, voucher_card, parse_mode=ParseMode.HTML)
                        await temp_bot.send_message(
                            target_uid,
                            f"✅ درخواست ووچر شما تایید شد!\n"
                            f"👈 <b>برای دریافت هدیه، پیام بالا (حاوی کد ووچر) را برای مالک فوروارد کنید:</b>\n"
                            f"🆔 @{OWNER_USERNAME}",
                            parse_mode=ParseMode.HTML,
                        )
                    msg_out = f"✅ ووچر #{vid} تایید شد و کد {v_code} به پیوی کاربر ارسال گردید."
                else:
                    await db.pool.execute(
                        "UPDATE dt_vouchers SET status='rejected', owner_note=$1 WHERE id=$2",
                        note, vid
                    )
                    await db.pool.execute(
                        "UPDATE dt_players SET coins=coins+$1 WHERE user_id=$2",
                        vrow["coins_offered"], target_uid
                    )
                    if temp_bot:
                        await temp_bot.send_message(
                            target_uid,
                            f"❌ <b>درخواست ووچر #{vid} شما رد شد</b> و مقدار {vrow['coins_offered']:,} سکه به حساب شما بازگشت.\n"
                            + (f"📌 یادداشت مالک: <b>{note}</b>" if note else ""),
                            parse_mode=ParseMode.HTML,
                        )
                    msg_out = f"❌ ووچر #{vid} رد شد و سکه کاربر برگردانده شد."
            except Exception:
                pass
            finally:
                if temp_bot:
                    await temp_bot.session.close()

    return {"ok": True, "msg": msg_out, "admin_data": await _collect_admin_state()}


async def _collect_admin_state() -> dict:
    floors = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_floors ORDER BY floor_num ASC")]
    items = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_items ORDER BY item_type, price ASC, id ASC")]
    gifts = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_gifts ORDER BY code ASC")]
    vouchers = [dict(r) for r in await db.pool.fetch("SELECT * FROM dt_vouchers ORDER BY id DESC LIMIT 25")]
    players_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM dt_players") or 0
    dev_mode = (await get_dt_config("dev_mode", "0")) == "1"
    male_img = await get_dt_config("male_img", "")
    female_img = await get_dt_config("female_img", "")
    popup_raw = await get_dt_config("active_popup", "")
    popup_data = None
    if popup_raw:
        try:
            popup_data = json.loads(popup_raw)
        except Exception:
            pass

    return {
        "players_count": players_cnt,
        "dev_mode": dev_mode,
        "male_img": male_img,
        "female_img": female_img,
        "popup": popup_data,
        "floors": floors,
        "items": items,
        "gifts": gifts,
        "vouchers": vouchers,
    }


# ═══════════════════════════════════════════════════════════════════════════
# دستور «پنل برج» در پیوی ربات (باز کردن مستقیم مینی‌اپ مخفی مالک)
# ═══════════════════════════════════════════════════════════════════════════

@router.message(Command("tower_panel"))
@router.message(F.text.in_({"پنل برج", "پنل برج شیاطین", "/tower"}))
async def cmd_tower_panel(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    uid = msg.from_user.id
    admin_url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    await msg.answer(
        f"👑 <b>مینی‌اپ اختصاصی مدیریت برج شیاطین</b>\n\n"
        f"این پنل کاملاً از کاربران عادی مخفی است و فقط برای مالک باز می‌شود.\n"
        f"در داخل مینی‌اپ می‌توانید خانه‌به‌خانه غول‌ها، سلاح‌ها، زره‌ها، کدهای هدیه، پاپ‌آپ و ووچرها را مدیریت کنید و عکس‌ها را مستقیم از گالری آپلود نمایید:",
        reply_markup=kb([
            [success("👑 ورود به مینی‌اپ پنل برج (ویژه مالک)", web_app_url=admin_url)]
        ]),
        parse_mode=ParseMode.HTML,
    )
