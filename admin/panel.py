# -*- coding: utf-8 -*-
"""پنل ادمین استایل‌دار — نسخه بازی"""

from __future__ import annotations
import asyncio
import math
from datetime import datetime, timezone
from typing import Union

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from emojis import E
from langs import t, get_user_lang
from utils.premium import (
    btn, primary, success, danger, back_btn, cancel_btn, kb,
)
from database import db

router = Router(name="admin_panel")

OWNER_IDS = {7662192190, 6041119040}
USERS_PAGE = 8
GROUPS_PAGE = 6


class A(StatesGroup):
    search_user = State()
    broadcast_users = State()
    broadcast_groups = State()
    add_admin = State()
    add_channel = State()
    set_hangman_lives = State()


# ═══════════════════════════════════════════════
# کمکی‌ها
# ═══════════════════════════════════════════════

async def _is_admin(uid: int) -> bool:
    if uid in OWNER_IDS:
        return True
    return await db.pool.fetchval(
        "SELECT 1 FROM admins WHERE user_id=$1", uid
    ) is not None


async def _is_owner(uid: int) -> bool:
    return uid in OWNER_IDS


def _fa_digits(s: str) -> str:
    return s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


GAME_NAMES = {
    "hokm": "حکم", "dooz": "دوز ۲ نفره", "doz4p": "دوز ۴ نفره",
    "connect4": "چهار در ردیف", "rps": "سنگ کاغذ قیچی",
    "memory": "بازی حافظه", "2048": "2048", "samegame": "جفت‌ها",
    "spuzzle": "پازل کشویی", "hangman": "حدس کلمه",
    "typing": "تایپ سرعتی", "number_guess": "حدس عدد",
    "gardone": "گردونه شانس",
}


# ═══════════════════════════════════════════════
# منوی اصلی
# ═══════════════════════════════════════════════

def _main_kb(lang: str = "fa") -> "InlineKeyboardMarkup":
    return kb([
        [success(f"{E.CHART} {t('admin_stats', lang)}", "adm:stats")],
        [primary(f"{E.SEARCH} {t('admin_users', lang)}", "adm:users"),
         primary(f"{E.PARTY} مدیریت گروه‌ها", "adm:groups")],
        [primary(f"{E.GAME} مدیریت بازی‌ها", "adm:games"),
         primary(f"{E.LOCK} {t('admin_locks', lang)}", "adm:locks")],
        [primary(f"{E.MEGA} {t('admin_bcast', lang)}", "adm:bcast"),
         primary(f"{E.CAL} {t('admin_settings', lang)}", "adm:settings")],
        [danger(f"{E.CROWN} {t('admin_admins', lang)}", "adm:admins")],
        [primary(f"{E.BOX} {t('admin_backup', lang)}", "adm:backup")],
        [back_btn(lang, "menu")],
    ])


def _main_text(lang: str) -> str:
    return (
        f"{E.CROWN}{E.PC} <b>{t('admin_panel', lang)}</b>\n\n"
        f"{E.GAME} مدیریت کامل ربات بازی\n"
        f"{E.SPARK} یک بخش انتخاب کن:"
    )


@router.message(Command("admin"))
async def cmd_admin(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await msg.answer(f"{E.BLOCK} {t('admin_only', lang)}", parse_mode=ParseMode.HTML)
        return
    await state.clear()
    await msg.answer(_main_text(lang), reply_markup=_main_kb(lang), parse_mode=ParseMode.HTML)


@router.message(F.text.in_({"ادمین", "پنل ادمین", "مدیر"}))
async def msg_admin(msg: Message, state: FSMContext):
    await cmd_admin(msg, state)


@router.callback_query(F.data == "adm:panel")
async def cb_panel(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(_main_text(lang), reply_markup=_main_kb(lang), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:noop")
async def cb_noop(cb: CallbackQuery):
    await cb.answer()


# ═══════════════════════════════════════════════
# آمار
# ═══════════════════════════════════════════════

async def _gather_stats() -> dict:
    try:
        users = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
        banned = await db.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE is_banned=TRUE"
        ) or 0
        groups = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
        total_wins = await db.pool.fetchval(
            "SELECT COALESCE(SUM(wins),0) FROM game_wins"
        ) or 0
        from games.state import active_games
        active_now = sum(
            len(g) for gtype in active_games for g in active_games[gtype].values()
        )
        top = await db.pool.fetch(
            """SELECT game_type, SUM(wins) as total FROM game_wins
               GROUP BY game_type ORDER BY total DESC LIMIT 5"""
        )
    except Exception:
        users = banned = groups = total_wins = active_now = 0
        top = []
    return {
        "users": users, "banned": banned, "active": users - banned,
        "groups": groups, "wins": total_wins, "now": active_now, "top": top,
    }


@router.callback_query(F.data == "adm:stats")
async def cb_stats(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()

    s = await _gather_stats()
    top_txt = ""
    for g in s["top"]:
        name = GAME_NAMES.get(g["game_type"], g["game_type"])
        top_txt += f"  • {name}: <b>{g['total']:,}</b>\n"
    if not top_txt:
        top_txt = "  —\n"

    text = (
        f"{E.CHART}{E.ROCKET} <b>آمار ربات</b>\n\n"
        f"{E.DISGUISE} کاربران کل: <b>{s['users']:,}</b>\n"
        f"{E.OK2} فعال: <b>{s['active']:,}</b>\n"
        f"{E.BLOCK} مسدود: <b>{s['banned']:,}</b>\n"
        f"{E.PARTY} گروه‌ها: <b>{s['groups']:,}</b>\n"
        f"{E.GAME} بازی فعال الان: <b>{s['now']:,}</b>\n"
        f"{E.TROPHY} مجموع بردها: <b>{s['wins']:,}</b>\n\n"
        f"{E.SPARK} <b>پرطرفدارترین بازی‌ها:</b>\n{top_txt}"
    )
    await cb.message.edit_text(
        text,
        reply_markup=kb([
            [primary(f"{E.REFRESH} بروزرسانی", "adm:stats")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("stats"))
@router.message(F.text.in_({"آمار", "امار"}))
async def cmd_stats(msg: Message):
    uid = msg.from_user.id
    if not await _is_admin(uid):
        return
    s = await _gather_stats()
    await msg.answer(
        f"{E.CHART} کاربران: <b>{s['users']:,}</b>\n"
        f"{E.PARTY} گروه‌ها: <b>{s['groups']:,}</b>\n"
        f"{E.GAME} بازی فعال: <b>{s['now']:,}</b>\n"
        f"{E.TROPHY} مجموع بردها: <b>{s['wins']:,}</b>",
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════
# کاربران
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:users")
async def cb_users(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(
        f"{E.SEARCH} <b>{t('admin_users', lang)}</b>\n\n{E.INFO} یک گزینه:",
        reply_markup=kb([
            [primary(f"{E.DISGUISE} لیست کاربران", "adm:ulist:0")],
            [success(f"{E.SEARCH} جستجو با آیدی", "adm:usearch")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:ulist:"))
async def cb_ulist(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 0

    try:
        users = await db.pool.fetch(
            """SELECT user_id, first_name, is_banned FROM users
               ORDER BY start_time DESC LIMIT $1 OFFSET $2""",
            USERS_PAGE, page * USERS_PAGE,
        )
        total = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
    except Exception:
        users, total = [], 0

    pages = max(1, math.ceil(total / USERS_PAGE))
    rows = []
    for u in users:
        icon = E.BLOCK if u["is_banned"] else E.OK2
        name = u["first_name"] or f"user_{u['user_id']}"
        rows.append([primary(f"{icon} {name}", f"adm:up:{u['user_id']}")])

    nav = []
    if page > 0:
        nav.append(primary("◀️", f"adm:ulist:{page-1}"))
    nav.append(primary(f"{page+1}/{pages}", "adm:noop"))
    if page < pages - 1:
        nav.append(primary("▶️", f"adm:ulist:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([back_btn(lang, "adm:users")])

    await cb.answer()
    await cb.message.edit_text(
        f"{E.DISGUISE} <b>کاربران</b> ({total:,})",
        reply_markup=kb(rows), parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:usearch")
async def cb_usearch(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.search_user)
    await cb.message.edit_text(
        f"{E.SEARCH} <b>جستجوی کاربر</b>\n\n{E.INFO} آیدی عددی:",
        reply_markup=kb([[cancel_btn(lang, "adm:users")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(A.search_user, F.text)
async def msg_search_user(msg: Message, state: FSMContext):
    try:
        target = int(_fa_digits(msg.text.strip()))
    except ValueError:
        await msg.answer(f"{E.WARN} آیدی نامعتبر.")
        return
    await state.clear()
    await _show_user(msg, target)


async def _show_user(event, target_uid: int):
    user = await db.pool.fetchrow(
        "SELECT user_id, first_name, username, is_banned, start_time FROM users WHERE user_id=$1",
        target_uid,
    )
    if not user:
        msg = f"{E.CROSS} کاربر یافت نشد."
        if isinstance(event, CallbackQuery):
            await event.answer(msg, show_alert=True)
        else:
            await event.answer(msg)
        return

    try:
        wins = await db.pool.fetch(
            "SELECT game_type, wins FROM game_wins WHERE user_id=$1 ORDER BY wins DESC",
            target_uid,
        )
    except Exception:
        wins = []
    total = sum(w["wins"] for w in wins)

    top_txt = ""
    for w in wins[:3]:
        name = GAME_NAMES.get(w["game_type"], w["game_type"])
        top_txt += f"    • {name}: {w['wins']}\n"
    top_txt = top_txt or "    —\n"

    status_icon = E.BLOCK if user["is_banned"] else E.OK2
    status_txt = "مسدود" if user["is_banned"] else "فعال"

    join_date = user["start_time"].strftime("%Y-%m-%d") if user["start_time"] else "—"

    text = (
        f"{E.CROWN} <b>پنل کاربر</b>\n\n"
        f"{E.DISGUISE} نام: <b>{user['first_name'] or '—'}</b>\n"
        f"{E.PIN} یوزرنیم: @{user['username'] or '—'}\n"
        f"{E.INFO} آیدی: <code>{target_uid}</code>\n"
        f"{status_icon} وضعیت: {status_txt}\n"
        f"{E.CAL} عضویت: {join_date}\n\n"
        f"{E.TROPHY} مجموع بردها: <b>{total}</b>\n"
        f"{E.CHART} <b>برترین بازی‌ها:</b>\n{top_txt}"
    )

    if user["is_banned"]:
        ban_btn = success(f"{E.OK2} رفع مسدودی", f"adm:unban:{target_uid}")
    else:
        ban_btn = danger(f"{E.BLOCK} مسدود کردن", f"adm:ban:{target_uid}")

    rows = [
        [ban_btn],
        [primary(f"{E.REFRESH} ریست آمار بازی‌ها", f"adm:ureset:{target_uid}")],
        [back_btn(get_user_lang(event.from_user.id), "adm:users")],
    ]

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:up:"))
async def cb_up(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await _show_user(cb, target)


@router.callback_query(F.data.startswith("adm:ban:"))
async def cb_ban(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await db.pool.execute("UPDATE users SET is_banned=TRUE WHERE user_id=$1", target)
    await db.log_admin(cb.from_user.id, "ban_user", target)
    await cb.answer("مسدود شد ✅", show_alert=True)
    await _show_user(cb, target)


@router.callback_query(F.data.startswith("adm:unban:"))
async def cb_unban(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await db.pool.execute("UPDATE users SET is_banned=FALSE WHERE user_id=$1", target)
    await db.log_admin(cb.from_user.id, "unban_user", target)
    await cb.answer("رفع مسدودی شد ✅", show_alert=True)
    await _show_user(cb, target)


@router.callback_query(F.data.startswith("adm:ureset:"))
async def cb_ureset(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    try:
        await db.pool.execute("DELETE FROM game_wins WHERE user_id=$1", target)
    except Exception:
        pass
    await cb.answer("آمار پاک شد ✅", show_alert=True)
    await _show_user(cb, target)


# ═══════════════════════════════════════════════
# گروه‌ها
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:groups")
async def cb_groups(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()
    await cb.message.edit_text(
        f"{E.PARTY} <b>مدیریت گروه‌ها</b>",
        reply_markup=kb([
            [primary(f"{E.EYES} لیست گروه‌ها", "adm:glist:0")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:glist:"))
async def cb_glist(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 0

    try:
        groups = await db.pool.fetch(
            """SELECT group_id, title, member_count FROM groups
               ORDER BY added_time DESC LIMIT $1 OFFSET $2""",
            GROUPS_PAGE, page * GROUPS_PAGE,
        )
        total = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
    except Exception:
        groups, total = [], 0

    pages = max(1, math.ceil(total / GROUPS_PAGE))
    rows = []
    for g in groups:
        title = g["title"] or f"گروه {g['group_id']}"
        rows.append([primary(f"{E.PARTY} {title}", f"adm:gp:{g['group_id']}")])

    nav = []
    if page > 0:
        nav.append(primary("◀️", f"adm:glist:{page-1}"))
    nav.append(primary(f"{page+1}/{pages}", "adm:noop"))
    if page < pages - 1:
        nav.append(primary("▶️", f"adm:glist:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([back_btn(lang, "adm:groups")])

    await cb.answer()
    await cb.message.edit_text(
        f"{E.PARTY} <b>گروه‌ها</b> ({total:,})",
        reply_markup=kb(rows), parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:gp:"))
async def cb_gp(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    try:
        gid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return

    g = await db.pool.fetchrow("SELECT * FROM groups WHERE group_id=$1", gid)
    if not g:
        await cb.answer("گروه یافت نشد", show_alert=True)
        return

    added = g["added_time"].strftime("%Y-%m-%d") if g["added_time"] else "—"

    await cb.answer()
    await cb.message.edit_text(
        f"{E.PARTY} <b>اطلاعات گروه</b>\n\n"
        f"{E.DISGUISE} نام: <b>{g['title'] or '—'}</b>\n"
        f"{E.INFO} آیدی: <code>{gid}</code>\n"
        f"{E.CROWN} اعضا: <b>{g['member_count'] or 0:,}</b>\n"
        f"{E.CAL} افزوده: {added}",
        reply_markup=kb([
            [danger(f"{E.TRASH} اخراج ربات", f"adm:gleave:{gid}")],
            [back_btn(lang, "adm:groups")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:gleave:"))
async def cb_gleave(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    try:
        gid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return

    try:
        await cb.bot.leave_chat(gid)
        await db.pool.execute("DELETE FROM groups WHERE group_id=$1", gid)
        await cb.answer("اخراج شد ✅", show_alert=True)
    except Exception as e:
        await cb.answer(f"خطا: {e}", show_alert=True)

    cb.data = "adm:glist:0"
    await cb_glist(cb)


# ═══════════════════════════════════════════════
# مدیریت بازی‌ها (روشن/خاموش)
# ═══════════════════════════════════════════════

ALL_GAMES = [
    ("hokm", "🃏 حکم"),
    ("dooz", "❌ دوز ۲ نفره"),
    ("doz4p", "🔴 دوز ۴ نفره"),
    ("connect4", "🔴 چهار در ردیف"),
    ("rps", "🪨 سنگ کاغذ قیچی"),
    ("memory", "🧠 حافظه"),
    ("2048", "🔢 2048"),
    ("samegame", "✨ جفت‌ها"),
    ("spuzzle", "🧩 پازل کشویی"),
    ("hangman", "🎯 حدس کلمه"),
    ("typing", "⌨️ تایپ سرعتی"),
    ("number_guess", "🔢 حدس عدد"),
    ("gardone", "🎡 گردونه شانس"),
]


@router.callback_query(F.data == "adm:games")
async def cb_games(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()

    try:
        rows = await db.pool.fetch("SELECT game_type, is_enabled FROM game_settings")
        state = {r["game_type"]: r["is_enabled"] for r in rows}
    except Exception:
        state = {}

    rows_kb = []
    for gtype, gname in ALL_GAMES:
        is_on = state.get(gtype, True)
        icon = E.OK2 if is_on else E.CROSS
        style = "success" if is_on else "danger"
        rows_kb.append([btn(f"{icon} {gname}", f"adm:gtog:{gtype}", style=style)])
    rows_kb.append([back_btn(lang, "adm:panel")])

    await cb.message.edit_text(
        f"{E.GAME} <b>مدیریت بازی‌ها</b>\n\n"
        f"{E.INFO} روی هر بازی کلیک کن تا روشن/خاموش شود.\n"
        f"{E.CHECK} سبز = فعال | {E.CROSS} قرمز = غیرفعال",
        reply_markup=kb(rows_kb),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:gtog:"))
async def cb_gtoggle(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    gtype = cb.data.split(":")[2]
    try:
        current = await db.pool.fetchval(
            "SELECT is_enabled FROM game_settings WHERE game_type=$1", gtype
        )
        new_state = False if current else True
        await db.pool.execute(
            """INSERT INTO game_settings (game_type, is_enabled) VALUES ($1, $2)
               ON CONFLICT (game_type) DO UPDATE
               SET is_enabled=$2, updated_at=NOW()""",
            gtype, new_state,
        )
        await db.log_admin(uid, "toggle_game", detail=f"{gtype}={new_state}")
        await cb.answer("✅ ذخیره شد")
    except Exception as e:
        await cb.answer(f"خطا: {e}", show_alert=True)

    cb.data = "adm:games"
    await cb_games(cb)


# ═══════════════════════════════════════════════
# اسپانسری (کانال اجباری)
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:locks")
async def cb_locks(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()
    await cb.message.edit_text(
        f"{E.LOCK} <b>{t('admin_locks', lang)}</b>",
        reply_markup=kb([
            [primary(f"{E.EYES} لیست کانال‌ها", "adm:chlst")],
            [success(f"{E.PLUS} افزودن کانال", "adm:chadd")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:chlst")
async def cb_chlist(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()

    try:
        chans = await db.pool.fetch("SELECT * FROM forced_channels")
    except Exception:
        chans = []

    rows = []
    for c in chans:
        title = c["title"] or c["chat_id"]
        rows.append([danger(f"{E.TRASH} {title}", f"adm:chdel:{c['id']}")])
    rows.append([back_btn(lang, "adm:locks")])

    text = f"{E.LOCK} <b>کانال‌های اجباری</b> ({len(chans)})\n\n"
    text += "برای حذف روی کانال بزن." if chans else "هیچ کانالی وجود ندارد."

    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:chadd")
async def cb_chadd(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.add_channel)
    await cb.message.edit_text(
        f"{E.PLUS} <b>افزودن کانال اجباری</b>\n\n"
        f"{E.INFO} یوزرنیم یا لینک کانال:\n"
        f"مثال: <code>@MyChannel</code>\n\n"
        f"{E.WARN} ربات باید ادمین کانال باشد.",
        reply_markup=kb([[cancel_btn(lang, "adm:locks")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(A.add_channel, F.text)
async def msg_chadd(msg: Message, state: FSMContext):
    text = msg.text.strip()
    try:
        if text.startswith("https://t.me/"):
            text = "@" + text.split("/")[-1]
        elif not text.startswith("@"):
            text = "@" + text

        chat = await msg.bot.get_chat(text)
        await db.pool.execute(
            """INSERT INTO forced_channels (chat_id, username, title)
               VALUES ($1, $2, $3)
               ON CONFLICT (chat_id) DO UPDATE SET title=$3, username=$2""",
            str(chat.id), chat.username or "", chat.title or "",
        )
        await state.clear()
        await msg.answer(f"{E.OK2} کانال <b>{chat.title}</b> اضافه شد.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.answer(f"{E.WARN} خطا: {e}", parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:chdel:"))
async def cb_chdel(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    try:
        cid = int(cb.data.split(":")[2])
        await db.pool.execute("DELETE FROM forced_channels WHERE id=$1", cid)
        await cb.answer("حذف شد ✅", show_alert=True)
    except Exception:
        await cb.answer("خطا", show_alert=True)
    cb.data = "adm:chlst"
    await cb_chlist(cb)


# ═══════════════════════════════════════════════
# ارسال همگانی
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:bcast")
async def cb_bcast(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()
    await cb.message.edit_text(
        f"{E.MEGA} <b>{t('admin_bcast', lang)}</b>\n\n"
        f"{E.INFO} مقصد را انتخاب کن:",
        reply_markup=kb([
            [success(f"{E.DISGUISE} کاربران", "adm:bcu")],
            [primary(f"{E.PARTY} گروه‌ها", "adm:bcg")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:bcu")
async def cb_bcu(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.broadcast_users)
    await cb.message.edit_text(
        f"{E.MEGA} <b>ارسال به کاربران</b>\n\n"
        f"{E.INFO} پیام خود را بفرست (متن/عکس/ویدیو/...):\n"
        f"{E.WARN} فقط کاربران غیرمسدود.",
        reply_markup=kb([[cancel_btn(lang, "adm:bcast")]]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:bcg")
async def cb_bcg(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.broadcast_groups)
    await cb.message.edit_text(
        f"{E.MEGA} <b>ارسال به گروه‌ها</b>\n\n"
        f"{E.INFO} پیام خود را بفرست:",
        reply_markup=kb([[cancel_btn(lang, "adm:bcast")]]),
        parse_mode=ParseMode.HTML,
    )


async def _do_broadcast(msg: Message, target_type: str):
    status = await msg.answer(f"{E.HOURGLASS} در حال ارسال...", parse_mode=ParseMode.HTML)
    try:
        if target_type == "users":
            rows = await db.pool.fetch("SELECT user_id FROM users WHERE is_banned=FALSE")
            key = "user_id"
        else:
            rows = await db.pool.fetch("SELECT group_id FROM groups")
            key = "group_id"
    except Exception:
        rows = []
        key = "user_id"

    sent = failed = 0
    for i, r in enumerate(rows):
        try:
            await msg.copy_to(r[key])
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            await asyncio.sleep(0.05)
        if i % 100 == 0 and i > 0:
            try:
                await status.edit_text(
                    f"{E.HOURGLASS} در حال ارسال...\n"
                    f"{E.OK2} موفق: {sent}\n{E.CROSS} ناموفق: {failed}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    await status.edit_text(
        f"{E.PARTY}{E.OK2} <b>ارسال کامل شد!</b>\n\n"
        f"{E.OK2} موفق: {sent:,}\n{E.CROSS} ناموفق: {failed:,}",
        parse_mode=ParseMode.HTML,
    )


@router.message(A.broadcast_users)
async def msg_bcast_users(msg: Message, state: FSMContext):
    await state.clear()
    await _do_broadcast(msg, "users")


@router.message(A.broadcast_groups)
async def msg_bcast_groups(msg: Message, state: FSMContext):
    await state.clear()
    await _do_broadcast(msg, "groups")


# ═══════════════════════════════════════════════
# تنظیمات
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:settings")
async def cb_settings(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await cb.answer()

    try:
        lives = await db.pool.fetchval(
            "SELECT config->>'initial_lives' FROM game_settings WHERE game_type='hangman'"
        ) or "10"
    except Exception:
        lives = "10"

    await cb.message.edit_text(
        f"{E.CAL} <b>{t('admin_settings', lang)}</b>\n\n"
        f"{E.HEART} جان اولیه در حدس کلمه: <b>{lives}</b>",
        reply_markup=kb([
            [primary(f"{E.HEART} تغییر جان حدس کلمه", "adm:set_lives")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:set_lives")
async def cb_set_lives(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.set_hangman_lives)
    await cb.message.edit_text(
        f"{E.HEART} <b>جان اولیه جدید (بین ۱ تا ۲۰):</b>",
        reply_markup=kb([[cancel_btn(lang, "adm:settings")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(A.set_hangman_lives, F.text)
async def msg_set_lives(msg: Message, state: FSMContext):
    try:
        lives = int(_fa_digits(msg.text.strip()))
        if not (1 <= lives <= 20):
            raise ValueError
    except ValueError:
        await msg.answer(f"{E.WARN} عدد بین ۱ تا ۲۰ بفرست.")
        return

    try:
        await db.pool.execute(
            """INSERT INTO game_settings (game_type, config) VALUES ('hangman', $1::jsonb)
               ON CONFLICT (game_type) DO UPDATE
               SET config = jsonb_set(
                   COALESCE(game_settings.config, '{}'::jsonb),
                   '{initial_lives}', to_jsonb($2::int)
               )""",
            f'{{"initial_lives": {lives}}}', lives,
        )
        await state.clear()
        await msg.answer(f"{E.OK2} جان اولیه = <b>{lives}</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.answer(f"{E.WARN} خطا: {e}")


# ═══════════════════════════════════════════════
# ادمین‌ها
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:admins")
async def cb_admins(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_owner(uid):
        await cb.answer("فقط مالک", show_alert=True)
        return
    await cb.answer()

    try:
        admins = await db.pool.fetch("SELECT * FROM admins ORDER BY created_at")
    except Exception:
        admins = []

    text = f"{E.CROWN} <b>مدیران</b>\n\n"
    text += f"{E.STAR} سوپرادمین‌ها:\n"
    for oid in OWNER_IDS:
        text += f"  • <code>{oid}</code>\n"
    text += f"\n{E.SHIELD} ادمین‌ها ({len(admins)}):\n"
    for a in admins:
        text += f"  • <code>{a['user_id']}</code>\n"

    rows = [[success(f"{E.PLUS} افزودن ادمین", "adm:aadd")]]
    for a in admins:
        rows.append([danger(f"{E.TRASH} حذف {a['user_id']}", f"adm:adel:{a['user_id']}")])
    rows.append([back_btn(lang, "adm:panel")])

    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:aadd")
async def cb_aadd(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_owner(uid):
        await cb.answer("فقط مالک", show_alert=True)
        return
    await state.clear()
    await cb.answer()
    await state.set_state(A.add_admin)
    await cb.message.edit_text(
        f"{E.PLUS} <b>آیدی ادمین جدید:</b>",
        reply_markup=kb([[cancel_btn(lang, "adm:admins")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(A.add_admin, F.text)
async def msg_add_admin(msg: Message, state: FSMContext):
    try:
        target = int(_fa_digits(msg.text.strip()))
    except ValueError:
        await msg.answer(f"{E.WARN} آیدی نامعتبر.")
        return

    try:
        await db.pool.execute(
            "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            target,
        )
        await state.clear()
        await msg.answer(
            f"{E.OK2} ادمین <code>{target}</code> اضافه شد.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await msg.answer(f"{E.WARN} خطا: {e}")


@router.callback_query(F.data.startswith("adm:adel:"))
async def cb_adel(cb: CallbackQuery):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    try:
        target = int(cb.data.split(":")[2])
        await db.pool.execute("DELETE FROM admins WHERE user_id=$1", target)
        await cb.answer("حذف شد ✅", show_alert=True)
    except Exception:
        await cb.answer("خطا", show_alert=True)
    cb.data = "adm:admins"
    await cb_admins(cb)


# ═══════════════════════════════════════════════
# بکاپ — دکمه‌های منو
# ═══════════════════════════════════════════════

@router.callback_query(F.data == "adm:backup")
async def cb_backup(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_owner(uid):
        await cb.answer("فقط مالک", show_alert=True)
        return
    await cb.answer()
    await cb.message.edit_text(
        f"{E.BOX} <b>{t('admin_backup', lang)}</b>\n\n"
        f"{E.INFO} عملیات:",
        reply_markup=kb([
            [success(f"{E.DOWN} بکاپ فوری", "adm:do_backup")],
            [primary(f"{E.REFRESH} بازسازی تامب‌ها", "adm:rebuild")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:do_backup")
async def cb_do_backup(cb: CallbackQuery):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    await cb.answer("شروع شد ✅")
    from admin.backup import create_and_send_backup
    await create_and_send_backup(cb.from_user.id, "manual")


@router.message(Command("backup"))
@router.message(F.text.in_({"بکاپ", "backup"}))
async def cmd_backup(msg: Message):
    if not await _is_owner(msg.from_user.id):
        return
    from admin.backup import create_and_send_backup
    await create_and_send_backup(msg.from_user.id, "manual")
