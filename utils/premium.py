"""ساخت دکمه با استایل + ایموجی پریمیوم"""

import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from emojis import E
from langs import t, get_user_lang, LANGS

EMOJI_ID_RE = re.compile(r"\[(\d{5,25})\]")


def _strip_icon(text: str):
    m = EMOJI_ID_RE.search(text or "")
    if not m:
        return text or "·", None
    cleaned = (text[:m.start()] + text[m.end():]).strip() or "·"
    return cleaned, m.group(1)


def btn(
    text: str,
    data=None,
    *,
    url=None,
    style=None,
    switch_inline=None,
    switch_current=None,
) -> InlineKeyboardButton:
    """دکمه با استایل و ایموجی پریمیوم — پشتیبانی از callback_data یا url"""
    cleaned, icon = _strip_icon(text)
    kwargs = {"text": cleaned}
    if data is not None:
        kwargs["callback_data"] = data
    if url is not None:
        kwargs["url"] = url
    if switch_inline is not None:
        kwargs["switch_inline_query"] = switch_inline
    if switch_current is not None:
        kwargs["switch_inline_query_current_chat"] = switch_current
    if style:
        kwargs["style"] = style
    if icon:
        kwargs["icon_custom_emoji_id"] = icon
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        kwargs.pop("style", None)
        try:
            return InlineKeyboardButton(**kwargs)
        except TypeError:
            kwargs.pop("icon_custom_emoji_id", None)
            return InlineKeyboardButton(**kwargs)


# ── میان‌برهای رنگ — حالا از url هم پشتیبانی می‌کنند
def primary(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url, style="primary")


def success(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url, style="success")


def danger(text: str, data=None, *, url=None) -> InlineKeyboardButton:
    return btn(text, data, url=url, style="danger")


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
