"""دوز ۴ نفره — رفع باگ active_games['doz4p'] = {chat_id: {}}"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, danger, primary, kb
from . import state

router = Router(name="doz4p")

SIZE = 10
SYMBOLS = ["🔴", "🔵", "🟢", "🟡"]


def _winner(b, sym):
    for r in range(SIZE):
        for c in range(SIZE - 3):
            if all(b[r][c+i] == sym for i in range(4)): return True
    for r in range(SIZE - 3):
        for c in range(SIZE):
            if all(b[r+i][c] == sym for i in range(4)): return True
    for r in range(3, SIZE):
        for c in range(SIZE - 3):
            if all(b[r-i][c+i] == sym for i in range(4)): return True
    for r in range(SIZE - 3):
        for c in range(SIZE - 3):
            if all(b[r+i][c+i] == sym for i in range(4)): return True
    return False


async def _render(game, lang, finished=False):
    gid = game["game_id"]
    b = game["board"]
    plist = "\n".join(f"{p['symbol']} {p['name']}" for p in game["players_info"])
    if finished:
        text = f"{E.TARGET} <b>{t('doz4p_title', lang)} — {t('finished', lang)}</b>\n\n{plist}"
    else:
        tp = game["players_info"][game["turn_index"]]
        text = f"{E.TARGET} <b>{t('doz4p_title', lang)}</b>\n\n{plist}\n\n{E.ARROW} {t('turn_of', lang)}: {tp['symbol']} {tp['name']}"

    rows = []
    for r in range(SIZE):
        row = []
        for c in range(SIZE):
            action = "noop" if finished else "move"
            row.append(danger(b[r][c], f"doz4p_{action}_{gid}_{r}_{c}"))
        rows.append(row)
    return text, kb(rows)


@router.callback_query(F.data.startswith("doz4p_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    try: target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id

    # ── ⚠️ باگ اصلی: اینجا قبلاً `active_games['doz4p'] = {chat_id: {}}` بود!
    # حالا از state.register استفاده می‌شود که دیکشنری را نمی‌شکند
    game = {
        "game_id": gid, "status": "joining",
        "players_info": [{"id": uid, "name": cb.from_user.first_name, "symbol": SYMBOLS[0]}],
        "board": [["▪️"] * SIZE for _ in range(SIZE)],
        "turn_index": 0, "player_id": uid,
    }
    state.register("doz4p", chat_id, gid, game)

    text = (
        f"{E.PARTY}{E.TARGET} <b>{t('doz4p_created', lang, name=cb.from_user.first_name)}</b> (1/4)\n\n"
        f"{E.INFO} {t('waiting_players', lang)}\n\n{E.LINK} @RHINOBOT_TM"
    )
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"doz4p_join_{gid}")]])
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


@router.callback_query(F.data.startswith("doz4p_join_"))
async def join(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except (ValueError, IndexError):
        await cb.answer("❌"); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("doz4p", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["status"] != "joining":
        await cb.answer(t("game_already_started", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["players_info"]):
        await cb.answer(t("already_joined", lang), show_alert=True); return
    if len(game["players_info"]) >= 4:
        await cb.answer(t("game_full", lang), show_alert=True); return

    n = len(game["players_info"])
    game["players_info"].append({
        "id": uid, "name": cb.from_user.first_name, "symbol": SYMBOLS[n],
    })

    if n + 1 < 4:
        names = "، ".join(p["name"] for p in game["players_info"])
        text = (
            f"{E.PARTY} <b>{t('doz4p_created', lang, name=game['players_info'][0]['name'])}</b> "
            f"({n+1}/4)\n\n{E.DISGUISE} {names}\n\n{E.LINK} @RHINOBOT_TM"
        )
        markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"doz4p_join_{gid}")]])
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        game["status"] = "playing"
        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("doz4p_move_"))
async def move(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, r, c = int(parts[2]), int(parts[3]), int(parts[4])
    except (ValueError, IndexError):
        await cb.answer("❌"); return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("doz4p", chat_id, gid)
    if not game or game["status"] != "playing":
        await cb.answer(t("game_not_active", lang), show_alert=True); return

    tp = game["players_info"][game["turn_index"]]
    if uid != tp["id"]:
        await cb.answer(t("not_your_turn", lang), show_alert=True); return
    if game["board"][r][c] != "▪️":
        await cb.answer(t("cell_occupied", lang), show_alert=True); return

    sym = tp["symbol"]
    game["board"][r][c] = sym

    is_won = _winner(game["board"], sym)
    is_draw = all(cell != "▪️" for row in game["board"] for cell in row) and not is_won

    if is_won or is_draw:
        game["status"] = "finished"
        text, markup = await _render(game, lang, finished=True)
        if is_won:
            text += f"\n\n{E.TROPHY} {t('game_winner', lang, name=f'{sym} {tp["name"]}')}"
        else:
            text += f"\n\n{t('game_draw', lang)}"
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        state.unregister("doz4p", chat_id, gid)
    else:
        game["turn_index"] = (game["turn_index"] + 1) % 4
        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("doz4p_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer()
