"""بازی چهار در یک ردیف"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, danger, kb
from . import state

router = Router(name="connect4")

ROWS, COLS = 6, 7


def _check_win(b, sym):
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(b[r][c+i] == sym for i in range(4)): return True
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(b[r+i][c] == sym for i in range(4)): return True
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(b[r-i][c+i] == sym for i in range(4)): return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(b[r+i][c+i] == sym for i in range(4)): return True
    return False


def _render(game, lang, finished=False):
    gid = game["game_id"]
    b = game["board"]
    p1, p2 = game["players_info"]
    if finished:
        text = f"{E.PARTY} <b>{t('c4_title', lang)}</b>\n{p1['name']} ({p1['symbol']}) ⚔️ {p2['name']} ({p2['symbol']})"
    else:
        tp = next(p for p in game["players_info"] if p["id"] == game["turn"])
        text = f"{E.GAME} <b>{t('c4_title', lang)}</b>\n{p1['name']} ({p1['symbol']}) ⚔️ {p2['name']} ({p2['symbol']})\n\n{E.ARROW} {t('turn_of', lang)}: {tp['name']}"

    rows = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            action = "noop" if finished else "move"
            row.append(danger(b[r][c], f"connect4_{action}_{gid}_{c}"))
        rows.append(row)
    return text, kb(rows)


@router.callback_query(F.data.startswith("connect4_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except: await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id
    state.register("connect4", chat_id, gid, {
        "game_id": gid, "status": "joining",
        "players_info": [{"id": uid, "name": cb.from_user.first_name, "symbol": "🔴"}],
        "board": [["⚪️"] * COLS for _ in range(ROWS)],
        "turn": None, "player_id": uid,
    })
    text = f"{E.PARTY} <b>{t('c4_created', lang, name=cb.from_user.first_name)}</b>\n\n{E.LINK} @RHINOBOT_TM"
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"connect4_join_{gid}")]])
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


@router.callback_query(F.data.startswith("connect4_join_"))
async def join(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("connect4", chat_id, gid)
    if not game or game["status"] != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["players_info"]):
        await cb.answer(t("already_joined", lang), show_alert=True); return
    if len(game["players_info"]) >= 2:
        await cb.answer(t("game_full", lang), show_alert=True); return

    game["players_info"].append({"id": uid, "name": cb.from_user.first_name, "symbol": "🟡"})
    game["status"] = "playing"
    game["turn"] = game["players_info"][0]["id"]

    text, markup = _render(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("connect4_move_"))
async def move(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, col = int(parts[2]), int(parts[3])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("connect4", chat_id, gid)
    if not game or game["status"] != "playing":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if uid not in [p["id"] for p in game["players_info"]]:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    if uid != game["turn"]:
        await cb.answer(t("not_your_turn", lang), show_alert=True); return

    row = -1
    for r in range(ROWS - 1, -1, -1):
        if game["board"][r][col] == "⚪️":
            row = r; break
    if row == -1:
        await cb.answer(t("c4_col_full", lang), show_alert=True); return

    player = next(p for p in game["players_info"] if p["id"] == uid)
    game["board"][row][col] = player["symbol"]
    is_won = _check_win(game["board"], player["symbol"])
    is_draw = all(c != "⚪️" for r in game["board"] for c in r) and not is_won

    if is_won or is_draw:
        game["status"] = "finished"
        text, markup = _render(game, lang, True)
        text += f"\n\n{E.TROPHY} {t('game_winner', lang, name=player['name'])}" if is_won else f"\n\n{t('game_draw', lang)}"
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        state.unregister("connect4", chat_id, gid)
    else:
        next_p = next(p for p in game["players_info"] if p["id"] != uid)
        game["turn"] = next_p["id"]
        text, markup = _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("connect4_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer(t("finished", get_user_lang(cb.from_user.id)))
