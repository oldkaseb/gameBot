# -*- coding: utf-8 -*-
"""webapp/backend/main.py — مینی‌اپ گیم باکس راینو با UI آرکید نئونی + تغییر تمام عکس‌ها از پنل ادمین"""

import base64
import io
import json
import os
import random
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

from database import db
from webapp.backend.game_logic.hokm import HokmGame

app = FastAPI(title="Rhino Game Box Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FONT_PATH = BASE_DIR / "Vazirmatn-SemiBold.ttf"

CUSTOM_HERO_FILE = BASE_DIR / "rhino_banner.png"
CUSTOM_MENU_BG = BASE_DIR / "menu_bg.png"
CUSTOM_CARPET_BG = BASE_DIR / "hokm_carpet.png"
CUSTOM_TOWER_BG = BASE_DIR / "tower_bg.png"
CUSTOM_TOWER_HERO = BASE_DIR / "tower_hero.png"

hokm_rooms: dict[str, HokmGame] = {}
guess_rooms: dict[str, dict] = {}

GAME_META = {
    "hub":          {"title": "RHINO GAME BOX", "c1": (18, 10, 42),  "c2": (109, 40, 217)},
    "demontower":   {"title": "DEMON TOWER",    "c1": (85, 12, 18),  "c2": (220, 38, 38)},
    "wip1":         {"title": "DUNGEON HEIST",  "c1": (30, 27, 75),  "c2": (124, 58, 237)},
    "wip2":         {"title": "CYBER VAULT",    "c1": (6, 78, 59),   "c2": (16, 185, 129)},
    "tower_admin":  {"title": "TOWER ADMIN",    "c1": (30, 27, 75),  "c2": (124, 58, 237)},
    "hokm":         {"title": "HOKM 4P",        "c1": (127, 17, 22), "c2": (220, 38, 38)},
    "hokm2p":       {"title": "HOKM 2P",        "c1": (105, 15, 45), "c2": (219, 39, 119)},
    "2048":         {"title": "2048 PUZZLE",    "c1": (30, 58, 138), "c2": (59, 130, 246)},
    "spuzzle":      {"title": "PUZZLE 15",      "c1": (12, 74, 110), "c2": (14, 165, 233)},
    "samegame":     {"title": "COLOR MATCH",    "c1": (88, 28, 135), "c2": (168, 85, 247)},
    "dooz":         {"title": "RINGS 2P",       "c1": (15, 23, 42),  "c2": (59, 130, 246)},
    "doz4p":        {"title": "RINGS 4P",       "c1": (80, 7, 36),   "c2": (236, 72, 153)},
    "connect4":     {"title": "CONNECT 4",      "c1": (6, 78, 59),   "c2": (16, 185, 129)},
    "rps":          {"title": "ROCK PAPER",     "c1": (49, 46, 129), "c2": (99, 102, 241)},
    "memory":       {"title": "MEMORY",         "c1": (76, 29, 149), "c2": (139, 92, 246)},
    "typing":       {"title": "SPEED TYPE",     "c1": (120, 53, 15), "c2": (245, 158, 11)},
    "hangman":      {"title": "WORD GUESS",     "c1": (136, 19, 55), "c2": (225, 29, 72)},
    "guess":        {"title": "NUMBER GUESS",   "c1": (20, 83, 45),  "c2": (34, 197, 94)},
    "gardone_anim": {"title": "LUCKY WHEEL",    "c1": (76, 29, 149), "c2": (217, 70, 239)},
}


def generate_game_banner(game_key: str) -> bytes:
    """تولید پوستر گرافیکی نئونی در صورتی که هنوز عکسی از پنل ادمین برای بازی آپلود نشده باشد"""
    meta = GAME_META.get(game_key, GAME_META["hub"])
    w, h = 500, 500
    img = Image.new("RGB", (w, h), meta["c1"])
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = meta["c1"]
    r2, g2, b2 = meta["c2"]
    for y in range(h):
        ratio = y / h
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    draw.ellipse([60, 60, w - 60, h - 60], outline=(255, 255, 255, 40), width=4)
    draw.rounded_rectangle([18, 18, w - 18, h - 18], radius=36, outline=(255, 255, 255), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def _get_saved_ui_assets() -> dict:
    try:
        from games.demon_tower import get_dt_config
        raw = await get_dt_config("ui_assets", "{}")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


@app.get("/api/ui_assets")
async def api_get_ui_assets():
    """دریافت تمام عکس‌های سفارشی آپلودشده در پنل ادمین + آمار کلی برای نمایش در UI"""
    assets = await _get_saved_ui_assets()
    recent_wins = []
    try:
        await db.ensure_pool()
        rows = await db.pool.fetch("""
            SELECT first_name, username FROM users
            ORDER BY user_id DESC LIMIT 6
        """)
        games_sample = ["HOKM 4P", "DEMON TOWER", "2048", "RINGS 2P", "RPS", "GUESS"]
        for idx, r in enumerate(rows):
            recent_wins.append({
                "name": (r["first_name"] or r["username"] or f"Player {idx+1}")[:12],
                "game": games_sample[idx % len(games_sample)],
                "time": f"{idx + 1}m ago",
            })
    except Exception:
        pass
    return {"ok": True, "assets": assets, "recent_wins": recent_wins}


@app.get("/api/custom_bg/{bg_name}")
async def serve_custom_bg(bg_name: str):
    # ۱. اولویت اول: بررسی عکس آپلودشده توسط ادمین در دیتابیس
    assets = await _get_saved_ui_assets()
    b64_data = assets.get(bg_name, "")
    if b64_data and b64_data.startswith("data:image"):
        try:
            header, encoded = b64_data.split(",", 1)
            mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
            return Response(content=base64.b64decode(encoded), media_type=mime)
        except Exception:
            pass

    # ۲. اولویت دوم: فایل‌های موجود در مخزن گیت‌هاب
    if bg_name in ("hero", "rhino_hero") and CUSTOM_HERO_FILE.exists():
        return FileResponse(str(CUSTOM_HERO_FILE), media_type="image/png")
    if bg_name in ("menu", "menu_bg") and CUSTOM_MENU_BG.exists():
        return FileResponse(str(CUSTOM_MENU_BG), media_type="image/png")
    if bg_name in ("carpet", "hokm_carpet") and CUSTOM_CARPET_BG.exists():
        return FileResponse(str(CUSTOM_CARPET_BG), media_type="image/png")
    if bg_name == "tower_bg" and CUSTOM_TOWER_BG.exists():
        return FileResponse(str(CUSTOM_TOWER_BG), media_type="image/png")
    if bg_name == "tower_hero" and CUSTOM_TOWER_HERO.exists():
        return FileResponse(str(CUSTOM_TOWER_HERO), media_type="image/png")

    # ۳. اولویت سوم: تولید پوستر گرافیکی نئونی
    png_bytes = generate_game_banner(game_key=bg_name)
    return Response(content=png_bytes, media_type="image/png")


@app.get("/api/banner/{game_type}.png")
async def serve_game_banner(game_type: str):
    return await serve_custom_bg(game_type)


class WinPayload(BaseModel):
    uid: int
    game_type: str
    best_time: float | None = None


class InvitePlayersPayload(BaseModel):
    inviter_id: int
    inviter_name: str
    game_type: str
    session: str
    targets: list[str]
    extra: str = ""


class HokmActionPayload(BaseModel):
    session: str
    mode: str = "4p"
    uid: int
    name: str = "Player"
    username: str = ""
    photo: str = ""
    action: str
    suit: str | None = None
    card: str | None = None
    text: str | None = None
    mic: bool | None = None
    idx1: int | None = None
    idx2: int | None = None


class GuessActionPayload(BaseModel):
    session: str
    uid: int
    name: str
    action: str
    min_val: int = 1
    max_val: int = 100
    guess_val: int | None = None


class TowerActionPayload(BaseModel):
    uid: int
    name: str = "Player"
    lang: str = "fa"
    action: str = "state"
    move: str | None = None
    gender: str | None = None
    item_id: int | None = None
    weapon_id: int | None = None
    amount: int | None = None
    target: str | None = None
    pack_id: str | None = None
    code: str | None = None
    coins: int | None = None
    voucher_type: str | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/tower/action")
async def tower_action_endpoint(payload: TowerActionPayload):
    from games.demon_tower import handle_tower_api_action
    return await handle_tower_api_action(payload.model_dump())


@app.post("/api/tower/admin")
async def tower_admin_endpoint(request: Request):
    from games.demon_tower import handle_tower_admin_api
    body = await request.json()
    return await handle_tower_admin_api(body)


@app.get("/api/check_join/{user_id}")
async def api_check_join(user_id: int):
    try:
        from aiogram import Bot
        from runtime import check_forced_join
        bot_token = os.environ.get("BOT_TOKEN", "")
        if not bot_token or user_id <= 0:
            return {"ok": True, "joined": True, "channels": []}

        temp_bot = Bot(token=bot_token)
        try:
            missing = await check_forced_join(temp_bot, user_id)
        finally:
            await temp_bot.session.close()

        channels_data = []
        for ch in missing:
            uname = (ch.get("username") or "").lstrip("@")
            cid = str(ch.get("chat_id") or "").lstrip("@")
            link_target = uname or cid
            url = f"https://t.me/{link_target}" if link_target and not link_target.startswith("-") else "https://t.me/RHINOBOT_TM"
            channels_data.append({
                "title": ch.get("title") or uname or "Sponsor Channel",
                "url": url,
            })

        return {
            "ok": True,
            "joined": len(channels_data) == 0,
            "channels": channels_data,
        }
    except Exception:
        return {"ok": True, "joined": True, "channels": []}


@app.post("/api/invite_friends")
async def api_invite_friends(payload: InvitePlayersPayload):
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from utils.premium import success, kb
    from runtime import get_bot_username

    bot_token = os.environ.get("BOT_TOKEN", "")
    short_name = os.environ.get("MINI_APP_SHORT_NAME", "RhinoGamesApp").strip() or "RhinoGamesApp"
    bot_user = get_bot_username()

    await db.ensure_pool()
    not_started = []
    invited = []

    temp_bot = Bot(token=bot_token) if bot_token else None
    try:
        for raw_t in payload.targets:
            t_str = (raw_t or "").strip()
            if not t_str:
                continue

            row = None
            if t_str.lstrip("-").isdigit():
                row = await db.pool.fetchrow("SELECT user_id, first_name, username FROM users WHERE user_id=$1", int(t_str))
            else:
                uname = t_str.lstrip("@").lower()
                row = await db.pool.fetchrow("SELECT user_id, first_name, username FROM users WHERE LOWER(username)=$1", uname)

            if not row:
                not_started.append(t_str)
                continue

            target_uid = row["user_id"]
            start_param = f"{payload.game_type}__{payload.session}__fa"
            join_url = f"https://t.me/{bot_user}/{short_name}?startapp={start_param}"

            if temp_bot:
                try:
                    await temp_bot.send_message(
                        chat_id=target_uid,
                        text=(
                            f"🎮 <b>RHINO GAME BOX</b>\n\n"
                            f"👤 <b>{payload.inviter_name}</b> invited you to play!\n"
                            f"Tap below to join the table:"
                        ),
                        reply_markup=kb([[success("▶️ Join Game", url=join_url)]]),
                        parse_mode=ParseMode.HTML,
                    )
                    invited.append(row["first_name"] or t_str)
                except Exception:
                    not_started.append(t_str)
    finally:
        if temp_bot:
            await temp_bot.session.close()

    return {
        "ok": len(not_started) == 0,
        "invited": invited,
        "not_started": not_started,
    }


@app.post("/api/win")
async def record_win(payload: WinPayload):
    try:
        await db.add_win(payload.uid, payload.game_type, payload.best_time)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/hokm/action")
async def hokm_action_endpoint(payload: HokmActionPayload):
    session_key = f"{payload.mode}_{payload.session}"
    if session_key not in hokm_rooms:
        hokm_rooms[session_key] = HokmGame(session_key, mode=payload.mode)

    game = hokm_rooms[session_key]
    game.join(payload.uid, payload.name, payload.username, payload.photo)

    res = {"ok": True}
    if payload.action == "add_bots":
        game.fill_with_bots()
    elif payload.action == "start_match":
        res = game.start_match(fill_bots=True)
    elif payload.action == "swap_seats" and payload.idx1 is not None and payload.idx2 is not None:
        res = game.swap_seats(payload.uid, payload.idx1, payload.idx2)
    elif payload.action == "choose_trump" and payload.suit:
        res = game.choose_trump(payload.uid, payload.suit)
    elif payload.action == "play_card" and payload.card:
        res = game.play_card(payload.uid, payload.card)
        if game.status == "finished":
            try:
                await db.add_win(payload.uid, "hokm")
            except Exception:
                pass
    elif payload.action == "chat" and payload.text:
        game.post_bubble(payload.uid, payload.text)
    elif payload.action == "mic" and payload.mic is not None:
        game.toggle_mic(payload.uid, payload.mic)
    elif payload.action in ("state", "step_bot"):
        game.step_bot_once()

    return {
        **res,
        "state": game.get_state_for_player(payload.uid),
    }


@app.post("/api/guess/action")
async def guess_action_endpoint(payload: GuessActionPayload):
    sid = payload.session
    if payload.action == "create" or sid not in guess_rooms:
        lo = min(payload.min_val, payload.max_val)
        hi = max(payload.min_val, payload.max_val)
        if hi - lo < 2:
            hi = lo + 100
        guess_rooms[sid] = {
            "session": sid,
            "host_id": payload.uid,
            "host_name": payload.name,
            "min": lo,
            "max": hi,
            "secret": random.randint(lo, hi),
            "winner_id": None,
            "winner_name": "",
            "history": [],
        }

    room = guess_rooms[sid]

    if payload.action == "restart":
        if int(payload.uid) != int(room["host_id"]):
            return {"ok": False, "error": "Only host can restart!", "room": room}
        room["secret"] = random.randint(room["min"], room["max"])
        room["winner_id"] = None
        room["winner_name"] = ""
        room["history"] = []

    elif payload.action == "guess" and payload.guess_val is not None and not room["winner_id"]:
        gval = int(payload.guess_val)
        if gval == room["secret"]:
            room["winner_id"] = payload.uid
            room["winner_name"] = payload.name
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "🏆"})
            try:
                await db.add_win(payload.uid, "number_guess")
            except Exception:
                pass
        elif gval < room["secret"]:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬆️"})
        else:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬇️"})
        room["history"] = room["history"][:12]

    safe_room = {k: v for k, v in room.items() if k != "secret"}
    if room["winner_id"]:
        safe_room["secret_revealed"] = room["secret"]
    return {"ok": True, "room": safe_room}


@app.get("/api/gardone/{chat_id}")
async def get_gardone_data(chat_id: int):
    from games.gardone import active_gardones
    g = active_gardones.get(chat_id)
    if not g:
        return {"ok": False, "names": ["Player 1", "Player 2"], "winners": ["Player 1"]}
    names = [p["name"] for p in g["participants"].values()]
    winners = [w["name"] for w in g.get("winners", [])]
    return {"ok": True, "names": names, "winners": winners, "host": g.get("host_name", "")}

@app.post("/api/social/action")
async def social_action_endpoint(request: Request):
    from social_platform import handle_social_api
    body = await request.json()
    return await handle_social_api(body)

MINIAPP_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <title>__OG_TITLE__</title>
  <meta property="og:type" content="website" />
  <meta property="og:title" content="__OG_TITLE__" />
  <meta property="og:description" content="گیم باکس راینو — مجموعه بازی‌های گروهی و آنلاین" />
  <meta property="og:image" content="__OG_IMAGE__" />
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    ::-webkit-scrollbar { width: 0px; height: 0px; }
    html, body {
      width: 100vw;
      height: 100vh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: #090514;
      background-image:
        var(--custom-menu-bg, none),
        radial-gradient(circle at 15% 10%, rgba(124, 58, 237, 0.25) 0%, transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(219, 39, 119, 0.18) 0%, transparent 45%);
      background-size: cover;
      background-position: center;
      color: #fff;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    input, textarea, select {
      user-select: text !important;
      -webkit-user-select: text !important;
    }
    #app {
      width: 100vw;
      height: 100vh;
      padding-top: calc(env(safe-area-inset-top, 10px) + 32px);
      padding-bottom: env(safe-area-inset-bottom, 6px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .glass-panel {
      background: rgba(19, 14, 38, 0.72);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.11);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .glass-soft {
      background: rgba(255, 255, 255, 0.06);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .btn-primary {
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
      border: 1px solid rgba(255,255,255,0.22);
      box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35);
    }
    .btn-success {
      background: linear-gradient(135deg, #059669, #10b981);
      border: 1px solid rgba(255,255,255,0.22);
    }
    .btn-danger {
      background: linear-gradient(135deg, #e11d48, #ef4444);
      border: 1px solid rgba(255,255,255,0.22);
    }
    .ltr-grid { direction: ltr !important; }

    /* کارت‌های مربعی کازینو-آرکید مشابه تصویر ارسالی */
    .arcade-card {
      position: relative;
      aspect-ratio: 1 / 1.04;
      border-radius: 24px;
      overflow: hidden;
      border: 1.5px solid rgba(168, 85, 247, 0.32);
      background: #130d26;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.65);
      transition: transform 0.16s ease, border-color 0.16s ease;
    }
    .arcade-card:active {
      transform: scale(0.96);
      border-color: rgba(168, 85, 247, 0.85);
    }
    .arcade-card-bg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }
    .arcade-card-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(10, 6, 24, 0.55) 0%, rgba(10, 6, 24, 0.15) 45%, rgba(10, 6, 24, 0.88) 100%);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 14px 12px 11px 12px;
    }
    .arcade-title {
      font-weight: 900;
      font-size: 1.15rem;
      line-height: 1.15;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: #ffffff;
      text-shadow: 0 3px 12px rgba(0, 0, 0, 0.9);
      text-align: right;
    }
    .pill-players {
      background: rgba(15, 23, 42, 0.78);
      backdrop-filter: blur(6px);
      border: 1px solid rgba(52, 211, 153, 0.35);
      color: #34d399;
      font-size: 10px;
      font-weight: 900;
      padding: 2px 7px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }
    .pill-mode-pve {
      background: linear-gradient(135deg, #0ea5e9, #2563eb);
      color: #fff;
      font-size: 10px;
      font-weight: 900;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .pill-mode-slot {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #000;
      font-size: 10px;
      font-weight: 900;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .pill-new {
      background: rgba(88, 28, 135, 0.85);
      border: 1px solid rgba(192, 132, 252, 0.5);
      color: #f3e8ff;
      font-size: 10px;
      font-weight: 900;
      padding: 2px 8px;
      border-radius: 999px;
    }
    .bottom-dock {
      background: rgba(18, 13, 36, 0.88);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 28px;
      box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.65);
    }

    .tower-bg-wrap {
      background-image:
        var(--custom-tower-bg, __TOWER_BG__),
        radial-gradient(circle at top, rgba(153, 27, 27, 0.45) 0%, rgba(15, 23, 42, 0.92) 70%);
      background-size: cover;
      background-position: center;
    }
    .persian-carpet {
      position: relative;
      width: 100%;
      height: 100%;
      background-color: #781014;
      background-image:
        var(--custom-carpet-bg, __CARPET_BG__),
        radial-gradient(ellipse at center, rgba(185, 28, 28, 0.52) 0%, rgba(102, 10, 14, 0.94) 68%, #3a0608 100%),
        repeating-linear-gradient(45deg, rgba(245, 158, 11, 0.06) 0px, rgba(245, 158, 11, 0.06) 2px, transparent 2px, transparent 6px);
      background-size: cover;
      background-position: center;
      border: 6px solid #1e1b4b;
      border-radius: 18px;
      box-shadow: inset 0 0 0 2px #d97706, inset 0 0 0 6px #450a0a, inset 0 0 40px rgba(0,0,0,0.85);
    }
    .carpet-medallion {
      position: absolute;
      top: 44%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 185px;
      height: 185px;
      border-radius: 50%;
      border: 2.5px solid rgba(251, 191, 36, 0.42);
      background: radial-gradient(circle, rgba(30, 58, 138, 0.32) 0%, rgba(127, 29, 29, 0.38) 65%, transparent 75%);
      pointer-events: none;
    }
    .playing-card {
      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
      border: 1.5px solid #94a3b8;
      border-radius: 10px;
      box-shadow: -2px 5px 12px rgba(0, 0, 0, 0.65);
      color: #0f172a;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 5px 6px;
      font-family: Georgia, serif;
    }
    .playing-card.red { color: #dc2626; }
    .card-back-real {
      background-color: #1e3a8a;
      background-image:
        radial-gradient(circle, #fbbf24 18%, transparent 19%),
        repeating-linear-gradient(45deg, rgba(255,255,255,0.14) 0, rgba(255,255,255,0.14) 2px, transparent 2px, transparent 5px);
      background-size: 12px 12px;
      border: 1.5px solid #fde68a;
      border-radius: 7px;
      box-shadow: -1px 3px 7px rgba(0,0,0,0.75);
    }
  </style>
</head>
<body>
  <div id="app"></div>

  <script>
    window.onerror = function(msg, url, line) {
      console.warn("MiniApp non-fatal error:", msg, line);
      return true;
    };

    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }

    function isUserTyping() {
      const el = document.activeElement;
      return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT');
    }

    /* ─── ابزار فشرده‌سازی و آپلود مستقیم عکس از گالری گوشی ─── */
    window.uploadedImages = {};
    window.uiAssetsMap = {};
    window.recentWinsList = [];

    window.handleImageUpload = function(inputEl, targetKey, previewImgId) {
      const file = inputEl.files && inputEl.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(ev) {
        const img = new Image();
        img.onload = function() {
          const canvas = document.createElement('canvas');
          const maxDim = 560;
          let w = img.width, h = img.height;
          if (w > h && w > maxDim) { h = Math.round(h * maxDim / w); w = maxDim; }
          else if (h >= w && h > maxDim) { w = Math.round(w * maxDim / h); h = maxDim; }
          canvas.width = w; canvas.height = h;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, w, h);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.84);
          window.uploadedImages[targetKey] = dataUrl;
          const prev = document.getElementById(previewImgId);
          if (prev) {
            prev.src = dataUrl;
            prev.classList.remove('hidden');
          }
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    };

    function getAssetImg(key, fallbackUrl = '') {
      if (window.uiAssetsMap && window.uiAssetsMap[key]) {
        return window.uiAssetsMap[key];
      }
      return fallbackUrl || (`/api/custom_bg/${key}`);
    }

    function applyDynamicCssBackgrounds() {
      const rootStyle = document.documentElement.style;
      if (window.uiAssetsMap?.menu_bg) {
        document.body.style.backgroundImage = `url('${window.uiAssetsMap.menu_bg}')`;
      } else {
        document.body.style.backgroundImage = `radial-gradient(circle at 15% 10%, rgba(124, 58, 237, 0.25) 0%, transparent 45%), radial-gradient(circle at 85% 85%, rgba(219, 39, 119, 0.18) 0%, transparent 45%)`;
      }
      if (window.uiAssetsMap?.hokm_carpet) {
        rootStyle.setProperty('--custom-carpet-bg', `url('${window.uiAssetsMap.hokm_carpet}'),`);
      }
      if (window.uiAssetsMap?.tower_bg) {
        rootStyle.setProperty('--custom-tower-bg', `url('${window.uiAssetsMap.tower_bg}'),`);
      }
    }

    async function loadUiAssets() {
      try {
        const res = await fetch('/api/ui_assets');
        const data = await res.json();
        if (data.assets) {
          window.uiAssetsMap = data.assets;
          applyDynamicCssBackgrounds();
        }
        if (data.recent_wins) window.recentWinsList = data.recent_wins;
      } catch (e) {}
    }

    const HERO_CUSTOM_IMG = "__HERO_IMAGE__";
    const TOWER_HERO_IMG = "__TOWER_HERO__";
    const BOT_USERNAME = "__BOT_USERNAME__";
    const SHORT_NAME = "__SHORT_NAME__";
    const OWNER_IDS = [7662192190, 6041119040];

    const params = new URLSearchParams(window.location.search);
    const startParam = tg?.initDataUnsafe?.start_param || params.get('startapp') || params.get('tgWebAppStartParam') || '';
    let parsedGame = params.get('game') || '';
    let parsedChat = params.get('chat') || params.get('session') || ('rm_' + Math.floor(Math.random()*89999+10000));
    let lang = localStorage.getItem('rhino_lang') || params.get('lang') || (tg?.initDataUnsafe?.user?.language_code || 'fa').split('-')[0].toLowerCase();

    if (startParam) {
      const parts = startParam.split('__');
      if (parts[0]) parsedGame = parts[0];
      if (parts[1]) parsedChat = parts[1];
      if (parts[2] && ['fa','en','ar','tr','ru','de','zh'].includes(parts[2])) lang = parts[2];
    }
    if (!['fa','en','ar','tr','ru','de','zh'].includes(lang)) lang = 'fa';

    function applyDir() {
      document.documentElement.dir = (lang === 'fa' || lang === 'ar') ? 'rtl' : 'ltr';
    }
    applyDir();

    const I18N = {
      fa: {
        heroTitle: "گیم باکس راینو",
        heroBody: "به گیم باکس راینو خوش اومدی رفیق\nاینجا کلی بازی خفن رو توی یک ربات برات جمع کردیم\nلذت ببر دوست من",
        bigWins: "برندگان اخیر",
        wipBadge: "SOON",
        backMenu: "منو",
        playBtn: "ورود",
        optBot: "🤖 بازی با ربات",
        optInvite: "📩 دعوت دوستان با ربات",
        optShare: "📤 اشتراک‌گذاری لینک میز",
        sendInviteBtn: "ارسال دعوت‌نامه",
        enterTableBtn: "ورود به میز",
        notStartedWarn: "⚠️ این کاربران هنوز ربات را استارت نکرده‌اند (به آن‌ها بگو ابتدا ربات را استارت کنند):",
        swipeHint: "صفحه را به ۴ جهت بکشید (Swipe)",
        restart: "شروع مجدد",
        score: "امتیاز",
        turn: "نوبت",
        winner: "برنده",
        trump: "حکم",
        ourTricks: "دست ما",
        oppTricks: "دست حریف",
        sets: "ست",
        chooseTrumpPrompt: "👑 شما حاکم هستید! خال حکم را انتخاب کنید:",
        waitingHakem: "در حال تعیین حکم...",
        pickPartner: "انتخاب یار",
        fillBotsBtn: "🤖 پر کردن با هوش مصنوعی و شروع",
        rpsAskWins: "تعداد بردهای لازم:",
        winsUnit: "برد",
        rock: "سنگ", paper: "کاغذ", scissors: "قیچی",
        pickColor: "رنگ مهره شما:",
        fromNum: "از عدد:", toNum: "تا عدد:",
        createGame: "ساخت بازی",
        submitBtn: "ثبت",
        playAgainBtn: "🔄 یه دور دیگه",
        chatPlaceholder: "پیام شفاف بالای اسم...",
        sendBtn: "ارسال",
        micOn: "🎙️ روشن", micOff: "🔇 مایک",
        dt: {
          floorBtn: "طبقه", enterBattle: "ورود به نبرد", charBtn: "🦸 کاراکتر", hospBtn: "🏥 بیمارستان",
          vaultBtn: "🏦 خزانه", shopBtn: "🛒 فروشگاه", giftBtn: "🎁 کد هدیه", voucherBtn: "🎟️ درخواست ووچر",
          accBtn: "👤 حسابم", backTower: "بازگشت به منوی برج", humanity: "انسانیت",
          bossPower: "قدرت غول", bossWeak: "نقطه ضعف", bossReward: "پاداش مرحله",
          pickWeaponHint: "سلاح خود را برای ورود به مرحله انتخاب کنید:", startBattleBtn: "⚔️ شروع نبرد طبقه",
          pickGenderTitle: "انتخاب کاراکتر (یک‌بار و غیرقابل تغییر)", male: "مرد 🚹", female: "زن 🚺",
          equipped: "تجهیز شده", select: "انتخاب", buy: "خرید",
          hospDesc: "پس از هر جنگ برای بازیابی جان و انسانیت به بیمارستان بیایید. اگر انسانیت صفر شود ۲ روز به خواب می‌روید!",
          healBtn: "💉 بستری شدن و درمان کامل", deposit: "سپرده‌گذاری", withdraw: "برداشت",
          sellLootBtn: "💰 فروش غنیمت‌ها", transferTitle: "💸 انتقال سکه به کاربر دیگر (۳٪ مالیات)",
          transferBtn: "ارسال سکه (کسر ۳٪ مالیات)", redeemBtn: "دریافت هدیه",
          vchOfferHint: "مقدار سکه پیشنهادی...",
          vchTypes: ["ووچر استارز", "ووچر گیفت", "ووچر سندر", "ووچر شارژ ربات"],
          vchSendBtn: "ارسال درخواست برای مالک",
          vchChatTitle: "💬 وضعیت درخواست‌های ووچر (در انتظار پاسخ مالک)",
          vchPending: "⏳ در انتظار پاسخ مالک...",
          vchApproved: "✅ تایید شد — پیام کد ووچر را از پیوی برای @oldkaseb فوروارد کنید",
          vchRejected: "❌ رد شد (سکه عودت داده شد)", ownerNote: "یادداشت مالک"
        },
        games: {
          wip1: "شکارچی سیاه‌چال", wip2: "هک گاوصندوق", wip3: "برج شیاطین", wip3Sub: "RPG • طبقات و غول‌ها",
          hokm: "حکم ۴ نفره", hokmSub: "۴ نفره • فرش ایرانی",
          hokm2p: "حکم ۲ نفره", hokm2pSub: "۲ نفره • تک‌به‌تک",
          dooz: "دوز ۲ نفره", doozSub: "۲ نفره • حلقه رنگی",
          doz4p: "دوز ۴ نفره", doz4pSub: "۴ نفره • حلقه رنگی",
          connect4: "چهار در ردیف", connect4Sub: "۲ نفره • استراتژیک",
          rps: "سنگ کاغذ قیچی", rpsSub: "۲ نفره • سرعتی",
          guess: "حدس عدد", guessSub: "گروهی • رقابتی",
          g2048: "پازل ۲۰۴۸", g2048Sub: "تک‌نفره • لمسی",
          spuzzle: "پازل ۱۵", spuzzleSub: "تک‌نفره • لمسی",
          samegame: "جفت‌های رنگی", samegameSub: "تک‌نفره • رنگی",
          memory: "حافظه", memorySub: "۲ نفره • تمرکزی",
          typing: "تایپ سرعتی", typingSub: "سرعتی • رکوردی",
          hangman: "حدس کلمه", hangmanSub: "فکری • حروف"
        }
      },
      en: {
        heroTitle: "Rhino Game Box",
        heroBody: "Welcome to Rhino Game Box my friend\nAwesome games gathered in one bot for you\nEnjoy my friend",
        bigWins: "BIG WINS",
        wipBadge: "SOON", backMenu: "Menu", playBtn: "Play",
        optBot: "🤖 Play with AI Bot", optInvite: "📩 Invite Friends via Bot", optShare: "📤 Share Table Link",
        sendInviteBtn: "Send Invites", enterTableBtn: "Enter Table",
        notStartedWarn: "⚠️ These users haven't started the bot yet:",
        swipeHint: "Swipe in 4 directions to move", restart: "Restart", score: "Score", turn: "Turn", winner: "Winner",
        trump: "Trump", ourTricks: "Our Tricks", oppTricks: "Opp Tricks", sets: "Sets",
        chooseTrumpPrompt: "👑 Choose Trump suit:", waitingHakem: "Choosing trump...", pickPartner: "Set Partner",
        fillBotsBtn: "🤖 Fill with AI & Start", rpsAskWins: "Target wins:", winsUnit: "Wins",
        rock: "Rock", paper: "Paper", scissors: "Scissors", pickColor: "Your Color:",
        fromNum: "From:", toNum: "To:", createGame: "Create Game", submitBtn: "Submit", playAgainBtn: "🔄 Play Again",
        chatPlaceholder: "Quick message...", sendBtn: "Send", micOn: "🎙️ On", micOff: "🔇 Mic",
        dt: {
          floorBtn: "Floor", enterBattle: "Battle", charBtn: "🦸 Character", hospBtn: "🏥 Hospital",
          vaultBtn: "🏦 Vault", shopBtn: "🛒 Shop", giftBtn: "🎁 Gift Code", voucherBtn: "🎟️ Voucher",
          accBtn: "👤 My Account", backTower: "Back to Tower Menu", humanity: "Humanity",
          bossPower: "Boss Power", bossWeak: "Weakness", bossReward: "Stage Reward",
          pickWeaponHint: "Select your weapon:", startBattleBtn: "⚔️ Start Floor Battle",
          pickGenderTitle: "Choose Character (One-time)", male: "Male 🚹", female: "Female 🚺",
          equipped: "Equipped", select: "Equip", buy: "Buy",
          hospDesc: "Heal after battles. If Humanity hits 0, you sleep for 2 days!",
          healBtn: "💉 Enter Hospital & Heal", deposit: "Deposit", withdraw: "Withdraw",
          sellLootBtn: "💰 Sell All Loot", transferTitle: "💸 Transfer Coins (3% Tax)",
          transferBtn: "Send Coins (3% Tax)", redeemBtn: "Redeem Code",
          vchOfferHint: "Offered Coins...",
          vchTypes: ["Stars Voucher", "Gift Voucher", "Sender Voucher", "Bot Charge Voucher"],
          vchSendBtn: "Send Request to Owner",
          vchChatTitle: "💬 Voucher Requests",
          vchPending: "⏳ Waiting for Owner...",
          vchApproved: "✅ Approved — Forward code from Bot PM to @oldkaseb",
          vchRejected: "❌ Rejected (Refunded)", ownerNote: "Owner Note"
        },
        games: {
          wip1: "DUNGEON HEIST", wip2: "CYBER VAULT", wip3: "DEMON TOWER", wip3Sub: "RPG • Bosses & Loot",
          hokm: "HOKM 4P", hokmSub: "4 Players • Cards", hokm2p: "HOKM 2P", hokm2pSub: "2 Players • Duel",
          dooz: "RINGS 2P", doozSub: "2 Players • Color", doz4p: "RINGS 4P", doz4pSub: "4 Players • Color",
          connect4: "CONNECT 4", connect4Sub: "2 Players • Strategy", rps: "ROCK PAPER", rpsSub: "2 Players • Duel",
          guess: "NUMBER GUESS", guessSub: "Group • Live", g2048: "2048 PUZZLE", g2048Sub: "Solo • Swipe",
          spuzzle: "PUZZLE 15", spuzzleSub: "Solo • Swipe", samegame: "COLOR MATCH", samegameSub: "Solo • Match",
          memory: "MEMORY", memorySub: "2 Players • Match", typing: "SPEED TYPE", typingSub: "Speed • Record",
          hangman: "WORD GUESS", hangmanSub: "Solo • Letters"
        }
      }
    };

    function T() { return I18N[lang] || I18N.fa; }

    let currentGame = parsedGame || 'hub';
    let hubFilter = 'all'; // all | pve | pvp
    const tgUser = tg?.initDataUnsafe?.user || {};
    const realTgUid = tgUser.id || Number(params.get('uid')) || 0;
    const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
    const isOwner = OWNER_IDS.includes(Number(uid));
    const myName = tgUser.first_name || 'CEORHINO';
    const myUsername = tgUser.username || '';
    const myPhoto = tgUser.photo_url || '';

    let hokmPollTimer = null;
    let guessPollTimer = null;
    let isJoinVerified = false;
    let lobbyState = { game: '', maxPlayers: 2, rpsTargetWins: 3, step: 'options', inviteWarning: '', inviteSuccess: '' };

    window.cycleLang = function() {
      const codes = ['fa', 'en'];
      lang = codes[(codes.indexOf(lang) + 1) % codes.length];
      localStorage.setItem('rhino_lang', lang);
      applyDir();
      render();
    };

    function renderTopBar(titleText = '') {
      const langFlags = { fa: '🇮🇷 FA', en: '🇬🇧 EN' };
      return `
        <div class="glass-panel mx-3 mb-2 px-3 py-2 rounded-2xl flex justify-between items-center shrink-0">
          <div class="flex items-center gap-1.5">
            ${currentGame !== 'hub' ? `<button onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-xs font-extrabold">${T().backMenu}</button>` : `<span class="text-xs font-black text-purple-400">RHINO™</span>`}
            <span class="text-sm font-black text-white truncate max-w-[140px]">${titleText || T().heroTitle}</span>
          </div>
          <div class="flex items-center gap-1.5">
            ${isOwner && currentGame !== 'tower_admin' ? `
              <button onclick="nav('tower_admin')" class="btn-primary px-2.5 py-1 rounded-xl text-[11px] font-black text-amber-200">👑 پنل مدیریت</button>
            ` : ''}
            <button onclick="cycleLang()" class="glass-soft px-2.5 py-1 rounded-xl text-xs font-extrabold text-amber-300">
              🌐 ${langFlags[lang] || 'FA'}
            </button>
          </div>
        </div>
      `;
    }

    window.openChannelLink = function(url) {
      if (tg && tg.openTelegramLink && url.startsWith('https://t.me/')) tg.openTelegramLink(url);
      else window.open(url, '_blank');
    };

    window.verifyJoinAndRender = async function() {
      const root = document.getElementById('app');
      await loadUiAssets();
      if (!realTgUid || isOwner) { isJoinVerified = true; return render(); }
      try {
        const res = await fetch('/api/check_join/' + realTgUid);
        const data = await res.json();
        if (data && data.joined === false && data.channels?.length > 0) {
          isJoinVerified = false;
          const chBtns = data.channels.map(c => `<button onclick="openChannelLink('${c.url}')" class="btn-primary w-full py-3 rounded-xl font-bold">${c.title}</button>`).join('');
          root.innerHTML = `
            ${renderTopBar()}
            <div class="flex-1 flex flex-col justify-center p-4">
              <div class="glass-panel p-6 rounded-3xl text-center">
                <div class="text-3xl mb-2">🔒</div>
                <div class="flex flex-col gap-2.5 my-4">${chBtns}</div>
                <button onclick="verifyJoinAndRender()" class="btn-success w-full py-3.5 rounded-xl font-black">✅ OK</button>
              </div>
            </div>
          `;
          return;
        }
      } catch (e) {}
      isJoinVerified = true;
      render();
    };

    window.nav = function(g, skipLobbyGate = false) {
      if (hokmPollTimer) { clearInterval(hokmPollTimer); hokmPollTimer = null; }
      if (guessPollTimer) { clearInterval(guessPollTimer); guessPollTimer = null; }
      if (window.dtBattleTimer) { clearInterval(window.dtBattleTimer); window.dtBattleTimer = null; }
      currentGame = g;

      const lobbyGames = { hokm: 4, hokm2p: 2, dooz: 2, doz4p: 4, connect4: 2, rps: 2, memory: 2 };
      if (!skipLobbyGate && lobbyGames[g]) {
        lobbyState = {
          game: g,
          maxPlayers: lobbyGames[g],
          rpsTargetWins: 3,
          step: g === 'rps' ? 'rps_count' : 'options',
          inviteWarning: '',
          inviteSuccess: ''
        };
        currentGame = 'lobby_gate';
      }
      render();
    };

    window.setHubFilter = function(f) {
      hubFilter = f;
      renderHub(document.getElementById('app'));
    };

    /* ═══════════════════════════════════════════════════════════════════════════
       صفحه اصلی گیم باکس راینو با طراحی کازینو-آرکید نئونی (مشابه تصویر ارسالی)
       ═══════════════════════════════════════════════════════════════════════════ */
    function renderHub(root) {
      const G = T().games;
      const avatarUrl = myPhoto || '';
      const initial = (myName || 'R')[0].toUpperCase();

      const allCards = [
        { id: "demontower", title: G.wip3,     mode: "RPG",  tag: "NEW",  online: 14, cat: "pve", wip: false, c1: "#450a0a", c2: "#dc2626", icon: "👹" },
        { id: "hokm",       title: G.hokm,     mode: "PVP",  tag: "HOT",  online: 28, cat: "pvp", wip: false, c1: "#7f1d1d", c2: "#b91c1c", icon: "♠️" },
        { id: "hokm2p",     title: G.hokm2p,   mode: "PVP",  tag: "NEW",  online: 12, cat: "pvp", wip: false, c1: "#500724", c2: "#db2777", icon: "👑" },
        { id: "dooz",       title: G.dooz,     mode: "PVP",  tag: "NEW",  online: 9,  cat: "pvp", wip: false, c1: "#1e1b4b", c2: "#3b82f6", icon: "🟢" },
        { id: "doz4p",      title: G.doz4p,    mode: "PVP",  tag: "NEW",  online: 6,  cat: "pvp", wip: false, c1: "#4a044e", c2: "#ec4899", icon: "🟣" },
        { id: "connect4",   title: G.connect4, mode: "PVP",  tag: "HOT",  online: 11, cat: "pvp", wip: false, c1: "#064e3b", c2: "#10b981", icon: "🔴" },
        { id: "rps",        title: G.rps,      mode: "PVP",  tag: "NEW",  online: 7,  cat: "pvp", wip: false, c1: "#312e81", c2: "#6366f1", icon: "✂️" },
        { id: "guess",      title: G.guess,    mode: "PVE",  tag: "LIVE", online: 19, cat: "pvp", wip: false, c1: "#14532d", c2: "#22c55e", icon: "🎯" },
        { id: "2048",       title: G.g2048,    mode: "PVE",  tag: "NEW",  online: 15, cat: "pve", wip: false, c1: "#1e3a8a", c2: "#2563eb", icon: "🧩" },
        { id: "spuzzle",    title: G.spuzzle,  mode: "PVE",  tag: "",     online: 5,  cat: "pve", wip: false, c1: "#0c4a6e", c2: "#0ea5e9", icon: "🔢" },
        { id: "samegame",   title: G.samegame, mode: "PVE",  tag: "",     online: 8,  cat: "pve", wip: false, c1: "#581c87", c2: "#a855f7", icon: "🟦" },
        { id: "memory",     title: G.memory,   mode: "PVE",  tag: "NEW",  online: 10, cat: "pve", wip: false, c1: "#4c1d95", c2: "#8b5cf6", icon: "🧠" },
        { id: "typing",     title: G.typing,   mode: "PVE",  tag: "",     online: 4,  cat: "pve", wip: false, c1: "#78350f", c2: "#f59e0b", icon: "⌨️" },
        { id: "hangman",    title: G.hangman,  mode: "PVE",  tag: "",     online: 9,  cat: "pve", wip: false, c1: "#881337", c2: "#e11d48", icon: "🕵️" },
        { id: "wip1",       title: G.wip1,     mode: "SLOT", tag: T().wipBadge, online: 0, cat: "pve", wip: true, c1: "#1e1b4b", c2: "#6d28d9", icon: "🏰" },
        { id: "wip2",       title: G.wip2,     mode: "PVE",  tag: T().wipBadge, online: 0, cat: "pve", wip: true, c1: "#0f172a", c2: "#059669", icon: "🔐" }
      ];

      const filteredCards = allCards.filter(c => {
        if (hubFilter === 'pve') return c.cat === 'pve';
        if (hubFilter === 'pvp') return c.cat === 'pvp';
        return true;
      });

      const winsData = window.recentWinsList?.length ? window.recentWinsList : [
        { name: myName, game: "DEMON TOWER", time: "1m ago" },
        { name: "RHINO PRO", game: "HOKM 4P", time: "2m ago" },
        { name: "KING_88", game: "2048", time: "4m ago" }
      ];

      const bigWinsHtml = winsData.map((w, i) => `
        <div class="glass-panel rounded-2xl px-3 py-2 flex items-center gap-2.5 shrink-0 min-w-[165px] border border-purple-500/25">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center font-black text-xs shrink-0">
            ${(w.name || 'P')[0]}
          </div>
          <div class="leading-tight truncate">
            <div class="text-[11px] font-black text-amber-300 truncate">👑 ${w.name}</div>
            <div class="text-[9px] text-slate-400 font-bold">${w.game} • ${w.time}</div>
          </div>
          <span class="text-base ml-auto">${['🧸','🎰','🏆','💎'][i % 4]}</span>
        </div>
      `).join('');

      const cardsHtml = filteredCards.map(g => {
        const customImg = getAssetImg(g.id, '');
        return `
          <div onclick="${g.wip ? '' : `nav('${g.id}')`}" class="arcade-card cursor-pointer ${g.wip ? 'opacity-80' : ''}">
            <img src="${customImg}" onerror="this.style.display='none'" class="arcade-card-bg" />
            <div style="background: radial-gradient(circle at 75% 70%, ${g.c2}55 0%, ${g.c1}ee 85%);" class="absolute inset-0 -z-10 flex items-center justify-end p-3">
              <span class="text-7xl opacity-45 select-none">${g.icon}</span>
            </div>
            <div class="arcade-card-overlay">
              <div class="arcade-title">${g.title}</div>
              <div class="flex items-center gap-1.5 flex-wrap ltr-grid">
                <span class="pill-players">👤 ${g.online}</span>
                <span class="${g.mode === 'SLOT' ? 'pill-mode-slot' : 'pill-mode-pve'}">${g.mode}</span>
                ${g.tag ? `<span class="pill-new">${g.tag}</span>` : ''}
              </div>
            </div>
          </div>
        `;
      }).join('');

      const heroImgSrc = getAssetImg('rhino_hero', HERO_CUSTOM_IMG);

      root.innerHTML = `
        <!-- ۱. هدر پروفایل گیمینگ مشابه اسکرین‌شات -->
        <div class="glass-panel mx-3 mb-2 px-3 py-2.5 rounded-3xl flex items-center justify-between gap-2 shrink-0 border border-purple-500/25">
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            ${avatarUrl ? `
              <img src="${avatarUrl}" class="w-11 h-11 rounded-full object-cover border-2 border-purple-500 shrink-0" />
            ` : `
              <div class="w-11 h-11 rounded-full bg-gradient-to-br from-purple-600 to-indigo-800 flex items-center justify-center font-black text-base border-2 border-purple-400 shrink-0">${initial}</div>
            `}
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="font-black text-sm text-white truncate">${myName}</span>
                <span class="px-1.5 py-0.5 rounded-md bg-white/10 text-[10px] font-black text-purple-300">1 ^</span>
              </div>
              <div class="flex items-center gap-1.5 mt-1">
                <span class="text-[10px] font-black text-slate-300">1</span>
                <div class="flex-1 h-2 bg-slate-900/90 rounded-full overflow-hidden border border-white/10">
                  <div class="w-1/3 h-full bg-gradient-to-r from-purple-500 to-indigo-400 rounded-full"></div>
                </div>
                <span class="text-[10px] font-black text-slate-400">2</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <div class="flex flex-col gap-1 items-end">
              <div class="px-2.5 py-0.5 rounded-full bg-white text-slate-950 font-black text-[11px] flex items-center gap-1 shadow">
                <span>0</span><span>🪙</span>
              </div>
              <div class="px-2.5 py-0.5 rounded-full bg-slate-800/90 border border-white/15 text-white font-black text-[11px] flex items-center gap-1">
                <span>16</span><span>🎮</span>
              </div>
            </div>
            <button onclick="nav('demontower')" class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-xl font-black shadow-lg border border-purple-300/40">+</button>
            ${isOwner ? `
              <button onclick="nav('tower_admin')" title="پنل مدیریت" class="w-10 h-10 rounded-full glass-soft flex items-center justify-center text-base border border-amber-400/50">👑</button>
            ` : `
              <button onclick="cycleLang()" class="w-10 h-10 rounded-full glass-soft flex items-center justify-center text-xs font-black text-amber-300">${lang.toUpperCase()}</button>
            `}
          </div>
        </div>

        <!-- ۲. محتوای اسکرول‌شونده: نوار BIG WINS + بنر معرفی راینو + گرید ۲ ستونی کارت‌های مربعی -->
        <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col gap-3">
          <!-- نوار BIG WINS -->
          <div>
            <div class="flex items-center justify-between px-1 mb-1.5">
              <div class="flex items-center gap-1 text-[11px] font-black text-orange-400 tracking-wider uppercase">
                <span>🔥</span><span>${T().bigWins}</span>
              </div>
              ${isOwner ? `<button onclick="cycleLang()" class="text-[10px] font-black text-purple-300">🌐 ${lang.toUpperCase()}</button>` : ''}
            </div>
            <div class="flex gap-2 overflow-x-auto pb-1">${bigWinsHtml}</div>
          </div>

          <!-- کارت معرفی گیم باکس راینو (قابل تغییر از پنل ادمین) -->
          <div class="glass-panel rounded-3xl overflow-hidden shrink-0 border border-purple-500/25">
            <img src="${heroImgSrc}" onerror="this.style.display='none'" class="w-full h-32 object-cover border-b border-white/10" />
            <div class="p-3 text-center">
              <h1 class="text-base font-black text-amber-300 mb-0.5">${T().heroTitle}</h1>
              <p class="text-[11px] text-slate-200 font-bold leading-relaxed whitespace-pre-line">${T().heroBody}</p>
            </div>
          </div>

          <!-- گرید ۲ ستونی بازی‌ها با ظاهر مربعی پوستردار -->
          <div class="grid grid-cols-2 gap-3">
            ${cardsHtml}
          </div>
        </div>

        <!-- نوار ناوبری شناور پایین صفحه (اتاق‌های صوتی + بازی‌ها + فروشگاه + پروفایل) -->
        <div class="fixed bottom-3 left-3 right-3 z-30 bottom-dock px-3 py-2 flex justify-around items-center">
          <button onclick="nav('hub')" class="${currentGame==='hub' ? 'text-purple-400 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🎮</span><span>Games</span>
          </button>
          <button onclick="nav('voice_hub')" class="${currentGame==='voice_hub' ? 'text-amber-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🎙️</span><span>Rooms</span>
          </button>
          <button onclick="openMyVoiceRoomQuick()" class="w-12 h-10 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-xl shadow-[0_0_18px_rgba(168,85,247,0.75)] border border-purple-300/40">
            ➕
          </button>
          <button onclick="nav('sp_store')" class="${currentGame==='sp_store' ? 'text-emerald-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🛍️</span><span>Store</span>
          </button>
          <button onclick="nav('sp_profile')" class="${currentGame==='sp_profile' ? 'text-sky-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">👤</span><span>Profile</span>
          </button>
        </div>
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       مینی‌اپ مخفی «فرماندهی کل ربات و برج شیاطین» (۱۱ تب کامل شامل تغییر تمام عکس‌ها)
       ═══════════════════════════════════════════════════════════════════════════ */
    let admState = null;
    let admTab = 'ui_assets';
    let admMsg = '';
    let admErr = '';
    let admLookedUpUser = null;

    async function callTowerAdminApi(action = 'state', extra = {}) {
      try {
        const res = await fetch('/api/tower/admin', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ uid: Number(uid), action: action, ...extra })
        });
        const data = await res.json();
        admMsg = data.msg || '';
        admErr = data.ok === false ? (data.error || '') : '';
        if (data.looked_up) admLookedUpUser = data.looked_up;
        if (data.admin_data) {
          admState = data.admin_data;
          if (admState.ui_assets) {
            window.uiAssetsMap = admState.ui_assets;
            applyDynamicCssBackgrounds();
          }
        }
        drawTowerAdminApp(document.getElementById('app'));
      } catch (e) {}
    }

    window.admSwitchTab = function(t) {
      admTab = t; admMsg = ''; admErr = '';
      drawTowerAdminApp(document.getElementById('app'));
    };

    window.admSaveUiAsset = function(assetKey) {
      const dataUrl = window.uploadedImages['asset_' + assetKey];
      if (!dataUrl) {
        if (tg?.showAlert) tg.showAlert('ابتدا یک تصویر از گالری انتخاب کنید!');
        return;
      }
      callTowerAdminApi('save_ui_asset', { asset_key: assetKey, photo: dataUrl });
    };

    window.admDeleteUiAsset = function(assetKey) {
      callTowerAdminApi('delete_ui_asset', { asset_key: assetKey });
    };

    window.admFillFloorForm = function(fnum) {
      const f = (admState?.floors || []).find(x => x.floor_num === fnum);
      if (!f) return;
      document.getElementById('af_num').value = f.floor_num;
      document.getElementById('af_name').value = f.boss_name || '';
      document.getElementById('af_desc').value = f.description || '';
      document.getElementById('af_power').value = f.power_desc || '';
      document.getElementById('af_weak').value = f.weakness || '';
      document.getElementById('af_hp').value = f.hp || 100;
      document.getElementById('af_atk').value = f.atk || 20;
      document.getElementById('af_def').value = f.def || 10;
      document.getElementById('af_coins').value = f.reward_coins || 100;
      document.getElementById('af_xp').value = f.reward_xp || 50;
      document.getElementById('af_drop').value = f.drop_item || '';
      document.getElementById('af_dprice').value = f.drop_price || 50;
      if (f.photo) {
        window.uploadedImages['floor_photo'] = f.photo;
        const pImg = document.getElementById('prev_floor_photo');
        if (pImg) { pImg.src = f.photo; pImg.classList.remove('hidden'); }
      }
    };

    window.admSubmitFloor = function() {
      callTowerAdminApi('save_floor', {
        floor_num: Number(document.getElementById('af_num').value || 1),
        boss_name: document.getElementById('af_name').value,
        photo: window.uploadedImages['floor_photo'] || '',
        description: document.getElementById('af_desc').value,
        power_desc: document.getElementById('af_power').value,
        weakness: document.getElementById('af_weak').value,
        hp: Number(document.getElementById('af_hp').value || 100),
        atk: Number(document.getElementById('af_atk').value || 20),
        def_val: Number(document.getElementById('af_def').value || 10),
        reward_coins: Number(document.getElementById('af_coins').value || 100),
        reward_xp: Number(document.getElementById('af_xp').value || 50),
        drop_item: document.getElementById('af_drop').value,
        drop_price: Number(document.getElementById('af_dprice').value || 50)
      });
    };

    window.admSubmitItem = function() {
      callTowerAdminApi('save_item', {
        item_type: document.getElementById('ai_type').value,
        name: document.getElementById('ai_name').value,
        photo: window.uploadedImages['item_photo'] || '',
        price: Number(document.getElementById('ai_price').value || 0),
        hp_bonus: Number(document.getElementById('ai_hp').value || 0),
        atk_bonus: Number(document.getElementById('ai_atk').value || 0),
        def_bonus: Number(document.getElementById('ai_def').value || 0),
        spd_bonus: Number(document.getElementById('ai_spd').value || 0)
      });
    };

    window.admSubmitChars = function() {
      callTowerAdminApi('save_gender_imgs', {
        male_img: window.uploadedImages['male_photo'] || '',
        female_img: window.uploadedImages['female_photo'] || ''
      });
    };

    window.admSubmitGift = function() {
      callTowerAdminApi('save_gift', {
        code: document.getElementById('ag_code').value,
        coins: Number(document.getElementById('ag_coins').value || 0),
        xp: Number(document.getElementById('ag_xp').value || 0),
        max_uses: Number(document.getElementById('ag_uses').value || 1)
      });
    };

    window.admSubmitPopup = function(clear = false) {
      if (clear) return callTowerAdminApi('save_popup', { clear: true });
      callTowerAdminApi('save_popup', {
        text: document.getElementById('ap_text').value,
        photo: window.uploadedImages['popup_photo'] || '',
        btn_text: document.getElementById('ap_btxt').value,
        btn_url: document.getElementById('ap_burl').value,
        hours: Number(document.getElementById('ap_hrs').value || 24)
      });
    };

    window.admDecideVoucher = function(vid, dec) {
      const noteEl = document.getElementById('vnote_' + vid);
      callTowerAdminApi('decide_voucher', {
        voucher_id: vid,
        decision: dec,
        note: noteEl ? noteEl.value : ''
      });
    };

    function startTowerAdminApp(root) {
      if (!isOwner) {
        root.innerHTML = `<div class="p-8 text-center"><div class="glass-panel p-6 rounded-3xl text-rose-400 font-black">⛔ دسترسی غیرمجاز (فقط مالک ربات)</div></div>`;
        return;
      }
      root.innerHTML = `<div class="p-6 text-center"><div class="glass-panel p-6 rounded-3xl font-bold">در حال بارگذاری پنل فرماندهی کل ربات...</div></div>`;
      callTowerAdminApi('state');
    }

    function drawTowerAdminApp(root) {
      if (!root || currentGame !== 'tower_admin') return;
      if (!isOwner) {
        root.innerHTML = `<div class="p-8 text-center"><div class="glass-panel p-6 rounded-3xl text-rose-400 font-black">⛔ دسترسی غیرمجاز</div></div>`;
        return;
      }
      if (!admState) return;

      const tabs = [
        { id: 'ui_assets',    lbl: '🖼️ عکس بازی‌ها' },
        { id: 'bot_stats',    lbl: '📊 آمار و همگانی' },
        { id: 'bot_channels', lbl: '🔒 قفل کانال' },
        { id: 'bot_groups',   lbl: '👥 گروه‌ها' },
        { id: 'users',        lbl: '👤 کاربران و بن' },
        { id: 'floors',       lbl: '👹 طبقات برج' },
        { id: 'items',        lbl: '⚔️ سلاح و زره' },
        { id: 'chars',        lbl: '🚻 عکس کاراکتر' },
        { id: 'vouchers',     lbl: '🎟️ ووچرها' },
        { id: 'gifts',        lbl: '🎁 کد هدیه' },
        { id: 'popup',        lbl: '📢 پاپ‌آپ' }
      ];
      const tabsHtml = tabs.map(t => `
        <button onclick="admSwitchTab('${t.id}')" class="px-3 py-2 rounded-xl text-xs font-black shrink-0 ${admTab === t.id ? 'btn-primary text-white' : 'glass-soft text-slate-300'}">
          ${t.lbl}
        </button>
      `).join('');

      let sectionHtml = '';

      /* تب ۰: تغییر و آپلود مستقیم تمام عکس‌های بازی‌ها و بک‌گراندهای مینی‌اپ */
      if (admTab === 'ui_assets') {
        const assetItems = [
          { key: 'rhino_hero',  title: '🦏 بنر کارت معرفی گیم باکس راینو' },
          { key: 'menu_bg',     title: '🌌 پس‌زمینه کل مینی‌اپ (Menu BG)' },
          { key: 'hokm_carpet', title: '🟥 طرح فرش میز حکم (Hokm Carpet)' },
          { key: 'tower_hero',  title: '👹 بنر بالای منوی برج شیاطین' },
          { key: 'tower_bg',    title: '🌋 پس‌زمینه صفحات برج شیاطین' },
          { key: 'demontower',  title: '🃏 پوستر کارت بازی: برج شیاطین' },
          { key: 'hokm',        title: '🃏 پوستر کارت بازی: حکم ۴ نفره' },
          { key: 'hokm2p',      title: '🃏 پوستر کارت بازی: حکم ۲ نفره' },
          { key: 'dooz',        title: '🃏 پوستر کارت بازی: دوز ۲ نفره' },
          { key: 'doz4p',       title: '🃏 پوستر کارت بازی: دوز ۴ نفره' },
          { key: 'connect4',    title: '🃏 پوستر کارت بازی: چهار در ردیف' },
          { key: 'rps',         title: '🃏 پوستر کارت بازی: سنگ کاغذ قیچی' },
          { key: 'guess',       title: '🃏 پوستر کارت بازی: حدس عدد' },
          { key: '2048',        title: '🃏 پوستر کارت بازی: پازل ۲۰۴۸' },
          { key: 'spuzzle',     title: '🃏 پوستر کارت بازی: پازل ۱۵' },
          { key: 'samegame',    title: '🃏 پوستر کارت بازی: جفت‌های رنگی' },
          { key: 'memory',      title: '🃏 پوستر کارت بازی: حافظه' },
          { key: 'typing',      title: '🃏 پوستر کارت بازی: تایپ سرعتی' },
          { key: 'hangman',     title: '🃏 پوستر کارت بازی: حدس کلمه' },
          { key: 'wip1',        title: '🃏 پوستر کارت بازی: شکارچی سیاه‌چال' },
          { key: 'wip2',        title: '🃏 پوستر کارت بازی: هک گاوصندوق' }
        ];

        const savedMap = admState.ui_assets || {};
        const cardsListHtml = assetItems.map(item => {
          const curImg = savedMap[item.key] || `/api/custom_bg/${item.key}`;
          const hasCustom = Boolean(savedMap[item.key]);
          return `
            <div class="glass-soft p-3 rounded-2xl flex flex-col gap-2 border ${hasCustom ? 'border-emerald-400/50' : 'border-white/10'}">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2.5 min-w-0">
                  <img id="prev_asset_${item.key}" src="${curImg}" class="w-14 h-14 rounded-xl object-cover border border-purple-400/40 shrink-0" />
                  <div class="min-w-0">
                    <div class="font-black text-xs text-white truncate">${item.title}</div>
                    <div class="text-[10px] ${hasCustom ? 'text-emerald-300' : 'text-slate-400'} font-bold">
                      ${hasCustom ? '✅ عکس سفارشی فعال است' : '⚪ تصویر پیش‌فرض'}
                    </div>
                  </div>
                </div>
                ${hasCustom ? `
                  <button onclick="admDeleteUiAsset('${item.key}')" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold shrink-0">حذف</button>
                ` : ''}
              </div>
              <div class="flex items-center gap-2 pt-1 border-t border-white/10">
                <input type="file" accept="image/*" onchange="handleImageUpload(this, 'asset_${item.key}', 'prev_asset_${item.key}')" class="flex-1 text-[10px] text-slate-300" />
                <button onclick="admSaveUiAsset('${item.key}')" class="btn-success px-3.5 py-1.5 rounded-xl text-[11px] font-black shrink-0">💾 ذخیره</button>
              </div>
            </div>
          `;
        }).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">🖼️ مدیریت و تغییر تمام عکس‌های مینی‌اپ</h3>
            <p class="text-[11px] text-slate-300 text-center">برای هر بازی یا پس‌زمینه، عکس دلخواهتان را از گالری انتخاب و روی «ذخیره» بزنید تا بلافاصله در کل مینی‌اپ تغییر کند:</p>
            <div class="flex flex-col gap-2.5">${cardsListHtml}</div>
          </div>
        `;
      }

      /* ۰-الف. تب آمار کل ربات و ارسال همگانی هیبریدی */
      else if (admTab === 'bot_stats') {
        const st = admState.bot_stats || {};
        const draft = admState.bc_draft || null;

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">📊 آمار زنده کل ربات راینو</h3>
            <div class="grid grid-cols-2 gap-2 text-center font-extrabold">
              <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">کل کاربران</div><div class="text-lg text-emerald-300">${st.users || 0}</div></div>
              <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">کل گروه‌ها</div><div class="text-lg text-sky-300">${st.groups || 0}</div></div>
              <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">بازیکنان برج</div><div class="text-lg text-amber-300">${admState.players_count || 0}</div></div>
              <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">مجموع استارز</div><div class="text-lg text-purple-300">⭐ ${st.stars || 0}</div></div>
            </div>

            <div class="border-t border-white/10 pt-3 space-y-2.5">
              <h4 class="font-black text-sm text-indigo-300 text-center">📢 ارسال پیام همگانی (با حفظ ایموجی پریمیوم)</h4>

              <div class="glass-soft p-3 rounded-2xl text-center space-y-2 border ${draft ? 'border-emerald-400/50' : 'border-amber-400/40'}">
                ${draft ? `
                  <div class="text-emerald-300 font-black text-xs">✅ پیام همگانی شما در پیوی دریافت و آماده ارسال است!</div>
                  <div class="p-2 rounded-xl bg-black/40 text-slate-200 text-[11px] truncate">«${draft.preview}» (ثبت در ${draft.saved_at})</div>
                  <div class="grid grid-cols-2 gap-2 pt-1">
                    <button onclick="callTowerAdminApi('bot_arm_bc_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary py-2 rounded-xl font-bold text-[11px]">🔄 تغییر پیام در پیوی</button>
                    <button onclick="callTowerAdminApi('bot_clear_bc_draft')" class="btn-danger py-2 rounded-xl font-bold text-[11px]">🗑️ پاک کردن پیام</button>
                  </div>
                ` : `
                  <div class="text-amber-200 font-bold text-[11px]">هنوز پیامی برای ارسال همگانی ثبت نشده است:</div>
                  <button onclick="callTowerAdminApi('bot_arm_bc_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary w-full py-3.5 rounded-2xl font-black text-xs border border-amber-400/50">
                    📝 ثبت پیام همگانی در پیوی ربات (با ایموجی پریمیوم)
                  </button>
                `}
              </div>

              <div class="space-y-2 pt-1">
                <label class="block text-[11px] text-slate-300 font-bold">۱. انتخاب مقصد ارسال:</label>
                <select id="bc_target" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
                  <option value="users">👤 ارسال به تمام کاربران (پیوی)</option>
                  <option value="groups">👥 ارسال به تمام گروه‌ها</option>
                </select>

                <label class="block text-[11px] text-slate-300 font-bold">۲. دکمه شیشه‌ای زیر پیام (اختیاری):</label>
                <div class="grid grid-cols-2 gap-2">
                  <input id="bc_btxt" type="text" placeholder="متن دکمه شیشه‌ای" class="p-2.5 rounded-xl glass-soft text-white text-center" />
                  <input id="bc_burl" type="text" placeholder="لینک (https://...)" class="p-2.5 rounded-xl glass-soft text-white text-center" />
                </div>

                <button onclick="callTowerAdminApi('bot_broadcast',{target_type:document.getElementById('bc_target').value,btn_text:document.getElementById('bc_btxt').value,btn_url:document.getElementById('bc_burl').value})" ${!draft ? 'disabled' : ''} class="${draft ? 'btn-success' : 'bg-slate-800 opacity-50'} w-full py-4 rounded-2xl font-black text-sm mt-2">
                  🚀 شروع ارسال همگانی نهایی
                </button>
              </div>
            </div>
          </div>
        `;
      }

      /* ۰-ب. تب مدیریت کانال‌های عضویت اجباری */
      else if (admTab === 'bot_channels') {
        const chRows = (admState.forced_channels || []).map(c => `
          <div class="glass-soft p-3 rounded-2xl flex justify-between items-center text-xs">
            <div>
              <div class="font-black text-amber-300">${c.title || c.chat_id}</div>
              <div class="text-[10px] text-slate-300">ID: ${c.chat_id} ${c.username ? '(@'+c.username+')' : ''}</div>
            </div>
            <button onclick="callTowerAdminApi('bot_del_channel',{chat_id:'${c.chat_id}'})" class="btn-danger px-3 py-1.5 rounded-xl text-[10px] font-black">حذف</button>
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">🔒 افزودن کانال به قفل عضویت اجباری</h3>
            <div>
              <label class="block text-[11px] text-slate-300 mb-1">یوزرنیم کانال (با @) یا آیدی عددی (-100...):</label>
              <input id="fc_cid" type="text" placeholder="مثلاً: @RHINOBOT_TM" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">عنوان نمایشی دکمه:</label>
                <input id="fc_title" type="text" placeholder="کانال رسمی راینو" class="w-full p-2.5 rounded-xl glass-soft text-center text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">یوزرنیم بدون @ (جهت لینک):</label>
                <input id="fc_uname" type="text" placeholder="RHINOBOT_TM" class="w-full p-2.5 rounded-xl glass-soft text-center text-white" />
              </div>
            </div>
            <button onclick="callTowerAdminApi('bot_add_channel',{chat_id:document.getElementById('fc_cid').value,title:document.getElementById('fc_title').value,username:document.getElementById('fc_uname').value})" class="btn-success w-full py-3.5 rounded-2xl font-black text-sm">
              ➕ افزودن کانال به قفل اجباری
            </button>
          </div>

          <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3">
            <h4 class="text-xs font-black text-indigo-300 text-center">لیست کانال‌های عضویت اجباری فعال</h4>
            <div class="flex flex-col gap-2">${chRows || '<div class="text-center text-xs text-slate-400">هیچ کانالی ثبت نشده است.</div>'}</div>
          </div>
        `;
      }

      /* ۰-ج. تب لیست گروه‌ها */
      else if (admTab === 'bot_groups') {
        const gRows = (admState.groups_list || []).map(g => `
          <div class="glass-soft p-3 rounded-2xl flex justify-between items-center gap-2 text-xs">
            <div class="truncate">
              <div class="font-black text-white truncate">${g.title || 'Group'}</div>
              <div class="text-[10px] text-slate-400 font-mono">${g.chat_id}</div>
            </div>
            <div class="flex gap-1 shrink-0">
              <button onclick="callTowerAdminApi('bot_group_link',{chat_id:${g.chat_id}})" class="btn-primary px-2.5 py-1.5 rounded-xl text-[10px] font-bold">🔗 لینک</button>
              <button onclick="callTowerAdminApi('bot_leave_group',{chat_id:${g.chat_id}})" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold">🚪 خروج</button>
            </div>
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5">
            <h3 class="font-black text-sm text-amber-300 text-center">👥 لیست گروه‌های فعال ربات (${(admState.groups_list || []).length})</h3>
            <div class="flex flex-col gap-2">${gRows || '<div class="text-center text-xs text-slate-400">گروهی ثبت نشده است.</div>'}</div>
          </div>
        `;
      }

      /* ۱. تب طبقات و غول‌ها */
      else if (admTab === 'floors') {
        const fList = (admState.floors || []).map(f => `
          <div class="glass-soft p-2.5 rounded-2xl flex items-center justify-between gap-2 text-xs">
            <div class="flex items-center gap-2">
              ${f.photo ? `<img src="${f.photo}" class="w-10 h-10 rounded-xl object-cover" />` : `<div class="w-10 h-10 rounded-xl bg-rose-900/50 flex items-center justify-center">👹</div>`}
              <div>
                <div class="font-black text-amber-300">طبقه ${f.floor_num}: ${f.boss_name}</div>
                <div class="text-[10px] text-slate-300">❤️${f.hp} | ⚔️${f.atk} | 🛡️${f.def} | 🪙${f.reward_coins}</div>
              </div>
            </div>
            <div class="flex gap-1">
              <button onclick="admFillFloorForm(${f.floor_num})" class="btn-primary px-2.5 py-1.5 rounded-xl text-[10px] font-bold">ویرایش</button>
              <button onclick="callTowerAdminApi('delete_floor',{floor_num:${f.floor_num}})" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold">حذف</button>
            </div>
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center mb-1">👹 افزودن / ویرایش طبقه و غول (خانه‌به‌خانه)</h3>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">شماره طبقه:</label>
                <input id="af_num" type="number" value="${(admState.floors?.length || 0) + 1}" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">نام غول:</label>
                <input id="af_name" type="text" placeholder="مثلاً: اژدهای خاکستر" class="w-full p-2.5 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
            </div>

            <div class="glass-soft p-3 rounded-2xl text-center">
              <label class="block text-[11px] text-amber-200 font-bold mb-2">📷 عکس غول (آپلود مستقیم از گالری):</label>
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'floor_photo', 'prev_floor_photo')" class="w-full text-[11px] text-slate-300" />
              <img id="prev_floor_photo" class="hidden w-28 h-28 object-cover rounded-2xl mx-auto mt-2 border border-amber-400" />
            </div>

            <div>
              <label class="block text-[11px] text-slate-300 mb-1">توضیح کوتاه مرحله:</label>
              <input id="af_desc" type="text" placeholder="توضیح داستان یا ویژگی غول..." class="w-full p-2.5 rounded-xl glass-soft text-white" />
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">🔥 قدرت ویژه غول:</label>
                <input id="af_power" type="text" placeholder="مثلاً: نفس آتشین" class="w-full p-2.5 rounded-xl glass-soft text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">⚡ نقطه ضعف غول:</label>
                <input id="af_weak" type="text" placeholder="مثلاً: شمشیر یخی" class="w-full p-2.5 rounded-xl glass-soft text-white" />
              </div>
            </div>

            <div class="grid grid-cols-3 gap-2">
              <div>
                <label class="block text-[11px] text-rose-300 mb-1">❤️ جان (HP):</label>
                <input id="af_hp" type="number" value="250" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-amber-300 mb-1">⚔️ حمله (ATK):</label>
                <input id="af_atk" type="number" value="35" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-sky-300 mb-1">🛡️ دفاع (DEF):</label>
                <input id="af_def" type="number" value="15" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-amber-300 mb-1">🪙 پاداش سکه:</label>
                <input id="af_coins" type="number" value="300" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-purple-300 mb-1">⭐ پاداش XP:</label>
                <input id="af_xp" type="number" value="100" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-emerald-300 mb-1">🎁 نام غنیمت افتاده:</label>
                <input id="af_drop" type="text" placeholder="مثلاً: یاقوت سرخ" class="w-full p-2 rounded-xl glass-soft text-center text-white" />
              </div>
              <div>
                <label class="block text-[11px] text-emerald-300 mb-1">💰 قیمت فروش غنیمت:</label>
                <input id="af_dprice" type="number" value="80" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" />
              </div>
            </div>

            <button onclick="admSubmitFloor()" class="btn-success w-full py-3.5 rounded-2xl font-black text-sm mt-2">💾 ذخیره طبقه و غول</button>
          </div>

          <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3">
            <h4 class="text-xs font-black text-indigo-300 text-center">لیست طبقات فعلی برج (${(admState.floors || []).length} طبقه)</h4>
            <div class="flex flex-col gap-2">${fList}</div>
          </div>
        `;
      }

      /* ۲. تب سلاح‌ها و زره‌ها */
      else if (admTab === 'items') {
        const iList = (admState.items || []).map(it => `
          <div class="glass-soft p-2.5 rounded-2xl flex items-center justify-between gap-2 text-xs">
            <div class="flex items-center gap-2">
              ${it.photo ? `<img src="${it.photo}" class="w-10 h-10 rounded-xl object-cover" />` : `<div class="w-10 h-10 rounded-xl glass-panel flex items-center justify-center">${it.item_type==='weapon'?'⚔️':'🛡️'}</div>`}
              <div>
                <div class="font-black text-white">${it.name} (${it.price} 🪙)</div>
                <div class="text-[10px] text-emerald-300">+HP:${it.hp_bonus} | +ATK:${it.atk_bonus} | +DEF:${it.def_bonus} | SPD:${it.spd_bonus}</div>
              </div>
            </div>
            <button onclick="callTowerAdminApi('delete_item',{item_id:${it.id}})" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold">حذف</button>
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">⚔️ افزودن سلاح یا زره جدید</h3>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">نوع آیتم:</label>
                <select id="ai_type" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold">
                  <option value="weapon">⚔️ سلاح (Weapon)</option>
                  <option value="armor">🛡️ زره (Armor)</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">نام سلاح / زره:</label>
                <input id="ai_name" type="text" placeholder="مثلاً: شمشیر اژدها" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold" />
              </div>
            </div>

            <div class="glass-soft p-3 rounded-2xl text-center">
              <label class="block text-[11px] text-amber-200 font-bold mb-2">📷 عکس سلاح یا زره (آپلود مستقیم از گالری):</label>
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'item_photo', 'prev_item_photo')" class="w-full text-[11px] text-slate-300" />
              <img id="prev_item_photo" class="hidden w-24 h-24 object-cover rounded-2xl mx-auto mt-2 border border-amber-400" />
            </div>

            <div>
              <label class="block text-[11px] text-amber-300 mb-1">🪙 قیمت خرید (۰ = رایگان):</label>
              <input id="ai_price" type="number" value="1000" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div><label class="block text-[11px] text-rose-300 mb-1">❤️ +HP:</label><input id="ai_hp" type="number" value="40" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
              <div><label class="block text-[11px] text-amber-300 mb-1">⚔️ +ATK:</label><input id="ai_atk" type="number" value="50" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
              <div><label class="block text-[11px] text-sky-300 mb-1">🛡️ +DEF:</label><input id="ai_def" type="number" value="20" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
              <div><label class="block text-[11px] text-emerald-300 mb-1">⚡ +SPD:</label><input id="ai_spd" type="number" value="5" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
            </div>

            <button onclick="admSubmitItem()" class="btn-success w-full py-3.5 rounded-2xl font-black text-sm">➕ افزودن به لیست تجهیزات برج</button>
          </div>

          <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3">
            <h4 class="text-xs font-black text-indigo-300 text-center">لیست سلاح‌ها و زره‌های موجود</h4>
            <div class="flex flex-col gap-2">${iList}</div>
          </div>
        `;
      }

      /* ۳. تب عکس کاراکتر مرد و زن */
      else if (admTab === 'chars') {
        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-4 text-xs text-center">
            <h3 class="font-black text-sm text-amber-300">🚻 آپلود مستقیم تصاویر کاراکتر مرد و زن</h3>
            <div class="glass-soft p-3.5 rounded-2xl">
              <div class="font-black text-sky-300 mb-2">🚹 تصویر کاراکتر مرد</div>
              ${admState.male_img ? `<img src="${admState.male_img}" class="w-28 h-32 object-cover rounded-xl mx-auto mb-2 border border-sky-400" />` : ''}
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'male_photo', 'prev_male_photo')" class="w-full text-[11px]" />
              <img id="prev_male_photo" class="hidden w-28 h-32 object-cover rounded-xl mx-auto mt-2 border-2 border-emerald-400" />
            </div>
            <div class="glass-soft p-3.5 rounded-2xl">
              <div class="font-black text-pink-300 mb-2">🚺 تصویر کاراکتر زن</div>
              ${admState.female_img ? `<img src="${admState.female_img}" class="w-28 h-32 object-cover rounded-xl mx-auto mb-2 border border-pink-400" />` : ''}
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'female_photo', 'prev_female_photo')" class="w-full text-[11px]" />
              <img id="prev_female_photo" class="hidden w-28 h-32 object-cover rounded-xl mx-auto mt-2 border-2 border-emerald-400" />
            </div>
            <button onclick="admSubmitChars()" class="btn-success w-full py-3.5 rounded-2xl font-black text-sm">💾 ذخیره تصاویر کاراکترها</button>
          </div>
        `;
      }

      /* ۴. تب مدیریت درخواست‌های ووچر */
      else if (admTab === 'vouchers') {
        const vRows = (admState.vouchers || []).map(v => `
          <div class="glass-soft p-3 rounded-2xl text-xs space-y-2 border border-white/10">
            <div class="flex justify-between items-center">
              <span class="font-black text-amber-300">#${v.id} — ${v.user_name} (${v.user_id})</span>
              <span class="px-2 py-0.5 rounded-lg bg-indigo-600/50 font-bold">${v.voucher_type}</span>
            </div>
            <div class="flex justify-between text-[11px]">
              <span>سکه پیشنهادی: <b class="text-emerald-300">${v.coins_offered.toLocaleString()} 🪙</b></span>
              <span>وضعیت: <b>${v.status}</b></span>
            </div>
            ${v.status === 'pending' ? `
              <input id="vnote_${v.id}" type="text" placeholder="یادداشت شما برای این کاربر (اختیاری)..." class="w-full p-2 rounded-xl bg-slate-900 border border-white/20 text-white text-xs" />
              <div class="grid grid-cols-2 gap-2">
                <button onclick="admDecideVoucher(${v.id}, 'approved')" class="btn-success py-2 rounded-xl font-black">✅ تایید و ارسال کد</button>
                <button onclick="admDecideVoucher(${v.id}, 'rejected')" class="btn-danger py-2 rounded-xl font-black">❌ رد و عودت سکه</button>
              </div>
            ` : `
              ${v.voucher_code ? `<div class="text-emerald-300 font-bold">کد صادرشده: ${v.voucher_code}</div>` : ''}
              ${v.owner_note ? `<div class="text-slate-300">یادداشت: ${v.owner_note}</div>` : ''}
            `}
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5">
            <h3 class="font-black text-sm text-amber-300 text-center">🎟️ مدیریت درخواست‌های ووچر بازیکنان</h3>
            <div class="flex flex-col gap-2.5">${vRows || '<div class="text-center text-xs text-slate-400">درخواستی ثبت نشده است.</div>'}</div>
          </div>
        `;
      }

      /* ۵. تب ساخت کد هدیه */
      else if (admTab === 'gifts') {
        const gRows = (admState.gifts || []).map(g => {
          const usedCnt = JSON.parse(g.used_by || '[]').length;
          return `
            <div class="glass-soft p-2.5 rounded-2xl flex justify-between items-center text-xs">
              <div>
                <div class="font-black text-amber-300">${g.code}</div>
                <div class="text-[10px] text-slate-300">+${g.coins} 🪙 | +${g.xp} XP | مصرف: ${usedCnt}/${g.max_uses}</div>
              </div>
              <button onclick="callTowerAdminApi('delete_gift',{code:'${g.code}'})" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold">حذف</button>
            </div>
          `;
        }).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">🎁 ساخت کد هدیه جدید</h3>
            <div>
              <label class="block text-[11px] text-slate-300 mb-1">کد هدیه:</label>
              <input id="ag_code" type="text" placeholder="مثلاً: RHINO2026" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
            </div>
            <div class="grid grid-cols-3 gap-2">
              <div><label class="block text-[11px] text-amber-300 mb-1">سکه:</label><input id="ag_coins" type="number" value="2000" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
              <div><label class="block text-[11px] text-purple-300 mb-1">XP:</label><input id="ag_xp" type="number" value="300" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
              <div><label class="block text-[11px] text-emerald-300 mb-1">ظرفیت:</label><input id="ag_uses" type="number" value="50" class="w-full p-2 rounded-xl glass-soft text-center font-bold text-white" /></div>
            </div>
            <button onclick="admSubmitGift()" class="btn-success w-full py-3.5 rounded-2xl font-black text-sm">➕ ثبت کد هدیه</button>
          </div>
          <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3">
            <h4 class="text-xs font-black text-indigo-300 text-center">کدهای هدیه فعال</h4>
            <div class="flex flex-col gap-2">${gRows}</div>
          </div>
        `;
      }

      /* ۶. تب ساخت پاپ‌آپ تبلیغاتی شناور */
      else if (admTab === 'popup') {
        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">📢 تنظیم پاپ‌آپ تبلیغاتی شناور</h3>
            <textarea id="ap_text" rows="3" placeholder="متن تبلیغ یا اطلاعیه..." class="w-full p-2.5 rounded-xl glass-soft text-white"></textarea>
            <div class="glass-soft p-3 rounded-2xl text-center">
              <label class="block text-[11px] text-amber-200 font-bold mb-1">📷 عکس پاپ‌آپ (آپلود مستقیم از گالری):</label>
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'popup_photo', 'prev_popup_photo')" class="w-full text-[11px]" />
              <img id="prev_popup_photo" class="hidden w-32 h-24 object-cover rounded-xl mx-auto mt-2 border border-amber-400" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <input id="ap_btxt" type="text" placeholder="متن دکمه (اختیاری)" class="w-full p-2 rounded-xl glass-soft text-white" />
              <input id="ap_burl" type="text" placeholder="لینک دکمه (https://...)" class="w-full p-2 rounded-xl glass-soft text-white" />
            </div>
            <div>
              <label class="block text-[11px] text-amber-300 mb-1">⏳ مدت نمایش شناور (ساعت):</label>
              <input id="ap_hrs" type="number" value="24" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
            </div>
            <div class="grid grid-cols-2 gap-2 pt-2">
              <button onclick="admSubmitPopup(false)" class="btn-success py-3 rounded-2xl font-black">✅ فعال‌سازی</button>
              <button onclick="admSubmitPopup(true)" class="btn-danger py-3 rounded-2xl font-black">🗑️ حذف پاپ‌آپ</button>
            </div>
          </div>
        `;
      }

      /* ۷. تب مدیریت کاربران + لیست کامل تمام کاربران با مشخصات کامل */
      else if (admTab === 'users') {
        const u = admLookedUpUser;
        const allUsers = admState.users_list || [];
        const usersRowsHtml = allUsers.map((usr, idx) => `
          <div onclick="callTowerAdminApi('Lookup_user',{target_uid:${usr.user_id}})" class="glass-soft p-3 rounded-2xl flex items-center justify-between gap-2 text-xs cursor-pointer hover:border-amber-400/50 transition">
            <div class="text-right space-y-0.5 min-w-0">
              <div class="font-black text-white truncate">
                ${idx + 1}. ${usr.first_name || 'بدون نام'}
                ${usr.username ? `<span class="text-sky-300 font-normal">(@${usr.username})</span>` : ''}
                ${usr.is_bot_admin ? '<span class="text-amber-300">👑</span>' : ''}
              </div>
              <div class="text-[10px] text-slate-300 font-mono">
                ID: ${usr.user_id} | 🌐 ${usr.language || 'fa'} | ⭐ Lvl ${usr.dt_level} | 🏰 طبقه ${usr.dt_floor} | 🪙 ${Number(usr.dt_coins || 0).toLocaleString()}
              </div>
              <div class="text-[10px]">
                ${usr.global_banned ? '<span class="text-rose-400 font-bold">⛔ بن از ربات</span> ' : '<span class="text-emerald-400">🟢 فعال</span> '}
                ${usr.dt_banned ? '<span class="text-rose-400 font-bold">| 🚫 بن از برج</span>' : ''}
              </div>
            </div>
            <button class="btn-primary px-2.5 py-1.5 rounded-xl text-[10px] font-black shrink-0">مدیریت ◀</button>
          </div>
        `).join('');

        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
            <div class="flex justify-between items-center glass-soft p-3 rounded-2xl">
              <span class="font-black">وضعیت کلی بازی برج شیاطین:</span>
              <button onclick="callTowerAdminApi('toggle_dev')" class="${admState.dev_mode ? 'btn-danger' : 'btn-success'} px-3 py-1.5 rounded-xl font-black">
                ${admState.dev_mode ? '🛠️ در حال توسعه (فقط مالک)' : '🟢 باز برای همه'}
              </button>
            </div>

            <h3 class="font-black text-sm text-amber-300 text-center pt-1">🔍 جستجو، شارژ و مدیریت کاربر</h3>
            <div class="flex gap-2">
              <input id="au_uid" type="number" value="${u ? u.user_id : ''}" placeholder="آیدی عددی کاربر..." class="flex-1 p-2.5 rounded-xl glass-soft text-center font-black text-white" />
              <button onclick="callTowerAdminApi('Lookup_user',{target_uid:Number(document.getElementById('au_uid').value)})" class="btn-primary px-4 rounded-xl font-black">جستجو</button>
            </div>

            ${u ? `
              <div class="glass-soft p-3 rounded-2xl space-y-1.5 border-2 border-amber-400">
                <div class="flex justify-between"><span>نام و یوزرنیم:</span><b>${u.first_name || '—'} ${u.username ? '(@'+u.username+')' : ''}</b></div>
                <div class="flex justify-between"><span>آیدی عددی:</span><b class="font-mono text-amber-200">${u.user_id}</b></div>
                <div class="flex justify-between"><span>کاراکتر / لول برج:</span><b class="text-purple-300">${u.gender || 'ندارد'} | Lvl ${u.level} (${u.xp} XP)</b></div>
                <div class="flex justify-between"><span>موجودی کیف / بانک:</span><b class="text-amber-300">${u.coins.toLocaleString()} 🪙 / ${u.bank_coins.toLocaleString()} 🏦</b></div>
                <div class="flex justify-between"><span>طبقه / جان / انسانیت:</span><b>طبقه ${u.current_floor} | ❤️${u.hp}/${u.max_hp} | 🧠${u.humanity}%</b></div>
                <div class="flex justify-between"><span>وضعیت در برج / ربات:</span><b class="${(u.is_banned || u.global_banned) ? 'text-rose-400' : 'text-emerald-400'}">${u.is_banned ? '🚫 بن برج' : '🟢 آزاد برج'} | ${u.global_banned ? '⛔ بن ربات' : '🟢 فعال ربات'}</b></div>

                <div class="grid grid-cols-2 gap-2 pt-2 border-t border-white/10">
                  <input id="au_addc" type="number" placeholder="سکه اهدایی (+)" class="p-2 rounded-xl bg-slate-900 text-center text-white font-bold" />
                  <input id="au_addx" type="number" placeholder="XP اهدایی (+)" class="p-2 rounded-xl bg-slate-900 text-center text-white font-bold" />
                </div>
                <div class="grid grid-cols-2 gap-2 pt-1">
                  <button onclick="callTowerAdminApi('charge_user',{target_uid:${u.user_id},add_coins:Number(document.getElementById('au_addc').value||0),add_xp:Number(document.getElementById('au_addx').value||0)})" class="btn-success py-2 rounded-xl font-black">⚡ شارژ در برج</button>
                  <button onclick="callTowerAdminApi('toggle_ban_user',{target_uid:${u.user_id}})" class="btn-danger py-2 rounded-xl font-black">${u.is_banned ? '🟢 آزادی در برج' : '🚫 بن از برج'}</button>
                  <button onclick="callTowerAdminApi('bot_global_ban',{target_id:${u.user_id},ban:${!u.global_banned}})" class="btn-danger py-2 rounded-xl font-black">${u.global_banned ? '🟢 آن‌بن کل ربات' : '⛔ بن از کل ربات'}</button>
                  <button onclick="callTowerAdminApi('bot_set_admin',{target_id:${u.user_id},is_admin:${!u.is_bot_admin}})" class="btn-primary py-2 rounded-xl font-black">${u.is_bot_admin ? 'حذف ادمین' : '👑 ارتقا به ادمین'}</button>
                </div>
              </div>
            ` : ''}
          </div>

          <div class="glass-panel p-4 rounded-3xl space-y-2.5 mt-3">
            <h4 class="text-xs font-black text-indigo-300 text-center">📋 لیست کامل کاربران ربات (${allUsers.length} نفر — برای مدیریت روی کاربر بزنید)</h4>
            <div class="flex flex-col gap-2 max-h-96 overflow-y-auto">${usersRowsHtml || '<div class="text-center text-xs text-slate-400">کاربری یافت نشد.</div>'}</div>
          </div>
        `;
      }

      root.innerHTML = `
        ${renderTopBar('👑 فرماندهی کل ربات')}
        <div class="flex-1 overflow-y-auto px-3 pb-6 flex flex-col">
          <div class="flex gap-1.5 overflow-x-auto pb-2 mb-2 shrink-0">${tabsHtml}</div>
          ${admMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-extrabold text-center mb-2.5 whitespace-pre-line">${admMsg}</div>` : ''}
          ${admErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-extrabold text-center mb-2.5 whitespace-pre-line">${admErr}</div>` : ''}
          ${sectionHtml}
          <button onclick="nav('hub')" class="btn-primary w-full py-3 rounded-2xl font-black text-xs mt-3">🏠 مشاهده منوی اصلی با تغییرات جدید</button>
        </div>
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       بازی کامل برج شیاطین (Demon Tower RPG)
       ═══════════════════════════════════════════════════════════════════════════ */
    let dtData = null;
    let dtTab = 'main';
    let dtMsg = '';
    let dtErr = '';
    let dtSelectedWeapon = 0;
    let dtPopupDismissed = false;

    async function callTowerApi(action = 'state', extra = {}) {
      try {
        const res = await fetch('/api/tower/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ uid: Number(uid), name: myName, lang: lang, action: action, ...extra })
        });
        const data = await res.json();
        dtMsg = data.msg || '';
        dtErr = data.ok === false ? (data.error || '') : '';
        if (data.invoice_link && tg?.openInvoice) {
          tg.openInvoice(data.invoice_link, () => callTowerApi('state'));
          return;
        } else if (data.invoice_link) {
          window.open(data.invoice_link, '_blank');
        }
        if (data.state) {
          dtData = data.state;
          if (!dtSelectedWeapon) dtSelectedWeapon = dtData.player?.equipped_weapon || 1;
          drawDemonTower(document.getElementById('app'));
        }
      } catch (e) {}
    }

    window.dtNav = function(tab) {
      dtTab = tab; dtMsg = ''; dtErr = '';
      drawDemonTower(document.getElementById('app'));
    };
    window.dtAct = function(act, extra = {}) { callTowerApi(act, extra); };

    function startDemonTowerApp(root) {
      dtTab = 'main';
      root.innerHTML = `<div class="p-6 text-center"><div class="glass-panel p-6 rounded-3xl font-bold">...</div></div>`;
      callTowerApi('state');
    }

    function drawDemonTower(root) {
      if (!root || currentGame !== 'demontower' || !dtData) return;
      const p = dtData.player;
      const boss = dtData.current_boss;
      const D = T().dt;

      if (dtData.dev_mode && !dtData.is_owner) {
        root.innerHTML = `
          ${renderTopBar(T().games.wip3)}
          <div class="flex-1 flex items-center justify-center p-5 tower-bg-wrap">
            <div class="glass-panel p-6 rounded-3xl text-center border border-amber-400/50">
              <div class="text-5xl mb-3">🛠️</div>
              <h2 class="text-base font-black text-amber-300">${dtErr || 'Under Development (Owner Only)'}</h2>
            </div>
          </div>
        `;
        return;
      }

      const pop = (!dtPopupDismissed && dtData.popup) ? dtData.popup : null;
      const popupHtml = pop ? `
        <div class="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-5">
          <div class="glass-panel p-5 rounded-3xl max-w-sm w-full text-center border border-amber-400/50">
            ${pop.photo ? `<img src="${pop.photo}" class="w-full h-40 object-cover rounded-2xl mb-3" />` : ''}
            <p class="text-sm font-bold text-white mb-4 whitespace-pre-line">${pop.text}</p>
            <div class="flex gap-2">
              ${pop.btn_text && pop.btn_url ? `<button onclick="openChannelLink('${pop.btn_url}')" class="btn-success flex-1 py-2.5 rounded-xl font-black text-xs">${pop.btn_text}</button>` : ''}
              <button onclick="dtPopupDismissed=true;drawDemonTower(document.getElementById('app'))" class="btn-danger flex-1 py-2.5 rounded-xl font-bold text-xs">✖</button>
            </div>
          </div>
        </div>
      ` : '';

      const alertHtml = `
        ${dtMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-extrabold text-emerald-100 mb-3 whitespace-pre-line text-center">${dtMsg}</div>` : ''}
        ${dtErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-extrabold text-rose-100 mb-3 whitespace-pre-line text-center">${dtErr}</div>` : ''}
      `;

      let bodyHtml = '';

      if (dtTab === 'main') {
        const tHero = getAssetImg('tower_hero', TOWER_HERO_IMG || '/api/banner/demontower.png');
        bodyHtml = `
          <div class="glass-panel rounded-3xl overflow-hidden mb-3 shrink-0">
            <img src="${tHero}" class="w-full h-36 object-cover border-b border-white/10" />
            <div class="p-3 flex justify-between items-center text-xs font-extrabold">
              <span class="text-amber-300">🪙 ${p.coins.toLocaleString()}</span>
              <span class="text-emerald-300">❤️ ${p.hp}/${p.max_hp}</span>
              <span class="text-sky-300">🧠 ${D.humanity}: ${p.humanity}%</span>
              <span class="text-purple-300">⭐ Lvl ${p.level}</span>
            </div>
          </div>

          ${alertHtml}

          <button onclick="dtNav('floor')" class="btn-danger w-full py-4 px-4 rounded-2xl font-black text-base mb-2.5 flex items-center justify-between shadow-lg">
            <span>⚔️ ${D.floorBtn} ${p.current_floor} (${boss ? boss.boss_name : '✓'})</span>
            <span class="text-xs bg-black/30 px-2.5 py-1 rounded-xl">${D.enterBattle} ◀</span>
          </button>

          <div class="grid grid-cols-2 gap-2.5">
            <button onclick="dtNav('char')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.charBtn}</button>
            <button onclick="dtNav('hospital')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.hospBtn}</button>
            <button onclick="dtNav('vault')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.vaultBtn}</button>
            <button onclick="dtNav('shop')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.shopBtn}</button>
            <button onclick="dtNav('gift')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.giftBtn}</button>
            <button onclick="dtNav('voucher')" class="glass-panel p-3.5 rounded-2xl font-black text-sm flex items-center justify-center gap-2">${D.voucherBtn}</button>
            <button onclick="dtNav('account')" class="btn-primary col-span-2 p-3.5 rounded-2xl font-black text-sm text-center">${D.accBtn}</button>
          </div>
        `;
      }
      
      else if (dtTab === 'floor') {
        if (window.dtBattleTimer) { clearInterval(window.dtBattleTimer); window.dtBattleTimer = null; }
        const bt = dtData.active_battle;

        if (bt) {
          const bossHpPct = Math.max(0, Math.min(100, Math.round((bt.boss_hp / bt.boss_max_hp) * 100)));
          const myHpPct = Math.max(0, Math.min(100, Math.round((bt.p_hp / bt.p_max_hp) * 100)));
          const isCharging = bt.boss_state === 'charging';
          const isAbsDef = bt.boss_state === 'abs_defense';
          const isStunned = bt.boss_state === 'stunned';

          const stateColors = {
            charging: 'bg-rose-600/50 border-rose-400 text-rose-100 animate-pulse',
            abs_defense: 'bg-sky-600/40 border-sky-400 text-sky-100',
            evasive: 'bg-amber-600/40 border-amber-400 text-amber-100',
            stunned: 'bg-emerald-600/40 border-emerald-400 text-emerald-100',
            normal: 'glass-soft border-white/20 text-slate-200'
          };

          const logsHtml = (bt.logs || []).map((l, idx) => `
            <div class="text-[11px] ${idx === 0 ? 'text-amber-300 font-black' : 'text-slate-300'} border-b border-white/5 pb-1">${l}</div>
          `).join('');

          bodyHtml = `
            ${alertHtml}
            <div class="glass-panel p-3.5 rounded-3xl mb-2.5 border ${isCharging ? 'border-rose-500 shadow-[0_0_25px_rgba(244,63,94,0.45)]' : 'border-white/15'}">
              <div class="flex items-center gap-3 mb-2">
                ${bt.boss_photo ? `<img src="${bt.boss_photo}" class="w-16 h-16 rounded-2xl object-cover border-2 border-rose-500 shrink-0" />` : `<div class="w-16 h-16 rounded-2xl bg-rose-950 flex items-center justify-center text-4xl shrink-0">👹</div>`}
                <div class="flex-1 min-w-0">
                  <div class="flex justify-between items-center mb-1">
                    <span class="font-black text-sm text-amber-300 truncate">${bt.boss_name}</span>
                    <span class="text-xs font-extrabold text-rose-300">❤️ ${bt.boss_hp} / ${bt.boss_max_hp}</span>
                  </div>
                  <div class="w-full h-3 bg-slate-900 rounded-full overflow-hidden border border-white/10">
                    <div style="width: ${bossHpPct}%" class="h-full bg-gradient-to-r from-rose-600 to-amber-500 transition-all"></div>
                  </div>
                  <div class="text-[10px] text-slate-300 mt-1 flex justify-between">
                    <span>نوبت ${bt.turn}</span>
                    <span>⚔️ ATK: ${bt.boss_atk} | 🛡️ DEF: ${bt.boss_def}</span>
                  </div>
                </div>
              </div>

              <div class="p-3 rounded-2xl border text-center font-black text-xs mb-3 ${stateColors[bt.boss_state] || stateColors.normal}">
                <div>${bt.state_prompt}</div>
                ${isCharging ? `
                  <div class="mt-2 flex items-center justify-center gap-2">
                    <span class="px-3 py-1 rounded-xl bg-black/60 text-rose-300 text-sm font-black">
                      ⏱️ فرصت واکنش: <span id="dtCountdownNum">5.0</span> ثانیه
                    </span>
                  </div>
                ` : ''}
              </div>

              <div class="glass-soft p-2.5 rounded-2xl mb-3">
                <div class="flex justify-between text-xs font-extrabold mb-1">
                  <span class="text-emerald-300">❤️ جان شما: ${bt.p_hp} / ${bt.p_max_hp}</span>
                  <span class="text-amber-300">🔥 خشم (Rage): ${bt.p_rage}%</span>
                </div>
                <div class="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden mb-1.5">
                  <div style="width: ${myHpPct}%" class="h-full bg-emerald-500 transition-all"></div>
                </div>
                <div class="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                  <div style="width: ${bt.p_rage}%" class="h-full bg-amber-400 transition-all"></div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-2 mb-3">
                <button onclick="dtAct('battle_move',{move:'quick'})" class="btn-primary py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>⚡ حمله سریع</span>
                  <span class="text-[10px] opacity-80 font-bold">ضد جاخالی (+25 خشم)</span>
                </button>
                <button onclick="dtAct('battle_move',{move:'heavy'})" class="${isStunned ? 'btn-success ring-2 ring-white' : 'btn-danger'} py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>💥 ضربه سنگین</span>
                  <span class="text-[10px] opacity-80 font-bold">خسارت بالا به غول</span>
                </button>
                <button onclick="dtAct('battle_move',{move:'shield'})" class="${isCharging ? 'btn-success ring-2 ring-amber-300' : 'glass-soft'} py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>🛡️ سپر دفاعی</span>
                  <span class="text-[10px] opacity-80 font-bold">دفع حمله ۵ ثانیه‌ای + ضدحمله</span>
                </button>
                <button onclick="dtAct('battle_move',{move:'dodge'})" class="${isCharging ? 'btn-success ring-2 ring-amber-300' : 'glass-soft'} py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>💨 جاخالی سریع</span>
                  <span class="text-[10px] opacity-80 font-bold">فرار از ضربه (+30 خشم)</span>
                </button>
                <button onclick="dtAct('battle_move',{move:'break'})" class="${isAbsDef ? 'btn-success ring-2 ring-sky-300' : 'glass-soft'} py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>🔨 شکستن گارد</span>
                  <span class="text-[10px] opacity-80 font-bold">ضد حالت دفاع مطلق غول</span>
                </button>
                <button onclick="dtAct('battle_move',{move:'blood'})" ${bt.p_rage < 50 ? 'disabled' : ''} class="${bt.p_rage >= 50 ? 'btn-danger ring-2 ring-rose-300' : 'bg-slate-800/60 opacity-45'} py-3 px-2 rounded-2xl font-black text-xs flex flex-col items-center">
                  <span>🩸 جادوی خون (50% خشم)</span>
                  <span class="text-[10px] opacity-80 font-bold">ضربه مرگبار + شفای جان</span>
                </button>
              </div>

              <div class="glass-soft p-2.5 rounded-2xl max-h-28 overflow-y-auto space-y-1 text-right">
                ${logsHtml}
              </div>
            </div>
          `;

          if (isCharging) {
            let rem = 5.0;
            setTimeout(() => {
              if (window.dtBattleTimer) clearInterval(window.dtBattleTimer);
              window.dtBattleTimer = setInterval(() => {
                if (currentGame !== 'demontower' || dtTab !== 'floor') {
                  clearInterval(window.dtBattleTimer);
                  return;
                }
                rem = Math.max(0, rem - 0.2);
                const el = document.getElementById('dtCountdownNum');
                if (el) el.innerText = rem.toFixed(1);
                if (rem <= 0) {
                  clearInterval(window.dtBattleTimer);
                  window.dtBattleTimer = null;
                  dtAct('battle_move', { move: 'timeout' });
                }
              }, 200);
            }, 50);
          }
        } else {
          const myWeapons = (dtData.items || []).filter(i => i.item_type === 'weapon' && p.owned_weapons.includes(i.id));
          const wSelectHtml = myWeapons.map(w => `
            <button onclick="dtSelectedWeapon=${w.id};drawDemonTower(document.getElementById('app'))" class="px-3 py-2 rounded-xl text-xs font-bold border ${dtSelectedWeapon === w.id ? 'btn-success border-white' : 'glass-soft border-white/10'}">
              ⚔️ ${w.name} (+${w.atk_bonus} ATK)
            </button>
          `).join('');

          bodyHtml = `
            ${alertHtml}
            ${boss ? `
              <div class="glass-panel p-4 rounded-3xl text-center mb-3">
                ${boss.photo ? `<img src="${boss.photo}" class="w-full h-40 object-cover rounded-2xl mb-3" />` : `<div class="text-6xl my-3">👹</div>`}
                <div class="text-xs font-black text-rose-400">${D.floorBtn} ${boss.floor_num}</div>
                <h2 class="text-xl font-black text-amber-300 mb-1">${boss.boss_name}</h2>
                <p class="text-xs text-slate-200 mb-3">${boss.description}</p>
                <div class="grid grid-cols-3 gap-2 text-xs font-extrabold glass-soft p-2.5 rounded-2xl mb-2">
                  <span class="text-rose-300">❤️ HP: ${boss.hp * 2}</span>
                  <span class="text-amber-300">⚔️ ATK: ${boss.atk}</span>
                  <span class="text-sky-300">🛡️ DEF: ${boss.def}</span>
                </div>
                <div class="text-[11px] text-slate-300 text-start space-y-1 glass-soft p-2.5 rounded-2xl mb-3">
                  <div>🔥 <b>${D.bossPower}:</b> ${boss.power_desc}</div>
                  <div>⚡ <b>${D.bossWeak}:</b> ${boss.weakness}</div>
                  <div>🎁 <b>${D.bossReward}:</b> ${boss.reward_coins} 🪙 + ${boss.reward_xp} XP + «${boss.drop_item}»</div>
                </div>

                <div class="text-xs font-bold text-amber-200 mb-2">${D.pickWeaponHint}</div>
                <div class="flex flex-wrap gap-1.5 justify-center mb-4">${wSelectHtml}</div>

                <button onclick="dtAct('battle_start', {weapon_id: dtSelectedWeapon})" class="btn-danger w-full py-4 rounded-2xl font-black text-base">
                  ${D.startBattleBtn} ${boss.floor_num}
                </button>
              </div>
            ` : `<div class="glass-panel p-6 rounded-3xl text-center font-black text-emerald-300">🎉</div>`}
            <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
          `;
        }
      }

      else if (dtTab === 'char') {
        const genderSection = !p.gender ? `
          <div class="glass-panel p-4 rounded-3xl text-center mb-3 border border-amber-400/50">
            <h3 class="text-sm font-black text-amber-300 mb-3">${D.pickGenderTitle}</h3>
            <div class="grid grid-cols-2 gap-3">
              <button onclick="dtAct('choose_gender', {gender:'male'})" class="glass-soft p-3 rounded-2xl flex flex-col items-center border hover:border-amber-400">
                ${dtData.male_img ? `<img src="${dtData.male_img}" class="w-24 h-28 object-cover rounded-xl mb-2" />` : `<div class="text-5xl my-4">🥷</div>`}
                <span class="font-black text-xs text-sky-300">${D.male}</span>
              </button>
              <button onclick="dtAct('choose_gender', {gender:'female'})" class="glass-soft p-3 rounded-2xl flex flex-col items-center border hover:border-amber-400">
                ${dtData.female_img ? `<img src="${dtData.female_img}" class="w-24 h-28 object-cover rounded-xl mb-2" />` : `<div class="text-5xl my-4">🧝‍♀️</div>`}
                <span class="font-black text-xs text-pink-300">${D.female}</span>
              </button>
            </div>
          </div>
        ` : `
          <div class="glass-panel p-3.5 rounded-2xl flex items-center justify-between mb-3 text-xs font-bold">
            <span><b class="text-amber-300">${p.gender === 'male' ? D.male : D.female}</b></span>
            <span>⚔️ ATK: ${p.atk} | 🛡️ DEF: ${p.def} | ⚡ SPD: ${p.spd}</span>
          </div>
        `;

        const itemsHtml = (dtData.items || []).map(it => {
          const isW = it.item_type === 'weapon';
          const owned = isW ? p.owned_weapons.includes(it.id) : p.owned_armors.includes(it.id);
          const equipped = isW ? (p.equipped_weapon === it.id) : (p.equipped_armor === it.id);
          return `
            <div class="glass-panel p-3 rounded-2xl flex items-center justify-between gap-2">
              <div class="flex items-center gap-2.5">
                ${it.photo ? `<img src="${it.photo}" class="w-12 h-12 rounded-xl object-cover" />` : `<div class="w-12 h-12 rounded-xl glass-soft flex items-center justify-center text-2xl">${isW ? '⚔️' : '🛡️'}</div>`}
                <div class="text-start">
                  <div class="font-black text-xs text-white">${it.name}</div>
                  <div class="text-[10px] text-emerald-300 font-bold">
                    +HP:${it.hp_bonus} | +ATK:${it.atk_bonus} | +DEF:${it.def_bonus} | SPD:${it.spd_bonus}
                  </div>
                </div>
              </div>
              <button onclick="dtAct('buy_or_equip_item', {item_id:${it.id}})" class="${equipped ? 'btn-success' : (owned ? 'btn-primary' : 'btn-danger')} px-3 py-2 rounded-xl text-[11px] font-black shrink-0">
                ${equipped ? D.equipped : (owned ? D.select : `${it.price} 🪙 ${D.buy}`)}
              </button>
            </div>
          `;
        }).join('');

        bodyHtml = `
          ${alertHtml}
          ${genderSection}
          <div class="flex flex-col gap-2 mb-3">${itemsHtml}</div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'hospital') {
        bodyHtml = `
          ${alertHtml}
          <div class="glass-panel p-5 rounded-3xl text-center mb-3">
            <div class="text-5xl mb-2">🏥</div>
            <h2 class="text-lg font-black text-emerald-300 mb-2">${D.hospBtn}</h2>
            <p class="text-xs text-slate-300 leading-relaxed mb-4">${D.hospDesc}</p>
            <div class="grid grid-cols-2 gap-2 glass-soft p-3 rounded-2xl text-xs font-extrabold mb-4">
              <span class="text-rose-300">❤️ HP: ${p.hp} / ${p.max_hp}</span>
              <span class="text-sky-300">🧠 ${D.humanity}: ${p.humanity}%</span>
            </div>
            ${p.sleep_rem > 0 ? `<div class="p-3 rounded-xl bg-rose-600/40 text-xs font-bold mb-3">😴 (${Math.ceil(p.sleep_rem/60)}m)</div>` : ''}
            ${p.hospital_rem > 0 ? `
              <div class="p-3 rounded-xl bg-amber-500/30 text-amber-200 text-xs font-extrabold mb-3">⏳ ${p.hospital_rem}s</div>
              <button onclick="dtAct('state')" class="btn-primary w-full py-3 rounded-xl font-bold text-xs">🔄</button>
            ` : `
              <button onclick="dtAct('enter_hospital')" class="btn-success w-full py-4 rounded-2xl font-black text-sm">${D.healBtn}</button>
            `}
          </div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'vault') {
        const lootCount = (p.inventory || []).length;
        const lootVal = (p.inventory || []).reduce((a, b) => a + (b.price || 50), 0);
        bodyHtml = `
          ${alertHtml}
          <div class="glass-panel p-4 rounded-3xl mb-3 text-center">
            <h2 class="text-base font-black text-amber-300 mb-2">${D.vaultBtn} (2% / h)</h2>
            <div class="grid grid-cols-2 gap-2 glass-soft p-3 rounded-2xl text-xs font-extrabold mb-3">
              <span class="text-amber-300">🪙 ${p.coins.toLocaleString()}</span>
              <span class="text-emerald-300">🏦 ${p.bank_coins.toLocaleString()}</span>
            </div>

            <div class="flex gap-2 mb-3">
              <input id="bankAmt" type="number" placeholder="🪙..." class="flex-1 p-2.5 rounded-xl glass-soft text-center text-white text-xs font-bold" />
              <button onclick="dtAct('bank_deposit', {amount: Number(document.getElementById('bankAmt').value)})" class="btn-success px-3 py-2 rounded-xl text-xs font-black">${D.deposit}</button>
              <button onclick="dtAct('bank_withdraw', {amount: Number(document.getElementById('bankAmt').value)})" class="btn-primary px-3 py-2 rounded-xl text-xs font-black">${D.withdraw}</button>
            </div>

            <div class="border-t border-white/10 pt-3 mb-3">
              <div class="text-xs font-bold mb-2">🎒 (${lootCount}) = ${lootVal} 🪙</div>
              <button onclick="dtAct('sell_loot')" class="btn-primary w-full py-2.5 rounded-xl font-black text-xs">${D.sellLootBtn}</button>
            </div>

            <div class="border-t border-white/10 pt-3">
              <div class="text-xs font-black text-amber-200 mb-2">${D.transferTitle}</div>
              <input id="trTarget" type="text" placeholder="@username / ID" class="w-full p-2.5 rounded-xl glass-soft text-center text-white text-xs font-bold mb-2" />
              <input id="trAmt" type="number" placeholder="🪙" class="w-full p-2.5 rounded-xl glass-soft text-center text-white text-xs font-bold mb-2" />
              <button onclick="dtAct('transfer_coins', {target: document.getElementById('trTarget').value, amount: Number(document.getElementById('trAmt').value)})" class="btn-danger w-full py-3 rounded-xl font-black text-xs">
                ${D.transferBtn}
              </button>
            </div>
          </div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'shop') {
        const packsHtml = (dtData.star_packages || []).map(pk => `
          <div class="glass-panel p-3.5 rounded-2xl flex items-center justify-between">
            <div class="text-start">
              <div class="font-black text-xs text-amber-300">${pk.title}</div>
              <div class="text-[11px] text-emerald-300 font-bold mt-0.5">+${pk.coins.toLocaleString()} 🪙 | +${pk.xp.toLocaleString()} XP</div>
            </div>
            <button onclick="dtAct('create_star_invoice', {pack_id:'${pk.id}'})" class="btn-success px-3.5 py-2 rounded-xl font-black text-xs shrink-0">
              ⭐ ${pk.stars} Stars
            </button>
          </div>
        `).join('');
        bodyHtml = `
          ${alertHtml}
          <div class="flex flex-col gap-2.5 mb-3">${packsHtml}</div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'gift') {
        bodyHtml = `
          ${alertHtml}
          <div class="glass-panel p-5 rounded-3xl text-center mb-3">
            <div class="text-4xl mb-2">🎁</div>
            <h3 class="text-base font-black text-amber-300 mb-3">${D.giftBtn}</h3>
            <input id="giftInp" type="text" placeholder="CODE..." class="w-full p-3.5 rounded-2xl glass-soft text-center font-black text-white mb-3" />
            <button onclick="dtAct('redeem_gift', {code: document.getElementById('giftInp').value})" class="btn-success w-full py-3.5 rounded-2xl font-black">${D.redeemBtn}</button>
          </div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'voucher') {
        const optsHtml = D.vchTypes.map(vt => `<option value="${vt}">${vt}</option>`).join('');
        const vListHtml = (dtData.vouchers || []).map(v => {
          const stBadge = v.status === 'approved'
            ? `<span class="text-emerald-300 font-black">${D.vchApproved} (${v.voucher_code})</span>`
            : (v.status === 'rejected' ? `<span class="text-rose-400 font-black">${D.vchRejected}</span>` : `<span class="text-amber-300 font-black">${D.vchPending}</span>`);
          return `
            <div class="glass-soft p-3 rounded-2xl text-start text-xs space-y-1 border border-white/10">
              <div class="flex justify-between"><b>🎁 ${v.voucher_type}</b><span>🪙 ${v.coins_offered.toLocaleString()}</span></div>
              <div>${stBadge}</div>
              ${v.owner_note ? `<div class="p-2 rounded-xl bg-indigo-950/80 text-amber-200">💬 <b>${D.ownerNote}:</b> ${v.owner_note}</div>` : ''}
            </div>
          `;
        }).join('');

        bodyHtml = `
          ${alertHtml}
          <div class="glass-panel p-4 rounded-3xl mb-3">
            <h3 class="text-sm font-black text-amber-300 text-center mb-3">${D.voucherBtn}</h3>
            <input id="vchCoins" type="number" placeholder="${D.vchOfferHint} (${p.coins} 🪙)" class="w-full p-3 rounded-xl glass-soft text-center font-bold text-xs text-white mb-2.5" />
            <select id="vchType" class="w-full p-3 rounded-xl bg-slate-900 border border-white/20 text-white text-xs font-bold mb-3 text-center">
              ${optsHtml}
            </select>
            <button onclick="dtAct('request_voucher', {coins: Number(document.getElementById('vchCoins').value), voucher_type: document.getElementById('vchType').value})" class="btn-success w-full py-3 rounded-2xl font-black text-xs">
              ${D.vchSendBtn}
            </button>
          </div>

          <div class="glass-panel p-3.5 rounded-3xl mb-3">
            <div class="text-xs font-black text-indigo-300 mb-2 text-center">${D.vchChatTitle}</div>
            <div class="flex flex-col gap-2 max-h-52 overflow-y-auto">${vListHtml || '—'}</div>
          </div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      else if (dtTab === 'account') {
        bodyHtml = `
          <div class="glass-panel p-5 rounded-3xl text-start space-y-2 text-xs font-bold mb-3">
            <h3 class="text-base font-black text-amber-300 text-center mb-3">${D.accBtn}</h3>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>ID:</span><b>${myName} (${p.user_id})</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>${D.charBtn}:</span><b>${p.gender === 'male' ? D.male : (p.gender === 'female' ? D.female : '—')}</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>Level / XP:</span><b class="text-purple-300">Level ${p.level} (${p.xp} XP)</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>${D.floorBtn}:</span><b class="text-rose-400">${p.current_floor}</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>🪙 / 🏦:</span><b class="text-amber-300">${p.coins.toLocaleString()} / ${p.bank_coins.toLocaleString()}</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>❤️ / 🧠:</span><b class="text-emerald-300">${p.hp}/${p.max_hp} | ${p.humanity}%</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>ATK / DEF / SPD:</span><b>⚔️${p.atk} | 🛡️${p.def} | ⚡${p.spd}</b></div>
            <div class="flex justify-between glass-soft p-2.5 rounded-xl"><span>⚔️ / 🛡️:</span><b>${p.weapon_name} / ${p.armor_name}</b></div>
          </div>
          <button onclick="dtNav('main')" class="btn-primary w-full py-3 rounded-2xl font-bold text-xs">${D.backTower}</button>
        `;
      }

      root.innerHTML = `
        ${popupHtml}
        ${renderTopBar(T().games.wip3)}
        <div class="flex-1 overflow-y-auto px-3 pb-6 flex flex-col tower-bg-wrap">
          ${bodyHtml}
        </div>
      `;
    }

    /* ═══════════ درگاه ۳ گزینه‌ای بازی‌های لابی‌دار ═══════════ */
    window.setRpsTargetAndContinue = function(n) {
      lobbyState.rpsTargetWins = n;
      lobbyState.step = 'options';
      renderLobbyGate(document.getElementById('app'));
    };
    window.startLobbyWithBot = function() { nav(lobbyState.game, true); };
    window.openInviteBoxes = function() {
      lobbyState.step = 'invite_boxes';
      lobbyState.inviteWarning = '';
      lobbyState.inviteSuccess = '';
      renderLobbyGate(document.getElementById('app'));
    };
    window.submitBotInvites = async function() {
      const inputs = document.querySelectorAll('.invite-user-input');
      const targets = Array.from(inputs).map(i => i.value.trim()).filter(Boolean);
      if (!targets.length) return;
      try {
        const res = await fetch('/api/invite_friends', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            inviter_id: Number(uid),
            inviter_name: myName,
            game_type: lobbyState.game,
            session: String(parsedChat),
            targets: targets,
            extra: String(lobbyState.rpsTargetWins)
          })
        });
        const data = await res.json();
        lobbyState.inviteWarning = data.not_started?.length > 0 ? `${T().notStartedWarn}\n(${data.not_started.join(' , ')})` : '';
        lobbyState.inviteSuccess = data.invited?.length > 0 ? `✅ (${data.invited.join(' , ')})` : '';
        renderLobbyGate(document.getElementById('app'));
      } catch (e) {}
    };

    window.shareTableInline = function(gameType, extraStr = '') {
      const startParamStr = `${gameType}__${parsedChat}__${lang}`;
      const directTableUrl = `https://t.me/${BOT_USERNAME}/${SHORT_NAME}?startapp=${startParamStr}`;
      const shareText = `🎮 ${T().heroTitle} (${gameType.toUpperCase()})\n👤 ${myName}`;
      const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(directTableUrl)}&text=${encodeURIComponent(shareText)}`;
      try {
        if (tg && typeof tg.openTelegramLink === 'function') {
          tg.openTelegramLink(shareUrl);
          return;
        }
      } catch (err) {}
      window.open(shareUrl, '_blank');
    };

    function renderLobbyGate(root) {
      if (lobbyState.step === 'rps_count') {
        root.innerHTML = `
          ${renderTopBar(T().games.rps)}
          <div class="flex-1 flex flex-col justify-center p-4">
            <div class="glass-panel p-6 rounded-3xl text-center">
              <h2 class="text-base font-black text-amber-300 mb-4">${T().rpsAskWins}</h2>
              <div class="grid grid-cols-3 gap-3">
                <button onclick="setRpsTargetAndContinue(3)" class="btn-primary py-4 rounded-2xl font-black text-base">3 ${T().winsUnit}</button>
                <button onclick="setRpsTargetAndContinue(5)" class="btn-success py-4 rounded-2xl font-black text-base">5 ${T().winsUnit}</button>
                <button onclick="setRpsTargetAndContinue(7)" class="btn-danger py-4 rounded-2xl font-black text-base">7 ${T().winsUnit}</button>
              </div>
            </div>
          </div>
        `;
        return;
      }

      if (lobbyState.step === 'invite_boxes') {
        const needed = Math.max(1, lobbyState.maxPlayers - 1);
        let boxesHtml = '';
        for (let i = 0; i < needed; i++) {
          boxesHtml += `<input type="text" placeholder="@username / ID (${i + 1})" class="invite-user-input w-full p-3 rounded-xl glass-soft text-white text-sm font-bold text-center" />`;
        }
        root.innerHTML = `
          ${renderTopBar(T().optInvite)}
          <div class="flex-1 overflow-y-auto p-4 flex flex-col justify-center">
            <div class="glass-panel p-5 rounded-3xl text-center">
              <div class="flex flex-col gap-2.5 mb-4">${boxesHtml}</div>
              ${lobbyState.inviteWarning ? `<div class="p-3 rounded-xl bg-rose-600/30 border border-rose-400 text-xs font-extrabold text-rose-200 mb-3 whitespace-pre-line">${lobbyState.inviteWarning}</div>` : ''}
              ${lobbyState.inviteSuccess ? `<div class="p-3 rounded-xl bg-emerald-600/30 border border-emerald-400 text-xs font-extrabold text-emerald-200 mb-3">${lobbyState.inviteSuccess}</div>` : ''}
              <button onclick="submitBotInvites()" class="btn-success w-full py-3.5 rounded-2xl font-black mb-2">${T().sendInviteBtn}</button>
              <button onclick="nav('${lobbyState.game}', true)" class="btn-primary w-full py-3.5 rounded-2xl font-black mb-2">${T().enterTableBtn}</button>
              <button onclick="lobbyState.step='options';renderLobbyGate(document.getElementById('app'))" class="btn-danger w-full py-2.5 rounded-xl font-bold text-xs">${T().backMenu}</button>
            </div>
          </div>
        `;
        return;
      }

      root.innerHTML = `
        ${renderTopBar()}
        <div class="flex-1 flex flex-col justify-center p-4">
          <div class="glass-panel p-5 rounded-3xl text-center flex flex-col gap-3">
            <button onclick="startLobbyWithBot()" class="btn-success w-full py-4 rounded-2xl font-black text-sm">${T().optBot}</button>
            <button onclick="openInviteBoxes()" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">${T().optInvite}</button>
            <button onclick="shareTableInline('${lobbyState.game}', '${lobbyState.rpsTargetWins}');nav('${lobbyState.game}', true)" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">${T().optShare}</button>
          </div>
        </div>
      `;
    }

    /* ═══════════ میز حکم واقعی روی فرش قرمز ایرانی ═══════════ */
    let hokmMode = '4p';
    let hokmError = '';
    let myMicActive = false;
    let localAudioStream = null;

    async function callHokmApi(action, extra = {}) {
      if (action === 'state' && isUserTyping()) return;
      try {
        const res = await fetch('/api/hokm/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            session: String(parsedChat || 'default'),
            mode: hokmMode,
            uid: Number(uid),
            name: myName,
            username: myUsername,
            photo: myPhoto,
            action: action,
            ...extra
          })
        });
        const data = await res.json();
        if (data.ok === false && data.error) {
          hokmError = data.error;
          if (tg?.showAlert) tg.showAlert(data.error);
        } else if (action !== 'state') {
          hokmError = '';
        }
        if (data.state && !(action === 'state' && isUserTyping())) {
          drawHokmTable(data.state);
        }
      } catch (e) {}
    }

    window.hokmChooseSuit = function(s) { callHokmApi('choose_trump', { suit: s }); };
    window.hokmPlayCard = function(code) { callHokmApi('play_card', { card: code }); };
    window.hokmFillBots = function() { callHokmApi('add_bots'); };
    window.hokmSwapSeats = function(i1, i2) { callHokmApi('swap_seats', { idx1: i1, idx2: i2 }); };
    window.hokmSendReaction = function(txt) { callHokmApi('chat', { text: txt }); };
    window.hokmSendCustomChat = function() {
      const inp = document.getElementById('hokmChatInp');
      if (inp && inp.value.trim()) {
        const msgText = inp.value.trim();
        inp.value = '';
        inp.blur();
        callHokmApi('chat', { text: msgText });
      }
    };
    window.hokmToggleMic = async function() {
      if (!myMicActive) {
        try {
          localAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          myMicActive = true;
        } catch (e) {
          myMicActive = true;
        }
      } else {
        if (localAudioStream) localAudioStream.getTracks().forEach(t => t.stop());
        myMicActive = false;
      }
      callHokmApi('mic', { mic: myMicActive });
    };

    function startHokmEngine(root, mode) {
      hokmMode = mode;
      root.innerHTML = `<div class="p-4 flex-1 flex items-center justify-center"><div class="glass-panel p-6 rounded-3xl font-bold">...</div></div>`;
      callHokmApi('join');
      if (hokmPollTimer) clearInterval(hokmPollTimer);
      hokmPollTimer = setInterval(() => callHokmApi('state'), 1200);
    }

    function renderRealFaceDownTricks(count) {
      let items = '';
      for (let i = 0; i < 7; i++) {
        if (i < count) {
          items += `<div class="card-back-real w-7 h-10 -ml-2.5 first:ml-0 flex items-center justify-center text-[10px] font-black text-amber-300">${i+1}</div>`;
        } else {
          items += `<div class="w-6 h-9 -ml-2 first:ml-0 rounded border border-amber-200/20 bg-black/25"></div>`;
        }
      }
      return `<div class="ltr-grid flex items-center px-2">${items}</div>`;
    }

    function renderPlayerRectCard(seat) {
      if (!seat) return '';
      const pct = seat.timer_pct ?? 100;
      const ringColor = seat.is_turn ? (pct > 35 ? '#10b981' : '#ef4444') : 'rgba(255,255,255,0.2)';
      const initial = (seat.name || 'P')[0];
      const avatarHtml = seat.photo
        ? `<img src="${seat.photo}" class="w-8 h-8 rounded-full object-cover" />`
        : `<div class="w-8 h-8 rounded-full bg-indigo-800 flex items-center justify-center font-black text-xs">${initial}</div>`;

      return `
        <div class="relative flex flex-col items-center">
          ${seat.bubble ? `
            <div class="absolute -top-8 z-30 px-2.5 py-1 rounded-xl bg-black/55 backdrop-blur-md border border-white/25 text-white text-xs font-extrabold whitespace-nowrap shadow-lg">
              ${seat.bubble}
            </div>
          ` : ''}
          <div class="glass-panel rounded-xl px-2.5 py-1 flex items-center gap-2 border ${seat.is_turn ? 'border-emerald-400' : 'border-white/15'}">
            <div style="background: conic-gradient(${ringColor} ${pct * 3.6}deg, rgba(255,255,255,0.1) 0deg);" class="p-0.5 rounded-full">
              ${avatarHtml}
            </div>
            <div class="text-start leading-tight">
              <div class="text-[11px] font-black text-white flex items-center gap-1">
                ${seat.is_hakem ? '👑' : ''}<span class="truncate max-w-[75px]">${seat.name}</span>
                ${seat.mic_on ? '<span class="text-emerald-400">🎙️</span>' : ''}
              </div>
              <div class="text-[9px] text-amber-200/80 font-bold">
                🃏 ${seat.cards_left} ${seat.is_turn ? `(${seat.timer_sec}s)` : ''}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function drawHokmTable(st) {
      const root = document.getElementById('app');
      if (!root || (currentGame !== 'hokm' && currentGame !== 'hokm4p' && currentGame !== 'hokm2p')) return;

      const pList = st.players || [];
      const isHost = !st.host_id || Number(st.host_id) === Number(uid);

      if (st.status === 'joining') {
        const rowsHtml = pList.map((p, idx) => `
          <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center text-xs font-bold">
            <span>#${idx + 1}: <b class="text-amber-300">${p.name}</b></span>
            ${isHost && st.mode === '4p' && idx > 0 ? `
              <button onclick="hokmSwapSeats(2, ${idx})" class="btn-primary px-2 py-1 rounded-lg text-[10px]">${T().pickPartner}</button>
            ` : ''}
          </div>
        `).join('');

        root.innerHTML = `
          ${renderTopBar(st.mode === '2p' ? T().games.hokm2p : T().games.hokm)}
          <div class="flex-1 p-3 flex flex-col justify-between">
            <div class="persian-carpet p-4 flex flex-col justify-between">
              <div class="carpet-medallion"></div>
              <div class="z-10 glass-panel p-4 rounded-2xl text-center my-auto">
                <h2 class="text-base font-black text-amber-300 mb-3">(${pList.length}/${st.max_players})</h2>
                <div class="flex flex-col gap-2 mb-4">${rowsHtml}</div>
                <div class="flex flex-col gap-2">
                  <button onclick="hokmFillBots()" class="btn-success w-full py-3 rounded-xl font-black text-xs">${T().fillBotsBtn}</button>
                  <button onclick="shareTableInline('${st.mode === '2p' ? 'hokm2p' : 'hokm'}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs">${T().optShare}</button>
                </div>
              </div>
            </div>
          </div>
        `;
        return;
      }

      const topSeat = st.seats?.top || { name: 'P2', cards_left: 0 };
      const rightSeat = st.seats?.right || null;
      const leftSeat = st.seats?.left || null;
      const bottomSeat = st.seats?.bottom || { name: myName, cards_left: (st.my_hand || []).length };
      const isMyTurn = Number(st.turn_id) === Number(uid) && st.status === 'playing';

      let centerStageHtml = '';
      if (st.status === 'hakem_choosing') {
        if (Number(st.hakem_id) === Number(uid)) {
          centerStageHtml = `
            <div class="z-20 glass-panel p-3.5 rounded-2xl border border-amber-400 text-center max-w-[260px]">
              <div class="text-amber-300 font-black text-xs mb-2">${T().chooseTrumpPrompt}</div>
              <div class="grid grid-cols-2 gap-2">
                <button onclick="hokmChooseSuit('S')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-base">♠️</button>
                <button onclick="hokmChooseSuit('H')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-base">♥️</button>
                <button onclick="hokmChooseSuit('D')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-base">♦️</button>
                <button onclick="hokmChooseSuit('C')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-base">♣️</button>
              </div>
            </div>
          `;
        } else {
          centerStageHtml = `<div class="z-20 glass-panel px-4 py-2.5 rounded-2xl text-xs font-extrabold text-amber-300">👑 ${st.hakem_name}: ${T().waitingHakem}</div>`;
        }
      } else if (st.status === 'finished') {
        centerStageHtml = `
          <div class="z-20 glass-panel p-5 rounded-3xl text-center border-2 border-amber-400">
            <div class="text-xl font-black text-amber-300 mb-3">🏆 ${T().winner}: ${st.winner_display}</div>
            <button onclick="nav('hub')" class="btn-success px-5 py-2.5 rounded-xl font-bold text-xs">${T().backMenu}</button>
          </div>
        `;
      } else {
        const posStyles = {
          top:    "top: 2px; left: 50%; transform: translateX(-50%);",
          bottom: "bottom: 2px; left: 50%; transform: translateX(-50%);",
          right:  "right: 6px; top: 50%; transform: translateY(-50%);",
          left:   "left: 6px; top: 50%; transform: translateY(-50%);"
        };
        const playedHtml = (st.trick || []).map(t => `
          <div style="${posStyles[t.pos] || posStyles.bottom}" class="absolute z-10 flex flex-col items-center">
            <div class="playing-card w-14 h-20 ${t.card.is_red ? 'red' : ''}">
              <div class="text-xs font-black leading-none">${t.card.rank}</div>
              <div class="text-2xl text-center leading-none">${t.card.suit_icon}</div>
              <div class="text-xs font-black leading-none self-end rotate-180">${t.card.rank}</div>
            </div>
          </div>
        `).join('');
        centerStageHtml = `<div class="relative w-48 h-44 flex items-center justify-center">${playedHtml}</div>`;
      }

      const handCards = st.my_hand || [];
      const overlapPx = handCards.length > 9 ? -15 : (handCards.length > 6 ? -10 : -4);
      const handHtml = handCards.map((c, idx) => `
        <button
          onclick="hokmPlayCard('${c.code}')"
          style="margin-left: ${idx === 0 ? '0px' : overlapPx + 'px'}; z-index: ${idx + 1};"
          class="playing-card w-[52px] h-[78px] shrink-0 transition-transform ${c.is_red ? 'red' : ''} ${isMyTurn ? 'hover:-translate-y-2.5 active:-translate-y-3 border-amber-400' : ''}"
        >
          <div class="text-sm font-black leading-none text-left">${c.rank}</div>
          <div class="text-2xl text-center leading-none">${c.suit_icon}</div>
          <div class="text-xs font-black leading-none text-right">${c.rank}</div>
        </button>
      `).join('');

      root.innerHTML = `
        <div class="flex-1 p-1.5 flex flex-col overflow-hidden">
          <div class="persian-carpet flex flex-col justify-between p-2 overflow-hidden">
            <div class="carpet-medallion"></div>

            <div class="z-20 flex justify-between items-start gap-1">
              <div class="glass-panel px-2 py-1 rounded-xl text-[10px] font-extrabold">
                <div>${T().trump}: <span class="bg-white text-black px-1 rounded">${st.trump_icon}</span></div>
                <div class="text-amber-300">${T().sets}: ${st.our_sets} - ${st.their_sets}</div>
              </div>

              ${renderPlayerRectCard(topSeat)}

              <button onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold">${T().backMenu}</button>
            </div>

            <div class="z-20 flex-1 flex items-center justify-between px-0.5 min-h-[150px]">
              <div class="flex flex-col items-center gap-1">
                ${rightSeat ? renderPlayerRectCard(rightSeat) : ''}
              </div>

              <div class="flex-1 flex flex-col items-center justify-center">
                <div class="mb-1 flex items-center gap-1">
                  <span class="text-[10px] font-bold text-rose-200">${T().oppTricks}:</span>
                  ${renderRealFaceDownTricks(st.their_tricks)}
                </div>
                ${centerStageHtml}
              </div>

              <div class="flex flex-col items-center gap-1">
                ${leftSeat ? renderPlayerRectCard(leftSeat) : ''}
              </div>
            </div>

            <div class="z-20 flex flex-col items-center gap-1">
              <div class="flex items-center gap-1.5">
                <span class="text-[10px] font-extrabold text-emerald-300">${T().ourTricks} (${st.our_tricks}/7):</span>
                ${renderRealFaceDownTricks(st.our_tricks)}
              </div>

              ${hokmError ? `<div class="bg-rose-600/90 px-3 py-0.5 rounded-lg text-[11px] font-bold">${hokmError}</div>` : ''}

              <div class="ltr-grid w-full flex justify-center items-end py-1 px-1 overflow-hidden">
                ${handHtml}
              </div>

              <div class="w-full flex items-center justify-between gap-1 px-1">
                ${renderPlayerRectCard(bottomSeat)}

                <div class="flex items-center gap-1">
                  <button onclick="hokmToggleMic()" class="${myMicActive ? 'btn-success' : 'glass-panel'} px-2.5 py-1.5 rounded-xl text-xs font-bold">
                    ${myMicActive ? T().micOn : T().micOff}
                  </button>
                  <button onclick="hokmSendReaction('🔥')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">🔥</button>
                  <button onclick="hokmSendReaction('😂')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">😂</button>
                  <button onclick="hokmSendReaction('👏')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">👏</button>
                </div>
              </div>

              <div class="w-full flex gap-1 px-1">
                <input id="hokmChatInp" type="text" maxlength="40" placeholder="${T().chatPlaceholder}" onkeydown="if(event.key==='Enter')hokmSendCustomChat()" class="flex-1 px-2.5 py-1 rounded-xl glass-soft text-white text-[11px]" />
                <button onclick="hokmSendCustomChat()" class="btn-primary px-3 py-1 rounded-xl text-[11px] font-bold">${T().sendBtn}</button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    /* ═══════════ بازی ۲۰۴۸ با اسکرول لمسی ═══════════ */
    let b2048 = null, s2048 = 0, t2048X = 0, t2048Y = 0;
    const TILE_COLORS_2048 = {
      0:    "bg-white/5 text-transparent border-white/5",
      2:    "bg-sky-500/80 text-white border-sky-300",
      4:    "bg-blue-600/85 text-white border-blue-300",
      8:    "bg-emerald-600/85 text-white border-emerald-300",
      16:   "bg-amber-500/90 text-black border-amber-200",
      32:   "bg-orange-600/90 text-white border-orange-300",
      64:   "bg-rose-600/90 text-white border-rose-300",
      128:  "bg-purple-600/90 text-white border-purple-300",
      256:  "bg-fuchsia-600/90 text-white border-fuchsia-300",
      512:  "bg-indigo-600/90 text-white border-indigo-300",
      1024: "bg-cyan-500/95 text-black border-white",
      2048: "bg-yellow-400 text-black border-white shadow-[0_0_20px_#facc15]"
    };
    function init2048() { b2048 = Array(4).fill(0).map(() => Array(4).fill(0)); s2048 = 0; addTile2048(); addTile2048(); }
    function addTile2048() {
      const emp = [];
      for (let r=0;r<4;r++) for (let c=0;c<4;c++) if (!b2048[r][c]) emp.push([r,c]);
      if (emp.length) { const [r,c] = emp[Math.floor(Math.random()*emp.length)]; b2048[r][c] = Math.random() < 0.9 ? 2 : 4; }
    }
    function move2048(dir) {
      const rot = m => m[0].map((_, i) => m.map(row => row[i]).reverse());
      let b = b2048.map(r => [...r]);
      if (dir==='up') b = rot(rot(rot(b)));
      if (dir==='right') b = b.map(r => r.reverse());
      if (dir==='down') b = rot(b);
      let moved = false;
      b = b.map(row => {
        let arr = row.filter(Boolean), out = [];
        for (let i=0;i<arr.length;i++) {
          if (arr[i]===arr[i+1]) { out.push(arr[i]*2); s2048+=arr[i]*2; i++; } else out.push(arr[i]);
        }
        while (out.length<4) out.push(0);
        if (out.join(',') !== row.join(',')) moved = true;
        return out;
      });
      if (dir==='up') b = rot(b);
      if (dir==='right') b = b.map(r => r.reverse());
      if (dir==='down') b = rot(rot(rot(b)));
      if (moved) { b2048 = b; addTile2048(); render2048(document.getElementById('app')); }
    }
    function render2048(root) {
      if (!b2048) init2048();
      const cells = b2048.flat().map(v => {
        const cls = TILE_COLORS_2048[v] || TILE_COLORS_2048[2048];
        return `<div class="aspect-square rounded-2xl border flex items-center justify-center font-black text-2xl ${cls}">${v || ''}</div>`;
      }).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.g2048)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2.5 rounded-2xl flex justify-between items-center">
            <span class="font-extrabold text-sm">${T().score}: <b class="text-amber-300">${s2048}</b></span>
            <button onclick="init2048();render()" class="btn-success px-3 py-1 rounded-xl text-xs font-bold">${T().restart}</button>
          </div>
          <div id="board2048" class="ltr-grid grid grid-cols-4 gap-2.5 glass-panel p-3.5 rounded-3xl touch-none">${cells}</div>
          <p class="text-center text-xs text-slate-300 font-bold">${T().swipeHint}</p>
        </div>
      `;
      const el = document.getElementById('board2048');
      if (el) {
        el.ontouchstart = e => { t2048X = e.changedTouches[0].clientX; t2048Y = e.changedTouches[0].clientY; };
        el.ontouchend = e => {
          const dx = e.changedTouches[0].clientX - t2048X, dy = e.changedTouches[0].clientY - t2048Y;
          if (Math.max(Math.abs(dx), Math.abs(dy)) > 25) {
            if (Math.abs(dx) > Math.abs(dy)) move2048(dx > 0 ? 'right' : 'left');
            else move2048(dy > 0 ? 'down' : 'up');
          }
        };
      }
    }

    /* ═══════════ پازل ۱۵ با اسکرول لمسی ═══════════ */
    let spz = null, spzX = 0, spzY = 0;
    function initSpz() { spz = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0].sort(() => Math.random()-0.5); }
    window.clickSpz = function(i) {
      const emp = spz.indexOf(0);
      if (Math.abs(Math.floor(i/4)-Math.floor(emp/4))+Math.abs((i%4)-(emp%4))===1) {
        [spz[i], spz[emp]] = [spz[emp], spz[i]]; renderSpuzzle(document.getElementById('app'));
      }
    };
    function swipeSpz(dir) {
      const emp = spz.indexOf(0), r = Math.floor(emp/4), c = emp%4;
      let target = -1;
      if (dir === 'up' && r < 3) target = (r+1)*4 + c;
      if (dir === 'down' && r > 0) target = (r-1)*4 + c;
      if (dir === 'left' && c < 3) target = r*4 + (c+1);
      if (dir === 'right' && c > 0) target = r*4 + (c-1);
      if (target >= 0) window.clickSpz(target);
    }
    function renderSpuzzle(root) {
      if (!spz) initSpz();
      const cells = spz.map((v,i) => `<button onclick="clickSpz(${i})" class="aspect-square rounded-2xl font-black text-xl ${v ? 'btn-primary' : 'bg-white/5'}">${v || ''}</button>`).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.spuzzle)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="flex justify-end"><button onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-xl font-bold text-xs">${T().restart}</button></div>
          <div id="spzBoard" class="ltr-grid grid grid-cols-4 gap-2 glass-panel p-3.5 rounded-3xl touch-none">${cells}</div>
          <p class="text-center text-xs text-slate-300 font-bold">${T().swipeHint}</p>
        </div>
      `;
      const el = document.getElementById('spzBoard');
      if (el) {
        el.ontouchstart = e => { spzX = e.changedTouches[0].clientX; spzY = e.changedTouches[0].clientY; };
        el.ontouchend = e => {
          const dx = e.changedTouches[0].clientX - spzX, dy = e.changedTouches[0].clientY - spzY;
          if (Math.max(Math.abs(dx), Math.abs(dy)) > 25) {
            if (Math.abs(dx) > Math.abs(dy)) swipeSpz(dx > 0 ? 'right' : 'left');
            else swipeSpz(dy > 0 ? 'down' : 'up');
          }
        };
      }
    }

    /* ═══════════ دوز با دایره‌های رنگی ═══════════ */
    const DOOZ_COLORS = [
      { id: 'rose',   cls: 'bg-rose-500 shadow-[0_0_12px_#f43f5e]' },
      { id: 'cyan',   cls: 'bg-cyan-400 shadow-[0_0_12px_#22d3ee]' },
      { id: 'emerald',cls: 'bg-emerald-400 shadow-[0_0_12px_#34d399]' },
      { id: 'amber',  cls: 'bg-amber-400 shadow-[0_0_12px_#fbbf24]' },
      { id: 'purple', cls: 'bg-purple-500 shadow-[0_0_12px_#a855f7]' }
    ];
    let doozB = null, doozTurn = 0, doozWin = null, doozMode = 'dooz', myDoozColorIdx = 0;
    function initDooz(m) { doozMode = m; const sz = m === 'doz4p' ? 5 : 3; doozB = Array(sz*sz).fill(null); doozTurn = 0; doozWin = null; }
    window.pickDoozColor = function(idx) { myDoozColorIdx = idx; initDooz(doozMode); renderDooz(document.getElementById('app'), doozMode); };
    window.clickDooz = function(i) {
      if (doozB[i] !== null || doozWin !== null) return;
      const numP = doozMode === 'doz4p' ? 4 : 2;
      const sz = doozMode === 'doz4p' ? 5 : 3, need = doozMode === 'doz4p' ? 4 : 3;
      const colorIdx = (myDoozColorIdx + doozTurn) % DOOZ_COLORS.length;
      doozB[i] = colorIdx;
      for (let r=0;r<sz;r++) for (let c=0;c<sz;c++) for (const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
        let ok = true;
        for (let k=0;k<need;k++) { const nr=r+dr*k, nc=c+dc*k; if (nr<0||nr>=sz||nc<0||nc>=sz||doozB[nr*sz+nc]!==colorIdx) { ok=false; break; } }
        if (ok) doozWin = colorIdx;
      }
      if (doozWin === null) doozTurn = (doozTurn + 1) % numP;
      renderDooz(document.getElementById('app'), doozMode);
    };
    function renderDooz(root, mode) {
      if (!doozB || doozMode !== mode) initDooz(mode);
      const sz = mode === 'doz4p' ? 5 : 3;
      const colorPickerHtml = DOOZ_COLORS.map((c, idx) => `
        <button onclick="pickDoozColor(${idx})" class="w-7 h-7 rounded-full ${c.cls} border-2 ${myDoozColorIdx === idx ? 'border-white scale-110' : 'border-transparent opacity-60'}"></button>
      `).join('');
      const cells = doozB.map((v,i) => `
        <button onclick="clickDooz(${i})" class="aspect-square rounded-full glass-soft flex items-center justify-center p-2">
          ${v !== null ? `<div class="w-full h-full rounded-full ${DOOZ_COLORS[v].cls}"></div>` : ''}
        </button>
      `).join('');
      root.innerHTML = `
        ${renderTopBar(mode==='doz4p' ? T().games.doz4p : T().games.dooz)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel p-3 rounded-2xl flex justify-between items-center">
            <span class="text-xs font-extrabold">${T().pickColor}</span>
            <div class="flex gap-2">${colorPickerHtml}</div>
          </div>
          <div class="ltr-grid grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-3 glass-panel p-4 rounded-3xl">${cells}</div>
          <button onclick="initDooz('${mode}');render()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().restart}</button>
        </div>
      `;
    }

    /* ═══════════ حدس عدد همگانی گروه ═══════════ */
    let guessRoomData = null;
    async function callGuessApi(action, extra = {}) {
      if (action === 'state' && isUserTyping()) return;
      try {
        const res = await fetch('/api/guess/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            session: String(parsedChat),
            uid: Number(uid),
            name: myName,
            action: action,
            ...extra
          })
        });
        const data = await res.json();
        if (data.ok === false && data.error && tg?.showAlert) tg.showAlert(data.error);
        if (data.room && !(action === 'state' && isUserTyping())) {
          guessRoomData = data.room;
          drawGuessRoom(document.getElementById('app'));
        }
      } catch (e) {}
    }

    window.createGroupGuessRange = function() {
      const lo = Number(document.getElementById('gMinInp')?.value || 1);
      const hi = Number(document.getElementById('gMaxInp')?.value || 500);
      callGuessApi('create', { min_val: lo, max_val: hi });
      if (guessPollTimer) clearInterval(guessPollTimer);
      guessPollTimer = setInterval(() => callGuessApi('state'), 2500);
    };
    window.sendGroupGuessVal = function() {
      const inp = document.getElementById('gValInp');
      const v = Number(inp?.value);
      if (inp && inp.value.trim() !== '' && !isNaN(v)) {
        inp.value = '';
        inp.blur();
        callGuessApi('guess', { guess_val: v });
      }
    };
    window.restartGroupGuess = function() { callGuessApi('restart'); };

    function renderGuess(root) {
      if (!guessRoomData) {
        root.innerHTML = `
          ${renderTopBar(T().games.guess)}
          <div class="flex-1 flex flex-col justify-center p-4">
            <div class="glass-panel p-5 rounded-3xl text-center">
              <div class="grid grid-cols-2 gap-3 my-4">
                <div>
                  <label class="text-xs text-slate-300 font-bold block mb-1">${T().fromNum}</label>
                  <input id="gMinInp" type="number" value="1" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                </div>
                <div>
                  <label class="text-xs text-slate-300 font-bold block mb-1">${T().toNum}</label>
                  <input id="gMaxInp" type="number" value="1000" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                </div>
              </div>
              <button onclick="createGroupGuessRange()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().createGame}</button>
            </div>
          </div>
        `;
        return;
      }
      drawGuessRoom(root);
    }

    function drawGuessRoom(root) {
      if (!root || currentGame !== 'guess' || !guessRoomData) return;
      const r = guessRoomData;
      const isHost = Number(r.host_id) === Number(uid);
      const histHtml = (r.history || []).map(h => `
        <div class="glass-soft px-3 py-1.5 rounded-xl flex justify-between text-xs font-bold">
          <span>👤 ${h.name}: <b>${h.val}</b></span>
          <span class="text-amber-300">${h.hint}</span>
        </div>
      `).join('');

      root.innerHTML = `
        ${renderTopBar(`${T().games.guess} (${r.min}-${r.max})`)}
        <div class="flex-1 flex flex-col justify-between p-4 overflow-hidden">
          <div class="glass-panel p-4 rounded-3xl text-center">
            ${r.winner_id ? `
              <div class="p-4 rounded-2xl bg-emerald-600/30 border border-emerald-400 my-2">
                <div class="text-lg font-black text-emerald-300">🎉 ${T().winner}: ${r.winner_name} (${r.secret_revealed})</div>
              </div>
            ` : `
              <div class="flex gap-2 my-2">
                <input id="gValInp" type="number" placeholder="${r.min} - ${r.max}" onkeydown="if(event.key==='Enter')sendGroupGuessVal()" class="flex-1 p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                <button onclick="sendGroupGuessVal()" class="btn-success px-5 rounded-xl font-black">${T().submitBtn}</button>
              </div>
            `}
            <button onclick="shareTableInline('guess', '${r.min}-${r.max}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs mt-2">${T().optShare}</button>
          </div>

          <div class="flex-1 overflow-y-auto my-3 flex flex-col gap-1.5">${histHtml}</div>

          <div class="flex gap-2">
            ${r.winner_id && isHost ? `<button onclick="restartGroupGuess()" class="btn-success flex-1 py-3.5 rounded-2xl font-black">${T().playAgainBtn}</button>` : ''}
            <button onclick="guessRoomData=null;nav('hub')" class="btn-danger flex-1 py-3.5 rounded-2xl font-black">${T().backMenu}</button>
          </div>
        </div>
      `;
    }

    /* ═══════════ سنگ کاغذ قیچی ═══════════ */
    let rpsU = 0, rpsB = 0, rpsMsg = '...';
    window.playRPS = function(c) {
      const target = lobbyState.rpsTargetWins || 3;
      if (rpsU >= target || rpsB >= target) { rpsU = 0; rpsB = 0; }
      const b = ['rock','paper','scissors'][Math.floor(Math.random()*3)];
      if (c===b) rpsMsg = '=';
      else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) {
        rpsU++; rpsMsg = rpsU >= target ? `🏆 ${T().winner}!` : '+1';
      } else {
        rpsB++; rpsMsg = rpsB >= target ? '❌' : '-1';
      }
      renderRPS(document.getElementById('app'));
    };
    function renderRPS(root) {
      const target = lobbyState.rpsTargetWins || 3;
      root.innerHTML = `
        ${renderTopBar(`${T().games.rps} (${target})`)}
        <div class="flex-1 flex flex-col justify-between p-4 text-center">
          <div class="glass-panel p-6 rounded-3xl">
            <p class="text-3xl font-black mb-3">${rpsU} — ${rpsB}</p>
            <div class="p-3 rounded-xl glass-soft font-bold text-sm">${rpsMsg}</div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <button onclick="playRPS('rock')" class="btn-primary py-5 rounded-2xl font-black">🪨 ${T().rock}</button>
            <button onclick="playRPS('paper')" class="btn-success py-5 rounded-2xl font-black">📄 ${T().paper}</button>
            <button onclick="playRPS('scissors')" class="btn-danger py-5 rounded-2xl font-black">✂️ ${T().scissors}</button>
          </div>
          <div></div>
        </div>
      `;
    }

    /* ═══════════ سایر بازی‌ها ═══════════ */
    let c4B = null, c4Turn = 1, c4Win = 0;
    function initC4() { c4B = Array(6).fill(0).map(()=>Array(7).fill(0)); c4Turn = 1; c4Win = 0; }
    window.dropC4 = function(col) {
      if (c4Win) return;
      for (let r=5;r>=0;r--) if (!c4B[r][col]) {
        c4B[r][col] = c4Turn;
        for (let rr=0;rr<6;rr++) for (let cc=0;cc<7;cc++) for (const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
          let ok=true; for (let k=0;k<4;k++) { const nr=rr+dr*k, nc=cc+dc*k; if (nr<0||nr>=6||nc<0||nc>=7||c4B[nr][nc]!==c4Turn){ok=false;break;} }
          if (ok) c4Win = c4Turn;
        }
        if (!c4Win) c4Turn = c4Turn===1?2:1;
        renderConnect4(document.getElementById('app')); return;
      }
    };
    function renderConnect4(root) {
      if (!c4B) initC4();
      const cells = c4B.map(row=>row.map((v,c)=>`<button onclick="dropC4(${c})" class="aspect-square rounded-full ${v===1?'btn-danger':v===2?'btn-success':'glass-soft'}"></button>`).join('')).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.connect4)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold text-sm">${c4Win ? `🏆 P${c4Win}` : `${T().turn}: P${c4Turn}`}</div>
          <div class="ltr-grid grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${cells}</div>
          <button onclick="initC4();render()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().restart}</button>
        </div>
      `;
    }

    let sgGrid = null, sgScore = 0;
    const sgCls = ['btn-danger', 'btn-primary', 'btn-success', 'bg-amber-500'];
    function initSg() { sgGrid = Array(8).fill(0).map(()=>Array(8).fill(0).map(()=>Math.floor(Math.random()*4))); sgScore = 0; }
    window.clickSg = function(r0, c0) {
      const target = sgGrid[r0][c0], q = [[r0,c0]], vis = new Set([r0+','+c0]), grp = [[r0,c0]];
      while (q.length) {
        const [r,c] = q.pop();
        for (const [dr,dc] of [[0,1],[0,-1],[1,0],[-1,0]]) {
          const nr=r+dr, nc=c+dc, k=nr+','+nc;
          if (nr>=0 && nr<8 && nc>=0 && nc<8 && !vis.has(k) && sgGrid[nr][nc]===target) { vis.add(k); grp.push([nr,nc]); q.push([nr,nc]); }
        }
      }
      if (grp.length < 2) return;
      grp.forEach(([r,c]) => sgGrid[r][c] = Math.floor(Math.random()*4)); sgScore += grp.length * 10; renderSameGame(document.getElementById('app'));
    };
    function renderSameGame(root) {
      if (!sgGrid) initSg();
      const cells = sgGrid.map((row,r)=>row.map((v,c)=>`<button onclick="clickSg(${r},${c})" class="aspect-square rounded-lg ${sgCls[v]}"></button>`).join('')).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.samegame)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold">${T().score}: ${sgScore}</div>
          <div class="ltr-grid grid grid-cols-8 gap-1.5 glass-panel p-3 rounded-3xl">${cells}</div>
          <div></div>
        </div>
      `;
    }

    let memCards = null, memFlip = [], memMatch = [];
    function initMem() { const s = ['🍎','💎','🔥','⚡','👑','🎯','🚀','🌈']; memCards = [...s,...s].sort(()=>Math.random()-0.5); memFlip = []; memMatch = []; }
    window.clickMem = function(i) {
      if (memFlip.length===2 || memFlip.includes(i) || memMatch.includes(i)) return;
      memFlip.push(i); renderMemory(document.getElementById('app'));
      if (memFlip.length===2) {
        const [a,b] = memFlip;
        if (memCards[a]===memCards[b]) { memMatch.push(a,b); memFlip = []; renderMemory(document.getElementById('app')); }
        else setTimeout(()=>{ memFlip=[]; renderMemory(document.getElementById('app')); }, 600);
      }
    };
    function renderMemory(root) {
      if (!memCards) initMem();
      const cells = memCards.map((v,i)=>{ const open = memFlip.includes(i) || memMatch.includes(i); return `<button onclick="clickMem(${i})" class="aspect-square rounded-2xl font-black text-2xl ${open?'btn-success':'glass-panel'}">${open?v:'?'}</button>`; }).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.memory)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="ltr-grid grid grid-cols-4 gap-2.5 glass-panel p-3.5 rounded-3xl my-auto">${cells}</div>
        </div>
      `;
    }

    const sentences = ["آب از سرچشمه گل آلود است", "به عمل کار برآید به سخندانی نیست", "نابرده رنج گنج میسر نمیشود"];
    let targetSentence = sentences[0], typeStart = 0, typeMsg = '';
    function initTyping() { targetSentence = sentences[Math.floor(Math.random()*sentences.length)]; typeStart = Date.now(); typeMsg = ''; }
    window.checkTyping = function() {
      const val = document.getElementById('typeInput').value.trim();
      if (val === targetSentence) typeMsg = `🏆 ${((Date.now() - typeStart)/1000).toFixed(1)}s`; else typeMsg = '❌';
      renderTyping(document.getElementById('app'));
    };
    function renderTyping(root) {
      if (!typeStart) initTyping();
      root.innerHTML = `
        ${renderTopBar(T().games.typing)}
        <div class="flex-1 flex flex-col justify-center p-4">
          <div class="glass-panel p-5 rounded-3xl">
            <p class="p-3.5 rounded-2xl glass-soft font-bold text-emerald-300 mb-4 text-center">${targetSentence}</p>
            <input id="typeInput" type="text" class="w-full p-3.5 rounded-2xl glass-soft text-white mb-3 text-center" />
            ${typeMsg ? `<p class="font-bold text-amber-300 mb-3 text-center">${typeMsg}</p>` : ''}
            <button onclick="checkTyping()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().submitBtn}</button>
          </div>
        </div>
      `;
    }

    const wordsList = ["تلگرام", "راینو", "پایتون", "امپراتور", "کهکشان"];
    let hmWord = "", hmGuessed = [], hmLives = 10;
    function initHangman() { hmWord = wordsList[Math.floor(Math.random()*wordsList.length)]; hmGuessed = []; hmLives = 10; }
    window.guessLetter = function(ch) {
      if (hmGuessed.includes(ch) || hmLives <= 0) return;
      hmGuessed.push(ch); if (!hmWord.includes(ch)) hmLives--; renderHangman(document.getElementById('app'));
    };
    function renderHangman(root) {
      if (!hmWord) initHangman();
      const display = hmWord.split('').map(c => hmGuessed.includes(c) ? c : '_').join(' ');
      const kbHtml = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی".split('').map(ch => `<button onclick="guessLetter('${ch}')" class="py-2 rounded-xl font-bold ${hmGuessed.includes(ch) ? 'opacity-30 glass-soft' : 'btn-primary'}">${ch}</button>`).join('');
      root.innerHTML = `
        ${renderTopBar(T().games.hangman)}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel p-5 rounded-3xl text-center">
            <div class="text-xs text-rose-300 font-bold">❤️ ${hmLives}</div>
            <div class="text-3xl font-black tracking-widest my-3">${display}</div>
          </div>
          <div class="grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${kbHtml}</div>
        </div>
      `;
    }

    async function renderGardoneAnim(root) {
      root.innerHTML = `
        ${renderTopBar()}
        <div class="flex-1 flex flex-col justify-between p-4 text-center">
          <div class="glass-panel rounded-3xl p-8 border-2 border-indigo-400 my-auto"><div id="wheelSlot" class="text-3xl font-black text-amber-300">...</div></div>
          <div id="wheelWinners" class="glass-panel p-4 rounded-2xl flex flex-col gap-2 text-sm max-h-52 overflow-y-auto"></div>
        </div>
      `;
      let allNames = ['Player 1', 'Player 2'], winNames = ['Player 1'];
      if (parsedChat) {
        try {
          const res = await fetch('/api/gardone/' + parsedChat);
          const data = await res.json();
          if (data.names?.length) allNames = data.names;
          if (data.winners?.length) winNames = data.winners;
        } catch (e) {}
      }
      const slot = document.getElementById('wheelSlot'), wBox = document.getElementById('wheelWinners');
      let idx = 0;
      function nextWinner() {
        if (idx >= winNames.length) { slot.innerText = "🏆"; return; }
        let elapsed = 0; const target = winNames[idx];
        const timer = setInterval(() => {
          slot.innerText = allNames[Math.floor(Math.random() * allNames.length)];
          elapsed += 70;
          if (elapsed >= 1600) {
            clearInterval(timer); idx++; slot.innerText = `🥇 ${target}`;
            const row = document.createElement('div');
            row.className = "p-2 rounded-xl glass-soft font-bold text-emerald-300";
            row.innerText = `#${idx} - ${target}`;
            wBox.appendChild(row);
            setTimeout(nextWinner, 1200);
          }
        }, 70);
      }
      setTimeout(nextWinner, 400);
    }

/* ═══════════════════════════════════════════════════════════════════════════
       پلتفرم اجتماعی راینو: اتاق‌های صوتی (SUGO Style) + پروفایل کاربری + فروشگاه VIP
       ═══════════════════════════════════════════════════════════════════════════ */
    let spState = null;
    let activeVoiceRoom = null;
    let minimizedVoiceRoom = null;
    let viewedProfileData = null;
    let spMsg = '';
    let spErr = '';
    let vrSheet = ''; // '' | 'manage' | 'modes' | 'details' | 'gifts' | 'edit_room'
    let vrPollTimer = null;
    let storeTab = 'subs'; // subs | rings | gifts

    async function callSocialApi(action = 'state', extra = {}) {
      try {
        const res = await fetch('/api/social/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            uid: Number(uid),
            name: myName,
            username: myUsername,
            photo: myPhoto,
            action: action,
            ...extra
          })
        });
        const data = await res.json();
        spMsg = data.msg || '';
        spErr = data.ok === false ? (data.error || '') : '';

        if (data.need_pin) {
          const pin = prompt(data.error || 'رمز اتاق صوتی را وارد کنید:');
          if (pin !== null) {
            return callSocialApi('join_room', { room_id: data.room_id, pin_code: pin });
          }
          return;
        }
        if (data.invoice_link && tg?.openInvoice) {
          tg.openInvoice(data.invoice_link, () => callSocialApi('state'));
          return;
        } else if (data.invoice_link) {
          window.open(data.invoice_link, '_blank');
        }
        if (data.state) spState = data.state;
        if (data.viewed_profile) viewedProfileData = data.viewed_profile;
        if (data.active_room) {
          activeVoiceRoom = data.active_room;
          currentGame = 'voice_room_live';
        }
        if (data.left) {
          activeVoiceRoom = null;
          minimizedVoiceRoom = null;
          if (vrPollTimer) { clearInterval(vrPollTimer); vrPollTimer = null; }
          currentGame = 'voice_hub';
        }
        render();
      } catch (e) {}
    }

    window.openMyVoiceRoomQuick = async function() {
      if (!spState) await callSocialApi('state');
      if (spState?.me?.room) {
        callSocialApi('join_room', { room_id: spState.me.room.room_id });
      } else {
        currentGame = 'voice_hub';
        vrSheet = 'edit_room';
        render();
      }
    };

    window.openUserProfileModal = function(targetUid) {
      viewedProfileData = null;
      currentGame = 'sp_profile';
      callSocialApi('view_profile', { target_uid: Number(targetUid) });
    };

    window.vrOpenExitPrompt = function() {
      vrSheet = 'exit_confirm';
      drawLiveVoiceRoom(document.getElementById('app'));
    };

    window.vrKeepMinimized = function() {
      minimizedVoiceRoom = activeVoiceRoom;
      vrSheet = '';
      currentGame = 'voice_hub';
      render();
    };

    /* ۱. صفحه لیست اتاق‌های صوتی (مشابه تصویر ۶ اپلیکیشن SUGO) */
    function renderVoiceHub(root) {
      if (!spState) {
        root.innerHTML = `<div class="p-6 text-center"><div class="glass-panel p-6 rounded-3xl font-bold">در حال بارگذاری اتاق‌های صوتی...</div></div>`;
        callSocialApi('state');
        return;
      }
      const me = spState.me;
      const rooms = spState.rooms || [];

      const roomsGridHtml = rooms.map(r => `
        <div onclick="callSocialApi('join_room',{room_id:${r.room_id}})" class="arcade-card cursor-pointer">
          <img src="${r.photo || '/api/banner/hub.png'}" onerror="this.src='/api/banner/hub.png'" class="arcade-card-bg" />
          <div class="arcade-card-overlay">
            <div class="flex justify-between items-start">
              <span class="px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-black text-amber-300 border border-amber-400/30">
                Lv.${r.level || 1}
              </span>
              ${r.is_locked ? `<span class="w-7 h-7 rounded-full bg-rose-600/90 flex items-center justify-center text-xs shadow">🔒</span>` : `<span class="px-2 py-0.5 rounded-full bg-emerald-500/80 text-[9px] font-black">LIVE</span>`}
            </div>
            <div>
              <div class="font-black text-sm text-white truncate drop-shadow">${r.title}</div>
              <div class="text-[10px] text-slate-300 truncate mb-1.5">${r.description || ''}</div>
              <div class="flex items-center justify-between ltr-grid">
                <span class="pill-mode-pve">${r.category || 'Friendship'}</span>
                <span class="pill-players">👥 ${r.online_count || 1}</span>
              </div>
            </div>
          </div>
        </div>
      `).join('');

      const editModalHtml = vrSheet === 'edit_room' ? renderEditRoomModal(me.room) : '';

      root.innerHTML = `
        ${editModalHtml}
        ${renderMinimizedFloatingWidget()}
        <div class="glass-panel mx-3 mb-2 px-3.5 py-2.5 rounded-3xl flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3 text-sm font-black">
            <span class="text-white border-b-2 border-purple-400 pb-0.5">Rooms</span>
            <button onclick="nav('hub')" class="text-slate-400 hover:text-white">Games</button>
            <button onclick="nav('sp_store')" class="text-slate-400 hover:text-white">VIP Store</button>
          </div>
          <div class="flex items-center gap-1.5">
            <button onclick="vrSheet='edit_room';renderVoiceHub(document.getElementById('app'))" class="btn-primary px-3 py-1.5 rounded-xl text-xs font-black">
              ${me.room ? '⚙️ اتاق من' : '➕ ساخت اتاق'}
            </button>
            <button onclick="openUserProfileModal(${uid})" class="glass-soft px-2.5 py-1.5 rounded-xl text-xs font-bold">👤</button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-3 pb-24">
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center mb-3">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center mb-3">${spErr}</div>` : ''}

          ${me.room ? `
            <div onclick="callSocialApi('join_room',{room_id:${me.room.room_id}})" class="glass-panel p-3 rounded-3xl mb-3 flex items-center justify-between border border-purple-400/40 cursor-pointer">
              <div class="flex items-center gap-3 min-w-0">
                <img src="${me.room.photo || myPhoto || '/api/banner/hub.png'}" class="w-12 h-12 rounded-2xl object-cover border border-amber-400" />
                <div class="min-w-0">
                  <div class="text-xs font-black text-amber-300 truncate">👑 اتاق شخصی شما: ${me.room.title}</div>
                  <div class="text-[10px] text-slate-300">ID: ${me.room.room_id} • ${me.room.is_locked ? '🔒 قفل‌شده' : '🟢 عمومی'} • ${me.room.mic_count} مایک</div>
                </div>
              </div>
              <span class="btn-success px-3 py-1.5 rounded-xl text-xs font-black shrink-0">ورود ◀</span>
            </div>
          ` : ''}

          <div class="grid grid-cols-2 gap-3">
            ${roomsGridHtml || `<div class="col-span-2 glass-panel p-8 rounded-3xl text-center text-xs text-slate-300">هنوز اتاق صوتی ساخته نشده است! اولین اتاق را شما بسازید.</div>`}
          </div>
        </div>
      `;
    }

    function renderEditRoomModal(rm) {
      const me = spState?.me || {};
      return `
        <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div class="glass-panel p-4 rounded-3xl w-full max-w-sm space-y-2.5 text-xs max-h-[90vh] overflow-y-auto border border-purple-400/40">
            <h3 class="text-sm font-black text-amber-300 text-center">🎙️ تنظیمات اتاق صوتی شخصی شما</h3>
            <div>
              <label class="block text-[11px] text-slate-300 mb-1">نام اتاق صوتی:</label>
              <input id="rm_title" type="text" value="${rm?.title || ('مجلس ' + myName)}" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
            </div>
            <div>
              <label class="block text-[11px] text-slate-300 mb-1">بیوگرافی / معرفی اتاق (Room Info):</label>
              <input id="rm_desc" type="text" value="${rm?.description || 'به اتاق صوتی خوش آمدید!'}" class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />
            </div>
            <div class="glass-soft p-2.5 rounded-2xl text-center">
              <label class="block text-[11px] text-amber-200 font-bold mb-1">📷 عکس کاور اتاق صوتی (آپلود از گالری):</label>
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'my_room_photo', 'prev_my_room_photo')" class="w-full text-[10px]" />
              <img id="prev_my_room_photo" src="${rm?.photo || ''}" class="${rm?.photo ? '' : 'hidden'} w-20 h-20 rounded-2xl object-cover mx-auto mt-2 border border-amber-400" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">تعداد میکروفون‌ها:</label>
                <select id="rm_mics" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
                  ${[1,2,6,8,10,12,15,20,24,30,36].map(n => `<option value="${n}" ${(rm?.mic_count||8)===n?'selected':''}>${n} Mic</option>`).join('')}
                </select>
              </div>
              <div>
                <label class="block text-[11px] text-slate-300 mb-1">دسته‌بندی:</label>
                <select id="rm_cat" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
                  <option value="Friendship">Friendship</option>
                  <option value="Families">Families</option>
                  <option value="PK Battle">PK Battle</option>
                  <option value="Music">Music</option>
                </select>
              </div>
            </div>

            <div class="glass-soft p-3 rounded-2xl space-y-2 border ${me.can_lock_room ? 'border-emerald-400/40' : 'border-rose-400/40'}">
              <div class="flex justify-between items-center">
                <span class="font-black text-amber-300">🔒 قفل کردن اتاق (ویژه اشتراک PRO+):</span>
                <input id="rm_lock" type="checkbox" ${rm?.is_locked ? 'checked' : ''} ${!me.can_lock_room ? 'disabled' : ''} class="w-4 h-4" />
              </div>
              ${!me.can_lock_room ? `<div class="text-[10px] text-rose-300">برای قفل کردن اتاق نیاز به اشتراک PRO، PLUS یا ULTRA دارید.</div>` : `
                <input id="rm_pin" type="text" value="${rm?.pin_code || ''}" placeholder="رمز عبور اتاق (مثلاً: 1234)" class="w-full p-2 rounded-xl bg-slate-900 text-white text-center font-bold" />
              `}
            </div>

            <div class="grid grid-cols-2 gap-2 pt-2">
              <button onclick="vrSheet='';callSocialApi('save_my_room',{title:document.getElementById('rm_title').value,description:document.getElementById('rm_desc').value,room_photo:window.uploadedImages['my_room_photo']||'',mic_count:Number(document.getElementById('rm_mics').value),category:document.getElementById('rm_cat').value,is_locked:document.getElementById('rm_lock').checked,pin_code:document.getElementById('rm_pin')?.value||''})" class="btn-success py-3 rounded-2xl font-black">💾 ذخیره و ورود</button>
              <button onclick="vrSheet='';render()" class="btn-danger py-3 rounded-2xl font-bold">انصراف</button>
            </div>
          </div>
        </div>
      `;
    }

    function renderMinimizedFloatingWidget() {
      if (!minimizedVoiceRoom || currentGame === 'voice_room_live') return '';
      return `
        <div onclick="activeVoiceRoom=minimizedVoiceRoom;minimizedVoiceRoom=null;currentGame='voice_room_live';render()" class="fixed top-20 left-3 z-40 w-20 h-24 rounded-2xl overflow-hidden border-2 border-purple-400 shadow-2xl cursor-pointer bg-slate-950">
          <img src="${minimizedVoiceRoom.photo || '/api/banner/hub.png'}" class="w-full h-16 object-cover" />
          <div class="bg-purple-900/90 text-[9px] font-black text-center py-1 truncate px-1">🎙️ ${minimizedVoiceRoom.title}</div>
        </div>
      `;
    }

    /* ۲. داخل اتاق صوتی زنده (مشابه تصاویر ۷ تا ۱۵ اپلیکیشن SUGO) */
    function startLiveVoiceRoom(root) {
      if (!activeVoiceRoom) { currentGame = 'voice_hub'; return render(); }
      drawLiveVoiceRoom(root);
      if (vrPollTimer) clearInterval(vrPollTimer);
      vrPollTimer = setInterval(() => {
        if (currentGame === 'voice_room_live' && activeVoiceRoom && !isUserTyping() && !vrSheet) {
          callSocialApi('room_op', { room_id: activeVoiceRoom.room_id, op: 'ping' });
        }
      }, 3500);
    }

    function drawLiveVoiceRoom(root) {
      if (!root || currentGame !== 'voice_room_live' || !activeVoiceRoom) return;
      const r = activeVoiceRoom;
      const me = spState?.me || {};
      const isRoomOwner = (Number(r.owner_id) === Number(uid)) || isOwner;

      const bgThemes = {
        lighthouse: "radial-gradient(circle at 50% 20%, #1e1b4b 0%, #090514 85%)",
        royal_stage: "radial-gradient(circle at 50% 15%, #581c87 0%, #1e1b4b 60%, #090514 95%)",
        crimson: "radial-gradient(circle at 50% 20%, #7f1d1d 0%, #111827 90%)",
        emerald: "radial-gradient(circle at 50% 20%, #065f46 0%, #090514 90%)"
      };
      const roomBgCss = bgThemes[r.bg_theme] || bgThemes.lighthouse;

      // چیدمان صندلی‌های میکروفون بر اساس تعداد (از ۱ تا ۳۶ مایک)
      const mc = r.mic_count || 8;
      const gridCols = mc === 1 ? 'grid-cols-1 max-w-[110px]' : (mc === 2 ? 'grid-cols-2 max-w-[220px]' : (mc <= 8 ? 'grid-cols-4' : (mc <= 15 ? 'grid-cols-5' : 'grid-cols-6')));
      const seatSize = mc <= 8 ? 'w-14 h-14 text-lg' : (mc <= 15 ? 'w-12 h-12 text-sm' : 'w-10 h-10 text-xs');

      let seatsHtml = '';
      for (let i = 1; i <= mc; i++) {
        const occ = (r.seats || {})[String(i)];
        const isLockedSeat = (r.locked_seats || []).includes(i);
        seatsHtml += `
          <div class="flex flex-col items-center gap-1">
            <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'take_seat',seat_idx:'${i}'})"
              style="${occ?.ring_css ? `box-shadow:${occ.ring_css};` : ''}"
              class="${seatSize} rounded-full ${occ ? 'bg-indigo-950 border-2 border-emerald-400' : 'bg-white/10 border border-white/25'} flex items-center justify-center relative overflow-hidden active:scale-95 transition">
              ${occ ? (occ.photo ? `<img src="${occ.photo}" class="w-full h-full object-cover" />` : `<span class="font-black">${(occ.name||'P')[0]}</span>`) : (isLockedSeat ? '🔒' : '➕')}
              ${occ?.muted ? `<span class="absolute bottom-0 right-0 bg-rose-600 text-[9px] rounded-full px-1">🔇</span>` : ''}
            </button>
            <div onclick="${occ ? `openUserProfileModal(${occ.uid})` : (isRoomOwner ? `callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_seat_lock',seat_idx:${i}})` : '')}" class="text-[10px] font-bold text-slate-200 truncate max-w-[64px] cursor-pointer">
              ${occ ? `${occ.name}` : `${i}`}
            </div>
          </div>
        `;
      }

      const membersAvatars = (r.visible_members || []).slice(0, 6).map(m => `
        <img onclick="openUserProfileModal(${m.uid})" src="${m.photo || '/api/banner/hub.png'}" title="${m.name}" class="w-7 h-7 rounded-full object-cover border border-amber-400/60 cursor-pointer" />
      `).join('');

      const chatsHtml = (r.chats || []).map(c => c.sys ? `
        <div class="px-3 py-1.5 rounded-2xl ${c.gift ? 'bg-amber-500/25 border border-amber-400/50 text-amber-200' : 'bg-teal-950/60 border border-teal-500/25 text-teal-300'} text-[11px] font-bold">
          ${c.text}
        </div>
      ` : `
        <div class="px-3 py-1.5 rounded-2xl bg-black/45 text-xs">
          <span onclick="openUserProfileModal(${c.uid})" class="font-black text-amber-300 cursor-pointer">${c.badge ? c.badge + ' ' : ''}${c.name}:</span>
          <span class="text-white mr-1">${c.text}</span>
        </div>
      `).join('');

      const imSeated = Object.values(r.seats || {}).some(s => s && Number(s.uid) === Number(uid));

      // شیت‌های کشویی (Room Management, Mic Modes, Room Details, Gifts, Keep/Exit)
      let modalSheetHtml = '';
      if (vrSheet === 'exit_confirm') {
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center gap-10">
            <div class="flex flex-col items-center gap-2">
              <button onclick="event.stopPropagation();vrKeepMinimized()" class="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-3xl shadow-[0_0_25px_#10b981]">🗗</button>
              <span class="font-black text-sm">Keep</span>
            </div>
            <div class="flex flex-col items-center gap-2">
              <button onclick="event.stopPropagation();callSocialApi('room_op',{room_id:${r.room_id},op:'leave_room'})" class="w-20 h-20 rounded-full bg-gradient-to-br from-rose-500 to-red-600 flex items-center justify-center text-3xl shadow-[0_0_25px_#f43f5e]">⏻</button>
              <span class="font-black text-sm">Exit</span>
            </div>
          </div>
        `;
      } else if (vrSheet === 'manage') {
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/65 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-4 border-t border-purple-400/40">
              <div class="flex justify-between items-center border-b border-white/10 pb-2 text-xs font-black">
                <span class="text-amber-300">🎛️ Room Management & Basic Tools</span>
                <button onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="text-slate-400">✖</button>
              </div>
              <div class="grid grid-cols-4 gap-3 text-center text-[11px] font-bold">
                <button onclick="vrSheet='modes';drawLiveVoiceRoom(document.getElementById('app'))" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">🎙️</span><span>Room Mode</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_lock_room'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">${r.is_locked ? '🔓' : '🔒'}</span><span>${r.is_locked ? 'Unlock' : 'Lock Room'}</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_auto_lock_mics'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">💺</span><span>Mic Lock</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'clear_chat'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">🧹</span><span>Delete Chat</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_music'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">🎵</span><span>Music</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_pk'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">⚔️</span><span>PK Battle</span></button>
                <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'change_bg',bg_theme:'royal_stage'});vrSheet=''" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">🌌</span><span>Stage BG</span></button>
                <button onclick="vrSheet='';nav('sp_store')" class="glass-soft p-3 rounded-2xl flex flex-col items-center gap-1"><span class="text-xl">🛍️</span><span>VIP Store</span></button>
              </div>
            </div>
          </div>
        `;
      } else if (vrSheet === 'modes') {
        const micOptions = [
          { n: 1, mode: 'normal', lbl: '1 Mic (Solo)' },
          { n: 2, mode: 'normal', lbl: '2 Mic (Couple)' },
          { n: 6, mode: 'normal', lbl: '6 Mic' },
          { n: 8, mode: 'pk',     lbl: '8 Mic (PK)' },
          { n: 10, mode: 'pk',    lbl: '10 Mic (PK)' },
          { n: 12, mode: 'theme', lbl: '12 Mic (Stage)' },
          { n: 15, mode: 'normal',lbl: '15 Mic' },
          { n: 20, mode: 'normal',lbl: '20 Mic' },
          { n: 24, mode: 'normal',lbl: '24 Mic' },
          { n: 30, mode: 'normal',lbl: '30 Mic' },
          { n: 36, mode: 'normal',lbl: '36 Mic (Mega)' }
        ];
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="bg-slate-950 rounded-t-3xl p-4 space-y-3 max-h-[75vh] overflow-y-auto border-t border-purple-400">
              <h3 class="text-sm font-black text-center text-amber-300">🎙️ انتخاب چیدمان میکروفون‌های اتاق (Voice Modes)</h3>
              <div class="grid grid-cols-3 gap-2.5 text-xs">
                ${micOptions.map(m => `
                  <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'change_layout',mic_count:${m.n},mic_mode:'${m.mode}'});vrSheet=''"
                    class="p-3 rounded-2xl border ${r.mic_count===m.n ? 'border-purple-400 bg-purple-950/60' : 'border-white/10 bg-white/5'} flex flex-col items-center gap-1.5">
                    <span class="px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 text-[9px] font-black">${m.mode.toUpperCase()}</span>
                    <span class="font-black text-white">${m.lbl}</span>
                  </button>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      } else if (vrSheet === 'details') {
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="bg-white text-slate-900 rounded-t-3xl p-5 space-y-4 max-h-[80vh] overflow-y-auto">
              <div class="flex justify-between items-center">
                <h3 class="font-black text-base">Room Details</h3>
                <button onclick="openUserProfileModal(${r.owner_id})" class="text-xs font-bold text-purple-700">👤 مشاهده پروفایل مالک</button>
              </div>
              <div class="flex items-center justify-between bg-slate-100 p-3 rounded-2xl">
                <div class="flex items-center gap-3">
                  <img src="${r.photo || '/api/banner/hub.png'}" class="w-14 h-14 rounded-2xl object-cover" />
                  <div>
                    <div class="font-black text-sm">👑 ${r.title}</div>
                    <div class="text-xs text-slate-500">ID: ${r.room_id}</div>
                  </div>
                </div>
                <span class="px-3 py-1 rounded-xl bg-amber-400 text-black font-black text-xs">Lv.${r.level || 1}</span>
              </div>
              <div class="bg-slate-100 p-3 rounded-2xl">
                <div class="font-black text-xs mb-2">Room Members (${r.online_count || 1})</div>
                <div class="flex gap-2 flex-wrap">
                  ${(r.visible_members || []).map(m => `
                    <div onclick="openUserProfileModal(${m.uid})" class="flex items-center gap-1 bg-white px-2 py-1 rounded-full text-xs font-bold shadow-sm cursor-pointer">
                      <span>👤 ${m.name}</span><span class="text-[10px] text-purple-600">${m.badge||''}</span>
                    </div>
                  `).join('')}
                </div>
              </div>
              <div class="bg-slate-100 p-3 rounded-2xl">
                <div class="font-black text-xs mb-1">Room Info</div>
                <div class="text-xs text-slate-600">${r.description || '—'}</div>
              </div>
            </div>
          </div>
        `;
      } else if (vrSheet === 'gifts') {
        const gifts = (spState?.store_items || []).filter(x => x.category === 'gift');
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/65 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-3 border-t border-amber-400/40">
              <div class="flex justify-between items-center text-xs font-black">
                <span class="text-amber-300">🎁 ارسال هدیه در اتاق صوتی (موجودی: ${(me.coins||0).toLocaleString()} 🪙)</span>
                <button onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))">✖</button>
              </div>
              <div class="grid grid-cols-4 gap-2 text-center text-xs">
                ${gifts.map(g => `
                  <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'send_gift',gift_id:${g.id}});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1 hover:border-amber-400">
                    ${g.photo ? `<img src="${g.photo}" class="w-10 h-10 object-cover rounded-xl" />` : `<span class="text-2xl">${g.icon}</span>`}
                    <span class="font-bold text-[10px] truncate w-full">${g.name}</span>
                    <span class="text-[10px] text-amber-300 font-black">${g.price_coins} 🪙</span>
                  </button>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      }

      root.innerHTML = `
        ${modalSheetHtml}
        <div style="background: ${roomBgCss};" class="flex-1 flex flex-col justify-between p-3 overflow-hidden relative">
          <!-- هدر بالای اتاق صوتی (مشابه عکس‌های SUGO) -->
          <div class="flex items-center justify-between gap-2 shrink-0">
            <div onclick="vrSheet='details';drawLiveVoiceRoom(document.getElementById('app'))" class="glass-panel px-2.5 py-1.5 rounded-2xl flex items-center gap-2 cursor-pointer">
              <img src="${r.photo || '/api/banner/hub.png'}" class="w-9 h-9 rounded-xl object-cover border border-amber-400" />
              <div class="leading-tight">
                <div class="font-black text-xs text-amber-200 flex items-center gap-1">
                  <span>👑 ${r.title}</span>
                  ${r.is_locked ? '<span>🔒</span>' : ''}
                </div>
                <div class="text-[10px] text-slate-400">ID: ${r.room_id} • 🪙 ${r.total_gifts || 0}</div>
              </div>
            </div>

            <div class="flex items-center gap-1.5">
              <div class="flex -space-x-2 overflow-hidden">${membersAvatars}</div>
              <span class="px-2 py-1 rounded-xl glass-soft text-[11px] font-black">👥 ${r.online_count || 1}</span>
              <button onclick="vrOpenExitPrompt()" class="w-8 h-8 rounded-full glass-panel flex items-center justify-center text-sm font-black">⏻</button>
            </div>
          </div>

          <!-- بنر وضعیت روح یا موزیک یا PK -->
          <div class="flex items-center justify-between gap-2 my-1 shrink-0">
            <div class="px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-400/30 text-[10px] font-black text-amber-300">
              🏆 Lv.${r.level || 1} • ${r.mic_count} Mic
            </div>
            ${r.music_playing ? `<div class="px-2.5 py-1 rounded-full bg-purple-600/40 border border-purple-400 text-[10px] font-bold animate-pulse">🎵 ${r.music_title}</div>` : ''}
            ${me.can_ghost_join && me.ghost_mode && !imSeated && !isRoomOwner ? `<div class="px-2.5 py-1 rounded-full bg-sky-500/30 border border-sky-300 text-[10px] font-black text-sky-200">👻 حالت روح فعال (مخفی)</div>` : ''}
          </div>

          ${r.pk_active ? `
            <div class="glass-panel p-2 rounded-2xl flex items-center justify-between text-xs font-black border border-rose-500/50 mb-1 shrink-0">
              <span class="text-sky-400">🔵 TEAM A: ${r.pk_score_a}</span>
              <span class="px-2 py-0.5 rounded bg-rose-600 text-[10px]">PK VS</span>
              <span class="text-rose-400">🔴 TEAM B: ${r.pk_score_b}</span>
            </div>
          ` : ''}

          <!-- چیدمان صندلی‌های میکروفون وسط اتاق -->
          <div class="my-auto py-2 overflow-y-auto max-h-[44vh] flex justify-center">
            <div class="grid ${gridCols} gap-3 justify-items-center w-full">
              ${seatsHtml}
            </div>
          </div>

          <!-- بخش اعلان و چت زنده پایین اتاق -->
          <div class="flex flex-col gap-1.5 max-h-[26vh] overflow-y-auto mb-2 pr-1">
            <div class="px-3 py-1.5 rounded-2xl bg-indigo-950/70 border border-indigo-400/30 text-[11px] text-amber-200">
              📣 <b>Room Info:</b> ${r.description}
            </div>
            ${chatsHtml}
          </div>

          <!-- نوار ابزار پایین اتاق صوتی (Say something, Mic, Tools, PK, Gift) -->
          <div class="flex items-center gap-1.5 shrink-0 pt-1">
            <div class="flex-1 flex items-center gap-1 glass-panel rounded-full px-3 py-1.5">
              <input id="vrChatInp" type="text" placeholder="Say something..." onkeydown="if(event.key==='Enter'){callSocialApi('room_op',{room_id:${r.room_id},op:'chat',text:this.value});this.value='';}" class="flex-1 bg-transparent text-xs text-white outline-none" />
              <button onclick="const el=document.getElementById('vrChatInp');if(el.value){callSocialApi('room_op',{room_id:${r.room_id},op:'chat',text:el.value});el.value='';}" class="text-purple-300 font-black text-xs">ارسال</button>
            </div>

            ${imSeated ? `
              <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_my_mic'})" class="w-10 h-10 rounded-full btn-success flex items-center justify-center text-base">🎙️</button>
              <button onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'leave_seat'})" class="w-10 h-10 rounded-full btn-danger flex items-center justify-center text-xs font-bold">⬇️</button>
            ` : ''}

            <button onclick="vrSheet='manage';drawLiveVoiceRoom(document.getElementById('app'))" class="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-base" title="ابزارهای اتاق">🎛️</button>
            <button onclick="vrSheet='gifts';drawLiveVoiceRoom(document.getElementById('app'))" class="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-rose-500 flex items-center justify-center text-base shadow-lg">🎁</button>
          </div>
        </div>
      `;
    }

    /* ۳. صفحه پروفایل اختصاصی کاربر با کارت‌های رنگی تلگرامی + نمایش اتاق صوتی داخل پروفایل */
    function renderSpProfile(root) {
      if (!spState) {
        root.innerHTML = `<div class="p-6 text-center"><div class="glass-panel p-6 rounded-3xl font-bold">در حال بارگذاری پروفایل...</div></div>`;
        callSocialApi('state');
        return;
      }
      const me = spState.me;
      const p = viewedProfileData || me;
      const isMe = Number(p.user_id) === Number(uid);
      const themes = spState.profile_themes || [];
      const curTheme = themes.find(t => t.id === p.card_theme) || themes[0];

      const themeSelectorHtml = isMe ? themes.map(t => `
        <button onclick="callSocialApi('save_profile',{card_theme:'${t.id}'})" style="background:${t.css}" class="px-2.5 py-2 rounded-xl text-[10px] font-black border ${p.card_theme===t.id ? 'border-white scale-105' : 'border-white/20 opacity-80'} flex items-center justify-between gap-1">
          <span>${t.title}</span>
          ${t.tier !== 'free' ? `<span class="px-1 rounded bg-black/50 text-amber-300 text-[8px]">${t.tier.toUpperCase()}</span>` : ''}
        </button>
      `).join('') : '';

      const visitorsHtml = isMe ? (p.visitors_log || []).map(v => `
        <div onclick="openUserProfileModal(${v.uid})" class="glass-soft p-2 rounded-xl flex items-center justify-between text-xs cursor-pointer">
          <div class="flex items-center gap-2">
            <img src="${v.photo || '/api/banner/hub.png'}" class="w-8 h-8 rounded-full object-cover" />
            <span class="font-bold">${v.name} <b class="text-amber-300">${v.badge||''}</b></span>
          </div>
          <span class="text-[10px] text-slate-400">${v.time}</span>
        </div>
      `).join('') : '';

      root.innerHTML = `
        ${renderTopBar('👤 پروفایل کاربری')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3">
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center">${spErr}</div>` : ''}

          <!-- کارت رنگی پروفایل به سبک تلگرام + حلقه دور آواتار + نشان اشتراک -->
          <div style="background: ${curTheme?.css || '#3b0764'};" class="p-5 rounded-3xl border border-white/20 shadow-2xl text-center relative overflow-hidden">
            <div class="relative inline-block mb-2">
              <img src="${p.photo || '/api/banner/hub.png'}" style="${p.ring_css ? `box-shadow:${p.ring_css};` : ''}" class="w-24 h-24 rounded-full object-cover mx-auto border-2 border-white" />
            </div>
            <div class="text-lg font-black text-white flex items-center justify-center gap-1.5">
              <span>${p.display_name}</span>
              ${p.sub_badge ? `<span class="px-2 py-0.5 rounded-full bg-black/45 border border-amber-300/50 text-amber-300 text-xs font-black">${p.sub_badge}</span>` : ''}
            </div>
            <div class="text-xs text-white/75 font-mono mb-2">ID: ${p.user_id} ${p.username ? '• @'+p.username : ''}</div>
            <p class="text-xs text-white/95 bg-black/25 p-2.5 rounded-2xl max-w-xs mx-auto">${p.bio}</p>

            <div class="grid grid-cols-3 gap-2 mt-3 text-xs font-black">
              <div class="bg-black/30 p-2 rounded-xl"><div class="text-[10px] text-white/70">سکه</div><div class="text-amber-300">🪙 ${(p.coins||0).toLocaleString()}</div></div>
              <div class="bg-black/30 p-2 rounded-xl"><div class="text-[10px] text-white/70">هدایا</div><div class="text-pink-300">🎁 ${p.gifts_received||0}</div></div>
              <div class="bg-black/30 p-2 rounded-xl"><div class="text-[10px] text-white/70">اشتراک</div><div class="text-emerald-300 uppercase">${p.sub_tier}</div></div>
            </div>
          </div>

          <!-- نمایش اتاق صوتی شخص در داخل پروفایلش (برای ورود مستقیم سایر کاربران) -->
          <div class="glass-panel p-4 rounded-3xl">
            <h4 class="text-xs font-black text-amber-300 mb-2">🎙️ اتاق صوتی اختصاصی ${isMe ? 'شما' : p.display_name}</h4>
            ${p.room ? `
              <div onclick="callSocialApi('join_room',{room_id:${p.room.room_id}})" class="glass-soft p-3 rounded-2xl flex items-center justify-between cursor-pointer border border-purple-400/40">
                <div class="flex items-center gap-3 min-w-0">
                  <img src="${p.room.photo || p.photo || '/api/banner/hub.png'}" class="w-12 h-12 rounded-2xl object-cover" />
                  <div class="min-w-0">
                    <div class="font-black text-xs text-white truncate">${p.room.title} ${p.room.is_locked ? '🔒' : '🟢'}</div>
                    <div class="text-[10px] text-slate-300 truncate">${p.room.description}</div>
                    <div class="text-[10px] text-emerald-300 font-bold">👥 ${p.room.online_count || 1} نفر داخل اتاق • Lv.${p.room.level || 1}</div>
                  </div>
                </div>
                <button class="btn-success px-3 py-2 rounded-xl text-xs font-black shrink-0">ورود ◀</button>
              </div>
            ` : `
              <div class="text-center text-xs text-slate-400 py-2">
                ${isMe ? `<button onclick="openMyVoiceRoomQuick()" class="btn-primary px-4 py-2.5 rounded-xl font-black">➕ ساخت اتاق صوتی شخصی</button>` : 'این کاربر هنوز اتاق صوتی نساخته است.'}
              </div>
            `}
          </div>

          ${isMe ? `
            <!-- تنظیمات ویرایش پروفایل، رنگ کارت و حالت‌های مخفی Plus/Ultra -->
            <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
              <h4 class="font-black text-sm text-indigo-300 text-center">🎨 رنگ پس‌زمینه کارت پروفایل (مشابه تلگرام)</h4>
              <div class="grid grid-cols-2 gap-2">${themeSelectorHtml}</div>

              <div class="border-t border-white/10 pt-3 space-y-2">
                <label class="block text-[11px] text-slate-300">نام نمایشی و بیوگرافی:</label>
                <input id="sp_name_inp" type="text" value="${p.display_name}" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
                <input id="sp_bio_inp" type="text" value="${p.bio}" class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />

                <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center">
                  <span>🕵️ بازدید مخفی پروفایل دیگران (PLUS+):</span>
                  <input id="sp_stealth_chk" type="checkbox" ${p.stealth_mode ? 'checked' : ''} ${!p.can_stealth_visit ? 'disabled' : ''} class="w-4 h-4" />
                </div>
                <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center">
                  <span>👻 ورود روح به اتاق‌های صوتی (ULTRA):</span>
                  <input id="sp_ghost_chk" type="checkbox" ${p.ghost_mode ? 'checked' : ''} ${!p.can_ghost_join ? 'disabled' : ''} class="w-4 h-4" />
                </div>

                <button onclick="callSocialApi('save_profile',{display_name:document.getElementById('sp_name_inp').value,bio:document.getElementById('sp_bio_inp').value,card_theme:'${p.card_theme}',stealth_mode:document.getElementById('sp_stealth_chk').checked,ghost_mode:document.getElementById('sp_ghost_chk').checked})" class="btn-success w-full py-3 rounded-2xl font-black">
                  💾 ذخیره تغییرات پروفایل
                </button>
              </div>
            </div>

            <div class="glass-panel p-4 rounded-3xl space-y-2 text-xs">
              <h4 class="font-black text-amber-300 text-center">👁️ آخرین بازدیدکنندگان پروفایل شما</h4>
              <div class="flex flex-col gap-1.5">${visitorsHtml || '<div class="text-center text-slate-400">هنوز کسی از پروفایل شما بازدید نکرده است.</div>'}</div>
            </div>
          ` : `
            <button onclick="viewedProfileData=null;renderSpProfile(document.getElementById('app'))" class="btn-primary w-full py-3 rounded-2xl font-black text-xs">🔙 بازگشت به پروفایل خودم</button>
          `}
        </div>
      `;
    }

    /* ۴. فروشگاه جامع (اشتراک‌های Pro/Plus/Ultra + حلقه‌های دور پروفایل + گیفت‌ها) */
    function renderSpStore(root) {
      if (!spState) {
        root.innerHTML = `<div class="p-6 text-center"><div class="glass-panel p-6 rounded-3xl font-bold">در حال بارگذاری فروشگاه...</div></div>`;
        callSocialApi('state');
        return;
      }
      const me = spState.me;
      const subs = (spState.sub_tiers || []).filter(s => s.id !== 'free');
      const rings = (spState.store_items || []).filter(i => i.category === 'ring');
      const gifts = (spState.store_items || []).filter(i => i.category === 'gift');

      let contentHtml = '';
      if (storeTab === 'subs') {
        contentHtml = subs.map(s => `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 border ${s.id==='ultra' ? 'border-pink-400 shadow-[0_0_20px_rgba(236,72,153,0.3)]' : (s.id==='plus' ? 'border-amber-400/60' : 'border-sky-400/50')}">
            <div class="flex justify-between items-center">
              <span class="text-base font-black text-white">${s.title}</span>
              <span class="px-2.5 py-1 rounded-full bg-white/10 text-amber-300 text-xs font-black">${s.badge}</span>
            </div>
            <ul class="text-xs text-slate-200 space-y-1 pr-2">
              ${s.perks.map(pk => `<li>✅ ${pk}</li>`).join('')}
            </ul>
            <div class="grid grid-cols-2 gap-2 pt-2">
              <button onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'stars'})" class="btn-primary py-2.5 rounded-xl font-black text-xs">⭐ خرید با ${s.stars} استارز</button>
              <button onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'coins'})" class="btn-success py-2.5 rounded-xl font-black text-xs">🪙 خرید با ${s.coins.toLocaleString()} سکه</button>
            </div>
          </div>
        `).join('');
      } else if (storeTab === 'rings') {
        contentHtml = rings.map(r => {
          const owned = (me.owned_rings || []).includes(r.id);
          const equipped = me.avatar_ring_id === r.id;
          return `
            <div class="glass-panel p-3.5 rounded-3xl flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div style="box-shadow:${r.ring_css}" class="w-14 h-14 rounded-full bg-slate-900 flex items-center justify-center text-2xl shrink-0">
                  ${r.icon || '⭕'}
                </div>
                <div>
                  <div class="font-black text-xs text-white">${r.name}</div>
                  <div class="text-[11px] text-amber-300 font-bold">${r.price_coins.toLocaleString()} 🪙</div>
                </div>
              </div>
              <button onclick="callSocialApi('buy_or_equip_ring',{ring_id:${r.id}})" class="${equipped ? 'btn-success' : (owned ? 'btn-primary' : 'btn-danger')} px-3.5 py-2 rounded-xl text-xs font-black shrink-0">
                ${equipped ? 'فعال ✓' : (owned ? 'استفاده' : 'خرید')}
              </button>
            </div>
          `;
        }).join('');
      } else {
        contentHtml = `<div class="grid grid-cols-2 gap-2.5">` + gifts.map(g => `
          <div class="glass-panel p-3.5 rounded-3xl text-center space-y-1.5">
            <div class="text-4xl">${g.icon}</div>
            <div class="font-black text-xs text-white">${g.name}</div>
            <div class="text-xs text-amber-300 font-extrabold">${g.price_coins.toLocaleString()} 🪙</div>
            <div class="text-[10px] text-slate-400">قابل ارسال در تمام اتاق‌های صوتی</div>
          </div>
        `).join('') + `</div>`;
      }

      root.innerHTML = `
        ${renderTopBar('🛍️ فروشگاه VIP و کاور پروفایل')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3">
          <div class="glass-panel p-3 rounded-2xl flex justify-between items-center text-xs font-black">
            <span>موجودی شما: <b class="text-amber-300">🪙 ${(me.coins||0).toLocaleString()}</b></span>
            <span>اشتراک فعلی: <b class="text-emerald-300 uppercase">${me.sub_tier} ${me.sub_badge||''}</b></span>
          </div>

          <div class="grid grid-cols-3 gap-2 text-xs font-black">
            <button onclick="storeTab='subs';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='subs' ? 'btn-primary' : 'glass-soft'}">💎 اشتراک VIP</button>
            <button onclick="storeTab='rings';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='rings' ? 'btn-primary' : 'glass-soft'}">⭕ حلقه آواتار</button>
            <button onclick="storeTab='gifts';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='gifts' ? 'btn-primary' : 'glass-soft'}">🎁 گیفت‌ها</button>
          </div>

          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center">${spErr}</div>` : ''}

          <div class="space-y-3">${contentHtml}</div>
        </div>
      `;
    }

    function render() {
      const root = document.getElementById('app');
      if (!root) return;
      if (currentGame === 'tower_admin') return startTowerAdminApp(root);
      if (currentGame === 'demontower') return startDemonTowerApp(root);
      if (currentGame === 'lobby_gate') return renderLobbyGate(root);
      if (currentGame === 'hokm' || currentGame === 'hokm4p') return startHokmEngine(root, '4p');
      if (currentGame === 'hokm2p') return startHokmEngine(root, '2p');
      if (currentGame === 'gardone_anim' || currentGame === 'gardone') return renderGardoneAnim(root);
      if (currentGame === '2048') return render2048(root);
      if (currentGame === 'spuzzle') return renderSpuzzle(root);
      if (currentGame === 'samegame') return renderSameGame(root);
      if (currentGame === 'dooz' || currentGame === 'doz4p') return renderDooz(root, currentGame);
      if (currentGame === 'connect4') return renderConnect4(root);
      if (currentGame === 'rps') return renderRPS(root);
      if (currentGame === 'memory') return renderMemory(root);
      if (currentGame === 'typing') return renderTyping(root);
      if (currentGame === 'hangman') return renderHangman(root);
      if (currentGame === 'guess') return renderGuess(root);
      if (currentGame === 'voice_hub') return renderVoiceHub(root);
      if (currentGame === 'voice_room_live') return startLiveVoiceRoom(root);
      if (currentGame === 'sp_profile') return renderSpProfile(root);
      if (currentGame === 'sp_store') return renderSpStore(root);
      return renderHub(root);
    }

    verifyJoinAndRender();
  </script>
</body>
</html>
"""


@app.get("/{full_path:path}")
async def serve_entry(request: Request, full_path: str):
    from runtime import get_bot_username
    game = request.query_params.get("game") or "hub"
    meta = GAME_META.get(game, GAME_META["hub"])
    base_url = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")
    short_name = os.environ.get("MINI_APP_SHORT_NAME", "RhinoGamesApp").strip() or "RhinoGamesApp"
    og_img = f"{base_url}/api/banner/{game}.png"

    hero_img = os.environ.get("RHINO_HERO_IMAGE", "")
    if not hero_img and CUSTOM_HERO_FILE.exists():
        hero_img = f"{base_url}/api/custom_bg/hero"

    menu_bg = os.environ.get("RHINO_MENU_BG", "")
    if not menu_bg and CUSTOM_MENU_BG.exists():
        menu_bg = f"{base_url}/api/custom_bg/menu"

    carpet_bg = os.environ.get("RHINO_CARPET_BG", "")
    if not carpet_bg and CUSTOM_CARPET_BG.exists():
        carpet_bg = f"{base_url}/api/custom_bg/carpet"

    tower_bg = os.environ.get("RHINO_TOWER_BG", "")
    if not tower_bg and CUSTOM_TOWER_BG.exists():
        tower_bg = f"{base_url}/api/custom_bg/tower_bg"

    tower_hero = os.environ.get("RHINO_TOWER_HERO", "")
    if not tower_hero and CUSTOM_TOWER_HERO.exists():
        tower_hero = f"{base_url}/api/custom_bg/tower_hero"

    html_content = (
        MINIAPP_TEMPLATE
        .replace("__OG_TITLE__", meta["title"])
        .replace("__OG_IMAGE__", og_img)
        .replace("__HERO_IMAGE__", hero_img)
        .replace("__TOWER_HERO__", tower_hero)
        .replace("__MENU_BG__", f"url('{menu_bg}')," if menu_bg else "")
        .replace("__CARPET_BG__", f"url('{carpet_bg}')" if carpet_bg else "none")
        .replace("__TOWER_BG__", f"url('{tower_bg}')" if tower_bg else "none")
        .replace("__BOT_USERNAME__", get_bot_username())
        .replace("__SHORT_NAME__", short_name)
    )
    return HTMLResponse(content=html_content, status_code=200)
