"""بازی حدس کلمه — با رفع باگ کلمات دارای فاصله"""

import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import btn, success, danger, primary, back_btn, kb
from . import state
from .words import get_random_word

router = Router(name="hangman")

INITIAL_LIVES = 10


@router.callback_query(F.data.startswith("hads_kalame_start_"))
async def start_game(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    # امنیت: مالکیت پنل
    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    if chat_id in state.active_games["hangman"] and state.active_games["hangman"][chat_id]:
        await cb.answer(t("game_already_running", lang), show_alert=True)
        return

    await cb.answer()
    word = get_random_word()  # ← فیلتر کلمات دارای فاصله در اینجا
    game_id = cb.message.message_id + 1

    game = {
        "game_id": game_id,
        "word": word,
        "display": ["_"] * len(word),
        "guessed": set(),
        "players": {},  # {user_id: lives}
        "finished": False,
        "player_id": None,  # برای پاک‌سازی
    }
    state.register("hangman", chat_id, game_id, game)

    text = (
        f"{E.BRAIN}{E.SPARK} <b>{t('hangman_started', lang)}</b>\n\n"
        f"{E.HEART} {t('each_player_lives', lang, n=INITIAL_LIVES)}\n"
        f"{E.INFO} {t('guess_one_letter', lang)}\n\n"
        f"{E.TARGET} <code>{' '.join(game['display'])}</code>"
    )
    await cb.message.edit_text(text, parse_mode=ParseMode.HTML)


@router.message(F.text.regexp(r"^[آ-ی]$") & F.chat.type.in_({"group", "supergroup"}))
async def handle_guess(message: Message):
    chat_id = message.chat.id
    uid = message.from_user.id
    lang = get_user_lang(uid)

    # پیدا کردن بازی فعال در این گروه
    games = state.active_games["hangman"].get(chat_id, {})
    if not games:
        return
    game = next(iter(games.values()), None)
    if not game or game["finished"]:
        return

    guess = (message.text or "").strip()

    # ── باگ قبلی: حرف تکراری خطا نمی‌داد
    if guess in game["guessed"]:
        await message.reply(f"{E.WARN} {t('letter_already', lang)}", quote=True)
        return

    game["guessed"].add(guess)
    game["players"].setdefault(uid, INITIAL_LIVES)

    # ── باگ قبلی: کاربر بدون جان می‌توانست بازی کند
    if game["players"][uid] <= 0:
        await message.reply(
            f"{E.SKULL} {t('no_lives_left', lang)}", quote=True
        )
        return

    if guess in game["word"]:
        # حرف درست
        for i, ch in enumerate(game["word"]):
            if ch == guess:
                game["display"][i] = ch

        if "_" not in game["display"]:
            # برنده
            game["finished"] = True
            user_name = message.from_user.first_name
            await message.reply(
                f"{E.PARTY}{E.TROPHY} <b>{t('word_winner', lang, name=user_name, word=game['word'])}</b>",
                parse_mode=ParseMode.HTML,
            )
            state.unregister("hangman", chat_id, game["game_id"])
            return

        await message.reply(
            f"<code>{' '.join(game['display'])}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        # حرف غلط
        game["players"][uid] -= 1
        lives = game["players"][uid]

        if lives > 0:
            await message.reply(
                f"{E.CROSS} {t('wrong_guess_lives', lang, name=message.from_user.first_name, n=lives)}",
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply(
                f"{E.SKULL} {t('player_eliminated', lang, name=message.from_user.first_name)}",
                parse_mode=ParseMode.HTML,
            )
            # آیا همه حذف شده‌اند؟
            if not any(l > 0 for l in game["players"].values()):
                await message.answer(
                    f"{E.SKULL}{E.CROSS} {t('all_lost_word_was', lang, word=game['word'])}",
                    parse_mode=ParseMode.HTML,
                )
                game["finished"] = True
                state.unregister("hangman", chat_id, game["game_id"])
