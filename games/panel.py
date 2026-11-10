"""پنل بازی‌ها — چندزبانه، سازگار با دکمه‌های امن"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command
from urllib.parse import urlencode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb

router = Router(name="panel")
MINI_APP_URL = "https://games.rhinokaseb.abrdns.com"


def webapp_btn(text: str, game: str, uid: int):
    params = urlencode({"game": game, "uid": uid})
    return primary(text, web_app_url=f"{MINI_APP_URL}/?{params}")


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(t("panel_group_only", lang), parse_mode=ParseMode.HTML)
        return

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=message.from_user.first_name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )
    rows = [
        [webapp_btn(f"{E.PUZZLE} {t('game_2048_title', lang)}", "2048", uid),
         webapp_btn(f"{E.PUZZLE} {t('game_spuzzle', lang)}", "spuzzle", uid)],
        [webapp_btn(f"{E.SPARK} {t('game_samegame', lang)}", "samegame", uid)],
        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],
        [webapp_btn(f"{E.MIC} {t('game_typing', lang)}", "typing", uid),
         webapp_btn(f"{E.BRAIN} {t('game_hangman', lang)}", "hangman", uid)],
        [webapp_btn(f"{E.TARGET} {t('game_guess_num', lang)}", "guess", uid)],
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
