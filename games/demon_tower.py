# -*- coding: utf-8 -*-
"""games/demon_tower.py — موتور کامل ۷ زبانه برج شیاطین + API پنل فرماندهی کل ربات بدون وابستگی به متدهای فرعی db"""

import json
import math
import os
import random
import string
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.enums import ParseMode
from aiogram.filters import Command

from database import db
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

active_tower_battles: dict[int, dict] = {}

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
    d = DT_MESSAGES.get(lang, DT_MESSAGES["en" if lang != "fa" else "fa"])
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


def _roll_next_boss_state(boss_name: str, lang: str = "fa") -> tuple[str, str, int]:
    roll = random.random()
    if roll < 0.38:
        msg = (
            f"⚠️ «{boss_name}» خیز برداشته و می‌خواهد حمله مرگبار بزند! ۵ ثانیه فرصت داری دفاع یا جاخالی بدهی!"
            if lang == "fa" else
            f"⚠️ '{boss_name}' is charging a deadly attack! You have 5 seconds to Shield or Dodge!"
        )
        return "charging", msg, 5
    elif roll < 0.65:
        msg = (
            f"🛡️ «{boss_name}» در حالت دفاع مطلق قرار گرفت! (باید گاردش را بشکنی)"
            if lang == "fa" else
            f"🛡️ '{boss_name}' entered Absolute Defense! (Use Guard Break)"
        )
        return "abs_defense", msg, 0
    elif roll < 0.85:
        msg = (
            f"💨 «{boss_name}» گارد فرز گرفت و آماده جاخالی دادن به ضربات سنگین است!"
            if lang == "fa" else
            f"💨 '{boss_name}' is agile and ready to dodge heavy strikes!"
        )
        return "evasive", msg, 0
    else:
        msg = (
            f"👹 «{boss_name}» در حالت رجزخوانی و آماده نبرد است!"
            if lang == "fa" else
            f"👹 '{boss_name}' is roaring and ready to clash!"
        )
        return "normal", msg, 0


async def _finalize_tower_battle(uid: int, p: dict, boss: dict, bt: dict, won: bool, lang: str) -> dict:
    now = time.time()
    active_tower_battles.pop(uid, None)
    new_humanity = max(0, p["humanity"] - random.randint(12, 20))
    sleep_until = (now + 2 * 86400) if new_humanity == 0 else 0

    if won:
        final_hp = max(1, bt["p_hp"])
        inv = p["inventory"]
        if boss.get("drop_item"):
            inv.append({"name": boss["drop_item"], "price": boss.get("drop_price", 50)})

        await db.pool.execute(
            """UPDATE dt_players
               SET hp=$1, humanity=$2, sleep_until=$3,
                   coins=coins+$4, xp=xp+$5, current_floor=current_floor+1, inventory=$6
               WHERE user_id=$7""",
            final_hp, new_humanity, sleep_until,
            boss["reward_coins"], boss["reward_xp"], json.dumps(inv), uid
        )
        dmg_taken = max(0, p["hp"] - final_hp)
        msg = _dt_msg(
            lang, "floor_won",
            floor=boss["floor_num"], boss=boss["boss_name"],
            coins=boss["reward_coins"], xp=boss["reward_xp"],
            drop=boss.get("drop_item") or "—", dmg=dmg_taken, hum=new_humanity
        )
        if sleep_until > 0:
            msg += _dt_msg(lang, "sleep_triggered")
        st = await get_or_create_player(uid)
        st["active_battle"] = None
        return {"ok": True, "battle_over": True, "won": True, "msg": msg, "state": st}
    else:
        await db.pool.execute(
            "UPDATE dt_players SET hp=5, humanity=$1, sleep_until=$2 WHERE user_id=$3",
            new_humanity, sleep_until, uid
        )
        st = await get_or_create_player(uid)
        st["active_battle"] = None
        return {
            "ok": False,
            "battle_over": True,
            "won": False,
            "error": _dt_msg(lang, "floor_lost", boss=boss["boss_name"]),
            "state": st,
        }


async def handle_tower_api_action(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    name = payload.get("name") or "Player"
    lang = payload.get("lang") or "fa"
    action = payload.get("action") or "state"
    now = time.time()

    full_state = await get_or_create_player(uid)
    full_state["active_battle"] = active_tower_battles.get(uid)
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
        st = await get_or_create_player(uid)
        st["active_battle"] = active_tower_battles.get(uid)
        return {"ok": True, "msg": _dt_msg(lang, "gender_saved"), "state": st}

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
                st = await get_or_create_player(uid)
                st["active_battle"] = active_tower_battles.get(uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": st}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_w.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_weapons=$2, equipped_weapon=$3 WHERE user_id=$4",
                price, json.dumps(owned_w), item_id, uid
            )
            st = await get_or_create_player(uid)
            st["active_battle"] = active_tower_battles.get(uid)
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": st}
        else:
            if item_id in owned_a:
                await db.pool.execute("UPDATE dt_players SET equipped_armor=$1 WHERE user_id=$2", item_id, uid)
                st = await get_or_create_player(uid)
                st["active_battle"] = active_tower_battles.get(uid)
                return {"ok": True, "msg": _dt_msg(lang, "equipped", name=item_row["name"]), "state": st}
            if p["coins"] < price:
                return {"ok": False, "error": _dt_msg(lang, "not_enough_coins", price=price), "state": full_state}
            owned_a.append(item_id)
            await db.pool.execute(
                "UPDATE dt_players SET coins=coins-$1, owned_armors=$2, equipped_armor=$3 WHERE user_id=$4",
                price, json.dumps(owned_a), item_id, uid
            )
            st = await get_or_create_player(uid)
            st["active_battle"] = active_tower_battles.get(uid)
            return {"ok": True, "msg": _dt_msg(lang, "bought_equipped", name=item_row["name"]), "state": st}

    if action in ("battle_floor", "battle_start"):
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

        scaled_boss_hp = max(180, int(boss["hp"] * 2.2))
        b_state, b_prompt, b_window = _roll_next_boss_state(boss["boss_name"], lang)

        battle_session = {
            "floor_num": boss["floor_num"],
            "boss_name": boss["boss_name"],
            "boss_photo": boss.get("photo") or "",
            "boss_hp": scaled_boss_hp,
            "boss_max_hp": scaled_boss_hp,
            "boss_atk": boss["atk"],
            "boss_def": boss["def"],
            "p_hp": p["hp"],
            "p_max_hp": p["max_hp"],
            "p_rage": 25,
            "turn": 1,
            "boss_state": b_state,
            "state_prompt": b_prompt,
            "deadline_sec": b_window,
            "state_ts": now,
            "logs": [
                f"⚔️ نبرد با «{boss['boss_name']}» در طبقه {boss['floor_num']} آغاز شد!" if lang == "fa"
                else f"⚔️ Battle against '{boss['boss_name']}' (Floor {boss['floor_num']}) started!"
            ],
        }
        active_tower_battles[uid] = battle_session
        full_state["active_battle"] = battle_session
        return {"ok": True, "state": full_state}

    if action == "battle_move":
        bt = active_tower_battles.get(uid)
        boss = full_state["current_boss"]
        if not bt or not boss:
            return {"ok": False, "error": "نبرد فعالی وجود ندارد!", "state": full_state}

        move = str(payload.get("move") or "quick")
        b_name = bt["boss_name"]
        b_state = bt["boss_state"]
        base_atk = max(10, p["atk"] - int(bt["boss_def"] * 0.35))
        base_boss_dmg = max(8, bt["boss_atk"] - int(p["def"] * 0.45))
        log_line = ""

        timed_out = (move == "timeout") or (b_state == "charging" and (now - bt["state_ts"]) > 6.2 and move not in ("shield", "dodge"))

        if timed_out:
            heavy_hit = int(base_boss_dmg * 1.85) + random.randint(4, 12)
            bt["p_hp"] = max(0, bt["p_hp"] - heavy_hit)
            log_line = (
                f"💥 ۵ ثانیه تمام شد و دفاع نکردی! «{b_name}» ضربه مرگبار زد و {heavy_hit} جان کم کرد!"
                if lang == "fa" else
                f"💥 5s expired! '{b_name}' landed a crushing blow for {heavy_hit} DMG!"
            )
            next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)

        elif b_state == "charging":
            if move == "shield":
                reduced = max(2, int(base_boss_dmg * 0.2))
                counter = int(base_atk * 0.75)
                bt["p_hp"] = max(0, bt["p_hp"] - reduced)
                bt["boss_hp"] = max(0, bt["boss_hp"] - counter)
                bt["p_rage"] = min(100, bt["p_rage"] + 25)
                log_line = (
                    f"🛡️ به موقع سپر گرفتی! ضربه «{b_name}» دفع شد (فقط {reduced} آسیب) و {counter} ضدحمله زدی! غول گیج شد!"
                    if lang == "fa" else
                    f"🛡️ Timely Shield! Blocked attack ({reduced} DMG) and countered for {counter}! Boss is Stunned!"
                )
                next_st = "stunned"
                next_pr = f"😵 «{b_name}» گیج و بی‌دفاع شده! با ضربه سنگین یا جادوی خون حمله کن!" if lang == "fa" else f"😵 '{b_name}' is Stunned! Use Heavy Strike!"
                next_w = 0
            elif move == "dodge":
                dodge_chance = min(0.88, 0.65 + (p["spd"] * 0.005))
                if random.random() < dodge_chance:
                    bt["p_rage"] = min(100, bt["p_rage"] + 30)
                    log_line = (
                        f"💨 با سرعت بالا از حمله مرگبار «{b_name}» جاخالی دادی و هیچ آسیبی ندیدی! (+30 خشم)"
                        if lang == "fa" else
                        f"💨 Dodged '{b_name}'s deadly attack completely! (+30 Rage)"
                    )
                    next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
                else:
                    hit = int(base_boss_dmg * 1.1)
                    bt["p_hp"] = max(0, bt["p_hp"] - hit)
                    log_line = f"⚠️ جاخالی کامل نبود و {hit} آسیب دیدی!" if lang == "fa" else f"⚠️ Partial dodge! Took {hit} DMG!"
                    next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
            else:
                heavy_hit = int(base_boss_dmg * 1.7)
                dmg_done = int(base_atk * 0.6)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg_done)
                bt["p_hp"] = max(0, bt["p_hp"] - heavy_hit)
                log_line = (
                    f"❌ به جای دفاع حمله زدی! {dmg_done} آسیب زدی ولی ضربه سنگین «{b_name}» {heavy_hit} جان از تو کم کرد!"
                    if lang == "fa" else
                    f"❌ Attacked instead of defending! Dealt {dmg_done}, but took {heavy_hit} heavy DMG!"
                )
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)

        elif b_state == "abs_defense":
            if move == "break":
                dmg = int(base_atk * 1.35)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_rage"] = min(100, bt["p_rage"] + 25)
                log_line = (
                    f"🔨 سپر دفاع مطلق «{b_name}» را متلاشی کردی! {dmg} آسیب وارد شد و غول گیج شد!"
                    if lang == "fa" else
                    f"🔨 Shattered Absolute Defense! Dealt {dmg} DMG and stunned the boss!"
                )
                next_st = "stunned"
                next_pr = f"😵 گارد «{b_name}» شکسته و گیج است! ضربه سنگین بزن!" if lang == "fa" else f"😵 Guard broken! Boss is Stunned!"
                next_w = 0
            elif move == "blood" and bt["p_rage"] >= 50:
                bt["p_rage"] -= 50
                dmg = int(base_atk * 1.5)
                heal = int(p["max_hp"] * 0.22)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_hp"] = min(bt["p_max_hp"], bt["p_hp"] + heal)
                log_line = f"🩸 جادوی خون از دفاع مطلق رد شد! {dmg} آسیب زدی و +{heal} جان گرفتی!"
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
            else:
                recoil = max(6, int(base_boss_dmg * 0.85))
                bt["p_hp"] = max(0, bt["p_hp"] - recoil)
                log_line = (
                    f"🛡️ «{b_name}» در حالت دفاع مطلق بود! ضربه‌ات برگشت خورد و {recoil} آسیب دیدی! (از شکستن گارد استفاده کن)"
                    if lang == "fa" else
                    f"🛡️ '{b_name}' is in Absolute Defense! Attack reflected for {recoil} DMG!"
                )
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)

        elif b_state == "evasive":
            if move == "heavy":
                counter = int(base_boss_dmg * 0.9)
                bt["p_hp"] = max(0, bt["p_hp"] - counter)
                log_line = (
                    f"💨 «{b_name}» از ضربه سنگین تو جاخالی داد و {counter} ضدحمله زد! (از حمله سریع استفاده کن)"
                    if lang == "fa" else
                    f"💨 '{b_name}' dodged your Heavy Strike and countered for {counter} DMG!"
                )
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
            elif move == "quick":
                dmg = int(base_atk * 1.25)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_rage"] = min(100, bt["p_rage"] + 25)
                log_line = (
                    f"⚡ حمله سریع تو قبل از جاخالی به «{b_name}» نشست و {dmg} آسیب زد!"
                    if lang == "fa" else
                    f"⚡ Quick Strike caught '{b_name}' for {dmg} DMG!"
                )
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
            elif move == "blood" and bt["p_rage"] >= 50:
                bt["p_rage"] -= 50
                dmg = int(base_atk * 1.6)
                heal = int(p["max_hp"] * 0.25)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_hp"] = min(bt["p_max_hp"], bt["p_hp"] + heal)
                log_line = f"🩸 جادوی خون! {dmg} آسیب زدی و +{heal} جان بازیابی شد!"
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)
            else:
                dmg = int(base_atk * 0.7)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                log_line = f"⚔️ {dmg} آسیب به «{b_name}» وارد شد."
                next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)

        else:
            mult = 1.65 if b_state == "stunned" else 1.0
            boss_retaliation = 0 if b_state == "stunned" else int(base_boss_dmg * random.uniform(0.65, 1.0))

            if move == "heavy":
                if b_state != "stunned" and random.random() < 0.22:
                    bt["p_hp"] = max(0, bt["p_hp"] - boss_retaliation)
                    log_line = f"💨 «{b_name}» در آخرین لحظه جاخالی داد و {boss_retaliation} آسیب زد!"
                else:
                    dmg = int(base_atk * 1.55 * mult)
                    bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                    bt["p_hp"] = max(0, bt["p_hp"] - boss_retaliation)
                    bt["p_rage"] = min(100, bt["p_rage"] + 20)
                    log_line = f"💥 ضربه سنگین! {dmg} خسارت به «{b_name}» زدی" + (f" و {boss_retaliation} آسیب دیدی." if boss_retaliation else "!")
            elif move == "quick":
                dmg = int(base_atk * 1.0 * mult)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_hp"] = max(0, bt["p_hp"] - int(boss_retaliation * 0.7))
                bt["p_rage"] = min(100, bt["p_rage"] + 25)
                log_line = f"⚡ حمله سریع! {dmg} آسیب به «{b_name}» وارد شد (+25 خشم)."
            elif move == "blood":
                if bt["p_rage"] < 50:
                    return {"ok": False, "error": "خشم (Rage) کافی نداری! حداقل ۵۰٪ خشم لازم است.", "state": full_state}
                bt["p_rage"] -= 50
                dmg = int(base_atk * 1.8 * mult)
                heal = int(p["max_hp"] * 0.28)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_hp"] = min(bt["p_max_hp"], bt["p_hp"] + heal - int(boss_retaliation * 0.5))
                log_line = f"🩸 جادوی خونین! {dmg} خسارت مرگبار زدی و +{heal} جان خودت را شفا دادی!"
            elif move == "break":
                dmg = int(base_atk * 0.8 * mult)
                bt["boss_hp"] = max(0, bt["boss_hp"] - dmg)
                bt["p_hp"] = max(0, bt["p_hp"] - boss_retaliation)
                log_line = f"🔨 ضربه گاردشکن ({dmg} آسیب)."
            else:
                bt["p_rage"] = min(100, bt["p_rage"] + 15)
                log_line = f"🛡️ حالت تدافعی گرفتی (+15 خشم)."

            next_st, next_pr, next_w = _roll_next_boss_state(b_name, lang)

        bt["turn"] += 1
        bt["logs"].insert(0, log_line)
        bt["logs"] = bt["logs"][:6]

        if bt["boss_hp"] <= 0:
            return await _finalize_tower_battle(uid, p, boss, bt, won=True, lang=lang)
        if bt["p_hp"] <= 0:
            return await _finalize_tower_battle(uid, p, boss, bt, won=False, lang=lang)

        bt["boss_state"] = next_st
        bt["state_prompt"] = next_pr
        bt["deadline_sec"] = next_w
        bt["state_ts"] = time.time()
        full_state["active_battle"] = bt
        return {"ok": True, "state": full_state}

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
        st = await get_or_create_player(uid)
        return {"ok": True, "msg": _dt_msg(lang, "hospital_entered", sec=wait_seconds), "state": st}

    if action == "sell_loot":
        inv = p["inventory"]
        if not inv:
            return {"ok": False, "error": _dt_msg(lang, "empty_loot"), "state": full_state}
        total_val = sum(int(x.get("price", 50)) for x in inv)
        await db.pool.execute(
            "UPDATE dt_players SET coins=coins+$1, inventory='[]' WHERE user_id=$2", total_val, uid
        )
        return {"ok": True, "msg": _dt_msg(lang, "loot_sold", val=total_val), "state": await get_or_create_player(uid)}

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
                                f"از دکمه زیر وارد مینی‌اپ پنل مدیریت شوید و در تب «ووچرها» با یادداشت تایید یا رد کنید:"
                            ),
                            reply_markup=kb([
                                [success("👑 باز کردن مینی‌اپ فرماندهی", web_app_url=f"{MINI_APP_URL}/?game=tower_admin&uid={oid}")]
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


async def handle_tower_admin_api(payload: dict) -> dict:
    uid = int(payload.get("uid") or 0)
    if uid not in OWNER_IDS:
        return {"ok": False, "error": "⛔ دسترسی غیرمجاز! این پنل فقط مخصوص مالک ربات است."}

    await ensure_tower_tables()
    action = payload.get("action") or "state"
    msg_out = ""

    # ─── ۱. مدیریت کلی ربات (کانال‌های قفل، همگانی، گروه‌ها، بن سراسری، ادمین‌ها) ───
    if action == "bot_add_channel":
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
            msg_out = f"✅ کانال «{title}» به قفل عضویت اجباری اضافه شد."

    elif action == "bot_del_channel":
        chat_id = str(payload.get("chat_id") or "").strip()
        try:
            await db.remove_channel(chat_id)
        except Exception:
            await db.pool.execute("DELETE FROM forced_channels WHERE chat_id=$1", chat_id)
        msg_out = "🗑️ کانال از لیست عضویت اجباری حذف شد."

    elif action == "bot_global_ban":
        target_id = int(payload.get("target_id") or 0)
        ban_state = bool(payload.get("ban"))
        if target_id:
            try:
                await db.upsert_user(target_id, "", "")
                await db.ban_user(target_id, ban_state)
            except Exception:
                await db.pool.execute("UPDATE users SET is_banned=$1 WHERE user_id=$2", ban_state, target_id)
            msg_out = f"✅ وضعیت کاربر {target_id} در کل ربات به «{'مسدود' if ban_state else 'آزاد'}» تغییر کرد."

    elif action == "bot_set_admin":
        target_id = int(payload.get("target_id") or 0)
        adm_state = bool(payload.get("is_admin"))
        if target_id:
            try:
                await db.upsert_user(target_id, "", "")
                await db.set_admin(target_id, adm_state)
            except Exception:
                await db.pool.execute("UPDATE users SET is_admin=$1 WHERE user_id=$2", adm_state, target_id)
            msg_out = f"👑 وضعیت ادمین بودن {target_id} به «{'فعال' if adm_state else 'غیرفعال'}» تغییر یافت."

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
            try:
                await db.pool.execute("DELETE FROM groups WHERE chat_id=$1", chat_id)
            except Exception:
                pass
            msg_out = f"🚪 ربات از گروه {chat_id} خارج شد."

    elif action == "bot_group_link":
        chat_id = int(payload.get("chat_id") or 0)
        bot_token = os.environ.get("BOT_TOKEN", "")
        invite_link = ""
        if chat_id and bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                link_obj = await temp_bot.create_chat_invite_link(chat_id)
                invite_link = link_obj.invite_link
            except Exception as e:
                return {"ok": False, "error": f"ربات در این گروه دسترسی ساخت لینک ندارد: {e}", "admin_data": await _collect_admin_state()}
            finally:
                await temp_bot.session.close()
        return {"ok": True, "msg": f"🔗 لینک ورود به گروه:\n{invite_link}", "invite_link": invite_link, "admin_data": await _collect_admin_state()}

    elif action == "bot_trigger_pm_broadcast":
        bot_token = os.environ.get("BOT_TOKEN", "")
        if bot_token:
            temp_bot = Bot(token=bot_token)
            try:
                await temp_bot.send_message(
                    chat_id=uid,
                    text=(
                        "✨ <b>ارسال همگانی با پشتیبانی ۱۰۰٪ از ایموجی پریمیوم</b>\n\n"
                        "مقصد ارسال همگانی را انتخاب کنید و سپس پیام حاوی ایموجی پریمیوم خود را در همین پیوی بفرستید:"
                    ),
                    reply_markup=kb([
                        [primary("👤 ارسال به تمام کاربران (پیوی)", "adm:bc_users")],
                        [primary("👥 ارسال به تمام گروه‌ها", "adm:bc_groups")],
                    ]),
                    parse_mode=ParseMode.HTML,
                )
            finally:
                await temp_bot.session.close()
        return {"ok": True, "msg": "📩 پیام شروع ارسال همگانی به پیوی شما ارسال شد! مینی‌اپ را ببندید و پیام پریمیوم خود را در پیوی بفرستید.", "admin_data": await _collect_admin_state()}
        
    elif action == "bot_broadcast":
        target_type = str(payload.get("target_type") or "users")
        text = str(payload.get("text") or "").strip()
        btn_text = str(payload.get("btn_text") or "").strip()
        btn_url = str(payload.get("btn_url") or "").strip()
        if not text:
            return {"ok": False, "error": "متن پیام همگانی نمی‌تواند خالی باشد!", "admin_data": await _collect_admin_state()}

        target_ids = []
        try:
            if target_type == "groups":
                rows = await db.pool.fetch("SELECT chat_id AS id FROM groups")
            else:
                rows = await db.pool.fetch("SELECT user_id AS id FROM users")
            target_ids = [r["id"] for r in rows]
        except Exception:
            pass

        bot_token = os.environ.get("BOT_TOKEN", "")
        sent_ok, sent_fail = 0, 0
        if bot_token and target_ids:
            temp_bot = Bot(token=bot_token)
            markup = kb([[primary(btn_text, url=btn_url)]]) if (btn_text and btn_url) else None
            try:
                for tid in target_ids:
                    try:
                        await temp_bot.send_message(tid, text, reply_markup=markup, parse_mode=ParseMode.HTML)
                        sent_ok += 1
                    except Exception:
                        sent_fail += 1
            finally:
                await temp_bot.session.close()
        msg_out = f"📢 ارسال همگانی به پایان رسید!\n✅ موفق: {sent_ok} | ❌ ناموفق: {sent_fail}"

    
    # ─── ۲. مدیریت برج شیاطین (طبقات، تجهیزات، کاراکتر، ووچرها، پاپ‌آپ، کد هدیه) ───
    elif action == "toggle_dev":
        cur = await get_dt_config("dev_mode", "0")
        new_val = "0" if cur == "1" else "1"
        await set_dt_config("dev_mode", new_val)
        msg_out = "🛠️ وضعیت بازی به «در حال توسعه» تغییر کرد." if new_val == "1" else "🟢 بازی برای همه کاربران باز شد."

    elif action == "save_gender_imgs":
        male_img = payload.get("male_img")
        female_img = payload.get("female_img")
        if male_img:
            await set_dt_config("male_img", male_img)
        if female_img:
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
        looked = st["player"]
        try:
            u_main = await db.get_user(t_uid)
            looked["global_banned"] = bool(u_main["is_banned"]) if u_main else False
            looked["is_bot_admin"] = bool(u_main["is_admin"]) if u_main else False
            looked["first_name"] = u_main["first_name"] if u_main else ""
            looked["username"] = u_main["username"] if u_main else ""
        except Exception:
            looked["global_banned"] = False
            looked["is_bot_admin"] = False
            looked["first_name"] = ""
            looked["username"] = ""
        return {"ok": True, "looked_up": looked, "admin_data": await _collect_admin_state()}

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
            "msg": f"وضعیت کاربر {t_uid} در برج به «{'مسدود' if new_b else 'آزاد'}» تغییر یافت.",
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
    """جمع‌آوری ایمن تمام اطلاعات پنل مدیریت + لیست کامل کاربران با تمام مشخصات"""
    await ensure_tower_tables()
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

    users_cnt = 0
    groups_cnt = 0
    stars_cnt = 0
    try:
        users_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
    except Exception:
        pass
    try:
        groups_cnt = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
    except Exception:
        pass
    try:
        stars_cnt = await db.pool.fetchval("SELECT COALESCE(SUM(amount), 0) FROM donations") or 0
    except Exception:
        pass

    forced_channels = []
    try:
        ch_rows = await db.pool.fetch("SELECT chat_id, title, username FROM forced_channels")
        forced_channels = [dict(r) for r in ch_rows]
    except Exception:
        pass

    groups_list = []
    try:
        g_rows = await db.pool.fetch("SELECT chat_id, title FROM groups LIMIT 50")
        groups_list = [dict(r) for r in g_rows]
    except Exception:
        pass

    # دریافت لیست کامل کاربران با مشخصات ربات و مشخصات برج شیاطین
    users_list = []
    try:
        u_rows = await db.pool.fetch("""
            SELECT
                u.user_id,
                u.first_name,
                u.username,
                u.language,
                u.is_banned AS global_banned,
                u.is_admin AS is_bot_admin,
                COALESCE(dp.level, 1) AS dt_level,
                COALESCE(dp.xp, 0) AS dt_xp,
                COALESCE(dp.coins, 0) AS dt_coins,
                COALESCE(dp.bank_coins, 0) AS dt_bank,
                COALESCE(dp.current_floor, 1) AS dt_floor,
                COALESCE(dp.gender, '') AS dt_gender,
                COALESCE(dp.is_banned, FALSE) AS dt_banned
            FROM users u
            LEFT JOIN dt_players dp ON u.user_id = dp.user_id
            ORDER BY u.user_id DESC
            LIMIT 200
        """)
        users_list = [dict(r) for r in u_rows]
    except Exception:
        pass

    return {
        "players_count": players_cnt,
        "bot_stats": {
            "users": users_cnt,
            "groups": groups_cnt,
            "stars": stars_cnt,
        },
        "forced_channels": forced_channels,
        "groups_list": groups_list,
        "users_list": users_list,
        "dev_mode": dev_mode,
        "male_img": male_img,
        "female_img": female_img,
        "popup": popup_data,
        "floors": floors,
        "items": items,
        "gifts": gifts,
        "vouchers": vouchers,
    }


@router.message(Command("tower_panel"))
@router.message(F.text.in_({"پنل برج", "پنل برج شیاطین", "/tower"}))
async def cmd_tower_panel(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    uid = msg.from_user.id
    admin_url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    await msg.answer(
        f"👑 <b>مینی‌اپ اختصاصی فرماندهی کل ربات و برج شیاطین</b>\n\n"
        f"این پنل کاملاً از کاربران عادی مخفی است و فقط برای مالک باز می‌شود:",
        reply_markup=kb([
            [success("👑 ورود به مینی‌اپ فرماندهی کل ربات", web_app_url=admin_url)]
        ]),
        parse_mode=ParseMode.HTML,
    )
