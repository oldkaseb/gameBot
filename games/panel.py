# -*- coding: utf-8 -*-
"""games/panel.py — منوی جدید گروه (لیست بازی‌ها در مینی‌اپ، بازی‌های گروهی لابی‌دار، گردونه و تغییر زبان)"""

import os
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardButton, BufferedInputFile,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
)
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import LANGS, t, get_user_lang, set_user_lang, load_lang_from_db
from utils.premium import success, primary, danger, kb
from runtime import get_bot_username
from database import db

router = Router(name="panel")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")
MINI_APP_SHORT_NAME = os.environ.get("MINI_APP_SHORT_NAME", "RhinoGamesApp").strip() or "RhinoGamesApp"


async def _resolve_lang(uid: int, tg_lang_code: str | None = None) -> str:
    try:
        user = await db.get_user(uid)
        if user and user["language"]:
            load_lang_from_db(uid, user["language"])
            return user["language"]
    except Exception:
        pass
    if tg_lang_code:
        short = tg_lang_code.split("-")[0].lower()
        if short in LANGS:
            set_user_lang(uid, short)
            try:
                await db.set_language(uid, short)
            except Exception:
                pass
            return short
    return get_user_lang(uid)


def make_miniapp_btn(text: str, start_param: str, is_pm: bool, style_fn=success) -> InlineKeyboardButton:
    if is_pm:
        return style_fn(text, web_app_url=f"{MINI_APP_URL}/?startapp={start_param}")

    bot_user = get_bot_username()
    direct_url = f"https://t.me/{bot_user}/{MINI_APP_SHORT_NAME}?startapp={start_param}"
    return style_fn(text, url=direct_url)


def build_group_root_menu(uid: int, chat_id: int, lang: str, is_pm: bool) -> tuple[str, list]:
    """منوی اصلی گروه طبق ساختار درخواستی: ۱. لیست بازی‌ها (مینی‌اپ) ۲. بازی‌های گروهی ۳. گردونه + زبان"""
    start_param = f"hub__{chat_id}__{lang}"
    text = (
        f"{E.GAME}{E.SPARK} <b>گیم باکس راینو (RHINO GAME BOX)</b>\n\n"
        f"به گیم باکس راینو خوش اومدی رفیق!\n"
        f"از دکمه‌های زیر وارد مینی‌اپ یا بازی‌های گروهی شو:"
    )
    rows = [
        [make_miniapp_btn(f"{E.GAME} لیست بازی‌ها (ورود به مینی‌اپ)", start_param, is_pm, success)],
        [primary(f"{E.PEOPLE} بازی‌های گروهی (لابی)", f"grp_lobby_menu_{uid}")],
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [
            primary(f"{E.GLOBE} {t('btn_change_lang', lang)}", f"grp_lang_menu_{uid}"),
            danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}"),
        ],
    ]
    return text, rows


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = await _resolve_lang(uid, getattr(message.from_user, "language_code", None))
    is_pm = message.chat.type == ChatType.PRIVATE
    text, rows = build_group_root_menu(uid, message.chat.id, lang, is_pm)
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("grp_root_"))
async def cb_group_root(cb: CallbackQuery):
    uid = cb.from_user.id
    host_id = int(cb.data.split("_")[-1])
    lang = await _resolve_lang(uid, getattr(cb.from_user, "language_code", None))
    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    is_pm = cb.message.chat.type == ChatType.PRIVATE
    text, rows = build_group_root_menu(uid, cb.message.chat.id, lang, is_pm)
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("grp_lobby_menu_"))
async def cb_group_lobby_games(cb: CallbackQuery):
    """زیرمنوی بازی‌های گروهی که نیاز به لابی دارند"""
    uid = cb.from_user.id
    host_id = int(cb.data.split("_")[-1])
    lang = await _resolve_lang(uid)
    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    cid = cb.message.chat.id
    is_pm = cb.message.chat.type == ChatType.PRIVATE

    text = (
        f"{E.PEOPLE}{E.GAME} <b>بازی‌های گروهی و لابی‌دار راینو</b>\n\n"
        f"بازی مورد نظر را انتخاب کنید (می‌توانید در گروه لابی بسازید یا مستقیماً در مینی‌اپ میز تشکیل دهید):"
    )
    rows = [
        [
            make_miniapp_btn(f"{E.CARD} حکم ۴ نفره", f"hokm__{cid}__{lang}", is_pm, success),
            make_miniapp_btn(f"{E.CARD} حکم ۲ نفره", f"hokm2p__{cid}__{lang}", is_pm, success),
        ],
        [
            make_miniapp_btn(f"{E.TARGET} دوز ۲ نفره", f"dooz__{cid}__{lang}", is_pm, primary),
            make_miniapp_btn(f"{E.TARGET} دوز ۴ نفره", f"doz4p__{cid}__{lang}", is_pm, primary),
        ],
        [
            make_miniapp_btn(f"{E.GAME} چهار در یک ردیف", f"connect4__{cid}__{lang}", is_pm, success),
            make_miniapp_btn(f"{E.PUZZLE} سنگ کاغذ قیچی", f"rps__{cid}__{lang}", is_pm, primary),
        ],
        [
            make_miniapp_btn(f"{E.BRAIN} بازی حافظه", f"memory__{cid}__{lang}", is_pm, primary),
            make_miniapp_btn(f"{E.TARGET} حدس عدد همگانی", f"guess__{cid}__{lang}", is_pm, success),
        ],
        [danger(f"{E.ARROW} {t('btn_back', lang)}", f"grp_root_{uid}")],
    ]
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("grp_lang_menu_"))
async def cb_group_lang_menu(cb: CallbackQuery):
    uid = cb.from_user.id
    host_id = int(cb.data.split("_")[-1])
    lang = await _resolve_lang(uid)
    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    rows = []
    items = list(LANGS.items())
    for i in range(0, len(items), 2):
        chunk = items[i:i + 2]
        rows.append([primary(f"{E.GLOBE} {lbl.split(' ', 1)[-1]}", f"grp_setlang_{code}_{uid}") for code, lbl in chunk])
    rows.append([danger(f"{E.ARROW} {t('btn_back', lang)}", f"grp_root_{uid}")])
    await cb.message.edit_text(
        f"{E.GLOBE} <b>{t('choose_lang', lang)}</b>",
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("grp_setlang_"))
async def cb_group_set_lang(cb: CallbackQuery):
    parts = cb.data.split("_")
    lang_code = parts[2]
    host_id = int(parts[3])
    uid = cb.from_user.id
    if uid != host_id:
        await cb.answer(t("not_your_panel", "fa"), show_alert=True)
        return
    if lang_code in LANGS:
        set_user_lang(uid, lang_code)
        try:
            await db.set_language(uid, lang_code)
        except Exception:
            pass
    await cb.answer(t("lang_saved", lang_code))
    is_pm = cb.message.chat.type == ChatType.PRIVATE
    text, rows = build_group_root_menu(uid, cb.message.chat.id, lang_code, is_pm)
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


# پشتیبانی از اشتراک‌گذاری مستقیم میز بازی در چت‌ها (Inline Share)
@router.inline_query(F.query.startswith("share_"))
async def inline_share_table(iq: InlineQuery):
    """وقتی کاربر گزینه اشتراک‌گذاری لینک میز بازی را می‌زند، بنر و دکمه پیوستن برای چت انتخاب‌شده ارسال می‌شود"""
    raw = iq.query.replace("share_", "", 1)
    parts = raw.split("__")
    game_type = parts[0] if len(parts) > 0 else "hokm"
    session_id = parts[1] if len(parts) > 1 else "room1"
    extra_info = parts[2] if len(parts) > 2 else ""

    bot_user = get_bot_username()
    start_param = f"{game_type}__{session_id}__fa"
    join_url = f"https://t.me/{bot_user}/{MINI_APP_SHORT_NAME}?startapp={start_param}"

    titles = {
        "hokm": "میز حکم ۴ نفره راینو",
        "hokm2p": "میز حکم ۲ نفره راینو",
        "dooz": "میز بازی دوز ۲ نفره",
        "doz4p": "میز بازی دوز ۴ نفره",
        "connect4": "میز بازی چهار در یک ردیف",
        "rps": f"میز سنگ کاغذ قیچی (سقف برد: {extra_info or 3})",
        "memory": "میز مسابقه حافظه",
        "guess": f"مسابقه حدس عدد همگانی ({extra_info or '1-100'})",
    }
    title = titles.get(game_type, f"میز بازی {game_type}")

    msg_text = (
        f"{E.GAME}{E.SPARK} <b>{title}</b>\n\n"
        f"{E.USER} میزبان: <b>{iq.from_user.first_name}</b>\n"
        f"{E.INFO} شما به این میز بازی دعوت شده‌اید! برای ورود مستقیم و بازی روی دکمه زیر بزنید:"
    )
    markup = kb([[success(f"{E.PLAY} پیوستن مستقیم به میز بازی", url=join_url)]])

    article = InlineQueryResultArticle(
        id=f"tbl_{game_type}_{session_id}",
        title=f"📨 ارسال دعوت‌نامه: {title}",
        description="برای ارسال کارت دعوت همراه با دکمه ورود به بازی روی این گزینه بزنید",
        input_message_content=InputTextMessageContent(
            message_text=msg_text,
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=markup,
    )
    await iq.answer([article], cache_time=1, is_personal=True)


@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass
