"""دستورات متنی فارسی (بدون /)"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

router = Router(name="persian_cmds")

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
    # ⚠️ ادمین/آمار/بکاپ اینجا نیست — admin_router آن‌ها را می‌گیرد
}


@router.message(F.chat.type.in_({"private", "group", "supergroup"}))
async def dispatch(message: Message, **kwargs):
    text = (message.text or "").strip()
    if not text:
        return

    cmd_id = COMMANDS.get(text)
    if not cmd_id:
        return

    from main import cmd_start, cmd_lang, _build_main_menu
    from database import db

    uid = message.from_user.id
    lang = "fa"

    try:
        from langs import get_user_lang
        lang = get_user_lang(uid)
    except Exception:
        pass

    if cmd_id == "start":
        await cmd_start(message)
        return

    if cmd_id == "menu":
        text_menu, markup = await _build_main_menu(uid, message.from_user.first_name or "دوست")
        await message.answer(text_menu, reply_markup=markup)
        return

    if cmd_id == "lang":
        await cmd_lang(message)
        return

    if cmd_id == "rsgame":
        from games.panel import show_panel
        await show_panel(message)
        return

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

    if cmd_id == "status":
        user = await db.get_user(uid)
        if not user:
            await message.answer("❌ کاربر یافت نشد.")
            return
        from emojis import E
        from utils.premium import back_btn, kb
        from database import db as _db

        try:
            wins = await _db.pool.fetch(
                "SELECT game_type, wins FROM game_wins WHERE user_id=$1 ORDER BY wins DESC LIMIT 5",
                uid,
            )
        except Exception:
            wins = []
        total_wins = sum(w["wins"] for w in wins)
        top_txt = ""
        for w in wins[:3]:
            top_txt += f"    • {w['game_type']}: {w['wins']}\n"
        top_txt = top_txt or "    —\n"

        text_status = (
            f"{E.CROWN} <b>پروفایل شما</b>\n\n"
            f"{E.DISGUISE} نام: <b>{user['first_name'] or '—'}</b>\n"
            f"{E.PIN} یوزرنیم: @{user['username'] or '—'}\n"
            f"{E.INFO} آیدی: <code>{uid}</code>\n"
            f"{E.TROPHY} مجموع بردها: <b>{total_wins}</b>\n"
            f"{E.CHART} <b>برترین بازی‌ها:</b>\n{top_txt}"
        )
        await message.answer(text_status, reply_markup=kb([[back_btn(uid)]]))
        return

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

    if cmd_id == "ping":
        import time
        start = time.time()
        sent = await message.answer("…")
        elapsed = (time.time() - start) * 1000
        from emojis import E
        await sent.edit_text(f"{E.ZAP} پینگ: <b>{elapsed:.0f}</b> ms")
        return

    if cmd_id == "cancel":
        await message.answer("✅ لغو شد.")
        return

    if cmd_id == "stop":
        if message.chat.type == ChatType.PRIVATE:
            await message.answer("این دستور فقط در گروه‌ها کار می‌کند.")
            return
        from games.stop import stop_all
        await stop_all(message)
        return
