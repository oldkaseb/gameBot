"""حدس عدد — ConversationHandler با چندزبانه + امنیت ادمین"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, cancel_btn, kb
from . import state
import random

router = Router(name="number_guess")


class GuessStates(StatesGroup):
    waiting_range = State()
    guessing = State()


def _to_en_digits(s: str) -> str:
    for i, d in enumerate("۰۱۲۳۴۵۶۷۸۹"):
        s = s.replace(d, str(i))
    for i, d in enumerate("٠١٢٣٤٥٦٧٨٩"):
        s = s.replace(d, str(i))
    return s


# ─────────── شروع از پنل
@router.callback_query(F.data.startswith("hads_addad_start_"))
async def start(cb: CallbackQuery, state_fsm: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    # فقط ادمین گروه
    try:
        member = await cb.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await cb.answer(t("only_admin", lang), show_alert=True)
        return

    if chat_id in state.active_games["guess_number"]:
        await cb.answer(t("game_already_running", lang), show_alert=True)
        return

    await cb.answer()
    await state_fsm.clear()
    await state_fsm.update_data(chat_id=chat_id, starter_id=uid)
    await state_fsm.set_state(GuessStates.waiting_range)

    await cb.message.edit_text(
        f"{E.TARGET}{E.CHART} <b>{t('game_guess_num', lang)}</b>\n\n"
        f"{E.INFO} بازه را بفرستید (مثال: <code>1-1000</code>)\n"
        f"{E.CROSS} برای لغو: /cancel",
        reply_markup=kb([[cancel_btn(lang, "rsgame_main_" + str(uid))]]),
        parse_mode=ParseMode.HTML,
    )


# ─────────── دریافت بازه
@router.message(GuessStates.waiting_range, F.text)
async def receive_range(message: Message, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if message.from_user.id != data.get("starter_id"):
        return  # فقط ادمین سازنده

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
    state.active_games["guess_number"][chat_id] = {
        "number": secret,
        "lo": lo,
        "hi": hi,
        "tries": 0,
        "guessed_by": set(),
        "game_id": message.message_id,
    }

    await state_fsm.clear()

    await message.reply(
        f"{E.PARTY}{E.TARGET} <b>{t('game_guess_num', lang)}</b>\n\n"
        f"{E.CHECK} یک عدد بین <b>{lo}</b> و <b>{hi}</b> انتخاب شد!\n"
        f"{E.INFO} عدد را حدس بزنید:",
        parse_mode=ParseMode.HTML,
    )


# ─────────── حدس عدد
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.regexp(r"^[\d۰-۹٠-٩]+$"))
async def on_guess(message: Message):
    chat_id = message.chat.id
    game = state.active_games["guess_number"].get(chat_id)
    if not game:
        return

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
        # ذخیره در leaderboard
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
        del state.active_games["guess_number"][chat_id]


# ─────────── لغو
@router.message(Command("cancel"))
async def cancel(message: Message, state_fsm: FSMContext):
    chat_id = message.chat.id
    game = state.active_games["guess_number"].pop(chat_id, None)
    if game:
        lang = get_user_lang(message.from_user.id)
        await message.reply(
            f"{E.OK2} {t('game_closed', lang)}",
            parse_mode=ParseMode.HTML,
        )
    await state_fsm.clear()
