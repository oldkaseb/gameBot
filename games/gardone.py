# -*- coding: utf-8 -*-
"""games/gardone.py — گردونه شانس گروهی (انتخاب تعداد برنده توسط سازنده + لابی شرکت‌کنندگان + قرعه‌کشی)"""

import asyncio
import html
import random
import time

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import primary, success, danger, kb
from database import db

router = Router(name="gardone")

# ساختار ذخیره‌سازی گردونه‌های فعال در گروه‌ها: {chat_id: {...}}
active_gardones: dict[int, dict] = {}


def _safe(name: str) -> str:
    return html.escape(name or "Player")


def _fa_to_en(text: str) -> str:
    return (text or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


def _ask_count_kb(uid: int, lang: str):
    """کیبورد انتخاب سریع تعداد برنده‌ها (۱ تا ۵) یا ارسال عدد در چت"""
    row1 = [primary(f"{E.TROPHY} {i}", f"gardone_cnt_{uid}_{i}") for i in range(1, 4)]
    row2 = [primary(f"{E.TROPHY} {i}", f"gardone_cnt_{uid}_{i}") for i in range(4, 6)]
    row3 = [danger(f"{E.CROSS} {t('gardone_cancel', lang)}", f"gardone_cancel_{uid}")]
    return kb([row1, row2, row3])


def _lobby_kb(uid: int, lang: str):
    """کیبورد لابی گردونه در گروه"""
    return kb([
        [success(f"{E.PLUS} {t('gardone_join', lang)}", "gardone_join")],
        [
            primary(f"{E.SPARK} {t('gardone_spin', lang)}", f"gardone_spin_{uid}"),
            danger(f"{E.CROSS} {t('gardone_cancel', lang)}", f"gardone_cancel_{uid}"),
        ],
    ])


def _render_lobby_text(g: dict, lang: str) -> str:
    participants = g["participants"]
    count = len(participants)
    if participants:
        plist = "\n".join(
            f"  {idx}. {E.USER} <b>{_safe(p['name'])}</b>"
            for idx, p in enumerate(participants.values(), start=1)
        )
    else:
        plist = f"  {E.INFO} {t('gardone_nobody', lang)}"

    return (
        f"{E.SPARK}{E.PARTY} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{E.INFO} {t('gardone_active', lang)}\n"
        f"{E.CROWN} سازنده: <b>{_safe(g['host_name'])}</b>\n"
        f"{E.TROPHY} {t('gardone_winner_count', lang, n=g['winner_count'])}\n\n"
        f"{E.PEOPLE} <b>{t('gardone_participants', lang, n=count)}:</b>\n{plist}"
    )


# ═══════════ مرحله ۱: شروع گردونه و پرسیدن تعداد برنده‌ها از درخواست‌کننده ═══════════

@router.callback_query(F.data.startswith("gardone_start_"))
async def gardone_start_cb(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        starter_id = int(parts[2])
    except (IndexError, ValueError):
        starter_id = cb.from_user.id

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != starter_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    if not await db.is_game_enabled("gardone"):
        await cb.answer(t("game_disabled", lang), show_alert=True)
        return

    chat_id = cb.message.chat.id
    existing = active_gardones.get(chat_id)
    if existing and time.time() - existing.get("created_at", 0) < 1800:
        await cb.answer(t("game_already_running", lang), show_alert=True)
        return

    active_gardones[chat_id] = {
        "status": "choosing_count",
        "host_id": uid,
        "host_name": cb.from_user.first_name or "Host",
        "winner_count": 1,
        "participants": {},
        "msg_id": cb.message.message_id,
        "chat_id": chat_id,
        "created_at": time.time(),
    }

    await cb.answer()
    text = (
        f"{E.SPARK}{E.TROPHY} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{E.USER} <b>{_safe(cb.from_user.first_name)}</b>\n"
        f"{E.INFO} {t('gardone_ask_count', lang)}"
    )
    try:
        await cb.message.edit_text(
            text,
            reply_markup=_ask_count_kb(uid, lang),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        msg = await cb.message.answer(
            text,
            reply_markup=_ask_count_kb(uid, lang),
            parse_mode=ParseMode.HTML,
        )
        active_gardones[chat_id]["msg_id"] = msg.message_id


# ═══════════ مرحله ۲: ثبت تعداد برنده‌ها (با دکمه یا ارسال عدد ۱ تا ۱۰ در چت) ═══════════

@router.callback_query(F.data.startswith("gardone_cnt_"))
async def gardone_set_count_cb(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        host_id = int(parts[2])
        w_count = int(parts[3])
    except (IndexError, ValueError):
        await cb.answer("Error", show_alert=True)
        return

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != host_id:
        await cb.answer(t("gardone_only_starter", lang), show_alert=True)
        return

    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    if not g or g.get("host_id") != uid:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return

    g["winner_count"] = max(1, min(10, w_count))
    g["status"] = "joining"

    await cb.answer()
    await cb.message.edit_text(
        _render_lobby_text(g, lang),
        reply_markup=_lobby_kb(uid, lang),
        parse_mode=ParseMode.HTML,
    )


@router.message(
    F.text,
    lambda msg: (
        msg.chat.id in active_gardones
        and active_gardones[msg.chat.id].get("status") == "choosing_count"
        and active_gardones[msg.chat.id].get("host_id") == msg.from_user.id
    ),
)
async def gardone_set_count_msg(msg: Message):
    chat_id = msg.chat.id
    g = active_gardones.get(chat_id)
    if not g:
        return

    uid = msg.from_user.id
    lang = get_user_lang(uid)
    raw = _fa_to_en(msg.text.strip())

    if not raw.isdigit():
        return

    w_count = int(raw)
    if not (1 <= w_count <= 10):
        await msg.reply(f"{E.WARN} {t('gardone_invalid_count', lang)}", parse_mode=ParseMode.HTML)
        return

    g["winner_count"] = w_count
    g["status"] = "joining"

    try:
        await msg.bot.delete_message(chat_id, g["msg_id"])
    except Exception:
        pass

    sent = await msg.answer(
        _render_lobby_text(g, lang),
        reply_markup=_lobby_kb(uid, lang),
        parse_mode=ParseMode.HTML,
    )
    g["msg_id"] = sent.message_id


# ═══════════ مرحله ۳: شرکت کاربران در گردونه شانس ═══════════

@router.callback_query(F.data == "gardone_join")
async def gardone_join_cb(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if not g or g.get("status") != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return

    if uid in g["participants"]:
        await cb.answer(t("gardone_already_joined", lang), show_alert=True)
        return

    g["participants"][uid] = {
        "id": uid,
        "name": cb.from_user.first_name or f"User {uid}",
        "username": cb.from_user.username or "",
    }

    await cb.answer(t("gardone_joined", lang))

    host_lang = get_user_lang(g["host_id"])
    try:
        await cb.message.edit_text(
            _render_lobby_text(g, host_lang),
            reply_markup=_lobby_kb(g["host_id"], host_lang),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


# ═══════════ مرحله ۴: چرخاندن گردونه توسط درخواست‌کننده ═══════════

@router.callback_query(F.data.startswith("gardone_spin_"))
async def gardone_spin_cb(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if not g or g.get("status") != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return

    if uid != g["host_id"]:
        await cb.answer(t("gardone_only_starter", lang), show_alert=True)
        return

    players = list(g["participants"].values())
    if not players:
        await cb.answer(t("gardone_empty", lang), show_alert=True)
        return

    g["status"] = "spinning"
    await cb.answer()

    try:
        await cb.message.edit_text(
            f"{E.SPARK}{E.HOURGLASS} <b>{t('gardone_spinning', lang)}</b>",
            reply_markup=None,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await asyncio.sleep(1.5)

    win_count = min(g["winner_count"], len(players))
    winners = random.sample(players, win_count)

    for w in winners:
        try:
            await db.add_win(w["id"], "gardone")
        except Exception:
            pass

    winners_lines = "\n".join(
        f"  {idx}. {E.TROPHY} <a href='tg://user?id={w['id']}'><b>{_safe(w['name'])}</b></a>"
        for idx, w in enumerate(winners, start=1)
    )

    final_text = (
        f"{E.PARTY}{E.TROPHY} <b>{t('gardone_title', lang)} — {t('gardone_winner', lang)}</b>\n\n"
        f"{winners_lines}\n\n"
        f"{E.PEOPLE} شرکت‌کنندگان کل: <b>{len(players)} نفر</b>\n"
        f"{E.CROWN} میزبان: <b>{_safe(g['host_name'])}</b>"
    )

    active_gardones.pop(chat_id, None)

    try:
        await cb.message.edit_text(final_text, parse_mode=ParseMode.HTML)
    except Exception:
        await cb.message.answer(final_text, parse_mode=ParseMode.HTML)


# ═══════════ مرحله ۵: لغو گردونه توسط درخواست‌کننده (یا ادمین) ═══════════

@router.callback_query(F.data.startswith("gardone_cancel_"))
async def gardone_cancel_cb(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if not g:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return

    if uid != g["host_id"] and not await db.is_admin(uid):
        await cb.answer(t("gardone_only_starter", lang), show_alert=True)
        return

    active_gardones.pop(chat_id, None)
    await cb.answer()

    try:
        await cb.message.edit_text(
            f"{E.CROSS} <b>{t('gardone_cancelled', lang)}</b>",
            reply_markup=None,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
