"""بازی دوز ۲ نفره"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, danger, kb
from . import state

router = Router(name="dooz")


def _check_win(b, sym):
    return (
        any(all(c == sym for c in r) for r in b)
        or any(all(b[r][c] == sym for r in range(3)) for c in range(3))
        or all(b[i][i] == sym for i in range(3))
        or all(b[i][2-i] == sym for i in range(3))
    )


@router.callback_query(F.data.startswith("dooz_start_2p_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError): await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id
    state.register("dooz", chat_id, gid, {
        "game_id": gid, "status": "joining",
        "players_info": [{"id": uid, "name": cb.from_user.first_name, "symbol": "❌"}],
        "board": [[" "]*3 for _ in range(3)],
        "turn": None, "player_id": uid,
    })
    text = (
        f"{E.PARTY}{E.TARGET} <b>{t('dooz_created', lang, name=cb.from_user.first_name)}</b>\n\n"
        f"{E.INFO} {t('waiting_players', lang)}\n\n{E.LINK} @RHINOBOT_TM"
    )
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"dooz_join_{gid}")]])
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


@router.callback_query(F.data.startswith("dooz_join_"))
async def join(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("dooz", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["status"] != "joining":
        await cb.answer(t("game_already_started", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["players_info"]):
        await cb.answer(t("already_joined", lang), show_alert=True); return
    if len(game["players_info"]) >= 2:
        await cb.answer(t("game_full", lang), show_alert=True); return

    game["players_info"].append({"id": uid, "name": cb.from_user.first_name, "symbol": "⭕️"})
    game["status"] = "playing"
    game["turn"] = game["players_info"][0]["id"]

    p1, p2 = game["players_info"]
    text = (
        f"{E.PARTY} <b>{t('dooz_started', lang, name1=p1['name'], name2=p2['name'])}</b>\n\n"
        f"{E.ARROW} {t('dooz_your_turn', lang, name=p1['name'], symbol=p1['symbol'])}"
    )
    rows = [[danger(" ", f"dooz_move_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("dooz_move_"))
async def move(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, idx = int(parts[2]), int(parts[3])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("dooz", chat_id, gid)
    if not game or game["status"] != "playing":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if uid not in [p["id"] for p in game["players_info"]]:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    if uid != game["turn"]:
        await cb.answer(t("not_your_turn", lang), show_alert=True); return

    r, c = divmod(idx, 3)
    if game["board"][r][c] != " ":
        await cb.answer(t("cell_occupied", lang), show_alert=True); return

    player = next(p for p in game["players_info"] if p["id"] == uid)
    sym = player["symbol"]
    game["board"][r][c] = sym
    b = game["board"]

    is_won = _check_win(b, sym)
    is_draw = all(cell != " " for row in b for cell in row) and not is_won

    if is_won or is_draw:
        game["status"] = "finished"
        if is_won:
            text = f"{E.PARTY}{E.TROPHY} <b>{t('dooz_won', lang, name=player['name'])}</b>"
        else:
            text = f"{E.HEART} <b>{t('game_draw', lang)}</b>"
        final = [[danger(b[r][c], f"dooz_noop_{gid}") for c in range(3)] for r in range(3)]
        await cb.message.edit_text(text, reply_markup=kb(final), parse_mode=ParseMode.HTML)
        state.unregister("dooz", chat_id, gid)
    else:
        next_p = next(p for p in game["players_info"] if p["id"] != uid)
        game["turn"] = next_p["id"]
        text = (
            f"{E.PARTY} <b>{t('dooz_started', lang, name1=game['players_info'][0]['name'], name2=game['players_info'][1]['name'])}</b>\n\n"
            f"{E.ARROW} {t('dooz_your_turn', lang, name=next_p['name'], symbol=next_p['symbol'])}"
        )
        rows = [[danger(b[r][c], f"dooz_move_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
        await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("dooz_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer(t("finished", get_user_lang(cb.from_user.id)), show_alert=False)
