"""پنل بازی‌ها — فقط در گروه"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, btn, back_btn, kb

router = Router(name="panel")


def _check_owner(cb: CallbackQuery) -> bool:
    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return False
    return cb.from_user.id == target


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            t("panel_group_only", lang),
            parse_mode=ParseMode.HTML,
        )
        return

    text = f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=message.from_user.first_name)}</b>"
    rows = [
        # ردیف سبز
        [success(f"{E.TROPHY} {t('btn_group', lang)}",   f"rsgame_cat_board_{uid}"),
         success(f"{E.TARGET} {t('btn_single', lang)}",  f"rsgame_cat_single_{uid}")],
        # ردیف آبی
        [primary(f"{E.MIC} {t('btn_typing', lang)}",     f"rsgame_cat_typing_{uid}"),
         primary(f"{E.GHOST} {t('btn_anon', lang)}",     f"rsgame_cat_anon_{uid}")],
        # ردیف سبز
        [success(f"{E.TROPHY} 🏆 برترین‌ها", "lb_menu")],
        # ردیف قرمز
        [danger(f"{E.CROSS} {t('btn_close', lang)}",     f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("rsgame_cat_"))
async def category(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not _check_owner(cb):
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    cat = cb.data.split("_")[2]
    await cb.answer()

    if cat == "board":
        text = f"{E.TROPHY} <b>{t('group_games_title', lang)}</b>"
        rows = [
            # ردیف سبز: حکم
            [success(f"{E.CARD} {t('game_hokm', lang)}", f"hokm_start_2p_{uid}"),
             success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"hokm_start_4p_{uid}")],
            # ردیف آبی: دوز
            [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"dooz_start_2p_{uid}"),
             primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"doz4p_start_{uid}")],
            # ردیف سبز: چهار در ردیف + RPS
            [success(f"{E.GAME} {t('game_connect4', lang)}", f"connect4_start_{uid}")],
            # ردیف آبی: RPS + Memory
            [primary("🪨📄✂️ " + t("game_rps", lang), f"rps_start_{uid}"),
             primary(f"{E.BRAIN} {t('game_memory', lang)}", f"memory_start_4x4_{uid}")],
            # ردیف قرمز: بازگشت
            [danger(f"{E.ARROW} {t('btn_back', lang)}", f"rsgame_main_{uid}")],
        ]
    elif cat == "single":
        text = f"{E.TARGET} <b>{t('single_games_title', lang)}</b>"
        rows = [
            [success(f"{E.PUZZLE} 2048", f"2048_start_{uid}")],
            [primary(f"{E.PUZZLE} {t('game_spuzzle', lang)}", f"spuzzle_start_{uid}")],
            [primary(f"{E.SPARK} {t('game_samegame', lang)}", f"samegame_start_{uid}")],
            [danger(f"{E.ARROW} {t('btn_back', lang)}", f"rsgame_main_{uid}")],
        ]
    elif cat == "typing":
        text = f"{E.MIC} <b>{t('typing_games_title', lang)}</b>"
        rows = [
            [success(f"{E.BRAIN} {t('game_hangman', lang)}", f"hads_kalame_start_{uid}")],
            [primary(f"{E.MIC} {t('game_typing', lang)}", f"type_start_{uid}")],
            [primary(f"{E.TARGET} {t('game_guess_num', lang)}", f"hads_addad_start_{uid}")],
            [danger(f"{E.ARROW} {t('btn_back', lang)}", f"rsgame_main_{uid}")],
        ]
    elif cat == "anon":
        text = f"{E.GHOST} <b>{t('anon_games_title', lang)}</b>"
        rows = [
            [success(f"{E.GHOST} {t('game_eteraf', lang)}", f"eteraf_start_default_{uid}")],
            [primary(f"{E.GHOST} {t('game_eteraf_custom', lang)}", f"eteraf_start_custom_{uid}")],
            [primary(f"{E.MASK} {t('game_gharch', lang)}", f"gharch_start_{uid}")],
            [danger(f"{E.ARROW} {t('btn_back', lang)}", f"rsgame_main_{uid}")],
        ]
    else:
        return

    try:
        await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.callback_query(F.data.startswith("rsgame_main_"))
async def back_main(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not _check_owner(cb):
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    text = f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=cb.from_user.first_name)}</b>"
    rows = [
        [success(f"{E.TROPHY} {t('btn_group', lang)}",  f"rsgame_cat_board_{uid}"),
         success(f"{E.TARGET} {t('btn_single', lang)}", f"rsgame_cat_single_{uid}")],
        [primary(f"{E.MIC} {t('btn_typing', lang)}",    f"rsgame_cat_typing_{uid}"),
         primary(f"{E.GHOST} {t('btn_anon', lang)}",    f"rsgame_cat_anon_{uid}")],
        [success(f"{E.TROPHY} 🏆 برترین‌ها", "lb_menu")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    try:
        await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not _check_owner(cb):
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        try:
            await cb.message.edit_text(f"{E.OK2} {t('panel_closed', lang)}")
        except Exception:
            pass
