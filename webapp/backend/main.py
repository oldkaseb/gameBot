# -*- coding: utf-8 -*-
"""webapp/backend/main.py — مینی‌اپ اسلایدری (Carousel UI) + کارت ویژه راینو + ۳ بازی اعتیادآور Core Loop"""

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
    "hokm":         {"title": "HOKM 4 PLAYERS",     "c1": (6, 78, 59),   "c2": (5, 150, 105)},
    "hokm2p":       {"title": "HOKM 2 PLAYERS",     "c1": (6, 78, 59),   "c2": (16, 185, 129)},
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
    action: str
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>__OG_TITLE__</title>
  <meta property="og:type" content="website" />
  <meta property="og:title" content="__OG_TITLE__" />
  <meta property="og:description" content="Rhino Multiplayer Mini-App Games" />
  <meta property="og:image" content="__OG_IMAGE__" />
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {
      background: radial-gradient(circle at top, #1e1b4b 0%, #090d16 65%, #020617 100%);
      color: #fff;
      font-family: system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      margin: 0;
      user-select: none;
      overflow-x: hidden;
    }
    .btn-primary {
      background: linear-gradient(135deg, #2563eb, #4f46e5);
      box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
    }
    .btn-success {
      background: linear-gradient(135deg, #059669, #10b981);
      box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
    }
    .btn-danger {
      background: linear-gradient(135deg, #e11d48, #ef4444);
      box-shadow: 0 4px 16px rgba(225, 29, 72, 0.4);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.14);
    }
    .game-grid-container {
      direction: ltr !important;
    }
    @keyframes floatSlow {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-6px); }
    }
    .float-anim { animation: floatSlow 3s ease-in-out infinite; }
    @keyframes neonPulse {
      0%, 100% { box-shadow: 0 0 25px rgba(236, 72, 153, 0.65), 0 0 50px rgba(59, 130, 246, 0.5); }
      50% { box-shadow: 0 0 45px rgba(16, 185, 129, 0.85), 0 0 80px rgba(245, 158, 11, 0.7); }
    }
    .wheel-stage { animation: neonPulse 1.1s infinite alternate; }
  </style>
</head>
<body class="p-3 flex flex-col items-center">
  <div id="app" class="w-full max-w-md"></div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

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
        title: "مینی‌اپ بازی‌های راینو", sub: "با اسکرول یا دکمه‌های چپ و راست بازی را انتخاب کنید", score: "امتیاز", back: "بازگشت به کارت بازی‌ها", reset: "شروع مجدد", up: "بالا", down: "پایین", left: "چپ", right: "راست", turn: "نوبت", win: "برنده", rock: "سنگ", paper: "کاغذ", scissors: "قیچی", wheel: "گردونه شانس راینو", wheelDone: "قرعه‌کشی تکمیل شد!", check: "بررسی",
        lockTitle: "عضویت اجباری در کانال", lockDesc: "برای ورود به بازی، ابتدا در کانال‌های زیر عضو شوید و سپس دکمه «عضو شدم» را بزنید:", joinBtn: "عضویت در", checkJoinBtn: "عضو شدم (ورود به بازی)", notJoinedAlert: "هنوز در همه کانال‌ها عضو نشده‌اید!",
        playNow: "ورود و شروع بازی", swipeHint: "کارت‌ها را به چپ یا راست بکشید"
      },
      en: {
        title: "Rhino Games Arena", sub: "Swipe or use arrows to browse games", score: "Score", back: "Back to Cards", reset: "Restart", up: "Up", down: "Down", left: "Left", right: "Right", turn: "Turn", win: "Winner", rock: "Rock", paper: "Paper", scissors: "Scissors", wheel: "Rhino Lucky Wheel", wheelDone: "Draw Completed!", check: "Submit",
        lockTitle: "Channel Join Required", lockDesc: "To play, please join our channels first and tap 'I Joined':", joinBtn: "Join", checkJoinBtn: "I Joined (Start Game)", notJoinedAlert: "You haven't joined all channels yet!",
        playNow: "LAUNCH GAME", swipeHint: "Swipe left or right to switch cards"
      }
    };
    const L = I18N[lang] || I18N.fa;

    /* ─── سیستم ذخیره دائمی سکه، XP و لول برای بازی‌های Core Loop ─── */
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
        <div class="glass-card rounded-2xl px-3.5 py-2.5 mb-3 flex justify-between items-center text-xs font-extrabold border border-indigo-500/30">
          <div class="flex items-center gap-1.5 text-amber-300">
            <span>🪙 ${playerProfile.coins.toLocaleString()}</span>
          </div>
          <div class="px-2.5 py-1 rounded-lg bg-indigo-600/60 text-white">
            ⭐ LVL ${playerProfile.level} (${playerProfile.xp % 100}/100 XP)
          </div>
          <div class="text-emerald-400">
            🔥 طبقه: ${playerProfile.bestFloor}
          </div>
        </div>
      `;
    }

    /* ─── لیست کارت‌های اسلایدر (کارت اول: RHINO™ TEAM + تمام بازی‌ها) ─── */
    const SLIDES = [
      {
        id: 'rhino_brand',
        badge: 'RHINO™ OFFICIAL',
        title: 'آرنا و باشگاه بازی راینو',
        desc: 'به دنیای رقابت‌های آنلاین تیم راینو خوش آمدید! با جمع کردن سکه و بردن در بازی‌ها لول خود را ارتقا دهید. برای دیدن بازی‌ها ورق بزنید.',
        theme: 'from-indigo-900 via-slate-900 to-purple-950',
        btnClass: 'btn-primary',
        btnText: 'شروع ماجراجویی (شکارچی سیاه‌چال)',
        targetGame: 'dungeon',
        isHero: true
      },
      {
        id: 'dungeon',
        badge: '🔥 بازی اعتیادآور جدید (Core Loop)',
        title: 'شکارچی سیاه‌چال (طمع یا فرار)',
        desc: 'درهای سیاه‌چال را باز کن و ضریب سکه بگیر! هر چقدر پایین‌تر بروی جایزه ۲ برابر می‌شود، اما اگر به تله شیطان بخوری همه غنائم آن دور می‌سوزد!',
        theme: 'from-rose-950 via-slate-900 to-purple-950',
        btnClass: 'btn-danger',
        visual: '🏰 ⚔️ 💎'
      },
      {
        id: 'cybervault',
        badge: '⚡ بازی اعتیادآور جدید (Core Loop)',
        title: 'هک گاوصندوق سایبری',
        desc: 'در لحظه دقیق روی پالس سبز قفل لیزری ضربه بزن! هر قفل که باز شود سرعت بالاتر می‌رود و ضریب سکه‌هایت تصاعدی چند برابر می‌شود.',
        theme: 'from-cyan-950 via-slate-900 to-blue-950',
        btnClass: 'btn-primary',
        visual: '🔐 ⚡ 💰'
      },
      {
        id: 'demontower',
        badge: '👹 بازی اعتیادآور جدید (RPG)',
        title: 'برج شیاطین (نبرد بی‌پایان)',
        desc: 'با کارت‌های شمشیر، سپر و جادوی خون به جنگ شیاطین طبقات برج برو، باس‌ها را شکست بده و تجهیزات کاراکترت را ارتقا بده.',
        theme: 'from-amber-950 via-slate-900 to-red-950',
        btnClass: 'btn-success',
        visual: '👹 🛡️ 🔥'
      },
      {
        id: 'hokm',
        badge: '🃏 بازی ورق گروهی',
        title: 'حکم ۴ نفره آنلاین',
        desc: 'تعیین حاکم با آس پیک، انتخاب خال حکم، بریدن و رقابت تیمی تا ۷ امتیاز همراه با اعضای گروه یا یار هوشمند.',
        theme: 'from-emerald-950 via-slate-900 to-teal-950',
        btnClass: 'btn-success',
        visual: '♠️ ♥️ ♦️ ♣️'
      },
      {
        id: 'hokm2p',
        badge: '🃏 دوئل کارتی',
        title: 'حکم ۲ نفره نخبگان',
        desc: 'رقابت نفس‌گیر تک‌به‌تک در میز حکم دو نفره با رعایت کامل قوانین خال زمین و حکم.',
        theme: 'from-teal-950 via-slate-900 to-emerald-950',
        btnClass: 'btn-success',
        visual: '👑 ♠️ ♦️'
      },
      {
        id: '2048',
        badge: '🧩 پازل رکوردی',
        title: 'پازل اعداد ۲۰۴۸',
        desc: 'کاشی‌های هم‌عدد را ترکیب کن، امتیاز جمع کن و به کاشی طلایی ۲۰۴۸ برس.',
        theme: 'from-blue-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '2️⃣ 0️⃣ 4️⃣ 8️⃣'
      },
      {
        id: 'connect4',
        badge: '🟢 استراتژیک',
        title: 'چهار در یک ردیف',
        desc: 'مهره‌ها را در ستون‌ها بینداز و زودتر از حریف ۴ مهره افقی، عمودی یا مورب ردیف کن.',
        theme: 'from-emerald-950 via-slate-900 to-cyan-950',
        btnClass: 'btn-success',
        visual: '🔴 🟡 🔴 🟡'
      },
      {
        id: 'dooz',
        badge: '❌⭕ کلاسیک',
        title: 'دوز ۲ نفره و ۴ نفره',
        desc: 'نبرد سریع دوز روی صفحه ۳×۳ یا ۵×۵ چهارنفره.',
        theme: 'from-indigo-950 via-slate-900 to-blue-950',
        btnClass: 'btn-primary',
        visual: '❌ ⚔️ ⭕'
      },
      {
        id: 'spuzzle',
        badge: '🔢 هوش و سرعت',
        title: 'پازل کشویی ۱۵ تایی',
        desc: 'کاشی‌های ۱ تا ۱۵ را در کمترین زمان ممکن به ترتیب مرتب کن.',
        theme: 'from-sky-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '1️⃣ 2️⃣ 3️⃣ 🧩'
      },
      {
        id: 'samegame',
        badge: '🎨 پازل رنگی',
        title: 'بازی جفت‌های رنگی',
        desc: 'بلوک‌های همرنگ کنار هم را منفجر کن و بیشترین امتیاز را ثبت کن.',
        theme: 'from-purple-950 via-slate-900 to-fuchsia-950',
        btnClass: 'btn-primary',
        visual: '🟥 🟦 🟩 🟨'
      },
      {
        id: 'memory',
        badge: '🧠 تمرکز',
        title: 'مسابقه کارت‌های حافظه',
        desc: 'کارت‌های مخفی را دو به دو برگردان و جفت‌های یکسان را پیدا کن.',
        theme: 'from-violet-950 via-slate-900 to-indigo-950',
        btnClass: 'btn-primary',
        visual: '🃏 🧠 ✨'
      },
      {
        id: 'rps',
        badge: '✂️ سرعتی',
        title: 'سنگ، کاغذ، قیچی',
        desc: 'انتخاب مخفیانه و دوئل سریع سه امتیازی.',
        theme: 'from-blue-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🪨 📄 ✂️'
      },
      {
        id: 'typing',
        badge: '⌨️ مهارت تایپ',
        title: 'مسابقه تایپ سرعتی',
        desc: 'جملات را با بیشترین سرعت و دقت تایپ کن و رکورد ثانیه ثبت کن.',
        theme: 'from-amber-950 via-slate-900 to-slate-950',
        btnClass: 'btn-success',
        visual: '⌨️ ⚡ 🏆'
      },
      {
        id: 'hangman',
        badge: '🕵️ حدس کلمه',
        title: 'حدس کلمه فارسی',
        desc: 'قبل از تمام شدن جان‌ها، حروف کلمه مخفی را کشف کن.',
        theme: 'from-rose-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🔤 🕵️ 💡'
      },
      {
        id: 'guess',
        badge: '🎯 ضریب هوشی',
        title: 'حدس عدد مخفی',
        desc: 'با راهنمایی‌های بالاتر و پایین‌تر عدد بین ۱ تا ۱۰۰ را پیدا کن.',
        theme: 'from-teal-950 via-slate-900 to-slate-950',
        btnClass: 'btn-primary',
        visual: '🎯 1️⃣0️⃣0️⃣'
      }
    ];

    let currentGame = parsedGame || 'hub';
    let slideIndex = 0;
    const realTgUid = tg?.initDataUnsafe?.user?.id || Number(params.get('uid')) || 0;
    const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
    const myName = tg?.initDataUnsafe?.user?.first_name || 'بازیکن';
    let hokmPollTimer = null;
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
        <button onclick="openChannelLink('${ch.url}')" class="btn-primary w-full py-3.5 px-4 rounded-xl font-extrabold flex items-center justify-center gap-2 active:scale-95 transition">
          <span>${L.joinBtn} ${ch.title}</span>
        </button>
      `).join('');

      root.innerHTML = `
        <div class="glass-card rounded-2xl p-6 text-center mt-6 border border-rose-500/40">
          <div class="w-16 h-16 rounded-2xl btn-danger mx-auto mb-4 flex items-center justify-center text-2xl font-black">🔒</div>
          <h2 class="text-xl font-extrabold mb-2 text-white">${L.lockTitle}</h2>
          <p class="text-slate-300 text-sm mb-5 leading-relaxed">${L.lockDesc}</p>
          <div class="flex flex-col gap-3 mb-4">${chButtons}</div>
          <button onclick="verifyJoinAndRender(true)" class="btn-success w-full py-3.5 px-4 rounded-xl font-extrabold active:scale-95 transition">
            ${L.checkJoinBtn}
          </button>
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
      if (currentGame === 'hokm' || currentGame === 'hokm4p') return startHokmEngine(root, '4p');
      if (currentGame === 'hokm2p') return startHokmEngine(root, '2p');
      return renderHub(root);
    }

    /* ═══════════ منوی اصلی کاروسل / اسلایدر کارت‌ها (غیرلیستی) ═══════════ */
    let touchStartX = 0;
    function renderHub(root) {
      const s = SLIDES[slideIndex];
      const dotsHtml = SLIDES.map((_, i) => `
        <button onclick="goToSlide(${i})" class="h-2 rounded-full transition-all ${i === slideIndex ? 'w-6 bg-indigo-400' : 'w-2 bg-slate-600'}"></button>
      `).join('');

      const artworkHtml = s.isHero ? `
        <div class="relative w-full h-48 rounded-2xl overflow-hidden mb-4 border border-indigo-400/40 shadow-2xl">
          <img src="${HERO_CUSTOM_IMG}" onerror="this.src='/api/banner/hub.png'" class="w-full h-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent flex flex-col justify-end p-4">
            <span class="px-2.5 py-0.5 rounded-full bg-indigo-600 text-[11px] font-black w-fit mb-1">RHINO™ TEAM</span>
            <h2 class="text-2xl font-black text-white drop-shadow">RHINO COMMUNITY</h2>
          </div>
        </div>
      ` : `
        <div class="w-full h-44 rounded-2xl bg-gradient-to-br ${s.theme} border border-white/15 mb-4 flex flex-col items-center justify-center relative overflow-hidden shadow-inner">
          <div class="text-5xl float-anim mb-2">${s.visual}</div>
          <span class="text-xs font-extrabold px-3 py-1 rounded-full bg-black/40 text-indigo-200 border border-white/10">${s.badge}</span>
        </div>
      `;

      root.innerHTML = `
        ${renderTopStatsBar()}

        <div id="carouselCard" class="glass-card rounded-3xl p-5 text-center relative transition-all shadow-2xl border border-indigo-500/30">
          <div class="flex justify-between items-center mb-2 text-xs text-slate-400 font-bold">
            <span>کارت ${slideIndex + 1} از ${SLIDES.length}</span>
            <span>${L.swipeHint}</span>
          </div>

          ${artworkHtml}

          <h1 class="text-2xl font-black mb-2 text-white">${s.title}</h1>
          <p class="text-slate-300 text-sm leading-relaxed mb-5 min-h-[60px]">${s.desc}</p>

          <!-- دکمه‌های چپ و راست و دکمه ورود به بازی -->
          <div class="game-grid-container flex items-center gap-2.5 mb-3">
            <button onclick="changeSlide(-1)" class="btn-primary w-14 py-3.5 rounded-2xl font-black text-xl active:scale-90 transition">◀</button>
            <button onclick="nav('${s.targetGame || s.id}')" class="${s.btnClass} flex-1 py-3.5 px-4 rounded-2xl font-extrabold text-base active:scale-95 transition">
              ${s.btnText || L.playNow}
            </button>
            <button onclick="changeSlide(1)" class="btn-primary w-14 py-3.5 rounded-2xl font-black text-xl active:scale-90 transition">▶</button>
          </div>

          ${s.id === 'dooz' ? `
            <button onclick="nav('doz4p')" class="btn-success w-full py-2.5 rounded-xl font-bold text-xs mb-2">ورود به نسخه دوز ۴ نفره (۵×۵)</button>
          ` : ''}

          <!-- نقاط وضعیت اسلایدر -->
          <div class="game-grid-container flex justify-center items-center gap-1.5 mt-3 flex-wrap">
            ${dotsHtml}
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

    /* ═══════════ بازی اعتیادآور ۱: شکارچی سیاه‌چال (Dungeon Heist — Push Your Luck) ═══════════ */
    let dgFloor = 1, dgPot = 0, dgAlive = true, dgMsg = 'یکی از ۳ دروازه سیاه‌چال را انتخاب کن!', dgRevealed = null;

    function initDungeon() {
      dgFloor = 1; dgPot = 0; dgAlive = true; dgRevealed = null;
      dgMsg = 'دروازه را باز کن: گنج بگیر یا با غنائم فرار کن!';
    }

    window.pickDungeonDoor = function(doorIdx) {
      if (!dgAlive) return;
      // هر در می‌تواند گنج بزرگ، گنج معمولی یا تله شیطان باشد
      // شمشیر بالاتر شانس شکست دادن تله را افزایش می‌دهد
      const outcomes = ['gem', 'coin', 'trap'];
      for (let i = outcomes.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [outcomes[i], outcomes[j]] = [outcomes[j], outcomes[i]];
      }
      const picked = outcomes[doorIdx];
      dgRevealed = outcomes;

      if (picked === 'trap') {
        const saveChance = Math.min(0.45, (playerProfile.shieldLvl - 1) * 0.08);
        if (Math.random() < saveChance) {
          const bonus = 15 * dgFloor;
          dgPot += bonus;
          dgMsg = `🛡️ سپر تو تله شیطان را شکست! +${bonus} سکه به غنائم اضافه شد!`;
          dgFloor++;
        } else {
          dgAlive = false;
          dgPot = 0;
          dgMsg = '💀 به تله شیطان خوردی و تمام غنائم این دور سوخت! دوباره امتحان کن!';
        }
      } else if (picked === 'gem') {
        const gain = (35 + playerProfile.swordLvl * 10) * dgFloor;
        dgPot += gain;
        dgMsg = `💎 الماس خونین پیدا کردی! +${gain} سکه در کیسه موقت! طمع می‌کنی یا فرار؟`;
        dgFloor++;
      } else {
        const gain = (20 + playerProfile.swordLvl * 5) * dgFloor;
        dgPot += gain;
        dgMsg = `🪙 صندوقچه سکه! +${gain} سکه جمع شد! می‌مونی یا فرار می‌کنی؟`;
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
      dgMsg = `🎉 فرار موفق! ${savedAmount} سکه به گاوصندوق دائمی تو منتقل شد!`;
      renderDungeon(document.getElementById('app'));
    };

    window.upgradeGear = function(type) {
      const cost = type === 'sword' ? playerProfile.swordLvl * 100 : playerProfile.shieldLvl * 120;
      if (playerProfile.coins < cost) {
        dgMsg = `⚠️ سکه کافی نداری! (${cost} سکه نیاز است)`;
        return renderDungeon(document.getElementById('app'));
      }
      playerProfile.coins -= cost;
      if (type === 'sword') playerProfile.swordLvl++;
      else playerProfile.shieldLvl++;
      saveProfile();
      dgMsg = `⚡ ارتقا انجام شد! قدرت غنیمت و بقای تو بیشتر شد.`;
      renderDungeon(document.getElementById('app'));
    };

    function renderDungeon(root) {
      const doorsHtml = [0, 1, 2].map(i => `
        <button onclick="pickDungeonDoor(${i})" ${!dgAlive ? 'disabled' : ''} class="aspect-[3/4] rounded-2xl ${dgAlive ? 'btn-primary hover:-translate-y-1' : 'bg-slate-800 opacity-50'} flex flex-col items-center justify-center p-3 border-2 border-indigo-400/40 shadow-xl active:scale-95 transition">
          <span class="text-4xl mb-2">🚪</span>
          <span class="font-extrabold text-xs">دروازه ${i + 1}</span>
        </button>
      `).join('');

      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="glass-card p-5 rounded-3xl text-center mb-3 border border-rose-500/30">
          <div class="flex justify-between items-center mb-3">
            <span class="px-3 py-1 rounded-xl bg-rose-600/40 font-extrabold text-xs">طبقه فعلی: ${dgFloor}</span>
            <span class="px-3 py-1 rounded-xl bg-amber-500/30 text-amber-300 font-extrabold text-sm">غنائم در خطر: ${dgPot} 🪙</span>
          </div>
          <p class="p-3 rounded-2xl bg-slate-900/90 font-bold text-sm text-emerald-300 mb-4">${dgMsg}</p>

          <div class="grid grid-cols-3 gap-3 mb-4">${doorsHtml}</div>

          <div class="flex gap-2 mb-3">
            ${dgAlive && dgPot > 0 ? `
              <button onclick="cashOutDungeon()" class="btn-success w-full py-3.5 rounded-xl font-black text-base">
                🏃 فرار و ذخیره ${dgPot} سکه در گاوصندوق!
              </button>
            ` : ''}
            ${!dgAlive ? `
              <button onclick="initDungeon();render()" class="btn-danger w-full py-3.5 rounded-xl font-black text-base">
                🔄 ورود دوباره به سیاه‌چال
              </button>
            ` : ''}
          </div>

          <div class="grid grid-cols-2 gap-2 pt-3 border-t border-white/10 text-xs">
            <button onclick="upgradeGear('sword')" class="btn-primary py-2.5 px-2 rounded-xl font-bold">
              ⚔️ شمشیر Lvl ${playerProfile.swordLvl} (${playerProfile.swordLvl * 100}🪙)
            </button>
            <button onclick="upgradeGear('shield')" class="btn-primary py-2.5 px-2 rounded-xl font-bold">
              🛡️ سپر ضدتله Lvl ${playerProfile.shieldLvl} (${playerProfile.shieldLvl * 120}🪙)
            </button>
          </div>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    /* ═══════════ بازی اعتیادآور ۲: هک گاوصندوق سایبری (Cyber Vault — Reflex Core Loop) ═══════════ */
    let vaultPos = 0, vaultDir = 1, vaultTarget = 50, vaultStreak = 0, vaultTimer = null, vaultMsg = 'وقتی نشانگر لیزری روی منطقه سبز قرار گرفت ضربه بزن!';

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
      const diff = Math.abs(vaultPos - vaultTarget);
      if (diff <= 14) {
        vaultStreak++;
        const reward = vaultStreak * 25;
        playerProfile.coins += reward;
        playerProfile.xp += 15;
        saveProfile();
        vaultTarget = Math.floor(Math.random() * 65) + 18;
        vaultMsg = `⚡ قفل باز شد! استریک ${vaultStreak}x (+${reward} سکه)`;
        if (vaultStreak % 3 === 0) reportWin('cybervault');
      } else {
        vaultStreak = 0;
        vaultMsg = '🚨 آژیر امنیتی به صدا درآمد! استریک صفر شد، دوباره تمرکز کن!';
      }
      renderCyberVault(document.getElementById('app'));
    };

    function renderCyberVault(root) {
      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="glass-card p-5 rounded-3xl text-center mb-4 border border-cyan-500/40">
          <h2 class="text-xl font-black text-cyan-300 mb-1">هک گاوصندوق سایبری</h2>
          <p class="text-xs text-slate-300 mb-4">ضریب استریک فعلی: <span class="text-amber-300 font-black">${vaultStreak}x</span></p>
          <div class="p-3 rounded-xl bg-slate-900 font-bold text-sm text-emerald-400 mb-6">${vaultMsg}</div>

          <div class="game-grid-container relative w-full h-14 bg-slate-950 rounded-2xl border-2 border-cyan-500/40 overflow-hidden mb-6">
            <div style="left: ${vaultTarget - 12}%; width: 24%;" class="absolute top-0 bottom-0 bg-emerald-500/40 border-x-2 border-emerald-400"></div>
            <div id="vaultCursor" style="left: ${vaultPos}%;" class="absolute top-1 bottom-1 w-3 -ml-1.5 rounded-full bg-rose-500 shadow-[0_0_15px_#f43f5e]"></div>
          </div>

          <button onclick="hackVaultTap()" class="btn-success w-full py-4 rounded-2xl font-black text-lg active:scale-95 transition">
            ⚡ ضربه و شکستن قفل!
          </button>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
      startVaultLoop();
    }

    /* ═══════════ بازی اعتیادآور ۳: برج شیاطین (Demon Tower — Endless Roguelike) ═══════════ */
    let dtStage = 1, dtHp = 100, dtMaxHp = 100, dtBossHp = 80, dtBossMax = 80, dtLog = 'کارت حمله یا دفاع خود را برای این نوبت انتخاب کن!';

    function initDemonTower() {
      dtMaxHp = 100 + (playerProfile.level - 1) * 15;
      dtHp = dtMaxHp;
      dtBossMax = 60 + dtStage * 25;
      dtBossHp = dtBossMax;
    }

    window.playTowerCard = function(type) {
      if (dtHp <= 0) { initDemonTower(); return renderDemonTower(document.getElementById('app')); }
      const baseAtk = 18 + playerProfile.swordLvl * 6 + playerProfile.level * 3;
      const bossAtk = 12 + dtStage * 5;

      if (type === 'strike') {
        const dmg = baseAtk + Math.floor(Math.random() * 12);
        dtBossHp -= dmg;
        dtHp -= bossAtk;
        dtLog = `⚔️ ${dmg} ضربه زدی و شیطان ${bossAtk} آسیب وارد کرد!`;
      } else if (type === 'shield') {
        const dmg = Math.floor(baseAtk * 0.6);
        const blocked = Math.max(2, bossAtk - (10 + playerProfile.shieldLvl * 5));
        dtBossHp -= dmg;
        dtHp -= blocked;
        dtLog = `🛡️ دفاع کردی! فقط ${blocked} آسیب دیدی و ${dmg} ضربه زدی!`;
      } else if (type === 'blood') {
        const heal = 22 + playerProfile.level * 4;
        const dmg = Math.floor(baseAtk * 0.85);
        dtBossHp -= dmg;
        dtHp = Math.min(dtMaxHp, dtHp + heal - bossAtk);
        dtLog = `🩸 جادوی خون! +${heal} جان گرفتی و ${dmg} آسیب زدی!`;
      }

      if (dtBossHp <= 0) {
        const reward = dtStage * 40;
        playerProfile.coins += reward;
        playerProfile.xp += 30;
        dtStage++;
        if (dtStage > playerProfile.bestFloor) playerProfile.bestFloor = dtStage;
        saveProfile();
        reportWin('demontower');
        dtBossMax = 60 + dtStage * 25;
        dtBossHp = dtBossMax;
        dtHp = Math.min(dtMaxHp, dtHp + 30);
        dtLog = `🏆 شیطان طبقه شکسته شد! +${reward} سکه گرفتی و وارد طبقه ${dtStage} شدی!`;
      } else if (dtHp <= 0) {
        dtHp = 0;
        dtLog = `💀 در طبقه ${dtStage} سقوط کردی! دوباره برخیز!`;
      }
      renderDemonTower(document.getElementById('app'));
    };

    function renderDemonTower(root) {
      if (dtBossMax === 80 && dtStage === 1 && dtHp === 100) initDemonTower();
      root.innerHTML = `
        ${renderTopStatsBar()}
        <div class="glass-card p-5 rounded-3xl text-center mb-3 border border-amber-500/30">
          <div class="flex justify-between items-center text-xs font-extrabold mb-3">
            <span class="px-3 py-1 rounded-xl bg-amber-500/30 text-amber-300">طبقه برج: ${dtStage}</span>
            <span class="px-3 py-1 rounded-xl bg-emerald-600/40 text-emerald-300">جان شما: ${dtHp}/${dtMaxHp} ❤️</span>
          </div>

          <div class="my-4 p-4 rounded-2xl bg-gradient-to-b from-rose-950/80 to-slate-950 border border-rose-500/30">
            <div class="text-5xl mb-2 float-anim">👹</div>
            <div class="font-black text-rose-400">ارباب تاریکی — طبقه ${dtStage}</div>
            <div class="text-xs text-slate-300 mt-1">جان شیطان: ${Math.max(0, dtBossHp)} / ${dtBossMax}</div>
          </div>

          <p class="p-2.5 rounded-xl bg-slate-900 text-xs font-bold text-amber-300 mb-4">${dtLog}</p>

          ${dtHp > 0 ? `
            <div class="grid grid-cols-3 gap-2">
              <button onclick="playTowerCard('strike')" class="btn-danger py-3.5 px-2 rounded-2xl font-extrabold text-xs flex flex-col items-center gap-1">
                <span class="text-2xl">⚔️</span><span>حمله سنگین</span>
              </button>
              <button onclick="playTowerCard('shield')" class="btn-primary py-3.5 px-2 rounded-2xl font-extrabold text-xs flex flex-col items-center gap-1">
                <span class="text-2xl">🛡️</span><span>سپر و ضدحمله</span>
              </button>
              <button onclick="playTowerCard('blood')" class="btn-success py-3.5 px-2 rounded-2xl font-extrabold text-xs flex flex-col items-center gap-1">
                <span class="text-2xl">🩸</span><span>جادوی خون</span>
              </button>
            </div>
          ` : `
            <button onclick="dtStage=1;initDemonTower();render()" class="btn-success w-full py-3.5 rounded-2xl font-black">شروع دوباره نبرد</button>
          `}
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    /* ═══════════ میز کامل حکم ۲ و ۴ نفره ═══════════ */
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
      root.innerHTML = `<div class="glass-card p-6 rounded-2xl text-center">در حال اتصال به میز حکم...</div>`;
      callHokmApi('join');
      if (hokmPollTimer) clearInterval(hokmPollTimer);
      hokmPollTimer = setInterval(() => callHokmApi('state'), 1500);
    }

    function drawHokmTable(st) {
      const root = document.getElementById('app');
      if (!root || (currentGame !== 'hokm' && currentGame !== 'hokm4p' && currentGame !== 'hokm2p')) return;

      const is4p = st.mode === '4p';
      const pList = st.players || [];

      if (st.status === 'joining') {
        const pRows = pList.map((p, i) => `<div class="p-2 rounded-xl bg-slate-800/80 font-bold">${i+1}. ${p.name}</div>`).join('');
        root.innerHTML = `
          <div class="glass-card p-5 rounded-2xl text-center mb-4">
            <h2 class="text-xl font-extrabold mb-2">لابی حکم ${st.max_players} نفره</h2>
            <p class="text-sm text-slate-300 mb-3">بازیکنان حاضر (${pList.length} از ${st.max_players}):</p>
            <div class="flex flex-col gap-2 mb-4">${pRows}</div>
            <button onclick="hokmFillBots()" class="btn-success w-full py-3 rounded-xl font-bold mb-2">پر کردن صندلی‌های خالی با هوش مصنوعی و شروع فوری</button>
          </div>
          <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
        `;
        return;
      }

      let trickScoreStr = '';
      let totalScoreStr = '';
      if (is4p) {
        trickScoreStr = `دست‌ها: تیم ۱ (${st.trick_scores?.A || 0}) — تیم ۲ (${st.trick_scores?.B || 0})`;
        totalScoreStr = `امتیاز کل: تیم ۱ (${st.game_scores?.A || 0}) — تیم ۲ (${st.game_scores?.B || 0})`;
      } else {
        const p0 = pList[0] || {id: 0, name: 'P1'}, p1 = pList[1] || {id: 1, name: 'P2'};
        trickScoreStr = `دست: ${p0.name} (${st.trick_scores?.[p0.id] || 0}) — ${p1.name} (${st.trick_scores?.[p1.id] || 0})`;
        totalScoreStr = `کل: ${p0.name} (${st.game_scores?.[p0.id] || 0}) — ${p1.name} (${st.game_scores?.[p1.id] || 0})`;
      }

      let centerStageHtml = '';
      if (st.status === 'hakem_choosing') {
        if (Number(st.hakem_id) === Number(uid)) {
          centerStageHtml = `
            <div class="text-center">
              <p class="font-extrabold text-amber-300 mb-3">شما حاکم هستید! خال حکم را انتخاب کنید:</p>
              <div class="grid grid-cols-4 gap-2">
                <button onclick="hokmChooseSuit('S')" class="btn-primary py-3 rounded-xl text-xl font-bold">♠️ پیک</button>
                <button onclick="hokmChooseSuit('H')" class="btn-danger py-3 rounded-xl text-xl font-bold">♥️ دل</button>
                <button onclick="hokmChooseSuit('D')" class="btn-danger py-3 rounded-xl text-xl font-bold">♦️ خشت</button>
                <button onclick="hokmChooseSuit('C')" class="btn-primary py-3 rounded-xl text-xl font-bold">♣️ گشنیز</button>
              </div>
            </div>
          `;
        } else {
          centerStageHtml = `<div class="text-center font-bold text-amber-300">حاکم (${st.hakem_name}) در حال انتخاب خال حکم است...</div>`;
        }
      } else if (st.status === 'finished') {
        centerStageHtml = `<div class="text-center text-2xl font-black text-emerald-400">🏆 بازی تمام شد! برنده: ${st.winner_display}</div>`;
      } else {
        const tableCards = (st.trick || []).map(t => `
          <div class="flex flex-col items-center">
            <div class="w-14 h-20 bg-white rounded-xl flex flex-col items-center justify-center shadow-lg border-2 border-slate-300 ${t.card.is_red ? 'text-rose-600' : 'text-slate-900'}">
              <span class="font-extrabold text-lg leading-none">${t.card.rank}</span>
              <span class="text-xl leading-none mt-1">${t.card.suit_icon}</span>
            </div>
            <span class="text-[11px] font-bold text-slate-300 mt-1">${t.name}</span>
          </div>
        `).join('');
        centerStageHtml = tableCards.length
          ? `<div class="flex justify-center gap-3 flex-wrap">${tableCards}</div>`
          : `<div class="text-slate-400 text-sm font-bold">${st.last_trick_winner ? 'دست قبلی: ' + st.last_trick_winner : 'منتظر شروع دست...'}</div>`;
      }

      const isMyTurn = Number(st.turn_id) === Number(uid) && st.status === 'playing';
      const handHtml = (st.my_hand || []).map(c => `
        <button
          onclick="hokmPlayCard('${c.code}')"
          class="bg-white rounded-xl py-2.5 px-1 flex flex-col items-center justify-center shadow-md active:scale-95 transition border-2 ${isMyTurn ? 'border-emerald-400 hover:-translate-y-1' : 'border-slate-300 opacity-90'} ${c.is_red ? 'text-rose-600' : 'text-slate-900'}"
        >
          <span class="font-black text-base leading-none">${c.rank}</span>
          <span class="text-lg leading-none mt-1">${c.suit_icon}</span>
        </button>
      `).join('');

      root.innerHTML = `
        <div class="glass-card p-3 rounded-2xl mb-3 text-xs font-bold flex flex-col gap-1.5">
          <div class="flex justify-between items-center text-sm">
            <span class="text-amber-300">حاکم: ${st.hakem_name}</span>
            <span class="px-2.5 py-1 rounded-lg bg-indigo-600/50 text-white">حکم: ${st.trump_icon}</span>
          </div>
          <div class="flex justify-between text-emerald-300"><span>${trickScoreStr}</span></div>
          <div class="flex justify-between text-sky-300"><span>${totalScoreStr}</span></div>
          <div class="text-center py-1 rounded-lg ${isMyTurn ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300'}">
            ${isMyTurn ? 'نوبت شماست! یک کارت بازی کنید' : 'نوبت: ' + st.turn_name}
          </div>
          ${hokmError ? `<div class="text-center text-rose-400 font-bold">${hokmError}</div>` : ''}
        </div>

        <div class="glass-card p-4 rounded-2xl mb-3 min-h-[150px] flex items-center justify-center">
          ${centerStageHtml}
        </div>

        <div class="glass-card p-3 rounded-2xl mb-3">
          <div class="text-xs text-slate-300 font-bold mb-2 text-center">دست شما (${(st.my_hand || []).length} کارت):</div>
          <div class="game-grid-container grid grid-cols-7 gap-1.5">${handHtml}</div>
        </div>

        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    async function renderGardoneAnim(root) {
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <h2 class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-amber-300 to-emerald-400 mb-1">${L.wheel}</h2>
        </div>
        <div class="glass-card wheel-stage rounded-3xl p-8 text-center my-5 border-2 border-indigo-400 flex flex-col items-center justify-center min-h-[190px]">
          <div id="wheelSlot" class="text-3xl font-extrabold text-amber-300">...</div>
        </div>
        <div class="glass-card p-4 rounded-2xl mb-4">
          <div id="wheelWinners" class="flex flex-col gap-2 text-sm"></div>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
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
      if (!allNames.length) allNames = ['Player 1', 'Player 2', 'Player 3'];
      if (!winNames.length) winNames = [allNames[0]];

      const slot = document.getElementById('wheelSlot');
      const wBox = document.getElementById('wheelWinners');
      const colors = ['text-pink-400', 'text-amber-300', 'text-cyan-400', 'text-emerald-400', 'text-purple-400'];
      let idx = 0;

      function nextWinner() {
        if (idx >= winNames.length) {
          slot.className = "text-2xl font-black text-emerald-400";
          slot.innerText = L.wheelDone;
          return;
        }
        let elapsed = 0;
        const target = winNames[idx];
        const timer = setInterval(() => {
          const rnd = allNames[Math.floor(Math.random() * allNames.length)];
          const clr = colors[Math.floor(Math.random() * colors.length)];
          slot.className = `text-3xl font-extrabold ${clr} transition-all scale-105`;
          slot.innerText = rnd;
          elapsed += 65;
          if (elapsed >= 1800) {
            clearInterval(timer);
            idx++;
            slot.className = "text-3xl font-black text-emerald-400 scale-110";
            slot.innerText = `#${idx}: ${target}`;
            const row = document.createElement('div');
            row.className = "p-2.5 rounded-xl bg-slate-800/90 border border-emerald-500/40 font-bold text-white";
            row.innerText = `#${idx} - ${target}`;
            wBox.appendChild(row);
            setTimeout(nextWinner, 1400);
          }
        }, 65);
      }
      setTimeout(nextWinner, 500);
    }

    let b2048 = null, s2048 = 0;
    function init2048() {
      b2048 = Array(4).fill(0).map(() => Array(4).fill(0));
      s2048 = 0; addTile2048(); addTile2048();
    }
    function addTile2048() {
      const emp = [];
      for (let r=0;r<4;r++) for (let c=0;c<4;c++) if (!b2048[r][c]) emp.push([r,c]);
      if (emp.length) {
        const [r,c] = emp[Math.floor(Math.random()*emp.length)];
        b2048[r][c] = Math.random() < 0.9 ? 2 : 4;
      }
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
          if (arr[i]===arr[i+1]) { out.push(arr[i]*2); s2048+=arr[i]*2; i++; }
          else out.push(arr[i]);
        }
        while (out.length<4) out.push(0);
        if (out.join(',') !== row.join(',')) moved = true;
        return out;
      });
      if (dir==='up') b = rot(b);
      if (dir==='right') b = b.map(r => r.reverse());
      if (dir==='down') b = rot(rot(rot(b)));
      if (moved) {
        b2048 = b; addTile2048();
        if (b2048.some(r => r.includes(2048))) reportWin('2048');
        render2048(document.getElementById('app'));
      }
    };
    function render2048(root) {
      if (!b2048) init2048();
      const cells = b2048.flat().map(v => `
        <div class="aspect-square rounded-xl flex items-center justify-center font-extrabold text-xl ${v ? 'btn-primary' : 'bg-slate-800/70 text-transparent'}">${v || 0}</div>
      `).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">2048</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${L.score}: ${s2048}</span>
        </div>
        <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="game-grid-container grid grid-cols-3 gap-2 mb-4">
          <div></div><button onclick="move2048('up')" class="btn-primary py-3 rounded-xl font-bold">${L.up}</button><div></div>
          <button onclick="move2048('left')" class="btn-primary py-3 rounded-xl font-bold">${L.left}</button>
          <button onclick="init2048();render()" class="btn-success py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="move2048('right')" class="btn-primary py-3 rounded-xl font-bold">${L.right}</button>
          <div></div><button onclick="move2048('down')" class="btn-primary py-3 rounded-xl font-bold">${L.down}</button><div></div>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    let spz = null;
    function initSpz() { spz = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0].sort(() => Math.random()-0.5); }
    window.clickSpz = function(i) {
      const emp = spz.indexOf(0);
      const r1 = Math.floor(i/4), c1 = i%4, r2 = Math.floor(emp/4), c2 = emp%4;
      if (Math.abs(r1-r2)+Math.abs(c1-c2)===1) {
        [spz[i], spz[emp]] = [spz[emp], spz[i]];
        if (spz.slice(0,15).every((v,idx)=>v===idx+1)) reportWin('spuzzle');
        renderSpuzzle(document.getElementById('app'));
      }
    };
    function renderSpuzzle(root) {
      if (!spz) initSpz();
      const cells = spz.map((v,i) => `
        <button onclick="clickSpz(${i})" class="aspect-square rounded-xl font-extrabold text-xl ${v ? 'btn-primary' : 'bg-slate-800/40'}">${v || ''}</button>
      `).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">Sliding Puzzle</h2>
          <button onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-lg font-bold text-sm">${L.reset}</button>
        </div>
        <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    let sgGrid = null, sgScore = 0;
    const sgCls = ['btn-danger', 'btn-primary', 'btn-success', 'bg-amber-500'];
    function initSg() {
      sgGrid = Array(8).fill(0).map(()=>Array(8).fill(0).map(()=>Math.floor(Math.random()*4)));
      sgScore = 0;
    }
    window.clickSg = function(r0, c0) {
      const target = sgGrid[r0][c0], q = [[r0,c0]], vis = new Set([r0+','+c0]), grp = [[r0,c0]];
      while (q.length) {
        const [r,c] = q.pop();
        for (const [dr,dc] of [[0,1],[0,-1],[1,0],[-1,0]]) {
          const nr=r+dr, nc=c+dc, k=nr+','+nc;
          if (nr>=0 && nr<8 && nc>=0 && nc<8 && !vis.has(k) && sgGrid[nr][nc]===target) {
            vis.add(k); grp.push([nr,nc]); q.push([nr,nc]);
          }
        }
      }
      if (grp.length < 2) return;
      grp.forEach(([r,c]) => sgGrid[r][c] = Math.floor(Math.random()*4));
      sgScore += grp.length * 10;
      renderSameGame(document.getElementById('app'));
    };
    function renderSameGame(root) {
      if (!sgGrid) initSg();
      const cells = sgGrid.map((row,r)=>row.map((v,c)=>`
        <button onclick="clickSg(${r},${c})" class="aspect-square rounded-lg ${sgCls[v]}"></button>
      `).join('')).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">SameGame</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${L.score}: ${sgScore}</span>
        </div>
        <div class="game-grid-container grid grid-cols-8 gap-1.5 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initSg();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let doozB = null, doozTurn = 0, doozWin = null, doozMode = 'dooz';
    function initDooz(m) {
      doozMode = m;
      const sz = m === 'doz4p' ? 5 : 3;
      doozB = Array(sz*sz).fill('');
      doozTurn = 0; doozWin = null;
    }
    window.clickDooz = function(i) {
      if (doozB[i] || doozWin) return;
      const syms = doozMode === 'doz4p' ? ['X','O','A','B'] : ['X','O'];
      const sz = doozMode === 'doz4p' ? 5 : 3;
      const need = doozMode === 'doz4p' ? 4 : 3;
      const sym = syms[doozTurn];
      doozB[i] = sym;
      for (let r=0;r<sz;r++) for (let c=0;c<sz;c++) {
        for (const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
          let ok = true;
          for (let k=0;k<need;k++) {
            const nr=r+dr*k, nc=c+dc*k;
            if (nr<0||nr>=sz||nc<0||nc>=sz||doozB[nr*sz+nc]!==sym) { ok=false; break; }
          }
          if (ok) doozWin = sym;
        }
      }
      if (doozWin) reportWin(doozMode);
      else doozTurn = (doozTurn + 1) % syms.length;
      renderDooz(document.getElementById('app'), doozMode);
    };
    function renderDooz(root, mode) {
      if (!doozB || doozMode !== mode) initDooz(mode);
      const sz = mode === 'doz4p' ? 5 : 3;
      const syms = mode === 'doz4p' ? ['X','O','A','B'] : ['X','O'];
      const cells = doozB.map((v,i)=>`
        <button onclick="clickDooz(${i})" class="aspect-square rounded-xl font-extrabold text-2xl ${v==='X'?'btn-primary':v==='O'?'btn-success':v?'btn-danger':'bg-slate-800/80'}">${v}</button>
      `).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">${mode==='doz4p'?'Tic-Tac-Toe 4P':'Tic-Tac-Toe 2P'}</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${doozWin ? L.win+': '+doozWin : L.turn+': '+syms[doozTurn]}</span>
        </div>
        <div class="game-grid-container grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initDooz('${mode}');render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let c4B = null, c4Turn = 1, c4Win = 0;
    function initC4() { c4B = Array(6).fill(0).map(()=>Array(7).fill(0)); c4Turn = 1; c4Win = 0; }
    window.dropC4 = function(col) {
      if (c4Win) return;
      for (let r=5;r>=0;r--) {
        if (!c4B[r][col]) {
          c4B[r][col] = c4Turn;
          for (let rr=0;rr<6;rr++) for (let cc=0;cc<7;cc++) {
            for (const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
              let ok=true;
              for (let k=0;k<4;k++) {
                const nr=rr+dr*k, nc=cc+dc*k;
                if (nr<0||nr>=6||nc<0||nc>=7||c4B[nr][nc]!==c4Turn){ok=false;break;}
              }
              if (ok) c4Win = c4Turn;
            }
          }
          if (c4Win) reportWin('connect4');
          else c4Turn = c4Turn===1?2:1;
          renderConnect4(document.getElementById('app'));
          return;
        }
      }
    };
    function renderConnect4(root) {
      if (!c4B) initC4();
      const cells = c4B.map(row=>row.map((v,c)=>`
        <button onclick="dropC4(${c})" class="aspect-square rounded-full ${v===1?'btn-danger':v===2?'btn-success':'bg-slate-800'}"></button>
      `).join('')).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">Connect 4</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${c4Win ? L.win+': P'+c4Win : L.turn+': P'+c4Turn}</span>
        </div>
        <div class="game-grid-container grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initC4();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let rpsU = 0, rpsB = 0, rpsMsg = '...';
    window.playRPS = function(c) {
      const opts = ['rock','paper','scissors'];
      const b = opts[Math.floor(Math.random()*3)];
      if (c===b) rpsMsg = `=`;
      else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) {
        rpsU++; rpsMsg = `+1`;
        if (rpsU===3) reportWin('rps');
      } else {
        rpsB++; rpsMsg = `-1`;
      }
      renderRPS(document.getElementById('app'));
    };
    function renderRPS(root) {
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <h2 class="text-xl font-extrabold mb-2">${L.rock} / ${L.paper} / ${L.scissors}</h2>
          <p class="font-bold text-slate-300 mb-3">${rpsU} — ${rpsB}</p>
          <div class="p-3 rounded-xl bg-slate-900/90 font-bold">${rpsMsg}</div>
        </div>
        <div class="grid grid-cols-3 gap-3 mb-4">
          <button onclick="playRPS('rock')" class="btn-primary py-3 rounded-xl font-bold">${L.rock}</button>
          <button onclick="playRPS('paper')" class="btn-success py-3 rounded-xl font-bold">${L.paper}</button>
          <button onclick="playRPS('scissors')" class="btn-danger py-3 rounded-xl font-bold">${L.scissors}</button>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">${L.back}</button>
      `;
    }

    let memCards = null, memFlip = [], memMatch = [];
    function initMem() {
      const s = ['A','B','C','D','E','F','G','H'];
      memCards = [...s,...s].sort(()=>Math.random()-0.5);
      memFlip = []; memMatch = [];
    }
    window.clickMem = function(i) {
      if (memFlip.length===2 || memFlip.includes(i) || memMatch.includes(i)) return;
      memFlip.push(i);
      renderMemory(document.getElementById('app'));
      if (memFlip.length===2) {
        const [a,b] = memFlip;
        if (memCards[a]===memCards[b]) {
          memMatch.push(a,b); memFlip = [];
          if (memMatch.length===16) reportWin('memory');
          renderMemory(document.getElementById('app'));
        } else {
          setTimeout(()=>{ memFlip=[]; renderMemory(document.getElementById('app')); }, 650);
        }
      }
    };
    function renderMemory(root) {
      if (!memCards) initMem();
      const cells = memCards.map((v,i)=>{
        const open = memFlip.includes(i) || memMatch.includes(i);
        return `<button onclick="clickMem(${i})" class="aspect-square rounded-xl font-extrabold text-xl ${open?'btn-success':'btn-primary'}">${open?v:'?'}</button>`;
      }).join('');
      root.innerHTML = `
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-extrabold">Memory</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${memMatch.length/2} / 8</span>
        </div>
        <div class="game-grid-container grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initMem();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    const sentences = ["آب از سرچشمه گل آلود است", "به عمل کار برآید به سخندانی نیست", "نابرده رنج گنج میسر نمیشود", "سرعت نور در خلا سیصد هزار کیلومتر بر ثانیه است"];
    let targetSentence = sentences[0], typeStart = 0, typeMsg = '';
    function initTyping() {
      targetSentence = sentences[Math.floor(Math.random()*sentences.length)];
      typeStart = Date.now(); typeMsg = '';
    }
    window.checkTyping = function() {
      const val = document.getElementById('typeInput').value.trim();
      if (val === targetSentence) {
        const sec = ((Date.now() - typeStart)/1000).toFixed(1);
        typeMsg = `${sec}s!`;
        reportWin('typing', Number(sec));
        renderTyping(document.getElementById('app'));
      } else {
        typeMsg = '!';
        renderTyping(document.getElementById('app'));
      }
    };
    function renderTyping(root) {
      if (!typeStart) initTyping();
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl mb-4">
          <h2 class="text-xl font-extrabold mb-3">Typing</h2>
          <p class="p-3 rounded-xl bg-slate-900 font-bold text-emerald-400 mb-4">${targetSentence}</p>
          <input id="typeInput" type="text" class="w-full p-3 rounded-xl bg-slate-800 text-white border border-slate-600 mb-3" />
          ${typeMsg ? `<p class="font-bold text-amber-400 mb-2">${typeMsg}</p>` : ''}
          <button onclick="checkTyping()" class="btn-success w-full py-3 rounded-xl font-bold">${L.check}</button>
        </div>
        <div class="flex gap-2">
          <button onclick="initTyping();render()" class="btn-primary flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    const wordsList = ["تلگرام", "راینو", "پایتون", "امپراتور", "کهکشان", "سیمرغ", "ققنوس", "الماس"];
    let hmWord = "", hmGuessed = [], hmLives = 10;
    function initHangman() {
      hmWord = wordsList[Math.floor(Math.random()*wordsList.length)];
      hmGuessed = []; hmLives = 10;
    }
    window.guessLetter = function(ch) {
      if (hmGuessed.includes(ch) || hmLives <= 0) return;
      hmGuessed.push(ch);
      if (!hmWord.includes(ch)) hmLives--;
      if (hmWord.split('').every(c => hmGuessed.includes(c))) reportWin('hangman');
      renderHangman(document.getElementById('app'));
    };
    function renderHangman(root) {
      if (!hmWord) initHangman();
      const display = hmWord.split('').map(c => hmGuessed.includes(c) ? c : '_').join(' ');
      const letters = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی".split('');
      const kbHtml = letters.map(ch => `
        <button onclick="guessLetter('${ch}')" class="py-2 rounded-lg font-bold ${hmGuessed.includes(ch) ? 'bg-slate-800 text-slate-500' : 'btn-primary'}">${ch}</button>
      `).join('');
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-extrabold">Hangman</h2>
            <span class="px-3 py-1 rounded-lg bg-rose-600/30 font-bold">${hmLives}</span>
          </div>
          <div class="text-3xl font-extrabold tracking-widest my-4">${display}</div>
        </div>
        <div class="grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl mb-4">${kbHtml}</div>
        <div class="flex gap-2">
          <button onclick="initHangman();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
        </div>
      `;
    }

    let secretNum = 0, guessHint = '1 - 100';
    function initGuess() { secretNum = Math.floor(Math.random()*100)+1; guessHint = '1 - 100'; }
    window.submitGuess = function() {
      const v = Number(document.getElementById('guessInp').value);
      if (!v) return;
      if (v === secretNum) { guessHint = `= ${secretNum}!`; reportWin('number_guess'); }
      else if (v < secretNum) guessHint = '▲ بالاتر';
      else guessHint = '▼ پایین‌تر';
      renderGuess(document.getElementById('app'));
    };
    function renderGuess(root) {
      if (!secretNum) initGuess();
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <h2 class="text-xl font-extrabold mb-2">1 - 100</h2>
          <p class="font-bold text-amber-400 text-2xl mb-4">${guessHint}</p>
          <input id="guessInp" type="number" min="1" max="100" class="w-full p-3 rounded-xl bg-slate-800 text-white text-center text-xl font-bold mb-3" />
          <button onclick="submitGuess()" class="btn-success w-full py-3 rounded-xl font-bold">${L.check}</button>
        </div>
        <div class="flex gap-2">
          <button onclick="initGuess();render()" class="btn-primary flex-1 py-3 rounded-xl font-bold">${L.reset}</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">${L.back}</button>
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
