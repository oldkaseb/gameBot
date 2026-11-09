# -*- coding: utf-8 -*-
"""ربات راینوبازی — نسخه ۲.۰
aiogram 3 + asyncpg + ۷ زبان + ایموجی پریمیوم
"""

from __future__ import annotations
import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from emojis import E
from langs import t, get_user_lang
from utils.premium import btn, primary, success, danger, back_btn, kb
from utils.commands import router as persian_cmd_router
from database import db
from games import register_all_games
from admin.panel import router as admin_router, register_admin_commands

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rhino")

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_IDS = {7662192190, 6041119040}


# ── منوی اصلی
async def main_menu(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)
    text = (
        f"{E.PARTY}{E.SPARK} <b>{t('welcome', lang, name=message.from_user.first_name)}</b>\n\n"
        f"{E.GAME} {t('game_panel', lang, name=message.from_user.first_name)}"
    )
    rows = [
        [success(f"{E.TROPHY} {t('btn_group', lang)}",  f"rsgame_cat_board_{uid}"),
         primary(f"{E.TARGET} {t('btn_single', lang)}", f"rsgame_cat_single_{uid}")],
        [primary(f"{E.MIC} {t('btn_typing', lang)}",    f"rsgame_cat_typing_{uid}"),
         danger(f"{E.GHOST} {t('btn_anon', lang)}",     f"rsgame_cat_anon_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} پنل ادمین", "adm:panel")])
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


# ── استارت
async def cmd_start(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)
    # اگر زبان انتخاب نشده
    rows = [[btn(v, f"set_lang:{k}")] for k, v in __import__("langs").LANGS.items()]
    await message.answer(
        f"{E.WAVE}{E.SPARK} {t('choose_lang', lang)}",
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


# ── اجرا
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await db.connect()
    await db.init()

    register_all_games(dp)
    register_admin_commands(dp)

    dp.include_router(persian_cmd_router)

    # callback ساده برای زبان
    from aiogram import F
    from aiogram.types import CallbackQuery
    from langs import set_user_lang

    @dp.callback_query(F.data.startswith("set_lang:"))
    async def _set_lang(cb: CallbackQuery):
        lang = cb.data.split(":")[1]
        set_user_lang(cb.from_user.id, lang)
        await cb.message.edit_text(t("lang_saved", lang))
        await main_menu(cb.message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
