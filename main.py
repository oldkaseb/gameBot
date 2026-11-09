# -*- coding: utf-8 -*-
"""main.py — ربات بازی راینو"""

import asyncio
import logging
import os

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from emojis import E
from langs import LANGS, t, get_user_lang, set_user_lang
from utils.premium import btn, success, primary, danger, kb
from utils.commands import router as persian_cmd_router
from database import db
from games import register_all_games
from games.state import cleanup_loop
from games.stop import router as stop_router
from games.anon import router as anon_router
from games.leaderboard import router as lb_router
from admin.panel import router as admin_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rhino")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_IDS = {7662192190, 6041119040}


class GameGuard(BaseMiddleware):
    PREFIXES = {
        "hokm_start_": "hokm", "dooz_start_": "dooz",
        "doz4p_start_": "doz4p", "connect4_start_": "connect4",
        "rps_start_": "rps", "memory_start_": "memory",
        "2048_start_": "2048", "samegame_start_": "samegame",
        "spuzzle_start_": "spuzzle", "hads_kalame_start_": "hangman",
        "type_start_": "typing", "hads_addad_start_": "number_guess",
        "gardone_start_": "gardone", "gharch_start_": "gharch",
        "eteraf_start_": "eteraf",
    }

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery) and event.data:
            for prefix, gtype in self.PREFIXES.items():
                if event.data.startswith(prefix):
                    try:
                        if not await db.is_game_enabled(gtype):
                            await event.answer(
                                "🔒 این بازی موقتاً غیرفعال است.",
                                show_alert=True,
                            )
                            return
                    except Exception:
                        pass
                    break
        return await handler(event, data)


async def _build_main_menu(uid: int, name: str):
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
        [success(f"{E.TROPHY} 🏆 برترین‌ها", "lb_menu")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def cmd_start(message: Message, command=None):
    uid = message.from_user.id
    payload = (command.args if command else "") or ""

    # دیپ‌لینک ناشناس → anon_router جواب می‌دهد
    if payload.startswith("gharch_") or payload.startswith("eteraf_"):
        return

    user = await db.get_user(uid)
    is_new = user is None

    if is_new:
        await db.upsert_user(
            uid,
            message.from_user.username or "",
            message.from_user.first_name or "",
        )

    # زبان از DB
    user_lang = user["language"] if user else None
    if user_lang:
        set_user_lang(uid, user_lang)

    # اگر کاربر جدید است یا زبان ندارد → انتخاب زبان
    if is_new or not user_lang:
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
        await db.set_language(cb.from_user.id, lang)
    except Exception:
        pass
    await cb.answer(t("lang_saved", lang))
    text, markup = await _build_main_menu(
        cb.from_user.id, cb.from_user.first_name or "دوست"
    )
    try:
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            await cb.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def cmd_lang(message: Message):
    rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
    await message.answer(
        t("choose_lang", get_user_lang(message.from_user.id)),
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


async def _start_health_server(port: int = 8080):
    """سرور HTTP سبک برای healthcheck در Coolify"""
    try:
        from aiohttp import web

        async def health(_request):
            return web.Response(text="ok")

        app = web.Application()
        app.router.add_get("/", health)
        app.router.add_get("/health", health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        log.info(f"✅ Health server on :{port}")
        return runner
    except Exception as e:
        log.warning(f"⚠️ Health server failed: {e}")
        return None


async def main():
    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN not set!")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    await db.connect()
    await db.init()

    # ───── ثبت Routerها (ترتیب مهم)
    register_all_games(dp)          # بازی‌ها
    dp.include_router(anon_router)  # deep link ناشناس
    dp.include_router(stop_router)  # توقف بازی‌ها
    dp.include_router(lb_router)    # leaderboard
    dp.include_router(admin_router) # پنل ادمین
    dp.include_router(persian_cmd_router)  # دستورات فارسی

    # Middleware محافظ بازی‌ها
    dp.callback_query.outer_middleware(GameGuard())

    # ───── هندلرهای اصلی
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

    # ⚠️ این هندلر قبلاً گم بود — منوی اصلی
    @dp.callback_query(F.data == "menu")
    async def _menu(cb: CallbackQuery):
        await cb.answer()
        text, markup = await _build_main_menu(
            cb.from_user.id, cb.from_user.first_name or "دوست"
        )
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await cb.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            except Exception:
                pass

    # Background tasks
    asyncio.create_task(cleanup_loop(bot))

    # Health server
    health_runner = await _start_health_server(int(os.getenv("PORT", "8080")))

    log.info("🚀 Bot starting…")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if health_runner:
            await health_runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
