"""بازی جفت‌ها — SameGame با رفع باگ حافظه"""

import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import danger, kb
from . import state

router = Router(name="samegame")

W, H = 10, 10
COLORS = ["🟥", "🟩", "🟦", "🟨", "🟪"]
EMPTY = "⬛️"


def _create():
    return [[random.choice(COLORS) for _ in range(W)] for _ in range(H)]


def _find_group(b, r0, c0):
    color = b[r0][c0]
    if color == EMPTY: return []
    q, grp = [(r0, c0)], {(r0, c0)}
    while q:
        r, c = q.pop()
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and b[nr][nc] == color and (nr, nc) not in grp:
                grp.add((nr, nc)); q.append((nr, nc))
    return list(grp)


def _refill(b):
    for r in range(H):
        for c in range(W):
            if b[r][c] == EMPTY:
                b[r][c] = random.choice(COLORS)
    return b


def _game_over(b):
    for r in range(H):
        for c in range(W):
            if b[r][c] != EMPTY:
                if c + 1 < W and b[r][c] == b[r][c+1]: return False
                if r + 1 < H and b[r][c] == b[r+1][c]: return False
    return True


async def _render(game, lang, finished=False):
    gid = game["game_id"]
    b = game["board"]

    text = (
        f"{E.PUZZLE}{E.SPARK} <b>{t('samegame_title', lang)}</b>\n"
        f"{E.CHART} {t('score', lang)}: <b>{game['score']}</b>"
    )
    if finished:
        text += f"\n\n{E.SKULL}{E.CROSS} <b>{t('no_more_moves', lang)}</b>"

    rows = []
    for r in range(H):
        row = []
        for c in range(W):
            action = "noop" if finished else "click"
            row.append(danger(b[r][c], f"samegame_{action}_{gid}_{r}_{c}"))
        rows.append(row)

    if not finished:
        rows.append([danger(f"{E.CROSS} {t('close_game', lang)}", f"samegame_close_{gid}")])
    return text, kb(rows)


@router.callback_query(F.data.startswith("samegame_start_"))
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

    if state.user_has_game("samegame", chat_id, uid):
        await cb.answer(t("you_have_active_game", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id

    game = {
        "game_id": gid, "player_id": uid,
        "board": _create(), "score": 0, "is_busy": False,
    }
    state.register("samegame", chat_id, gid, game)

    text, markup = await _render(game, lang)
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


@router.callback_query(F.data.startswith("samegame_click_"))
async def click(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, r, c = int(parts[2]), int(parts[3]), int(parts[4])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    game = state.get("samegame", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    if game["is_busy"]:
        await cb.answer(t("wait_a_bit", lang)); return

    grp = _find_group(game["board"], r, c)
    if len(grp) < 2:
        await cb.answer(t("need_two_blocks", lang), show_alert=True); return

    game["is_busy"] = True
    try:
        game["score"] += len(grp)
        for rr, cc in grp:
            game["board"][rr][cc] = EMPTY
        game["board"] = _refill(game["board"])

        if _game_over(game["board"]):
            text, markup = await _render(game, lang, finished=True)
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            state.unregister("samegame", chat_id, gid)
        else:
            text, markup = await _render(game, lang)
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await cb.answer()
    finally:
        if state.exists("samegame", chat_id, gid):
            game["is_busy"] = False


@router.callback_query(F.data.startswith("samegame_close_"))
async def close(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except (ValueError, IndexError): await cb.answer("❌"); return
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("samegame", chat_id, gid)
    if not game or game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    state.unregister("samegame", chat_id, gid)
    await cb.answer(t("game_closed", lang))
    await cb.message.edit_text(f"{E.OK2} {t('game_closed', lang)}")


@router.callback_query(F.data.startswith("samegame_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer()
