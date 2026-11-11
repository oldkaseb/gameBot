# -*- coding: utf-8 -*-
"""main.py — ربات بازی راینو"""

import asyncio
import html
import logging
import os
from urllib.parse import urlencode

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
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
MINI_APP_SHORT_NAME = os.environ.get("MINI_APP_SHORT_NAME", "").strip()


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
                log.warning(f"Telegram emoji/button fallback triggered ({err}) — retrying cleanly")
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
# Forced Join UI & Middlewares
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
        "hokm_start_": "hokm", "dooz_start_": "dooz",
        "doz4p_start_": "doz4p", "connect4_start_": "connect4",
        "rps_start_": "rps", "memory_start_": "memory",
        "2048_start_": "2048", "samegame_start_": "samegame",
        "spuzzle_start_": "spuzzle", "hads_kalame_start_": "hangman",
        "type_start_": "typing", "hads_addad_start_": "number_guess",
        "gardone_start_": "gardone", "gharch_start_": "gharch",
        "eteraf_start_": "eteraf",
        "gcard_": "__gcard__",
        "lobby_": "__lobby__",
    }

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery) and event.data:
            for prefix, gtype in self.PREFIXES.items():
                if event.data.startswith(prefix):
                    if gtype in ("__gcard__", "__lobby__"):
                        parts = event.data.split("_")
                        if len(parts) >= 2:
                            gtype = "number_guess" if parts[1] == "guess" else parts[1]
                        else:
                            break
                    try:
                        if not await db.is_game_enabled(gtype):
                            await event.answer(
                                t("game_disabled", get_user_lang(event.from_user.id)),
                                show_alert=True,
                            )
                            return
                    except Exception:
                        pass
                    break
        return await handler(event, data)


# ═══════════════════════════════════════════════
# منوی اصلی
# ═══════════════════════════════════════════════

async def _build_main_menu(uid: int, name: str, is_pm: bool = False):
    lang = get_user_lang(uid)
    safe_n = _safe_name(name)
    text = (
        f"{E.PARTY}{E.SPARK} <b>{t('welcome', lang, name=safe_n)}</b>\n\n"
        f"{E.GAME} {t('game_panel', lang, name=safe_n)}\n\n{t('choose_game_hint', lang)}"
    )

    rows = [
        [primary(f"{E.PUZZLE} {t('game_2048_title', lang)}", f"gcard_2048_{uid}"),
         primary(f"{E.PUZZLE} {t('game_spuzzle', lang)}", f"gcard_spuzzle_{uid}")],
        [primary(f"{E.SPARK} {t('game_samegame', lang)}", f"gcard_samegame_{uid}")],
        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],
        [primary(f"{E.MIC} {t('game_typing', lang)}", f"gcard_typing_{uid}"),
         primary(f"{E.BRAIN} {t('game_hangman', lang)}", f"gcard_hangman_{uid}")],
        [primary(f"{E.TARGET} {t('game_guess_num', lang)}", f"gcard_guess_{uid}")],
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def _build_pm_welcome(uid: int, name: str):
    lang = get_user_lang(uid)
    bot_username = get_bot_username()
    safe_n = _safe_name(name)

    text = (
        f"{E.WAVE}{E.SPARK} <b>{t('pm_welcome_title', lang, name=safe_n)}</b>\n\n"
        f"{E.GAME} {t('pm_welcome_body', lang)}\n\n"
        f"{E.HEART} {t('pm_welcome_donate_hint', lang)}"
    )
    rows = [
        [success(
            f"{E.PLUS} {t('btn_add_to_group', lang)}",
            url=f"https://t.me/{bot_username}?startgroup=true",
        )],
        [primary(
            f"{E.GAME} {t('open_game_btn', lang)}",
            "open_pm_games",
        )],
        [primary(f"{E.HEART} {t('btn_donate', lang)}", "donate")],
        [primary(f"{E.GLOBE} {t('btn_change_lang', lang)}", "lang_menu")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def _show_pm_welcome(cb_or_msg, uid: int, name: str, edit: bool = True):
    text, markup = await _build_pm_welcome(uid, name)
    is_cb = isinstance(cb_or_msg, CallbackQuery)
    target_msg = cb_or_msg.message if is_cb else cb_or_msg

    if edit:
        try:
            await target_msg.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            return
        except TelegramBadRequest as e:
            if "not modified" in str(e).lower():
                return
        except Exception:
            pass

    try:
        await target_msg.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.error(f"_show_pm_welcome error: {e}")


# ═══════════════════════════════════════════════
# Start & Language Handlers
# ═══════════════════════════════════════════════

async def cmd_start(message: Message, command=None):
    uid = message.from_user.id
    is_pm = message.chat.type == ChatType.PRIVATE
    payload = ""
    if command and getattr(command, "args", None):
        payload = command.args
    elif message.text and message.text.startswith("/start "):
        payload = message.text.split(" ", 1)[1].strip()

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
        user = await db.get_user(uid)

    user_lang = user["language"] if user else None
    if user_lang:
        set_user_lang(uid, user_lang)
    lang = get_user_lang(uid)

    try:
        missing = await check_forced_join(message.bot, uid)
    except Exception:
        missing = []

    if missing:
        await message.answer(
            t("force_join_msg", lang),
            reply_markup=_join_kb(missing, lang),
            parse_mode=ParseMode.HTML,
        )
        return

    if is_pm and payload.startswith("game_"):
        game = payload[5:]
        if game:
            game_url = f"{MINI_APP_URL}/?game={game}&uid={uid}&lang={lang}"
            await message.answer(
                f"{E.GAME} <b>{t('open_in_pm_title', lang)}</b>\n\n"
                f"{E.INFO} {t('open_in_pm_body', lang)}",
                reply_markup=kb([
                    [success(f"{E.PLAY} {t('open_game_btn', lang)}", web_app_url=game_url)],
                    [danger(f"{E.ARROW} {t('btn_back', lang)}", "menu")],
                ]),
                parse_mode=ParseMode.HTML,
            )
            return

    if is_pm and (is_new or not user_lang):
        rows = [[primary(_clean_lang_label(v), f"set_lang:{k}")] for k, v in LANGS.items()]
        await message.answer(
            f"{E.WAVE}{E.SPARK} {t('choose_lang', 'fa')}",
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
        )
        return

    player_name = message.from_user.first_name or t("player", lang)
    if is_pm:
        await _show_pm_welcome(message, uid, player_name, edit=False)
    else:
        text, markup = await _build_main_menu(uid, player_name, is_pm=False)
        await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def set_lang_cb(cb: CallbackQuery):
    lang = cb.data.split(":")[1]
    if lang not in LANGS:
        await cb.answer(t("error", "fa"), show_alert=True)
        return
    set_user_lang(cb.from_user.id, lang)
    try:
        await db.set_language(cb.from_user.id, lang)
    except Exception:
        pass
    await cb.answer(t("lang_saved", lang))

    is_pm = cb.message.chat.type == ChatType.PRIVATE
    name = cb.from_user.first_name or "دوست"
    if is_pm:
        await _show_pm_welcome(cb, cb.from_user.id, name)
    else:
        text, markup = await _build_main_menu(cb.from_user.id, name, is_pm=False)
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def cmd_lang(message: Message):
    rows = [[primary(_clean_lang_label(v), f"set_lang:{k}")] for k, v in LANGS.items()]
    await message.answer(
        t("choose_lang", get_user_lang(message.from_user.id)),
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════
# Donate Stars
# ═══════════════════════════════════════════════

DONATE_PRESETS = [50, 100, 250, 500, 1000]


class DonateStates(StatesGroup):
    custom_amount = State()


async def _show_donate_menu(cb: CallbackQuery, edit: bool = True):
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    rows = [
        [primary(f"{E.STAR} {n}", f"donate_pay:{n}") for n in DONATE_PRESETS[:3]],
        [primary(f"{E.STAR} {n}", f"donate_pay:{n}") for n in DONATE_PRESETS[3:]],
        [success(f"{E.PLUS} {t('donate_custom', lang)}", "donate_custom")],
        [danger(f"{E.ARROW} {t('btn_back', lang)}", "menu")],
    ]

    text = t("donate_title", lang)
    try:
        if edit:
            await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
        else:
            await cb.message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    except TelegramBadRequest as e:
        if "not modified" not in str(e).lower():
            log.debug(f"donate: {e}")


async def _send_stars_invoice(bot: Bot, chat_id: int, amount: int, uid: int):
    lang = get_user_lang(uid)
    await bot.send_invoice(
        chat_id=chat_id,
        title=t("donate_invoice_title", lang),
        description=t("donate_invoice_desc", lang, n=amount),
        payload=f"donate_{amount}_{uid}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)],
    )


# ═══════════════════════════════════════════════
# Health & MiniApp FastAPI Server
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
        log.info(f"Mini App FastAPI + WebSocket server running on :{port}")
        return server
    except Exception as e:
        log.warning(f"FastAPI server fallback: {e}")
        return None


# ═══════════════════════════════════════════════
# Main
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
        "شروع", "استارت", "start", "بدء", "ابدأ", "başla", "başlat",
        "начать", "старт", "los", "starten", "开始",
    }))
    async def _start_p(msg: Message):
        await cmd_start(msg)

    @dp.message(F.text.in_({"زبان", "language", "lang"}))
    async def _lang(msg: Message):
        await cmd_lang(msg)

    @dp.callback_query(F.data.startswith("set_lang:"))
    async def _setlang(cb: CallbackQuery):
        await set_lang_cb(cb)

    @dp.callback_query(F.data == "open_pm_games")
    async def _open_pm_games(cb: CallbackQuery):
        await cb.answer()
        uid = cb.from_user.id
        name = cb.from_user.first_name or "دوست"
        text, markup = await _build_main_menu(uid, name, is_pm=True)
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            await cb.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)

    @dp.callback_query(F.data == "check_join")
    async def _check_join(cb: CallbackQuery):
        lang = get_user_lang(cb.from_user.id)
        missing = await check_forced_join(cb.bot, cb.from_user.id)
        if missing:
            await cb.answer(t("not_member", lang), show_alert=True)
            try:
                await cb.message.edit_text(
                    t("force_join_msg", lang),
                    reply_markup=_join_kb(missing, lang),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
            return

        await cb.answer(t("lang_saved", lang))
        user = await db.get_user(cb.from_user.id)
        if not user:
            await db.upsert_user(
                cb.from_user.id,
                cb.from_user.username or "",
                cb.from_user.first_name or "",
            )

        name = cb.from_user.first_name or "دوست"
        if cb.message.chat.type == ChatType.PRIVATE:
            await _show_pm_welcome(cb, cb.from_user.id, name)
        else:
            text, markup = await _build_main_menu(cb.from_user.id, name, is_pm=False)
            try:
                await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            except Exception:
                pass

    @dp.callback_query(F.data == "menu")
    async def _menu(cb: CallbackQuery):
        await cb.answer()
        uid = cb.from_user.id
        name = cb.from_user.first_name or "دوست"
        if cb.message.chat.type == ChatType.PRIVATE:
            await _show_pm_welcome(cb, uid, name)
        else:
            text, markup = await _build_main_menu(uid, name, is_pm=False)
            try:
                await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            except TelegramBadRequest as e:
                if "not modified" not in str(e).lower():
                    log.debug(f"menu: {e}")

    @dp.callback_query(F.data == "lang_menu")
    async def _lang_menu(cb: CallbackQuery):
        await cb.answer()
        lang = get_user_lang(cb.from_user.id)
        rows = [[primary(_clean_lang_label(v), f"set_lang:{k}")] for k, v in LANGS.items()]
        rows.append([danger(f"{E.ARROW} {t('btn_back', lang)}", "menu")])
        try:
            await cb.message.edit_text(
                t("choose_lang", lang),
                reply_markup=kb(rows),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    @dp.callback_query(F.data == "donate")
    async def _donate(cb: CallbackQuery):
        await cb.answer()
        await _show_donate_menu(cb)

    @dp.callback_query(F.data.startswith("donate_pay:"))
    async def _donate_pay(cb: CallbackQuery):
        try:
            amount = int(cb.data.split(":")[1])
            if not (1 <= amount <= 10000):
                raise ValueError
        except (ValueError, IndexError):
            await cb.answer("Invalid amount", show_alert=True)
            return
        await cb.answer()
        try:
            await _send_stars_invoice(cb.bot, cb.from_user.id, amount, cb.from_user.id)
        except Exception as e:
            log.error(f"invoice: {e}")
            lang = get_user_lang(cb.from_user.id)
            await cb.answer(t("donate_invoice_error", lang), show_alert=True)

    @dp.callback_query(F.data == "donate_custom")
    async def _donate_custom(cb: CallbackQuery, state: FSMContext):
        await cb.answer()
        await state.clear()
        await state.set_state(DonateStates.custom_amount)
        lang = get_user_lang(cb.from_user.id)
        try:
            await cb.message.edit_text(
                t("donate_custom_prompt", lang),
                reply_markup=kb([[danger(f"{E.CROSS} {t('btn_cancel', lang)}", "menu")]]),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    @dp.message(StateFilter(DonateStates.custom_amount), F.text)
    async def _donate_custom_amount(msg: Message, state: FSMContext):
        lang = get_user_lang(msg.from_user.id)
        txt = (msg.text or "").strip().lower()
        if txt in ("/cancel", "لغو", "cancel"):
            await state.clear()
            await msg.answer(t("cancelled", lang))
            return
        try:
            amount = int(msg.text.strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
            if not (1 <= amount <= 10000):
                raise ValueError
        except ValueError:
            await msg.answer(t("donate_amount_invalid", lang))
            return
        await state.clear()
        try:
            await _send_stars_invoice(msg.bot, msg.from_user.id, amount, msg.from_user.id)
        except Exception as e:
            log.error(f"custom invoice: {e}")
            await msg.answer(t("donate_invoice_error", lang))

    @dp.pre_checkout_query()
    async def _pre_checkout(pcq: PreCheckoutQuery):
        try:
            await pcq.answer(ok=True)
        except Exception as e:
            log.debug(f"pre_checkout: {e}")

    @dp.message(F.successful_payment)
    async def _payment_ok(msg: Message):
        amount = msg.successful_payment.total_amount
        lang = get_user_lang(msg.from_user.id)
        await msg.answer(t("donate_thanks", lang, n=amount), parse_mode=ParseMode.HTML)
        for oid in OWNER_IDS:
            try:
                await msg.bot.send_message(
                    oid,
                    t("donate_owner_notify", "fa",
                      name=_safe_name(msg.from_user.first_name or "—"),
                      uid=msg.from_user.id, n=amount),
                    parse_mode=ParseMode.HTML,
                )
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
