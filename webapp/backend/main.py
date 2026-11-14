# -*- coding: utf-8 -*-
"""webapp/backend/main.py — هسته FastAPI مینی‌اپ راینو (معماری ماژولار ۴ فایلی)"""

import base64
import io
import json
import os
import random
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw

from database import db
from webapp.backend.game_logic.hokm import HokmGame

app = FastAPI(title="Rhino Social & Casino Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CUSTOM_HERO_FILE = BASE_DIR / "rhino_banner.png"
CUSTOM_MENU_BG = BASE_DIR / "menu_bg.png"
CUSTOM_CARPET_BG = BASE_DIR / "hokm_carpet.png"

hokm_rooms: dict[str, HokmGame] = {}
guess_rooms: dict[str, dict] = {}

GAME_META = {
    "hub":          {"title": "RHINO PLATFORM", "c1": (18, 10, 42),  "c2": (109, 40, 217)},
    "crash":        {"title": "CRASH ROCKET",   "c1": (88, 28, 135), "c2": (236, 72, 153)},
    "bombs":        {"title": "GOLD BOMBS",     "c1": (120, 53, 15), "c2": (245, 158, 11)},
    "pickaxe":      {"title": "HELL PICKAXE",   "c1": (127, 29, 29), "c2": (239, 68, 68)},
    "slot":         {"title": "ROYAL SLOT",     "c1": (49, 46, 129), "c2": (139, 92, 246)},
    "voice_hub":    {"title": "VOICE ROOMS",    "c1": (30, 27, 75),  "c2": (124, 58, 237)},
    "tower_admin":  {"title": "ADMIN PANEL",    "c1": (30, 27, 75),  "c2": (124, 58, 237)},
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
    meta = GAME_META.get(game_key, GAME_META["hub"])
    w, h = 450, 450
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
    draw.ellipse([55, 55, w - 55, h - 55], outline=(255, 255, 255), width=3)
    draw.rounded_rectangle([16, 16, w - 16, h - 16], radius=34, outline=(255, 255, 255), width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def _get_saved_ui_assets() -> dict:
    try:
        from social_platform import get_sp_config
        raw = await get_sp_config("ui_assets", "{}")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


@app.get("/api/ui_assets")
async def api_get_ui_assets():
    from social_platform import recent_big_wins
    assets = await _get_saved_ui_assets()
    return {"ok": True, "assets": assets, "recent_wins": recent_big_wins[:8]}


@app.get("/api/tg_emoji/{emoji_id}")
async def serve_tg_custom_emoji(emoji_id: str):
    from social_platform import fetch_tg_custom_emoji_bytes
    raw, mime = await fetch_tg_custom_emoji_bytes(emoji_id)
    if raw:
        return Response(content=raw, media_type=mime, headers={"Cache-Control": "public, max-age=86400"})
    return Response(status_code=404)


@app.get("/api/custom_bg/{bg_name}")
async def serve_custom_bg(bg_name: str):
    assets = await _get_saved_ui_assets()
    b64_data = assets.get(bg_name, "")
    if b64_data and b64_data.startswith("data:image"):
        try:
            header, encoded = b64_data.split(",", 1)
            mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
            return Response(content=base64.b64decode(encoded), media_type=mime)
        except Exception:
            pass
    if bg_name in ("hero", "rhino_hero") and CUSTOM_HERO_FILE.exists():
        return FileResponse(str(CUSTOM_HERO_FILE), media_type="image/png")
    if bg_name in ("menu", "menu_bg") and CUSTOM_MENU_BG.exists():
        return FileResponse(str(CUSTOM_MENU_BG), media_type="image/png")
    if bg_name in ("carpet", "hokm_carpet") and CUSTOM_CARPET_BG.exists():
        return FileResponse(str(CUSTOM_CARPET_BG), media_type="image/png")
    return Response(content=generate_game_banner(game_key=bg_name), media_type="image/png")


@app.get("/api/banner/{game_type}.png")
async def serve_game_banner(game_type: str):
    return await serve_custom_bg(game_type)


# ─── سرو کردن ۳ ماژول جاوااسکریپت به صورت مجزا و تمیز ───
@app.get("/static/js_core_casino.js")
async def serve_js_core():
    from webapp.backend.js_core_casino import JS_CORE_CASINO
    return Response(content=JS_CORE_CASINO, media_type="application/javascript; charset=utf-8")


@app.get("/static/js_social.js")
async def serve_js_social():
    from webapp.backend.js_social import JS_SOCIAL
    return Response(content=JS_SOCIAL, media_type="application/javascript; charset=utf-8")


@app.get("/static/js_games_admin.js")
async def serve_js_games_admin():
    from webapp.backend.js_games_admin import JS_GAMES_ADMIN
    return Response(content=JS_GAMES_ADMIN, media_type="application/javascript; charset=utf-8")


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


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/social/action")
async def social_action_endpoint(request: Request):
    from social_platform import handle_social_api
    return await handle_social_api(await request.json())


@app.post("/api/tower/admin")
async def platform_admin_endpoint(request: Request):
    from social_platform import handle_platform_admin_api
    return await handle_platform_admin_api(await request.json())


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
            channels_data.append({"title": ch.get("title") or uname or "Sponsor Channel", "url": url})
        return {"ok": True, "joined": len(channels_data) == 0, "channels": channels_data}
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
    not_started, invited = [], []

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
                        text=f"🎮 <b>RHINO GAME BOX</b>\n\n👤 <b>{payload.inviter_name}</b> شما را به میز بازی دعوت کرد!",
                        reply_markup=kb([[success("▶️ ورود به میز بازی", url=join_url)]]),
                        parse_mode=ParseMode.HTML,
                    )
                    invited.append(row["first_name"] or t_str)
                except Exception:
                    not_started.append(t_str)
    finally:
        if temp_bot:
            await temp_bot.session.close()
    return {"ok": len(not_started) == 0, "invited": invited, "not_started": not_started}


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
    return {**res, "state": game.get_state_for_player(payload.uid)}


@app.post("/api/guess/action")
async def guess_action_endpoint(payload: GuessActionPayload):
    sid = payload.session
    if payload.action == "create" or sid not in guess_rooms:
        lo, hi = min(payload.min_val, payload.max_val), max(payload.min_val, payload.max_val)
        if hi - lo < 2:
            hi = lo + 100
        guess_rooms[sid] = {
            "session": sid, "host_id": payload.uid, "host_name": payload.name,
            "min": lo, "max": hi, "secret": random.randint(lo, hi),
            "winner_id": None, "winner_name": "", "history": [],
        }
    room = guess_rooms[sid]
    if payload.action == "restart":
        if int(payload.uid) != int(room["host_id"]):
            return {"ok": False, "error": "فقط سازنده بازی می‌تواند دور جدید را شروع کند!", "room": room}
        room["secret"] = random.randint(room["min"], room["max"])
        room["winner_id"], room["winner_name"], room["history"] = None, "", []
    elif payload.action == "guess" and payload.guess_val is not None and not room["winner_id"]:
        gval = int(payload.guess_val)
        if gval == room["secret"]:
            room["winner_id"], room["winner_name"] = payload.uid, payload.name
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "🏆"})
            try:
                await db.add_win(payload.uid, "number_guess")
            except Exception:
                pass
        else:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬆️ بالاتر" if gval < room["secret"] else "⬇️ پایین‌تر"})
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


MINIAPP_HTML = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <title>__OG_TITLE__</title>
  <meta property="og:type" content="website" />
  <meta property="og:title" content="__OG_TITLE__" />
  <meta property="og:description" content="پلتفرم راینو — اتاق‌های صوتی، کازینو و بازی‌های آنلاین" />
  <meta property="og:image" content="__OG_IMAGE__" />
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    ::-webkit-scrollbar { width: 0px; height: 0px; }
    html, body {
      width: 100vw; height: 100vh; margin: 0; padding: 0; overflow: hidden;
      background-color: #090514;
      background-image:
        radial-gradient(circle at 15% 10%, rgba(124, 58, 237, 0.25) 0%, transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(219, 39, 119, 0.18) 0%, transparent 45%);
      background-size: cover; background-position: center; color: #fff;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    input, textarea, select { user-select: text !important; -webkit-user-select: text !important; }
    #app {
      width: 100vw; height: 100vh;
      padding-top: calc(env(safe-area-inset-top, 10px) + 32px);
      padding-bottom: env(safe-area-inset-bottom, 6px);
      display: flex; flex-direction: column; overflow: hidden;
    }
    .glass-panel {
      background: rgba(19, 14, 38, 0.78); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.55);
    }
    .glass-soft {
      background: rgba(255, 255, 255, 0.07); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.11);
    }
    .btn-primary { background: linear-gradient(135deg, #7c3aed, #4f46e5); border: 1px solid rgba(255,255,255,0.22); box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35); }
    .btn-success { background: linear-gradient(135deg, #059669, #10b981); border: 1px solid rgba(255,255,255,0.22); }
    .btn-danger  { background: linear-gradient(135deg, #e11d48, #ef4444); border: 1px solid rgba(255,255,255,0.22); }
    .ltr-grid { direction: ltr !important; }

    .arcade-card {
      position: relative; aspect-ratio: 1 / 1.04; border-radius: 24px; overflow: hidden;
      border: 1.5px solid rgba(168, 85, 247, 0.34); background: #130d26;
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.65); transition: transform 0.16s ease, border-color 0.16s ease;
    }
    .arcade-card:active { transform: scale(0.96); border-color: rgba(168, 85, 247, 0.85); }
    .arcade-card-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    .arcade-card-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(10, 6, 24, 0.6) 0%, rgba(10, 6, 24, 0.15) 45%, rgba(10, 6, 24, 0.9) 100%);
      display: flex; flex-direction: column; justify-content: space-between; padding: 14px 12px 11px 12px;
    }
    .arcade-title { font-weight: 900; font-size: 1.1rem; line-height: 1.15; text-transform: uppercase; color: #fff; text-shadow: 0 3px 12px rgba(0,0,0,0.9); }
    .pill-players { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(52, 211, 153, 0.35); color: #34d399; font-size: 10px; font-weight: 900; padding: 2px 7px; border-radius: 999px; display: inline-flex; align-items: center; gap: 3px; }
    .pill-mode-pve { background: linear-gradient(135deg, #0ea5e9, #2563eb); color: #fff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; }
    .pill-mode-slot { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; }
    .pill-new { background: rgba(88, 28, 135, 0.88); border: 1px solid rgba(192, 132, 252, 0.5); color: #f3e8ff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; }
    .bottom-dock { background: rgba(18, 13, 36, 0.94); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 28px; box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.7); }

    @keyframes voiceWaveAnim {
      0%   { transform: scale(1); opacity: 0.85; }
      70%  { transform: scale(1.38); opacity: 0; }
      100% { transform: scale(1.42); opacity: 0; }
    }
    .speaking-wave::before, .speaking-wave::after {
      content: ''; position: absolute; inset: -3px; border-radius: 9999px;
      border: 2.5px solid #34d399; pointer-events: none; z-index: 1;
      animation: voiceWaveAnim 1.6s infinite ease-out;
    }
    .speaking-wave::after { animation-delay: 0.75s; border-color: #a855f7; }

    @keyframes floatGiftSlow {
      0%, 100% { transform: translateY(0px) rotate(-4deg); }
      50%      { transform: translateY(-7px) rotate(5deg); }
    }
    .floating-profile-gift { animation: floatGiftSlow 3.4s infinite ease-in-out; }

    .persian-carpet {
      position: relative; width: 100%; height: 100%; background-color: #781014;
      background-image:
        var(--custom-carpet-bg, __CARPET_BG__)
        radial-gradient(ellipse at center, rgba(185, 28, 28, 0.52) 0%, rgba(102, 10, 14, 0.94) 68%, #3a0608 100%),
        repeating-linear-gradient(45deg, rgba(245, 158, 11, 0.06) 0px, rgba(245, 158, 11, 0.06) 2px, transparent 2px, transparent 6px);
      background-size: cover; background-position: center; border: 6px solid #1e1b4b; border-radius: 18px;
      box-shadow: inset 0 0 0 2px #d97706, inset 0 0 0 6px #450a0a, inset 0 0 40px rgba(0,0,0,0.85);
    }
    .carpet-medallion {
      position: absolute; top: 44%; left: 50%; transform: translate(-50%, -50%);
      width: 185px; height: 185px; border-radius: 50%; border: 2.5px solid rgba(251, 191, 36, 0.42);
      background: radial-gradient(circle, rgba(30, 58, 138, 0.32) 0%, rgba(127, 29, 29, 0.38) 65%, transparent 75%);
      pointer-events: none;
    }
    .playing-card {
      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%); border: 1.5px solid #94a3b8;
      border-radius: 10px; box-shadow: -2px 5px 12px rgba(0, 0, 0, 0.65); color: #0f172a;
      display: flex; flex-direction: column; justify-content: space-between; padding: 5px 6px; font-family: Georgia, serif;
    }
    .playing-card.red { color: #dc2626; }
    .card-back-real {
      background-color: #1e3a8a;
      background-image: radial-gradient(circle, #fbbf24 18%, transparent 19%), repeating-linear-gradient(45deg, rgba(255,255,255,0.14) 0, rgba(255,255,255,0.14) 2px, transparent 2px, transparent 5px);
      background-size: 12px 12px; border: 1.5px solid #fde68a; border-radius: 7px; box-shadow: -1px 3px 7px rgba(0,0,0,0.75);
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    window.RHINO_CONFIG = {
      HERO_CUSTOM_IMG: "__HERO_IMAGE__",
      BOT_USERNAME: "__BOT_USERNAME__",
      SHORT_NAME: "__SHORT_NAME__"
    };
  </script>
  <script src="/static/js_core_casino.js?v=2"></script>
  <script src="/static/js_social.js?v=2"></script>
  <script src="/static/js_games_admin.js?v=2"></script>
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
    carpet_bg = os.environ.get("RHINO_CARPET_BG", "")
    if not carpet_bg and CUSTOM_CARPET_BG.exists():
        carpet_bg = f"{base_url}/api/custom_bg/carpet"

    html_content = (
        MINIAPP_HTML
        .replace("__OG_TITLE__", meta["title"])
        .replace("__OG_IMAGE__", og_img)
        .replace("__HERO_IMAGE__", hero_img)
        .replace("__CARPET_BG__", f"url('{carpet_bg}')," if carpet_bg else "")
        .replace("__BOT_USERNAME__", get_bot_username())
        .replace("__SHORT_NAME__", short_name)
    )
    return HTMLResponse(content=html_content, status_code=200)
