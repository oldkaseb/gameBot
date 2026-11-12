# -*- coding: utf-8 -*-
"""webapp/backend/main.py — سرور کامل گیم باکس راینو (مینی‌اپ گلس‌مورفیسم + لابی ۳ گزینه‌ای + حکم فرش ایرانی)"""

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
CUSTOM_MENU_BG = BASE_DIR / "menu_bg.jpg"
CUSTOM_CARPET_BG = BASE_DIR / "hokm_carpet.jpg"

hokm_rooms: dict[str, HokmGame] = {}
guess_rooms: dict[str, dict] = {}
voice_signals: dict[str, list] = {}

GAME_META = {
    "hub":          {"title": "RHINO GAME BOX",      "c1": (15, 23, 42),  "c2": (79, 70, 229)},
    "hokm":         {"title": "HOKM 4 PLAYERS",      "c1": (127, 17, 22), "c2": (185, 28, 28)},
    "hokm2p":       {"title": "HOKM 2 PLAYERS",      "c1": (127, 17, 22), "c2": (185, 28, 28)},
    "2048":         {"title": "PUZZLE 2048",         "c1": (15, 23, 42),  "c2": (37, 99, 235)},
    "spuzzle":      {"title": "SLIDING PUZZLE",      "c1": (15, 23, 42),  "c2": (14, 165, 233)},
    "samegame":     {"title": "SAME GAME",           "c1": (15, 23, 42),  "c2": (168, 85, 247)},
    "dooz":         {"title": "COLOR RINGS 2P",      "c1": (15, 23, 42),  "c2": (59, 130, 246)},
    "doz4p":        {"title": "COLOR RINGS 4P",      "c1": (15, 23, 42),  "c2": (236, 72, 153)},
    "connect4":     {"title": "CONNECT FOUR",        "c1": (6, 78, 59),   "c2": (16, 185, 129)},
    "rps":          {"title": "ROCK PAPER SCISSORS", "c1": (15, 23, 42),  "c2": (99, 102, 241)},
    "memory":       {"title": "MEMORY MATCH",        "c1": (15, 23, 42),  "c2": (139, 92, 246)},
    "typing":       {"title": "TYPING SPEED",        "c1": (15, 23, 42),  "c2": (245, 158, 11)},
    "hangman":      {"title": "WORD GUESS",          "c1": (15, 23, 42),  "c2": (225, 29, 72)},
    "guess":        {"title": "GROUP NUMBER GUESS",  "c1": (15, 23, 42),  "c2": (16, 185, 129)},
    "gardone_anim": {"title": "LUCKY WHEEL",         "c1": (76, 29, 149), "c2": (217, 70, 239)},
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
    draw.text((w // 2, 215), "RHINO™ GAME BOX", fill=(165, 180, 252), font=font_med, anchor="mm")
    draw.rounded_rectangle([230, 285, w - 230, 350], radius=18, fill=(16, 185, 129))
    draw.text((w // 2, 317), "PLAY NOW", fill=(255, 255, 255), font=font_sm, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.get("/api/banner/{game_type}.png")
async def serve_game_banner(game_type: str):
    if game_type == "rhino_hero" and CUSTOM_HERO_FILE.exists():
        return FileResponse(str(CUSTOM_HERO_FILE))
    if game_type == "menu_bg" and CUSTOM_MENU_BG.exists():
        return FileResponse(str(CUSTOM_MENU_BG))
    if game_type == "hokm_carpet" and CUSTOM_CARPET_BG.exists():
        return FileResponse(str(CUSTOM_CARPET_BG))
    png_bytes = generate_game_banner(game_key=game_type)
    return Response(content=png_bytes, media_type="image/png")


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
    action: str  # create | state | guess | restart
    min_val: int = 1
    max_val: int = 100
    guess_val: int | None = None


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


@app.post("/api/invite_friends")
async def api_invite_friends(payload: InvitePlayersPayload):
    """
    دعوت دوستان از طریق ربات با یوزرنیم یا آیدی عددی.
    اگر کاربر تا کنون ربات را استارت نکرده باشد، به دعوت‌کننده اخطار دقیق می‌دهد.
    """
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
                            f"🎮 <b>دعوت‌نامه میز بازی گیم باکس راینو</b>\n\n"
                            f"👤 دوست شما <b>{payload.inviter_name}</b> شما را به میز بازی دعوت کرده است!\n"
                            f"برای ورود مستقیم به بازی روی دکمه زیر بزنید:"
                        ),
                        reply_markup=kb([[success("▶️ ورود مستقیم به میز بازی", url=join_url)]]),
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
    """حدس عدد همگانی گروهی: ساخت بازه، اشتراک‌گذاری، ثبت برنده و دکمه دور بعد فقط برای سازنده"""
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
            return {"ok": False, "error": "فقط سازنده بازی می‌تواند دور جدید را شروع کند!", "room": room}
        room["secret"] = random.randint(room["min"], room["max"])
        room["winner_id"] = None
        room["winner_name"] = ""
        room["history"] = []

    elif payload.action == "guess" and payload.guess_val is not None and not room["winner_id"]:
        gval = int(payload.guess_val)
        if gval == room["secret"]:
            room["winner_id"] = payload.uid
            room["winner_name"] = payload.name
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "🏆 درست حدس زد!"})
            try:
                await db.add_win(payload.uid, "number_guess")
            except Exception:
                pass
        elif gval < room["secret"]:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬆️ برو بالاتر"})
        else:
            room["history"].insert(0, {"name": payload.name, "val": gval, "hint": "⬇️ بیا پایین‌تر"})
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


MINIAPP_TEMPLATE = """<!DOCTYPE html>
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
    :root {
      --menu-bg: url('__MENU_BG__');
      --carpet-bg: url('__CARPET_BG__');
    }
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body {
      width: 100vw;
      height: 100dvh;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: #070b14;
      background-image:
        var(--menu-bg),
        radial-gradient(circle at 20% 15%, rgba(79, 70, 229, 0.28) 0%, transparent 45%),
        radial-gradient(circle at 80% 85%, rgba(16, 185, 129, 0.22) 0%, transparent 45%);
      background-size: cover;
      background-position: center;
      color: #fff;
      font-family: system-ui, -apple-system, sans-serif;
      user-select: none;
    }
    /* فاصله ایمن از بالای صفحه گوشی برای عدم تداخل با دکمه‌های بستن و مینیمایز تلگرام */
    #app {
      width: 100vw;
      height: 100dvh;
      padding-top: calc(env(safe-area-inset-top, 14px) + 38px);
      padding-bottom: env(safe-area-inset-bottom, 8px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    /* تم گلس‌مورفیسم با اوپاسیتی کم و بلور نرم */
    .glass-panel {
      background: rgba(15, 23, 42, 0.42);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    }
    .glass-soft {
      background: rgba(255, 255, 255, 0.07);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.12);
    }
    .btn-primary {
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.85), rgba(79, 70, 229, 0.85));
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255,255,255,0.22);
    }
    .btn-success {
      background: linear-gradient(135deg, rgba(5, 150, 105, 0.88), rgba(16, 185, 129, 0.88));
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255,255,255,0.22);
    }
    .btn-danger {
      background: linear-gradient(135deg, rgba(225, 29, 72, 0.88), rgba(239, 68, 68, 0.88));
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255,255,255,0.22);
    }
    .ltr-grid { direction: ltr !important; }

    /* زمینه فرش ایرانی قرمز حکم (قابل جایگزینی با فایل hokm_carpet.jpg در گیت‌هاب) */
    .persian-carpet {
      position: relative;
      width: 100%;
      height: 100%;
      background-color: #781014;
      background-image:
        var(--carpet-bg),
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
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }

    const HERO_CUSTOM_IMG = "__HERO_IMAGE__";
    const BOT_USERNAME = "__BOT_USERNAME__";
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
        wipBadge: "در حال ساخت",
        backMenu: "بازگشت به منو",
        optBot: "🤖 بازی با ربات (شروع فوری)",
        optInvite: "📩 دعوت دوستان از طریق ربات",
        optShare: "📤 اشتراک‌گذاری لینک میز بازی در چت‌ها",
        sendInviteBtn: "ارسال دعوت‌نامه با ربات",
        notStartedWarn: "⚠️ کاربران زیر هنوز ربات را استارت نکرده‌اند! لطفاً به آن‌ها بگو ابتدا ربات را استارت کنند:",
        swipeHint: "برای حرکت، صفحه بازی را به چپ، راست، بالا یا پایین بکشید"
      },
      en: {
        heroTitle: "Rhino Game Box",
        heroBody: "Welcome to Rhino Game Box my friend!\nWe gathered awesome games in one place for you.\nEnjoy!",
        wipBadge: "Coming Soon",
        backMenu: "Back to Menu",
        optBot: "🤖 Play with AI Bot",
        optInvite: "📩 Invite Friends via Bot",
        optShare: "📤 Share Table Link to Chats",
        sendInviteBtn: "Send Bot Invites",
        notStartedWarn: "⚠️ These users haven't started the bot yet! Tell them to start the bot first:",
        swipeHint: "Swipe Up, Down, Left, or Right on the board to move"
      },
      ar: {
        heroTitle: "صندوق ألعاب رينو",
        heroBody: "مرحباً بك في صندوق ألعاب رينو يا صديقي\nجمعنا لك أروع الألعاب في مكان واحد\nاستمتع!",
        wipBadge: "قيد الإنشاء",
        backMenu: "العودة للقائمة",
        optBot: "🤖 اللعب مع البوت",
        optInvite: "📩 دعوة الأصدقاء عبر البوت",
        optShare: "📤 مشاركة رابط الطاولة",
        sendInviteBtn: "إرسال الدعوة",
        notStartedWarn: "⚠️ هؤلاء المستخدمون لم يشغلوا البوت بعد! أخبرهم بتشغيل البوت أولاً:",
        swipeHint: "اسحب لليمين أو اليسار أو للأعلى أو للأسفل للتحرك"
      },
      tr: {
        heroTitle: "Rhino Oyun Kutusu",
        heroBody: "Rhino Oyun Kutusuna hoş geldin dostum!\nHarika oyunları senin için bir araya getirdik.",
        wipBadge: "Yapım Aşamasında",
        backMenu: "Menüye Dön",
        optBot: "🤖 Bot ile Oyna",
        optInvite: "📩 Bot ile Arkadaş Davet Et",
        optShare: "📤 Masa Linkini Paylaş",
        sendInviteBtn: "Davet Gönder",
        notStartedWarn: "⚠️ Bu kullanıcılar henüz botu başlatmadı! Önce botu başlatmalarını söyleyin:",
        swipeHint: "Hareket etmek için kaydırın"
      },
      ru: {
        heroTitle: "Игровая Коробка Rhino",
        heroBody: "Добро пожаловать в Rhino Game Box, друг!\nЗдесь собраны лучшие игры для тебя.",
        wipBadge: "В разработке",
        backMenu: "В меню",
        optBot: "🤖 Играть с ботом",
        optInvite: "📩 Пригласить друзей через бота",
        optShare: "📤 Поделиться ссылкой на стол",
        sendInviteBtn: "Отправить приглашения",
        notStartedWarn: "⚠️ Эти пользователи ещё не запустили бота:",
        swipeHint: "Свайпайте по полю для хода"
      },
      de: {
        heroTitle: "Rhino Spielbox",
        heroBody: "Willkommen in der Rhino Spielbox, mein Freund!\nGenieße unsere Spiele.",
        wipBadge: "In Arbeit",
        backMenu: "Zurück zum Menü",
        optBot: "🤖 Gegen Bot spielen",
        optInvite: "📩 Freunde über Bot einladen",
        optShare: "📤 Tisch-Link teilen",
        sendInviteBtn: "Einladung senden",
        notStartedWarn: "⚠️ Diese Nutzer haben den Bot noch nicht gestartet:",
        swipeHint: "Wische über das Feld zum Bewegen"
      },
      zh: {
        heroTitle: "Rhino 游戏盒",
        heroBody: "欢迎来到 Rhino 游戏盒，朋友！\n这里汇集了超棒的游戏，尽情享受吧！",
        wipBadge: "开发中",
        backMenu: "返回菜单",
        optBot: "🤖 与机器人对战",
        optInvite: "📩 通过机器人邀请好友",
        optShare: "📤 分享房间链接",
        sendInviteBtn: "发送邀请",
        notStartedWarn: "⚠️ 以下用户尚未启动机器人，请先让他们启动：",
        swipeHint: "上下左右滑动屏幕进行移动"
      }
    };

    function T() { return I18N[lang] || I18N.fa; }

    let currentGame = parsedGame || 'hub';
    const tgUser = tg?.initDataUnsafe?.user || {};
    const realTgUid = tgUser.id || Number(params.get('uid')) || 0;
    const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
    const myName = tgUser.first_name || 'بازیکن';
    const myUsername = tgUser.username || '';
    const myPhoto = tgUser.photo_url || '';

    let hokmPollTimer = null;
    let guessPollTimer = null;
    let isJoinVerified = false;
    let lobbyState = { game: '', maxPlayers: 2, rpsTargetWins: 3, step: 'options', inviteWarning: '', inviteSuccess: '' };

    window.cycleLang = function() {
      const codes = ['fa', 'en', 'ar', 'tr', 'ru', 'de', 'zh'];
      lang = codes[(codes.indexOf(lang) + 1) % codes.length];
      localStorage.setItem('rhino_lang', lang);
      applyDir();
      render();
    };

    function renderTopBar(titleText = '') {
      const langFlags = { fa: '🇮🇷 FA', en: '🇬🇧 EN', ar: '🇸🇦 AR', tr: '🇹🇷 TR', ru: '🇷🇺 RU', de: '🇩🇪 DE', zh: '🇨🇳 ZH' };
      return `
        <div class="glass-panel mx-3 mb-2 px-3.5 py-2 rounded-2xl flex justify-between items-center shrink-0">
          <div class="flex items-center gap-2">
            ${currentGame !== 'hub' ? `<button onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-xs font-extrabold">${T().backMenu}</button>` : `<span class="text-xs font-black text-indigo-300">RHINO™</span>`}
            <span class="text-sm font-black text-white">${titleText || T().heroTitle}</span>
          </div>
          <button onclick="cycleLang()" class="glass-soft px-2.5 py-1 rounded-xl text-xs font-extrabold text-amber-300">
            🌐 ${langFlags[lang] || 'FA'}
          </button>
        </div>
      `;
    }

    window.openChannelLink = function(url) {
      if (tg && tg.openTelegramLink && url.startsWith('https://t.me/')) tg.openTelegramLink(url);
      else window.open(url, '_blank');
    };

    window.verifyJoinAndRender = async function(showAlertOnFail = false) {
      const root = document.getElementById('app');
      if (!realTgUid) { isJoinVerified = true; return render(); }
      try {
        const res = await fetch('/api/check_join/' + realTgUid);
        const data = await res.json();
        if (data && data.joined === false && data.channels?.length > 0) {
          isJoinVerified = false;
          if (showAlertOnFail && tg?.showAlert) tg.showAlert("لطفاً ابتدا در کانال عضو شوید!");
          const chBtns = data.channels.map(c => `<button onclick="openChannelLink('${c.url}')" class="btn-primary w-full py-3 rounded-xl font-bold">عضویت در ${c.title}</button>`).join('');
          root.innerHTML = `
            ${renderTopBar()}
            <div class="flex-1 flex flex-col justify-center p-4">
              <div class="glass-panel p-6 rounded-3xl text-center">
                <h2 class="text-xl font-black mb-3">🔒 عضویت اجباری</h2>
                <div class="flex flex-col gap-2.5 mb-4">${chBtns}</div>
                <button onclick="verifyJoinAndRender(true)" class="btn-success w-full py-3.5 rounded-xl font-black">✅ عضو شدم (ورود)</button>
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

    /* ═══════════ صفحه اصلی گیم باکس راینو (کارت معرفی + ۳ بازی در حال ساخت + لیست بازی‌ها) ═══════════ */
    function renderHub(root) {
      const wipGames = [
        { title: "شکارچی سیاه‌چال", icon: "🏰" },
        { title: "هک گاوصندوق سایبری", icon: "🔐" },
        { title: "برج شیاطین", icon: "👹" }
      ];
      const activeGames = [
        { id: "hokm", title: "حکم ۴ نفره (فرش ایرانی)", badge: "۴ نفره • لابی/ربات", icon: "♠️", cls: "btn-success" },
        { id: "hokm2p", title: "حکم ۲ نفره", badge: "۲ نفره • لابی/ربات", icon: "👑", cls: "btn-success" },
        { id: "dooz", title: "دوز با حلقه‌های رنگی", badge: "۲ نفره • انتخاب رنگ", icon: "🟢", cls: "btn-primary" },
        { id: "doz4p", title: "دوز ۴ نفره رنگی", badge: "۴ نفره • انتخاب رنگ", icon: "🟣", cls: "btn-primary" },
        { id: "connect4", title: "چهار در یک ردیف", badge: "۲ نفره • استراتژیک", icon: "🔴", cls: "btn-success" },
        { id: "rps", title: "سنگ کاغذ قیچی", badge: "تعیین سقف برد + لابی", icon: "✂️", cls: "btn-primary" },
        { id: "guess", title: "حدس عدد همگانی گروه", badge: "تعیین بازه + اشتراک‌گذاری", icon: "🎯", cls: "btn-success" },
        { id: "2048", title: "پازل ۲۰۴۸ رنگی (اسکرولی)", badge: "تک‌نفره • لمسی", icon: "🧩", cls: "btn-primary" },
        { id: "spuzzle", title: "پازل کشویی ۱۵ تایی (اسکرولی)", badge: "تک‌نفره • لمسی", icon: "🔢", cls: "btn-primary" },
        { id: "samegame", title: "بازی جفت‌های رنگی", badge: "پازل امتیازی", icon: "🟦", cls: "btn-primary" },
        { id: "memory", title: "مسابقه کارت‌های حافظه", badge: "لابی / فکری", icon: "🧠", cls: "btn-primary" },
        { id: "typing", title: "مسابقه تایپ سرعتی", badge: "ثبت رکورد ثانیه", icon: "⌨️", cls: "btn-primary" },
        { id: "hangman", title: "حدس کلمه فارسی", badge: "هوشی", icon: "🕵️", cls: "btn-primary" }
      ];

      const wipHtml = wipGames.map(w => `
        <div class="glass-soft rounded-2xl p-3 flex items-center justify-between opacity-75">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl">${w.icon}</span>
            <span class="font-extrabold text-sm text-slate-200">${w.title}</span>
          </div>
          <span class="px-2.5 py-1 rounded-xl bg-amber-500/20 border border-amber-400/40 text-amber-300 text-[11px] font-black">🛠️ ${T().wipBadge}</span>
        </div>
      `).join('');

      const gamesHtml = activeGames.map(g => `
        <button onclick="nav('${g.id}')" class="glass-panel rounded-2xl p-3.5 flex items-center justify-between text-right active:scale-[0.98] transition">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-xl ${g.cls} flex items-center justify-center text-2xl">${g.icon}</div>
            <div>
              <div class="font-black text-sm text-white">${g.title}</div>
              <div class="text-[11px] text-slate-300 font-bold mt-0.5">${g.badge}</div>
            </div>
          </div>
          <span class="px-3 py-1.5 rounded-xl ${g.cls} text-xs font-extrabold">ورود ◀</span>
        </button>
      `).join('');

      root.innerHTML = `
        ${renderTopBar(T().heroTitle)}
        <div class="flex-1 overflow-y-auto px-3 pb-6 flex flex-col gap-3">
          <!-- کارت اصلی معرفی تیم راینو -->
          <div class="glass-panel rounded-3xl overflow-hidden shrink-0">
            <img src="${HERO_CUSTOM_IMG}" onerror="this.src='/api/banner/hub.png'" class="w-full h-40 object-cover border-b border-white/10" />
            <div class="p-4 text-center">
              <h1 class="text-xl font-black text-amber-300 mb-1.5">${T().heroTitle}</h1>
              <p class="text-xs text-slate-200 font-bold leading-relaxed whitespace-pre-line">${T().heroBody}</p>
            </div>
          </div>

          <!-- سه بازی در حال ساخت -->
          <div class="flex flex-col gap-2">${wipHtml}</div>

          <!-- لیست سایر بازی‌ها -->
          <div class="flex flex-col gap-2.5 mt-1">${gamesHtml}</div>
        </div>
      `;
    }

    /* ═══════════ درگاه ۳ گزینه‌ای بازی‌های لابی‌دار (ربات / دعوت با باکس یوزرنیم / اشتراک‌گذاری مستقیم) ═══════════ */
    window.setRpsTargetAndContinue = function(n) {
      lobbyState.rpsTargetWins = n;
      lobbyState.step = 'options';
      renderLobbyGate(document.getElementById('app'));
    };

    window.startLobbyWithBot = function() {
      nav(lobbyState.game, true);
    };

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
        if (data.not_started?.length > 0) {
          lobbyState.inviteWarning = `${T().notStartedWarn}\n(${data.not_started.join(' ، ')})`;
        } else {
          lobbyState.inviteWarning = '';
        }
        if (data.invited?.length > 0) {
          lobbyState.inviteSuccess = `✅ دعوت‌نامه برای (${data.invited.join(' ، ')}) ارسال شد!`;
        }
        renderLobbyGate(document.getElementById('app'));
      } catch (e) {}
    };

    window.shareTableInline = function(gameType, extraStr = '') {
      const q = `share_${gameType}__${parsedChat}__${extraStr}`;
      if (tg && tg.switchInlineQuery) {
        tg.switchInlineQuery(q, ['users', 'groups', 'supergroups']);
      } else {
        window.open(`https://t.me/${BOT_USERNAME}?startgroup=true`, '_blank');
      }
    };

    function renderLobbyGate(root) {
      if (lobbyState.step === 'rps_count') {
        root.innerHTML = `
          ${renderTopBar('سنگ کاغذ قیچی')}
          <div class="flex-1 flex flex-col justify-center p-4">
            <div class="glass-panel p-6 rounded-3xl text-center">
              <h2 class="text-lg font-black text-amber-300 mb-2">تعداد بردهای لازم را مشخص کنید</h2>
              <p class="text-xs text-slate-300 mb-5">هر بازیکنی که زودتر به این تعداد برد برسد برنده نهایی است:</p>
              <div class="grid grid-cols-3 gap-3 mb-4">
                <button onclick="setRpsTargetAndContinue(3)" class="btn-primary py-4 rounded-2xl font-black text-lg">۳ برد</button>
                <button onclick="setRpsTargetAndContinue(5)" class="btn-success py-4 rounded-2xl font-black text-lg">۵ برد</button>
                <button onclick="setRpsTargetAndContinue(7)" class="btn-danger py-4 rounded-2xl font-black text-lg">۷ برد</button>
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
          boxesHtml += `
            <input type="text" placeholder="یوزرنیم (@username) یا آیدی عددی بازیکن ${i + 1}" class="invite-user-input w-full p-3 rounded-xl glass-soft text-white text-sm font-bold text-center" />
          `;
        }
        root.innerHTML = `
          ${renderTopBar('دعوت دوستان از طریق ربات')}
          <div class="flex-1 overflow-y-auto p-4 flex flex-col justify-center">
            <div class="glass-panel p-5 rounded-3xl text-center">
              <h3 class="text-base font-black text-amber-300 mb-3">مشخصات دوستان خود را وارد کنید (${needed} نفر)</h3>
              <div class="flex flex-col gap-2.5 mb-4">${boxesHtml}</div>
              ${lobbyState.inviteWarning ? `<div class="p-3 rounded-xl bg-rose-600/30 border border-rose-400 text-xs font-extrabold text-rose-200 mb-3 whitespace-pre-line">${lobbyState.inviteWarning}</div>` : ''}
              ${lobbyState.inviteSuccess ? `<div class="p-3 rounded-xl bg-emerald-600/30 border border-emerald-400 text-xs font-extrabold text-emerald-200 mb-3">${lobbyState.inviteSuccess}</div>` : ''}
              <button onclick="submitBotInvites()" class="btn-success w-full py-3.5 rounded-2xl font-black mb-2">${T().sendInviteBtn}</button>
              <button onclick="nav('${lobbyState.game}', true)" class="btn-primary w-full py-3.5 rounded-2xl font-black mb-2">ورود به میز بازی</button>
              <button onclick="lobbyState.step='options';renderLobbyGate(document.getElementById('app'))" class="btn-danger w-full py-2.5 rounded-xl font-bold text-xs">بازگشت به گزینه‌های لابی</button>
            </div>
          </div>
        `;
        return;
      }

      root.innerHTML = `
        ${renderTopBar('انتخاب نحوه شروع بازی')}
        <div class="flex-1 flex flex-col justify-center p-4">
          <div class="glass-panel p-5 rounded-3xl text-center flex flex-col gap-3">
            <h2 class="text-lg font-black text-amber-300 mb-1">چطور می‌خواهید بازی کنید؟</h2>
            <button onclick="startLobbyWithBot()" class="btn-success w-full py-4 rounded-2xl font-black text-sm">
              ${T().optBot}
            </button>
            <button onclick="openInviteBoxes()" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">
              ${T().optInvite}
            </button>
            <button onclick="shareTableInline('${lobbyState.game}', '${lobbyState.rpsTargetWins}');nav('${lobbyState.game}', true)" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">
              ${T().optShare}
            </button>
          </div>
        </div>
      `;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       میز حکم واقعی روی فرش قرمز ایرانی:
       - کارت‌های بزرگ و طبیعی بدون بیرون زدن از صفحه
       - کارت‌های برعکس با حجم واقعی جلوی دست هر تیم تا ۷ کارت
       - کارت مستطیلی پروفایل زیر دست هر بازیکن + تایمر چرخشی ۲ دقیقه‌ای دور عکس
       - چت و ری‌اکشن شفاف بالای اسم بازیکن + مایک صوتی + تعیین تیم توسط سازنده
       ═══════════════════════════════════════════════════════════════════════════ */
    let hokmMode = '4p';
    let hokmError = '';
    let myMicActive = false;
    let localAudioStream = null;

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
        if (data.state) drawHokmTable(data.state);
      } catch (e) {}
    }

    window.hokmChooseSuit = function(s) { callHokmApi('choose_trump', { suit: s }); };
    window.hokmPlayCard = function(code) { callHokmApi('play_card', { card: code }); };
    window.hokmFillBots = function() { callHokmApi('add_bots'); };
    window.hokmStartMatch = function() { callHokmApi('start_match'); };
    window.hokmSwapSeats = function(i1, i2) { callHokmApi('swap_seats', { idx1: i1, idx2: i2 }); };
    window.hokmSendReaction = function(txt) { callHokmApi('chat', { text: txt }); };
    window.hokmSendCustomChat = function() {
      const inp = document.getElementById('hokmChatInp');
      if (inp && inp.value.trim()) {
        callHokmApi('chat', { text: inp.value.trim() });
        inp.value = '';
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
      root.innerHTML = `<div class="p-4 flex-1 flex items-center justify-center"><div class="glass-panel p-6 rounded-3xl font-bold">در حال چیدن فرش حکم...</div></div>`;
      callHokmApi('join');
      if (hokmPollTimer) clearInterval(hokmPollTimer);
      hokmPollTimer = setInterval(() => callHokmApi('state'), 1000);
    }

    function renderRealFaceDownTricks(count) {
      /* کارت‌های برعکس با حجم واقعی که جلوی دست تیم قرار می‌گیرند تا به ۷ برسند */
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

    function renderPlayerRectCard(seat, compact = false) {
      /* کارت مستطیلی مشخصات بازیکن + تایمر چرخشی دور عکس + پاپ‌آپ شفاف پیام/ری‌اکشن بالای اسم */
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
            <div class="text-right leading-tight">
              <div class="text-[11px] font-black text-white flex items-center gap-1">
                ${seat.is_hakem ? '👑' : ''}<span>${seat.name}</span>
                ${seat.mic_on ? '<span class="text-emerald-400">🎙️</span>' : ''}
              </div>
              <div class="text-[9px] text-amber-200/80 font-bold">
                ${seat.team} • ${seat.cards_left} کارت ${seat.is_turn ? `(${seat.timer_sec}s)` : ''}
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

      // ۱. لابی تعیین تیم‌ها توسط سازنده و پر کردن یار کم با هوش مصنوعی
      if (st.status === 'joining') {
        const rowsHtml = pList.map((p, idx) => `
          <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center text-xs font-bold">
            <span>صندلی ${idx + 1} (${p.team}): <b class="text-amber-300">${p.name}</b></span>
            ${isHost && st.mode === '4p' && idx > 0 ? `
              <button onclick="hokmSwapSeats(2, ${idx})" class="btn-primary px-2 py-1 rounded-lg text-[10px]">انتخاب به عنوان یار من</button>
            ` : ''}
          </div>
        `).join('');

        root.innerHTML = `
          ${renderTopBar('چینش میز و تیم‌های حکم')}
          <div class="flex-1 p-3 flex flex-col justify-between">
            <div class="persian-carpet p-4 flex flex-col justify-between">
              <div class="carpet-medallion"></div>
              <div class="z-10 glass-panel p-4 rounded-2xl text-center">
                <h2 class="text-base font-black text-amber-300 mb-1">تعیین یارها و بازیکنان (${pList.length}/${st.max_players})</h2>
                <p class="text-[11px] text-slate-200 mb-3">صندلی ۱ و ۳ هم‌تیمی هستند (رو‌به‌روی هم). اگر یار کم دارید با هوش مصنوعی پر کنید:</p>
                <div class="flex flex-col gap-2 mb-3">${rowsHtml}</div>
                <div class="flex flex-col gap-2">
                  <button onclick="hokmFillBots()" class="btn-success w-full py-3 rounded-xl font-black text-xs">
                    🤖 پر کردن جاهای خالی با هوش مصنوعی و شروع بازی
                  </button>
                  <button onclick="shareTableInline('${st.mode === '2p' ? 'hokm2p' : 'hokm'}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs">
                    📤 اشتراک‌گذاری لینک میز برای دعوت دوستان
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
        return;
      }

      const topSeat = st.seats?.top || { name: 'یار خودی', cards_left: 0, team: 'تیم ۱' };
      const rightSeat = st.seats?.right || null;
      const leftSeat = st.seats?.left || null;
      const bottomSeat = st.seats?.bottom || { name: myName, cards_left: (st.my_hand || []).length, team: 'تیم ۱' };
      const isMyTurn = Number(st.turn_id) === Number(uid) && st.status === 'playing';

      let centerStageHtml = '';
      if (st.status === 'hakem_choosing') {
        if (Number(st.hakem_id) === Number(uid)) {
          centerStageHtml = `
            <div class="z-20 glass-panel p-3.5 rounded-2xl border border-amber-400 text-center max-w-[260px]">
              <div class="text-amber-300 font-black text-xs mb-2">👑 شما حاکم هستید! خال حکم را انتخاب کنید:</div>
              <div class="grid grid-cols-2 gap-2">
                <button onclick="hokmChooseSuit('S')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-sm">♠️ پیک</button>
                <button onclick="hokmChooseSuit('H')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-sm">♥️ دل</button>
                <button onclick="hokmChooseSuit('D')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-sm">♦️ خشت</button>
                <button onclick="hokmChooseSuit('C')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-sm">♣️ گشنیز</button>
              </div>
            </div>
          `;
        } else {
          centerStageHtml = `<div class="z-20 glass-panel px-4 py-2.5 rounded-2xl text-xs font-extrabold text-amber-300">👑 حاکم (${st.hakem_name}) در حال تعیین حکم...</div>`;
        }
      } else if (st.status === 'finished') {
        centerStageHtml = `
          <div class="z-20 glass-panel p-5 rounded-3xl text-center border-2 border-amber-400">
            <div class="text-xl font-black text-amber-300 mb-2">🏆 برنده نهایی: ${st.winner_display}</div>
            <button onclick="nav('hub')" class="btn-success px-5 py-2.5 rounded-xl font-bold text-xs">بازگشت به منو</button>
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

      // چیدمان بزرگ و طبیعی کارت‌های دست در پایین صفحه بدون بیرون زدن از کادر
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

            <!-- ردیف بالا: خروج + حکم + یار روبه‌رو + دست‌های برعکس حریف -->
            <div class="z-20 flex justify-between items-start gap-1">
              <div class="glass-panel px-2 py-1 rounded-xl text-[10px] font-extrabold">
                <div>حکم: <span class="bg-white text-black px-1 rounded">${st.trump_icon}</span></div>
                <div class="text-amber-300">ست ما ${st.our_sets} - ${st.their_sets} حریف</div>
              </div>

              ${renderPlayerRectCard(topSeat)}

              <button onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold">خروج</button>
            </div>

            <!-- ردیف میانی: حریف راست + ترنج وسط فرش + حریف چپ -->
            <div class="z-20 flex-1 flex items-center justify-between px-0.5 min-h-[150px]">
              <div class="flex flex-col items-center gap-1">
                ${rightSeat ? renderPlayerRectCard(rightSeat, true) : ''}
              </div>

              <div class="flex-1 flex flex-col items-center justify-center">
                <div class="mb-1 flex items-center gap-1">
                  <span class="text-[10px] font-bold text-rose-200">دست حریف:</span>
                  ${renderRealFaceDownTricks(st.their_tricks)}
                </div>
                ${centerStageHtml}
              </div>

              <div class="flex flex-col items-center gap-1">
                ${leftSeat ? renderPlayerRectCard(leftSeat, true) : ''}
              </div>
            </div>

            <!-- بخش پایین: کارت‌های برعکسِ برده ما جلوی دستمان + کارت‌های دست بزرگ + کارت مستطیلی پروفایل و چت/مایک -->
            <div class="z-20 flex flex-col items-center gap-1">
              <!-- ردیف ۷ کارت برعکس با حجم واقعی جلوی دست ما -->
              <div class="flex items-center gap-1.5">
                <span class="text-[10px] font-extrabold text-emerald-300">دست‌های ما (${st.our_tricks}/7):</span>
                ${renderRealFaceDownTricks(st.our_tricks)}
              </div>

              ${hokmError ? `<div class="bg-rose-600/90 px-3 py-0.5 rounded-lg text-[11px] font-bold">${hokmError}</div>` : ''}

              <!-- دست کامل کارت‌های بازیکن (بزرگ و داخل کادر) -->
              <div class="ltr-grid w-full flex justify-center items-end py-1 px-1 overflow-hidden">
                ${handHtml}
              </div>

              <!-- کارت مستطیلی مشخصات خود بازیکن + مایک + ری‌اکشن سریع و پیام شفاف -->
              <div class="w-full flex items-center justify-between gap-1 px-1">
                ${renderPlayerRectCard(bottomSeat)}

                <div class="flex items-center gap-1">
                  <button onclick="hokmToggleMic()" class="${myMicActive ? 'btn-success' : 'glass-panel'} px-2.5 py-1.5 rounded-xl text-xs font-bold">
                    ${myMicActive ? '🎙️ روشن' : '🔇 مایک'}
                  </button>
                  <button onclick="hokmSendReaction('🔥 دست خوش!')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">🔥</button>
                  <button onclick="hokmSendReaction('😂')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">😂</button>
                  <button onclick="hokmSendReaction('👏 عالی')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">👏</button>
                </div>
              </div>

              <div class="w-full flex gap-1 px-1">
                <input id="hokmChatInp" type="text" maxlength="40" placeholder="پیام شفاف بالای اسم..." class="flex-1 px-2.5 py-1 rounded-xl glass-soft text-white text-[11px]" />
                <button onclick="hokmSendCustomChat()" class="btn-primary px-3 py-1 rounded-xl text-[11px] font-bold">ارسال</button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    /* ═══════════ بازی ۲۰۴۸ با اسکرول لمسی (بدون دکمه) و رنگ مجزا برای هر عدد ═══════════ */
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
        ${renderTopBar('پازل 2048 رنگی')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2.5 rounded-2xl flex justify-between items-center">
            <span class="font-extrabold text-sm">امتیاز: <b class="text-amber-300">${s2048}</b></span>
            <button onclick="init2048();render()" class="btn-success px-3 py-1 rounded-xl text-xs font-bold">شروع مجدد</button>
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

    /* ═══════════ پازل کشویی با اسکرول لمسی و تپ ═══════════ */
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
        ${renderTopBar('پازل کشویی')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="flex justify-end"><button onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-xl font-bold text-xs">چینش مجدد</button></div>
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

    /* ═══════════ بازی دوز با دایره‌های رنگی و قابلیت انتخاب رنگ توسط کاربر ═══════════ */
    const DOOZ_COLORS = [
      { id: 'rose',   cls: 'bg-rose-500 shadow-[0_0_12px_#f43f5e]',   name: 'قرمز' },
      { id: 'cyan',   cls: 'bg-cyan-400 shadow-[0_0_12px_#22d3ee]',   name: 'آبی نئون' },
      { id: 'emerald',cls: 'bg-emerald-400 shadow-[0_0_12px_#34d399]',name: 'سبز' },
      { id: 'amber',  cls: 'bg-amber-400 shadow-[0_0_12px_#fbbf24]',  name: 'طلایی' },
      { id: 'purple', cls: 'bg-purple-500 shadow-[0_0_12px_#a855f7]', name: 'بنفش' }
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
        ${renderTopBar(mode==='doz4p' ? 'دوز ۴ نفره رنگی' : 'دوز ۲ نفره رنگی')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel p-3 rounded-2xl flex justify-between items-center">
            <span class="text-xs font-extrabold">انتخاب رنگ مهره شما:</span>
            <div class="flex gap-2">${colorPickerHtml}</div>
          </div>
          <div class="ltr-grid grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-3 glass-panel p-4 rounded-3xl">${cells}</div>
          <button onclick="initDooz('${mode}');render()" class="btn-success w-full py-3.5 rounded-2xl font-black">شروع دور جدید</button>
        </div>
      `;
    }

    /* ═══════════ حدس عدد همگانی گروه (باکس از عدد تا عدد + اشتراک‌گذاری + دور بعد فقط سازنده) ═══════════ */
    let guessRoomData = null;
    async function callGuessApi(action, extra = {}) {
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
        if (data.room) {
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
      guessPollTimer = setInterval(() => callGuessApi('state'), 2000);
    };
    window.sendGroupGuessVal = function() {
      const v = Number(document.getElementById('gValInp')?.value);
      if (!isNaN(v)) callGuessApi('guess', { guess_val: v });
    };
    window.restartGroupGuess = function() {
      callGuessApi('restart');
    };

    function renderGuess(root) {
      if (!guessRoomData) {
        root.innerHTML = `
          ${renderTopBar('حدس عدد همگانی')}
          <div class="flex-1 flex flex-col justify-center p-4">
            <div class="glass-panel p-5 rounded-3xl text-center">
              <h2 class="text-lg font-black text-amber-300 mb-2">بازه مسابقه حدس عدد را مشخص کنید</h2>
              <div class="grid grid-cols-2 gap-3 my-4">
                <div>
                  <label class="text-xs text-slate-300 font-bold block mb-1">از عدد:</label>
                  <input id="gMinInp" type="number" value="1" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                </div>
                <div>
                  <label class="text-xs text-slate-300 font-bold block mb-1">تا عدد:</label>
                  <input id="gMaxInp" type="number" value="1000" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                </div>
              </div>
              <button onclick="createGroupGuessRange()" class="btn-success w-full py-3.5 rounded-2xl font-black">ساخت مسابقه حدس عدد</button>
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
        ${renderTopBar(`حدس عدد (${r.min} تا ${r.max})`)}
        <div class="flex-1 flex flex-col justify-between p-4 overflow-hidden">
          <div class="glass-panel p-4 rounded-3xl text-center">
            <div class="flex justify-between items-center text-xs font-bold text-slate-300 mb-2">
              <span>میزبان: ${r.host_name}</span>
              <span>بازه: ${r.min} تا ${r.max}</span>
            </div>
            ${r.winner_id ? `
              <div class="p-4 rounded-2xl bg-emerald-600/30 border border-emerald-400 my-2">
                <div class="text-lg font-black text-emerald-300">🎉 برنده: ${r.winner_name} 🎉</div>
                <div class="text-xs font-bold mt-1">عدد مخفی ${r.secret_revealed} بود!</div>
              </div>
            ` : `
              <div class="flex gap-2 my-2">
                <input id="gValInp" type="number" placeholder="حدس شما..." class="flex-1 p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
                <button onclick="sendGroupGuessVal()" class="btn-success px-5 rounded-xl font-black">ثبت</button>
              </div>
            `}
            <button onclick="shareTableInline('guess', '${r.min}-${r.max}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs mt-2">
              📤 اشتراک‌گذاری بازی در گروه و چت‌ها
            </button>
          </div>

          <div class="flex-1 overflow-y-auto my-3 flex flex-col gap-1.5">${histHtml}</div>

          <div class="flex gap-2">
            ${r.winner_id && isHost ? `<button onclick="restartGroupGuess()" class="btn-success flex-1 py-3.5 rounded-2xl font-black">🔄 یه دور دیگه</button>` : ''}
            <button onclick="guessRoomData=null;nav('hub')" class="btn-danger flex-1 py-3.5 rounded-2xl font-black">${T().backMenu}</button>
          </div>
        </div>
      `;
    }

    /* ═══════════ سنگ کاغذ قیچی با سقف برد تعیین‌شده ═══════════ */
    let rpsU = 0, rpsB = 0, rpsMsg = 'انتخاب کنید:';
    window.playRPS = function(c) {
      const target = lobbyState.rpsTargetWins || 3;
      if (rpsU >= target || rpsB >= target) { rpsU = 0; rpsB = 0; }
      const b = ['rock','paper','scissors'][Math.floor(Math.random()*3)];
      if (c===b) rpsMsg = 'مساوی شد!';
      else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) {
        rpsU++; rpsMsg = rpsU >= target ? '🏆 شما به سقف برد رسیدید و برنده شدید!' : 'این دست را بردید!';
      } else {
        rpsB++; rpsMsg = rpsB >= target ? 'حریف به سقف برد رسید!' : 'حریف این دست را برد!';
      }
      renderRPS(document.getElementById('app'));
    };
    function renderRPS(root) {
      const target = lobbyState.rpsTargetWins || 3;
      root.innerHTML = `
        ${renderTopBar(`سنگ کاغذ قیچی (تا ${target} برد)`)}
        <div class="flex-1 flex flex-col justify-between p-4 text-center">
          <div class="glass-panel p-6 rounded-3xl">
            <div class="text-xs text-amber-300 font-bold mb-2">سقف برد: ${target} امتیاز</div>
            <p class="text-3xl font-black mb-3">${rpsU} — ${rpsB}</p>
            <div class="p-3 rounded-xl glass-soft font-bold text-sm">${rpsMsg}</div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <button onclick="playRPS('rock')" class="btn-primary py-5 rounded-2xl font-black">🪨 سنگ</button>
            <button onclick="playRPS('paper')" class="btn-success py-5 rounded-2xl font-black">📄 کاغذ</button>
            <button onclick="playRPS('scissors')" class="btn-danger py-5 rounded-2xl font-black">✂️ قیچی</button>
          </div>
          <div></div>
        </div>
      `;
    }

    /* ═══════════ سایر بازی‌ها (چهار در ردیف، جفت‌ها، حافظه، تایپ، حدس کلمه، گردونه) ═══════════ */
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
        ${renderTopBar('چهار در یک ردیف')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold text-sm">${c4Win ? '🏆 برنده: بازیکن '+c4Win : 'نوبت بازیکن '+c4Turn}</div>
          <div class="ltr-grid grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${cells}</div>
          <button onclick="initC4();render()" class="btn-success w-full py-3.5 rounded-2xl font-black">شروع مجدد</button>
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
        ${renderTopBar('بازی جفت‌ها')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold">امتیاز: ${sgScore}</div>
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
      const cells = memCards.map((v,i)=>{ const open = memFlip.includes(i) || memMatch.includes(i); return `<button onclick="clickMem(${i})" class="aspect-square rounded-2xl font-black text-2xl ${open?'btn-success':'glass-panel'}">${open?v:'؟'}</button>`; }).join('');
      root.innerHTML = `
        ${renderTopBar('بازی حافظه')}
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
      if (val === targetSentence) typeMsg = `🏆 زمان شما: ${((Date.now() - typeStart)/1000).toFixed(1)} ثانیه`; else typeMsg = '❌ متن دقیق نیست!';
      renderTyping(document.getElementById('app'));
    };
    function renderTyping(root) {
      if (!typeStart) initTyping();
      root.innerHTML = `
        ${renderTopBar('تایپ سرعتی')}
        <div class="flex-1 flex flex-col justify-center p-4">
          <div class="glass-panel p-5 rounded-3xl">
            <p class="p-3.5 rounded-2xl glass-soft font-bold text-emerald-300 mb-4 text-center">${targetSentence}</p>
            <input id="typeInput" type="text" class="w-full p-3.5 rounded-2xl glass-soft text-white mb-3 text-center" />
            ${typeMsg ? `<p class="font-bold text-amber-300 mb-3 text-center">${typeMsg}</p>` : ''}
            <button onclick="checkTyping()" class="btn-success w-full py-3.5 rounded-2xl font-black">ثبت رکورد</button>
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
        ${renderTopBar('حدس کلمه')}
        <div class="flex-1 flex flex-col justify-between p-4">
          <div class="glass-panel p-5 rounded-3xl text-center">
            <div class="text-xs text-rose-300 font-bold">جان باقی‌مانده: ${hmLives}</div>
            <div class="text-3xl font-black tracking-widest my-3">${display}</div>
          </div>
          <div class="grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${kbHtml}</div>
        </div>
      `;
    }

    async function renderGardoneAnim(root) {
      root.innerHTML = `
        ${renderTopBar('گردونه شانس راینو')}
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
        if (idx >= winNames.length) { slot.innerText = "🏆 پایان قرعه‌کشی!"; return; }
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

    function render() {
      const root = document.getElementById('app');
      if (!root) return;
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
      return renderHub(root);
    }

    verifyJoinAndRender(false);
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
    og_img = f"{base_url}/api/banner/{game}.png"
    hero_img = os.environ.get("RHINO_HERO_IMAGE", f"{base_url}/api/banner/rhino_hero.png")
    menu_bg = os.environ.get("RHINO_MENU_BG", f"{base_url}/api/banner/menu_bg.png")
    carpet_bg = os.environ.get("RHINO_CARPET_BG", f"{base_url}/api/banner/hokm_carpet.png")

    html_content = (
        MINIAPP_TEMPLATE
        .replace("__OG_TITLE__", meta["title"])
        .replace("__OG_IMAGE__", og_img)
        .replace("__HERO_IMAGE__", hero_img)
        .replace("__MENU_BG__", menu_bg)
        .replace("__CARPET_BG__", carpet_bg)
        .replace("__BOT_USERNAME__", get_bot_username())
    )
    return HTMLResponse(content=html_content, status_code=200)
