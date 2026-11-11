# -*- coding: utf-8 -*-
"""webapp/backend/main.py — مینی‌اپ تمام‌صفحه + میز حکم واقعی روی فرش قرمز ایرانی با چیدمان ۴ طرفه و ۷ کارت برعکس"""

import io
import json
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

from database import db
from webapp.backend.game_logic.hokm import HokmGame

app = FastAPI(title="Rhino Games Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FONT_PATH = BASE_DIR / "Vazirmatn-SemiBold.ttf"
CUSTOM_HERO_FILE = BASE_DIR / "rhino_banner.png"

hokm_rooms: dict[str, HokmGame] = {}

GAME_META = {
    "hub":          {"title": "RHINO™ COMMUNITY",   "c1": (15, 23, 42),  "c2": (79, 70, 229)},
    "dungeon":      {"title": "DUNGEON HEIST",      "c1": (49, 10, 49),  "c2": (225, 29, 72)},
    "cybervault":   {"title": "CYBER VAULT",        "c1": (6, 48, 75),   "c2": (6, 182, 212)},
    "demontower":   {"title": "DEMON TOWER",        "c1": (69, 10, 10),  "c2": (249, 115, 22)},
    "hokm":         {"title": "HOKM 4 PLAYERS",     "c1": (127, 17, 22), "c2": (185, 28, 28)},
    "hokm2p":       {"title": "HOKM 2 PLAYERS",     "c1": (127, 17, 22), "c2": (185, 28, 28)},
    "2048":         {"title": "PUZZLE 2048",        "c1": (15, 23, 42),  "c2": (37, 99, 235)},
    "spuzzle":      {"title": "SLIDING PUZZLE",     "c1": (15, 23, 42),  "c2": (14, 165, 233)},
    "samegame":     {"title": "SAME GAME",          "c1": (15, 23, 42),  "c2": (168, 85, 247)},
    "dooz":         {"title": "TIC-TAC-TOE 2P",     "c1": (15, 23, 42),  "c2": (59, 130, 246)},
    "doz4p":        {"title": "TIC-TAC-TOE 4P",     "c1": (15, 23, 42),  "c2": (236, 72, 153)},
    "connect4":     {"title": "CONNECT FOUR",       "c1": (6, 78, 59),   "c2": (16, 185, 129)},
    "rps":          {"title": "ROCK PAPER SCISSORS","c1": (15, 23, 42),  "c2": (99, 102, 241)},
    "memory":       {"title": "MEMORY MATCH",       "c1": (15, 23, 42),  "c2": (139, 92, 246)},
    "typing":       {"title": "TYPING SPEED",       "c1": (15, 23, 42),  "c2": (245, 158, 11)},
    "hangman":      {"title": "WORD GUESS",         "c1": (15, 23, 42),  "c2": (225, 29, 72)},
    "guess":        {"title": "GUESS NUMBER",       "c1": (15, 23, 42),  "c2": (16, 185, 129)},
    "gardone_anim": {"title": "LUCKY WHEEL",        "c1": (76, 29, 149), "c2": (217, 70, 239)},
}


def generate_game_banner(game_key: str) -> bytes:
    meta = GAME_META.get(game_key, GAME_META["hub"])
    w, h = 800, 420
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

    draw.rounded_rectangle([36, 36, w - 36, h - 36], radius=32, fill=(11, 17, 32), outline=(255, 255, 255), width=3)
    draw.rounded_rectangle([54, 54, w - 54, 138], radius=22, fill=meta["c2"])

    try:
        font_big = ImageFont.truetype(str(FONT_PATH), 44)
        font_med = ImageFont.truetype(str(FONT_PATH), 28)
        font_sm = ImageFont.truetype(str(FONT_PATH), 22)
    except Exception:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    draw.text((w // 2, 96), meta["title"], fill=(255, 255, 255), font=font_big, anchor="mm")
    draw.text((w // 2, 215), "RHINO™ GAMING ARENA", fill=(165, 180, 252), font=font_med, anchor="mm")
    draw.rounded_rectangle([230, 285, w - 230, 350], radius=18, fill=(16, 185, 129))
    draw.text((w // 2, 317), "PLAY NOW", fill=(255, 255, 255), font=font_sm, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.get("/api/banner/{game_type}.png")
async def serve_game_banner(game_type: str):
    if game_type == "rhino_hero" and CUSTOM_HERO_FILE.exists():
        return FileResponse(str(CUSTOM_HERO_FILE))
    png_bytes = generate_game_banner(game_type)
    return Response(content=png_bytes, media_type="image/png")


class WinPayload(BaseModel):
    uid: int
    game_type: str
    best_time: float | None = None


class HokmActionPayload(BaseModel):
    session: str
    mode: str = "4p"
    uid: int
    name: str = "Player"
    action: str  # state | join | add_bots | choose_trump | play_card | step_bot
    suit: str | None = None
    card: str | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


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
        initial_players = None
        try:
            from games.lobbies import active_lobbies
            lobby = active_lobbies.get(payload.session)
            if lobby and lobby.get("players"):
                initial_players = lobby["players"]
        except Exception:
            pass
        hokm_rooms[session_key] = HokmGame(session_key, mode=payload.mode, initial_players=initial_players)

    game = hokm_rooms[session_key]
    game.join(payload.uid, payload.name)

    res = {"ok": True}
    if payload.action == "add_bots":
        game.fill_with_bots()
    elif payload.action == "choose_trump" and payload.suit:
        res = game.choose_trump(payload.uid, payload.suit)
    elif payload.action == "play_card" and payload.card:
        res = game.play_card(payload.uid, payload.card)
        if game.status == "finished":
            try:
                await db.add_win(payload.uid, "hokm")
            except Exception:
                pass
    elif payload.action in ("state", "step_bot"):
        game.step_bot_once()

    return {
        **res,
        "state": game.get_state_for_player(payload.uid),
    }


@app.get("/api/gardone/{chat_id}")
async def get_gardone_data(chat_id: int):
    from games.gardone import active_gardones
    g = active_gardones.get(chat_id)
    if not g:
        return {"ok": False, "names": ["Player 1", "Player 2", "Player 3"], "winners": ["Player 1"]}
    names = [p["name"] for p in g["participants"].values()]
    winners = [w["name"] for w in g.get("winners", [])]
    return {"ok": True, "names": names, "winners": winners, "host": g.get("host_name", "")}


MINIAPP_TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <title>__OG_TITLE__</title>
  <meta property="og:type" content="website" />
  <meta property="og:title" content="__OG_TITLE__" />
  <meta property="og:description" content="Rhino Multiplayer Mini-App Games" />
  <meta property="og:image" content="__OG_IMAGE__" />
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body {
      width: 100vw;
      height: 100dvh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #060913;
      color: #fff;
      font-family: system-ui, -apple-system, sans-serif;
      user-select: none;
    }
    #app {
      width: 100vw;
      height: 100dvh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .btn-primary {
      background: linear-gradient(135deg, #1d4ed8, #4338ca);
      border: 1px solid rgba(255,255,255,0.18);
    }
    .btn-success {
      background: linear-gradient(135deg, #047857, #059669);
      border: 1px solid rgba(255,255,255,0.18);
    }
    .btn-danger {
      background: linear-gradient(135deg, #be123c, #dc2626);
      border: 1px solid rgba(255,255,255,0.18);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid rgba(255, 255, 255, 0.14);
    }
    .game-grid-container {
      direction: ltr !important;
    }

    /* ─── بافت فرش دستباف لاکی (قرمز) ایرانی برای بازی حکم ─── */
    .persian-carpet {
      position: relative;
      width: 100%;
      height: 100%;
      background-color: #7a1216;
      background-image:
        radial-gradient(ellipse at center, rgba(185, 28, 28, 0.55) 0%, rgba(105, 12, 16, 0.92) 65%, #3b0709 100%),
        repeating-linear-gradient(45deg, rgba(217, 119, 6, 0.06) 0px, rgba(217, 119, 6, 0.06) 2px, transparent 2px, transparent 6px),
        repeating-linear-gradient(-45deg, rgba(15, 23, 42, 0.08) 0px, rgba(15, 23, 42, 0.08) 2px, transparent 2px, transparent 6px);
      border: 10px solid #1e1b4b;
      box-shadow:
        inset 0 0 0 3px #d97706,
        inset 0 0 0 9px #450a0a,
        inset 0 0 0 11px #fbbf24,
        inset 0 0 50px rgba(0,0,0,0.85);
    }
    /* ترنج مرکزی فرش ایرانی */
    .carpet-medallion {
      position: absolute;
      top: 44%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 210px;
      height: 210px;
      border-radius: 50%;
      border: 3px solid rgba(251, 191, 36, 0.45);
      background: radial-gradient(circle, rgba(30, 58, 138, 0.35) 0%, rgba(127, 29, 29, 0.4) 60%, transparent 72%);
      box-shadow: inset 0 0 0 6px rgba(217, 119, 6, 0.2), 0 0 25px rgba(0,0,0,0.45);
      pointer-events: none;
    }
    /* کارت واقعی بازی ورق */
    .playing-card {
      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
      border: 1.5px solid #94a3b8;
      border-radius: 9px;
      box-shadow: -2px 4px 10px rgba(0, 0, 0, 0.65);
      color: #0f172a;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 4px 5px;
      font-family: Georgia, serif;
    }
    .playing-card.red {
      color: #dc2626;
    }
    /* پشت کارت سنتی (برای دست‌های گرفته‌شده تا ۷ و کارت‌های حریف) */
    .card-back {
      background-color: #1e3a8a;
      background-image:
        radial-gradient(circle, #f59e0b 15%, transparent 16%),
        repeating-linear-gradient(45deg, rgba(255,255,255,0.12) 0, rgba(255,255,255,0.12) 2px, transparent 2px, transparent 5px);
      background-size: 10px 10px;
      border: 1.5px solid #fde68a;
      border-radius: 5px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.7);
    }
  </style>
</head>
<body>
  <div id="app"></div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      try { tg.requestFullscreen?.(); } catch (e) {}
    }

    const HERO_CUSTOM_IMG = "__HERO_IMAGE__";
    const params = new URLSearchParams(window.location.search);
    const startParam = tg?.initDataUnsafe?.start_param || params.get('startapp') || params.get('tgWebAppStartParam') || '';
    let parsedGame = params.get('game') || '';
    let parsedChat = params.get('chat') || params.get('session') || 'room1';
    let lang = params.get('lang') || tg?.initDataUnsafe?.user?.language_code || 'fa';

    if (startParam) {
      const parts = startParam.split('__');
      if (parts[0]) parsedGame = parts[0];
      if (parts[1]) parsedChat = parts[1];
      if (parts[2] && ['fa','en','ar','tr','ru','de','zh'].includes(parts[2])) lang = parts[2];
    }
    if (!['fa','en','ar','tr','ru','de','zh'].includes(lang)) lang = 'fa';
    document.documentElement.dir = (lang === 'fa' || lang === 'ar') ? 'rtl' : 'ltr';

    const I18N = {
      fa: {
        title: "مینی‌اپ بازی‌های راینو", sub: "با اسکرول یا دکمه‌های چپ و راست بازی را انتخاب کنید", score: "امتیاز", back: "خروج به منو", reset: "شروع مجدد", up: "بالا", down: "پایین", left: "چپ", right: "راست", turn: "نوبت", win: "برنده", rock: "سنگ", paper: "کاغذ", scissors: "قیچی", wheel: "گردونه شانس راینو", wheelDone: "قرعه‌کشی تکمیل شد!", check: "بررسی",
        lockTitle: "عضویت اجباری در کانال", lockDesc: "برای ورود به بازی، ابتدا در کانال‌های زیر عضو شوید و سپس دکمه «عضو شدم» را بزنید:", joinBtn: "عضویت در", checkJoinBtn: "عضو شدم (ورود به بازی)", notJoinedAlert: "هنوز در همه کانال‌ها عضو نشده‌اید!",
        playNow: "ورود و شروع بازی", swipeHint: "کارت را ورق بزنید"
      },
      en: {
        title: "Rhino Games Arena", sub: "Swipe or use arrows to browse games", score: "Score", back: "Menu", reset: "Restart", up: "Up", down: "Down", left: "Left", right: "Right", turn: "Turn", win: "Winner", rock: "Rock", paper: "Paper", scissors: "Scissors", wheel: "Rhino Lucky Wheel", wheelDone: "Draw Completed!", check: "Submit",
        lockTitle: "Channel Join Required", lockDesc: "To play, please join our channels first and tap 'I Joined':", joinBtn: "Join", checkJoinBtn: "I Joined (Start Game)", notJoinedAlert: "You haven't joined all channels yet!",
        playNow: "LAUNCH GAME", swipeHint: "Swipe left or right"
      }
    };
    const L = I18N[lang] || I18N.fa;

    let playerProfile = { coins: 250, xp: 0, level: 1, streak: 1, swordLvl: 1, shieldLvl: 1, bestFloor: 1 };
    try {
      const saved = localStorage.getItem('rhino_core_profile_v2');
      if (saved) playerProfile = { ...playerProfile, ...JSON.parse(saved) };
    } catch (e) {}

    function saveProfile() {
      playerProfile.level = Math.floor(playerProfile.xp / 100) + 1;
      try { localStorage.setItem('rhino_core_profile_v2', JSON.stringify(playerProfile)); } catch (e) {}
    }

    function renderTopStatsBar() {
      return `
        <div class="glass-card px-4 py-2.5 flex justify-between items-center text-xs font-extrabold border-b border-white/10 shrink-0">
          <div class="text-amber-300">🪙 ${playerProfile.coins.toLocaleString()}</div>
          <div class="px-2.5 py-0.5 rounded-lg bg-indigo-600 text-white">LVL ${playerProfile.level} (${playerProfile.xp % 100}/100 XP)</div>
          <div class="text-emerald-400">رکورد طبقه: ${playerProfile.bestFloor}</div>
        </div>
      `;
    }

    const SLIDES = [
      {
        id: 'rhino_brand',
        badge: 'RHINO™ OFFICIAL',
        title: 'باشگاه بازی‌های راینو',
        desc: 'به آرنای رسمی تیم راینو خوش آمدید. برای جابه‌جایی بین بازی‌ها از دکمه‌های چپ و راست استفاده کنید یا صفحه را ورق بزنید.',
        theme: 'from-indigo-950 via-slate-900 to-slate-950',
        btnClass: 'btn-success',
        btnText: 'شروع سریع حکم ۴ نفره روی فرش ایرانی',
        targetGame: 'hokm',
        isHero: true
      },
      {
        id: 'hokm',
        badge: 'فرش دستباف لاکی • ۴ نفره',
        title: 'حکم ۴ نفره اصیل ایرانی',
        desc: 'یار روبه‌روی شما و حریفان در چپ و راست؛ پخش ۱۳ کارت کامل در پایین صفحه، پرتاب واقعی کارت روی ترنج فرش و چیدن ۷ دست کارت برعکس.',
        theme: 'from-red-950 via-rose-950 to-slate-950',
        btnClass: 'btn-success',
        visual: '♠️ ♥️ ♦️ ♣️'
      },
      {
        id: 'hokm2p',
        badge: 'فرش دستباف لاکی • ۲ نفره',
        title: 'حکم ۲ نفره نخبگان',
        desc: 'دوئل تک‌به‌تک حکم روی فرش قرمز ایرانی با شمارش ۷ دست کارت برعکس.',
        theme: 'from-red-950 via-slate-900 to-amber-950',
        btnClass: 'btn-success',
        visual: '👑 ♠️ ♥️'
      },
      {
        id: 'dungeon',
        badge: 'Core Loop • ریسک و طمع',
        title: 'شکارچی سیاه‌چال',
        desc: 'دروازه‌ها را باز کن و ضریب سکه بگیر؛ هر زمان خواستی با غنائم فرار کن یا ریسک کن و به طبقه پایین‌تر برو.',
        theme: 'from-rose-950 via-slate-900 to-purple-950',
        btnClass: 'btn-danger',
        visual: '🏰 ⚔️ 💎'
      },
      {
        id: 'cybervault',
        badge: 'Core Loop • دقت و سرعت',
        title: 'هک گاوصندوق سایبری',
        desc: 'در لحظه رسیدن نشانگر به ناحیه سبز قفل را بشکن و ضریب جایزه را بالا ببر.',
        theme: 'from-cyan-950 via-slate-900 to-blue-950',
        btnClass: 'btn-primary',
        visual: '🔐 ⚡ 💰'
      },
      {
        id: 'demontower',
        badge: 'Core Loop • نبرد کارتی',
        title: 'برج شیاطین',
        desc: 'نبرد نوبتی با اربابان تاریکی در طبقات برج و ارتقای سطح شمشیر و زره.',
        theme: 'from-amber-950 via-slate-900 to-red-950',
        btnClass: 'btn-success',
        visual: '👹 🛡️ 🔥'
      },
      {
        id: '2048',
        badge: 'پازل اعداد',
        title: 'پازل 2048 تمام‌صفحه',
        desc: 'کاشی‌های هم‌عدد را ترکیب کن و به عدد ۲۰۴۸ برس.',
        theme: 'from-blue-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '2️⃣ 0️⃣ 4️⃣ 8️⃣'
      },
      {
        id: 'connect4',
        badge: 'استراتژیک ۲ نفره',
        title: 'چهار در یک ردیف',
        desc: 'مهره‌ها را در ستون‌ها بینداز و ۴ مهره هم‌رنگ ردیف کن.',
        theme: 'from-emerald-950 via-slate-900 to-cyan-950',
        btnClass: 'btn-success',
        visual: '🔴 🟡 🔴 🟡'
      },
      {
        id: 'dooz',
        badge: 'کلاسیک',
        title: 'دوز ۲ نفره و ۴ نفره',
        desc: 'رقابت سریع دوز در حالت ۳×۳ یا ۵×۵ چهارنفره.',
        theme: 'from-indigo-950 via-slate-900 to-blue-950',
        btnClass: 'btn-primary',
        visual: '❌ ⚔️ ⭕'
      },
      {
        id: 'spuzzle',
        badge: 'پازل فکری',
        title: 'پازل کشویی ۱۵ تایی',
        desc: 'اعداد ۱ تا ۱۵ را به ترتیب در جدول مرتب کن.',
        theme: 'from-sky-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '1️⃣ 2️⃣ 3️⃣ 🧩'
      },
      {
        id: 'samegame',
        badge: 'پازل رنگی',
        title: 'بازی جفت‌ها',
        desc: 'بلوک‌های همرنگ متصل را حذف کن و امتیاز بگیر.',
        theme: 'from-purple-950 via-slate-900 to-fuchsia-950',
        btnClass: 'btn-primary',
        visual: '🟥 🟦 🟩 🟨'
      },
      {
        id: 'memory',
        badge: 'تمرکز و حافظه',
        title: 'کارت‌های حافظه',
        desc: 'کارت‌ها را برگردان و جفت‌های یکسان را پیدا کن.',
        theme: 'from-violet-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '🃏 🧠 ✨'
      },
      {
        id: 'rps',
        badge: 'دوئل سریع',
        title: 'سنگ، کاغذ، قیچی',
        desc: 'رقابت سه امتیازی سنگ کاغذ قیچی.',
        theme: 'from-blue-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🪨 📄 ✂️'
      },
      {
        id: 'typing',
        badge: 'سرعت عمل',
        title: 'مسابقه تایپ سرعتی',
        desc: 'جملات را با بیشترین سرعت تایپ و ثبت کن.',
        theme: 'from-amber-950 via-slate-900 to-slate-950',
        btnClass: 'btn-success',
        visual: '⌨️ ⚡ 🏆'
      },
      {
        id: 'hangman',
        badge: 'حدس حروف',
        title: 'حدس کلمه فارسی',
        desc: 'حروف کلمه مخفی را پیش از اتمام جان‌ها پیدا کن.',
        theme: 'from-rose-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🔤 🕵️ 💡'
      },
      {
        id: 'guess',
        badge: 'ضریب هوشی',
        title: 'حدس عدد ۱ تا ۱۰۰',
        desc: 'عدد مخفی را با راهنمایی‌های بالاتر و پایین‌تر پیدا کن.',
        theme: 'from-teal-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🎯 1️⃣0️⃣0️⃣'
      }
    ];

    let currentGame = parsedGame || 'hub';
    let slideIndex = 0;
    const realTgUid = tg?.initDataUnsafe?.user?.id || Number(params.get('uid')) || 0;
    const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
    const myName = tg?.initDataUnsafe?.user?.first_name || 'شما';
    let hokmPollTimer = null;
    let vaultTimer = null;
    let isJoinVerified = false;

    window.openChannelLink = function(url) {
      if (tg && tg.openTelegramLink && url.startsWith('https://t.me/')) {
        tg.openTelegramLink(url);
      } else {
        window.open(url, '_blank');
      }
    };

    window.verifyJoinAndRender = async function(showAlertOnFail = false) {
      const root = document.getElementById('app');
      if (!realTgUid) {
        isJoinVerified = true;
        return render();
      }
      try {
        const res = await fetch('/api/check_join/' + realTgUid);
        const data = await res.json();
        if (data && data.joined === false && data.channels && data.channels.length > 0) {
          isJoinVerified = false;
          if (showAlertOnFail && tg?.showAlert) tg.showAlert(L.notJoinedAlert);
          return renderJoinLockScreen(root, data.channels);
        }
      } catch (e) {}
      isJoinVerified = true;
      render();
    };

    function renderJoinLockScreen(root, channels) {
      const chButtons = channels.map(ch => `
        <button onclick="openChannelLink('${ch.url}')" class="btn-primary w-full py-3.5 px-4 rounded-xl font-extrabold">
          ${L.joinBtn} ${ch.title}
        </button>
      `).join('');

      root.innerHTML = `
        <div class="w-full h-full flex flex-col justify-center p-5">
          <div class="glass-card rounded-2xl p-6 text-center border border-rose-500/40">
            <h2 class="text-xl font-extrabold mb-2 text-white">${L.lockTitle}</h2>
            <p class="text-slate-300 text-sm mb-5 leading-relaxed">${L.lockDesc}</p>
            <div class="flex flex-col gap-3 mb-4">${chButtons}</div>
            <button onclick="verifyJoinAndRender(true)" class="btn-success w-full py-3.5 px-4 rounded-xl font-extrabold">
              ${L.checkJoinBtn}
            </button>
          </div>
        </div>
      `;
    }

    window.nav = function(g) {
      if (hokmPollTimer) { clearInterval(hokmPollTimer); hokmPollTimer = null; }
      if (vaultTimer) { clearInterval(vaultTimer); vaultTimer = null; }
      currentGame = g;
      if (!isJoinVerified) return verifyJoinAndRender(false);
      render();
    };

    window.changeSlide = function(delta) {
      slideIndex = (slideIndex + delta + SLIDES.length) % SLIDES.length;
      renderHub(document.getElementById('app'));
    };

    window.goToSlide = function(idx) {
      slideIndex = idx;
      renderHub(document.getElementById('app'));
    };

    async function reportWin(gameType, bestTime = null) {
      playerProfile.xp += 35;
      playerProfile.coins += 50;
      saveProfile();
      if (!uid) return;
      try {
        await fetch('/api/win', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ uid: Number(uid), game_type: gameType, best_time: bestTime })
        });
      } catch (e) {}
    }

    function render() {
      const root = document.getElementById('app');
      if (!root) return;
      if (currentGame === 'hokm' || currentGame === 'hokm4p') return startHokmEngine(root, '4p');
      if (currentGame === 'hokm2p') return startHokmEngine(root, '2p');
      if (currentGame === 'dungeon') return renderDungeon(root);
      if (currentGame === 'cybervault') return renderCyberVault(root);
      if (currentGame === 'demontower') return renderDemonTower(root);
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
      return renderHub(root);
    }

    /* ═══════════ منوی تمام‌صفحه اسلایدری ═══════════ */
    let touchStartX = 0;
    function renderHub(root) {
      const s = SLIDES[slideIndex];
      const dotsHtml = SLIDES.map((_, i) => `
        <button onclick="goToSlide(${i})" class="h-2 rounded-full ${i === slideIndex ? 'w-6 bg-amber-400' : 'w-2 bg-slate-600'}"></button>
      `).join('');

      const artworkHtml = s.isHero ? `
        <div class="relative w-full flex-1 min-h-[180px] rounded-2xl overflow-hidden mb-4 border border-indigo-400/40">
          <img src="${HERO_CUSTOM_IMG}" onerror="this.src='/api/banner/hub.png'" class="w-full h-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent flex flex-col justify-end p-4">
            <span class="px-2.5 py-0.5 rounded-full bg-indigo-600 text-[11px] font-black w-fit mb-1">RHINO™ TEAM</span>
            <h2 class="text-2xl font-black text-white">RHINO COMMUNITY</h2>
          </div>
        </div>
      ` : `
        <div class="w-full flex-1 min-h-[180px] rounded-2xl bg-gradient-to-br ${s.theme} border border-white/15 mb-4 flex flex-col items-center justify-center p-4">
          <div class="text-6xl mb-3">${s.visual}</div>
          <span class="text-xs font-extrabold px-3 py-1 rounded-full bg-black/50 text-amber-300 border border-white/10">${s.badge}</span>
        </div>
      `;

      root.innerHTML = `
        ${renderTopStatsBar()}
        <div id="carouselCard" class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center mb-2 text-xs text-slate-400 font-bold">
            <span>کارت ${slideIndex + 1} از ${SLIDES.length}</span>
            <span>${L.swipeHint}</span>
          </div>

          ${artworkHtml}

          <div class="text-center mb-4">
            <h1 class="text-2xl font-black mb-2 text-white">${s.title}</h1>
            <p class="text-slate-300 text-sm leading-relaxed">${s.desc}</p>
          </div>

          <div>
            <div class="game-grid-container flex items-center gap-2.5 mb-3">
              <button onclick="changeSlide(-1)" class="btn-primary w-14 py-4 rounded-2xl font-black text-xl">◀</button>
              <button onclick="nav('${s.targetGame || s.id}')" class="${s.btnClass} flex-1 py-4 px-4 rounded-2xl font-extrabold text-base">
                ${s.btnText || L.playNow}
              </button>
              <button onclick="changeSlide(1)" class="btn-primary w-14 py-4 rounded-2xl font-black text-xl">▶</button>
            </div>
            ${s.id === 'dooz' ? `<button onclick="nav('doz4p')" class="btn-success w-full py-2.5 rounded-xl font-bold text-xs mb-2">نسخه دوز ۴ نفره (۵×۵)</button>` : ''}
            <div class="game-grid-container flex justify-center items-center gap-1.5 mt-2 flex-wrap">${dotsHtml}</div>
          </div>
        </div>
      `;

      const cardEl = document.getElementById('carouselCard');
      if (cardEl) {
        cardEl.ontouchstart = (e) => { touchStartX = e.changedTouches[0].screenX; };
        cardEl.ontouchend = (e) => {
          const diff = e.changedTouches[0].screenX - touchStartX;
          if (Math.abs(diff) > 40) {
            if (diff > 0) changeSlide(1);
            else changeSlide(-1);
          }
        };
      }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       میز واقعی حکم روی فرش قرمز ایرانی (تمام‌صفحه، ۴ طرفه، ۷ کارت برعکس)
       ═══════════════════════════════════════════════════════════════════════════ */
    let hokmMode = '4p';
    let hokmError = '';

    async function callHokmApi(action, extra = {}) {
      try {
        const res = await fetch('/api/hokm/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            session: String(parsedChat || 'default'),
            mode: hokmMode,
            uid: Number(uid),
            name: myName,
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
        if (data.state) drawHokmTable(data.state);
      } catch (e) {}
    }

    window.hokmChooseSuit = function(s) { callHokmApi('choose_trump', { suit: s }); };
    window.hokmPlayCard = function(code) { callHokmApi('play_card', { card: code }); };
    window.hokmFillBots = function() { callHokmApi('add_bots'); };

    function startHokmEngine(root, mode) {
      hokmMode = mode;
      root.innerHTML = `<div class="persian-carpet flex items-center justify-center"><div class="bg-black/70 px-6 py-4 rounded-2xl font-bold border border-amber-400/50">در حال پهن کردن فرش و چیدن میز حکم...</div></div>`;
      callHokmApi('join');
      if (hokmPollTimer) clearInterval(hokmPollTimer);
      // هر ۹۰۰ میلی‌ثانیه یک نوبت جلو می‌رود تا حریف‌ها یکی‌یکی و طبیعی کارت بیندازند
      hokmPollTimer = setInterval(() => callHokmApi('state'), 900);
    }

    function renderSevenFaceDownCards(tricksWon) {
      /* ردیف ۷ تایی کارت‌های برعکس که با هر دست برده شدن یکی‌یکی پر می‌شوند */
      let html = '<div class="game-grid-container flex items-center gap-0.5">';
      for (let i = 0; i < 7; i++) {
        if (i < tricksWon) {
          html += `<div class="card-back w-3.5 h-5" title="دست ${i+1}"></div>`;
        } else {
          html += `<div class="w-3.5 h-5 rounded border border-amber-200/25 bg-black/25"></div>`;
        }
      }
      html += '</div>';
      return html;
    }

    function renderOpponentHiddenHand(count, vertical = false) {
      const n = Math.min(count || 0, 13);
      if (vertical) {
        let items = '';
        for (let i = 0; i < n; i++) {
          items += `<div class="card-back w-6 h-4 -mt-2.5 first:mt-0"></div>`;
        }
        return `<div class="flex flex-col items-center py-1">${items}</div>`;
      } else {
        let items = '';
        for (let i = 0; i < n; i++) {
          items += `<div class="card-back w-4 h-6 -ml-2 first:ml-0"></div>`;
        }
        return `<div class="game-grid-container flex items-center justify-center px-1">${items}</div>`;
      }
    }

    function drawHokmTable(st) {
      const root = document.getElementById('app');
      if (!root || (currentGame !== 'hokm' && currentGame !== 'hokm4p' && currentGame !== 'hokm2p')) return;

      const pList = st.players || [];

      // ۱. اگر هنوز ۴ نفر کامل نشده‌اند
      if (st.status === 'joining') {
        const pRows = pList.map((p, i) => `<div class="p-2.5 rounded-xl bg-black/50 border border-amber-500/30 font-bold">${i+1}. ${p.name}</div>`).join('');
        root.innerHTML = `
          <div class="persian-carpet flex flex-col justify-between p-5">
            <div class="carpet-medallion"></div>
            <div class="flex justify-between items-center z-10">
              <span class="px-3 py-1 rounded-lg bg-black/60 border border-amber-400/40 text-amber-300 font-extrabold text-xs">میز حکم ${st.max_players} نفره</span>
              <button onclick="nav('hub')" class="btn-danger px-3 py-1 rounded-lg text-xs font-bold">${L.back}</button>
            </div>
            <div class="z-10 bg-black/75 p-5 rounded-2xl border border-amber-400/40 text-center">
              <h2 class="text-xl font-black text-amber-300 mb-2">منتظر نشستن بازیکنان دور فرش (${pList.length}/${st.max_players})</h2>
              <div class="flex flex-col gap-2 mb-4">${pRows}</div>
              <button onclick="hokmFillBots()" class="btn-success w-full py-3.5 rounded-xl font-extrabold text-sm">
                نشاندن یار و حریف هوشمند و شروع فوری بازی
              </button>
            </div>
            <div class="z-10 text-center text-xs text-amber-200/70 font-bold">فرش دستباف حکم راینو</div>
          </div>
        `;
        return;
      }

      const topSeat = st.seats?.top || { name: 'یار خودی', cards_left: 0, is_turn: false, is_hakem: false };
      const rightSeat = st.seats?.right || null;
      const leftSeat = st.seats?.left || null;
      const bottomSeat = st.seats?.bottom || { name: myName, is_turn: false, is_hakem: false };
      const isMyTurn = Number(st.turn_id) === Number(uid) && st.status === 'playing';

      // ۲. ساخت مرکز فرش (یا انتخاب حکم، یا کارت‌های پرتاب‌شده از ۴ جهت روی ترنج فرش)
      let centerCarpetHtml = '';
      if (st.status === 'hakem_choosing') {
        if (Number(st.hakem_id) === Number(uid)) {
          centerCarpetHtml = `
            <div class="z-20 bg-black/85 p-4 rounded-2xl border-2 border-amber-400 text-center max-w-[270px]">
              <div class="text-amber-300 font-black text-sm mb-1">👑 شما حاکم هستید!</div>
              <div class="text-white text-xs mb-3">۵ کارت اول خود را در پایین ببینید و خال حکم را انتخاب کنید:</div>
              <div class="grid grid-cols-2 gap-2">
                <button onclick="hokmChooseSuit('S')" class="bg-slate-100 text-slate-900 py-2.5 rounded-xl font-black text-base border-2 border-amber-400">♠️ پیک</button>
                <button onclick="hokmChooseSuit('H')" class="bg-slate-100 text-rose-600 py-2.5 rounded-xl font-black text-base border-2 border-amber-400">♥️ دل</button>
                <button onclick="hokmChooseSuit('D')" class="bg-slate-100 text-rose-600 py-2.5 rounded-xl font-black text-base border-2 border-amber-400">♦️ خشت</button>
                <button onclick="hokmChooseSuit('C')" class="bg-slate-100 text-slate-900 py-2.5 rounded-xl font-black text-base border-2 border-amber-400">♣️ گشنیز</button>
              </div>
            </div>
          `;
        } else {
          centerCarpetHtml = `
            <div class="z-20 bg-black/80 px-4 py-3 rounded-2xl border border-amber-400/50 text-center">
              <div class="text-amber-300 font-extrabold text-sm">👑 حاکم (${st.hakem_name})</div>
              <div class="text-white text-xs mt-1">در حال نگاه کردن به ۵ کارت اول و تعیین حکم...</div>
            </div>
          `;
        }
      } else if (st.status === 'finished') {
        centerCarpetHtml = `
          <div class="z-20 bg-black/90 p-5 rounded-2xl border-2 border-amber-400 text-center">
            <div class="text-2xl font-black text-amber-300 mb-2">🏆 پایان بازی حکم 🏆</div>
            <div class="text-base font-extrabold text-emerald-400 mb-4">برنده: ${st.winner_display}</div>
            <button onclick="nav('hub')" class="btn-success px-6 py-2.5 rounded-xl font-bold text-sm">بازگشت به منو</button>
          </div>
        `;
      } else {
        // نمایش کارت‌های بازی‌شده روی ترنج فرش دقیقاً در سمت بازیکنی که کارت را انداخته است
        const posStyles = {
          top:    "top: 8px; left: 50%; transform: translateX(-50%) rotate(-4deg);",
          bottom: "bottom: 8px; left: 50%; transform: translateX(-50%) rotate(3deg);",
          right:  "right: 12px; top: 50%; transform: translateY(-50%) rotate(8deg);",
          left:   "left: 12px; top: 50%; transform: translateY(-50%) rotate(-8deg);"
        };
        const playedHtml = (st.trick || []).map(t => `
          <div style="${posStyles[t.pos] || posStyles.bottom}" class="absolute z-10 flex flex-col items-center">
            <div class="playing-card w-14 h-20 ${t.card.is_red ? 'red' : ''}">
              <div class="text-xs font-black leading-none">${t.card.rank}</div>
              <div class="text-2xl text-center leading-none">${t.card.suit_icon}</div>
              <div class="text-xs font-black leading-none self-end rotate-180">${t.card.rank}</div>
            </div>
            <span class="bg-black/80 text-amber-200 text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5 border border-amber-400/30">${t.name}</span>
          </div>
        `).join('');

        centerCarpetHtml = `
          <div class="relative w-56 h-52 flex items-center justify-center">
            ${playedHtml}
            ${(!st.trick || !st.trick.length) && st.last_trick_winner ? `
              <div class="bg-black/65 px-3 py-1 rounded-xl border border-amber-400/30 text-[11px] font-bold text-amber-200">
                ${st.last_trick_winner}
              </div>
            ` : ''}
          </div>
        `;
      }

      // ۳. رندر کامل کارت‌های دست بازیکن در پایین صفحه (کنار هم و روی هم به صورت طبیعی)
      const handCards = st.my_hand || [];
      const handHtml = handCards.map((c, idx) => `
        <button
          onclick="hokmPlayCard('${c.code}')"
          style="margin-left: ${idx === 0 ? '0px' : '-12px'}; z-index: ${idx + 1};"
          class="playing-card w-12 h-[74px] shrink-0 ${c.is_red ? 'red' : ''} ${isMyTurn ? 'hover:-translate-y-3 active:-translate-y-3 border-amber-400' : 'opacity-95'}"
        >
          <div class="text-xs font-black leading-none text-left">${c.rank}</div>
          <div class="text-xl text-center leading-none">${c.suit_icon}</div>
          <div class="text-[10px] font-black leading-none text-right">${c.rank}</div>
        </button>
      `).join('');

      root.innerHTML = `
        <div class="persian-carpet flex flex-col justify-between p-2 select-none">
          <div class="carpet-medallion"></div>

          <!-- نوار وضعیت بالای فرش: خال حکم + دست‌های ۷ تایی برعکس برای دو تیم -->
          <div class="z-20 flex justify-between items-center bg-black/75 px-2.5 py-1.5 rounded-xl border border-amber-500/40 text-[11px] font-bold">
            <div class="flex flex-col gap-0.5">
              <div class="flex items-center gap-1.5">
                <span class="text-emerald-400">ما (ست: ${st.our_sets})</span>
                ${renderSevenFaceDownCards(st.our_tricks)}
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-rose-400">حریف (ست: ${st.their_sets})</span>
                ${renderSevenFaceDownCards(st.their_tricks)}
              </div>
            </div>

            <div class="flex items-center gap-2">
              <div class="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-400/50 text-amber-200 font-black text-xs">
                حکم: <span class="text-base bg-white px-1.5 py-0.5 rounded">${st.trump_icon}</span>
              </div>
              <button onclick="nav('hub')" class="btn-danger px-2.5 py-1.5 rounded-lg text-[11px] font-extrabold">خروج</button>
            </div>
          </div>

          <!-- بازیکن روبه‌رو (در ۴ نفره: یار خودی | در ۲ نفره: حریف) -->
          <div class="z-20 flex flex-col items-center mt-0.5">
            <div class="px-3 py-0.5 rounded-full text-xs font-extrabold border ${topSeat.is_turn ? 'bg-amber-500 text-black border-white' : 'bg-black/75 text-amber-100 border-amber-400/40'}">
              ${topSeat.is_hakem ? '👑 ' : ''}${topSeat.name} ${st.mode === '4p' ? '(یار شما)' : ''}
            </div>
            <div class="mt-1">${renderOpponentHiddenHand(topSeat.cards_left, false)}</div>
          </div>

          <!-- بخش میانی فرش: حریف راست + ترنج وسط فرش + حریف چپ -->
          <div class="z-20 flex-1 flex items-center justify-between px-1 relative min-h-[190px]">
            ${rightSeat ? `
              <div class="flex flex-col items-center gap-1">
                <div class="px-2 py-0.5 rounded-lg text-[10px] font-extrabold border ${rightSeat.is_turn ? 'bg-amber-500 text-black border-white' : 'bg-black/75 text-rose-200 border-rose-400/40'}">
                  ${rightSeat.is_hakem ? '👑 ' : ''}${rightSeat.name}
                </div>
                ${renderOpponentHiddenHand(rightSeat.cards_left, true)}
              </div>
            ` : '<div></div>'}

            <!-- ترنج وسط فرش که کارت‌ها روی آن انداخته می‌شوند -->
            <div class="flex-1 flex items-center justify-center">
              ${centerCarpetHtml}
            </div>

            ${leftSeat ? `
              <div class="flex flex-col items-center gap-1">
                <div class="px-2 py-0.5 rounded-lg text-[10px] font-extrabold border ${leftSeat.is_turn ? 'bg-amber-500 text-black border-white' : 'bg-black/75 text-rose-200 border-rose-400/40'}">
                  ${leftSeat.is_hakem ? '👑 ' : ''}${leftSeat.name}
                </div>
                ${renderOpponentHiddenHand(leftSeat.cards_left, true)}
              </div>
            ` : '<div></div>'}
          </div>

          <!-- پایین فرش: نام بازیکن و ردیف کامل ۱۳ کارت در دست -->
          <div class="z-20 flex flex-col items-center pb-1">
            ${hokmError ? `<div class="bg-rose-700 text-white text-xs font-bold px-3 py-1 rounded-lg mb-1">${hokmError}</div>` : ''}
            <div class="flex items-center gap-2 mb-1.5">
              <span class="px-3 py-0.5 rounded-full text-xs font-extrabold border ${isMyTurn ? 'bg-emerald-500 text-black border-white' : 'bg-black/80 text-white border-amber-400/40'}">
                ${bottomSeat.is_hakem ? '👑 ' : ''}${bottomSeat.name} — ${isMyTurn ? 'نوبت شماست (کارت بزنید)' : 'نوبت: ' + st.turn_name}
              </span>
            </div>

            <!-- دست کامل کارت‌ها در پایین صفحه -->
            <div class="game-grid-container w-full overflow-x-auto flex justify-center items-end py-2 px-2">
              ${handHtml}
            </div>
          </div>
        </div>
      `;
    }

    /* ═══════════ بازی‌های Core Loop و کلاسیک (تمام‌صفحه بدون انیمیشن اضافی) ═══════════ */
    let dgFloor = 1, dgPot = 0, dgAlive = true, dgMsg = 'یکی از ۳ دروازه را انتخاب کن!';
    function initDungeon() { dgFloor = 1; dgPot = 0; dgAlive = true; dgMsg = 'دروازه را باز کن: گنج بگیر یا با غنائم فرار کن!'; }

    window.pickDungeonDoor = function(doorIdx) {
      if (!dgAlive) return;
      const outcomes = ['gem', 'coin', 'trap'].sort(() => Math.random() - 0.5);
      const picked = outcomes[doorIdx];
      if (picked === 'trap') {
        const saveChance = Math.min(0.45, (playerProfile.shieldLvl - 1) * 0.08);
        if (Math.random() < saveChance) {
          const bonus = 15 * dgFloor;
          dgPot += bonus;
          dgMsg = `🛡️ سپر تو تله را دفع کرد! +${bonus} سکه`;
          dgFloor++;
        } else {
          dgAlive = false; dgPot = 0;
          dgMsg = '💀 به تله خوردی و غنائم این دور سوخت!';
        }
      } else {
        const gain = (picked === 'gem' ? 35 : 20) * dgFloor;
        dgPot += gain;
        dgMsg = `🪙 +${gain} سکه به صندوق موقت اضافه شد!`;
        dgFloor++;
      }
      if (dgFloor > playerProfile.bestFloor) playerProfile.bestFloor = dgFloor;
      saveProfile();
      renderDungeon(document.getElementById('app'));
    };

    window.cashOutDungeon = function() {
      if (dgPot <= 0) return;
      playerProfile.coins += dgPot;
      playerProfile.xp += Math.floor(dgPot / 4);
      saveProfile();
      reportWin('dungeon');
      const savedAmount = dgPot;
      initDungeon();
      dgMsg = `🎉 ${savedAmount} سکه در گاوصندوق ذخیره شد!`;
      renderDungeon(document.getElementById('app'));
    };

    function renderDungeon(root) {
      const doorsHtml = [0, 1, 2].map(i => `
        <button onclick="pickDungeonDoor(${i})" ${!dgAlive ? 'disabled' : ''} class="h-36 rounded-2xl ${dgAlive ? 'btn-primary' : 'bg-slate-800 opacity-50'} flex flex-col items-center justify-center p-3 border border-indigo-400/40">
          <span class="text-4xl mb-2">🚪</span>
          <span class="font-extrabold text-xs">دروازه ${i + 1}</span>
        </button>
      `).join('');

      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="glass-card p-4 rounded-2xl text-center">
            <div class="flex justify-between items-center mb-2 text-xs font-extrabold">
              <span class="text-rose-400">طبقه: ${dgFloor}</span>
              <span class="text-amber-300">غنائم دور: ${dgPot} 🪙</span>
            </div>
            <p class="p-2.5 rounded-xl bg-slate-900 font-bold text-xs text-emerald-300">${dgMsg}</p>
          </div>
          <div class="grid grid-cols-3 gap-3 my-4">${doorsHtml}</div>
          <div class="flex flex-col gap-2">
            ${dgAlive && dgPot > 0 ? `<button onclick="cashOutDungeon()" class="btn-success w-full py-3.5 rounded-xl font-black">ذخیره ${dgPot} سکه و فرار</button>` : ''}
            ${!dgAlive ? `<button onclick="initDungeon();render()" class="btn-danger w-full py-3.5 rounded-xl font-black">شروع دوباره</button>` : ''}
            <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
          </div>
        </div>
      `;
    }

    let vaultPos = 0, vaultDir = 1, vaultTarget = 50, vaultStreak = 0, vaultMsg = 'وقتی نشانگر روی منطقه سبز است ضربه بزن!';
    function startVaultLoop() {
      if (vaultTimer) clearInterval(vaultTimer);
      const speed = Math.max(12, 28 - vaultStreak * 2);
      vaultTimer = setInterval(() => {
        vaultPos += vaultDir * 3;
        if (vaultPos >= 96) { vaultPos = 96; vaultDir = -1; }
        if (vaultPos <= 4) { vaultPos = 4; vaultDir = 1; }
        const cursor = document.getElementById('vaultCursor');
        if (cursor) cursor.style.left = vaultPos + '%';
      }, speed);
    }
    window.hackVaultTap = function() {
      if (Math.abs(vaultPos - vaultTarget) <= 14) {
        vaultStreak++;
        const reward = vaultStreak * 25;
        playerProfile.coins += reward; playerProfile.xp += 15; saveProfile();
        vaultTarget = Math.floor(Math.random() * 65) + 18;
        vaultMsg = `⚡ قفل باز شد! استریک ${vaultStreak}x (+${reward} سکه)`;
      } else {
        vaultStreak = 0;
        vaultMsg = '🚨 خطا! استریک صفر شد.';
      }
      renderCyberVault(document.getElementById('app'));
    };
    function renderCyberVault(root) {
      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950 text-center">
          <div class="glass-card p-5 rounded-2xl">
            <h2 class="text-xl font-black text-cyan-300 mb-1">هک گاوصندوق سایبری</h2>
            <p class="text-xs text-amber-300 font-bold mb-3">استریک: ${vaultStreak}x</p>
            <div class="p-3 rounded-xl bg-slate-900 font-bold text-xs text-emerald-400">${vaultMsg}</div>
          </div>
          <div class="game-grid-container relative w-full h-16 bg-slate-900 rounded-2xl border-2 border-cyan-500/40 overflow-hidden">
            <div style="left: ${vaultTarget - 12}%; width: 24%;" class="absolute top-0 bottom-0 bg-emerald-500/40 border-x-2 border-emerald-400"></div>
            <div id="vaultCursor" style="left: ${vaultPos}%;" class="absolute top-1 bottom-1 w-3 -ml-1.5 rounded-full bg-rose-500"></div>
          </div>
          <div class="flex flex-col gap-2">
            <button onclick="hackVaultTap()" class="btn-success w-full py-4 rounded-2xl font-black text-lg">⚡ شکستن قفل</button>
            <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
          </div>
        </div>
      `;
      startVaultLoop();
    }

    let dtStage = 1, dtHp = 100, dtMaxHp = 100, dtBossHp = 80, dtBossMax = 80, dtLog = 'کارت نوبت خود را انتخاب کن!';
    function initDemonTower() { dtMaxHp = 100 + (playerProfile.level - 1) * 15; dtHp = dtMaxHp; dtBossMax = 60 + dtStage * 25; dtBossHp = dtBossMax; }
    window.playTowerCard = function(type) {
      if (dtHp <= 0) { initDemonTower(); return renderDemonTower(document.getElementById('app')); }
      const baseAtk = 18 + playerProfile.swordLvl * 6 + playerProfile.level * 3;
      const bossAtk = 12 + dtStage * 5;
      if (type === 'strike') { dtBossHp -= baseAtk; dtHp -= bossAtk; dtLog = `⚔️ ${baseAtk} ضربه زدی و ${bossAtk} آسیب دیدی!`; }
      else if (type === 'shield') { const b = Math.max(2, bossAtk - 12); dtBossHp -= Math.floor(baseAtk*0.6); dtHp -= b; dtLog = `🛡️ دفاع کردی و فقط ${b} آسیب دیدی!`; }
      else { dtBossHp -= Math.floor(baseAtk*0.8); dtHp = Math.min(dtMaxHp, dtHp + 20 - bossAtk); dtLog = `🩸 +20 درمان شدی و حمله کردی!`; }
      if (dtBossHp <= 0) {
        const reward = dtStage * 40; playerProfile.coins += reward; playerProfile.xp += 30; dtStage++; saveProfile();
        dtBossMax = 60 + dtStage * 25; dtBossHp = dtBossMax;
        dtLog = `🏆 طبقه پاکسازی شد! +${reward} سکه`;
      }
      renderDemonTower(document.getElementById('app'));
    };
    function renderDemonTower(root) {
      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950 text-center">
          <div class="flex justify-between text-xs font-extrabold glass-card p-3 rounded-xl">
            <span class="text-amber-300">طبقه برج: ${dtStage}</span>
            <span class="text-emerald-300">جان شما: ${Math.max(0, dtHp)}/${dtMaxHp}</span>
          </div>
          <div class="glass-card p-6 rounded-2xl">
            <div class="text-5xl mb-2">👹</div>
            <div class="font-black text-rose-400">نگهبان طبقه ${dtStage}</div>
            <div class="text-xs text-slate-300 mt-1">جان: ${Math.max(0, dtBossHp)} / ${dtBossMax}</div>
            <p class="mt-3 p-2 rounded-lg bg-slate-900 text-xs text-amber-300 font-bold">${dtLog}</p>
          </div>
          <div class="flex flex-col gap-2">
            <div class="grid grid-cols-3 gap-2">
              <button onclick="playTowerCard('strike')" class="btn-danger py-3.5 rounded-xl font-bold text-xs">⚔️ حمله</button>
              <button onclick="playTowerCard('shield')" class="btn-primary py-3.5 rounded-xl font-bold text-xs">🛡️ سپر</button>
              <button onclick="playTowerCard('blood')" class="btn-success py-3.5 rounded-xl font-bold text-xs">🩸 جادوی خون</button>
            </div>
            <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
          </div>
        </div>
      `;
    }

    async function renderGardoneAnim(root) {
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950 text-center">
          <div class="glass-card p-4 rounded-2xl"><h2 class="text-xl font-black text-amber-300">${L.wheel}</h2></div>
          <div class="glass-card rounded-3xl p-8 border-2 border-indigo-400"><div id="wheelSlot" class="text-3xl font-extrabold text-amber-300">...</div></div>
          <div id="wheelWinners" class="glass-card p-4 rounded-2xl flex flex-col gap-2 text-sm max-h-48 overflow-y-auto"></div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
      let allNames = (params.get('names') || '').split(',').filter(Boolean);
      let winNames = (params.get('winners') || '').split(',').filter(Boolean);
      if ((!allNames.length || !winNames.length) && parsedChat) {
        try {
          const res = await fetch('/api/gardone/' + parsedChat);
          const data = await res.json();
          if (data.names?.length) allNames = data.names;
          if (data.winners?.length) winNames = data.winners;
        } catch (e) {}
      }
      if (!allNames.length) allNames = ['Player 1', 'Player 2'];
      if (!winNames.length) winNames = [allNames[0]];
      const slot = document.getElementById('wheelSlot'), wBox = document.getElementById('wheelWinners');
      let idx = 0;
      function nextWinner() {
        if (idx >= winNames.length) { slot.innerText = L.wheelDone; return; }
        let elapsed = 0; const target = winNames[idx];
        const timer = setInterval(() => {
          slot.innerText = allNames[Math.floor(Math.random() * allNames.length)];
          elapsed += 70;
          if (elapsed >= 1600) {
            clearInterval(timer); idx++; slot.innerText = `#${idx}: ${target}`;
            const row = document.createElement('div');
            row.className = "p-2 rounded-xl bg-slate-800 font-bold text-emerald-300";
            row.innerText = `#${idx} - ${target}`;
            wBox.appendChild(row);
            setTimeout(nextWinner, 1200);
          }
        }, 70);
      }
      setTimeout(nextWinner, 400);
    }

    let b2048 = null, s2048 = 0;
    function init2048() { b2048 = Array(4).fill(0).map(() => Array(4).fill(0)); s2048 = 0; addTile2048(); addTile2048(); }
    function addTile2048() {
      const emp = [];
      for (let r=0;r<4;r++) for (let c=0;c<4;c++) if (!b2048[r][c]) emp.push([r,c]);
      if (emp.length) { const [r,c] = emp[Math.floor(Math.random()*emp.length)]; b2048[r][c] = Math.random() < 0.9 ? 2 : 4; }
    }
    window.move2048 = function(dir) {
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
    };
    function render2048(root) {
      if (!b2048) init2048();
      const cells = b2048.flat().map(v => `<div class="aspect-square rounded-xl flex items-center justify-center font-extrabold text-xl ${v ? 'btn-primary' : 'bg-slate-800 text-transparent'}">${v || 0}</div>`).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">2048</h2><span class="glass-card px-3 py-1 rounded-lg font-bold">${L.score}: ${s2048}</span></div>
          <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl">${cells}</div>
          <div class="game-grid-container grid grid-cols-3 gap-2">
            <div></div><button onclick="move2048('up')" class="btn-primary py-3 rounded-xl font-bold">${L.up}</button><div></div>
            <button onclick="move2048('left')" class="btn-primary py-3 rounded-xl font-bold">${L.left}</button>
            <button onclick="init2048();render()" class="btn-success py-3 rounded-xl font-bold">${L.reset}</button>
            <button onclick="move2048('right')" class="btn-primary py-3 rounded-xl font-bold">${L.right}</button>
            <div></div><button onclick="move2048('down')" class="btn-primary py-3 rounded-xl font-bold">${L.down}</button><div></div>
          </div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let spz = null;
    function initSpz() { spz = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0].sort(() => Math.random()-0.5); }
    window.clickSpz = function(i) {
      const emp = spz.indexOf(0);
      if (Math.abs(Math.floor(i/4)-Math.floor(emp/4))+Math.abs((i%4)-(emp%4))===1) {
        [spz[i], spz[emp]] = [spz[emp], spz[i]]; renderSpuzzle(document.getElementById('app'));
      }
    };
    function renderSpuzzle(root) {
      if (!spz) initSpz();
      const cells = spz.map((v,i) => `<button onclick="clickSpz(${i})" class="aspect-square rounded-xl font-extrabold text-xl ${v ? 'btn-primary' : 'bg-slate-900'}">${v || ''}</button>`).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">Sliding Puzzle</h2><button onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-lg font-bold text-sm">${L.reset}</button></div>
          <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl">${cells}</div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
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
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">SameGame</h2><span class="glass-card px-3 py-1 rounded-lg font-bold">${L.score}: ${sgScore}</span></div>
          <div class="game-grid-container grid grid-cols-8 gap-1.5 glass-card p-3 rounded-2xl">${cells}</div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let doozB = null, doozTurn = 0, doozWin = null, doozMode = 'dooz';
    function initDooz(m) { doozMode = m; const sz = m === 'doz4p' ? 5 : 3; doozB = Array(sz*sz).fill(''); doozTurn = 0; doozWin = null; }
    window.clickDooz = function(i) {
      if (doozB[i] || doozWin) return;
      const syms = doozMode === 'doz4p' ? ['X','O','A','B'] : ['X','O'];
      const sz = doozMode === 'doz4p' ? 5 : 3, need = doozMode === 'doz4p' ? 4 : 3, sym = syms[doozTurn];
      doozB[i] = sym;
      for (let r=0;r<sz;r++) for (let c=0;c<sz;c++) for (const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
        let ok = true;
        for (let k=0;k<need;k++) { const nr=r+dr*k, nc=c+dc*k; if (nr<0||nr>=sz||nc<0||nc>=sz||doozB[nr*sz+nc]!==sym) { ok=false; break; } }
        if (ok) doozWin = sym;
      }
      if (!doozWin) doozTurn = (doozTurn + 1) % syms.length;
      renderDooz(document.getElementById('app'), doozMode);
    };
    function renderDooz(root, mode) {
      if (!doozB || doozMode !== mode) initDooz(mode);
      const sz = mode === 'doz4p' ? 5 : 3, syms = mode === 'doz4p' ? ['X','O','A','B'] : ['X','O'];
      const cells = doozB.map((v,i)=>`<button onclick="clickDooz(${i})" class="aspect-square rounded-xl font-extrabold text-2xl ${v==='X'?'btn-primary':v==='O'?'btn-success':v?'btn-danger':'bg-slate-800'}">${v}</button>`).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">${mode==='doz4p'?'دوز ۴ نفره':'دوز ۲ نفره'}</h2><span class="glass-card px-3 py-1 rounded-lg font-bold">${doozWin ? L.win+': '+doozWin : L.turn+': '+syms[doozTurn]}</span></div>
          <div class="game-grid-container grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-2 glass-card p-3 rounded-2xl">${cells}</div>
          <div class="flex gap-2"><button onclick="initDooz('${mode}');render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button><button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button></div>
        </div>
      `;
    }

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
      const cells = c4B.map(row=>row.map((v,c)=>`<button onclick="dropC4(${c})" class="aspect-square rounded-full ${v===1?'btn-danger':v===2?'btn-success':'bg-slate-800'}"></button>`).join('')).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">Connect 4</h2><span class="glass-card px-3 py-1 rounded-lg font-bold">${c4Win ? L.win+': P'+c4Win : L.turn+': P'+c4Turn}</span></div>
          <div class="game-grid-container grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl">${cells}</div>
          <div class="flex gap-2"><button onclick="initC4();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button><button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button></div>
        </div>
      `;
    }

    let rpsU = 0, rpsB = 0, rpsMsg = '...';
    window.playRPS = function(c) {
      const b = ['rock','paper','scissors'][Math.floor(Math.random()*3)];
      if (c===b) rpsMsg = '='; else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) { rpsU++; rpsMsg = '+1'; } else { rpsB++; rpsMsg = '-1'; }
      renderRPS(document.getElementById('app'));
    };
    function renderRPS(root) {
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950 text-center">
          <div class="glass-card p-6 rounded-2xl"><h2 class="text-xl font-extrabold mb-2">${L.rock} / ${L.paper} / ${L.scissors}</h2><p class="text-2xl font-black">${rpsU} — ${rpsB}</p><div class="mt-3 p-3 rounded-xl bg-slate-900 font-bold">${rpsMsg}</div></div>
          <div class="grid grid-cols-3 gap-3"><button onclick="playRPS('rock')" class="btn-primary py-4 rounded-xl font-bold">${L.rock}</button><button onclick="playRPS('paper')" class="btn-success py-4 rounded-xl font-bold">${L.paper}</button><button onclick="playRPS('scissors')" class="btn-danger py-4 rounded-xl font-bold">${L.scissors}</button></div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let memCards = null, memFlip = [], memMatch = [];
    function initMem() { const s = ['A','B','C','D','E','F','G','H']; memCards = [...s,...s].sort(()=>Math.random()-0.5); memFlip = []; memMatch = []; }
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
      const cells = memCards.map((v,i)=>{ const open = memFlip.includes(i) || memMatch.includes(i); return `<button onclick="clickMem(${i})" class="aspect-square rounded-xl font-extrabold text-xl ${open?'btn-success':'btn-primary'}">${open?v:'?'}</button>`; }).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="flex justify-between items-center"><h2 class="text-xl font-extrabold">Memory</h2><span class="glass-card px-3 py-1 rounded-lg font-bold">${memMatch.length/2} / 8</span></div>
          <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl">${cells}</div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    const sentences = ["آب از سرچشمه گل آلود است", "به عمل کار برآید به سخندانی نیست", "نابرده رنج گنج میسر نمیشود"];
    let targetSentence = sentences[0], typeStart = 0, typeMsg = '';
    function initTyping() { targetSentence = sentences[Math.floor(Math.random()*sentences.length)]; typeStart = Date.now(); typeMsg = ''; }
    window.checkTyping = function() {
      const val = document.getElementById('typeInput').value.trim();
      if (val === targetSentence) { typeMsg = `${((Date.now() - typeStart)/1000).toFixed(1)}s!`; } else typeMsg = '!';
      renderTyping(document.getElementById('app'));
    };
    function renderTyping(root) {
      if (!typeStart) initTyping();
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="glass-card p-5 rounded-2xl"><h2 class="text-xl font-extrabold mb-3">Typing</h2><p class="p-3 rounded-xl bg-slate-900 font-bold text-emerald-400 mb-4">${targetSentence}</p><input id="typeInput" type="text" class="w-full p-3 rounded-xl bg-slate-800 text-white border border-slate-600 mb-3" />${typeMsg ? `<p class="font-bold text-amber-400 mb-2">${typeMsg}</p>` : ''}<button onclick="checkTyping()" class="btn-success w-full py-3 rounded-xl font-bold">${L.check}</button></div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
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
      const kbHtml = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی".split('').map(ch => `<button onclick="guessLetter('${ch}')" class="py-2 rounded-lg font-bold ${hmGuessed.includes(ch) ? 'bg-slate-800 text-slate-500' : 'btn-primary'}">${ch}</button>`).join('');
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950">
          <div class="glass-card p-5 rounded-2xl text-center"><div class="flex justify-between mb-2"><h2 class="font-extrabold">Hangman</h2><span>جان: ${hmLives}</span></div><div class="text-3xl font-extrabold tracking-widest my-3">${display}</div></div>
          <div class="grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl">${kbHtml}</div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let secretNum = 0, guessHint = '1 - 100';
    function initGuess() { secretNum = Math.floor(Math.random()*100)+1; guessHint = '1 - 100'; }
    window.submitGuess = function() {
      const v = Number(document.getElementById('guessInp').value);
      if (!v) return;
      if (v === secretNum) guessHint = `= ${secretNum}!`; else if (v < secretNum) guessHint = '▲ بالاتر'; else guessHint = '▼ پایین‌تر';
      renderGuess(document.getElementById('app'));
    };
    function renderGuess(root) {
      if (!secretNum) initGuess();
      root.innerHTML = `
        <div class="flex-1 flex flex-col justify-between p-4 bg-slate-950 text-center">
          <div class="glass-card p-6 rounded-2xl"><h2 class="text-xl font-extrabold mb-2">1 - 100</h2><p class="font-bold text-amber-400 text-2xl mb-4">${guessHint}</p><input id="guessInp" type="number" min="1" max="100" class="w-full p-3 rounded-xl bg-slate-800 text-white text-center text-xl font-bold mb-3" /><button onclick="submitGuess()" class="btn-success w-full py-3 rounded-xl font-bold">${L.check}</button></div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    verifyJoinAndRender(false);
  </script>
</body>
</html>
"""


@app.get("/{full_path:path}")
async def serve_entry(request: Request, full_path: str):
    game = request.query_params.get("game") or "hub"
    meta = GAME_META.get(game, GAME_META["hub"])
    base_url = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")
    og_img = f"{base_url}/api/banner/{game}.png"
    hero_img = os.environ.get("RHINO_HERO_IMAGE", f"{base_url}/api/banner/rhino_hero.png")

    html_content = (
        MINIAPP_TEMPLATE
        .replace("__OG_TITLE__", meta["title"])
        .replace("__OG_IMAGE__", og_img)
        .replace("__HERO_IMAGE__", hero_img)
    )
    return HTMLResponse(content=html_content, status_code=200)
