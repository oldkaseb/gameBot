# -*- coding: utf-8 -*-
"""پنل بازی‌های گروهی — بدون ارسال به PV همراه با لود مستقیم مینی‌اپ"""

import os
from urllib.parse import urlencode

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from utils.premium import success, primary, danger, kb

router = Router(name="panel")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


def _solo_btn(text: str, game: str, chat_id: int):
    """اجرای تک‌نفره و تایپی بدون پیوی مستقیم با پیش‌نمایش در گروه"""
    params = urlencode({"game": game, "chat": chat_id})
    return primary(text, web_app_url=f"{MINI_APP_URL}/?{params}")


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    cid = message.chat.id
    name = message.from_user.first_name or "رفیق"

    text = (
        f"{E.GAME}{E.SPARK} <b>سالن بازی‌های گروهی راینو</b>\n\n"
        f"انتخاب کنید تا میز بازی در همین گروه ایجاد شود:"
    )

    rows = [
        # بازی‌های پازلی و تک‌نفره (باز شدن مستقیم در گروه)
        [_solo_btn(f"{E.PUZZLE} 2048", "2048", cid),
         _solo_btn(f"{E.PUZZLE} پازل کشویی", "spuzzle", cid)],
        [_solo_btn(f"{E.SPARK} جفت‌ها", "samegame", cid)],

        # بازی‌های نیازمند تعیین اعضا (لابی گروهی)
        [primary(f"{E.TARGET} دوز ۲ نفره", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} دوز ۴ نفره", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} چهار در ردیف", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} حکم ۴ نفره", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} سنگ کاغذ قیچی", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} بازی حافظه", f"lobby_memory_{uid}")],

        # بازی‌های سرعتی و تایپی و هوشی
        [_solo_btn(f"{E.MIC} تایپ سرعتی", "typing", cid),
         _solo_btn(f"{E.BRAIN} حدس کلمه", "hangman", cid)],
        [_solo_btn(f"{E.TARGET} حدس عدد", "guess", cid)],

        # گردونه شانس
        [success(f"{E.TARGET} گردونه شانس و قرعه‌کشی", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} بستن منو", f"close_menu_{uid}")]
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("close_menu_"))
async def close_panel(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
