# -*- coding: utf-8 -*-
"""main.py — ربات بازی راینو (نسخه اصلاح‌شده: فعال‌سازی قطعی همه دکمه‌های منو در گروه و مینی‌اپ)"""

import asyncio
import html
import logging
import os
from urllib.parse import urlencode

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery,
    WebAppInfo, InlineKeyboardButton,
)

from emojis import (
    E, render_emojis, strip_custom_emoji_tags, extract_emoji_ids,
    BASE_MAP, EMOJI_ID_RE,
)
from langs import LANGS, t, get_user_lang, set_user_lang
from utils.premium import btn, success, primary, danger, kb
from utils.commands import router as persian_cmd_router
from database import db
from runtime import check_forced_join, get_bot_username, set_bot_username
from games import register_all_games
from games.state import cleanup_loop
from games.stop import router as stop_router
from games.anon import router as anon_router
from games.inline_games import router as inline_games_router
from admin.panel import router as admin_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rhino")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_IDS = {7662192190, 6041119040}
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════

def _clean_lang_label(label: str) -> str:
    parts = (label or "").split(" ", 1)
    clean_name = parts[1] if len(parts) > 1 else label
    return f"{E.GLOBE} {clean_name}".strip()


def _safe_name(name: str) -> str:
    return html.escape(name or "Player")


class EmojiBot(Bot):
    async def __call__(self, method, request_timeout=None):
        for attr in ("text", "caption"):
            val = getattr(method, attr, None)
            if isinstance(val, str) and "[E:" in val:
                try:
                    setattr(method, attr, render_emojis(val))
                except Exception:
                    pass

        try:
            return await super().__call__(method, request_timeout)
        except TelegramBadRequest as e:
            err = str(e)
            if any(k in err for k in ("DOCUMENT_INVALID", "ENTITY_TEXT_INVALID", "CUSTOM_EMOJI", "BUTTON_ICON")):
                log.warning(f"Telegram emoji/button fallback triggered ({err})")
                for attr in ("text", "caption"):
                    val = getattr(method, attr, None)
                    if isinstance(val, str) and ("<tg-emoji" in val or "[E:" in val):
                        try:
                            setattr(method, attr, strip_custom_emoji_tags(val, keep_unicode=False))
                        except Exception:
                            pass
                return await super().__call__(method, request_timeout)
            raise


# ═══════════════════════════════════════════════
# Forced Join UI
# ═══════════════════════════════════════════════

def _join_kb(channels, lang: str = "fa"):
    rows = []
    for ch in channels:
        label = f"{E.LINK} {t('force_join_btn', lang)} — {ch['title'] or ch['chat_id']}"
        if ch["username"]:
            url = f"https://t.me/{ch['username'].lstrip('@')}"
            rows.append([primary(label, url=url)])
        else:
            rows.append([success(label, "check_join")])
    rows.append([success(f"{E.REFRESH} {t('force_join_check', lang)}", "check_join")])
    return kb(rows)


class ForcedJoinMiddleware(BaseMiddleware):
    EXEMPT_CALLBACK_PREFIXES = (
        "check_join", "set_lang:", "lang_menu", "donate", "menu",
    )
    EXEMPT_TEXT_STARTS = ("/start", "/cancel", "/help")
    EXEMPT_TEXTS = ("شروع", "استارت", "زبان", "language", "lang", "start")

    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(self, handler, event, data):
        from_user = getattr(event, "from_user", None)
        if not from_user:
            return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data:
            for p in self.EXEMPT_CALLBACK_PREFIXES:
                if event.data.startswith(p):
                    return await handler(event, data)

        if isinstance(event, Message) and event.text:
            txt = event.text.strip()
            if any(txt.startswith(p) for p in self.EXEMPT_TEXT_STARTS):
                return await handler(event, data)
            if txt in self.EXEMPT_TEXTS:
                return await handler(event, data)

        try:
            missing = await check_forced_join(self.bot, from_user.id)
        except Exception:
            return await handler(event, data)

        if not missing:
            return await handler(event, data)

        lang = get_user_lang(from_user.id)
        if isinstance(event, CallbackQuery):
            try:
                await event.answer(t("force_join_alert", lang), show_alert=True)
            except Exception:
                pass
        elif isinstance(event, Message):
            try:
                await event.answer(
                    t("force_join_msg", lang),
                    reply_markup=_join_kb(missing, lang),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
        return


class GameGuard(BaseMiddleware):
    PREFIXES = {
        "hokm": "hokm", "dooz": "dooz", "doz4p": "doz4p",
        "connect4": "connect4", "rps": "rps", "memory": "memory",
        "2048": "2048", "samegame": "samegame", "spuzzle": "spuzzle",
        "hangman": "hangman", "typing": "typing", "guess": "number_guess",
        "gardone": "gardone",
    }

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery) and event.data:
            for key, gtype in self.PREFIXES.items():
                if key in event.data:
                    try:
                        if not await db.is_game_enabled(gtype):
                            await event.answer("این بازی فعلاً غیرفعال است.", show_alert=True)
                            return
                    except Exception:
                        pass
                    break
        return await handler(event, data)


# ═══════════════════════════════════════════════
# ساخت منوی بازی‌ها (مستقیم داخل گروه بدون ارسال به پیوی)
# ═══════════════════════════════════════════════

def _app_button(text: str, game: str, chat_id: int, style_fn=primary) -> InlineKeyboardButton:
    """دکمه باز شدن مستقیم Mini App در داخل گروه"""
    params = urlencode({"game": game, "chat": chat_id})
    return style_fn(text, web_app_url=f"{MINI_APP_URL}/?{params}")


def _build_games_menu(uid: int, chat_id: int):
    """
    ساختار کامل دکمه‌ها:
    - بازی‌های انفرادی و سرعتی مستقیم با Mini App باز می‌شوند.
    - بازی‌های چندنفره لابی گروهی تشکیل می‌دهند.
    - گردونه شانس وارد لابی و شمارش برندگان می‌شود.
    """
    rows = [
        # پازلی و انفرادی (مینی‌اپ مستقیم)
        [_app_button(f"{E.PUZZLE} 2048", "2048", chat_id, primary),
         _app_button(f"{E.PUZZLE} پازل کشویی", "spuzzle", chat_id, primary)],
        [_app_button(f"{E.SPARK} جفت‌ها", "samegame", chat_id, primary)],

        # چندنفره (تشکیل لابی در گروه)
        [primary(f"{E.TARGET} دوز ۲ نفره", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} دوز ۴ نفره", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} چهار در ردیف", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} حکم ۴ نفره", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} سنگ کاغذ قیچی", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} بازی حافظه", f"lobby_memory_{uid}")],

        # سرعتی و تایپی و هوش (مینی‌اپ مستقیم)
        [_app_button(f"{E.MIC} تایپ سرعتی", "typing", chat_id, primary),
         _app_button(f"{E.BRAIN} حدس کلمه", "hangman", chat_id, primary)],
        [_app_button(f"{E.TARGET} حدس عدد", "guess", chat_id, primary)],

        # گردونه شانس گروهی
        [success(f"{E.TARGET} گردونه شانس و قرعه‌کشی", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} بستن منو", f"close_menu_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} پنل ادمین", "adm:panel")])

    text = (
        f"{E.GAME}{E.SPARK} <b>سالن بازی‌های گروهی راینو</b>\n\n"
        f"بازی مورد نظر را انتخاب کنید تا مستقیماً اجرا یا لابی آن تشکیل شود:"
    )
    return text, kb(rows)


# ═══════════════════════════════════════════════
# هندلر دستورات شروع و بازی
# ═══════════════════════════════════════════════

async def cmd_start(message: Message, command=None):
    uid = message.from_user.id
    cid = message.chat.id

    user = await db.get_user(uid)
    if not user:
        await db.upsert_user(
            uid,
            message.from_user.username or "",
            message.from_user.first_name or "",
        )

    # بررسی جوین اجباری
    try:
        missing = await check_forced_join(message.bot, uid)
    except Exception:
        missing = []

    if missing:
        await message.answer(
            t("force_join_msg", "fa"),
            reply_markup=_join_kb(missing, "fa"),
            parse_mode=ParseMode.HTML,
        )
        return

    # تمام پیام‌ها (چه گروه و چه پیوی) مستقیماً به سالن بازی‌ها متصل می‌شوند
    text, markup = _build_games_menu(uid, cid)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════
# سرور Uvicorn و FastApi
# ═══════════════════════════════════════════════

async def _start_health_server(port: int = 8080):
    try:
        import uvicorn
        from webapp.backend.main import app as webapp_fastapi

        config = uvicorn.Config(
            webapp_fastapi,
            host="0.0.0.0",
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        log.info(f"Mini App FastAPI server running on :{port}")
        return server
    except Exception as e:
        log.warning(f"FastAPI server fallback error: {e}")
        return None


# ═══════════════════════════════════════════════
# Main Function
# ═══════════════════════════════════════════════

async def main():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set!")
        return

    bot = EmojiBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    await db.connect()
    await db.init()

    me = await bot.get_me()
    set_bot_username(me.username or "bot")
    log.info(f"Bot connected: @{get_bot_username()}")

    # ثبت روترها
    register_all_games(dp)
    dp.include_router(anon_router)
    dp.include_router(stop_router)
    dp.include_router(inline_games_router)
    dp.include_router(admin_router)
    dp.include_router(persian_cmd_router)

    forced = ForcedJoinMiddleware(bot)
    dp.message.outer_middleware(forced)
    dp.callback_query.outer_middleware(forced)
    dp.callback_query.outer_middleware(GameGuard())

    @dp.message(CommandStart())
    async def _start(msg: Message, command=None):
        await cmd_start(msg, command)

    @dp.message(F.text.in_({
        "شروع", "استارت", "start", "بازی", "بازی‌ها", "بازیها", "پنل", "games", "panel"
    }))
    async def _start_text(msg: Message):
        await cmd_start(msg)

    @dp.callback_query(F.data == "check_join")
    async def _check_join(cb: CallbackQuery):
        missing = await check_forced_join(cb.bot, cb.from_user.id)
        if missing:
            await cb.answer(t("not_member", "fa"), show_alert=True)
            return
        await cb.answer("عضویت تایید شد!")
        text, markup = _build_games_menu(cb.from_user.id, cb.message.chat.id)
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            await cb.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)

    @dp.callback_query(F.data == "menu")
    async def _menu(cb: CallbackQuery):
        await cb.answer()
        text, markup = _build_games_menu(cb.from_user.id, cb.message.chat.id)
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    @dp.callback_query(F.data.startswith("close_menu_"))
    async def _close_menu(cb: CallbackQuery):
        await cb.answer()
        try:
            await cb.message.delete()
        except Exception:
            pass

    asyncio.create_task(cleanup_loop(bot))
    health_runner = await _start_health_server(int(os.getenv("PORT", "8080")))

    log.info("Bot starting polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message", "edited_message", "callback_query",
                "inline_query", "chosen_inline_result",
                "pre_checkout_query", "successful_payment",
            ],
        )
    finally:
        if health_runner:
            health_runner.should_exit = True
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
