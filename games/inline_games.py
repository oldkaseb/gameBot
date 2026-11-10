"""بازی‌های اینلاین — با دکمه fallback برای شروع مطمئن"""

import asyncio
import logging
import random
import time

from aiogram import Router, F
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChosenInlineResult, CallbackQuery,
)
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from runtime import check_forced_join

router = Router(name="inline_games")
log = logging.getLogger("inline_games")

inline_games: dict[str, dict] = {}
INLINE_TTL = 60 * 60


async def _edit(bot, mid, text, markup=None, retries=4):
    if not mid:
        log.error("_edit called with mid=None")
        return False
    for attempt in range(retries):
        try:
            await bot.edit_message_text(
                text=text,
                inline_message_id=mid,
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
            return True
        except Exception as e:
            err = str(e)
            if "not modified" in err.lower():
                return True
            log.warning(f"_edit attempt {attempt+1} failed: {err[:120]}")
            if attempt < retries - 1:
                await asyncio.sleep(0.35 * (attempt + 1))
    return False


INLINE_GAMES_LIST = [
    ("2048",      "🔢", "2048",           "پازل عددی"),
    ("spuzzle",   "🧩", "پازل کششی",      "پازل کلاسیک"),
    ("samegame",  "✨", "جفت‌ها",          "پازل رنگی"),
    ("dooz",      "❌", "دوز",             "دوز ۲ نفره"),
    ("connect4",  "🔴", "چهار در ردیف",    "استراتژیک"),
    ("rps",       "🪨", "سنگ کاغذ قیچی",  "کلاسیک"),
    ("memory",    "🧠", "حافظه",           "تقویت حافظه"),
]


@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    uid = query.from_user.id
    lang = get_user_lang(uid)
    log.info(f"🔍 inline_query from {uid} q={query.query!r}")

    try:
        missing = await check_forced_join(query.bot, uid)
        if missing:
            await query.answer(
                [], cache_time=1, is_personal=True,
                switch_pm_text=t("inline_join_required", lang),
                switch_pm_parameter="start",
            )
            return
    except Exception:
        pass

    q = (query.query or "").strip().lower()
    results = []
    for gtype, icon, name, desc in INLINE_GAMES_LIST:
        if q and q not in gtype.lower() and q not in name:
            continue
        results.append(InlineQueryResultArticle(
            id=f"ig|{gtype}|{uid}",
            title=f"{icon} {name}",
            description=desc,
            input_message_content=InputTextMessageContent(
                message_text=f"{E.HOURGLASS} {name}\n\nآماده‌سازی…",
                parse_mode=ParseMode.HTML,
            ),
            reply_markup=kb([[
                primary(f"{E.GAME} شروع بازی", f"igstart_{gtype}"),
            ]]),
        ))

    log.info(f"📤 {len(results)} results")
    await query.answer(results, cache_time=1, is_personal=True)


# ═══════════ chosen_inline_result — شروع خودکار ═══════════

@router.chosen_inline_result()
async def on_chosen(result: ChosenInlineResult):
    log.info(f"🎯 chosen: rid={result.result_id!r} mid={result.inline_message_id!r} from={result.from_user.id}")

    if not result.result_id.startswith("ig|"):
        return
    parts = result.result_id.split("|")
    if len(parts) < 2:
        return

    gtype = parts[1]
    uid = result.from_user.id
    lang = get_user_lang(uid)
    mid = result.inline_message_id

    if mid is None:
        log.warning(f"⚠️ mid=None for {uid} — inline in PM not supported")
        return

    if mid in inline_games:
        return

    await asyncio.sleep(0.5)

    try:
        await _start_game(result.bot, mid, gtype, uid,
                          result.from_user.first_name or "P1", lang)
    except Exception as e:
        log.exception(f"chosen init failed {gtype}: {e}")


# ═══════════ دکمه fallback ═══════════

@router.callback_query(F.data.startswith("igstart_"))
async def on_start_button(cb: CallbackQuery):
    log.info(f"🎯 igstart: {cb.data} mid={cb.inline_message_id!r}")

    mid = cb.inline_message_id
    if mid is None:
        await cb.answer("⚠️ فقط توی گروه کار می‌کنه", show_alert=True)
        return

    gtype = cb.data.replace("igstart_", "")
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if mid in inline_games:
        await cb.answer(t("game_already_running", lang))
        return

    await cb.answer()
    try:
        await _start_game(cb.bot, mid, gtype, uid,
                          cb.from_user.first_name or "P1", lang)
    except Exception as e:
        log.exception(f"button init failed: {e}")
        await cb.answer(f"⚠️ {e}", show_alert=True)


async def _start_game(bot, mid, gtype, uid, name, lang):
    if gtype == "2048":
        await _init_2048(bot, mid, uid, lang)
    elif gtype == "spuzzle":
        await _init_spuzzle(bot, mid, uid, lang)
    elif gtype == "samegame":
        await _init_samegame(bot, mid, uid, lang)
    elif gtype == "dooz":
        await _init_dooz(bot, mid, uid, name, lang)
    elif gtype == "connect4":
        await _init_connect4(bot, mid, uid, name, lang)
    elif gtype == "rps":
        await _init_rps(bot, mid, uid, name, lang)
    elif gtype == "memory":
        await _init_memory(bot, mid, uid, name, lang)
    else:
        log.warning(f"unknown gtype: {gtype}")


# ═══════════ 2048 ═══════════

T2048 = {
    0: "⬛️", 2: "2️⃣", 4: "4️⃣", 8: "8️⃣", 16: "1️⃣6️⃣", 32: "3️⃣2️⃣",
    64: "6️⃣4️⃣", 128: "1️⃣2️⃣8️⃣", 256: "2️⃣5️⃣6️⃣", 512: "5️⃣1️⃣2️⃣",
    1024: "🔟2️⃣4️⃣", 2048: "🏆",
}


def _t2048_new():
    b = [[0]*4 for _ in range(4)]
    _t2048_add(b); _t2048_add(b)
    return b


def _t2048_add(b):
    cells = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
    if cells:
        r, c = random.choice(cells)
        b[r][c] = 2 if random.random() < 0.9 else 4
    return b


def _t2048_can_move(b):
    for r in range(4):
        for c in range(4):
            if b[r][c] == 0: return True
            if c < 3 and b[r][c] == b[r][c+1]: return True
            if r < 3 and b[r][c] == b[r+1][c]: return True
    return False


def _t2048_transform(b, d):
    if d == "left": return b
    if d == "right": return [row[::-1] for row in b]
    if d == "up": return [list(col) for col in zip(*b)]
    if d == "down":
        z = [list(col) for col in zip(*b)]
        return [row[::-1] for row in z]


def _t2048_reverse(b, d):
    if d == "left": return b
    if d == "right": return [row[::-1] for row in b]
    if d == "up": return [list(col) for col in zip(*b)]
    if d == "down":
        b = [row[::-1] for row in b]
        return [list(col) for col in zip(*b)]


def _t2048_move_left(b):
    new, score, moved = [], 0, False
    for row in b:
        comp = [x for x in row if x != 0]
        out, i = [], 0
        while i < len(comp):
            if i+1 < len(comp) and comp[i] == comp[i+1]:
                v = comp[i] * 2
                out.append(v); score += v; i += 2
            else:
                out.append(comp[i]); i += 1
        out.extend([0] * (4 - len(out)))
        new.append(out)
    if new != b: moved = True
    return new, score, moved


def _t2048_render(game, lang):
    b = game["board"]
    header = (
        f"{E.PUZZLE}{E.SPARK} <b>{t('game_2048_title', lang)}</b>\n"
        f"{E.CHART} {t('score', lang)}: <b>{game['score']}</b>"
    )
    rows = []
    for r in range(4):
        rows.append([danger(T2048.get(b[r][c], str(b[r][c])), "i2048_noop") for c in range(4)])
    rows.append([danger(" ", "i2048_noop"), danger("⬆️", "i2048_move_up"), danger(" ", "i2048_noop")])
    rows.append([danger("⬅️", "i2048_move_left"), danger(" ", "i2048_noop"), danger("➡️", "i2048_move_right")])
    rows.append([danger(" ", "i2048_noop"), danger("⬇️", "i2048_move_down"), danger(" ", "i2048_noop")])
    return header, kb(rows)


async def _init_2048(bot, mid, uid, lang):
    inline_games[mid] = {
        "type": "2048", "player_id": uid,
        "board": _t2048_new(), "score": 0,
        "_created": time.time(),
    }
    header, markup = _t2048_render(inline_games[mid], lang)
    await _edit(bot, mid, header, markup)


@router.callback_query(F.data.startswith("i2048_move_"))
async def i2048_move(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game: await cb.answer("بازی منقضی شد", show_alert=True); return
    if game["player_id"] != cb.from_user.id:
        await cb.answer("مال تو نیست", show_alert=True); return

    lang = get_user_lang(cb.from_user.id)
    direction = cb.data.split("_")[2]

    transformed = _t2048_transform(game["board"], direction)
    moved_board, inc, moved = _t2048_move_left(transformed)
    final = _t2048_reverse(moved_board, direction)
    if not moved:
        await cb.answer("حرکت نمی‌شه"); return

    game["board"] = _t2048_add(final)
    game["score"] += inc
    header, markup = _t2048_render(game, lang)

    if any(2048 in row for row in game["board"]):
        header += f"\n\n{E.TROPHY}{E.PARTY} <b>{t('you_won_2048', lang)}</b>"
        await _edit(cb.bot, mid, header, None)
        inline_games.pop(mid, None)
    elif not _t2048_can_move(game["board"]):
        header += f"\n\n{E.SKULL}{E.CROSS} <b>{t('you_lost_2048', lang)}</b>"
        await _edit(cb.bot, mid, header, None)
        inline_games.pop(mid, None)
    else:
        await _edit(cb.bot, mid, header, markup)
    await cb.answer()


# ═══════════ Pازل کششی ═══════════

SPZ = 4


def _spz_solvable():
    b = list(range(1, SPZ*SPZ)) + [0]
    e = len(b) - 1
    for _ in range(300):
        mv = []
        if e < SPZ*(SPZ-1): mv.append("up")
        if e >= SPZ: mv.append("down")
        if e % SPZ < SPZ-1: mv.append("left")
        if e % SPZ > 0: mv.append("right")
        m = random.choice(mv)
        swap = {"up": e+SPZ, "down": e-SPZ, "left": e+1, "right": e-1}[m]
        b[e], b[swap] = b[swap], b[e]
        e = swap
    return [b[i:i+SPZ] for i in range(0, len(b), SPZ)]


def _spz_solved(b):
    return [x for row in b for x in row] == list(range(1, SPZ*SPZ)) + [0]


def _spz_render(game, lang):
    b = game["board"]
    text = f"{E.PUZZLE}{E.SPARK} <b>{t('spuzzle_title', lang)}</b>\n\n{E.INFO} {t('sort_numbers', lang)}"
    rows = []
    for r in range(SPZ):
        row = [danger(str(b[r][c]) if b[r][c] else " ", "ispz_noop") for c in range(SPZ)]
        rows.append(row)
    rows.append([danger("⬆️", "ispz_move_up")])
    rows.append([danger("⬅️", "ispz_move_left"), danger("⬇️", "ispz_move_down"), danger("➡️", "ispz_move_right")])
    return text, kb(rows)


async def _init_spuzzle(bot, mid, uid, lang):
    inline_games[mid] = {
        "type": "spuzzle", "player_id": uid,
        "board": _spz_solvable(), "start_time": time.time(),
        "_created": time.time(),
    }
    text, markup = _spz_render(inline_games[mid], lang)
    await _edit(bot, mid, text, markup)


@router.callback_query(F.data.startswith("ispz_move_"))
async def ispz_move(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game: await cb.answer("بازی منقضی شد", show_alert=True); return
    if game["player_id"] != cb.from_user.id:
        await cb.answer("مال تو نیست", show_alert=True); return

    lang = get_user_lang(cb.from_user.id)
    d = cb.data.split("_")[2]
    b = game["board"]
    er = ec = -1
    for r in range(SPZ):
        if 0 in b[r]:
            er, ec = r, b[r].index(0); break

    tr, tc = er, ec
    if d == "up": tr += 1
    elif d == "down": tr -= 1
    elif d == "left": tc += 1
    elif d == "right": tc -= 1

    if not (0 <= tr < SPZ and 0 <= tc < SPZ):
        await cb.answer("حرکت نمی‌شه"); return

    b[er][ec], b[tr][tc] = b[tr][tc], b[er][ec]

    if _spz_solved(b):
        dur = int(time.time() - game["start_time"])
        final = f"{E.TROPHY}{E.PARTY} <b>{t('puzzle_solved', lang, name=cb.from_user.first_name)}</b>\n\n{E.CAL} {t('solved_in_seconds', lang, n=dur)}"
        await _edit(cb.bot, mid, final, None)
        inline_games.pop(mid, None)
    else:
        text, markup = _spz_render(game, lang)
        await _edit(cb.bot, mid, text, markup)
    await cb.answer()


# ═══════════ جفت‌ها ═══════════

SG_COLORS = ["🟥", "🟩", "🟦", "🟨", "🟪"]
SG_EMPTY = "⬛️"


def _sg_create():
    return [[random.choice(SG_COLORS) for _ in range(10)] for _ in range(10)]


def _sg_find(b, r0, c0):
    color = b[r0][c0]
    if color == SG_EMPTY: return []
    q, grp = [(r0, c0)], {(r0, c0)}
    while q:
        r, c = q.pop()
        for dr, dc in ((0,1),(0,-1),(1,0),(-1,0)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < 10 and 0 <= nc < 10 and b[nr][nc] == color and (nr, nc) not in grp:
                grp.add((nr, nc)); q.append((nr, nc))
    return list(grp)


def _sg_refill(b):
    for r in range(10):
        for c in range(10):
            if b[r][c] == SG_EMPTY:
                b[r][c] = random.choice(SG_COLORS)
    return b


def _sg_over(b):
    for r in range(10):
        for c in range(10):
            if b[r][c] != SG_EMPTY:
                if c+1 < 10 and b[r][c] == b[r][c+1]: return False
                if r+1 < 10 and b[r][c] == b[r+1][c]: return False
    return True


def _sg_render(game, lang, finished=False):
    b = game["board"]
    text = f"{E.PUZZLE}{E.SPARK} <b>{t('samegame_title', lang)}</b>\n{E.CHART} {t('score', lang)}: <b>{game['score']}</b>"
    if finished:
        text += f"\n\n{E.SKULL}{E.CROSS} <b>{t('no_more_moves', lang)}</b>"
    rows = []
    for r in range(10):
        row = [danger(b[r][c], "isg_noop" if finished else f"isg_click_{r}_{c}") for c in range(10)]
        rows.append(row)
    return text, kb(rows)


async def _init_samegame(bot, mid, uid, lang):
    inline_games[mid] = {
        "type": "samegame", "player_id": uid,
        "board": _sg_create(), "score": 0,
        "_created": time.time(),
    }
    text, markup = _sg_render(inline_games[mid], lang)
    await _edit(bot, mid, text, markup)


@router.callback_query(F.data.startswith("isg_click_"))
async def isg_click(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game: await cb.answer("بازی منقضی شد", show_alert=True); return
    if game["player_id"] != cb.from_user.id:
        await cb.answer("مال تو نیست", show_alert=True); return

    parts = cb.data.split("_")
    try: r, c = int(parts[2]), int(parts[3])
    except: await cb.answer("❌"); return

    lang = get_user_lang(cb.from_user.id)
    grp = _sg_find(game["board"], r, c)
    if len(grp) < 2:
        await cb.answer(t("need_two_blocks", lang), show_alert=True); return

    game["score"] += len(grp)
    for rr, cc in grp:
        game["board"][rr][cc] = SG_EMPTY
    game["board"] = _sg_refill(game["board"])

    if _sg_over(game["board"]):
        text, markup = _sg_render(game, lang, True)
        await _edit(cb.bot, mid, text, markup)
        inline_games.pop(mid, None)
    else:
        text, markup = _sg_render(game, lang)
        await _edit(cb.bot, mid, text, markup)
    await cb.answer()


# ═══════════ دوز ═══════════

def _dooz_check(b, sym):
    return (
        any(all(c == sym for c in r) for r in b)
        or any(all(b[r][c] == sym for r in range(3)) for c in range(3))
        or all(b[i][i] == sym for i in range(3))
        or all(b[i][2-i] == sym for i in range(3))
    )


def _dooz_render(game, lang):
    p1, p2 = game["players"]
    if game["status"] == "joining":
        text = f"{E.PARTY}{E.TARGET} <b>{t('dooz_created', lang, name=p1['name'])}</b>\n\n{E.INFO} {t('waiting_players', lang)}"
        return text, kb([[success(f"{E.PLUS} {t('join_game', lang)}", "idooz_join")]])

    b = game["board"]
    if game.get("finished"):
        if game.get("winner"):
            text = f"{E.PARTY}{E.TROPHY} <b>{t('dooz_won', lang, name=game['winner'])}</b>"
        else:
            text = f"{E.HEART} <b>{t('game_draw', lang)}</b>"
        rows = [[danger(b[r][c] or " ", "idooz_noop") for c in range(3)] for r in range(3)]
        return text, kb(rows)

    tp = p1 if game["turn"] == p1["id"] else p2
    text = f"{E.PARTY} <b>{t('dooz_started', lang, name1=p1['name'], name2=p2['name'])}</b>\n\n{E.ARROW} {t('dooz_your_turn', lang, name=tp['name'], symbol=tp['symbol'])}"
    rows = [[danger(b[r][c] or " ", f"idooz_move_{r*3+c}") for c in range(3)] for r in range(3)]
    return text, kb(rows)


async def _init_dooz(bot, mid, uid, name, lang):
    inline_games[mid] = {
        "type": "dooz", "status": "joining",
        "players": [{"id": uid, "name": name, "symbol": "❌"}],
        "board": [[""]*3 for _ in range(3)],
        "turn": None, "_created": time.time(),
    }
    text, markup = _dooz_render(inline_games[mid], lang)
    await _edit(bot, mid, text, markup)


@router.callback_query(F.data == "idooz_join")
async def idooz_join(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "joining":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if any(p["id"] == cb.from_user.id for p in game["players"]):
        await cb.answer(t("already_joined", get_user_lang(cb.from_user.id)), show_alert=True); return
    if len(game["players"]) >= 2:
        await cb.answer(t("game_full", get_user_lang(cb.from_user.id)), show_alert=True); return

    game["players"].append({"id": cb.from_user.id, "name": cb.from_user.first_name or "P2", "symbol": "⭕️"})
    game["status"] = "playing"
    game["turn"] = game["players"][0]["id"]

    lang = get_user_lang(cb.from_user.id)
    text, markup = _dooz_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    await cb.answer()


@router.callback_query(F.data.startswith("idooz_move_"))
async def idooz_move(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "playing":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if game["turn"] != cb.from_user.id:
        await cb.answer(t("not_your_turn", get_user_lang(cb.from_user.id)), show_alert=True); return

    try:
        idx = int(cb.data.split("_")[2])
        r, c = divmod(idx, 3)
    except: await cb.answer("❌"); return

    if game["board"][r][c]:
        await cb.answer(t("cell_occupied", get_user_lang(cb.from_user.id)), show_alert=True); return

    player = next(p for p in game["players"] if p["id"] == cb.from_user.id)
    game["board"][r][c] = player["symbol"]

    if _dooz_check(game["board"], player["symbol"]):
        game["finished"] = True
        game["winner"] = player["name"]
    elif all(cell for row in game["board"] for cell in row):
        game["finished"] = True
    else:
        nxt = next(p for p in game["players"] if p["id"] != cb.from_user.id)
        game["turn"] = nxt["id"]

    lang = get_user_lang(cb.from_user.id)
    text, markup = _dooz_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    if game.get("finished"):
        inline_games.pop(mid, None)
    await cb.answer()


# ═══════════ چهار در ردیف ═══════════

C4R, C4C = 6, 7


def _c4_check(b, sym):
    for r in range(C4R):
        for c in range(C4C-3):
            if all(b[r][c+i] == sym for i in range(4)): return True
    for r in range(C4R-3):
        for c in range(C4C):
            if all(b[r+i][c] == sym for i in range(4)): return True
    for r in range(3, C4R):
        for c in range(C4C-3):
            if all(b[r-i][c+i] == sym for i in range(4)): return True
    for r in range(C4R-3):
        for c in range(C4C-3):
            if all(b[r+i][c+i] == sym for i in range(4)): return True
    return False


def _c4_render(game, lang):
    p1, p2 = game["players"]
    if game["status"] == "joining":
        text = f"{E.PARTY}{E.GAME} <b>{t('c4_created', lang, name=p1['name'])}</b>\n\n{E.INFO} {t('waiting_players', lang)}"
        return text, kb([[success(f"{E.PLUS} {t('join_game', lang)}", "ic4_join")]])

    b = game["board"]
    if game.get("finished"):
        if game.get("winner"):
            text = f"{E.PARTY}{E.TROPHY} <b>{t('game_winner', lang, name=game['winner'])}</b>"
        else:
            text = f"{E.HEART} <b>{t('game_draw', lang)}</b>"
        rows = [[danger(b[r][c], "ic4_noop") for c in range(C4C)] for r in range(C4R)]
        return text, kb(rows)

    tp = p1 if game["turn"] == p1["id"] else p2
    text = f"{E.GAME} <b>{t('c4_title', lang)}</b>\n{p1['name']} ({p1['symbol']}) ⚔️ {p2['name']} ({p2['symbol']})\n\n{E.ARROW} {t('turn_of', lang)}: {tp['name']}"
    rows = [[danger(b[r][c], f"ic4_move_{c}") for c in range(C4C)] for r in range(C4R)]
    return text, kb(rows)


async def _init_connect4(bot, mid, uid, name, lang):
    inline_games[mid] = {
        "type": "connect4", "status": "joining",
        "players": [{"id": uid, "name": name, "symbol": "🔴"}],
        "board": [["⚪️"]*C4C for _ in range(C4R)],
        "turn": None, "_created": time.time(),
    }
    text, markup = _c4_render(inline_games[mid], lang)
    await _edit(bot, mid, text, markup)


@router.callback_query(F.data == "ic4_join")
async def ic4_join(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "joining":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if any(p["id"] == cb.from_user.id for p in game["players"]):
        await cb.answer(t("already_joined", get_user_lang(cb.from_user.id)), show_alert=True); return
    if len(game["players"]) >= 2:
        await cb.answer(t("game_full", get_user_lang(cb.from_user.id)), show_alert=True); return

    game["players"].append({"id": cb.from_user.id, "name": cb.from_user.first_name or "P2", "symbol": "🟡"})
    game["status"] = "playing"
    game["turn"] = game["players"][0]["id"]

    lang = get_user_lang(cb.from_user.id)
    text, markup = _c4_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    await cb.answer()


@router.callback_query(F.data.startswith("ic4_move_"))
async def ic4_move(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "playing":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if game["turn"] != cb.from_user.id:
        await cb.answer(t("not_your_turn", get_user_lang(cb.from_user.id)), show_alert=True); return

    try: col = int(cb.data.split("_")[2])
    except: await cb.answer("❌"); return

    row = -1
    for r in range(C4R-1, -1, -1):
        if game["board"][r][col] == "⚪️":
            row = r; break
    if row == -1:
        await cb.answer(t("c4_col_full", get_user_lang(cb.from_user.id)), show_alert=True); return

    player = next(p for p in game["players"] if p["id"] == cb.from_user.id)
    game["board"][row][col] = player["symbol"]

    if _c4_check(game["board"], player["symbol"]):
        game["finished"] = True; game["winner"] = player["name"]
    elif all(cell != "⚪️" for row in game["board"] for cell in row):
        game["finished"] = True
    else:
        nxt = next(p for p in game["players"] if p["id"] != cb.from_user.id)
        game["turn"] = nxt["id"]

    lang = get_user_lang(cb.from_user.id)
    text, markup = _c4_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    if game.get("finished"):
        inline_games.pop(mid, None)
    await cb.answer()


# ═══════════ سنگ کاغذ قیچی ═══════════

RPS_SYM = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RPS_RULES = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
RPS_NEEDED = 3


def _rps_choice_kb(lang):
    return kb([[
        success(f"🪨 {t('rps_rock', lang)}", "irps_choose_rock"),
        primary(f"📄 {t('rps_paper', lang)}", "irps_choose_paper"),
        danger(f"✂️ {t('rps_scissors', lang)}", "irps_choose_scissors"),
    ]])


def _rps_render(game, lang):
    p1, p2 = game["players"]
    if game["status"] == "joining":
        text = f"{E.PARTY}{E.GAME} <b>{t('rps_created', lang, name=p1['name'], n=RPS_NEEDED)}</b>\n\n{E.INFO} {t('waiting_players', lang)}"
        return text, kb([[success(f"{E.PLUS} {t('join_game', lang)}", "irps_join")]])

    s1 = game["scores"].get(p1["id"], 0)
    s2 = game["scores"].get(p2["id"], 0)
    if game.get("finished"):
        winner = p1 if s1 >= RPS_NEEDED else p2
        text = f"{E.TROPHY}{E.PARTY} <b>{t('rps_game_winner', lang, name=winner['name'])}</b>\n\n{E.CHART} {t('rps_final_score', lang, n1=p1['name'], s1=s1, n2=p2['name'], s2=s2)}"
        return text, None

    text = f"{E.GAME} <b>{t('rps_started', lang, name1=p1['name'], name2=p2['name'], n=RPS_NEEDED)}</b>\n\n{E.CHART} {t('rps_score_line', lang, n1=p1['name'], s1=s1, n2=p2['name'], s2=s2, needed=RPS_NEEDED)}"
    return text, _rps_choice_kb(lang)


async def _init_rps(bot, mid, uid, name, lang):
    inline_games[mid] = {
        "type": "rps", "status": "joining",
        "players": [{"id": uid, "name": name}],
        "choices": {}, "scores": {uid: 0},
        "rounds_needed": RPS_NEEDED, "_created": time.time(),
    }
    text, markup = _rps_render(inline_games[mid], lang)
    await _edit(bot, mid, text, markup)


@router.callback_query(F.data == "irps_join")
async def irps_join(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "joining":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if any(p["id"] == cb.from_user.id for p in game["players"]):
        await cb.answer(t("already_joined", get_user_lang(cb.from_user.id)), show_alert=True); return
    if len(game["players"]) >= 2:
        await cb.answer(t("game_full", get_user_lang(cb.from_user.id)), show_alert=True); return

    game["players"].append({"id": cb.from_user.id, "name": cb.from_user.first_name or "P2"})
    game["scores"][cb.from_user.id] = 0
    game["status"] = "playing"

    lang = get_user_lang(cb.from_user.id)
    text, markup = _rps_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    await cb.answer()


@router.callback_query(F.data.startswith("irps_choose_"))
async def irps_choose(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "playing":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if cb.from_user.id not in [p["id"] for p in game["players"]]:
        await cb.answer("تو بازیکن نیستی", show_alert=True); return
    if cb.from_user.id in game["choices"]:
        await cb.answer(t("rps_already_chosen", get_user_lang(cb.from_user.id)), show_alert=True); return

    choice = cb.data.split("_")[2]
    game["choices"][cb.from_user.id] = choice
    await cb.answer(t("rps_chosen", get_user_lang(cb.from_user.id)))

    if len(game["choices"]) < 2:
        lang = get_user_lang(cb.from_user.id)
        p1, p2 = game["players"]
        s1 = "✓" if p1["id"] in game["choices"] else "..."
        s2 = "✓" if p2["id"] in game["choices"] else "..."
        text = f"{E.BRAIN} <b>{t('rps_waiting', lang, name1=p1['name'], s1=s1, name2=p2['name'], s2=s2)}</b>"
        await _edit(cb.bot, mid, text, _rps_choice_kb(lang))
        return

    p1, p2 = game["players"]
    c1, c2 = game["choices"][p1["id"]], game["choices"][p2["id"]]
    winner = None
    if RPS_RULES[c1] == c2: winner = p1
    elif RPS_RULES[c2] == c1: winner = p2
    if winner: game["scores"][winner["id"]] += 1

    s1 = game["scores"][p1["id"]]
    s2 = game["scores"][p2["id"]]

    if s1 >= RPS_NEEDED or s2 >= RPS_NEEDED:
        game["finished"] = True
        lang = get_user_lang(cb.from_user.id)
        text, markup = _rps_render(game, lang)
        await _edit(cb.bot, mid, text, markup)
        inline_games.pop(mid, None)
        return

    game["choices"] = {}
    lang = get_user_lang(cb.from_user.id)
    text = (
        f"{E.GAME} <b>{t('rps_result', lang, name1=p1['name'], c1=RPS_SYM[c1], name2=p2['name'], c2=RPS_SYM[c2])}</b>\n\n"
        f"{E.CHART} {t('rps_score_line', lang, n1=p1['name'], s1=s1, n2=p2['name'], s2=s2, needed=RPS_NEEDED)}\n"
        f"{E.ARROW} {t('rps_next_round', lang)}"
    )
    await _edit(cb.bot, mid, text, _rps_choice_kb(lang))


# ═══════════ حافظه ═══════════

MEM_EMOJIS = ["🍎","🍓","🍉","🍕","🍔","🎂","🍦","🍩","🍿","🌸","🌻","🍁","🍀","🍄","🌈","⭐","🔥","🌊"]


def _mem_board():
    pool = random.sample(MEM_EMOJIS, 8) * 2
    random.shuffle(pool)
    return [pool[i*4:(i+1)*4] for i in range(4)]


def _mem_render(game, lang, finished=False):
    p1, p2 = game["players"]
    if finished:
        winner = p1 if p1["score"] > p2["score"] else (p2 if p2["score"] > p1["score"] else None)
        text = f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n\n{E.CHART} {t('memory_final_score', lang, name1=p1['name'], s1=p1['score'], name2=p2['name'], s2=p2['score'])}"
        if winner:
            text += f"\n\n{E.TROPHY} {t('game_winner', lang, name=winner['name'])}"
        else:
            text += f"\n\n{t('game_draw', lang)}"
    else:
        tp = next(p for p in game["players"] if p["id"] == game["turn"])
        text = (
            f"{E.BRAIN} <b>{t('memory_title', lang)}</b>\n"
            f"{E.CHART} {p1['name']}: {p1['score']} | {p2['name']}: {p2['score']}\n\n"
            f"{E.ARROW} {t('memory_turn', lang, name=tp['name'])}"
        )
    bv = game["board_view"]
    rows = []
    for r in range(4):
        row = [danger(bv[r][c], f"imem_{'noop' if finished else 'flip'}_{r}_{c}") for c in range(4)]
        rows.append(row)
    return text, kb(rows)


async def _init_memory(bot, mid, uid, name, lang):
    inline_games[mid] = {
        "type": "memory", "status": "joining",
        "players": [{"id": uid, "name": name, "score": 0}],
        "board_solution": _mem_board(),
        "board_view": [["❔"]*4 for _ in range(4)],
        "turn": None, "first_card": None, "is_checking": False,
        "matched": 0, "total": 8, "_created": time.time(),
    }
    p1 = inline_games[mid]["players"][0]
    text = f"{E.BRAIN} <b>{t('memory_created', lang, name=p1['name'], size='4x4')}</b>\n\n{E.INFO} {t('waiting_players', lang)}"
    await _edit(bot, mid, text, kb([[success(f"{E.PLUS} {t('join_game', lang)}", "imem_join")]]))


@router.callback_query(F.data == "imem_join")
async def imem_join(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "joining":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if any(p["id"] == cb.from_user.id for p in game["players"]):
        await cb.answer(t("already_joined", get_user_lang(cb.from_user.id)), show_alert=True); return
    if len(game["players"]) >= 2:
        await cb.answer(t("game_full", get_user_lang(cb.from_user.id)), show_alert=True); return

    game["players"].append({"id": cb.from_user.id, "name": cb.from_user.first_name or "P2", "score": 0})
    game["status"] = "playing"
    game["turn"] = game["players"][0]["id"]

    lang = get_user_lang(cb.from_user.id)
    text, markup = _mem_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    await cb.answer()


@router.callback_query(F.data.startswith("imem_flip_"))
async def imem_flip(cb: CallbackQuery):
    mid = cb.inline_message_id
    if not mid: await cb.answer("❌"); return
    game = inline_games.get(mid)
    if not game or game["status"] != "playing":
        await cb.answer("بازی فعال نیست", show_alert=True); return
    if game["is_checking"]:
        await cb.answer(t("wait_a_bit", get_user_lang(cb.from_user.id))); return
    if cb.from_user.id != game["turn"]:
        await cb.answer(t("not_your_turn", get_user_lang(cb.from_user.id)), show_alert=True); return

    try:
        parts = cb.data.split("_")
        r, c = int(parts[2]), int(parts[3])
    except: await cb.answer("❌"); return
    if game["board_view"][r][c] != "❔":
        await cb.answer(t("memory_already_flipped", get_user_lang(cb.from_user.id)), show_alert=True); return

    await cb.answer()
    val = game["board_solution"][r][c]
    game["board_view"][r][c] = val
    lang = get_user_lang(cb.from_user.id)

    if not game["first_card"]:
        game["first_card"] = {"r": r, "c": c, "val": val}
        text, markup = _mem_render(game, lang)
        await _edit(cb.bot, mid, text, markup)
        return

    game["is_checking"] = True
    text, markup = _mem_render(game, lang)
    await _edit(cb.bot, mid, text, markup)
    await asyncio.sleep(1.2)

    fc = game["first_card"]
    if val == fc["val"] and (r, c) != (fc["r"], fc["c"]):
        game["matched"] += 1
        for p in game["players"]:
            if p["id"] == game["turn"]:
                p["score"] += 1; break
    else:
        game["board_view"][r][c] = "❔"
        game["board_view"][fc["r"]][fc["c"]] = "❔"
        nxt = next(p for p in game["players"] if p["id"] != game["turn"])
        game["turn"] = nxt["id"]

    game["first_card"] = None
    game["is_checking"] = False

    if game["matched"] == game["total"]:
        text, markup = _mem_render(game, lang, True)
        await _edit(cb.bot, mid, text, markup)
        inline_games.pop(mid, None)
    else:
        text, markup = _mem_render(game, lang)
        await _edit(cb.bot, mid, text, markup)


@router.callback_query(F.data.endswith("_noop"))
async def noop(cb: CallbackQuery):
    await cb.answer()
