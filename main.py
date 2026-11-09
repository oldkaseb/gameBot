# -*- coding: utf-8 -*-
"""ربات راینوبازی ۲.۰ — آپدیت‌شده با همه بازی‌ها + ۷ زبان"""

from __future__ import annotations
import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from emojis import E
from langs import LANGS, t, get_user_lang, set_user_lang
from utils.premium import btn, success, primary, danger, kb
from utils.commands import router as persian_cmd_router
from database import db
from games import register_all_games
from games.state import cleanup_loop
from games.stop import router as stop_router
from games.anon import router as anon_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rhino")

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_IDS = {7662192190, 6041119040}


async def _build_main_menu(uid: int, name: str) -> tuple[str, "InlineKeyboardMarkup"]:
    lang = get_user_lang(uid)
    text = (
        f"{E.PARTY}{E.SPARK} <b>{t('welcome', lang, name=name)}</b>\n\n"
        f"{E.GAME} {t('game_panel', lang)}"
    )
    rows = [
        [success(f"{E.TROPHY} {t('btn_group', lang)}",  f"rsgame_cat_board_{uid}"),
         primary(f"{E.TARGET} {t('btn_single', lang)}", f"rsgame_cat_single_{uid}")],
        [primary(f"{E.MIC} {t('btn_typing', lang)}",    f"rsgame_cat_typing_{uid}"),
         danger(f"{E.GHOST} {t('btn_anon', lang)}",     f"rsgame_cat_anon_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def cmd_start(message: Message, command=None):
    uid = message.from_user.id
    payload = (command.args if command else "") or ""

    # اگر دیپ‌لینک ناشناس است، بگذار anon_router جواب بدهد
    if payload.startswith("gharch_") or payload.startswith("eteraf_"):
        return

    user = await db.get_user(uid)
    if not user:
        await db.upsert_user(uid, message.from_user.username, message.from_user.first_name or "")

    # اگر زبان انتخاب نشده، انتخاب زبان
    if not user or not user.get("language"):
        rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
        await message.answer(
            f"{E.WAVE}{E.SPARK} {t('choose_lang', 'fa')}",
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
        )
        return

    text, markup = await _build_main_menu(uid, message.from_user.first_name or "دوست")
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def set_lang_cb(cb: CallbackQuery):
    lang = cb.data.split(":")[1]
    set_user_lang(cb.from_user.id, lang)
    try:
        await db.pool.execute("UPDATE users SET language=$1 WHERE user_id=$2", lang, cb.from_user.id)
    except Exception:
        pass
    await cb.answer(t("lang_saved", lang))
    text, markup = await _build_main_menu(cb.from_user.id, cb.from_user.first_name or "دوست")
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def cmd_lang(message: Message):
    """تغییر زبان"""
    uid = message.from_user.id
    rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
    await message.answer(t("choose_lang", uid), reply_markup=kb(rows), parse_mode=ParseMode.HTML)


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await db.connect()
    await db.init()

    # ثبت همه بازی‌ها
    register_all_games(dp)
    dp.include_router(anon_router)
    dp.include_router(stop_router)
    dp.include_router(persian_cmd_router)

    # هندلرهای اصلی
    @dp.message(CommandStart())
    async def _start(msg: Message, command=None):
        await cmd_start(msg, command)

    @dp.message(F.text.in_({"شروع", "استارت"}))
    async def _start_p(msg: Message):
        await cmd_start(msg)

    @dp.message(F.text.in_({"زبان", "language", "lang"}))
    async def _lang(msg: Message):
        await cmd_lang(msg)

    @dp.callback_query(F.data.startswith("set_lang:"))
    async def _setlang(cb: CallbackQuery):
        await set_lang_cb(cb)

    # حلقه پاکسازی بازی‌ها
    asyncio.create_task(cleanup_loop(bot))

    log.info("Bot starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
