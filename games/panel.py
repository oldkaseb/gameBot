"""پنل بازی‌ها — گروه: callback / پیوی: web_app"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username

router = Router(name="panel")
MINI_APP_URL = "https://games.rhinokaseb.abrdns.com"


def _group_game_btn(text: str, game: str, uid: int):
    """دکمه امن برای گروه — callback به جای web_app"""
    return primary(text, f"open_game_{game}_{uid}")


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)
    name = message.from_user.first_name or "—"

    if message.chat.type == ChatType.PRIVATE:
        await _send_pm_panel(message, uid, lang, name)
        return

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )
    rows = [
        [_group_game_btn(f"{E.PUZZLE} {t('game_2048_title', lang)}", "2048", uid),
         _group_game_btn(f"{E.PUZZLE} {t('game_spuzzle', lang)}", "spuzzle", uid)],
        [_group_game_btn(f"{E.SPARK} {t('game_samegame', lang)}", "samegame", uid)],
        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],
        [_group_game_btn(f"{E.MIC} {t('game_typing', lang)}", "typing", uid),
         _group_game_btn(f"{E.BRAIN} {t('game_hangman', lang)}", "hangman", uid)],
        [_group_game_btn(f"{E.TARGET} {t('game_guess_num', lang)}", "guess", uid)],
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


async def _send_pm_panel(message: Message, uid: int, lang: str, name: str):
    """نسخه پیوی — web_app مجاز است"""
    def wa(text, game):
        return primary(text, web_app_url=f"{MINI_APP_URL}/?game={game}&uid={uid}")

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )
    rows = [
        [wa(f"{E.PUZZLE} {t('game_2048_title', lang)}", "2048"),
         wa(f"{E.PUZZLE} {t('game_spuzzle', lang)}", "spuzzle")],
        [wa(f"{E.SPARK} {t('game_samegame', lang)}", "samegame")],
        [wa(f"{E.MIC} {t('game_typing', lang)}", "typing"),
         wa(f"{E.BRAIN} {t('game_hangman', lang)}", "hangman")],
        [wa(f"{E.TARGET} {t('game_guess_num', lang)}", "guess")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("open_game_"))
async def open_game_redirect(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        game = parts[2]
        target_uid = int(parts[3])
    except (IndexError, ValueError):
        await cb.answer("❌", show_alert=True)
        return

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != target_uid:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    await cb.answer()

    bot_name = get_bot_username()
    deep_link = f"https://t.me/{bot_name}?start=game_{game}"

    try:
        await cb.bot.send_message(
            uid,
            f"{E.GAME} <b>{t('open_in_pm_title', lang)}</b>\n\n"
            f"{E.INFO} {t('open_in_pm_body', lang)}",
            reply_markup=kb([[
                primary(
                    f"{E.PLAY} {t('open_game_btn', lang)}",
                    web_app_url=f"{MINI_APP_URL}/?game={game}&uid={uid}",
                )
            ]]),
            parse_mode=ParseMode.HTML,
        )
        await cb.answer(t("check_pm", lang), show_alert=True)
    except Exception:
        # کاربر ربات را در PM استارت نکرده
        try:
            await cb.message.answer(
                f"{E.WARN} {t('start_pm_first_msg', lang)}",
                reply_markup=kb([[
                    primary(f"{E.BOT} {t('open_bot_btn', lang)}", url=deep_link)
                ]]),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        await cb.answer(t("start_pm_first", lang), show_alert=True)


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
