"""سنگ، کاغذ، قیچی — با تعداد راند قابل تنظیم"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from . import state

router = Router(name="rps")

SYMBOLS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RULES = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


class RPSStates(StatesGroup):
    waiting_rounds = State()


@router.callback_query(F.data.startswith("rps_start_"))
async def start(cb: CallbackQuery, state_fsm: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except: await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    await cb.answer()
    await state_fsm.clear()
    await state_fsm.update_data(chat_id=chat_id, starter=uid, setup_msg=cb.message.message_id)
    await state_fsm.set_state(RPSStates.waiting_rounds)

    await cb.message.edit_text(
        f"{E.GAME} <b>{t('rps_title', lang)}</b>\n\n"
        f"{E.INFO} {t('rps_ask_rounds', lang)}",
        parse_mode=ParseMode.HTML,
    )


@router.message(RPSStates.waiting_rounds, F.text)
async def receive_rounds(msg, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if msg.from_user.id != data.get("starter"):
        return
    lang = get_user_lang(msg.from_user.id)
    try:
        n = int(msg.text.strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
        if not (1 <= n <= 10):
            raise ValueError
    except ValueError:
        await msg.reply(f"{E.WARN} {t('rps_invalid_rounds', lang)}")
        return

    chat_id = data["chat_id"]
    gid = msg.message_id
    state.register("rps", chat_id, gid, {
        "game_id": gid, "status": "joining",
        "players_info": [{"id": data["starter"], "name": msg.from_user.first_name}],
        "choices": {}, "wins_needed": n,
        "scores": {data["starter"]: 0}, "player_id": data["starter"],
    })
    await state_fsm.clear()

    text = (
        f"{E.PARTY} <b>{t('rps_created', lang, name=msg.from_user.first_name, n=n)}</b>\n\n"
        f"{E.LINK} @RHINOBOT_TM"
    )
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"rps_join_{gid}")]])
    try:
        await msg.bot.edit_message_text(
            text, chat_id=chat_id, message_id=data["setup_msg"],
            reply_markup=markup, parse_mode=ParseMode.HTML,
        )
    except Exception:
        await msg.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("rps_join_"))
async def join(cb: CallbackQuery):
    try: gid = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("rps", chat_id, gid)
    if not game or game["status"] != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["players_info"]):
        await cb.answer(t("already_joined", lang), show_alert=True); return
    if len(game["players_info"]) >= 2:
        await cb.answer(t("game_full", lang), show_alert=True); return

    game["players_info"].append({"id": uid, "name": cb.from_user.first_name})
    game["status"] = "playing"
    game["scores"][uid] = 0
    p1, p2 = game["players_info"]

    text = (
        f"{E.PARTY} <b>{t('rps_started', lang, name1=p1['name'], name2=p2['name'], n=game['wins_needed'])}</b>"
    )
    rows = [
        [success(f"🪨 {t('rps_rock', lang)}", f"rps_choose_{gid}_rock"),
         primary(f"📄 {t('rps_paper', lang)}", f"rps_choose_{gid}_paper"),
         danger(f"✂️ {t('rps_scissors', lang)}", f"rps_choose_{gid}_scissors")],
    ]
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    await cb.answer()


@router.callback_query(F.data.startswith("rps_choose_"))
async def choose(cb: CallbackQuery):
    parts = cb.data.split("_")
    try: gid, choice = int(parts[2]), parts[3]
    except: await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("rps", chat_id, gid)
    if not game or game["status"] != "playing":
        await cb.answer(t("game_not_active", lang), show_alert=True); return
    if uid not in [p["id"] for p in game["players_info"]]:
        await cb.answer(t("not_your_game", lang), show_alert=True); return
    if uid in game["choices"]:
        await cb.answer(t("rps_already_chosen", lang), show_alert=True); return

    game["choices"][uid] = choice
    await cb.answer(t("rps_chosen", lang))

    p1, p2 = game["players_info"]

    if len(game["choices"]) < 2:
        s1 = t("rps_chosen_status", lang) if p1["id"] in game["choices"] else t("rps_waiting_status", lang)
        s2 = t("rps_chosen_status", lang) if p2["id"] in game["choices"] else t("rps_waiting_status", lang)
        text = f"{E.BRAIN} <b>{t('rps_waiting', lang, name1=p1['name'], s1=s1, name2=p2['name'], s2=s2)}</b>"
        rows = [
            [success(f"🪨 {t('rps_rock', lang)}", f"rps_choose_{gid}_rock"),
             primary(f"📄 {t('rps_paper', lang)}", f"rps_choose_{gid}_paper"),
             danger(f"✂️ {t('rps_scissors', lang)}", f"rps_choose_{gid}_scissors")],
        ]
        await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
        return

    c1, c2 = game["choices"][p1["id"]], game["choices"][p2["id"]]
    winner = None
    if RULES[c1] == c2: winner = p1
    elif RULES[c2] == c1: winner = p2

    if winner:
        game["scores"][winner["id"]] += 1

    s1, s2 = game["scores"][p1["id"]], game["scores"][p2["id"]]
    needed = game["wins_needed"]

    if s1 >= needed or s2 >= needed:
        final_winner = p1 if s1 >= needed else p2
        text = (
            f"{E.TROPHY}{E.PARTY} <b>{t('rps_game_winner', lang, name=final_winner['name'])}</b>\n\n"
            f"{E.CHART} {t('rps_final_score', lang, n1=p1['name'], s1=s1, n2=p2['name'], s2=s2)}"
        )
        await cb.message.edit_text(text, reply_markup=None, parse_mode=ParseMode.HTML)
        state.unregister("rps", chat_id, gid)
        return

    game["choices"] = {}
    text = (
        f"{E.GAME} <b>{t('rps_result', lang, name1=p1['name'], c1=SYMBOLS[c1], name2=p2['name'], c2=SYMBOLS[c2])}</b>\n\n"
        f"{E.CHART} {t('rps_score_line', lang, n1=p1['name'], s1=s1, n2=p2['name'], s2=s2, needed=needed)}\n"
        f"{E.ARROW} {t('rps_next_round', lang)}"
    )
    rows = [
        [success(f"🪨 {t('rps_rock', lang)}", f"rps_choose_{gid}_rock"),
         primary(f"📄 {t('rps_paper', lang)}", f"rps_choose_{gid}_paper"),
         danger(f"✂️ {t('rps_scissors', lang)}", f"rps_choose_{gid}_scissors")],
    ]
    await cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
