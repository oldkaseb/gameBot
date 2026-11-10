from typing import Optional
from telegram import InlineKeyboardButton, KeyboardButton, WebAppInfo


def tg_emoji(emoji_id: str, fallback: str = "⚡") -> str:
    """
    تولید تگ HTML ایموجی پریمیوم برای استفاده در متن پیام‌ها.
    تلگرام برای رندر کاستوم ایموجی در متن، نیاز به یک کاراکتر جایگزین داخل تگ دارد،
    اما به همه کاربران ایموجی پریمیوم با آیدی مشخص‌شده را نمایش می‌دهد.
    """
    if not emoji_id:
        return ""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def styled_inline_btn(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    web_app_url: Optional[str] = None,
    switch_inline_query: Optional[str] = None,
    switch_inline_query_current_chat: Optional[str] = None,
    emoji_id: Optional[str] = None,
    style: str = "primary",  # مقادیر مجاز: "primary", "success", "danger"
) -> InlineKeyboardButton:
    """
    ساخت دکمه شیشه‌ای با استایل (primary / success / danger) و کاستوم ایموجی پریمیوم
    بدون استفاده از ایموجی یونیکد داخل متن دکمه.
    """
    api_kwargs = {}

    if emoji_id:
        api_kwargs["icon_custom_emoji_id"] = str(emoji_id)

    if style in ("primary", "success", "danger"):
        api_kwargs["style"] = style

    web_app = WebAppInfo(url=web_app_url) if web_app_url else None

    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data,
        url=url,
        web_app=web_app,
        switch_inline_query=switch_inline_query,
        switch_inline_query_current_chat=switch_inline_query_current_chat,
        api_kwargs=api_kwargs if api_kwargs else None,
    )


def styled_reply_btn(
    text: str,
    web_app_url: Optional[str] = None,
    emoji_id: Optional[str] = None,
    style: str = "primary",
) -> KeyboardButton:
    """
    ساخت دکمه کیبورد پایین چت با استایل و کاستوم ایموجی پریمیوم.
    """
    api_kwargs = {}

    if emoji_id:
        api_kwargs["icon_custom_emoji_id"] = str(emoji_id)

    if style in ("primary", "success", "danger"):
        api_kwargs["style"] = style

    web_app = WebAppInfo(url=web_app_url) if web_app_url else None

    return KeyboardButton(
        text=text,
        web_app=web_app,
        api_kwargs=api_kwargs if api_kwargs else None,
    )
