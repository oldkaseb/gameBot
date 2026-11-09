"""دستورات متنی فارسی (بدون /)"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

router = Router(name="persian_cmds")

# ─────────── نگاشت فارسی → شناسه
COMMANDS = {
    # استارت و منو
    "شروع": "start",
    "استارت": "start",
    "منو": "menu",
    "خانه": "menu",
    "بازی": "rsgame",
    "بازی‌ها": "rsgame",
    "بازیها": "rsgame",
    "پنل": "rsgame",
    # راهنما
    "راهنما": "help",
    "کمک": "help",
    "help": "help",
    # زبان
    "زبان": "lang",
    "language": "lang",
    "lang": "lang",
    # وضعیت
    "وضعیت": "status",
    "پروفایل": "status",
    "پروفايل": "status",
    # پشتیبانی
    "پشتیبانی": "support",
    "پشتيباني": "support",
    # پینگ
    "پینگ": "ping",
    "ping": "ping",
    # لغو
    "لغو": "cancel",
    "کنسل": "cancel",
    "cancel": "cancel",
    # توقف همه بازی‌ها
    "توقف": "stop",
    "توقف بازی": "stop",
    "stop": "stop",
    # ادمین
    "ادمین": "admin",
    "پنل ادمین": "admin",
    "مدیر": "admin",
    # آمار
    "آمار": "stats",
    "امار": "stats",
    "stats": "stats",
    # بکاپ
    "بکاپ": "backup",
    "backup": "backup",
    # اشتراک
    "اشتراک": "subscription",
    "عضویت": "subscription",
    "subscription": "subscription",
}


@router.message(F.chat.type.in_({"private", "group", "supergroup"}))
async def dispatch(message: Message, bot, **kwargs):
    """همه پیام‌های متنی را بررسی می‌کند و اگر با دستور فارسی مطابقت داشت اجرا می‌کند."""
    text = (message.text or "").strip()
    if not text:
        return

    # فقط اگر دقیقاً برابر یکی از کلیدها باشد
    cmd_id = COMMANDS.get(text)
    if not cmd_id:
        return

    # دیسپچ بر اساس شناسه
    from main import (
        cmd_start, cmd_lang, _build_main_menu,
    )
    from database import db

    uid = message.from_user.id
    lang = "fa"

    try:
        from langs import get_user_lang
        lang = get_user_lang(uid)
    except Exception:
        pass

    # ─── استارت
    if cmd_id == "start":
        await cmd_start(message)
        return

    # ─── منو
    if cmd_id == "menu":
        text_menu, markup = await _build_main_menu(uid, message.from_user.first_name or "دوست")
        await message.answer(text_menu, reply_markup=markup)
        return

    # ─── زبان
    if cmd_id == "lang":
        await cmd_lang(message)
        return

    # ─── بازی‌ها
    if cmd_id == "rsgame":
        # پنل بازی‌ها را از games/panel.py صدا بزن
        from games.panel import show_panel
        await show_panel(message)
        return

    # ─── راهنما
    if cmd_id == "help":
        from emojis import E
        from utils.premium import back_btn, kb
        text_help = (
            f"{E.INFO} <b>راهنمای راینوبازی</b>\n\n"
            f"{E.GAME} <b>بازی‌ها:</b>\n"
            f"• بنویسید <code>بازی</code> یا <code>/rsgame</code> تا پنل باز شود.\n\n"
            f"{E.SPARK} <b>دستورات فارسی:</b>\n"
            f"• <code>شروع</code> — منوی اصلی\n"
            f"• <code>بازی</code> — پنل بازی‌ها\n"
            f"• <code>زبان</code> — تغییر زبان\n"
            f"• <code>وضعیت</code> — پروفایل شما\n"
            f"• <code>پشتیبانی</code> — ارتباط با ما\n"
            f"• <code>توقف</code> — لغو همه بازی‌ها (ادمین گروه)\n"
            f"• <code>لغو</code> — لغو عملیات فعلی\n\n"
            f"{E.CROWN} <b>ادمین‌ها:</b>\n"
            f"• <code>ادمین</code> — پنل ادمین\n"
            f"• <code>آمار</code> — آمار ربات\n"
            f"• <code>بکاپ</code> — بکاپ دیتابیس"
        )
        await message.answer(text_help, reply_markup=kb([[back_btn(uid)]]))
        return

    # ─── وضعیت
    if cmd_id == "status":
        user = await db.get_user(uid)
        if not user:
            await message.answer("❌ کاربر یافت نشد.")
            return
        from emojis import E
        from utils.premium import back_btn, kb
        from langs import t
        # محاسبه روز باقی‌مانده
        from datetime import datetime, timezone
        end = user["subscription_end"]
        if end and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        days = max(0, (end - datetime.now(timezone.utc)).days) if end else 0

        text_status = (
            f"{E.CROWN} <b>{t('admin_panel', lang) if False else 'پروفایل شما'}</b>\n\n"
            f"{E.DISGUISE} نام: <b>{user['full_name'] or '—'}</b>\n"
            f"{E.PIN} یوزرنیم: @{user['username'] or '—'}\n"
            f"{E.INFO} آیدی: <code>{uid}</code>\n"
            f"{E.CAL} عضویت: {days} روز مانده\n"
            f"{E.SPARK} ایموجی‌های فعال: {user.get('enabled_emoji_count', 0) or 0}"
        )
        await message.answer(text_status, reply_markup=kb([[back_btn(uid)]]))
        return

    # ─── پشتیبانی
    if cmd_id == "support":
        from emojis import E
        from utils.premium import btn, back_btn, kb
        import os
        support = os.getenv("SUPPORT_USERNAME", "ImKasebBot").lstrip("@")
        await message.answer(
            f"{E.MEGA} <b>پشتیبانی</b>\n\n{E.LINK} @{support}",
            reply_markup=kb([
                [btn(f"{E.WAVE} ارتباط با پشتیبانی", url=f"https://t.me/{support}", style="primary")],
                [back_btn(uid)],
            ]),
        )
        return

    # ─── پینگ
    if cmd_id == "ping":
        import time
        start = time.time()
        sent = await message.answer("…")
        elapsed = (time.time() - start) * 1000
        from emojis import E
        await sent.edit_text(f"{E.ZAP} پینگ: <b>{elapsed:.0f}</b> ms")
        return

    # ─── لغو
    if cmd_id == "cancel":
        from aiogram.fsm.context import FSMContext
        # ساده — پیام را می‌فرستیم و FSM main خودش مدیریت می‌کند
        await message.answer("✅ لغو شد.")
        return

    # ─── توقف همه بازی‌ها (گروه)
    if cmd_id == "stop":
        if message.chat.type == ChatType.PRIVATE:
            await message.answer("این دستور فقط در گروه‌ها کار می‌کند.")
            return
        from games.stop import stop_all
        await stop_all(message)
        return

    # ─── اشتراک
    if cmd_id == "subscription":
        await message.answer(
            "برای مدیریت اشتراک، از پنل اصلی استفاده کنید.",
        )
        return

    # ─── ادمین
    if cmd_id == "admin":
        from admin.panel import open_panel
        await open_panel(message)
        return

    # ─── آمار
    if cmd_id == "stats":
        from admin.panel import open_stats
        await open_stats(message)
        return

    # ─── بکاپ
    if cmd_id == "backup":
        from admin.backup import cmd_backup
        await cmd_backup(message)
        return
