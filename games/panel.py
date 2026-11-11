# -*- coding: utf-8 -*-
"""games/panel.py — پنل کامل بازی‌ها (اجرای مستقیم در گروه بدون ارسال به پیوی + پیش‌نمایش مینی‌اپ)"""

import os
from urllib.parse import urlencode

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username

router = Router(name="panel")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")
# نام کوتاه مینی‌اپ ثبت‌شده در @BotFather (پیش‌فرض: app)
MINI_APP_SHORT_NAME = os.environ.get("MINI_APP_SHORT_NAME", "app").strip() or "app"


def make_miniapp_btn(text: str, start_param: str, is_pm: bool, style_fn=primary) -> InlineKeyboardButton:
    """
    ساخت دکمه ورود به مینی‌اپ:
    - در پیوی: استفاده از web_app_url مستقیم.
    - در گروه: استفاده از لینک استاندارد Direct Mini App (t.me/BotUsername/app?startapp=...)
      تا مینی‌اپ مستقیماً در همان گروه باز شود و خطای BUTTON_TYPE_INVALID ندهد.
    """
    if is_pm:
        return style_fn(text, web_app_url=f"{MINI_APP_URL}/?startapp={start_param}")

    bot_user = get_bot_username()
    direct_url = f"https://t.me/{bot_user}/{MINI_APP_SHORT_NAME}?startapp={start_param}"
    return style_fn(text, url=direct_url)


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)
    name = message.from_user.first_name or "رفیق"

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )

    rows = [
        # بازی‌های پازلی و انفرادی (ساخت میز و پیش‌نمایش مینی‌اپ در گروه)
        [primary(f"{E.PUZZLE} {t('game_2048_title', lang)}", f"gcard_2048_{uid}"),
         primary(f"{E.PUZZLE} {t('game_spuzzle', lang)}", f"gcard_spuzzle_{uid}")],
        [primary(f"{E.SPARK} {t('game_samegame', lang)}", f"gcard_samegame_{uid}")],

        # بازی‌های چندنفره (تشکیل لابی در گروه، عضوگیری و سپس ورود به مینی‌اپ)
        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],

        # بازی‌های سرعتی، تایپی و هوش (ساخت میز و پیش‌نمایش مینی‌اپ در گروه)
        [primary(f"{E.MIC} {t('game_typing', lang)}", f"gcard_typing_{uid}"),
         primary(f"{E.BRAIN} {t('game_hangman', lang)}", f"gcard_hangman_{uid}")],
        [primary(f"{E.TARGET} {t('game_guess_num', lang)}", f"gcard_guess_{uid}")],

        # گردونه شانس و قرعه‌کشی گروهی
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("gcard_"))
async def send_group_game_card(cb: CallbackQuery):
    """حذف منوی اصلی و نمایش کارت بازی به همراه پیش‌نمایش مینی‌اپ در همان گروه"""
    parts = cb.data.split("_")
    try:
        game = parts[1]
        host_id = int(parts[2])
    except (IndexError, ValueError):
        await cb.answer(t("error", "fa"), show_alert=True)
        return

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    await cb.answer()
    is_pm = cb.message.chat.type == ChatType.PRIVATE
    cid = cb.message.chat.id
    start_param = f"{game}__{cid}__{uid}"
    preview_url = f"{MINI_APP_URL}/?game={game}&chat={cid}&uid={uid}"

    game_titles = {
        "2048": t("game_2048_title", lang),
        "spuzzle": t("game_spuzzle", lang),
        "samegame": t("game_samegame", lang),
        "typing": t("game_typing", lang),
        "hangman": t("game_hangman", lang),
        "guess": t("game_guess_num", lang),
    }
    gtitle = game_titles.get(game, game)

    text = (
        f"<a href='{preview_url}'>&#8205;</a>"
        f"{E.GAME}{E.SPARK} <b>میز بازی {gtitle}</b>\n\n"
        f"{E.USER} آغازکننده: <b>{cb.from_user.first_name or 'Player'}</b>\n"
        f"{E.INFO} برای ورود مستقیم به مینی‌اپ بازی در همین صفحه روی دکمه زیر بزنید:"
    )

    rows = [
        [make_miniapp_btn(f"{E.PLAY} ورود به بازی ({gtitle})", start_param, is_pm, success)],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]

    try:
        await cb.message.edit_text(
            text,
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
    except Exception:
        await cb.message.answer(
            text,
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
