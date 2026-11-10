# -*- coding: utf-8 -*-
"""پنل بازی‌ها — تمام بازی‌ها متصل به مینی‌اپ + گردونه شانس به صورت لابی گروهی"""

import os
from urllib.parse import urlencode
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username

router = Router(name="panel")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


def _group_game_btn(text: str, game: str, uid: int, style_fn=primary):
    """دکمه امن برای گروه — هدایت به مینی‌اپ بازی"""
    return style_fn(text, f"open_game_{game}_{uid}")


def _pm_game_btn(text: str, game: str, uid: int, lang: str, style_fn=primary):
    """دکمه مستقیم WebApp برای پیوی"""
    params = urlencode({"game": game, "uid": uid, "lang": lang})
    return style_fn(text, web_app_url=f"{MINI_APP_URL}/?{params}")


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
        [_group_game_btn(f"{E.PUZZLE} {t('game_2048_title', lang)}", "2048", uid, primary),
         _group_game_btn(f"{E.PUZZLE} {t('game_spuzzle', lang)}", "spuzzle", uid, primary)],
        [_group_game_btn(f"{E.SPARK} {t('game_samegame', lang)}", "samegame", uid, primary)],
        [primary(f"{E.TARGET} {t('game_dooz', lang)}", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} {t('game_doz4p', lang)}", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} {t('game_connect4', lang)}", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} {t('game_hokm_4p', lang)}", f"lobby_hokm_{uid}")],
        [primary(f"{E.PUZZLE} {t('game_rps', lang)}", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} {t('game_memory', lang)}", f"lobby_memory_{uid}")],
        [_group_game_btn(f"{E.MIC} {t('game_typing', lang)}", "typing", uid, primary),
         _group_game_btn(f"{E.BRAIN} {t('game_hangman', lang)}", "hangman", uid, primary)],
        [_group_game_btn(f"{E.TARGET} {t('game_guess_num', lang)}", "guess", uid, primary)],
        # گردونه شانس: به صورت لابی داخل گروه با تعیین تعداد برنده توسط سازنده
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


async def _send_pm_panel(message: Message, uid: int, lang: str, name: str):
    """نسخه پیوی — تمام بازی‌ها با WebApp مستقیم باز می‌شوند"""
    def wa(text, game, style_fn=primary):
        return _pm_game_btn(text, game, uid, lang, style_fn=style_fn)

    text = (
        f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=name)}</b>\n\n"
        f"{t('choose_game_hint', lang)}"
    )
    rows = [
        [wa(f"{E.PUZZLE} {t('game_2048_title', lang)}", "2048", primary),
         wa(f"{E.PUZZLE} {t('game_spuzzle', lang)}", "spuzzle", primary)],
        [wa(f"{E.SPARK} {t('game_samegame', lang)}", "samegame", primary)],
        [wa(f"{E.TARGET} {t('game_dooz', lang)}", "dooz", primary),
         wa(f"{E.TARGET} {t('game_doz4p', lang)}", "doz4p", primary)],
        [wa(f"{E.GAME} {t('game_connect4', lang)}", "connect4", success),
         wa(f"{E.CARD} {t('game_hokm_4p', lang)}", "hokm", success)],
        [wa(f"{E.PUZZLE} {t('game_rps', lang)}", "rps", primary),
         wa(f"{E.BRAIN} {t('game_memory', lang)}", "memory", primary)],
        [wa(f"{E.MIC} {t('game_typing', lang)}", "typing", primary),
         wa(f"{E.BRAIN} {t('game_hangman', lang)}", "hangman", primary)],
        [wa(f"{E.TARGET} {t('game_guess_num', lang)}", "guess", primary)],
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
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
        await cb.answer("Invalid request", show_alert=True)
        return

    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if uid != target_uid:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    bot_name = get_bot_username()
    deep_link = f"https://t.me/{bot_name}?start=game_{game}"
    chat_id = cb.message.chat.id if cb.message else 0
    game_url = f"{MINI_APP_URL}/?game={game}&uid={uid}&chat_id={chat_id}&lang={lang}"

    try:
        await cb.bot.send_message(
            uid,
            f"{E.GAME} <b>{t('open_in_pm_title', lang)}</b>\n\n"
            f"{E.INFO} {t('open_in_pm_body', lang)}",
            reply_markup=kb([[
                success(
                    f"{E.PLAY} {t('open_game_btn', lang)}",
                    web_app_url=game_url,
                )
            ]]),
            parse_mode=ParseMode.HTML,
        )
        await cb.answer(t("check_pm", lang), show_alert=True)
    except Exception:
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
