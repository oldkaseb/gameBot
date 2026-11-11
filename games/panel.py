# -*- coding: utf-8 -*-
"""games/panel.py — پنل ۷ زبانه بازی‌ها با ارسال بنر تصویری و باز شدن مستقیم مینی‌اپ RhinoGamesApp"""

import os
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardButton, BufferedInputFile, LinkPreviewOptions
)
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang, load_lang_from_db
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username
from database import db

router = Router(name="panel")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")
MINI_APP_SHORT_NAME = os.environ.get("MINI_APP_SHORT_NAME", "RhinoGamesApp").strip() or "RhinoGamesApp"


async def _resolve_lang(uid: int) -> str:
    try:
        user = await db.get_user(uid)
        if user and user["language"]:
            load_lang_from_db(uid, user["language"])
    except Exception:
        pass
    return get_user_lang(uid)


def make_miniapp_btn(text: str, start_param: str, is_pm: bool, style_fn=success) -> InlineKeyboardButton:
    if is_pm:
        return style_fn(text, web_app_url=f"{MINI_APP_URL}/?startapp={start_param}")

    bot_user = get_bot_username()
    direct_url = f"https://t.me/{bot_user}/{MINI_APP_SHORT_NAME}?startapp={start_param}"
    return style_fn(text, url=direct_url)


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = await _resolve_lang(uid)
    name = message.from_user.first_name or t("player", lang)

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )

    rows = [
        # ۳ بازی اعتیادآور جدید (Core Loop)
        [primary(f"{E.FIRE} شکارچی سیاه‌چال", f"gcard_dungeon_{uid}"),
         primary(f"{E.SPARK} هک گاوصندوق", f"gcard_cybervault_{uid}")],
        [primary(f"{E.TROPHY} برج شیاطین (RPG)", f"gcard_demontower_{uid}")],

        # حکم ۲ نفره و ۴ نفره
        [primary(f"{E.CARD} {t('game_hokm', lang)}", f"lobby_hokm2p_{uid}"),
         primary(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_2048_title', lang)}", f"gcard_2048_{uid}"),
         primary(f"{E.PUZZLE} {t('game_spuzzle', lang)}", f"gcard_spuzzle_{uid}")],
        [primary(f"{E.SPARK} {t('game_samegame', lang)}", f"gcard_samegame_{uid}")],

        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [primary(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],

        [primary(f"{E.MIC} {t('game_typing', lang)}", f"gcard_typing_{uid}"),
         primary(f"{E.BRAIN} {t('game_hangman', lang)}", f"gcard_hangman_{uid}")],
        [primary(f"{E.TARGET} {t('game_guess_num', lang)}", f"gcard_guess_{uid}")],

        [primary(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("gcard_"))
async def send_group_game_card(cb: CallbackQuery):
    from webapp.backend.main import generate_game_banner

    parts = cb.data.split("_")
    try:
        game = parts[1]
        host_id = int(parts[2])
    except (IndexError, ValueError):
        await cb.answer(t("error", "fa"), show_alert=True)
        return

    uid = cb.from_user.id
    lang = await _resolve_lang(uid)

    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    await cb.answer()
    is_pm = cb.message.chat.type == ChatType.PRIVATE
    cid = cb.message.chat.id
    start_param = f"{game}__{cid}__{lang}"

    game_titles = {
        "2048": t("game_2048_title", lang),
        "spuzzle": t("game_spuzzle", lang),
        "samegame": t("game_samegame", lang),
        "typing": t("game_typing", lang),
        "hangman": t("game_hangman", lang),
        "guess": t("game_guess_num", lang),
        "dungeon": "شکارچی سیاه‌چال (Dungeon Heist)",
        "cybervault": "هک گاوصندوق سایبری",
        "demontower": "برج شیاطین (Demon Tower)",
    }
    gtitle = game_titles.get(game, game)

    caption = (
        f"{E.GAME}{E.SPARK} <b>{gtitle}</b>\n\n"
        f"{E.USER} {t('player', lang)}: <b>{cb.from_user.first_name or 'Player'}</b>\n"
        f"{E.INFO} {t('open_in_pm_body', lang)}"
    )

    rows = [
        [make_miniapp_btn(f"{E.PLAY} {t('enter_game_table', lang)} ({gtitle})", start_param, is_pm, success)],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]

    try:
        await cb.message.delete()
    except Exception:
        pass

    try:
        png_bytes = generate_game_banner(game)
        photo = BufferedInputFile(png_bytes, filename=f"{game}.png")
        await cb.message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        preview_url = f"{MINI_APP_URL}/?game={game}&chat={cid}&lang={lang}"
        await cb.message.answer(
            text=caption,
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            link_preview_options=LinkPreviewOptions(
                url=preview_url,
                prefer_large_media=True,
                show_above_text=True,
            ),
        )


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
