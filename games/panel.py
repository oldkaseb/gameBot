# -*- coding: utf-8 -*-
"""games/panel.py — منوی ۷ زبانه گروه با نام‌های کوتاه و استاندارد برای بازی‌ها"""

import os
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardButton,
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

# دیکشنری ۷ زبانه با نام‌های کوتاه برای منوی گروه و اشتراک‌گذاری
PANEL_I18N = {
    "fa": {
        "box_title": "گیم باکس راینو",
        "box_desc": "به گیم باکس راینو خوش اومدی رفیق!\nاینجا کلی بازی خفن برات جمع کردیم. لذت ببر دوست من:",
        "btn_all_games": "لیست بازی‌ها (مینی‌اپ)",
        "btn_group_games": "بازی‌های گروهی",
        "btn_wheel": "گردونه شانس",
        "lobby_header": "بازی‌های گروهی راینو",
        "lobby_sub": "بازی مورد نظر را انتخاب کنید:",
        "hokm4": "حکم ۴", "hokm2": "حکم ۲",
        "dooz2": "دوز ۲", "dooz4": "دوز ۴",
        "c4": "۴ در ردیف", "rps": "سنگ کاغذ قیچی",
        "memory": "حافظه", "guess": "حدس عدد",
        "invite_title": "دعوت به میز",
        "host": "میزبان",
        "join_btn": "ورود به بازی",
    },
    "en": {
        "box_title": "Rhino Game Box",
        "box_desc": "Welcome to Rhino Game Box my friend!\nAwesome games gathered in one place. Enjoy:",
        "btn_all_games": "Games List (Mini-App)",
        "btn_group_games": "Multiplayer Games",
        "btn_wheel": "Lucky Wheel",
        "lobby_header": "Rhino Multiplayer Games",
        "lobby_sub": "Pick a game to start:",
        "hokm4": "Hokm 4P", "hokm2": "Hokm 2P",
        "dooz2": "TicTacToe 2P", "dooz4": "TicTacToe 4P",
        "c4": "Connect 4", "rps": "Rock Paper",
        "memory": "Memory", "guess": "Number Guess",
        "invite_title": "Game Invite",
        "host": "Host",
        "join_btn": "Join Game",
    },
    "ar": {
        "box_title": "صندوق ألعاب رينو",
        "box_desc": "مرحباً بك في صندوق ألعاب رينو يا صديقي!\nاختر لعبتك المفضلة واستمتع:",
        "btn_all_games": "قائمة الألعاب (التطبيق)",
        "btn_group_games": "ألعاب جماعية",
        "btn_wheel": "عجلة الحظ",
        "lobby_header": "الألعاب الجماعية",
        "lobby_sub": "اختر اللعبة:",
        "hokm4": "حكم 4", "hokm2": "حكم 2",
        "dooz2": "إكس أو 2", "dooz4": "إكس أو 4",
        "c4": "أربعة بصف", "rps": "حجر ورقة",
        "memory": "الذاكرة", "guess": "تخمين الرقم",
        "invite_title": "دعوة للعب",
        "host": "المضيف",
        "join_btn": "دخول اللعبة",
    },
    "tr": {
        "box_title": "Rhino Oyun Kutusu",
        "box_desc": "Rhino Oyun Kutusuna hoş geldin dostum!\nHarika oyunlar seni bekliyor:",
        "btn_all_games": "Oyun Listesi (Mini-App)",
        "btn_group_games": "Grup Oyunları",
        "btn_wheel": "Çarkıfelek",
        "lobby_header": "Grup Oyunları",
        "lobby_sub": "Bir oyun seçin:",
        "hokm4": "Hokm 4K", "hokm2": "Hokm 2K",
        "dooz2": "XOX 2K", "dooz4": "XOX 4K",
        "c4": "Dörtlü Sıra", "rps": "Taş Kağıt",
        "memory": "Hafıza", "guess": "Sayı Tahmin",
        "invite_title": "Oyun Daveti",
        "host": "Kurucu",
        "join_btn": "Oyuna Katıl",
    },
    "ru": {
        "box_title": "Rhino Гейм Бокс",
        "box_desc": "Добро пожаловать в Rhino Game Box, друг!\nВыбирай игру и наслаждайся:",
        "btn_all_games": "Список игр (Mini-App)",
        "btn_group_games": "Групповые игры",
        "btn_wheel": "Колесо удачи",
        "lobby_header": "Групповые игры",
        "lobby_sub": "Выберите игру:",
        "hokm4": "Хокм 4", "hokm2": "Хокм 2",
        "dooz2": "Крестики 2", "dooz4": "Крестики 4",
        "c4": "4 в ряд", "rps": "Камень Ножницы",
        "memory": "Память", "guess": "Угадай число",
        "invite_title": "Приглашение в игру",
        "host": "Хост",
        "join_btn": "Войти в игру",
    },
    "de": {
        "box_title": "Rhino Spielbox",
        "box_desc": "Willkommen in der Rhino Spielbox, mein Freund!\nWähle ein Spiel:",
        "btn_all_games": "Spieleliste (Mini-App)",
        "btn_group_games": "Gruppenspiele",
        "btn_wheel": "Glücksrad",
        "lobby_header": "Gruppenspiele",
        "lobby_sub": "Wähle ein Spiel:",
        "hokm4": "Hokm 4P", "hokm2": "Hokm 2P",
        "dooz2": "TicTacToe 2", "dooz4": "TicTacToe 4",
        "c4": "4 Gewinnt", "rps": "Schere Stein",
        "memory": "Memory", "guess": "Zahl erraten",
        "invite_title": "Spieleinladung",
        "host": "Host",
        "join_btn": "Mitspielen",
    },
    "zh": {
        "box_title": "Rhino 游戏盒",
        "box_desc": "欢迎来到 Rhino 游戏盒，朋友！\n超多好玩的游戏等你体验：",
        "btn_all_games": "游戏列表 (小程序)",
        "btn_group_games": "多人联机游戏",
        "btn_wheel": "幸运转盘",
        "lobby_header": "多人游戏",
        "lobby_sub": "请选择一个游戏：",
        "hokm4": "王牌 4人", "hokm2": "王牌 2人",
        "dooz2": "井字棋 2人", "dooz4": "井字棋 4人",
        "c4": "四子连珠", "rps": "石头剪刀布",
        "memory": "记忆翻牌", "guess": "猜数字",
        "invite_title": "游戏邀请",
        "host": "房主",
        "join_btn": "加入游戏",
    },
}


def _pt(lang: str) -> dict:
    return PANEL_I18N.get(lang, PANEL_I18N["fa"])


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
    L = _pt(lang)
    start_param = f"hub__{chat_id}__{lang}"
    text = (
        f"{E.GAME}{E.SPARK} <b>{L['box_title']}</b>\n\n"
        f"{L['box_desc']}"
    )
    rows = [
        [make_miniapp_btn(f"{E.GAME} {L['btn_all_games']}", start_param, is_pm, success)],
        [primary(f"{E.PEOPLE} {L['btn_group_games']}", f"grp_lobby_menu_{uid}")],
        [success(f"{E.TARGET} {L['btn_wheel']}", f"gardone_start_{uid}")],
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
    uid = cb.from_user.id
    host_id = int(cb.data.split("_")[-1])
    lang = await _resolve_lang(uid)
    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return
    await cb.answer()
    cid = cb.message.chat.id
    is_pm = cb.message.chat.type == ChatType.PRIVATE
    L = _pt(lang)

    text = f"{E.PEOPLE}{E.GAME} <b>{L['lobby_header']}</b>\n\n{L['lobby_sub']}"
    rows = [
        [
            make_miniapp_btn(f"{E.CARD} {L['hokm4']}", f"hokm__{cid}__{lang}", is_pm, success),
            make_miniapp_btn(f"{E.CARD} {L['hokm2']}", f"hokm2p__{cid}__{lang}", is_pm, success),
        ],
        [
            make_miniapp_btn(f"{E.TARGET} {L['dooz2']}", f"dooz__{cid}__{lang}", is_pm, primary),
            make_miniapp_btn(f"{E.TARGET} {L['dooz4']}", f"doz4p__{cid}__{lang}", is_pm, primary),
        ],
        [
            make_miniapp_btn(f"{E.GAME} {L['c4']}", f"connect4__{cid}__{lang}", is_pm, success),
            make_miniapp_btn(f"{E.PUZZLE} {L['rps']}", f"rps__{cid}__{lang}", is_pm, primary),
        ],
        [
            make_miniapp_btn(f"{E.BRAIN} {L['memory']}", f"memory__{cid}__{lang}", is_pm, primary),
            make_miniapp_btn(f"{E.TARGET} {L['guess']}", f"guess__{cid}__{lang}", is_pm, success),
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


@router.inline_query(F.query.startswith("share_"))
async def inline_share_table(iq: InlineQuery):
    raw = iq.query.replace("share_", "", 1)
    parts = raw.split("__")
    game_type = parts[0] if len(parts) > 0 else "hokm"
    session_id = parts[1] if len(parts) > 1 else "room1"
    lang = await _resolve_lang(iq.from_user.id, getattr(iq.from_user, "language_code", None))
    L = _pt(lang)

    bot_user = get_bot_username()
    start_param = f"{game_type}__{session_id}__{lang}"
    join_url = f"https://t.me/{bot_user}/{MINI_APP_SHORT_NAME}?startapp={start_param}"

    msg_text = (
        f"{E.GAME}{E.SPARK} <b>{L['invite_title']} ({game_type.upper()})</b>\n\n"
        f"{E.USER} {L['host']}: <b>{iq.from_user.first_name}</b>"
    )
    markup = kb([[success(f"{E.PLAY} {L['join_btn']}", url=join_url)]])

    article = InlineQueryResultArticle(
        id=f"tbl_{game_type}_{session_id}",
        title=f"🎮 {L['invite_title']}: {game_type.upper()}",
        description=L["join_btn"],
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
