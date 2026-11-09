"""پازل کشویی — با رفع باگ قفل is_busy"""

import random, time
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import danger, primary, kb
from . import state

router = Router(name="spuzzle")

SIZE = 4


def _create_solvable():
    board = list(range(1, SIZE * SIZE)) + [0]
    empty = len(board) - 1
    for _ in range(300):
        moves = []
        if empty < SIZE * (SIZE - 1): moves.append("up")
        if empty >= SIZE: moves.append("down")
        if empty % SIZE < SIZE - 1: moves.append("left")
        if empty % SIZE > 0: moves.append("right")
        move = random.choice(moves)
        if move == "up":   swap = empty + SIZE
        elif move == "down": swap = empty - SIZE
        elif move == "left": swap = empty + 1
        else: swap = empty - 1
        board[empty], board[swap] = board[swap], board[empty]
        empty = swap
    return [board[i:i+SIZE] for i in range(0, len(board), SIZE)]


def _solved(b):
    flat = [x for row in b for x in row]
    return flat == list(range(1, SIZE * SIZE)) + [0]


async def _render(game, lang):
    gid = game["game_id"]
    b = game["board"]
    text = f"{E.PUZZLE}{E.SPARK} <b>{t('spuzzle_title', lang)}</b>\n\n{E.INFO} {t('sort_numbers', lang)}"
    rows = []
    for r in range(SIZE):
        row = []
        for c in range(SIZE):
            cell = b[r][c]
            row.append(danger(str(cell) if cell else " ", f"spuzzle_noop_{gid}"))
        rows.append(row)
    rows.append([danger("⬆️", f"spuzzle_move_{gid}_up")])
    rows.append([
        danger("⬅️", f"spuzzle_move_{gid}_left"),
        danger("⬇️", f"spuzzle_move_{gid}_down"),
        danger("➡️", f"spuzzle_move_{gid}_right"),
    ])
    rows.append([danger(f"{E.CROSS} {t('close_game', lang)}", f"spuzzle_close_{gid}")])
    return text, kb(rows)


@router.callback_query(F.data.startswith("spuzzle_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    try: target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    if state.user_has_game("spuzzle", chat_id, uid):
        await cb.answer(t("you_have_active_game", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id
    game = {
        "game_id": gid, "player_id": uid, "board": _create_solvable(),
        "start_time": time.time(), "is_busy": False,
    }
    state.register("spuzzle", chat_id, gid, game)
    text, markup = await _render(game, lang)
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


@router.callback_query(F.data.startswith("spuzzle_move_"))
async def move(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, direction = int(parts[2]), parts[3]
    except (ValueError, IndexError):
        await cb.answer("❌"); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    game = state.get("spuzzle", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    if game["is_busy"]:
        await cb.answer(t("wait_a_bit", lang)); return

    game["is_busy"] = True
    try:
        b = game["board"]
        er = ec = -1
        for r in range(SIZE):
            if 0 in b[r]:
                er, ec = r, b[r].index(0); break

        tr, tc = er, ec
        if direction == "up":    tr += 1
        elif direction == "down":  tr -= 1
        elif direction == "left":  tc += 1
        elif direction == "right": tc -= 1

        if not (0 <= tr < SIZE and 0 <= tc < SIZE):
            await cb.answer(t("invalid_move", lang)); return

        b[er][ec], b[tr][tc] = b[tr][tc], b[er][ec]

        if _solved(b):
            dur = int(time.time() - game["start_time"])
            final = (
                f"{E.TROPHY}{E.PARTY} <b>{t('puzzle_solved', lang, name=uid)}</b>\n\n"
                f"{E.CAL} {t('solved_in_seconds', lang, n=dur)}"
            )
            await cb.message.edit_text(final, reply_markup=None, parse_mode=ParseMode.HTML)
            state.unregister("spuzzle", chat_id, gid)
            await cb.answer()
            return

        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await cb.answer()
    finally:
        # ── باگ قبلی: این بلاک وجود نداشت → بعد از هر خطا قفل می‌ماند
        if state.exists("spuzzle", chat_id, gid):
            game["is_busy"] = False


@router.callback_query(F.data.startswith("spuzzle_close_"))
async def close(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("spuzzle", chat_id, gid)
    if not game or game["player_id"] != uid:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    state.unregister("spuzzle", chat_id, gid)
    await cb.answer(t("game_closed", lang))
    await cb.message.edit_text(f"{E.OK2} {t('game_closed', lang)}")


@router.callback_query(F.data.startswith("spuzzle_noop_"))
async def noop(cb: CallbackQuery): await cb.answer()
