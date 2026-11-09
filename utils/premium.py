"""ساخت دکمه با استایل + ایموجی پریمیوم (دقیقاً مثل ربات ایموجی شما)"""

import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from emojis import E
from langs import t, get_user_lang

EMOJI_ID_RE = re.compile(r"\[(\d{5,25})\]")


def _strip_icon(text: str) -> tuple[str, str | None]:
    """اولین [id] داخل متن را جدا می‌کند و به عنوان آیکون برمی‌گرداند."""
    m = EMOJI_ID_RE.search(text or "")
    if not m:
        return text or "·", None
    cleaned = (text[:m.start()] + text[m.end():]).strip() or "·"
    return cleaned, m.group(1)


def btn(
    text: str,
    data: str | None = None,
    *,
    url: str | None = None,
    style: str | None = None,
    switch_inline: str | None = None,
    switch_current: str | None = None,
) -> InlineKeyboardButton:
    """دکمه با استایل و ایموجی پریمیوم"""
    cleaned, icon = _strip_icon(text)
    kwargs: dict = {"text": cleaned}
    if data is not None:  kwargs["callback_data"] = data
    if url is not None:   kwargs["url"] = url
    if switch_inline is not None:  kwargs["switch_inline_query"] = switch_inline
    if switch_current is not None: kwargs["switch_inline_query_current_chat"] = switch_current
    if style: kwargs["style"] = style
    if icon:  kwargs["icon_custom_emoji_id"] = icon
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        kwargs.pop("style", None)
        return InlineKeyboardButton(**kwargs)


# ── میان‌برهای رنگ
def primary(text: str, data: str) -> InlineKeyboardButton:
    return btn(text, data, style="primary")

def success(text: str, data: str) -> InlineKeyboardButton:
    return btn(text, data, style="success")

def danger(text: str, data: str) -> InlineKeyboardButton:
    return btn(text, data, style="danger")

def back_btn(uid: int, target: str = "menu") -> InlineKeyboardButton:
    lang = get_user_lang(uid)
    return primary(f"{E.ARROW} {t('btn_back', lang)}", target)

def cancel_btn(uid: int, target: str = "menu") -> InlineKeyboardButton:
    lang = get_user_lang(uid)
    return danger(f"{E.CROSS} {t('btn_cancel', lang)}", target)

def kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)
