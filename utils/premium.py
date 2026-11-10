"""utils/premium.py — نسخه اصلاح‌شده با استایل و ایموجی پریمیوم"""

import re
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
)
from emojis import E, BASE_MAP, EMOJI_ID_RE, PREMIUM_EMOJIS_ENABLED
from langs import t, get_user_lang, LANGS


# ── شناسه ایموجی پریمیوم برای استایل دکمه‌ها
STYLE_ICON = {
    "primary": "5213060381366300423",   # ✨ SPARK
    "success": "5215668908278686541",   # ✔️ OK2
    "danger":  "5212985062187012340",   # ❌ CROSS
}

# فلگ جهانی — اگر Bot API ایموجی پریمیوم در دکمه را نپذیرفت، غیرفعال می‌شود
_button_premium_ok = True


def button_premium_enabled() -> bool:
    return _button_premium_ok


def disable_button_premium() -> None:
    global _button_premium_ok
    _button_premium_ok = False


def _to_unicode(text: str) -> str:
    """تبدیل ایموجی پریمیوم به یونیکد (فقط برای fallback)"""
    if not text:
        return "·"
    result = EMOJI_ID_RE.sub(lambda m: BASE_MAP.get(m.group(1), ""), text)
    return re.sub(r"\s+", " ", result).strip() or "·"


def _extract_premium(text: str) -> tuple[str, str | None]:
    """اولین ایموجی پریمیوم را جدا می‌کند تا به‌عنوان icon قرار گیرد"""
    if not text:
        return "·", None
    ids = EMOJI_ID_RE.findall(text)
    if not ids:
        return text.strip() or "·", None
    first_eid = ids[0]
    cleaned = EMOJI_ID_RE.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "·", first_eid


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
    ساخت دکمه با پشتیبانی از:
    - ایموجی پریمیوم (icon_custom_emoji_id)
    - استایل رنگی (style)
    - WebApp
    """
    use_premium = PREMIUM_EMOJIS_ENABLED and _button_premium_ok

    kwargs = {}
    if use_premium:
        cleaned, eid = _extract_premium(text)
        kwargs["text"] = cleaned
        if eid is None and style:
            eid = STYLE_ICON.get(style)
        if eid:
            kwargs["icon_custom_emoji_id"] = eid
    else:
        kwargs["text"] = _to_unicode(text)

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

    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        # aiogram این فیلدها را نمی‌شناسد
        kwargs.pop("icon_custom_emoji_id", None)
        kwargs["text"] = _to_unicode(text)
        return InlineKeyboardButton(**kwargs)


def primary(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url, style="primary")


def success(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url, style="success")


def danger(text, data=None, *, url=None, web_app_url=None):
    return btn(text, data, url=url, web_app_url=web_app_url, style="danger")


def _resolve_lang(user_or_lang) -> str:
    if isinstance(user_or_lang, int):
        return get_user_lang(user_or_lang)
    if isinstance(user_or_lang, str) and user_or_lang in LANGS:
        return user_or_lang
    return "fa"


def back_btn(user_or_lang, target: str = "menu"):
    return primary(f"{E.ARROW} {t('btn_back', _resolve_lang(user_or_lang))}", target)


def cancel_btn(user_or_lang, target: str = "menu"):
    return danger(f"{E.CROSS} {t('btn_cancel', _resolve_lang(user_or_lang))}", target)


def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)
