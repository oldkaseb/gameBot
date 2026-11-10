"""بازی حافظه — تک‌نفره و گروهی"""

import asyncio, random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from . import state

router = Router(name="memory")

EMOJIS = ["🍎","🍓","🍉","🍕","🍔","🎂","🍦","🍩","🍿","🌸","🌻","🍁","🍀","🍄","🌈","⭐","🔥","🌊","⚽","🏀","🎳","🎸","🎮","🎯","🎨","🚀","🎁","🎈","💎","👑","❤️","🧡","💙","💚","💜"]


class MemoryStates(StatesGroup):
    waiting_size = State()


def _gen_board(rows, cols):
    n = (rows * cols) // 2
    pool = random.sample(EMOJIS, n) * 2
    random.shuffle(pool)
    return [pool[i*cols:(i+1)*cols] for i in range(rows)]


async def _render(game, lang, finished=False):
    gid = game["game_id"]
    mode = game.get("mode", "multi")
    if finished:
        if mode == "solo":
            text = (
                f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n\n"
                f"{E.TROPHY} {t('memory_solo_done', lang, moves=game['moves'])}"
            )
        else:
            p1, p2 = game["players_info"]
            text = (
                f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n\n"
                f"{E.CHART} {t('memory_final_score', lang, name1=p1['name'], s1=p1['score'], name2=p2['name'], s2=p2['score'])}"
            )
    else:
        if mode == "solo":
            text = (
                f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n"
                f"{E.CHART} {t('memory_moves', lang, n=game['moves'])}\n"
                f"{E.INFO} {t('memory_solo_hint', lang)}"
            )
        else:
            p1, p2 = game["players_info"]
            tp = next(p for p in game["players_info"] if p["id"] == game["turn"])
            text = (
                f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n"
                f"{E.CHART} {p1['name']}: {p1['score']} | {p2['name']}: {p2['score']}\n\n"
                f"{E.ARROW} {t('memory_turn', lang, name=tp['name'])}"
            )

    bv = game["board_view"]
    rows = []
    for r, row in enumerate(bv):
        rb = []
        for c, cell in enumerate(row):
            action = "noop" if finished else "flip"
            rb.append(danger(cell, f"memory_{action}_{gid}_{r}_{c}"))
        rows.append(rb)
    return text, kb(rows)


@router.callback_query(F.data.startswith("memory_start_"))
async def start(cb: CallbackQuery, state_fsm: FSMContext):
    parts = cb.data.split("_")
    try:
        target = int(parts[-1])
        size = parts[2]
        rows, cols = map(int, size.split("x"))
    except: await cb.answer("❌"); return
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    await cb.answer()
    await state_fsm.clear()
    await state_fsm.update_data(
        chat_id=chat_id, starter=uid, size=size,
        rows=rows, cols=cols, setup_msg=cb.message.message_id,
    )

    await cb.message.edit_text(
        f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n\n"
        f"{E.INFO} {t('memory_choose_mode', lang)}",
        reply_markup=kb([
            [success(f"{E.TARGET} {t('memory_solo_btn', lang)}", "memory_mode_solo")],
            [primary(f"{E.PEOPLE} {t('memory_multi_btn', lang)}", "memory_mode_multi")],
            [danger(f"{E.ARROW} {t('btn_back', lang)}", f"rsgame_main_{uid}")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "memory_mode_solo")
async def solo_mode(cb: CallbackQuery, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if cb.from_user.id != data.get("starter"):
        await cb.answer("❌", show_alert=True); return
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = data["chat_id"]
    rows, cols = data["rows"], data["cols"]
    gid = data["setup_msg"]

    state.register("memory", chat_id, gid, {
        "game_id": gid, "mode": "solo", "status": "playing",
        "player_id": uid,
        "board_solution": _gen_board(rows, cols),
        "board_view": [["❔"]*cols for _ in range(rows)],
        "first_card": None, "is_checking": False,
        "moves": 0, "matched": 0, "total": (rows*cols)//2,
    })
    await state_fsm.clear()
    game = state.get("memory", chat_id, gid)
    text, markup = await _render(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data == "memory_mode_multi")
async def multi_mode(cb: CallbackQuery, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if cb.from_user.id != data.get("starter"):
        await cb.answer("❌", show_alert=True); return
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = data["chat_id"]
    rows, cols = data["rows"], data["cols"]
    gid = data["setup_msg"]

    state.register("memory", chat_id, gid, {
        "game_id": gid, "mode": "multi", "status": "joining",
        "players_info": [{"id": uid, "name": cb.from_user.first_name, "score": 0}],
        "board_solution": _gen_board(rows, cols),
        "board_view": [["❔"]*cols for _ in range(rows)],
        "turn": None, "first_card": None, "is_checking": False,
        "matched": 0, "total": (rows*cols)//2, "player_id": uid,
    })
    await state_fsm.clear()
    text = (
        f"{E.BRAIN} <b>{t('memory_created', lang, name=cb.from_user.first_name, size=data['size'])}</b>\n\n"
        f"{E.LINK} @RHINOBOT_TM"
    )
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"memory_join_{gid}")]])
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("memory_join_"))
async def join(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("memory", chat_id, gid)
    if not game or game["status"] != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["players_info"]):
        await cb.answer(t("already_joined", lang), show_alert=True); return
    if len(game["players_info"]) >= 2:
        await cb.answer(t("game_full", lang), show_alert=True); return

    game["players_info"].append({"id": uid, "name": cb.from_user.first_name, "score": 0})
    game["status"] = "playing"
    game["turn"] = game["players_info"][0]["id"]

    text, markup = await _render(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("memory_flip_"))
async def flip(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, r, c = int(parts[2]), int(parts[3]), int(parts[4])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("memory", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if game["is_checking"]:
        await cb.answer(t("wait_a_bit", lang)); return

    mode = game.get("mode", "multi")
    if mode == "multi" and uid != game["turn"]:
        await cb.answer(t("not_your_turn", lang), show_alert=True); return
    if mode == "solo" and uid != game.get("player_id"):
        await cb.answer(t("not_your_game", lang), show_alert=True); return

    if game["board_view"][r][c] != "❔":
        await cb.answer(t("memory_already_flipped", lang), show_alert=True); return

    await cb.answer()
    val = game["board_solution"][r][c]
    game["board_view"][r][c] = val

    if not game["first_card"]:
        game["first_card"] = {"r": r, "c": c, "val": val}
        if mode == "solo":
            game["moves"] += 1
        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    game["is_checking"] = True
    try:
        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1.5)

        fc = game["first_card"]
        if val == fc["val"] and (r, c) != (fc["r"], fc["c"]):
            game["matched"] += 1
            if mode == "multi":
                for p in game["players_info"]:
                    if p["id"] == game["turn"]:
                        p["score"] += 1; break
        else:
            game["board_view"][r][c] = "❔"
            game["board_view"][fc["r"]][fc["c"]] = "❔"
            if mode == "multi":
                nxt = next(p for p in game["players_info"] if p["id"] != game["turn"])
                game["turn"] = nxt["id"]
            game["moves"] += 1
    finally:
        game["first_card"] = None
        game["is_checking"] = False

    if game["matched"] == game["total"]:
        text, markup = await _render(game, lang, finished=True)
        if mode == "multi":
            p1, p2 = game["players_info"]
            winner = p1 if p1["score"] > p2["score"] else (p2 if p2["score"] > p1["score"] else None)
            if winner:
                text += f"\n\n{E.TROPHY} {t('game_winner', lang, name=winner['name'])}"
            else:
                text += f"\n\n{t('game_draw', lang)}"
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        state.unregister("memory", chat_id, gid)
    else:
        text, markup = await _render(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("memory_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer()
