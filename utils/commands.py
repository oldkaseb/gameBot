"""تبدیل دستورات متنی فارسی به هندلرها (بدون /)"""

from aiogram import Router, F
from aiogram.types import Message

router = Router(name="persian_commands")

# نگاشت دستور متنی فارسی → شناسه داخلی
PERSIAN_COMMANDS = {
    "شروع":     "start",
    "استارت":   "start",
    "بازی":     "rsgame",
    "بازی‌ها":  "rsgame",
    "بازیها":   "rsgame",
    "پنل":      "rsgame",
    "لغو":      "cancel",
    "کنسل":     "cancel",
    "توقف":     "stop",
    "تایم‌اوت": "stop",
    "راهنما":   "help",
    "پینگ":     "ping",
    "زبان":     "lang",
    "ادمین":    "admin",
    "پنل ادمین":"admin",
    "آمار":     "stats",
    "امار":     "stats",
    "بکاپ":     "backup",
    "پشتیبان":  "support",
}

# Router جدا برای دستورات متنی
@router.message(F.text.func(lambda t: (t or "").strip() in PERSIAN_COMMANDS))
async def dispatch_persian_command(message: Message, bot):
    cmd_id = PERSIAN_COMMANDS[(message.text or "").strip()]
    # نگاشت داخلی → فراخوانی مستقیم
    from main import COMMAND_DISPATCH
    handler = COMMAND_DISPATCH.get(cmd_id)
    if handler:
        await handler(message, bot)
