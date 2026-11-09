"""بازی حکم — ۲ و ۴ نفره، کامل با رفع همه باگ‌ها"""

from __future__ import annotations
import asyncio
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, btn, kb
from . import state

router = Router(name="hokm")

# ────────────────────── ثابت‌ها
SUITS = {"S": "♠️", "H": "♥️", "D": "♦️", "C": "♣️"}
RANK_DISPLAY = {11: "J", 12: "Q", 13: "K", 14: "A"}
SUIT_ORDER = {"C": 0, "D": 1, "S": 2, "H": 3}  # گشنیز، خشت، پیک، دل
NUMBER_EMOJIS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣",
                 "9️⃣","🔟","1️⃣1️⃣","1️⃣2️⃣","1️⃣3️⃣"]


# ────────────────────── توابع کمکی کارت
def create_deck() -> list[str]:
    deck = [f"{s}{r}" for s in SUITS for r in range(2, 15)]
    random.shuffle(deck)
    return deck


def card_fa(card: str) -> str:
    if not card:
        return "🃏"
    suit, rank = card[0], int(card[1:])
    return f"{SUITS[suit]} {RANK_DISPLAY.get(rank, rank)}"


def sort_hand(hand: list[str]) -> list[str]:
    return sorted(hand, key=lambda c: (SUIT_ORDER[c[0]], -int(c[1:])))


def card_value(card: str, trump: str, trick_suit: str) -> int:
    suit, rank = card[0], int(card[1:])
    if suit == trump:
        return rank + 200
    if suit == trick_suit:
        return rank + 100
    return rank


# ────────────────────── ساختار بازی
def _new_game(gid: int, mode: str, host_id: int, host_name: str) -> dict:
    return {
        "game_id": gid,
        "mode": mode,                  # "2p" | "4p"
        "status": "joining",           # joining | hakem_choosing | playing | finished
        "players": [{"id": host_id, "name": host_name}],
        "hands": {},
        "deck": [],
        "hakem_id": None,
        "hakem_name": None,
        "turn_index": 0,
        "hokm_suit": None,
        "current_trick": [],
        "trick_scores": {},
        "game_scores": {},
        "in_transition": False,        # ⚠️ قفل انتقال بین دست‌ها
        "player_id": host_id,          # برای مالکیت
    }


# ────────────────────── رندر صفحه بازی
async def _render_board(game: dict, lang: str) -> tuple[str, "InlineKeyboardMarkup"]:
    gid = game["game_id"]
    p_names = [p["name"] for p in game["players"]]
    p_ids = [p["id"] for p in game["players"]]
    is_4p = game["mode"] == "4p"

    # نقشه کارت‌های روی میز
    table_map = {pid: "➖" for pid in p_ids}
    for play in game.get("current_trick", []):
        table_map[play["player_id"]] = card_fa(play["card"])

    # ───── بخش بالای صفحه: نمایش بازیکنان و میز
    rows = []
    if is_4p:
        team_a = f"{E.RED} {t('hokm_team_a', lang)}: {p_names[0]} & {p_names[2]}"
        team_b = f"{E.BLUE} {t('hokm_team_b', lang)}: {p_names[1]} & {p_names[3]}"
        rows.append([primary(team_a, f"hokm_noop_{gid}")])
        rows.append([primary(team_b, f"hokm_noop_{gid}")])
        rows.append([
            primary(f"{E.DISGUISE} {t('player', lang)}", f"hokm_noop_{gid}"),
            primary(f"{E.CARD} {t('hokm_played_card', lang)}", f"hokm_noop_{gid}"),
        ])
        for i in range(4):
            rows.append([
                primary(f"{p_names[i]}", f"hokm_noop_{gid}"),
                success(f"{table_map[p_ids[i]]}", f"hokm_noop_{gid}"),
            ])
    else:
        for i in range(2):
            rows.append([
                primary(f"{p_names[i]}", f"hokm_noop_{gid}"),
                success(f"{table_map[p_ids[i]]}", f"hokm_noop_{gid}"),
            ])

    # ───── وضعیت و امتیاز
    trump_icon = card_fa(f"{game['hokm_suit']}2")[0] if game.get("hokm_suit") else "❓"
    hakem_display = game.get("hakem_name") or "…"

    if is_4p:
        trick_txt = f"{t('hokm_trick_score', lang)}: {E.RED} {game['trick_scores'].get('A', 0)} - {game['trick_scores'].get('B', 0)} {E.BLUE}"
        game_txt = f"{t('hokm_total_score', lang)}: {E.RED} {game['game_scores'].get('A', 0)} - {game['game_scores'].get('B', 0)} {E.BLUE}"
    else:
        a, b = p_ids[0], p_ids[1]
        trick_txt = (
            f"{t('hokm_trick_score', lang)}: {p_names[0]} "
            f"{game['trick_scores'].get(a, 0)} - {game['trick_scores'].get(b, 0)} {p_names[1]}"
        )
        game_txt = (
            f"{t('hokm_total_score', lang)}: {p_names[0]} "
            f"{game['game_scores'].get(a, 0)} - {game['game_scores'].get(b, 0)} {p_names[1]}"
        )

    rows.append([
        primary(f"{E.CROWN} {t('hokm_hakem', lang)}: {hakem_display}", f"hokm_noop_{gid}"),
        primary(f"{E.TARGET} {t('hokm_trump', lang)}: {trump_icon}", f"hokm_noop_{gid}"),
    ])
    rows.append([success(trick_txt, f"hokm_noop_{gid}")])
    rows.append([danger(game_txt, f"hokm_noop_{gid}")])

    # ───── دکمه‌های کنترلی
    rows.append([primary(f"{E.CARD} {t('hokm_show_hand', lang)}", f"hokm_showhand_{gid}")])

    if game["status"] == "hakem_choosing":
        suit_map = [("♠️", "S"), ("♥️", "H"), ("♦️", "D"), ("♣️", "C")]
        suit_btns = [
            primary(f"{emoji}", f"hokm_choose_{gid}_{char}")
            for emoji, char in suit_map
        ]
        rows.append(suit_btns)

    elif game["status"] == "playing":
        cur_pid = game["players"][game["turn_index"]]["id"]
        if cur_pid in game["hands"]:
            hand = sort_hand(game["hands"][cur_pid])
            card_btns = [
                success(str(i + 1), f"hokm_play_{gid}_{i}")
                for i in range(len(hand))
            ]
            for i in range(0, len(card_btns), 7):
                rows.append(card_btns[i:i + 7])

    # ───── متن
    if game["status"] == "hakem_choosing":
        text = (
            f"{E.CARD}{E.CROWN} <b>{t('hokm_title', lang)}</b>\n\n"
            f"{E.INFO} {t('hokm_choose_suit', lang)}"
        )
    elif game["status"] == "playing":
        tp = game["players"][game["turn_index"]]
        text = (
            f"{E.CARD}{E.PARTY} <b>{t('hokm_title', lang)}</b>\n\n"
            f"{E.ARROW} {t('turn_of', lang)}: <b>{tp['name']}</b>\n"
            f"{E.TARGET} {t('hokm_trump', lang)}: {trump_icon}"
        )
    else:
        text = f"{E.CARD} <b>{t('hokm_title', lang)}</b>"

    return text, kb(rows)


# ────────────────────── شروع بازی
@router.callback_query(F.data.startswith("hokm_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id

    parts = cb.data.split("_")
    try:
        mode = parts[2]  # 2p | 4p
        target = int(parts[-1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return

    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    if chat_id in state.active_games["hokm"] and state.active_games["hokm"][chat_id]:
        await cb.answer(t("game_already_running", lang), show_alert=True)
        return

    await cb.answer()
    sent = await cb.message.answer("⏳")
    gid = sent.message_id
    max_players = 4 if mode == "4p" else 2

    game = _new_game(gid, mode, uid, cb.from_user.first_name or "Player")
    state.register("hokm", chat_id, gid, game)

    text = (
        f"{E.PARTY}{E.CARD} <b>{t('hokm_created', lang, name=cb.from_user.first_name, mode=max_players)}</b>\n\n"
        f"{E.INFO} {t('waiting_players', lang)}\n"
        f"{E.DISGUISE} {cb.from_user.first_name}\n\n"
        f"{E.LINK} @RHINOBOT_TM"
    )
    markup = kb([[success(f"{E.PLUS} {t('join_game', lang)} (1/{max_players})",
                          f"hokm_join_{gid}")]])
    await sent.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    try:
        await cb.message.delete()
    except Exception:
        pass


# ────────────────────── پیوستن به بازی
@router.callback_query(F.data.startswith("hokm_join_"))
async def join(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid = int(parts[2])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("hokm", chat_id, gid)

    if not game or game["status"] != "joining":
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return
    if any(p["id"] == uid for p in game["players"]):
        await cb.answer(t("already_joined", lang), show_alert=True)
        return

    max_players = 4 if game["mode"] == "4p" else 2
    if len(game["players"]) >= max_players:
        await cb.answer(t("game_full", lang), show_alert=True)
        return

    game["players"].append({"id": uid, "name": cb.from_user.first_name or "Player"})
    n = len(game["players"])

    if n < max_players:
        names = "، ".join(p["name"] for p in game["players"])
        text = (
            f"{E.PARTY}{E.CARD} <b>{t('hokm_created', lang, name=game['players'][0]['name'], mode=max_players)}</b>\n\n"
            f"{E.DISGUISE} {names}\n\n{E.LINK} @RHINOBOT_TM"
        )
        markup = kb([[success(f"{E.PLUS} {t('join_game', lang)} ({n}/{max_players})",
                              f"hokm_join_{gid}")]])
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        await cb.answer()
        return

    # ───── بازی پر شد → پخش ۵ کارت اول
    await _start_first_deal(game, chat_id, lang)
    text, markup = await _render_board(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


async def _start_first_deal(game: dict, chat_id: int, lang: str) -> None:
    """پخش ۵ کارت اول + تعیین حاکم"""
    game["deck"] = create_deck()
    pids = [p["id"] for p in game["players"]]
    game["hands"] = {pid: [] for pid in pids}

    # ۵ کارت به هر بازیکن
    for _ in range(5):
        for p in game["players"]:
            game["hands"][p["id"]].append(game["deck"].pop(0))

    # حاکم: کسی که S14 (آس پیک) دارد
    hakem = next(
        (p for p in game["players"] if "S14" in game["hands"][p["id"]]),
        game["players"][0]
    )
    game["hakem_id"] = hakem["id"]
    game["hakem_name"] = hakem["name"]

    # مقدار اولیه امتیازها
    if game["mode"] == "4p":
        game["trick_scores"] = {"A": 0, "B": 0}
        game["game_scores"] = {"A": 0, "B": 0}
    else:
        game["trick_scores"] = {pid: 0 for pid in pids}
        game["game_scores"] = {pid: 0 for pid in pids}

    game["turn_index"] = next(i for i, p in enumerate(game["players"]) if p["id"] == hakem["id"])
    game["status"] = "hakem_choosing"


# ────────────────────── انتخاب حکم
@router.callback_query(F.data.startswith("hokm_choose_"))
async def choose_trump(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, suit = int(parts[2]), parts[3]
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("hokm", chat_id, gid)

    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return
    if game["status"] != "hakem_choosing":
        await cb.answer(t("hokm_not_choosing", lang), show_alert=True)
        return
    if uid != game["hakem_id"]:
        await cb.answer(t("hokm_not_hakem", lang), show_alert=True)
        return

    # ───── انتخاب شد → پخش ۸ کارت باقی‌مانده
    game["hokm_suit"] = suit
    for p in game["players"]:
        while len(game["hands"][p["id"]]) < 13 and game["deck"]:
            game["hands"][p["id"]].append(game["deck"].pop(0))

    game["status"] = "playing"
    game["turn_index"] = next(
        i for i, p in enumerate(game["players"]) if p["id"] == game["hakem_id"]
    )
    game["current_trick"] = []

    text, markup = await _render_board(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await cb.answer()


# ────────────────────── نمایش دست (خصوصی)
@router.callback_query(F.data.startswith("hokm_showhand_"))
async def show_hand(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid = int(parts[2])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("hokm", chat_id, gid)

    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return
    if not any(p["id"] == uid for p in game["players"]):
        await cb.answer(t("not_your_game", lang), show_alert=True)
        return

    hand = sort_hand(game["hands"].get(uid, []))
    if not hand:
        await cb.answer(t("hokm_no_cards", lang), show_alert=True)
        return

    # ساخت متن دست
    hand_lines = [f"{NUMBER_EMOJIS[i]} {card_fa(c)}" for i, c in enumerate(hand)]
    hand_str = "\n".join(hand_lines)

    # ───── ✅ رفع باگ: پیام در چت خصوصی (نه alert)
    try:
        await cb.bot.send_message(
            uid,
            f"{E.CARD} <b>{t('hokm_your_hand', lang, hand='')}</b>\n\n{hand_str}",
            parse_mode=ParseMode.HTML,
        )
        await cb.answer(f"{E.CHECK} {t('hokm_your_hand', lang, hand='').split(':')[0]} → چت خصوصی")
    except Exception:
        # اگر کاربر ربات را استارت نکرده باشد
        await cb.answer(
            f"{E.WARN} برای دریافت دست، ابتدا ربات را استارت کنید.",
            show_alert=True,
        )


# ────────────────────── بازی کارت
@router.callback_query(F.data.startswith("hokm_play_"))
async def play_card(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, card_index = int(parts[2]), int(parts[3])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True)
        return

    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("hokm", chat_id, gid)

    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return
    if game["status"] != "playing":
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return

    # ⚠️ قفل انتقال (در حین نمایش برنده دست)
    if game.get("in_transition"):
        await cb.answer(t("wait_a_bit", lang))
        return

    cur_pid = game["players"][game["turn_index"]]["id"]
    if uid != cur_pid:
        await cb.answer(t("not_your_turn", lang), show_alert=True)
        return

    hand = sort_hand(game["hands"][uid])
    if not (0 <= card_index < len(hand)):
        await cb.answer(t("hokm_invalid_card", lang), show_alert=True)
        return

    chosen_card = hand[card_index]

    # ───── بررسی قانون رعایت خال
    if game["current_trick"]:
        trick_suit = game["current_trick"][0]["card"][0]
        has_trick_suit = any(c.startswith(trick_suit) for c in hand)
        if has_trick_suit and not chosen_card.startswith(trick_suit):
            await cb.answer(
                t("hokm_must_follow", lang, suit=card_fa(f"{trick_suit}2")[0]),
                show_alert=True,
            )
            return

    await cb.answer()

    # ───── اجرای کارت
    game["hands"][uid].remove(chosen_card)
    game["current_trick"].append({"player_id": uid, "card": chosen_card})
    num_players = len(game["players"])

    # ───── آیا دست کامل شده؟
    if len(game["current_trick"]) < num_players:
        game["turn_index"] = (game["turn_index"] + 1) % num_players
        text, markup = await _render_board(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    # ───── تعیین برنده دست
    trick_suit = game["current_trick"][0]["card"][0]
    winner_play = max(
        game["current_trick"],
        key=lambda p: card_value(p["card"], game["hokm_suit"], trick_suit),
    )
    winner_id = winner_play["player_id"]

    # ───── امتیاز دست
    if game["mode"] == "4p":
        team_a_ids = [game["players"][0]["id"], game["players"][2]["id"]]
        winner_team = "A" if winner_id in team_a_ids else "B"
        game["trick_scores"][winner_team] += 1
        round_over = game["trick_scores"][winner_team] == 7
    else:
        game["trick_scores"][winner_id] += 1
        round_over = any(s == 7 for s in game["trick_scores"].values())

    winner_name = next(p["name"] for p in game["players"] if p["id"] == winner_id)
    game["turn_index"] = next(
        i for i, p in enumerate(game["players"]) if p["id"] == winner_id
    )

    # ⚠️ فعال‌سازی قفل انتقال
    game["in_transition"] = True

    # ───── نمایش موقت برنده دست
    tmp_text, tmp_markup = await _render_board(game, lang)
    tmp_text = f"{E.TROPHY} <b>{t('hokm_won_trick', lang, name=winner_name)}</b>\n\n{E.HOURGLASS} {t('hokm_wait', lang)}"
    await cb.message.edit_text(tmp_text, reply_markup=tmp_markup, parse_mode=ParseMode.HTML)

    await asyncio.sleep(2.5)

    # ⚠️ بررسی مجدد وجود بازی (ممکن است کاربر لغو کرده باشد)
    if not state.exists("hokm", chat_id, gid):
        return

    game["current_trick"] = []
    game["in_transition"] = False

    # ───── آیا دور (round) تمام شده؟
    if not round_over:
        text, markup = await _render_board(game, lang)
        await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    # ───── محاسبه برنده دور
    if game["mode"] == "4p":
        winning_team = "A" if game["trick_scores"]["A"] == 7 else "B"
        game["game_scores"][winning_team] += 1
        winner_display = t(f"hokm_team_{winning_team.lower()}", lang)
        game_over = game["game_scores"][winning_team] == 7
    else:
        round_winner_id = next(
            pid for pid, score in game["trick_scores"].items() if score == 7
        )
        winner_display = next(p["name"] for p in game["players"] if p["id"] == round_winner_id)
        game["game_scores"][round_winner_id] += 1
        game_over = any(s == 7 for s in game["game_scores"].values())

    # ───── آیا بازی کامل تمام شده؟
    if game_over:
        final = (
            f"{E.TROPHY}{E.PARTY} <b>{t('hokm_game_won', lang, name=winner_display)}</b>\n\n"
            f"{E.CHART} {t('hokm_total_score', lang)}: {winner_display} = 7"
        )
        await cb.message.edit_text(final, reply_markup=None, parse_mode=ParseMode.HTML)
        state.unregister("hokm", chat_id, gid)
        return

    # ───── شروع دور جدید
    cur_hakem_idx = next(
        i for i, p in enumerate(game["players"]) if p["id"] == game["hakem_id"]
    )

    if game["mode"] == "4p":
        hakem_team = "A" if cur_hakem_idx in (0, 2) else "B"
        next_hakem_idx = cur_hakem_idx if winning_team == hakem_team else (cur_hakem_idx + 1) % 4
    else:
        round_winner_id = next(
            pid for pid, score in game["trick_scores"].items() if score == 7
        )
        next_hakem_idx = cur_hakem_idx if round_winner_id == game["hakem_id"] else (cur_hakem_idx + 1) % 2

    # ───── پخش دور جدید
    game["deck"] = create_deck()
    pids = [p["id"] for p in game["players"]]
    game["hands"] = {pid: [] for pid in pids}

    for _ in range(5):
        for p in game["players"]:
            game["hands"][p["id"]].append(game["deck"].pop(0))

    if game["mode"] == "4p":
        game["trick_scores"] = {"A": 0, "B": 0}
    else:
        game["trick_scores"] = {pid: 0 for pid in pids}

    game["hakem_id"] = game["players"][next_hakem_idx]["id"]
    game["hakem_name"] = game["players"][next_hakem_idx]["name"]
    game["status"] = "hakem_choosing"
    game["turn_index"] = next_hakem_idx
    game["hokm_suit"] = None

    text = (
        f"{E.PARTY} <b>{t('hokm_round_finished', lang, name=winner_display, hakem=game['hakem_name'])}</b>"
    )
    _, markup = await _render_board(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ────────────────────── دکمه‌های noop
@router.callback_query(F.data.startswith("hokm_noop_"))
async def noop(cb: CallbackQuery):
    await cb.answer()
