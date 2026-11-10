# -*- coding: utf-8 -*-
"""لابی چندنفره — استارت تمام بازی‌ها در مینی‌اپ با حفظ استایل primary / success / danger و کاستوم ایموجی"""

import os
import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username

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


@router.callback_query(F.data.startswith("lobby_"))
async def create_lobby(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        game_type = parts[1]
        host_id = int(parts[2])
    except (IndexError, ValueError):
        await cb.answer(t("error", "fa"), show_alert=True)
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
    active_lobbies[lobby_id] = {
        "game_type": game_type,
        "host_id": host_id,
        "max_players": config["max"],
        "players": [{"id": uid, "name": cb.from_user.first_name or "P1"}],
        "msg_id": cb.message.message_id,
        "chat_id": cb.message.chat.id,
    }

    await cb.answer()
    await _update_lobby_message(cb.bot, lobby_id, lang)


async def _update_lobby_message(bot, lobby_id: str, lang: str):
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        return

    config = GAME_CONFIG[lobby["game_type"]]
    game_name = t(config["name_key"], lang)
    current_p = len(lobby["players"])
    max_p = lobby["max_players"]
    players_list = "\n".join(f"{E.USER} {p['name']}" for p in lobby["players"])

    text = (
        f"{config['icon']} <b>{t('lobby_title', lang, game=game_name)}</b>\n\n"
        f"{E.PEOPLE} {t('lobby_players', lang, cur=current_p, max=max_p)}:\n{players_list}\n\n"
        f"{E.HOURGLASS} {t('waiting_players', lang)}"
    )
    rows = [
        [success(f"{E.PLUS} {t('join_game', lang)}", f"join_lobby_{lobby_id}")],
        [danger(f"{E.CROSS} {t('btn_cancel', lang)}", f"cancel_lobby_{lobby_id}")],
    ]

    try:
        await bot.edit_message_text(
            text=text,
            chat_id=lobby["chat_id"],
            message_id=lobby["msg_id"],
            reply_markup=kb(rows),
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

    if len(lobby["players"]) == lobby["max_players"]:
        await _start_via_dm(cb.bot, lobby_id)
    else:
        await _update_lobby_message(cb.bot, lobby_id, lang)


async def _start_via_dm(bot, lobby_id: str):
    """ارسال لینک مینی‌اپ بازی به پیوی بازیکنان"""
    lobby = active_lobbies[lobby_id]
    bot_name = get_bot_username()

    for player in lobby["players"]:
        plang = get_user_lang(player["id"])
        game_url = f"{MINI_APP_URL}/?game={lobby['game_type']}&session={lobby_id}&uid={player['id']}&lang={plang}"
        try:
            await bot.send_message(
                player["id"],
                f"{E.PARTY} <b>{t('lobby_full_title', plang)}</b>\n\n"
                f"{E.INFO} {t('enter_game_table', plang)}",
                reply_markup=kb([[
                    success(f"{E.GAME} {t('enter_game_table', plang)}", web_app_url=game_url)
                ]]),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            try:
                await bot.send_message(
                    lobby["chat_id"],
                    f"{E.WARN} {t('start_pm_first_msg', plang)}",
                    reply_markup=kb([[
                        primary(
                            f"{E.BOT} {t('open_bot_btn', plang)}",
                            url=f"https://t.me/{bot_name}?start=game_{lobby['game_type']}",
                        )
                    ]]),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    lang = get_user_lang(lobby["host_id"])
    try:
        await bot.edit_message_text(
            text=(
                f"{E.PARTY} <b>{t('lobby_full_title', lang)}</b>\n\n"
                f"{E.INFO} {t('check_pm_for_game', lang)}"
            ),
            chat_id=lobby["chat_id"],
            message_id=lobby["msg_id"],
            reply_markup=None,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    del active_lobbies[lobby_id]


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
        await cb.message.edit_text(
            f"{E.CROSS} {t('lobby_cancelled', lang)}",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
    del active_lobbies[lobby_id]
