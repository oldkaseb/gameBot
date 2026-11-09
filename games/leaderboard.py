"""leaderboard — رتبه‌بندی بازیکنان"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from langs import t, get_user_lang
from utils.premium import primary, success, danger, back_btn, kb
from database import db

router = Router(name="leaderboard")

GAME_NAMES = {
    "hokm":         "🃏 حکم",
    "dooz":         "❌ دوز ۲ نفره",
    "doz4p":        "🔴 دوز ۴ نفره",
    "connect4":     "🔴 چهار در ردیف",
    "rps":          "🪨 سنگ کاغذ قیچی",
    "memory":       "🧠 حافظه",
    "2048":         "🔢 2048",
    "samegame":     "✨ جفت‌ها",
    "spuzzle":      "🧩 پازل",
    "hangman":      "🎯 حدس کلمه",
    "typing":       "⌨️ تایپ سرعتی",
    "number_guess": "🔢 حدس عدد",
    "gardone":      "🎡 گردونه",
}

MEDALS = ["🥇", "🥈", "🥉"]


def _medal(i: int) -> str:
    return MEDALS[i - 1] if i <= 3 else f"{i}."


async def _build_global_text() -> str:
    rows = await db.top_players(limit=10)
    text = f"{E.TROPHY}{E.CROWN} <b>برترین بازیکنان</b>\n\n"
    if not rows:
        text += f"{E.WARN} هنوز هیچ بازی‌ای انجام نشده."
        return text
    for i, r in enumerate(rows, 1):
        try:
            user = await db.get_user(r["user_id"])
            name = (user["first_name"] if user else None) or f"user_{r['user_id']}"
        except Exception:
            name = f"user_{r['user_id']}"
        text += f"{_medal(i)} <b>{name}</b> — {r['total']:,} برد\n"
    return text


def _kb_global(uid: int):
    game_buttons = [
        primary(gname, f"lb_game:{gtype}")
        for gtype, gname in GAME_NAMES.items()
    ]
    rows = [game_buttons[i:i + 2] for i in range(0, len(game_buttons), 2)]
    rows.append([back_btn(uid, "menu")])
    return kb(rows)


async def _show_global(event):
    text = await _build_global_text()
    markup = _kb_global(event.from_user.id)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text, reply_markup=markup, parse_mode=ParseMode.HTML
        )
    else:
        await event.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ────────── Entry points
@router.message(Command("lb"))
@router.message(Command("leaderboard"))
@router.message(F.text.in_({"برترین‌ها", "لیدربورد", "رتبه‌بندی", "leaderboard"}))
async def cmd_lb(msg: Message):
    await _show_global(msg)


@router.callback_query(F.data == "lb_menu")
async def cb_lb_menu(cb: CallbackQuery):
    await cb.answer()
    await _show_global(cb)


# ────────── Per-game
@router.callback_query(F.data.startswith("lb_game:"))
async def cb_lb_game(cb: CallbackQuery):
    try:
        gtype = cb.data.split(":")[1]
    except IndexError:
        await cb.answer("❌")
        return
    await cb.answer()

    rows = await db.top_players(game_type=gtype, limit=15)
    gname = GAME_NAMES.get(gtype, gtype)

    text = f"{E.TROPHY} <b>برترین‌های {gname}</b>\n\n"
    if not rows:
        text += f"{E.WARN} هنوز کسی در این بازی برنده نشده."
    else:
        for i, r in enumerate(rows, 1):
            name = r["first_name"] or f"user_{r['user_id']}"
            best = f" | ⏱ {r['best_time']:.1f}s" if r["best_time"] else ""
            text += f"{_medal(i)} <b>{name}</b> — {r['wins']} برد{best}\n"

    await cb.message.edit_text(
        text,
        reply_markup=kb([[back_btn(cb.from_user.id, "lb_menu")]]),
        parse_mode=ParseMode.HTML,
    )
