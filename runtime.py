# -*- coding: utf-8 -*-
"""runtime.py — مدیریت یوزرنیم ربات و بررسی دقیق عضویت اجباری در پیوی، گروه و مینی‌اپ"""

import os

_bot_username = "RhinoGamesBot"
DEFAULT_FORCED_CHANNEL = os.getenv("FORCED_JOIN_CHANNEL", "@RHINOBOT_TM").strip()


def get_bot_username() -> str:
    return _bot_username


def set_bot_username(u: str) -> None:
    global _bot_username
    _bot_username = u or "RhinoGamesBot"


async def check_forced_join(bot, user_id: int, bypass_admin: bool = True):
    """
    برگرداندن لیست کانال‌هایی که کاربر هنوز در آن‌ها عضو نشده است.
    هم کانال‌های ثبت‌شده در پنل ادمین (PostgreSQL) و هم کانال پیش‌فرض را بررسی می‌کند.
    """
    from database import db

    if bypass_admin:
        try:
            if await db.is_admin(user_id):
                return []
        except Exception:
            pass

    channels_to_check = []
    try:
        db_channels = await db.list_channels()
        for ch in db_channels:
            channels_to_check.append({
                "chat_id": ch["chat_id"],
                "username": (ch["username"] or "").lstrip("@"),
                "title": ch["title"] or ch["username"] or "کانال اسپانسر",
            })
    except Exception:
        pass

    # اگر هیچ کانالی در دیتابیس ثبت نشده بود ولی کانال پیش‌فرض تعریف شده بود
    if not channels_to_check and DEFAULT_FORCED_CHANNEL:
        uname = DEFAULT_FORCED_CHANNEL.lstrip("@")
        channels_to_check.append({
            "chat_id": f"@{uname}",
            "username": uname,
            "title": uname,
        })

    missing = []
    for ch in channels_to_check:
        target = ch["chat_id"]
        if not str(target).startswith("-") and not str(target).startswith("@"):
            target = f"@{target}"
        try:
            member = await bot.get_chat_member(target, int(user_id))
            if member.status in ("left", "kicked", "restricted"):
                if member.status == "restricted" and getattr(member, "is_member", False):
                    continue
                missing.append(ch)
        except Exception:
            # در صورتی که ربات هنوز در کانال ادمین نشده باشد، خطا را رد می‌کند تا ربات قفل نشود
            continue

    return missing
