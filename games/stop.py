"""توقف همه بازی‌ها در گروه"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ChatType, ParseMode

from emojis import E
from langs import t, get_user_lang
from . import state

router = Router(name="stop")

ALL_GAMES = [
    "hangman", "typing", "guess_number", "hokm", "dooz", "doz4p",
    "connect4", "rps", "memory", "2048", "samegame", "spuzzle", "gardone",
]


@router.message(Command("stop"))
@router.message(F.text.in_({"توقف", "لغو بازی", "stop"}))
async def stop_all(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        return
    uid = message.from_user.id
    lang = get_user_lang(uid)

    # فقط ادمین گروه یا مالک ربات
    try:
        member = await message.chat.get_member(uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await message.reply(f"{E.CROSS} {t('only_admin', lang)}")
        return

    total = 0
    for g in ALL_GAMES:
        total += state.clear_chat(g, message.chat.id)

    if total:
        await message.reply(
            f"{E.OK2} {t('stopped_n_games', lang, n=total)}",
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.reply(f"{E.INFO} {t('no_active_games', lang)}")
