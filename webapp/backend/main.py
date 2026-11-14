# -*- coding: utf-8 -*-
"""webapp/backend/main.py — پلتفرم کامل راینو: اتاق‌های صوتی، چت پیوی، روابط، کازینو، کیف پول و گیم باکس"""

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
}


def generate_game_banner(game_key: str) -> bytes:
    meta = GAME_META.get(game_key, GAME_META["hub"])
    w, h = 400, 400
    img = Image.new("RGB", (w, h), meta["c1"])
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = meta["c1"]
    r2, g2, b2 = meta["c2"]
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=(int(r1*(1-t)+r2*t), int(g1*(1-t)+g2*t), int(b1*(1-t)+b2*t)))
    draw.rounded_rectangle([14, 14, w - 14, h - 14], radius=32, outline=(255, 255, 255), width=2)
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


class WinPayload(BaseModel):
    uid: int
    game_type: str
    best_time: float | None = None


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
    if payload.action == "restart" and int(payload.uid) == int(room["host_id"]):
        room["secret"] = random.randint(room["min"], room["max"])
        room["winner_id"], room["winner_name"], room["history"] = None, "", []
    elif payload.action == "guess" and payload.guess_val is not None and not room["winner_id"]:
        gval = int(payload.guess_val)
        if gval == room["secret"]:
            room["winner_id"], room["winner_name"] = payload.uid, payload.name
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "🏆"})
        else:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬆️" if gval < room["secret"] else "⬇️"})
        room["history"] = room["history"][:12]
    safe_room = {k: v for k, v in room.items() if k != "secret"}
    if room["winner_id"]:
        safe_room["secret_revealed"] = room["secret"]
    return {"ok": True, "room": safe_room}


MINIAPP_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <title>__OG_TITLE__</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    ::-webkit-scrollbar { width: 0px; height: 0px; }
    html, body {
      width: 100vw; height: 100vh; margin: 0; padding: 0; overflow: hidden;
      background-color: #090514;
      background-image: radial-gradient(circle at 15% 10%, rgba(124, 58, 237, 0.25) 0%, transparent 45%), radial-gradient(circle at 85% 85%, rgba(219, 39, 119, 0.18) 0%, transparent 45%);
      background-size: cover; background-position: center; color: #fff;
      font-family: system-ui, -apple-system, sans-serif;
    }
    input, textarea, select { user-select: text !important; -webkit-user-select: text !important; }
    #app {
      width: 100vw; height: 100vh;
      padding-top: calc(env(safe-area-inset-top, 10px) + 30px);
      padding-bottom: env(safe-area-inset-bottom, 6px);
      display: flex; flex-direction: column; overflow: hidden;
    }
    .glass-panel {
      background: rgba(19, 14, 38, 0.78); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.55);
    }
    .glass-soft {
      background: rgba(255, 255, 255, 0.07); backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.11);
    }
    .btn-primary { background: linear-gradient(135deg, #7c3aed, #4f46e5); border: 1px solid rgba(255,255,255,0.22); }
    .btn-success { background: linear-gradient(135deg, #059669, #10b981); border: 1px solid rgba(255,255,255,0.22); }
    .btn-danger  { background: linear-gradient(135deg, #e11d48, #ef4444); border: 1px solid rgba(255,255,255,0.22); }
    .ltr-grid { direction: ltr !important; }
    .arcade-card {
      position: relative; aspect-ratio: 1 / 1.04; border-radius: 24px; overflow: hidden;
      border: 1.5px solid rgba(168, 85, 247, 0.34); background: #130d26; box-shadow: 0 10px 26px rgba(0, 0, 0, 0.65);
    }
    .arcade-card-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    .arcade-card-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(10, 6, 24, 0.6) 0%, rgba(10, 6, 24, 0.15) 45%, rgba(10, 6, 24, 0.9) 100%);
      display: flex; flex-direction: column; justify-content: space-between; padding: 12px;
    }
    .arcade-title { font-weight: 900; font-size: 1.05rem; color: #fff; text-shadow: 0 3px 10px #000; }
    .pill-players { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(52, 211, 153, 0.35); color: #34d399; font-size: 10px; font-weight: 900; padding: 2px 7px; border-radius: 999px; }
    .pill-mode-pve { background: linear-gradient(135deg, #0ea5e9, #2563eb); color: #fff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; }
    .pill-new { background: rgba(88, 28, 135, 0.88); border: 1px solid rgba(192, 132, 252, 0.5); color: #f3e8ff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; }
    .bottom-dock { background: rgba(18, 13, 36, 0.94); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 28px; box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.7); }

    /* امواج صوتی صحبت کردن دور پروفایل در اتاق صوتی */
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

    /* شناور شدن نامنظم گیفت‌ها روی کارت پروفایل با هاله نئون */
    @keyframes floatGiftSlow {
      0%, 100% { transform: translateY(0px) rotate(-4deg); }
      50%      { transform: translateY(-7px) rotate(5deg); }
    }
    .floating-profile-gift { animation: floatGiftSlow 3.4s infinite ease-in-out; }

    .persian-carpet {
      position: relative; width: 100%; height: 100%; background-color: #781014;
      background-image: var(--custom-carpet-bg, __CARPET_BG__) radial-gradient(ellipse at center, rgba(185, 28, 28, 0.52) 0%, rgba(102, 10, 14, 0.94) 68%, #3a0608 100%);
      background-size: cover; background-position: center; border: 5px solid #1e1b4b; border-radius: 18px;
    }
    .playing-card {
      background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%); border: 1.5px solid #94a3b8;
      border-radius: 10px; box-shadow: -2px 5px 12px rgba(0,0,0,0.65); color: #0f172a;
      display: flex; flex-direction: column; justify-content: space-between; padding: 5px 6px;
    }
    .playing-card.red { color: #dc2626; }
  </style>
</head>
<body>
  <div id="app"></div>

  <script>
    window.onerror = function(msg, url, line) { console.warn("MiniApp warn:", msg, line); return true; };
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    function isUserTyping() {
      const el = document.activeElement;
      return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT');
    }

    window.uploadedImages = {};
    window.uiAssetsMap = {};
    window.recentWinsList = [];

    window.handleImageUpload = function(inputEl, targetKey, previewImgId) {
      const file = inputEl.files && inputEl.files[0];
      if (!file) return;
      const isPng = file.type === 'image/png' || file.type === 'image/webp' || targetKey === 'store_item_photo';
      const reader = new FileReader();
      reader.onload = function(ev) {
        const img = new Image();
        img.onload = function() {
          const canvas = document.createElement('canvas');
          const maxDim = 520;
          let w = img.width, h = img.height;
          if (w > h && w > maxDim) { h = Math.round(h * maxDim / w); w = maxDim; }
          else if (h >= w && h > maxDim) { w = Math.round(w * maxDim / h); h = maxDim; }
          canvas.width = w; canvas.height = h;
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0, w, h);
          const dataUrl = isPng ? canvas.toDataURL('image/png') : canvas.toDataURL('image/jpeg', 0.84);
          window.uploadedImages[targetKey] = dataUrl;
          const prev = document.getElementById(previewImgId);
          if (prev) { prev.src = dataUrl; prev.classList.remove('hidden'); }
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    };

    /* رندر ایموجی پریمیوم تلگرام یا آیکون جایگزین */
    window.renderTgEmoji = function(emojiId, fallbackIcon = '✨', cls = 'w-5 h-5 inline-block object-contain align-middle') {
      if (emojiId && String(emojiId).length >= 10) {
        return `<img src="/api/tg_emoji/${emojiId}" onerror="this.outerHTML='<span>${fallbackIcon}</span>'" class="${cls}" />`;
      }
      return `<span>${fallbackIcon || ''}</span>`;
    };

    /* رندر آواتار با قاب PNG توخالی + امواج صوتی صحبت کردن */
    window.renderAvatarWithFrame = function(photoUrl, nameStr, sizeCls, ringPhoto, ringCss, extraBorderCls = 'border border-purple-400/60', isSpeaking = false) {
      const initial = ((nameStr || 'U')[0] || 'U').toUpperCase();
      const shadowStyle = (!ringPhoto && ringCss) ? ('box-shadow:' + ringCss + ';') : '';
      const innerAvatar = photoUrl
        ? `<img src="${photoUrl}" style="${shadowStyle}" class="w-full h-full rounded-full object-cover relative z-10 ${ringPhoto ? '' : extraBorderCls}" />`
        : `<div style="${shadowStyle}" class="w-full h-full rounded-full bg-gradient-to-br from-purple-700 to-indigo-900 flex items-center justify-center font-black text-white relative z-10 ${ringPhoto ? '' : extraBorderCls}">${initial}</div>`;
      const frameOverlay = ringPhoto
        ? `<img src="${ringPhoto}" class="absolute inset-0 w-full h-full object-contain pointer-events-none z-20" style="transform: scale(1.28);" />`
        : '';
      return `
        <div class="relative inline-flex items-center justify-center shrink-0 ${sizeCls} ${isSpeaking ? 'speaking-wave' : ''}" style="overflow: visible;">
          ${innerAvatar}
          ${frameOverlay}
        </div>
      `;
    };

    function getAssetImg(key, fallbackUrl = '') {
      if (window.uiAssetsMap && window.uiAssetsMap[key]) return window.uiAssetsMap[key];
      return fallbackUrl || ('/api/custom_bg/' + key);
    }

    function applyDynamicCssBackgrounds() {
      const rootStyle = document.documentElement.style;
      if (window.uiAssetsMap?.menu_bg) {
        document.body.style.backgroundImage = `url('${window.uiAssetsMap.menu_bg}')`;
      }
      if (window.uiAssetsMap?.hokm_carpet) {
        rootStyle.setProperty('--custom-carpet-bg', `url('${window.uiAssetsMap.hokm_carpet}'),`);
      }
    }

    async function loadUiAssets() {
      try {
        const res = await fetch('/api/ui_assets');
        const data = await res.json();
        if (data.assets) { window.uiAssetsMap = data.assets; applyDynamicCssBackgrounds(); }
        if (data.recent_wins) window.recentWinsList = data.recent_wins;
      } catch (e) {}
    }

    const BOT_USERNAME = "__BOT_USERNAME__";
    const SHORT_NAME = "__SHORT_NAME__";
    const OWNER_IDS = [7662192190, 6041119040];

    const params = new URLSearchParams(window.location.search);
    const startParam = tg?.initDataUnsafe?.start_param || params.get('startapp') || '';
    let parsedGame = params.get('game') || '';
    let parsedChat = params.get('chat') || params.get('session') || ('rm_' + Math.floor(Math.random()*89999+10000));
    let lang = localStorage.getItem('rhino_lang') || params.get('lang') || 'fa';
    if (startParam) {
      const parts = startParam.split('__');
      if (parts[0]) parsedGame = parts[0];
      if (parts[1]) parsedChat = parts[1];
    }

    let currentGame = parsedGame || 'hub';
    let hubFilter = 'all';
    const tgUser = tg?.initDataUnsafe?.user || {};
    const realTgUid = tgUser.id || Number(params.get('uid')) || 0;
    const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
    const isOwner = OWNER_IDS.includes(Number(uid));
    const myName = tgUser.first_name || 'CEORHINO';
    const myUsername = tgUser.username || '';
    const myPhoto = tgUser.photo_url || '';

    let hokmPollTimer = null, guessPollTimer = null, vrPollTimer = null, pmPollTimer = null;
    let spState = null;
    let activeVoiceRoom = null;
    let minimizedVoiceRoom = null;
    let viewedProfileData = null;
    let activePmChat = null;
    let activePmPeerUid = 0;
    let spMsg = '', spErr = '';
    let vrSheet = '';
    let selectedSeatIdx = 1;
    let selectedGiftRecs = [];
    let storeTab = 'subs';
    let bombsState = null, crashLastResult = null, pickaxeLastResult = null, slotLastResult = null;
    let mediaRecorder = null, audioChunks = [], isRecordingVoice = false;

    function renderBottomNav() {
      return `
        <div class="fixed bottom-3 left-3 right-3 z-30 bottom-dock px-3 py-2 flex justify-around items-center">
          <button type="button" onclick="nav('hub')" class="${currentGame==='hub' ? 'text-purple-400 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🏠</span><span>Home</span>
          </button>
          <button type="button" onclick="nav('voice_hub')" class="${currentGame==='voice_hub' ? 'text-amber-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🎙️</span><span>Rooms</span>
          </button>
          <button type="button" onclick="nav('sp_wallet')" class="w-12 h-10 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-xl shadow-lg border border-purple-300/40">
            🪙
          </button>
          <button type="button" onclick="nav('sp_pm_hub')" class="${currentGame==='sp_pm_hub'||currentGame==='sp_pm_chat' ? 'text-pink-400 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">💬</span><span>Chats</span>
          </button>
          <button type="button" onclick="nav('sp_store')" class="${currentGame==='sp_store' ? 'text-emerald-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">🛍️</span><span>Store</span>
          </button>
          <button type="button" onclick="openUserProfileModal(${uid})" class="${currentGame==='sp_profile' ? 'text-sky-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black">
            <span class="text-lg">👤</span><span>Profile</span>
          </button>
        </div>
      `;
    }

    function renderTopBar(titleText = '') {
      const me = spState?.me || {};
      return `
        <div class="glass-panel mx-3 mb-2 px-3 py-2 rounded-2xl flex justify-between items-center shrink-0">
          <div class="flex items-center gap-1.5">
            ${currentGame !== 'hub' ? `<button type="button" onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-xs font-extrabold">منو</button>` : `<span class="text-xs font-black text-purple-400">RHINO™</span>`}
            <span class="text-sm font-black text-white truncate max-w-[130px]">${titleText || 'پلتفرم راینو'}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <button type="button" onclick="nav('sp_wallet')" class="glass-soft px-2.5 py-1 rounded-xl text-[11px] font-black text-amber-300 flex items-center gap-1">
              <span>🪙 ${(me.coins ?? 1000).toLocaleString()}</span>
              <span class="text-purple-300">| ⭐ ${me.stars_balance ?? 0}</span>
            </button>
            ${isOwner && currentGame !== 'tower_admin' ? `<button type="button" onclick="nav('tower_admin')" class="btn-primary px-2.5 py-1 rounded-xl text-[11px] font-black text-amber-200">👑</button>` : ''}
          </div>
        </div>
      `;
    }

    async function callSocialApi(action = 'state', extra = {}) {
      try {
        const res = await fetch('/api/social/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ uid: Number(uid), name: myName, username: myUsername, photo: myPhoto, action: action, ...extra })
        });
        const data = await res.json();
        spMsg = data.msg || '';
        spErr = data.ok === false ? (data.error || '') : '';

        if (data.need_pin) {
          const pin = prompt(data.error || 'رمز اتاق صوتی را وارد کنید:');
          if (pin !== null) return callSocialApi('join_room', { room_id: data.room_id, pin_code: pin });
          return;
        }
        if (data.invoice_link && tg?.openInvoice) {
          tg.openInvoice(data.invoice_link, () => callSocialApi('state'));
          return;
        } else if (data.invoice_link) {
          window.open(data.invoice_link, '_blank');
        }
        if (data.state) {
          spState = data.state;
          if (spState.big_wins) window.recentWinsList = spState.big_wins;
        }
        if (data.bombs_state) bombsState = data.bombs_state;
        if (data.crash_result) crashLastResult = data.crash_result;
        if (data.pickaxe_result) pickaxeLastResult = data.pickaxe_result;
        if (data.slot_result) slotLastResult = data.slot_result;
        if (data.viewed_profile) viewedProfileData = data.viewed_profile;
        if (data.pm_chat) activePmChat = data.pm_chat;
        if (data.active_room) {
          activeVoiceRoom = data.active_room;
          currentGame = 'voice_room_live';
          if (activeVoiceRoom.my_mic_invite) {
            if (confirm('🎙️ مدیر اتاق شما را به میکروفون شماره ' + activeVoiceRoom.my_mic_invite + ' دعوت کرده است. می‌پذیرید؟')) {
              return callSocialApi('room_op', { room_id: activeVoiceRoom.room_id, op: 'take_seat', seat_idx: String(activeVoiceRoom.my_mic_invite) });
            }
          }
        }
        if (data.left) {
          activeVoiceRoom = null; minimizedVoiceRoom = null;
          if (vrPollTimer) { clearInterval(vrPollTimer); vrPollTimer = null; }
          currentGame = 'voice_hub';
        }
        render();
      } catch (e) {}
    }

    window.nav = function(g) {
      if (hokmPollTimer) { clearInterval(hokmPollTimer); hokmPollTimer = null; }
      if (guessPollTimer) { clearInterval(guessPollTimer); guessPollTimer = null; }
      if (vrPollTimer && g !== 'voice_room_live') { clearInterval(vrPollTimer); vrPollTimer = null; }
      if (pmPollTimer && g !== 'sp_pm_chat') { clearInterval(pmPollTimer); pmPollTimer = null; }
      spMsg = ''; spErr = '';
      currentGame = g;
      render();
    };

    window.openUserProfileModal = function(targetUid) {
      viewedProfileData = null;
      currentGame = 'sp_profile';
      callSocialApi('view_profile', { target_uid: Number(targetUid) });
    };

    window.openDirectPmChat = function(peerUid) {
      activePmPeerUid = Number(peerUid);
      currentGame = 'sp_pm_chat';
      callSocialApi('pm_op', { op: 'load', peer_uid: activePmPeerUid });
    };

    /* ═══════════════════════════════════════════════════════════════════════════
       ۱. صفحه اصلی (هدر با لول ثروت/جذابیت + نشان متحرک + بازی‌های کازینو و گروهی)
       ═══════════════════════════════════════════════════════════════════════════ */
    function renderHub(root) {
      const me = spState?.me || {};
      const avatarUrl = me.photo || myPhoto || '';
      const displayName = me.display_name || myName;
      const wLvl = me.wealth_level || 1;
      const cLvl = me.charm_level || 1;

      const allCards = [
        { id: "crash",     title: "CRASH",        mode: "PVE",  tag: "HOT", online: 34, cat: "casino", c1: "#581c87", c2: "#ec4899", icon: "🚀" },
        { id: "bombs",     title: "BOMBS",        mode: "PVE",  tag: "NEW", online: 26, cat: "casino", c1: "#78350f", c2: "#f59e0b", icon: "💣" },
        { id: "pickaxe",   title: "HELL PICKAXE", mode: "PVE",  tag: "NEW", online: 18, cat: "casino", c1: "#7f1d1d", c2: "#ef4444", icon: "⛏️" },
        { id: "slot",      title: "ROYAL SLOT",   mode: "SLOT", tag: "NEW", online: 22, cat: "casino", c1: "#312e81", c2: "#8b5cf6", icon: "🎰" },
        { id: "voice_hub", title: "VOICE ROOMS",  mode: "LIVE", tag: "VIP", online: 42, cat: "pvp",    c1: "#1e1b4b", c2: "#a855f7", icon: "🎙️" },
        { id: "hokm",      title: "HOKM 4P",      mode: "PVP",  tag: "HOT", online: 28, cat: "pvp",    c1: "#7f1d1d", c2: "#b91c1c", icon: "♠️" },
        { id: "hokm2p",    title: "HOKM 2P",      mode: "PVP",  tag: "",    online: 12, cat: "pvp",    c1: "#500724", c2: "#db2777", icon: "👑" },
        { id: "dooz",      title: "RINGS 2P",     mode: "PVP",  tag: "",    online: 9,  cat: "pvp",    c1: "#1e1b4b", c2: "#3b82f6", icon: "🟢" },
        { id: "doz4p",     title: "RINGS 4P",     mode: "PVP",  tag: "",    online: 6,  cat: "pvp",    c1: "#4a044e", c2: "#ec4899", icon: "🟣" },
        { id: "connect4",  title: "CONNECT 4",    mode: "PVP",  tag: "",    online: 11, cat: "pvp",    c1: "#064e3b", c2: "#10b981", icon: "🔴" },
        { id: "rps",       title: "ROCK PAPER",   mode: "PVP",  tag: "",    online: 7,  cat: "pvp",    c1: "#312e81", c2: "#6366f1", icon: "✂️" },
        { id: "guess",     title: "NUMBER GUESS", mode: "PVP",  tag: "LIVE",online: 19, cat: "pvp",    c1: "#14532d", c2: "#22c55e", icon: "🎯" },
        { id: "2048",      title: "2048 PUZZLE",  mode: "PVE",  tag: "",    online: 15, cat: "pve",    c1: "#1e3a8a", c2: "#2563eb", icon: "🧩" },
        { id: "spuzzle",   title: "PUZZLE 15",    mode: "PVE",  tag: "",    online: 5,  cat: "pve",    c1: "#0c4a6e", c2: "#0ea5e9", icon: "🔢" }
      ];

      const filteredCards = allCards.filter(c => hubFilter === 'all' ? true : c.cat === hubFilter);
      const cardsHtml = filteredCards.map(g => `
        <div onclick="nav('${g.id}')" class="arcade-card cursor-pointer">
          <img src="${getAssetImg(g.id, '')}" onerror="this.style.display='none'" class="arcade-card-bg" />
          <div style="background: radial-gradient(circle at 75% 70%, ${g.c2}55 0%, ${g.c1}ee 85%);" class="absolute inset-0 -z-10 flex items-center justify-end p-3">
            <span class="text-7xl opacity-45 select-none">${g.icon}</span>
          </div>
          <div class="arcade-card-overlay">
            <div class="arcade-title">${g.title}</div>
            <div class="flex items-center gap-1.5 flex-wrap ltr-grid">
              <span class="pill-players">👤 ${g.online}</span>
              <span class="pill-mode-pve">${g.mode}</span>
              ${g.tag ? `<span class="pill-new">${g.tag}</span>` : ''}
            </div>
          </div>
        </div>
      `).join('');

      root.innerHTML = `
        <div class="glass-panel mx-3 mb-2 px-3 py-2.5 rounded-3xl flex items-center justify-between gap-2 shrink-0 border border-purple-500/25">
          <div onclick="openUserProfileModal(${uid})" class="flex items-center gap-3 min-w-0 flex-1 cursor-pointer py-0.5 pr-1">
            ${window.renderAvatarWithFrame(avatarUrl, displayName, 'w-11 h-11 text-base', me.ring_photo, me.ring_css, 'border-2 border-purple-400')}
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1">
                <span class="font-black text-sm text-white truncate">${displayName}</span>
                ${me.custom_badge_emoji_id ? window.renderTgEmoji(me.custom_badge_emoji_id, me.custom_badge_icon || '💎') : ''}
                ${me.sub_badge ? `<span class="px-1.5 py-0.5 rounded-md bg-amber-500/25 border border-amber-400/50 text-[9px] font-black text-amber-300 shrink-0">${me.sub_badge}</span>` : ''}
              </div>
              <div class="flex items-center gap-1.5 mt-1 text-[10px] font-black">
                <span class="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/30">💰 ثروت Lv.${wLvl}</span>
                <span class="px-2 py-0.5 rounded-full bg-pink-500/20 text-pink-300 border border-pink-400/30">💖 جذابیت Lv.${cLvl}</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <div onclick="nav('sp_wallet')" class="flex flex-col gap-1 items-end cursor-pointer">
              <div class="px-2.5 py-0.5 rounded-full bg-white text-slate-950 font-black text-[11px] flex items-center gap-1 shadow">
                <span>${(me.coins ?? 1000).toLocaleString()}</span><span>🪙</span>
              </div>
              <div class="px-2.5 py-0.5 rounded-full bg-slate-800/90 border border-white/15 text-amber-300 font-black text-[11px] flex items-center gap-1">
                <span>${me.stars_balance ?? 0}</span><span>⭐</span>
              </div>
            </div>
            ${isOwner ? `<button type="button" onclick="nav('tower_admin')" class="w-10 h-10 rounded-full glass-soft flex items-center justify-center text-base border border-amber-400/50">👑</button>` : ''}
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col gap-3">
          <div class="flex items-center justify-between px-1">
            <span class="text-[11px] font-black text-orange-400">🔥 BIG WINS & GAMES</span>
            <div class="flex gap-1.5 text-[10px] font-black">
              <button type="button" onclick="hubFilter='all';renderHub(document.getElementById('app'))" class="px-2.5 py-1 rounded-lg ${hubFilter==='all'?'btn-primary':'glass-soft'}">همه</button>
              <button type="button" onclick="hubFilter='casino';renderHub(document.getElementById('app'))" class="px-2.5 py-1 rounded-lg ${hubFilter==='casino'?'btn-primary':'glass-soft'}">🎰 کازینو</button>
              <button type="button" onclick="hubFilter='pvp';renderHub(document.getElementById('app'))" class="px-2.5 py-1 rounded-lg ${hubFilter==='pvp'?'btn-primary':'glass-soft'}">🎙️ روم و گروهی</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">${cardsHtml}</div>
        </div>
        ${renderBottomNav()}
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۲. اتاق‌های صوتی (پاپ‌آپ صندلی ادمین، خط رابط ازدواج/رفاقت روی مایک مجاور، شنوندگان بدون مایک و افکت گیفت)
       ═══════════════════════════════════════════════════════════════════════════ */
    function renderVoiceHub(root) {
      if (!spState) { callSocialApi('state'); return; }
      const me = spState.me;
      const rooms = spState.rooms || [];

      const roomsGridHtml = rooms.map(r => `
        <div onclick="callSocialApi('join_room',{room_id:${r.room_id}})" class="arcade-card cursor-pointer">
          <img src="${r.photo || '/api/banner/voice_hub.png'}" onerror="this.src='/api/banner/voice_hub.png'" class="arcade-card-bg" />
          <div class="arcade-card-overlay">
            <div class="flex justify-between items-start">
              <span class="px-2 py-0.5 rounded-full bg-black/65 text-[10px] font-black text-amber-300 border border-amber-400/30">Lv.${r.level || 1}/50</span>
              ${r.is_locked ? `<span class="w-7 h-7 rounded-full bg-rose-600/90 flex items-center justify-center text-xs">🔒</span>` : `<span class="px-2 py-0.5 rounded-full bg-emerald-500/80 text-[9px] font-black">LIVE</span>`}
            </div>
            <div>
              <div class="font-black text-sm text-white truncate">${r.title}</div>
              <div class="text-[10px] text-slate-300 truncate mb-1">${r.description || ''}</div>
              <div class="flex items-center justify-between ltr-grid">
                <span class="pill-mode-pve">${r.mic_count} Mic</span>
                <span class="pill-players">👥 ${r.online_count || 1}</span>
              </div>
            </div>
          </div>
        </div>
      `).join('');

      const editModalHtml = vrSheet === 'edit_room' ? renderEditRoomModal(me.room) : '';

      root.innerHTML = `
        ${editModalHtml}
        ${renderTopBar('🎙️ اتاق‌های صوتی زنده')}
        <div class="flex-1 overflow-y-auto px-3 pb-24">
          <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-black text-slate-300">اتاق‌های فعال (${rooms.length})</span>
            <button type="button" onclick="vrSheet='edit_room';renderVoiceHub(document.getElementById('app'))" class="btn-primary px-3.5 py-2 rounded-xl text-xs font-black">
              ${me.room ? '⚙️ تنظیمات اتاق من' : '➕ ساخت اتاق صوتی'}
            </button>
          </div>
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center mb-3">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center mb-3">${spErr}</div>` : ''}
          <div class="grid grid-cols-2 gap-3">${roomsGridHtml || '<div class="col-span-2 glass-panel p-8 rounded-3xl text-center text-xs text-slate-300">هنوز اتاقی ساخته نشده است!</div>'}</div>
        </div>
        ${renderBottomNav()}
      `;
    }

    function renderEditRoomModal(rm) {
      const me = spState?.me || {};
      const allowedMics = rm?.allowed_mic_list || [1, 2, 6, 8];
      return `
        <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div class="glass-panel p-4 rounded-3xl w-full max-w-sm space-y-2.5 text-xs max-h-[90vh] overflow-y-auto border border-purple-400/40">
            <h3 class="text-sm font-black text-amber-300 text-center">🎙️ تنظیمات اتاق صوتی (لول فعلی: Lv.${rm?.level || 1}/50)</h3>
            <input id="rm_title" type="text" value="${rm?.title || ('مجلس ' + myName)}" placeholder="نام اتاق..." class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
            <input id="rm_desc" type="text" value="${rm?.description || 'به اتاق صوتی خوش آمدید!'}" placeholder="معرفی اتاق..." class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />
            <div class="glass-soft p-2.5 rounded-2xl text-center">
              <label class="block text-[11px] text-amber-200 font-bold mb-1">📷 عکس پروفایل اتاق:</label>
              <input type="file" accept="image/*" onchange="handleImageUpload(this, 'my_room_photo', 'prev_my_room_photo')" class="w-full text-[10px]" />
              <img id="prev_my_room_photo" src="${rm?.photo || ''}" class="${rm?.photo ? '' : 'hidden'} w-16 h-16 rounded-2xl object-cover mx-auto mt-2 border border-amber-400" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-300 mb-1">تعداد میکروفون‌ها (با بالا رفتن لول روم تا ۳۶ مایک باز می‌شود):</label>
              <select id="rm_mics" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
                ${[1,2,6,8,10,12,15,17,20,24,30,36].map(n => {
                  const unlocked = allowedMics.includes(n) || isOwner;
                  return `<option value="${n}" ${(rm?.mic_count||8)===n?'selected':''} ${!unlocked?'disabled':''}>${n} Mic ${!unlocked?'🔒 (نیاز به لول بالاتر روم)':''}</option>`;
                }).join('')}
              </select>
            </div>
            <div class="glass-soft p-3 rounded-2xl space-y-2 border ${me.can_lock_room ? 'border-emerald-400/40' : 'border-rose-400/40'}">
              <div class="flex justify-between items-center">
                <span class="font-black text-amber-300">🔒 قفل کردن اتاق (ویژه PRO+):</span>
                <input id="rm_lock" type="checkbox" ${rm?.is_locked ? 'checked' : ''} ${!me.can_lock_room ? 'disabled' : ''} class="w-4 h-4" />
              </div>
              ${me.can_lock_room ? `<input id="rm_pin" type="text" value="${rm?.pin_code || ''}" placeholder="رمز عبور اتاق" class="w-full p-2 rounded-xl bg-slate-900 text-white text-center font-bold" />` : ''}
            </div>
            <div class="grid grid-cols-2 gap-2 pt-2">
              <button type="button" onclick="vrSheet='';callSocialApi('save_my_room',{title:document.getElementById('rm_title').value,description:document.getElementById('rm_desc').value,room_photo:window.uploadedImages['my_room_photo']||'',mic_count:Number(document.getElementById('rm_mics').value),is_locked:document.getElementById('rm_lock').checked,pin_code:document.getElementById('rm_pin')?.value||''})" class="btn-success py-3 rounded-2xl font-black">💾 ذخیره و ورود</button>
              <button type="button" onclick="vrSheet='';render()" class="btn-danger py-3 rounded-2xl font-bold">انصراف</button>
            </div>
          </div>
        </div>
      `;
    }

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

    /* کلیک روی مایک: اگر مالک یا ادمین روم باشد مستقیم منتقل نمی‌شود بلکه منوی مدیریت مایک باز می‌شود */
    window.onVoiceSeatClick = function(seatIdx) {
      const r = activeVoiceRoom;
      if (!r) return;
      if (r.is_room_admin) {
        selectedSeatIdx = Number(seatIdx);
        vrSheet = 'seat_menu';
        drawLiveVoiceRoom(document.getElementById('app'));
      } else {
        callSocialApi('room_op', { room_id: r.room_id, op: 'take_seat', seat_idx: String(seatIdx) });
      }
    };

    window.toggleGiftRecSelection = function(targetUid) {
      const u = Number(targetUid);
      if (selectedGiftRecs.includes(u)) {
        selectedGiftRecs = selectedGiftRecs.filter(x => x !== u);
      } else {
        selectedGiftRecs.push(u);
      }
      drawLiveVoiceRoom(document.getElementById('app'));
    };

    function drawLiveVoiceRoom(root) {
      if (!root || currentGame !== 'voice_room_live' || !activeVoiceRoom) return;
      const r = activeVoiceRoom;
      const me = spState?.me || {};
      const isRoomOwner = (Number(r.owner_id) === Number(uid)) || isOwner;
      const isRoomAdmin = Boolean(r.is_room_admin);

      const mc = r.mic_count || 8;
      const colsCount = mc === 1 ? 1 : (mc === 2 ? 2 : (mc <= 8 ? 4 : (mc <= 15 ? 5 : 6)));
      const gridCols = colsCount === 1 ? 'grid-cols-1 max-w-[110px]' : (colsCount === 2 ? 'grid-cols-2 max-w-[220px]' : (colsCount === 4 ? 'grid-cols-4' : (colsCount === 5 ? 'grid-cols-5' : 'grid-cols-6')));
      const seatSize = mc <= 8 ? 'w-14 h-14 text-lg' : (mc <= 15 ? 'w-12 h-12 text-sm' : 'w-10 h-10 text-xs');

      let seatsHtml = '';
      for (let i = 1; i <= mc; i++) {
        const occ = (r.seats || {})[String(i)];
        const isLockedSeat = (r.locked_seats || []).includes(i);
        const occUid = occ ? Number(occ.uid) : 0;

        // بررسی اینکه آیا صندلی سمت چپ در همین ردیف با این کاربر رابطه ازدواج یا رفاقت دارد (بدون تداخل چپ و راست)
        let bondBridgeHtml = '';
        if (occ && (i % colsCount !== 0)) {
          const nextOcc = (r.seats || {})[String(i + 1)];
          if (nextOcc && occ.bonds && occ.bonds[String(nextOcc.uid)]) {
            const relType = occ.bonds[String(nextOcc.uid)];
            const linkMeta = relType === 'marriage' ? (occ.marriage_link || {icon:'💍', color:'#ec4899'}) : (occ.bestie_link || {icon:'⚡', color:'#06b6d4'});
            bondBridgeHtml = `
              <div style="background: linear-gradient(90deg, transparent, ${linkMeta.color || '#ec4899'}, transparent);"
                   class="absolute top-6 -left-5 w-10 h-1 z-30 flex items-center justify-center pointer-events-none">
                <div class="px-1.5 py-0.5 rounded-full bg-slate-950/90 border border-white/30 shadow-lg animate-pulse">
                  ${window.renderTgEmoji(linkMeta.emoji_id, linkMeta.icon, 'w-4 h-4 inline-block')}
                </div>
              </div>
            `;
          }
        }

        seatsHtml += `
          <div class="relative flex flex-col items-center gap-1.5">
            ${bondBridgeHtml}
            <button type="button" onclick="window.onVoiceSeatClick(${i})"
              class="${seatSize} rounded-full ${occ ? 'bg-indigo-950' : 'bg-white/10 border border-white/25'} flex items-center justify-center relative active:scale-95 transition">
              ${occ ? window.renderAvatarWithFrame(occ.photo, occ.name, 'w-full h-full', occ.ring_photo, occ.ring_css, 'border-2 border-emerald-400', !occ.muted) : (isLockedSeat ? '🔒' : '➕')}
              ${occ?.muted ? `<span class="absolute -bottom-0.5 -right-0.5 z-30 bg-rose-600 text-[9px] rounded-full px-1">🔇</span>` : ''}
            </button>
            <div onclick="${occ ? `openUserProfileModal(${occUid})` : `window.onVoiceSeatClick(${i})`}" class="text-[10px] font-bold text-slate-200 truncate max-w-[68px] cursor-pointer flex items-center gap-0.5">
              ${occ?.badge_emoji_id ? window.renderTgEmoji(occ.badge_emoji_id, '', 'w-3.5 h-3.5') : ''}
              <span>${occ ? occ.name : i}</span>
            </div>
          </div>
        `;
      }

      // لیست کاربران بدون مایک (شنوندگان پایین مایک‌ها)
      const listeners = r.unseated_listeners || [];
      const listenersHtml = listeners.map(m => `
        <div onclick="openUserProfileModal(${m.uid})" class="glass-soft px-2 py-1 rounded-full flex items-center gap-1.5 cursor-pointer shrink-0">
          ${window.renderAvatarWithFrame(m.photo, m.name, 'w-5 h-5 text-[8px]', m.ring_photo, m.ring_css)}
          <span class="text-[10px] font-bold text-slate-200 truncate max-w-[65px]">${m.name}</span>
        </div>
      `).join('');

      // افکت تمام‌صفحه ارسال گیفت با اوپاسیتی ملایم برای چند ثانیه
      const gfx = r.gift_fx;
      const giftOverlayHtml = gfx ? `
        <div class="fixed inset-0 z-40 pointer-events-none flex flex-col items-center justify-center bg-black/25 backdrop-blur-[2px] animate-pulse">
          <div class="p-6 rounded-3xl bg-purple-950/55 border border-amber-400/50 text-center shadow-2xl" style="opacity: 0.85;">
            <div class="text-6xl mb-2">
              ${gfx.custom_emoji_id ? window.renderTgEmoji(gfx.custom_emoji_id, gfx.icon, 'w-20 h-20 mx-auto') : (gfx.photo ? `<img src="${gfx.photo}" class="w-20 h-20 object-contain mx-auto" />` : gfx.icon)}
            </div>
            <div class="text-sm font-black text-amber-300">🎁 ${gfx.sender} ⬅️ ${gfx.recipients}</div>
            <div class="text-xs font-extrabold text-white mt-1">${gfx.gift_name} (${gfx.coins.toLocaleString()} 🪙)</div>
          </div>
        </div>
      ` : '';

      // پاپ‌آپ‌های مدیریتی (پاپ‌آپ صندلی برای مالک/ادمین، انتخاب گیرندگان گیفت، مدیریت ادمین‌ها)
      let modalSheetHtml = '';
      if (vrSheet === 'seat_menu') {
        const sIdx = selectedSeatIdx;
        const isLocked = (r.locked_seats || []).includes(sIdx);
        const occ = (r.seats || {})[String(sIdx)];
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-2.5 text-xs border-t border-purple-400">
              <h3 class="font-black text-sm text-amber-300 text-center">🎙️ مدیریت میکروفون شماره ${sIdx}</h3>
              <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'take_seat',seat_idx:'${sIdx}'})" class="btn-success w-full py-3 rounded-2xl font-black">🪑 نشستن / انتقال به این میکروفون</button>
              <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_seat_lock',seat_idx:${sIdx}})" class="btn-primary w-full py-3 rounded-2xl font-black">
                ${isLocked ? '🔓 باز کردن قفل این میکروفون' : '🔒 قفل کردن این میکروفون'}
              </button>
              ${occ ? `<button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'kick_from_seat',seat_idx:'${sIdx}'})" class="btn-danger w-full py-3 rounded-2xl font-black">⬇️ پایین آوردن ${occ.name} از مایک</button>` : ''}
              <div class="pt-2 border-t border-white/10">
                <div class="text-[11px] text-slate-300 font-bold mb-1.5 text-center">📩 دعوت کاربر حاضر در روم به این مایک:</div>
                <div class="flex gap-1.5 overflow-x-auto pb-1">
                  ${(r.unseated_listeners || []).map(u => `
                    <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'invite_to_seat',seat_idx:'${sIdx}',target_uid:${u.uid}})" class="glass-soft px-3 py-1.5 rounded-xl font-bold shrink-0">➕ ${u.name}</button>
                  `).join('') || '<span class="text-slate-400 text-[10px] mx-auto">همه اعضا روی مایک هستند</span>'}
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (vrSheet === 'gifts') {
        const gifts = (spState?.store_items || []).filter(x => x.category === 'gift');
        const allInRoom = r.visible_members || [];
        if (!selectedGiftRecs.length && r.owner_id) selectedGiftRecs = [Number(r.owner_id)];
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-3 border-t border-amber-400/40 text-xs">
              <div class="flex justify-between items-center font-black">
                <span class="text-amber-300">🎁 ارسال گیفت (انتخاب یک یا چند نفر از اعضای روم):</span>
                <button type="button" onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))">✖</button>
              </div>
              <div class="flex gap-1.5 overflow-x-auto pb-1">
                ${allInRoom.map(m => {
                  const sel = selectedGiftRecs.includes(Number(m.uid));
                  return `<button type="button" onclick="window.toggleGiftRecSelection(${m.uid})" class="px-2.5 py-1.5 rounded-xl font-bold shrink-0 border ${sel ? 'btn-success border-white' : 'glass-soft border-white/10'}">👤 ${m.name}</button>`;
                }).join('')}
              </div>
              <div class="grid grid-cols-4 gap-2 text-center">
                ${gifts.map(g => `
                  <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'send_gift',gift_id:${g.id},recipient_uids:selectedGiftRecs});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1 hover:border-amber-400">
                    <div class="text-2xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-8 h-8') : (g.photo ? `<img src="${g.photo}" class="w-8 h-8 object-contain" />` : g.icon)}</div>
                    <span class="font-bold text-[10px] truncate w-full">${g.name}</span>
                    <span class="text-[10px] text-amber-300 font-black">${g.price_coins} 🪙</span>
                  </button>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      } else if (vrSheet === 'manage') {
        modalSheetHtml = `
          <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
            <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-3 text-xs border-t border-purple-400">
              <div class="flex justify-between items-center font-black text-amber-300">
                <span>🎛️ ابزارهای مدیریت اتاق (Lv.${r.level}/50 — سقف مجاز: ${r.max_allowed_mics} مایک)</span>
                <button type="button" onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))">✖</button>
              </div>
              <div class="grid grid-cols-4 gap-2 text-center font-bold">
                ${(r.allowed_mic_list || [1,2,6,8]).map(n => `
                  <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'change_layout',mic_count:${n}})" class="p-2 rounded-xl ${r.mic_count===n?'btn-primary':'glass-soft'}">${n} Mic</button>
                `).join('')}
              </div>
              <div class="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 font-bold">
                <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_lock_room'})" class="glass-soft p-2.5 rounded-xl">${r.is_locked ? '🔓 باز کردن قفل' : '🔒 قفل اتاق'}</button>
                <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'clear_chat'})" class="glass-soft p-2.5 rounded-xl">🧹 پاکسازی چت</button>
                <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_pk'})" class="glass-soft p-2.5 rounded-xl">⚔️ حالت PK</button>
              </div>
              ${isRoomOwner ? `
                <div class="pt-2 border-t border-white/10 space-y-1.5">
                  <div class="font-black text-indigo-300 text-center">🛡️ نصب یا عزل ادمین‌های اتاق (روی عضو بزنید):</div>
                  <div class="flex gap-1.5 flex-wrap justify-center">
                    ${(r.visible_members || []).filter(m => Number(m.uid) !== Number(r.owner_id)).map(m => {
                      const isAdm = (r.admins_list || []).includes(Number(m.uid));
                      return `<button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'set_room_admin',target_uid:${m.uid}})" class="px-2.5 py-1 rounded-xl ${isAdm ? 'btn-success' : 'glass-soft'}">${isAdm ? '🛡️ ادمین: ' : '➕ '}${m.name}</button>`;
                    }).join('') || '<span class="text-slate-400">عضو دیگری در اتاق نیست</span>'}
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        `;
      }

      const chatsHtml = (r.chats || []).map(c => c.sys ? `
        <div class="px-3 py-1 rounded-2xl ${c.gift ? 'bg-amber-500/25 border border-amber-400/50 text-amber-200' : 'bg-teal-950/60 text-teal-300'} text-[11px] font-bold">${c.text}</div>
      ` : `
        <div class="px-3 py-1 rounded-2xl bg-black/45 text-xs">
          <span onclick="openUserProfileModal(${c.uid})" class="font-black text-amber-300 cursor-pointer">${c.badge_emoji_id ? window.renderTgEmoji(c.badge_emoji_id, '', 'w-4 h-4') : ''} ${c.name}:</span>
          <span class="text-white mr-1">${c.text}</span>
        </div>
      `).join('');

      const imSeated = Object.values(r.seats || {}).some(s => s && Number(s.uid) === Number(uid));

      root.innerHTML = `
        ${giftOverlayHtml}
        ${modalSheetHtml}
        <div class="flex-1 flex flex-col justify-between p-3 overflow-hidden relative" style="background: radial-gradient(circle at 50% 20%, #1e1b4b 0%, #090514 88%);">
          <!-- هدر اتاق صوتی با نوار پیشرفت لول تا ۵۰ -->
          <div class="flex items-center justify-between gap-2 shrink-0">
            <div class="glass-panel px-2.5 py-1.5 rounded-2xl flex items-center gap-2">
              <img src="${r.photo || '/api/banner/voice_hub.png'}" class="w-9 h-9 rounded-xl object-cover border border-amber-400" />
              <div>
                <div class="font-black text-xs text-amber-200">👑 ${r.title} ${r.is_locked ? '🔒' : ''}</div>
                <div class="text-[10px] text-emerald-300 font-bold">Lv.${r.level}/50 (${r.level_pct}%) • 🪙 ${(r.total_gifts||0).toLocaleString()}</div>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="px-2.5 py-1 rounded-xl glass-soft text-[11px] font-black">👥 ${r.online_count || 1}</span>
              <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'leave_room'})" class="w-8 h-8 rounded-full btn-danger flex items-center justify-center text-xs font-black">⏻</button>
            </div>
          </div>

          <!-- چیدمان مایک‌ها + خطوط رابط ازدواج و رفاقت بین مایک‌های مجاور -->
          <div class="my-auto py-2 overflow-y-auto max-h-[42vh] flex justify-center">
            <div class="grid ${gridCols} gap-3.5 justify-items-center w-full">${seatsHtml}</div>
          </div>

          <!-- بخش کاربران بدون مایک (شنوندگان داخل اتاق) -->
          <div class="glass-panel px-3 py-1.5 rounded-2xl mb-1.5 shrink-0">
            <div class="text-[9px] font-black text-slate-400 mb-1">🎧 حاضرین بدون مایک (${listeners.length} نفر):</div>
            <div class="flex gap-1.5 overflow-x-auto pb-0.5">${listenersHtml || '<span class="text-[10px] text-slate-500">همه حاضرین روی مایک هستند</span>'}</div>
          </div>

          <!-- چت زنده اتاق -->
          <div class="flex flex-col gap-1 max-h-[20vh] overflow-y-auto mb-1.5 pr-1">${chatsHtml}</div>

          <!-- نوار پایین اتاق + کیبورد ایموجی‌های پریمیوم -->
          <div class="flex items-center gap-1.5 shrink-0">
            <div class="flex-1 flex items-center gap-1 glass-panel rounded-full px-3 py-1.5">
              <input id="vrChatInp" type="text" placeholder="پیام در اتاق..." onkeydown="if(event.key==='Enter'){callSocialApi('room_op',{room_id:${r.room_id},op:'chat',text:this.value});this.value='';}" class="flex-1 bg-transparent text-xs text-white outline-none" />
              <button type="button" onclick="const el=document.getElementById('vrChatInp');if(el.value){callSocialApi('room_op',{room_id:${r.room_id},op:'chat',text:el.value});el.value='';}" class="text-purple-300 font-black text-xs">ارسال</button>
            </div>
            ${imSeated ? `
              <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_my_mic'})" class="w-10 h-10 rounded-full btn-success flex items-center justify-center text-base">🎙️</button>
              <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'leave_seat'})" class="w-10 h-10 rounded-full btn-danger flex items-center justify-center text-xs font-bold">⬇️</button>
            ` : ''}
            ${isRoomAdmin ? `<button type="button" onclick="vrSheet='manage';drawLiveVoiceRoom(document.getElementById('app'))" class="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-base">🎛️</button>` : ''}
            <button type="button" onclick="vrSheet='gifts';drawLiveVoiceRoom(document.getElementById('app'))" class="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-rose-500 flex items-center justify-center text-base shadow-lg">🎁</button>
          </div>
        </div>
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۳. چت خصوصی (PV) داخل مینی‌اپ با ارسال ویس، تعیین بک‌گراند، ایموجی پریمیوم و لول ارتباط
       ═══════════════════════════════════════════════════════════════════════════ */
    window.toggleVoiceRecording = async function() {
      if (!isRecordingVoice) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];
          mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
          mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();
            reader.onloadend = () => {
              callSocialApi('pm_op', { op: 'send', peer_uid: activePmPeerUid, msg_type: 'voice', voice_data: reader.result });
            };
            reader.readAsDataURL(blob);
            stream.getTracks().forEach(t => t.stop());
          };
          mediaRecorder.start();
          isRecordingVoice = true;
          render();
        } catch (err) {
          alert('دسترسی به میکروفون داده نشد!');
        }
      } else {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
        isRecordingVoice = false;
        render();
      }
    };

    function renderSpPmHub(root) {
      if (!spState) { callSocialApi('state'); return; }
      const peers = spState.inbox_peers || [];
      const rels = spState.me?.relationships || {};
      const pendingHtml = (rels.pending || []).map(p => `
        <div class="glass-panel p-3 rounded-2xl flex items-center justify-between text-xs border border-pink-400/50">
          <span>💌 درخواست <b>${p.pending_type === 'marriage' ? 'ازدواج 💍' : 'رفاقت ⚡'}</b> از <b>${p.partner_name}</b></span>
          ${Number(p.requested_by) !== Number(uid) ? `
            <div class="flex gap-1.5">
              <button type="button" onclick="callSocialApi('rel_op',{op:'respond',target_uid:${p.partner_uid},accept:true})" class="btn-success px-3 py-1 rounded-xl font-black">قبول</button>
              <button type="button" onclick="callSocialApi('rel_op',{op:'respond',target_uid:${p.partner_uid},accept:false})" class="btn-danger px-3 py-1 rounded-xl font-bold">رد</button>
            </div>
          ` : `<span class="text-amber-300 font-bold">در انتظار تایید...</span>`}
        </div>
      `).join('');

      root.innerHTML = `
        ${renderTopBar('💬 چت خصوصی و روابط')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3 text-xs">
          <div class="glass-panel p-3 rounded-2xl flex gap-2">
            <input id="pm_search_uid" type="number" placeholder="آیدی عددی مخاطب برای شروع چت..." class="flex-1 p-2.5 rounded-xl glass-soft text-center text-white font-bold" />
            <button type="button" onclick="const v=document.getElementById('pm_search_uid').value;if(v)openDirectPmChat(v)" class="btn-primary px-4 rounded-xl font-black">شروع چت</button>
          </div>
          ${pendingHtml}
          <div class="space-y-2">
            ${peers.map(p => `
              <div onclick="openDirectPmChat(${p.user_id})" class="glass-panel p-3 rounded-2xl flex items-center justify-between cursor-pointer">
                <div class="flex items-center gap-2.5">
                  <img src="${p.photo || '/api/banner/hub.png'}" class="w-11 h-11 rounded-full object-cover border border-purple-400" />
                  <div>
                    <div class="font-black text-sm text-white">${p.display_name}</div>
                    <div class="text-[10px] text-slate-400">ID: ${p.user_id}</div>
                  </div>
                </div>
                <span class="btn-primary px-3 py-1.5 rounded-xl font-black">ورود به پیوی ◀</span>
              </div>
            `).join('') || '<div class="glass-panel p-6 rounded-3xl text-center text-slate-400">هنوز گفتگویی ندارید! روی پروفایل کاربران بزنید یا آیدی عددی وارد کنید.</div>'}
          </div>
        </div>
        ${renderBottomNav()}
      `;
    }

    function renderSpPmChat(root) {
      if (!activePmChat) {
        root.innerHTML = `${renderTopBar('💬 چت خصوصی')}<div class="p-6 text-center">در حال بارگذاری چت...</div>`;
        return;
      }
      const c = activePmChat;
      const peer = c.peer || {};
      const customBgStyle = c.chat_bg ? (c.chat_bg.startsWith('data:image') ? `background-image:url('${c.chat_bg}');background-size:cover;` : `background:${c.chat_bg};`) : '';
      const emojiPacks = spState?.chat_emojis || [];

      const msgsHtml = (c.messages || []).map(m => {
        const isMine = Number(m.sender_id) === Number(uid);
        return `
          <div class="flex ${isMine ? 'justify-start' : 'justify-end'}">
            <div class="max-w-[78%] px-3.5 py-2 rounded-2xl text-xs ${isMine ? 'btn-primary text-white' : 'glass-panel text-slate-100'}">
              ${m.msg_type === 'voice' && m.voice_data ? `<audio controls src="${m.voice_data}" class="h-8 w-44"></audio>` : `<div>${m.text}</div>`}
              <div class="text-[9px] opacity-65 text-left mt-0.5">${m.time}</div>
            </div>
          </div>
        `;
      }).join('');

      root.innerHTML = `
        <div class="glass-panel mx-3 mb-1.5 px-3 py-2 rounded-2xl flex items-center justify-between shrink-0 text-xs">
          <div onclick="openUserProfileModal(${peer.user_id})" class="flex items-center gap-2 cursor-pointer">
            <button type="button" onclick="event.stopPropagation();nav('sp_pm_hub')" class="btn-danger px-2 py-1 rounded-lg">🔙</button>
            ${window.renderAvatarWithFrame(peer.photo, peer.display_name, 'w-8 h-8 text-xs', peer.ring_photo, peer.ring_css)}
            <div>
              <div class="font-black text-white">${peer.display_name}</div>
              <div class="text-[10px] text-pink-300 font-bold">❤️ لول ارتباط: Lv.${c.affinity_level} (${c.affinity_pts} امتیاز)</div>
            </div>
          </div>
          <div class="flex gap-1">
            <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${peer.user_id},rel_type:'bestie'})" class="glass-soft px-2 py-1 rounded-lg text-[10px] font-bold">⚡ رفاقت</button>
            <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${peer.user_id},rel_type:'marriage'})" class="glass-soft px-2 py-1 rounded-lg text-[10px] font-bold">💍 ازدواج</button>
          </div>
        </div>

        <div style="${customBgStyle}" class="flex-1 overflow-y-auto mx-3 rounded-3xl p-3 space-y-2 border border-white/10">
          ${msgsHtml || '<div class="text-center text-xs text-slate-400 my-auto">اولین پیام یا ویس را بفرستید تا لول ارتباط شما بالا برود!</div>'}
        </div>

        <!-- نوار انتخاب بک‌گراند چت و ایموجی‌های پریمیوم متحرک -->
        <div class="mx-3 mt-1.5 flex items-center justify-between gap-2 text-[10px]">
          <div class="flex gap-1">
            <button type="button" onclick="callSocialApi('pm_op',{op:'set_bg',peer_uid:${peer.user_id},chat_bg:'linear-gradient(135deg,#3b0764,#090514)'})" class="w-5 h-5 rounded-full bg-purple-800 border border-white/40"></button>
            <button type="button" onclick="callSocialApi('pm_op',{op:'set_bg',peer_uid:${peer.user_id},chat_bg:'linear-gradient(135deg,#831843,#090514)'})" class="w-5 h-5 rounded-full bg-pink-800 border border-white/40"></button>
            <button type="button" onclick="callSocialApi('pm_op',{op:'set_bg',peer_uid:${peer.user_id},chat_bg:'linear-gradient(135deg,#064e3b,#090514)'})" class="w-5 h-5 rounded-full bg-emerald-800 border border-white/40"></button>
          </div>
          <div class="flex gap-1.5 overflow-x-auto">
            ${emojiPacks.map(ep => `
              <button type="button" onclick="callSocialApi('pm_op',{op:'send',peer_uid:${peer.user_id},msg_type:'text',text:'${ep.icon}'})" class="glass-soft px-1.5 py-0.5 rounded-lg">
                ${window.renderTgEmoji(ep.id, ep.icon, 'w-5 h-5')}
              </button>
            `).join('')}
          </div>
        </div>

        <div class="mx-3 mt-1.5 pb-20 flex items-center gap-1.5 shrink-0">
          <input id="pmTxtInp" type="text" placeholder="پیام خصوصی..." onkeydown="if(event.key==='Enter'){callSocialApi('pm_op',{op:'send',peer_uid:${peer.user_id},msg_type:'text',text:this.value});this.value='';}" class="flex-1 px-3.5 py-2.5 rounded-2xl glass-panel text-xs text-white outline-none" />
          <button type="button" onclick="const el=document.getElementById('pmTxtInp');if(el.value){callSocialApi('pm_op',{op:'send',peer_uid:${peer.user_id},msg_type:'text',text:el.value});el.value='';}" class="btn-primary px-4 py-2.5 rounded-2xl text-xs font-black">ارسال</button>
          <button type="button" onclick="window.toggleVoiceRecording()" class="${isRecordingVoice ? 'btn-danger animate-pulse' : 'btn-success'} px-3 py-2.5 rounded-2xl text-xs font-black">
            ${isRecordingVoice ? '⏹️ ارسال ویس' : '🎙️ ویس'}
          </button>
        </div>
        ${renderBottomNav()}
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۴. پروفایل کاربری (لول ثروت و جذابیت تا ۵۰، گیفت‌های شناور نئونی روی کارت، کارت‌های روابط ازدواج/رفاقت و ست کردن ایموجی پریمیوم جلوی اسم)
       ═══════════════════════════════════════════════════════════════════════════ */
    window.toggleShowcaseGift = function(giftId) {
      const me = spState?.me;
      if (!me) return;
      let arr = [...(me.showcased_gifts || [])].map(Number);
      const gid = Number(giftId);
      if (arr.includes(gid)) arr = arr.filter(x => x !== gid);
      else if (arr.length < 6) arr.push(gid);
      callSocialApi('save_profile', { showcased_gifts: arr });
    };

    function renderSpProfile(root) {
      if (!spState) { callSocialApi('state'); return; }
      const me = spState.me;
      const p = viewedProfileData || me;
      const isMe = Number(p.user_id) === Number(uid);
      const themes = spState.profile_themes || [];
      const curTheme = themes.find(t => t.id === p.card_theme) || themes[0];
      const glowColor = curTheme?.glow || '#c084fc';

      // گیفت‌های شناور نامنظم روی کارت پروفایل با هاله نئون کمی روشن‌تر از کارت
      const floatPositions = [
        "top: 14px; right: 16px; animation-delay: 0s;",
        "top: 18px; left: 18px; animation-delay: 0.7s;",
        "bottom: 78px; right: 22px; animation-delay: 1.3s;",
        "bottom: 82px; left: 22px; animation-delay: 1.9s;",
        "top: 48%; right: 12px; animation-delay: 0.4s;",
        "top: 46%; left: 12px; animation-delay: 1.1s;"
      ];
      const invMap = {};
      (p.received_gifts_inv || []).forEach(g => { invMap[Number(g.id)] = g; });
      const floatingGiftsHtml = (p.showcased_gifts || []).slice(0, 6).map((gid, idx) => {
        const g = invMap[Number(gid)];
        if (!g) return '';
        return `
          <div style="${floatPositions[idx % floatPositions.length]} filter: drop-shadow(0 0 10px ${glowColor}); box-shadow: 0 0 14px ${glowColor}66;"
               class="floating-profile-gift absolute z-20 w-10 h-10 rounded-2xl bg-white/15 backdrop-blur-md border border-white/40 flex items-center justify-center text-xl pointer-events-none">
            ${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-7 h-7') : (g.photo ? `<img src="${g.photo}" class="w-7 h-7 object-contain" />` : g.icon)}
          </div>
        `;
      }).join('');

      const rels = p.relationships || { marriage: null, besties: [] };

      root.innerHTML = `
        ${renderTopBar('👤 پروفایل کاربری')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3 text-xs">
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 font-bold text-center">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 font-bold text-center">${spErr}</div>` : ''}

          <!-- کارت اصلی پروفایل با گیفت‌های شناور نئونی و لول ثروت/جذابیت -->
          <div style="background: ${curTheme?.css || '#3b0764'};" class="p-5 rounded-3xl border border-white/25 shadow-2xl text-center relative overflow-hidden">
            ${floatingGiftsHtml}
            <div class="relative inline-block my-2 z-10">
              ${window.renderAvatarWithFrame(p.photo, p.display_name, 'w-24 h-24 text-3xl', p.ring_photo, p.ring_css, 'border-2 border-white')}
            </div>
            <div class="text-lg font-black text-white flex items-center justify-center gap-1.5 mt-1 relative z-10">
              <span>${p.display_name}</span>
              ${p.custom_badge_emoji_id ? window.renderTgEmoji(p.custom_badge_emoji_id, p.custom_badge_icon || '💎', 'w-6 h-6') : ''}
              ${p.sub_badge ? `<span class="px-2.5 py-0.5 rounded-full bg-black/55 border border-amber-300 text-amber-300 text-xs font-black">${p.sub_badge}</span>` : ''}
            </div>
            <div class="text-[11px] text-white/80 font-mono mb-2">ID: ${p.user_id}</div>
            <p class="text-xs text-white/95 bg-black/30 p-2.5 rounded-2xl max-w-xs mx-auto mb-3">${p.bio}</p>

            <!-- نوار دوگانه لول ثروت (Wealth) و لول جذابیت (Charm) تا ۵۰ -->
            <div class="grid grid-cols-2 gap-2.5 bg-black/35 p-3 rounded-2xl text-right">
              <div>
                <div class="flex justify-between text-[10px] font-black text-amber-300 mb-1">
                  <span>💰 لول ثروت</span><span>Lv.${p.wealth_level || 1}/50</span>
                </div>
                <div class="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div style="width:${Math.max(8, p.wealth_pct || 0)}%" class="h-full bg-gradient-to-r from-amber-500 to-yellow-300"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-[10px] font-black text-pink-300 mb-1">
                  <span>💖 لول جذابیت</span><span>Lv.${p.charm_level || 1}/50</span>
                </div>
                <div class="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                  <div style="width:${Math.max(8, p.charm_pct || 0)}%" class="h-full bg-gradient-to-r from-pink-500 to-rose-400"></div>
                </div>
              </div>
            </div>

            ${!isMe ? `
              <div class="grid grid-cols-3 gap-2 mt-3">
                <button type="button" onclick="openDirectPmChat(${p.user_id})" class="btn-primary py-2.5 rounded-xl font-black">💬 چت پیوی</button>
                <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${p.user_id},rel_type:'marriage'})" class="btn-danger py-2.5 rounded-xl font-black">💍 ازدواج</button>
                <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${p.user_id},rel_type:'bestie'})" class="btn-success py-2.5 rounded-xl font-black">⚡ رفاقت</button>
              </div>
            ` : ''}
          </div>

          <!-- بخش کارت‌های جذاب روابط کاربر (۱ ازدواج + تا ۵ رفیق صمیمی) -->
          <div class="glass-panel p-4 rounded-3xl space-y-2.5">
            <h4 class="font-black text-amber-300 text-center">💞 روابط رسمی و پارتنرها (۱ ازدواج • ۵ رفیق)</h4>
            ${rels.marriage ? `
              <div onclick="openUserProfileModal(${rels.marriage.partner_uid})" class="p-3 rounded-2xl bg-gradient-to-r from-rose-900/70 via-pink-900/60 to-purple-900/70 border border-pink-400/60 flex items-center justify-between cursor-pointer">
                <div class="flex items-center gap-2.5">
                  <img src="${rels.marriage.partner_photo || '/api/banner/hub.png'}" class="w-11 h-11 rounded-full object-cover border-2 border-pink-300" />
                  <div>
                    <div class="font-black text-white">💍 همسر / پارتنر: ${rels.marriage.partner_name}</div>
                    <div class="text-[10px] text-pink-200 font-bold">❤️ لول عشق: Lv.${rels.marriage.affinity_level} (${rels.marriage.affinity_pts} امتیاز)</div>
                  </div>
                </div>
                ${window.renderTgEmoji(p.marriage_link?.emoji_id, p.marriage_link?.icon || '💍', 'w-7 h-7')}
              </div>
            ` : `<div class="glass-soft p-2.5 rounded-2xl text-center text-slate-400">💍 هنوز پارتنر ازدواج ثبت نشده است.</div>`}

            <div class="grid grid-cols-2 gap-2">
              ${(rels.besties || []).map(b => `
                <div onclick="openUserProfileModal(${b.partner_uid})" class="p-2.5 rounded-2xl bg-gradient-to-br from-cyan-950/80 to-indigo-950/80 border border-cyan-400/40 flex items-center gap-2 cursor-pointer">
                  <img src="${b.partner_photo || '/api/banner/hub.png'}" class="w-9 h-9 rounded-full object-cover border border-cyan-300" />
                  <div class="min-w-0">
                    <div class="font-black text-[11px] text-cyan-200 truncate">⚡ ${b.partner_name}</div>
                    <div class="text-[9px] text-slate-300">Lv.${b.affinity_level}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- نمایش اتاق صوتی در پروفایل -->
          ${p.room ? `
            <div onclick="callSocialApi('join_room',{room_id:${p.room.room_id}})" class="glass-panel p-3.5 rounded-3xl flex items-center justify-between cursor-pointer border border-purple-400/40">
              <div class="flex items-center gap-3">
                <img src="${p.room.photo || p.photo || '/api/banner/voice_hub.png'}" class="w-12 h-12 rounded-2xl object-cover" />
                <div>
                  <div class="font-black text-white">🎙️ اتاق صوتی: ${p.room.title}</div>
                  <div class="text-[10px] text-emerald-300">Lv.${p.room.level}/50 • 👥 ${p.room.online_count || 1} نفر آنلاین</div>
                </div>
              </div>
              <span class="btn-success px-3 py-1.5 rounded-xl font-black">ورود ◀</span>
            </div>
          ` : ''}

          ${isMe ? `
            <!-- انتخاب گیفت‌های دریافتی برای شناور شدن روی کارت پروفایل -->
            <div class="glass-panel p-4 rounded-3xl space-y-2">
              <h4 class="font-black text-pink-300 text-center">✨ انتخاب گیفت‌های دریافتی برای شناور شدن روی کارت پروفایل (حداکثر ۶ عدد)</h4>
              <div class="grid grid-cols-4 gap-2">
                ${(p.received_gifts_inv || []).map(g => {
                  const active = (p.showcased_gifts || []).map(Number).includes(Number(g.id));
                  return `
                    <button type="button" onclick="window.toggleShowcaseGift(${g.id})" class="p-2 rounded-2xl border ${active ? 'border-pink-400 bg-pink-950/60' : 'border-white/10 glass-soft'} flex flex-col items-center gap-1">
                      <div class="text-2xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-7 h-7') : g.icon}</div>
                      <span class="text-[9px] font-bold truncate w-full">${g.name} (x${g.count})</span>
                    </button>
                  `;
                }).join('') || '<div class="col-span-4 text-center text-slate-400 py-2">هنوز گیفتی دریافت نکرده‌اید.</div>'}
              </div>
            </div>

            <!-- ست کردن ایموجی پریمیوم متحرک جلوی نام + رنگ‌های کارت پروفایل -->
            <div class="glass-panel p-4 rounded-3xl space-y-3">
              <h4 class="font-black text-amber-300 text-center">🌟 ایموجی پریمیوم متحرک جلوی نام (ویژه مشترکین VIP)</h4>
              <div class="flex gap-2">
                <input id="sp_badge_eid" type="text" value="${p.custom_badge_emoji_id || ''}" placeholder="آیدی ۱۹ رقمی ایموجی پریمیوم..." class="flex-1 p-2.5 rounded-xl glass-soft text-center text-white ltr-grid" />
                <button type="button" onclick="callSocialApi('arm_user_badge_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary px-3 rounded-xl font-black">📩 ارسال به ربات</button>
              </div>

              <h4 class="font-black text-indigo-300 text-center pt-2">🎨 رنگ‌ها و تم‌های کارت پروفایل (شامل تم‌های جدید ULTRA)</h4>
              <div class="grid grid-cols-2 gap-2">
                ${themes.map(t => `
                  <button type="button" onclick="callSocialApi('save_profile',{card_theme:'${t.id}'})" style="background:${t.css}" class="px-2.5 py-2 rounded-xl text-[10px] font-black border ${p.card_theme===t.id ? 'border-white scale-105' : 'border-white/20 opacity-85'} flex items-center justify-between">
                    <span>${t.title}</span>
                    ${t.tier !== 'free' ? `<span class="px-1 rounded bg-black/50 text-amber-300 text-[8px]">${t.tier.toUpperCase()}</span>` : ''}
                  </button>
                `).join('')}
              </div>

              <input id="sp_name_inp" type="text" value="${p.display_name}" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
              <input id="sp_bio_inp" type="text" value="${p.bio}" class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />
              <button type="button" onclick="callSocialApi('save_profile',{display_name:document.getElementById('sp_name_inp').value,bio:document.getElementById('sp_bio_inp').value,card_theme:'${p.card_theme}',custom_badge_emoji_id:document.getElementById('sp_badge_eid').value})" class="btn-success w-full py-3 rounded-2xl font-black">💾 ذخیره تغییرات پروفایل</button>
            </div>
          ` : ''}
        </div>
        ${renderBottomNav()}
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۵. فروشگاه (اشتراک‌ها، کاورهای PNG دور پروفایل، خط رابط ازدواج/رفاقت و گیفت‌های متحرک)
       ═══════════════════════════════════════════════════════════════════════════ */
    function renderSpStore(root) {
      if (!spState) { callSocialApi('state'); return; }
      const me = spState.me;
      const subs = (spState.sub_tiers || []).filter(s => s.id !== 'free');
      const rings = (spState.store_items || []).filter(i => i.category === 'ring');
      const relLinks = (spState.store_items || []).filter(i => i.category === 'rel_marriage' || i.category === 'rel_bestie');
      const gifts = (spState.store_items || []).filter(i => i.category === 'gift');

      let contentHtml = '';
      if (storeTab === 'subs') {
        contentHtml = subs.map(s => `
          <div class="glass-panel p-4 rounded-3xl space-y-2 border ${me.sub_tier===s.id ? 'border-emerald-400' : 'border-purple-400/40'}">
            <div class="flex justify-between items-center"><span class="text-base font-black">${s.title}</span><span class="text-amber-300 font-black">${s.badge}</span></div>
            <ul class="text-xs text-slate-200 space-y-1 pr-2">${s.perks.map(pk => `<li>✅ ${pk}</li>`).join('')}</ul>
            <div class="grid grid-cols-2 gap-2 pt-2">
              <button type="button" onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'coins'})" class="btn-success py-2.5 rounded-xl font-black text-xs">🪙 ${s.coins.toLocaleString()} سکه</button>
              <button type="button" onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'direct_stars'})" class="btn-primary py-2.5 rounded-xl font-black text-xs">⭐ ${s.stars} استارز</button>
            </div>
          </div>
        `).join('');
      } else if (storeTab === 'rings') {
        contentHtml = rings.map(r => {
          const owned = (me.owned_rings || []).includes(Number(r.id));
          const equipped = Number(me.avatar_ring_id) === Number(r.id);
          return `
            <div class="glass-panel p-3.5 rounded-3xl flex items-center justify-between gap-3">
              <div class="flex items-center gap-3.5">
                <div class="p-1">${window.renderAvatarWithFrame(me.photo || myPhoto, me.display_name || myName, 'w-14 h-14 text-lg', r.photo, r.ring_css)}</div>
                <div><div class="font-black text-xs">${r.name}</div><div class="text-[11px] text-amber-300 font-bold">${r.price_coins.toLocaleString()} 🪙</div></div>
              </div>
              <button type="button" onclick="callSocialApi('buy_or_equip_ring',{ring_id:${r.id}})" class="${equipped ? 'btn-success' : 'btn-primary'} px-4 py-2 rounded-xl text-xs font-black">${equipped ? 'فعال ✓' : (owned ? 'پوشیدن' : 'خرید')}</button>
            </div>
          `;
        }).join('');
      } else if (storeTab === 'links') {
        contentHtml = relLinks.map(r => {
          const owned = (me.owned_rel_links || []).includes(Number(r.id));
          const equipped = Number(me.active_marriage_link_id) === Number(r.id) || Number(me.active_bestie_link_id) === Number(r.id);
          return `
            <div class="glass-panel p-3.5 rounded-3xl flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-2xl glass-soft flex items-center justify-center text-2xl">${r.custom_emoji_id ? window.renderTgEmoji(r.custom_emoji_id, r.icon, 'w-8 h-8') : r.icon}</div>
                <div><div class="font-black text-xs">${r.name}</div><div class="text-[10px] text-amber-300">${r.price_coins.toLocaleString()} 🪙</div></div>
              </div>
              <button type="button" onclick="callSocialApi('buy_or_equip_ring',{ring_id:${r.id}})" class="${equipped ? 'btn-success' : 'btn-primary'} px-4 py-2 rounded-xl text-xs font-black">${equipped ? 'فعال ✓' : (owned ? 'انتخاب' : 'خرید')}</button>
            </div>
          `;
        }).join('');
      } else {
        contentHtml = `<div class="grid grid-cols-2 gap-2.5">` + gifts.map(g => `
          <div class="glass-panel p-3.5 rounded-3xl text-center space-y-1.5">
            <div class="text-4xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-12 h-12 mx-auto') : (g.photo ? `<img src="${g.photo}" class="w-12 h-12 object-contain mx-auto" />` : g.icon)}</div>
            <div class="font-black text-xs">${g.name}</div>
            <div class="text-xs text-amber-300 font-extrabold">${g.price_coins.toLocaleString()} 🪙</div>
          </div>
        `).join('') + `</div>`;
      }

      root.innerHTML = `
        ${renderTopBar('🛍️ فروشگاه VIP')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3">
          <div class="grid grid-cols-4 gap-1.5 text-[11px] font-black">
            <button type="button" onclick="storeTab='subs';renderSpStore(document.getElementById('app'))" class="py-2 rounded-xl ${storeTab==='subs'?'btn-primary':'glass-soft'}">💎 اشتراک</button>
            <button type="button" onclick="storeTab='rings';renderSpStore(document.getElementById('app'))" class="py-2 rounded-xl ${storeTab==='rings'?'btn-primary':'glass-soft'}">⭕ کاورها</button>
            <button type="button" onclick="storeTab='links';renderSpStore(document.getElementById('app'))" class="py-2 rounded-xl ${storeTab==='links'?'btn-primary':'glass-soft'}">🔗 خط رابط</button>
            <button type="button" onclick="storeTab='gifts';renderSpStore(document.getElementById('app'))" class="py-2 rounded-xl ${storeTab==='gifts'?'btn-primary':'glass-soft'}">🎁 گیفت‌ها</button>
          </div>
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center">${spErr}</div>` : ''}
          <div class="space-y-2.5">${contentHtml}</div>
        </div>
        ${renderBottomNav()}
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۶. کیف پول و کازینو
       ═══════════════════════════════════════════════════════════════════════════ */
    function renderSpWallet(root) {
      if (!spState) { callSocialApi('state'); return; }
      const me = spState.me;
      const packs = spState.topup_packs || [];
      root.innerHTML = `
        ${renderTopBar('🪙 کیف پول استارز و سکه')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3 text-xs">
          ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 font-bold text-center">${spMsg}</div>` : ''}
          ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 font-bold text-center">${spErr}</div>` : ''}
          <div class="glass-panel p-4 rounded-3xl grid grid-cols-2 gap-3 text-center">
            <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">استارز</div><div class="text-2xl font-black text-amber-300">⭐ ${(me.stars_balance||0).toLocaleString()}</div></div>
            <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">سکه</div><div class="text-2xl font-black text-emerald-300">🪙 ${(me.coins||0).toLocaleString()}</div></div>
          </div>
          <div class="glass-panel p-4 rounded-3xl space-y-2">
            <h3 class="font-black text-sm text-emerald-300 text-center">🔄 تبدیل استارز به سکه (هر ۱ ⭐ = ۱۰۰ 🪙)</h3>
            <div class="flex gap-2">
              <input id="conv_stars_inp" type="number" value="10" class="flex-1 p-3 rounded-xl glass-soft text-center font-black text-white" />
              <button type="button" onclick="callSocialApi('convert_stars_to_coins',{stars:Number(document.getElementById('conv_stars_inp').value||0)})" class="btn-success px-5 rounded-xl font-black">تبدیل</button>
            </div>
          </div>
          <div class="glass-panel p-4 rounded-3xl space-y-2">
            ${packs.map(pk => `
              <div class="glass-soft p-3 rounded-2xl flex items-center justify-between">
                <span class="font-black">${pk.title}</span>
                <button type="button" onclick="callSocialApi('create_topup_invoice',{pack_id:'${pk.id}'})" class="btn-primary px-3.5 py-2 rounded-xl font-black">⭐ ${pk.stars}</button>
              </div>
            `).join('')}
          </div>
        </div>
        ${renderBottomNav()}
      `;
    }

    function renderCrashGame(root) {
      const r = crashLastResult;
      root.innerHTML = `
        ${renderTopBar('🚀 CRASH')}
        <div class="flex-1 px-3 pb-24 flex flex-col justify-between gap-3">
          <div class="glass-panel p-6 rounded-3xl text-center my-auto">
            <div class="text-6xl mb-3">${r ? (r.won ? '🚀💎' : '💥🔥') : '🚀'}</div>
            <div class="text-4xl font-black ${r ? (r.won ? 'text-emerald-400' : 'text-rose-400') : 'text-amber-300'}">${r ? (r.crash_point.toFixed(2) + 'x') : '1.00x'}</div>
            <div class="text-xs font-bold text-slate-300 mt-2">${spMsg || spErr || 'ضریب هدف و مبلغ شرط را وارد کنید'}</div>
          </div>
          <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
            <div class="grid grid-cols-2 gap-2">
              <input id="cr_bet" type="number" value="200" placeholder="سکه شرط" class="p-3 rounded-xl glass-soft text-center font-black text-amber-300" />
              <input id="cr_mult" type="number" step="0.1" value="2.0" placeholder="ضریب هدف" class="p-3 rounded-xl glass-soft text-center font-black text-emerald-300" />
            </div>
            <button type="button" onclick="callSocialApi('casino_play',{game:'crash',bet:Number(document.getElementById('cr_bet').value||100),target_mult:Number(document.getElementById('cr_mult').value||2)})" class="btn-primary w-full py-4 rounded-2xl font-black text-base">🚀 پرتاب موشک</button>
          </div>
        </div>
        ${renderBottomNav()}
      `;
    }

    function renderBombsGame(root) {
      const b = bombsState || { active: false, revealed: [], bombs: [], mult: 1.0, bet: 200, mines_count: 5 };
      let gridHtml = '';
      for (let i = 0; i < 25; i++) {
        const isRev = (b.revealed || []).includes(i);
        const isBomb = (b.bombs || []).includes(i);
        gridHtml += `<button type="button" ${!b.active || isRev ? 'disabled' : ''} onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'pick',cell:${i}})" class="aspect-square rounded-2xl font-black text-xl ${isRev ? (isBomb ? 'btn-danger' : 'btn-success') : 'glass-soft'}">${isRev ? (isBomb ? '💣' : '🪙') : '❓'}</button>`;
      }
      root.innerHTML = `
        ${renderTopBar('💣 BOMBS')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col justify-between gap-2 text-xs">
          <div class="glass-panel px-4 py-2 rounded-2xl flex justify-between font-black">
            <span>ضریب: <b class="text-emerald-300">${b.mult || 1.0}x</b></span>
            <span>جایزه: <b class="text-amber-300">${(b.potential_win || 0).toLocaleString()} 🪙</b></span>
          </div>
          <div class="ltr-grid grid grid-cols-5 gap-2 glass-panel p-3 rounded-3xl">${gridHtml}</div>
          <div class="glass-panel p-3.5 rounded-3xl">
            ${b.active ? `<button type="button" onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'cashout'})" class="btn-success w-full py-3.5 rounded-2xl font-black">💰 برداشت جایزه</button>` : `
              <div class="flex gap-2 mb-2">
                <input id="bm_bet" type="number" value="200" class="flex-1 p-2.5 rounded-xl glass-soft text-center font-black text-amber-300" />
                <input id="bm_mines" type="number" value="5" class="w-20 p-2.5 rounded-xl glass-soft text-center font-black text-rose-300" />
              </div>
              <button type="button" onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'start',bet:Number(document.getElementById('bm_bet').value||200),mines:Number(document.getElementById('bm_mines').value||5)})" class="btn-primary w-full py-3 rounded-2xl font-black">💣 شروع بازی</button>
            `}
          </div>
        </div>
        ${renderBottomNav()}
      `;
    }

    function renderPickaxeOrSlot(root, mode) {
      const isPick = mode === 'pickaxe';
      const res = isPick ? pickaxeLastResult : slotLastResult;
      root.innerHTML = `
        ${renderTopBar(isPick ? '⛏️ HELL PICKAXE' : '🎰 ROYAL SLOT')}
        <div class="flex-1 px-3 pb-24 flex flex-col justify-between gap-3">
          <div class="glass-panel p-6 rounded-3xl text-center my-auto space-y-2">
            <div class="text-6xl">${isPick ? '⛏️💎' : (res?.reels ? res.reels.join(' ') : '🎰 7️⃣ 💎')}</div>
            <div class="text-2xl font-black text-amber-300">${res ? (res.mult + 'x') : 'آماده!'}</div>
            <div class="text-xs font-bold text-slate-200">${spMsg || spErr || ''}</div>
          </div>
          <div class="glass-panel p-4 rounded-3xl space-y-2 text-xs">
            <input id="ps_bet" type="number" value="200" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-amber-300" />
            <button type="button" onclick="callSocialApi('casino_play',{game:'${mode}',bet:Number(document.getElementById('ps_bet').value||200)})" class="btn-primary w-full py-4 rounded-2xl font-black text-base">${isPick ? '⛏️ شکستن سنگ' : '🎰 چرخش اسلات'}</button>
          </div>
        </div>
        ${renderBottomNav()}
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ۷. پنل مدیریت کل پلتفرم (با همگام‌سازی فوری کاورها، ایموجی پریمیوم گیفت/روابط و دکمه ریست کل)
       ═══════════════════════════════════════════════════════════════════════════ */
    let admState = null, admTab = 'store_mgr', admMsg = '', admErr = '', admLookedUpUser = null;

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
        if (data.state) spState = data.state; // همگام‌سازی فوری فروشگاه کاربران با پنل ادمین!
        if (data.admin_data) {
          admState = data.admin_data;
          if (admState.ui_assets) { window.uiAssetsMap = admState.ui_assets; applyDynamicCssBackgrounds(); }
        }
        drawTowerAdminApp(document.getElementById('app'));
      } catch (e) {}
    }

    window.admSwitchTab = function(t) {
      admTab = t; admMsg = ''; admErr = '';
      drawTowerAdminApp(document.getElementById('app'));
    };

    function startTowerAdminApp(root) {
      if (!isOwner) { root.innerHTML = `<div class="p-8 text-center">⛔</div>`; return; }
      if (!admState) admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
      drawTowerAdminApp(root);
      callTowerAdminApi('state');
    }

    function drawTowerAdminApp(root) {
      if (!root) return;
      const tabs = [
        { id: 'store_mgr',    lbl: '🛍️ کاور و گیفت' },
        { id: 'ui_assets',    lbl: '🖼️ عکس بازی‌ها' },
        { id: 'bot_stats',    lbl: '📊 آمار و ریست' },
        { id: 'users',        lbl: '👤 کاربران' },
        { id: 'bot_channels', lbl: '🔒 قفل کانال' },
        { id: 'bot_groups',   lbl: '👥 گروه‌ها' }
      ];
      const tabsHtml = tabs.map(t => `<button type="button" onclick="window.admSwitchTab('${t.id}')" class="py-2 px-2 rounded-xl text-[11px] font-black ${admTab===t.id?'btn-primary':'glass-soft'}">${t.lbl}</button>`).join('');

      let sectionHtml = '';
      if (admTab === 'store_mgr') {
        const items = admState.store_items || [];
        const capId = admState.last_captured_emoji_id || '';
        const capIco = admState.last_captured_emoji_icon || '🎁';
        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <h3 class="font-black text-sm text-amber-300 text-center">🛍️ افزودن کاور PNG، گیفت متحرک یا خط رابط ازدواج/رفاقت</h3>
            <div class="grid grid-cols-2 gap-2">
              <select id="st_cat" class="p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold">
                <option value="ring">⭕ کاور پروفایل (PNG توخالی)</option>
                <option value="gift">🎁 گیفت متحرک اتاق صوتی</option>
                <option value="rel_marriage">💍 خط رابط ازدواج (قابل خرید)</option>
                <option value="rel_bestie">⚡ خط رابط رفاقت (قابل خرید)</option>
              </select>
              <input id="st_name" type="text" placeholder="نام آیتم..." class="p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
            </div>

            <div class="glass-soft p-3 rounded-2xl text-center space-y-2 border border-purple-400/40">
              <label class="block text-[11px] text-amber-300 font-black">۱. آپلود فایل PNG توخالی (برای کاور پروفایل):</label>
              <input type="file" accept="image/png,image/webp,image/*" onchange="handleImageUpload(this, 'store_item_photo', 'prev_store_item_photo')" class="w-full text-[10px]" />
              <img id="prev_store_item_photo" class="hidden w-14 h-14 object-contain mx-auto mt-1" />
            </div>

            <div class="glass-soft p-3 rounded-2xl space-y-2 border border-emerald-400/40">
              <label class="block text-[11px] text-emerald-300 font-black">۲. یا ایموجی پریمیوم متحرک تلگرام (برای گیفت / خط رابط / چت):</label>
              <div class="flex gap-2">
                <input id="st_eid" type="text" value="${capId}" placeholder="آیدی ایموجی پریمیوم..." class="flex-1 p-2 rounded-xl bg-slate-900 text-white text-center ltr-grid" />
                <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'gift'});setTimeout(()=>tg?.close?.(),700)" class="btn-primary px-3 rounded-xl font-black">📩 ارسال به ربات</button>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <input id="st_icon" type="text" value="${capIco}" placeholder="ایموجی جایگزین" class="p-2.5 rounded-xl glass-soft text-white text-center" />
              <input id="st_coins" type="number" value="2000" placeholder="قیمت (سکه)" class="p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
            </div>
            <input id="st_css" type="text" placeholder="کد رنگ یا سایه CSS (اختیاری)" class="w-full p-2 rounded-xl glass-soft text-white text-center ltr-grid" />
            <button type="button" onclick="callTowerAdminApi('save_store_item',{category:document.getElementById('st_cat').value,name:document.getElementById('st_name').value,icon:document.getElementById('st_icon').value,custom_emoji_id:document.getElementById('st_eid').value,photo:window.uploadedImages['store_item_photo']||'',price_coins:Number(document.getElementById('st_coins').value||1500),ring_css:document.getElementById('st_css').value});window.uploadedImages['store_item_photo']='';" class="btn-success w-full py-3 rounded-2xl font-black">➕ ذخیره و نمایش فوری در فروشگاه</button>

            <div class="border-t border-white/10 pt-3 space-y-2">
              <div class="font-black text-amber-200 text-center">🔗 تنظیم ایموجی پیش‌فرض ازدواج / رفاقت و پک چت:</div>
              <div class="grid grid-cols-3 gap-1.5">
                <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'rel_marriage'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">💍 ایموجی ازدواج</button>
                <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'rel_bestie'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">⚡ ایموجی رفاقت</button>
                <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'chat_pack'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">💬 افزودن پک چت</button>
              </div>
            </div>
          </div>

          <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3 text-xs">
            <h4 class="font-black text-center text-indigo-300">لیست آیتم‌های فعلی فروشگاه (${items.length})</h4>
            ${items.map(it => `
              <div class="glass-soft p-2.5 rounded-2xl flex justify-between items-center gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  ${it.category === 'ring' ? window.renderAvatarWithFrame('', 'U', 'w-10 h-10 text-xs', it.photo, it.ring_css) : (it.custom_emoji_id ? window.renderTgEmoji(it.custom_emoji_id, it.icon, 'w-8 h-8') : `<span class="text-xl">${it.icon}</span>`)}
                  <span class="truncate"><b>${it.name}</b> (${it.category}) — ${it.price_coins} 🪙</span>
                </div>
                <button type="button" onclick="callTowerAdminApi('delete_store_item',{item_id:${it.id}})" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold">حذف</button>
              </div>
            `).join('')}
          </div>
        `;
      } else if (admTab === 'bot_stats') {
        const st = admState.bot_stats || {};
        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
            <div class="grid grid-cols-2 gap-2 text-center font-black">
              <div class="glass-soft p-3 rounded-2xl">کاربران: <b class="text-emerald-300">${st.users||0}</b></div>
              <div class="glass-soft p-3 rounded-2xl">روم‌ها: <b class="text-amber-300">${st.rooms||0}</b></div>
            </div>
            <button type="button" onclick="if(confirm('آیا مطمئن هستید که می‌خواهید تمام لول‌ها، سکه‌ها و روم‌ها صفر شوند؟'))callTowerAdminApi('reset_all_platform')" class="btn-danger w-full py-3.5 rounded-2xl font-black text-sm">
              ♻️ ریست لول و موجودی کل کاربران و روم‌ها
            </button>
          </div>
        `;
      } else if (admTab === 'ui_assets') {
        const keys = ['menu_bg','hokm_carpet','crash','bombs','pickaxe','slot','voice_hub','hokm','hokm2p','dooz','doz4p','connect4','rps','guess','2048','spuzzle'];
        sectionHtml = `<div class="space-y-2 text-xs">` + keys.map(k => `
          <div class="glass-panel p-3 rounded-2xl flex items-center justify-between gap-2">
            <span class="font-black">${k}</span>
            <input type="file" accept="image/*" onchange="handleImageUpload(this, 'asset_${k}', 'prev_a_${k}')" class="w-36 text-[10px]" />
            <button type="button" onclick="callTowerAdminApi('save_ui_asset',{asset_key:'${k}',photo:window.uploadedImages['asset_${k}']||''})" class="btn-success px-3 py-1.5 rounded-xl font-black">ذخیره</button>
          </div>
        `).join('') + `</div>`;
      } else if (admTab === 'users') {
        const u = admLookedUpUser;
        sectionHtml = `
          <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
            <div class="flex gap-2">
              <input id="au_uid" type="number" value="${u?u.user_id:''}" placeholder="آیدی عددی کاربر..." class="flex-1 p-2.5 rounded-xl glass-soft text-center text-white font-black" />
              <button type="button" onclick="callTowerAdminApi('Lookup_user',{target_uid:Number(document.getElementById('au_uid').value)})" class="btn-primary px-4 rounded-xl font-black">جستجو</button>
            </div>
            ${u ? `
              <div class="glass-soft p-3 rounded-2xl space-y-2">
                <div><b>${u.display_name}</b> | 🪙 ${u.coins} | ⭐ ${u.stars_balance} | 💎 ${u.sub_tier}</div>
                <div class="grid grid-cols-2 gap-2">
                  <input id="au_addc" type="number" placeholder="+ سکه" class="p-2 rounded-xl bg-slate-900 text-center text-white" />
                  <select id="au_tier" class="p-2 rounded-xl bg-slate-900 text-white"><option value="">بدون تغییر</option><option value="free">FREE</option><option value="pro">PRO</option><option value="plus">PLUS</option><option value="ultra">ULTRA</option></select>
                </div>
                <button type="button" onclick="callTowerAdminApi('charge_user',{target_uid:${u.user_id},add_coins:Number(document.getElementById('au_addc').value||0),set_tier:document.getElementById('au_tier').value})" class="btn-success w-full py-2.5 rounded-xl font-black">اعمال</button>
              </div>
            ` : ''}
          </div>
        `;
      } else {
        sectionHtml = `<div class="glass-panel p-4 rounded-3xl text-center text-xs">از تب‌های بالا بخش مورد نظر را انتخاب کنید.</div>`;
      }

      root.innerHTML = `
        ${renderTopBar('👑 فرماندهی کل پلتفرم')}
        <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col">
          <div class="grid grid-cols-3 gap-1.5 mb-3 shrink-0">${tabsHtml}</div>
          ${admMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-extrabold text-center mb-2">${admMsg}</div>` : ''}
          ${admErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-extrabold text-center mb-2">${admErr}</div>` : ''}
          ${sectionHtml}
        </div>
        ${renderBottomNav()}
      `;
    }

    function render() {
      const root = document.getElementById('app');
      if (!root) return;
      if (currentGame === 'voice_hub') return renderVoiceHub(root);
      if (currentGame === 'voice_room_live') return startLiveVoiceRoom(root);
      if (currentGame === 'sp_profile') return renderSpProfile(root);
      if (currentGame === 'sp_store') return renderSpStore(root);
      if (currentGame === 'sp_wallet') return renderSpWallet(root);
      if (currentGame === 'sp_pm_hub') return renderSpPmHub(root);
      if (currentGame === 'sp_pm_chat') return renderSpPmChat(root);
      if (currentGame === 'crash') return renderCrashGame(root);
      if (currentGame === 'bombs') return renderBombsGame(root);
      if (currentGame === 'pickaxe') return renderPickaxeOrSlot(root, 'pickaxe');
      if (currentGame === 'slot') return renderPickaxeOrSlot(root, 'slot');
      if (currentGame === 'tower_admin') return startTowerAdminApp(root);
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
    carpet_bg = os.environ.get("RHINO_CARPET_BG", "")

    html_content = (
        MINIAPP_TEMPLATE
        .replace("__OG_TITLE__", meta["title"])
        .replace("__OG_IMAGE__", og_img)
        .replace("__HERO_IMAGE__", hero_img)
        .replace("__CARPET_BG__", f"url('{carpet_bg}')," if carpet_bg else "")
        .replace("__BOT_USERNAME__", get_bot_username())
        .replace("__SHORT_NAME__", short_name)
    )
    return HTMLResponse(content=html_content, status_code=200)
