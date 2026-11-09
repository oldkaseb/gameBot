# -*- coding: utf-8 -*-
"""runtime.py — state مشترک بین main و inline_games"""

_bot_username = "bot"


def get_bot_username() -> str:
    return _bot_username


def set_bot_username(u: str) -> None:
    global _bot_username
    _bot_username = u or "bot"


async def check_forced_join(bot, user_id: int):
    """برگرداندن لیست کانال‌هایی که کاربر هنوز عضو نشده"""
    from database import db

    try:
        if await db.is_admin(user_id):
            return []
    except Exception:
        pass

    missing = []
    try:
        channels = await db.list_channels()
    except Exception:
        return []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception:
            # fail-open: اگر چک نشد، رد کن
            continue
    return missing
