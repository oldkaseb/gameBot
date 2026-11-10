# -*- coding: utf-8 -*-
"""utils/premium.py — ساخت دکمه‌های استایل‌دار (primary / success / danger) با کاستوم ایموجی در Aiogram 3"""

import re
from typing import Optional, List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from emojis import EMOJI_ID_RE, TG_EMOJI_TAG_RE, EMOJI_MAP

# حذف هرگونه ایموجی یونیکد ساده احتمالی از روی متن دکمه‌ها و تبدیل آن به آیکون پریمیوم
UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0001FA00-\U0001FAFF"
    "\u200d\ufe0f\u20e3"
    "]+",
    flags=re.UNICODE,
)


def tg_emoji(emoji_id: str, fallback: str = "·") -> str:
    if not emoji_id:
        return ""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def _extract_btn_emoji_and_clean_text(text: str, default_emoji_id: Optional[str] = None) -> tuple[str, Optional[str]]:
    if not text:
        return "·", default_emoji_id

    found_id = default_emoji_id

    # ۱. استخراج آیدی از توکن [E:12345]
    m_tok = EMOJI_ID_RE.search(text)
    if m_tok and not found_id:
        found_id = m_tok.group(1)

    # ۲. استخراج آیدی از تگ <tg-emoji>
    m_tag = TG_EMOJI_TAG_RE.search(text)
    if m_tag and not found_id:
        found_id = m_tag.group(1)

    # حذف توکن‌ها، تگ‌ها و ایموجی‌های یونیکد ساده از متن دکمه
    clean = EMOJI_ID_RE.sub("", text)
    clean = TG_EMOJI_TAG_RE.sub("", clean)
    clean = UNICODE_EMOJI_RE.sub("", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        clean = "·"

    return clean, found_id


def _make_button(
    text: str,
    callback_data: Optional[str] = None,
    *,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
    style: str = "primary",
) -> InlineKeyboardButton:
    clean_text, resolved_emoji_id = _extract_btn_emoji_and_clean_text(text, emoji_id)

    # اگر هیچ ایموجی پریمیومی روی دکمه نبود، به صورت پیش‌فرض یک کاستوم ایموجی متناسب با استایل ست کن
    if not resolved_emoji_id:
        if style == "success":
            resolved_emoji_id = EMOJI_MAP["CHECK"]
        elif style == "danger":
            resolved_emoji_id = EMOJI_MAP["CROSS"]
        else:
            resolved_emoji_id = EMOJI_MAP["SPARK"]

    kwargs = {"text": clean_text}

    if web_app_url:
        kwargs["web_app"] = WebAppInfo(url=web_app_url)
    elif url:
        kwargs["url"] = url
    elif switch_inline_query is not None:
        kwargs["switch_inline_query"] = switch_inline_query
    elif switch_inline_query_current_chat is not None:
        kwargs["switch_inline_query_current_chat"] = switch_inline_query_current_chat
    else:
        kwargs["callback_data"] = callback_data or "noop"

    # ست کردن کاستوم ایموجی پریمیوم روی دکمه و استایل (primary / success / danger)
    kwargs["icon_custom_emoji_id"] = str(resolved_emoji_id)
    if style in ("primary", "success", "danger"):
        kwargs["style"] = style

    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        # در صورتی که نسخه aiogram قدیمی‌تر باشد و فیلدهای جدید را مستقیم در init نپذیرد
        kwargs.pop("style", None)
        try:
            return InlineKeyboardButton(**kwargs)
        except TypeError:
            kwargs.pop("icon_custom_emoji_id", None)
            return InlineKeyboardButton(**kwargs)


def btn(
    text: str,
    callback_data: Optional[str] = None,
    *,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
    style: str = "primary",
) -> InlineKeyboardButton:
    return _make_button(
        text,
        callback_data,
        url=url,
        web_app_url=web_app_url,
        switch_inline_query=switch_inline_query,
        switch_inline_query_current_chat=switch_inline_query_current_chat,
        emoji_id=emoji_id,
        style=style,
    )


def primary(
    text: str,
    callback_data: Optional[str] = None,
    *,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
) -> InlineKeyboardButton:
    return _make_button(
        text,
        callback_data,
        url=url,
        web_app_url=web_app_url,
        switch_inline_query=switch_inline_query,
        switch_inline_query_current_chat=switch_inline_query_current_chat,
        emoji_id=emoji_id,
        style="primary",
    )


def success(
    text: str,
    callback_data: Optional[str] = None,
    *,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
) -> InlineKeyboardButton:
    return _make_button(
        text,
        callback_data,
        url=url,
        web_app_url=web_app_url,
        switch_inline_query=switch_inline_query,
        switch_inline_query_current_chat=switch_inline_query_current_chat,
        emoji_id=emoji_id,
        style="success",
    )


def danger(
    text: str,
    callback_data: Optional[str] = None,
    *,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
) -> InlineKeyboardButton:
    return _make_button(
        text,
        callback_data,
        url=url,
        web_app_url=web_app_url,
        switch_inline_query=switch_inline_query,
        switch_inline_query_current_chat=switch_inline_query_current_chat,
        emoji_id=emoji_id,
        style="danger",
    )


def kb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)
