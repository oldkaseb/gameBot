"""پنل بازی‌ها — فقط در گروه"""

from aiogram import Router, F
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, btn, back_btn, kb
from aiogram.types import CallbackQuery, Message, WebAppInfo, InlineKeyboardButton

router = Router(name="panel")

# آدرس دامنه مینی اپ شما (باید HTTPS باشد)
MINI_APP_URL = "https://games.rhinokaseb.abrdns.com" 

def _check_owner(cb: CallbackQuery) -> bool:
    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return False
    return cb.from_user.id == target

def webapp_btn(text: str, path: str) -> InlineKeyboardButton:
    """دکمه ورود به مینی اپ"""
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=f"{MINI_APP_URL}{path}"))


@router.message(Command("rsgame"))
@router.message(F.text.in_({
    # فارسی
    "بازی", "بازی‌ها", "بازیها", "پنل",
    # English
    "game", "games", "panel", "play",
    # العربية
    "لعبة", "ألعاب", "لعب",
    # Türkçe
    "oyun", "oyunlar",
    # Русский
    "игра", "игры",
    # Deutsch
    "spiel", "spiele",
    # 中文
    "游戏",
}))
async def show_panel(message: Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(t("panel_group_only", lang), parse_mode=ParseMode.HTML)
        return

    text = f"{E.GAME}{E.PARTY} <b>{t('game_panel', lang, name=message.from_user.first_name)}</b>\n\n👇 یک بازی انتخاب کنید:"
    
    # ═══════════════════════════════════════════════
    # لیست همه بازی‌ها بدون کتگوری
    # ═══════════════════════════════════════════════
    rows = [
        # --- تک‌نفره (مستقیم به مینی اپ) ---
        [webapp_btn(f"{E.PUZZLE} 2048", f"/play?game=2048&uid={uid}"),
         webapp_btn(f"{E.PUZZLE} پازل کششی", f"/play?game=spuzzle&uid={uid}")],
        [webapp_btn(f"{E.SPARK} جفت‌ها", f"/play?game=samegame&uid={uid}")],
        
        # --- چندنفره (مستقیم به لابی ربات) ---
        [primary(f"{E.TARGET} دوز ۲ نفره", f"lobby_dooz_{uid}"),
         primary(f"{E.TARGET} دوز ۴ نفره", f"lobby_doz4p_{uid}")],
        [success(f"{E.GAME} چهار در ردیف", f"lobby_connect4_{uid}"),
         success(f"{E.CARD} حکم ۴ نفره", f"lobby_hokm_{uid}")],
        [primary("🪨 سنگ کاغذ قیچی", f"lobby_rps_{uid}"),
         primary(f"{E.BRAIN} حافظه", f"lobby_memory_{uid}")],
        
        # --- چت‌محور (مستقیم به مینی اپ چت) ---
        [webapp_btn(f"{E.MIC} تایپ سرعتی", f"/chat?game=typing&uid={uid}"),
         webapp_btn(f"{E.BRAIN} حدس کلمه", f"/chat?game=hangman&uid={uid}")],
        [webapp_btn(f"{E.TARGET} حدس عدد", f"/chat?game=guess&uid={uid}")],
        
        # --- سایر ---
        [success(f"{E.TARGET} گردونه شانس", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}", f"rsgame_close_{uid}")],
    ]
    
    await message.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("rsgame_close_"))
async def close(cb: CallbackQuery):
    await cb.answer()
    try: await cb.message.delete()
    except: pass


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
        [success(f"{E.TARGET} {t('game_gardone', lang)}", f"gardone_start_{uid}")],
        [danger(f"{E.CROSS} {t('btn_close', lang)}",    f"rsgame_close_{uid}")],
    ]
    try:
        await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass
