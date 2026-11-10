"""پنل بازی‌ها — لیست همه بازی‌ها بدون دسته‌بندی"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, WebAppInfo, InlineKeyboardButton
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command
from urllib.parse import urlencode

from emojis import E, BASE_MAP, EMOJI_ID_RE
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb

router = Router(name="panel")

MINI_APP_URL = "https://games.rhinokaseb.abrdns.com"


def _clean_btn_text(text: str) -> str:
    if not text:
        return "·"
    return EMOJI_ID_RE.sub(lambda m: BASE_MAP.get(m.group(1), "⭐"), text).strip() or "·"


def webapp_btn(text: str, game: str, uid: int) -> InlineKeyboardButton:
    params = urlencode({"game": game, "uid": uid})
    url = f"{MINI_APP_URL}/?{params}"
    return InlineKeyboardButton(text=_clean_btn_text(text), web_app=WebAppInfo(url=url))


@router.message(Command("rsgame"))
@router.message(F.text.in_({"بازی", "بازی‌ها", "بازیها", "پنل", "game", "games", "panel"}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(t("panel_group_only", lang), parse_mode=ParseMode.HTML)
        return

    text = f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=message.from_user.first_name)}</b>\n\n👇 یک بازی انتخاب کنید:"

    rows = [
        # ── تک‌نفره (مستقیم به مینی‌اپ)
        [webapp_btn(f"{E.PUZZLE} 2048", "2048", uid),
         webapp_btn(f"{E.PUZZLE} پازل کششی", "spuzzle", uid)],
        [webapp_btn(f"{E.SPARK} جفت‌ها", "samegame", uid)],

        # ── چندنفره (لابی ربات)
        [primary(f"{E.TARGET} دوز ۲ نفره", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} دوز ۴ نفره", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} چهار در ردیف", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} حکم ۴ نفره", f"lobby_hokm_{uid}")],
        [primary("🪨 سنگ کاغذ قیچی", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} حافظه", f"lobby_memory_{uid}")],

        # ── چت‌محور (مستقیم به مینی‌اپ چت)
        [webapp_btn(f"{E.MIC} تایپ سرعتی", "typing", uid),
         webapp_btn(f"{E.BRAIN} حدس کلمه", "hangman", uid)],
        [webapp_btn(f"{E.TARGET} حدس عدد", "guess", uid)],

        # ── سایر
        [success(f"{E.TARGET} گردونه شانس", f"gardone_start_{uid}")],
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
