# -*- coding: utf-8 -*-
"""webapp/backend/main.py — سرور مینی‌اپ و استیج انیمیشن قرعه‌کشی رنگارنگ و پیش‌نمایش‌ها"""

import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from database import db

app = FastAPI(title="Rhino Games Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WinPayload(BaseModel):
    uid: int
    game_type: str
    best_time: float | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/win")
async def record_win(payload: WinPayload):
    try:
        await db.add_win(payload.uid, payload.game_type, payload.best_time)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


MINIAPP_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>RHINO GAMES</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {
      background: radial-gradient(circle at top, #0f172a 0%, #020617 100%);
      color: #fff;
      font-family: system-ui, sans-serif;
      min-height: 100vh;
      margin: 0;
      user-select: none;
    }
    .btn-primary { background: linear-gradient(135deg, #2563eb, #4f46e5); }
    .btn-success { background: linear-gradient(135deg, #059669, #10b981); }
    .btn-danger { background: linear-gradient(135deg, #e11d48, #ef4444); }
    .glass { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(255, 255, 255, 0.1); }
    .ltr-box { direction: ltr !important; }
    @keyframes pulseGlow {
      0%, 100% { box-shadow: 0 0 25px rgba(236, 72, 153, 0.6), 0 0 50px rgba(59, 130, 246, 0.5); }
      50% { box-shadow: 0 0 45px rgba(16, 185, 129, 0.8), 0 0 80px rgba(245, 158, 11, 0.6); }
    }
    .anim-wheel { animation: pulseGlow 1.2s infinite alternate; }
  </style>
</head>
<body class="p-4 flex flex-col items-center">
  <div id="app" class="w-full max-w-md"></div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const params = new URLSearchParams(window.location.search);
    const game = params.get('game') || 'hub';

    function render() {
      const root = document.getElementById('app');
      if (game === 'gardone_anim') return renderGardoneAnim(root);
      if (game === '2048') return render2048(root);
      if (game === 'spuzzle') return renderSpuzzle(root);
      if (game === 'samegame') return renderSameGame(root);
      if (game === 'typing') return renderTyping(root);
      if (game === 'hangman') return renderHangman(root);
      if (game === 'guess') return renderGuess(root);
      root.innerHTML = `<div class="glass p-6 rounded-2xl text-center"><h2 class="text-xl font-bold mb-2">اتاق بازی راینو</h2><p class="text-slate-300">در حال اجرای بازی گروهی...</p></div>`;
    }

    /* استیج قرعه‌کشی انیمیشنی زنده */
    function renderGardoneAnim(root) {
      const allNames = (params.get('names') || 'کاربر ۱,کاربر ۲').split(',');
      const winNames = (params.get('winners') || '').split(',').filter(Boolean);
      
      root.innerHTML = `
        <div class="glass p-5 rounded-2xl text-center mb-4 border border-fuchsia-500/30">
          <h2 class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-400 mb-2">گردونه شانس و هیجان راینو</h2>
          <p class="text-xs text-slate-300">در حال چرخش زنده اسامی برای کشیدن برندگان...</p>
        </div>

        <div class="glass rounded-3xl p-8 text-center my-6 anim-wheel border-2 border-indigo-400 flex flex-col items-center justify-center min-h-[200px]">
          <div id="slotName" class="text-3xl font-extrabold text-amber-300 tracking-wider">آماده‌باش...</div>
        </div>

        <div class="glass p-4 rounded-2xl">
          <h3 class="text-sm font-bold text-emerald-400 mb-2">برندگان تعیین‌شده:</h3>
          <div id="winnersList" class="flex flex-col gap-1.5 text-sm"></div>
        </div>
      `;

      let timer;
      let revealed = 0;
      const slot = document.getElementById('slotName');
      const wList = document.getElementById('winnersList');

      function spinStep() {
        if (revealed >= winNames.length) {
          slot.innerHTML = "🏆 قرعه‌کشی به پایان رسید!";
          return;
        }

        let speed = 50;
        let counter = 0;
        const currentWinner = winNames[revealed];

        const shuffle = setInterval(() => {
          slot.innerText = allNames[Math.floor(Math.random() * allNames.length)];
          counter += speed;
          if (counter > 1500) {
            clearInterval(shuffle);
            slot.innerHTML = `<span class="text-emerald-400">🎉 ${currentWinner} 🎉</span>`;
            revealed++;
            const item = document.createElement('div');
            item.className = "p-2 rounded-xl bg-slate-800/80 font-bold border border-emerald-500/30 text-white";
            item.innerText = `🥇 برنده شماره ${revealed}: ${currentWinner}`;
            wList.appendChild(item);
            setTimeout(spinStep, 1400);
          }
        }, speed);
      }

      setTimeout(spinStep, 700);
    }

    /* بازی 2048 با جهت اصلاح‌شده */
    let b2048 = Array(4).fill(0).map(()=>Array(4).fill(0));
    b2048[0][0]=2; b2048[1][1]=4;
    function render2048(root) {
      const cells = b2048.flat().map(v=>`<div class="aspect-square rounded-xl flex items-center justify-center font-bold text-xl ${v?'btn-primary':'bg-slate-800'}">${v||''}</div>`).join('');
      root.innerHTML = `
        <h2 class="text-xl font-bold mb-3 text-center">پازل ۲۰۴۸</h2>
        <div class="ltr-box grid grid-cols-4 gap-2 glass p-3 rounded-2xl mb-4">${cells}</div>
        <div class="ltr-box grid grid-cols-3 gap-2">
          <div></div><button class="btn-primary py-3 rounded-xl">بالا</button><div></div>
          <button class="btn-primary py-3 rounded-xl">چپ</button>
          <div></div>
          <button class="btn-primary py-3 rounded-xl">راست</button>
          <div></div><button class="btn-primary py-3 rounded-xl">پایین</button><div></div>
        </div>
      `;
    }

    /* تایپ سرعتی */
    function renderTyping(root) {
      root.innerHTML = `
        <div class="glass p-5 rounded-2xl text-center">
          <h2 class="text-xl font-bold mb-2">مسابقه تایپ گروهی</h2>
          <p class="p-3 bg-slate-900 rounded-xl font-bold text-emerald-400 mb-3">سرعت بالا رمز برنده شدن است</p>
          <input type="text" placeholder="اینجا بنویسید..." class="w-full p-3 rounded-xl bg-slate-800 mb-3 text-center" />
          <button class="btn-success w-full py-3 rounded-xl font-bold">ارسال رکورد</button>
        </div>
      `;
    }

    function renderSpuzzle(root) { root.innerHTML = `<div class="glass p-6 rounded-2xl text-center">پازل کشویی آماده بازی است.</div>`; }
    function renderSameGame(root) { root.innerHTML = `<div class="glass p-6 rounded-2xl text-center">بازی جفت‌ها آماده بازی است.</div>`; }
    function renderHangman(root) { root.innerHTML = `<div class="glass p-6 rounded-2xl text-center">حدس کلمه در گروه در دسترس است.</div>`; }
    function renderGuess(root) { root.innerHTML = `<div class="glass p-6 rounded-2xl text-center">حدس عدد در گروه در دسترس است.</div>`; }

    render();
  </script>
</body>
</html>
"""

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/{full_path:path}")
async def serve_entry(full_path: str):
    return HTMLResponse(content=MINIAPP_HTML, status_code=200)
