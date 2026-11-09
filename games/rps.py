"""سنگ، کاغذ، قیچی"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from . import state

router = Router(name="rps")

SYMBOLS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RULES = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


@router.callback_query(F.data.startswith("rps_start_"))
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
    state.register("rps", chat_id, gid, {
        "game_id": gid, "status": "joining",
        "players_info": [{"id": uid, "name": cb.from_user.first_name}],
        "choices": {}, "player_id": uid,
    })
    text = f"{E.PARTY} <b>{t('rps_created', lang, name=cb.from_user.first_name)}</b>\n\n{E.LINK} @RHINOBOT_TM"
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)}", f"rps_join_{gid}")]])
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try: await cb.message.delete()
    except Exception: pass


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
    p1, p2 = game["players_info"]

    text = f"{E.PARTY} <b>{t('rps_started', lang, name1=p1['name'], name2=p2['name'])}</b>"
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

    text = f"{E.TROPHY} <b>{t('rps_result', lang, name1=p1['name'], c1=SYMBOLS[c1], name2=p2['name'], c2=SYMBOLS[c2])}</b>\n\n"
    if winner:
        text += f"{E.TROPHY} {t('game_winner', lang, name=winner['name'])}"
    else:
        text += t("game_draw", lang)

    await cb.message.edit_text(text, reply_markup=None, parse_mode=ParseMode.HTML)
    state.unregister("rps", chat_id, gid)
