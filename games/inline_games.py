# -*- coding: utf-8 -*-
"""games/inline_games.py — دعوت و اجرای تمام بازی‌ها در حالت اینلاین از طریق Mini App با کاستوم ایموجی"""

import logging
import os
import uuid

from aiogram import Router, F
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    CallbackQuery,
)
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import check_forced_join, get_bot_username

router = Router(name="inline_games")
log = logging.getLogger("inline_games")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

INLINE_GAMES_LIST = [
    ("2048",     E.PUZZLE, "2048",          "پازل عددی (Mini App)"),
    ("spuzzle",  E.PUZZLE, "پازل کششی",     "پازل کلاسیک (Mini App)"),
    ("samegame", E.SPARK,  "جفت‌ها",         "پازل رنگی (Mini App)"),
    ("dooz",     E.TARGET, "دوز ۲ نفره",    "رقابت آنلاین (Mini App)"),
    ("doz4p",    E.TARGET, "دوز ۴ نفره",    "رقابت ۴ نفره (Mini App)"),
    ("connect4", E.GAME,   "چهار در ردیف",   "استراتژیک (Mini App)"),
    ("hokm",     E.CARD,   "حکم ۴ نفره",     "ورق آنلاین (Mini App)"),
    ("rps",      E.PUZZLE, "سنگ کاغذ قیچی", "رقابت سریع (Mini App)"),
    ("memory",   E.BRAIN,  "حافظه",          "تقویت حافظه (Mini App)"),
    ("typing",   E.MIC,    "تایپ سرعتی",     "مسابقه تایپ (Mini App)"),
    ("hangman",  E.BRAIN,  "حدس کلمه",       "چالش کلمات (Mini App)"),
    ("guess",    E.TARGET, "حدس عدد",        "چالش هوش (Mini App)"),
    ("gardone",  E.SPARK,  "گردونه شانس",    "چرخ شانس (Mini App)"),
]


@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    uid = query.from_user.id
    lang = get_user_lang(uid)

    try:
        missing = await check_forced_join(query.bot, uid)
        if missing:
            await query.answer(
                [], cache_time=1, is_personal=True,
                switch_pm_text=t("inline_join_required", lang),
                switch_pm_parameter="start",
            )
            return
    except Exception:
        pass

    q = (query.query or "").strip().lower()
    results = []

    for gtype, emj, name, desc in INLINE_GAMES_LIST:
        if q and q not in gtype.lower() and q not in name:
            continue

        session_id = str(uuid.uuid4())[:8]
        results.append(InlineQueryResultArticle(
            id=f"ig|{gtype}|{session_id}",
            title=name,
            description=desc,
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"{emj} <b>{name}</b>\n\n"
                    f"{E.USER} میزبان: <b>{query.from_user.first_name or 'Player'}</b>\n"
                    f"{E.INFO} برای ورود به مینی‌اپ بازی روی دکمه زیر بزنید:"
                ),
                parse_mode=ParseMode.HTML,
            ),
            reply_markup=kb([
                [success(f"{E.PLAY} ورود به بازی (Mini App)", f"igstart_{gtype}_{session_id}")],
            ]),
        ))

    await query.answer(results, cache_time=1, is_personal=True)


@router.callback_query(F.data.startswith("igstart_"))
async def on_start_button(cb: CallbackQuery):
    parts = cb.data.split("_")
    gtype = parts[1] if len(parts) > 1 else "2048"
    session_id = parts[2] if len(parts) > 2 else "solo"

    uid = cb.from_user.id
    lang = get_user_lang(uid)
    bot_name = get_bot_username()
    game_url = f"{MINI_APP_URL}/?game={gtype}&session={session_id}&uid={uid}&lang={lang}"
    deep_link = f"https://t.me/{bot_name}?start=game_{gtype}"

    try:
        await cb.bot.send_message(
            uid,
            f"{E.GAME} <b>{t('open_in_pm_title', lang)}</b>\n\n"
            f"{E.INFO} {t('open_in_pm_body', lang)}",
            reply_markup=kb([[
                success(f"{E.PLAY} {t('open_game_btn', lang)}", web_app_url=game_url),
            ]]),
            parse_mode=ParseMode.HTML,
        )
        await cb.answer(t("check_pm", lang), show_alert=True)
    except Exception:
        await cb.answer(
            f"ابتدا ربات @{bot_name} را در پیوی استارت کنید!",
            show_alert=True,
        )
