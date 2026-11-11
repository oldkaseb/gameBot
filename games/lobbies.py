# -*- coding: utf-8 -*-
"""لابی‌های گروهی: عضویت و لانچ مینی‌اپ مستقیماً داخل همان پیام گروه"""

import os
import uuid
from urllib.parse import urlencode

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb

router = Router(name="lobbies")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

active_lobbies = {}

GAME_CONFIG = {
    "dooz":     {"max": 2, "title": "دوز ۲ نفره"},
    "doz4p":    {"max": 4, "title": "دوز ۴ نفره"},
    "connect4": {"max": 2, "title": "چهار در ردیف"},
    "hokm":     {"max": 4, "title": "حکم ۴ نفره"},
    "rps":      {"max": 2, "title": "سنگ کاغذ قیچی"},
    "memory":   {"max": 2, "title": "بازی حافظه"},
}


@router.callback_query(F.data.startswith("lobby_"))
async def create_lobby(cb: CallbackQuery):
    parts = cb.data.split("_")
    game_type = parts[1]
    host_id = int(parts[2])

    uid = cb.from_user.id
    if uid != host_id:
        await cb.answer("این پنل توسط شما ساخته نشده است.", show_alert=True)
        return

    cfg = GAME_CONFIG.get(game_type, {"max": 2, "title": game_type})
    lobby_id = str(uuid.uuid4())[:8]

    active_lobbies[lobby_id] = {
        "game_type": game_type,
        "title": cfg["title"],
        "host_id": host_id,
        "max_players": cfg["max"],
        "players": [{"id": uid, "name": cb.from_user.first_name or "P1"}],
        "chat_id": cb.message.chat.id,
        "msg_id": cb.message.message_id,
    }

    await cb.answer()
    await _render_lobby_message(cb.bot, lobby_id)


async def _render_lobby_message(bot, lobby_id: str):
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        return

    cur = len(lobby["players"])
    mx = lobby["max_players"]
    p_names = "\n".join(f"  {idx}. {E.USER} <b>{p['name']}</b>" for idx, p in enumerate(lobby["players"], 1))

    text = (
        f"{E.GAME}{E.SPARK} <b>میز بازی {lobby['title']}</b>\n\n"
        f"ظرفیت: <b>{cur}/{mx}</b>\n"
        f"لیست بازیکنان حاضر:\n{p_names}\n\n"
        f"{E.HOURGLASS} برای پیوستن روی دکمه زیر کلیک کنید:"
    )

    rows = []
    if cur < mx:
        rows.append([success(f"{E.PLUS} پیوستن به بازی ({cur}/{mx})", f"join_lobby_{lobby_id}")])
    else:
        params = urlencode({"game": lobby["game_type"], "session": lobby_id, "group": lobby["chat_id"]})
        app_url = f"{MINI_APP_URL}/?{params}"
        rows.append([success(f"{E.PLAY} ورود مستقیم به بازی (مینی‌اپ)", web_app_url=app_url)])

    rows.append([danger(f"{E.CROSS} بستن میز", f"cancel_lobby_{lobby_id}")])

    try:
        await bot.edit_message_text(
            text=text,
            chat_id=lobby["chat_id"],
            message_id=lobby["msg_id"],
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("join_lobby_"))
async def on_join(cb: CallbackQuery):
    lobby_id = cb.data.replace("join_lobby_", "")
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        await cb.answer("میز منقضی شده است.", show_alert=True)
        return

    uid = cb.from_user.id
    if any(p["id"] == uid for p in lobby["players"]):
        await cb.answer("شما قبلاً وارد شدید!", show_alert=True)
        return

    if len(lobby["players"]) >= lobby["max_players"]:
        await cb.answer("ظرفیت تکمیل است!", show_alert=True)
        return

    lobby["players"].append({"id": uid, "name": cb.from_user.first_name or f"P{len(lobby['players'])+1}"})
    await cb.answer("وارد میز شدید!")
    await _render_lobby_message(cb.bot, lobby_id)


@router.callback_query(F.data.startswith("cancel_lobby_"))
async def on_cancel(cb: CallbackQuery):
    lobby_id = cb.data.replace("cancel_lobby_", "")
    lobby = active_lobbies.get(lobby_id)
    if lobby and (cb.from_user.id == lobby["host_id"]):
        active_lobbies.pop(lobby_id, None)
        await cb.message.edit_text(f"{E.CROSS} میز بازی بسته شد.", reply_markup=None)
    else:
        await cb.answer("فقط سازنده میز اجازه لغو دارد.", show_alert=True)
