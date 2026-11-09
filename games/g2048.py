"""بازی 2048 — با رفع باگ حافظه و قفل"""

import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import danger, kb
from . import state

router = Router(name="g2048")

TILE_EMOJI = {
    0: "⬛️", 2: "2️⃣", 4: "4️⃣", 8: "8️⃣", 16: "1️⃣6️⃣", 32: "3️⃣2️⃣",
    64: "6️⃣4️⃣", 128: "1️⃣2️⃣8️⃣", 256: "2️⃣5️⃣6️⃣", 512: "5️⃣1️⃣2️⃣",
    1024: "🔟2️⃣4️⃣", 2048: "🏆",
}


def _new_board():
    b = [[0] * 4 for _ in range(4)]
    _add_tile(b); _add_tile(b)
    return b


def _add_tile(b):
    cells = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
    if cells:
        r, c = random.choice(cells)
        b[r][c] = 2 if random.random() < 0.9 else 4
    return b


def _can_move(b):
    for r in range(4):
        for c in range(4):
            if b[r][c] == 0: return True
            if c < 3 and b[r][c] == b[r][c+1]: return True
            if r < 3 and b[r][c] == b[r+1][c]: return True
    return False


def _transform(b, d):
    if d == "left": return b
    if d == "right": return [row[::-1] for row in b]
    if d == "up": return [list(col) for col in zip(*b)]
    if d == "down":
        t = [list(col) for col in zip(*b)]
        return [row[::-1] for row in t]


def _reverse(b, d):
    if d == "left": return b
    if d == "right": return [row[::-1] for row in b]
    if d == "up": return [list(col) for col in zip(*b)]
    if d == "down":
        b = [row[::-1] for row in b]
        return [list(col) for col in zip(*b)]


def _move_left(b):
    new, score, moved = [], 0, False
    for row in b:
        comp = [x for x in row if x != 0]
        out, i = [], 0
        while i < len(comp):
            if i + 1 < len(comp) and comp[i] == comp[i+1]:
                v = comp[i] * 2
                out.append(v); score += v; i += 2
            else:
                out.append(comp[i]); i += 1
        out.extend([0] * (4 - len(out)))
        new.append(out)
    if new != b: moved = True
    return new, score, moved


def _render(game, lang):
    gid = game["game_id"]
    b = game["board"]
    header = (
        f"{E.PUZZLE}{E.SPARK} <b>{t('game_2048_title', lang)}</b>\n"
        f"{E.CHART} {t('score', lang)}: <b>{game['score']}</b>"
    )
    rows = []
    for r in range(4):
        rows.append([
            danger(TILE_EMOJI.get(b[r][c], str(b[r][c])), f"2048_noop_{gid}")
            for c in range(4)
        ])
    rows.append([
        danger(" ", f"2048_noop_{gid}"),
        danger("⬆️", f"2048_move_{gid}_up"),
        danger(" ", f"2048_noop_{gid}"),
    ])
    rows.append([
        danger("⬅️", f"2048_move_{gid}_left"),
        danger(" ", f"2048_noop_{gid}"),
        danger("➡️", f"2048_move_{gid}_right"),
    ])
    rows.append([
        danger(" ", f"2048_noop_{gid}"),
        danger("⬇️", f"2048_move_{gid}_down"),
        danger(" ", f"2048_noop_{gid}"),
    ])
    rows.append([danger(f"{E.CROSS} {t('close_game', lang)}", f"2048_close_{gid}")])
    return header, kb(rows)


@router.callback_query(F.data.startswith("2048_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    # ── باگ قبلی: بازی قدیمی کاربر چک نمی‌شد
    if state.user_has_game("2048", chat_id, uid):
        await cb.answer(t("you_have_active_game", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id

    game = {
        "game_id": gid, "player_id": uid,
        "board": _new_board(), "score": 0,
        "is_busy": False,
    }
    state.register("2048", chat_id, gid, game)

    header, markup = _render(game, lang)
    await sent.edit_text(header, reply_markup=markup, parse_mode=ParseMode.HTML)
    try:
        await cb.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("2048_move_"))
async def move(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, direction = int(parts[2]), parts[3]
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    game = state.get("2048", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return

    if game["is_busy"]:
        await cb.answer(t("wait_a_bit", lang)); return
    game["is_busy"] = True
    try:
        transformed = _transform(game["board"], direction)
        moved_board, inc, moved = _move_left(transformed)
        final = _reverse(moved_board, direction)

        if not moved:
            await cb.answer(t("invalid_move", lang)); return

        game["board"] = _add_tile(final)
        game["score"] += inc

        header, markup = _render(game, lang)

        # ── شرط پایان
        if any(2048 in row for row in game["board"]):
            header += f"\n\n{E.TROPHY}{E.PARTY} <b>{t('you_won_2048', lang)}</b>"
            await cb.message.edit_text(header, reply_markup=None, parse_mode=ParseMode.HTML)
            state.unregister("2048", chat_id, gid)
        elif not _can_move(game["board"]):
            header += f"\n\n{E.SKULL}{E.CROSS} <b>{t('you_lost_2048', lang)}</b>"
            await cb.message.edit_text(header, reply_markup=None, parse_mode=ParseMode.HTML)
            state.unregister("2048", chat_id, gid)
        else:
            await cb.message.edit_text(header, reply_markup=markup, parse_mode=ParseMode.HTML)
    finally:
        # ── باگ قبلی: قفل در صورت خطا باز نمی‌شد
        if state.exists("2048", chat_id, gid):
            game["is_busy"] = False


@router.callback_query(F.data.startswith("2048_close_"))
async def close(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid = int(parts[2])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("2048", chat_id, gid)
    if not game or game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return

    state.unregister("2048", chat_id, gid)
    await cb.answer(t("game_closed", lang))
    await cb.message.edit_text(f"{E.OK2} {t('game_closed', lang)}")


@router.callback_query(F.data.startswith("2048_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer()
