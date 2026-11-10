"""utils/premium.py — دکمه‌های امن ۱۰۰٪، بدون BUTTON_TYPE_INVALID"""

import os
import re
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
)
from emojis import E, BASE_MAP, EMOJI_ID_RE
from langs import t, get_user_lang, LANGS

# اگر ربات Premium Bot دارید، این را true کنید (پیش‌فرض خاموش)
_BUTTON_PREMIUM = os.getenv("BUTTON_PREMIUM", "false").lower() in ("1", "true", "yes")

# ── regex برای حذف تمام ایموجی‌های یونیکد
_UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "\u2190-\u21FF"
    "\u2700-\u27BF"
    "\uFE0F\u200D"
    "]+",
    flags=re.UNICODE,
)


def _clean_button_text(text: str) -> str:
    """حذف کامل تمام ایموجی‌ها از متن دکمه"""
    if not text:
        return "·"
    text = EMOJI_ID_RE.sub("", text)
    text = _UNICODE_EMOJI_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "·"


def _first_premium_id(text: str) -> str | None:
    ids = EMOJI_ID_RE.findall(text or "")
    return ids[0] if ids else None


def btn(
    text: str,
    data=None,
    *,
    url=None,
    web_app_url=None,
    style=None,
    switch_inline=None,
    switch_current=None,
) -> InlineKeyboardButton:
    """
    دکمه امن — پیش‌فرض متن تمیز بدون هیچ ایموجی.
    با BUTTON_PREMIUM=true و Premium Bot، از icon_custom_emoji_id استفاده می‌شود.
    """
    if _BUTTON_PREMIUM:
        clean = EMOJI_ID_RE.sub("", text or "").strip() or "·"
        kwargs = {"text": clean}
        eid = _first_premium_id(text)
        if eid:
            kwargs["icon_custom_emoji_id"] = eid
        if data is not None:
            kwargs["callback_data"] = data
        if url is not None:
            kwargs["url"] = url
        if web_app_url is not None:
            kwargs["web_app"] = WebAppInfo(url=web_app_url)
        if switch_inline is not None:
            kwargs["switch_inline_query"] = switch_inline
        if switch_current is not None:
            kwargs["switch_inline_query_current_chat"] = switch_current
        return InlineKeyboardButton(**kwargs)

    # حالت امن پیش‌فرض — فقط متن
    kwargs = {"text": _clean_button_text(text)}
    if data is not None:
        kwargs["callback_data"] = data
    if url is not None:
        kwargs["url"] = url
    if web_app_url is not None:
        kwargs["web_app"] = WebAppInfo(url=web_app_url)
    if switch_inline is not None:
        kwargs["switch_inline_query"] = switch_inline
    if switch_current is not None:
        kwargs["switch_inline_query_current_chat"] = switch_current
    return InlineKeyboardButton(**kwargs)


def primary(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url)


def success(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url)


def danger(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url)


def _resolve_lang(user_or_lang) -> str:
    if isinstance(user_or_lang, int):
        return get_user_lang(user_or_lang)
    if isinstance(user_or_lang, str) and user_or_lang in LANGS:
        return user_or_lang
    return "fa"


def back_btn(user_or_lang, target: str = "menu"):
    return primary(t("btn_back", _resolve_lang(user_or_lang)), target)


def cancel_btn(user_or_lang, target: str = "menu"):
    return danger(t("btn_cancel", _resolve_lang(user_or_lang)), target)


def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)
