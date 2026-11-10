"""ساخت دکمه — بدون style و icon_custom_emoji_id (سازگار با گروه و PV)"""

import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from emojis import E, BASE_MAP, EMOJI_ID_RE
from langs import t, get_user_lang, LANGS


def _clean_text(text: str) -> str:
    """تبدیل [emoji_id] به ایموجی یونیکد (دکمه‌ها از ایموجی پریمیوم پشتیبانی نمی‌کنند)"""
    if not text:
        return "·"
    result = EMOJI_ID_RE.sub(lambda m: BASE_MAP.get(m.group(1), "⭐"), text)
    return result.strip() or "·"


def btn(
    text: str,
    data=None,
    *,
    url=None,
    style=None,
    switch_inline=None,
    switch_current=None,
) -> InlineKeyboardButton:
    """
    ساخت دکمه امن برای گروه و PV.
    پارامتر style نادیده گرفته می‌شود چون در Telegram Bot API وجود ندارد.
    ایموجی‌ها به یونیکد تبدیل می‌شوند.
    """
    kwargs = {"text": _clean_text(text)}
    if data is not None:
        kwargs["callback_data"] = data
    if url is not None:
        kwargs["url"] = url
    if switch_inline is not None:
        kwargs["switch_inline_query"] = switch_inline
    if switch_current is not None:
        kwargs["switch_inline_query_current_chat"] = switch_current
    return InlineKeyboardButton(**kwargs)


def primary(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url)


def success(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url)


def danger(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url)


def _resolve_lang(user_or_lang) -> str:
    if isinstance(user_or_lang, int):
        return get_user_lang(user_or_lang)
    if isinstance(user_or_lang, str) and user_or_lang in LANGS:
        return user_or_lang
    return "fa"


def back_btn(user_or_lang, target: str = "menu") -> InlineKeyboardButton:
    lang = _resolve_lang(user_or_lang)
    return primary(f"{E.ARROW} {t('btn_back', lang)}", target)


def cancel_btn(user_or_lang, target: str = "menu") -> InlineKeyboardButton:
    lang = _resolve_lang(user_or_lang)
    return danger(f"{E.CROSS} {t('btn_cancel', lang)}", target)


def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)
