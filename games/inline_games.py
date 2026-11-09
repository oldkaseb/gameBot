"""حالت اینلاین بازی‌ها"""

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent,
)

from emojis import E, render_emojis
from langs import t, get_user_lang
from runtime import get_bot_username, check_forced_join

router = Router(name="inline_games")


INLINE_GAMES = [
    ("hokm",      "🃏", "حکم",           "بازی حکم ۲ و ۴ نفره"),
    ("dooz",      "❌", "دوز",            "دوز ۲ نفره"),
    ("doz4p",     "🔴", "دوز ۴ نفره",     "دوز چهار نفره"),
    ("connect4",  "🔴", "چهار در ردیف",   "بازی استراتژیک"),
    ("rps",       "🪨", "سنگ کاغذ قیچی",  "کلاسیک و سریع"),
    ("memory",    "🧠", "بازی حافظه",      "تقویت حافظه"),
    ("2048",      "🔢", "2048",            "پازل عددی"),
    ("samegame",  "✨", "جفت‌ها",          "پازل رنگی"),
    ("spuzzle",   "🧩", "پازل کشویی",     "پازل کلاسیک"),
    ("gardone",   "🎡", "گردونه شانس",     "قرعه‌کشی و شانس"),
]


@router.inline_query()
async def inline_games(query: InlineQuery):
    uid = query.from_user.id
    lang = get_user_lang(uid)
    bot_username = get_bot_username()
    q = (query.query or "").strip().lower()

    # چک عضویت اجباری
    missing = await check_forced_join(query.bot, uid)
    if missing:
        await query.answer(
            [],
            cache_time=1,
            is_personal=True,
            switch_pm_text=t("inline_join_required", lang),
            switch_pm_parameter="start",
        )
        return

    results = []
    for gtype, icon, name, desc in INLINE_GAMES:
        if q and q not in gtype.lower() and q not in name:
            continue

        deep_link = f"https://t.me/{bot_username}?start=game_{gtype}"
        kb_inline = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{E.GAME} باز کردن بازی",
                url=deep_link,
            )]
        ])

        msg_text = (
            f"{E.GAME}{E.PARTY} <b>بازی {name}</b>\n\n"
            f"{E.INFO} {desc}\n\n"
            f"{E.ROCKET} برای شروع، روی دکمه زیر بزنید:\n"
            f"⚠️ بازی‌ها فقط در گروه‌ها اجرا می‌شوند."
        )

        results.append(InlineQueryResultArticle(
            id=f"game_{gtype}",
            title=f"{icon} {name}",
            description=f"{desc} — برای شروع روی دکمه بزنید",
            input_message_content=InputTextMessageContent(
                message_text=render_emojis(msg_text),
                parse_mode=ParseMode.HTML,
            ),
            reply_markup=kb_inline,
        ))

    await query.answer(results, cache_time=1, is_personal=True)
