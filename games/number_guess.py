"""حدس عدد — ساختار درست + لاگ + پاکسازی خودکار"""

import random
import time
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.dispatcher.event.bases import SkipHandler

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, cancel_btn, kb
from . import state

router = Router(name="number_guess")
log = logging.getLogger("number_guess")


class GuessStates(StatesGroup):
    waiting_range = State()


def _to_en_digits(s: str) -> str:
    for i, d in enumerate("۰۱۲۳۴۵۶۷۸۹"):
        s = s.replace(d, str(i))
    for i, d in enumerate("٠١٢٣٤٥٦٧٨٩"):
        s = s.replace(d, str(i))
    return s


def _clear_stale(chat_id: int) -> None:
    """پاک کردن بازی‌های قدیمی/خراب guess_number در این گروه"""
    existing = state.active_games["guess_number"].get(chat_id)
    if not existing:
        return
    if not isinstance(existing, dict):
        log.warning(f"🗑️ corrupted guess game: chat={chat_id} type={type(existing)}")
        state.active_games["guess_number"].pop(chat_id, None)
        return
    # ساختار قدیمی تک‌سطحی
    if "number" in existing:
        log.info(f"🗑️ old single-level guess game: chat={chat_id}")
        state.active_games["guess_number"].pop(chat_id, None)
        return
    # ساختار جدید — فقط قدیمی‌تر از ۲ ساعت
    now = time.time()
    for gid, g in list(existing.items()):
        if isinstance(g, dict) and now - g.get("_created", now) > 7200:
            state.unregister("guess_number", chat_id, gid)
            log.info(f"⏰ stale guess game removed: chat={chat_id} gid={gid}")


@router.callback_query(F.data.startswith("hads_addad_start_"))
async def start(cb: CallbackQuery, state_fsm: FSMContext):
    try:
        uid = cb.from_user.id
        lang = get_user_lang(uid)

        if not cb.message or not getattr(cb.message, "chat", None):
            await cb.answer("❌ پیام نامعتبر", show_alert=True)
            return

        chat_id = cb.message.chat.id

        try:
            target = int(cb.data.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            await cb.answer("❌", show_alert=True)
            return
        if uid != target:
            await cb.answer(t("not_your_panel", lang), show_alert=True)
            return

        try:
            member = await cb.bot.get_chat_member(chat_id, uid)
            is_admin = member.status in ("administrator", "creator")
        except Exception:
            is_admin = False
        if not is_admin:
            await cb.answer(t("only_admin", lang), show_alert=True)
            return

        _clear_stale(chat_id)
        if state.active_games["guess_number"].get(chat_id):
            await cb.answer(t("game_already_running", lang), show_alert=True)
            return

        await cb.answer()
        await state_fsm.clear()
        await state_fsm.update_data(chat_id=chat_id, starter_id=uid)
        await state_fsm.set_state(GuessStates.waiting_range)

        prompt = (
            f"{E.TARGET}{E.CHART} <b>{t('game_guess_num', lang)}</b>\n\n"
            f"{E.INFO} بازه را بفرستید (مثال: <code>1-1000</code>)\n"
            f"{E.CROSS} برای لغو: /cancel"
        )
        markup = kb([[cancel_btn(lang, "rsgame_main_" + str(uid))]])

        try:
            await cb.message.edit_text(prompt, reply_markup=markup, parse_mode=ParseMode.HTML)
            log.info(f"✅ number_guess opened: chat={chat_id} uid={uid}")
        except Exception as e:
            log.warning(f"edit_text failed: {e} — trying answer")
            try:
                await cb.message.answer(prompt, reply_markup=markup, parse_mode=ParseMode.HTML)
                log.info(f"✅ number_guess opened (answer): chat={chat_id}")
            except Exception as e2:
                log.error(f"❌ both failed: {e2}")
                await cb.answer(f"⚠️ {e2}", show_alert=True)

    except Exception as e:
        log.exception(f"❌ number_guess start crash: {e}")
        try:
            await cb.answer(f"⚠️ {e}", show_alert=True)
        except Exception:
            pass


@router.message(GuessStates.waiting_range, F.text)
async def receive_range(message: Message, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if message.from_user.id != data.get("starter_id"):
        return

    lang = get_user_lang(message.from_user.id)
    text = _to_en_digits(message.text or "")

    try:
        lo_s, hi_s = text.split("-")
        lo, hi = int(lo_s.strip()), int(hi_s.strip())
        if lo >= hi:
            raise ValueError
    except Exception:
        await message.reply(
            f"{E.WARN} فرمت اشتباه. مثال: <code>1-1000</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    secret = random.randint(lo, hi)
    chat_id = data["chat_id"]
    game_id = message.message_id

    state.register("guess_number", chat_id, game_id, {
        "game_id": game_id,
        "number": secret,
        "lo": lo,
        "hi": hi,
        "tries": 0,
        "guessed_by": set(),
        "player_id": data["starter_id"],
    })
    log.info(f"🎮 guess game registered: chat={chat_id} gid={game_id} range={lo}-{hi}")

    await state_fsm.clear()

    await message.reply(
        f"{E.PARTY}{E.TARGET} <b>{t('game_guess_num', lang)}</b>\n\n"
        f"{E.CHECK} یک عدد بین <b>{lo}</b> و <b>{hi}</b> انتخاب شد!\n"
        f"{E.INFO} عدد را حدس بزنید:",
        parse_mode=ParseMode.HTML,
    )


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.regexp(r"^[\d۰-۹٠-٩]+$"))
async def on_guess(message: Message):
    chat_id = message.chat.id
    games = state.active_games["guess_number"].get(chat_id, {})
    if not games or not isinstance(games, dict):
        raise SkipHandler
    game = next(iter(games.values()), None)
    if not game or not isinstance(game, dict) or "number" not in game:
        raise SkipHandler

    lang = get_user_lang(message.from_user.id)
    try:
        guess = int(_to_en_digits(message.text))
    except ValueError:
        return

    game["tries"] += 1
    game["guessed_by"].add(message.from_user.id)

    if guess < game["number"]:
        await message.reply(f"{E.UP} <b>بالاتر!</b> ⬆️", parse_mode=ParseMode.HTML)
    elif guess > game["number"]:
        await message.reply(f"{E.DOWN} <b>پایین‌تر!</b> ⬇️", parse_mode=ParseMode.HTML)
    else:
        await message.reply(
            f"{E.TROPHY}{E.PARTY} <b>{t('game_winner', lang, name=message.from_user.first_name)}</b>\n\n"
            f"{E.TARGET} عدد صحیح: <b>{game['number']}</b>\n"
            f"{E.CHART} تعداد تلاش: {game['tries']}",
            parse_mode=ParseMode.HTML,
        )
        try:
            from database import db
            await db.pool.execute(
                """INSERT INTO game_wins (user_id, game_type, wins)
                   VALUES ($1, 'number_guess', 1)
                   ON CONFLICT (user_id, game_type) DO UPDATE
                   SET wins = game_wins.wins + 1""",
                message.from_user.id,
            )
        except Exception:
            pass
        state.unregister("guess_number", chat_id, game["game_id"])


@router.message(Command("cancel"))
async def cancel(message: Message, state_fsm: FSMContext):
    chat_id = message.chat.id
    games = state.active_games["guess_number"].get(chat_id, {})
    if games and isinstance(games, dict):
        for gid in list(games.keys()):
            state.unregister("guess_number", chat_id, gid)
        lang = get_user_lang(message.from_user.id)
        await message.reply(
            f"{E.OK2} {t('game_closed', lang)}",
            parse_mode=ParseMode.HTML,
        )
    await state_fsm.clear()
