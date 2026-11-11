# -*- coding: utf-8 -*-
"""games/lobbies.py — لابی چندنفره تصویری داخل گروه و ورود مستقیم به RhinoGamesApp"""

import os
import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.enums import ParseMode, ChatType

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from games.panel import make_miniapp_btn
from webapp.backend.main import generate_game_banner

router = Router(name="lobbies")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

active_lobbies = {}

GAME_CONFIG = {
    "dooz":     {"max": 2, "name_key": "game_dooz",     "icon": E.TARGET},
    "doz4p":    {"max": 4, "name_key": "game_doz4p",    "icon": E.TARGET},
    "connect4": {"max": 2, "name_key": "game_connect4", "icon": E.GAME},
    "hokm":     {"max": 4, "name_key": "game_hokm_4p",  "icon": E.CARD},
    "rps":      {"max": 2, "name_key": "game_rps",      "icon": E.PUZZLE},
    "memory":   {"max": 2, "name_key": "game_memory",   "icon": E.BRAIN},
}


def _build_lobby_content(lobby: dict, lobby_id: str, lang: str):
    config = GAME_CONFIG[lobby["game_type"]]
    game_name = t(config["name_key"], lang)
    current_p = len(lobby["players"])
    max_p = lobby["max_players"]
    players_list = "\n".join(
        f"  {idx}. {E.USER} <b>{p['name']}</b>" for idx, p in enumerate(lobby["players"], 1)
    )

    if current_p < max_p:
        caption = (
            f"{config['icon']} <b>{t('lobby_title', lang, game=game_name)}</b>\n\n"
            f"{E.PEOPLE} {t('lobby_players', lang, cur=current_p, max=max_p)}:\n{players_list}\n\n"
            f"{E.HOURGLASS} {t('waiting_players', lang)}"
        )
        rows = [
            [success(f"{E.PLUS} {t('join_game', lang)} ({current_p}/{max_p})", f"join_lobby_{lobby_id}")],
            [danger(f"{E.CROSS} {t('btn_cancel', lang)}", f"cancel_lobby_{lobby_id}")],
        ]
    else:
        start_param = f"{lobby['game_type']}__{lobby_id}"
        caption = (
            f"{E.PARTY}{config['icon']} <b>{t('lobby_full_title', lang)} ({game_name})</b>\n\n"
            f"{E.PEOPLE} <b>بازیکنان میز:</b>\n{players_list}\n\n"
            f"{E.PLAY} روی دکمه زیر بزنید تا وارد مینی‌اپ بازی در همین گروه شوید:"
        )
        rows = [
            [make_miniapp_btn(f"{E.PLAY} {t('enter_game_table', lang)}", start_param, lobby["is_pm"], success)],
            [danger(f"{E.CROSS} بستن میز", f"cancel_lobby_{lobby_id}")],
        ]
    return caption, kb(rows)


@router.callback_query(F.data.startswith("lobby_"))
async def create_lobby(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        game_type = parts[1]
        host_id = int(parts[2])
    except (IndexError, ValueError):
        await cb.answer("Error", show_alert=True)
        return

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    config = GAME_CONFIG.get(game_type)
    if not config:
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return

    lobby_id = str(uuid.uuid4())[:8]
    lobby = {
        "game_type": game_type,
        "host_id": host_id,
        "max_players": config["max"],
        "players": [{"id": uid, "name": cb.from_user.first_name or "P1"}],
        "msg_id": cb.message.message_id,
        "chat_id": cb.message.chat.id,
        "is_pm": cb.message.chat.type == ChatType.PRIVATE,
        "is_photo": False,
    }
    active_lobbies[lobby_id] = lobby

    await cb.answer()

    # حذف منوی اصلی و ارسال کارت لابی با پیش‌نمایش تصویری
    try:
        await cb.message.delete()
    except Exception:
        pass

    caption, markup = _build_lobby_content(lobby, lobby_id, lang)
    try:
        png_bytes = generate_game_banner(game_type)
        photo = BufferedInputFile(png_bytes, filename=f"{game_type}.png")
        sent = await cb.message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        lobby["msg_id"] = sent.message_id
        lobby["is_photo"] = True
    except Exception:
        sent = await cb.message.answer(
            text=caption,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        lobby["msg_id"] = sent.message_id
        lobby["is_photo"] = False


async def _update_lobby_message(bot, lobby_id: str, lang: str):
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        return

    caption, markup = _build_lobby_content(lobby, lobby_id, lang)
    try:
        if lobby.get("is_photo"):
            await bot.edit_message_caption(
                chat_id=lobby["chat_id"],
                message_id=lobby["msg_id"],
                caption=caption,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.edit_message_text(
                text=caption,
                chat_id=lobby["chat_id"],
                message_id=lobby["msg_id"],
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        pass


@router.callback_query(F.data.startswith("join_lobby_"))
async def join_lobby(cb: CallbackQuery):
    lobby_id = cb.data.replace("join_lobby_", "")
    lobby = active_lobbies.get(lobby_id)
    lang = get_user_lang(cb.from_user.id)

    if not lobby:
        await cb.answer(t("lobby_expired", lang), show_alert=True)
        return
    if any(p["id"] == cb.from_user.id for p in lobby["players"]):
        await cb.answer(t("already_joined", lang), show_alert=True)
        return
    if len(lobby["players"]) >= lobby["max_players"]:
        await cb.answer(t("game_full", lang), show_alert=True)
        return

    lobby["players"].append({
        "id": cb.from_user.id,
        "name": cb.from_user.first_name or f"P{len(lobby['players']) + 1}",
    })
    await cb.answer(t("lobby_joined", lang))
    await _update_lobby_message(cb.bot, lobby_id, lang)


@router.callback_query(F.data.startswith("cancel_lobby_"))
async def cancel_lobby(cb: CallbackQuery):
    lobby_id = cb.data.replace("cancel_lobby_", "")
    lobby = active_lobbies.get(lobby_id)
    lang = get_user_lang(cb.from_user.id)

    if not lobby:
        await cb.answer(t("lobby_expired", lang), show_alert=True)
        return

    if cb.from_user.id != lobby["host_id"]:
        await cb.answer(t("not_your_game", lang), show_alert=True)
        return

    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
    active_lobbies.pop(lobby_id, None)
