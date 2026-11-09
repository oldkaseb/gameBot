# -*- coding: utf-8 -*-
"""main.py — ربات بازی راینو"""

import asyncio
import logging
import os

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, LabeledPrice, Message, PreCheckoutQuery,
)

from emojis import E, render_emojis
from langs import LANGS, t, get_user_lang, set_user_lang
from utils.premium import btn, success, primary, danger, kb
from utils.commands import router as persian_cmd_router
from database import db
from games import register_all_games
from games.state import cleanup_loop
from games.stop import router as stop_router
from games.anon import router as anon_router
from games.leaderboard import router as lb_router
from games.inline_games import router as inline_games_router
from admin.panel import router as admin_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rhino")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_IDS = {7662192190, 6041119040}

# BOT_USERNAME سراسری — در main() ست می‌شود
_bot_username = "bot"


def get_bot_username() -> str:
    return _bot_username


# ═══════════════════════════════════════════════
# Bot با پارسر خودکار ایموجی پریمیوم
# ═══════════════════════════════════════════════

class EmojiBot(Bot):
    """Bot که همه متن/caption ها را خودکار به <tg-emoji> تبدیل می‌کند"""

    async def __call__(self, method, request_timeout=None):
        for attr in ("text", "caption"):
            val = getattr(method, attr, None)
            if isinstance(val, str) and "[" in val and "<tg-emoji" not in val:
                try:
                    setattr(method, attr, render_emojis(val))
                except Exception:
                    pass
        return await super().__call__(method, request_timeout)


# ═══════════════════════════════════════════════
# Forced Join
# ═══════════════════════════════════════════════

async def _check_forced_join(bot: Bot, user_id: int):
    """برگرداندن لیست کانال‌هایی که کاربر هنوز عضو نشده"""
    try:
        if await db.is_admin(user_id):
            return []
    except Exception:
        pass

    missing = []
    try:
        channels = await db.list_channels()
    except Exception:
        return []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception:
            # اگر نتوانست چک کند، از این کانال رد شو (fail-open)
            continue
    return missing


def _join_kb(channels, lang: str = "fa"):
    rows = []
    for ch in channels:
        label = f"{E.LIKE} {t('force_join_btn', lang)} — {ch['title'] or ch['chat_id']}"
        if ch["username"]:
            url = f"https://t.me/{ch['username'].lstrip('@')}"
            rows.append([btn(label, url=url, style="success")])
        else:
            rows.append([success(label, "check_join")])
    rows.append([primary(f"{E.REFRESH} {t('force_join_check', lang)}", "check_join")])
    return kb(rows)


class ForcedJoinMiddleware(BaseMiddleware):
    """چک عضویت اجباری — بجز /start، انتخاب زبان، donate و check_join"""

    EXEMPT_CALLBACK_PREFIXES = (
        "check_join", "set_lang:", "lang_menu",
        "donate", "menu",
    )
    EXEMPT_TEXT_STARTS = ("/start", "/cancel", "/help")
    EXEMPT_TEXTS = ("شروع", "استارت", "زبان", "language", "lang")

    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(self, handler, event, data):
        from_user = getattr(event, "from_user", None)
        if not from_user:
            return await handler(event, data)

        # معافیت‌های مشخص
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

        # چک عضویت
        try:
            missing = await _check_forced_join(self.bot, from_user.id)
        except Exception:
            return await handler(event, data)  # fail-open

        if not missing:
            return await handler(event, data)

        # کاربر عضو نیست → هشدار
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


# ═══════════════════════════════════════════════
# منوها
# ═══════════════════════════════════════════════

async def _build_main_menu(uid: int, name: str):
    """منوی بازی‌ها — فقط در گروه"""
    lang = get_user_lang(uid)
    text = (
        f"{E.PARTY}{E.SPARK} <b>{t('welcome', lang, name=name)}</b>\n\n"
        f"{E.GAME} {t('game_panel', lang)}"
    )
    rows = [
        # ردیف سبز: ورودی‌های اصلی بازی
        [success(f"{E.TROPHY} {t('btn_group', lang)}",  f"rsgame_cat_board_{uid}"),
         success(f"{E.TARGET} {t('btn_single', lang)}", f"rsgame_cat_single_{uid}")],
        # ردیف آبی: دسته‌بندی‌های دیگر
        [primary(f"{E.MIC} {t('btn_typing', lang)}",    f"rsgame_cat_typing_{uid}"),
         primary(f"{E.GHOST} {t('btn_anon', lang)}",    f"rsgame_cat_anon_{uid}")],
        # ردیف سبز: برترین‌ها
        [success(f"{E.TROPHY} 🏆 برترین‌ها", "lb_menu")],
        # ردیف قرمز: بستن
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def _build_pm_welcome(uid: int, name: str):
    """منوی PV — خوشامد + افزودن به گروه + donate"""
    lang = get_user_lang(uid)
    bot_username = get_bot_username()

    text = (
        f"{E.WAVE}{E.SPARK} <b>{t('pm_welcome_title', lang, name=name)}</b>\n\n"
        f"{E.GAME} {t('pm_welcome_body', lang)}\n\n"
        f"{E.HEART} برای حمایت از ما می‌توانید از دکمه زیر استفاده کنید."
    )

    rows = [
        [success(
            f"{E.PLUS} {t('btn_add_to_group', lang)}",
            url=f"https://t.me/{bot_username}?startgroup=true",
        )],
        [primary(f"{E.HEART} {t('btn_donate', lang)}", "donate")],
        [primary(f"{E.SPARK} {t('btn_change_lang', lang)}", "lang_menu")],
    ]
    if uid in OWNER_IDS:
        rows.append([success(f"{E.CROWN} {t('admin_panel', lang)}", "adm:panel")])
    return text, kb(rows)


async def _show_pm_welcome(cb_or_msg, uid: int, name: str, edit: bool = True):
    text, markup = await _build_pm_welcome(uid, name)
    try:
        if edit and isinstance(cb_or_msg, CallbackQuery):
            await cb_or_msg.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        elif edit and isinstance(cb_or_msg, Message):
            await cb_or_msg.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            msg = cb_or_msg.message if isinstance(cb_or_msg, CallbackQuery) else cb_or_msg
            await msg.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except TelegramBadRequest as e:
        if "not modified" not in str(e).lower():
            log.debug(f"show_pm_welcome: {e}")
        if isinstance(cb_or_msg, CallbackQuery):
            await cb_or_msg.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════
# Start
# ═══════════════════════════════════════════════

async def cmd_start(message: Message, command=None):
    uid = message.from_user.id
    is_pm = message.chat.type == "private"
    payload = (command.args if command else "") or ""

    # دیپ‌لینک ناشناس → anon_router
    if payload.startswith("gharch_") or payload.startswith("eteraf_"):
        return

    # دیپ‌لینک بازی از inline
    game_payload = None
    if payload.startswith("game_"):
        game_payload = payload[5:]  # hokm, dooz, ...

    user = await db.get_user(uid)
    is_new = user is None
    if is_new:
        await db.upsert_user(
            uid,
            message.from_user.username or "",
            message.from_user.first_name or "",
        )

    user_lang = user["language"] if user else None
    if user_lang:
        set_user_lang(uid, user_lang)

    # اگر کاربر جدید یا زبان ندارد → انتخاب زبان
    if is_new or not user_lang:
        rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
        await message.answer(
            f"{E.WAVE}{E.SPARK} {t('choose_lang', 'fa')}",
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
        )
        return

    # پیام خوشامد در PV یا منوی بازی در گروه
    if is_pm:
        await _show_pm_welcome(message, uid, message.from_user.first_name or "دوست", edit=False)
    else:
        text, markup = await _build_main_menu(uid, message.from_user.first_name or "دوست")
        await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def set_lang_cb(cb: CallbackQuery):
    lang = cb.data.split(":")[1]
    if lang not in LANGS:
        await cb.answer("❌", show_alert=True)
        return
    set_user_lang(cb.from_user.id, lang)
    try:
        await db.set_language(cb.from_user.id, lang)
    except Exception:
        pass
    await cb.answer(t("lang_saved", lang))

    is_pm = cb.message.chat.type == "private"
    if is_pm:
        await _show_pm_welcome(cb, cb.from_user.id, cb.from_user.first_name or "دوست")
    else:
        text, markup = await _build_main_menu(cb.from_user.id, cb.from_user.first_name or "دوست")
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def cmd_lang(message: Message):
    rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
    await message.answer(
        t("choose_lang", get_user_lang(message.from_user.id)),
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════
# Donate با Stars
# ═══════════════════════════════════════════════

DONATE_PRESETS = [50, 100, 250, 500, 1000]


class DonateStates(StatesGroup):
    custom_amount = State()


async def _show_donate_menu(cb: CallbackQuery, edit: bool = True):
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    rows = []
    row1 = [primary(f"{E.STAR} {n}", f"donate_pay:{n}") for n in DONATE_PRESETS[:3]]
    row2 = [primary(f"{E.STAR} {n}", f"donate_pay:{n}") for n in DONATE_PRESETS[3:]]
    rows.append(row1)
    rows.append(row2)
    rows.append([success(f"{E.PLUS} {t('donate_custom', lang)}", "donate_custom")])
    rows.append([danger(f"{E.ARROW} {t('btn_back', lang)}", "menu")])

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
# Health server
# ═══════════════════════════════════════════════

async def _start_health_server(port: int = 8080):
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


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════

async def main():
    global _bot_username

    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN not set!")
        return

    bot = EmojiBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    await db.connect()
    await db.init()

    me = await bot.get_me()
    _bot_username = me.username or "bot"
    log.info(f"Bot: @{_bot_username}")

    # ───── ثبت Routerها
    register_all_games(dp)
    dp.include_router(anon_router)
    dp.include_router(stop_router)
    dp.include_router(lb_router)
    dp.include_router(inline_games_router)
    dp.include_router(admin_router)
    dp.include_router(persian_cmd_router)

    # ───── Middlewares (به ترتیب)
    forced = ForcedJoinMiddleware(bot)
    dp.message.outer_middleware(forced)
    dp.callback_query.outer_middleware(forced)

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

    @dp.callback_query(F.data == "menu")
    async def _menu(cb: CallbackQuery):
        await cb.answer()
        uid = cb.from_user.id
        name = cb.from_user.first_name or "دوست"
        if cb.message.chat.type == "private":
            await _show_pm_welcome(cb, uid, name)
        else:
            text, markup = await _build_main_menu(uid, name)
            try:
                await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            except TelegramBadRequest as e:
                if "not modified" not in str(e).lower():
                    log.debug(f"menu: {e}")

    @dp.callback_query(F.data == "lang_menu")
    async def _lang_menu(cb: CallbackQuery):
        await cb.answer()
        rows = [[btn(v, f"set_lang:{k}")] for k, v in LANGS.items()]
        rows.append([primary(f"{E.ARROW} {t('btn_back', get_user_lang(cb.from_user.id))}", "menu")])
        await cb.message.edit_text(
            t("choose_lang", get_user_lang(cb.from_user.id)),
            reply_markup=kb(rows), parse_mode=ParseMode.HTML,
        )

    # ───── Donate
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
            await cb.answer("❌", show_alert=True)
            return
        await cb.answer()
        try:
            await _send_stars_invoice(cb.bot, cb.from_user.id, amount, cb.from_user.id)
        except Exception as e:
            log.error(f"invoice: {e}")
            await cb.answer("❌ خطا در ساخت فاکتور", show_alert=True)

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

    @dp.message(DonateStates.custom_amount, F.text)
    async def _donate_custom_amount(msg: Message, state: FSMContext):
        if (msg.text or "").strip().lower() in ("/cancel", "لغو"):
            await state.clear()
            await msg.answer("✅ لغو شد.")
            return
        try:
            amount = int(msg.text.strip())
            if not (1 <= amount <= 10000):
                raise ValueError
        except ValueError:
            await msg.answer("❌ عددی بین ۱ تا ۱۰۰۰۰ وارد کنید.")
            return
        await state.clear()
        try:
            await _send_stars_invoice(msg.bot, msg.from_user.id, amount, msg.from_user.id)
        except Exception as e:
            log.error(f"custom invoice: {e}")
            await msg.answer("❌ خطا در ساخت فاکتور")

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
                    f"💰 <b>حمایت جدید</b>\n\n"
                    f"👤 {msg.from_user.first_name or '—'} (<code>{msg.from_user.id}</code>)\n"
                    f"⭐ {amount} ستاره",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    # ───── Background tasks
    asyncio.create_task(cleanup_loop(bot))
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
