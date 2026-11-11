# -*- coding: utf-8 -*-
"""webapp/backend/main.py — سرور کامل مینی‌اپ و وب‌سوکت با تضمین عدم نمایش صفحه سفید"""

import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

try:
    from webapp.backend.game_logic.hokm import HokmGame
    from webapp.backend.auth import validate_init_data
except ImportError:
    try:
        from game_logic.hokm import HokmGame
        from auth import validate_init_data
    except Exception:
        HokmGame = None
        validate_init_data = None

from database import db

app = FastAPI(title="Rhino Games Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

active_rooms = {}
connections = {}


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


@app.websocket("/ws/{game_type}/{session_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_type: str,
    session_id: str,
    user_id: int,
    init_data: str = Query(None),
):
    await websocket.accept()

    if session_id not in connections:
        connections[session_id] = []
    connections[session_id].append({"ws": websocket, "user_id": user_id})

    if session_id not in active_rooms:
        if game_type == "hokm" and HokmGame:
            active_rooms[session_id] = HokmGame(session_id)
        else:
            active_rooms[session_id] = {
                "type": game_type,
                "board": {},
                "players": [],
            }

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if game_type == "hokm" and HokmGame:
                game = active_rooms[session_id]
                game.handle_action(user_id, msg)
                for conn in list(connections.get(session_id, [])):
                    try:
                        await conn["ws"].send_json(game.get_state_for_player(conn["user_id"]))
                    except Exception:
                        pass
            else:
                payload = {"user_id": user_id, "game_type": game_type, **msg}
                for conn in list(connections.get(session_id, [])):
                    try:
                        await conn["ws"].send_json(payload)
                    except Exception:
                        pass

    except WebSocketDisconnect:
        if session_id in connections:
            connections[session_id] = [
                c for c in connections[session_id] if c["ws"] != websocket
            ]


# رابط مستقل با استایل و بازی‌های داخلی
FALLBACK_MINIAPP_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>RHINO GAMES</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {
      background: radial-gradient(circle at top, #1e1b4b 0%, #0f172a 60%, #020617 100%);
      color: #fff;
      font-family: system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      margin: 0;
      user-select: none;
    }
    .btn-primary {
      background: linear-gradient(135deg, #2563eb, #4f46e5);
      box-shadow: 0 4px 15px rgba(37, 99, 235, 0.35);
    }
    .btn-success {
      background: linear-gradient(135deg, #059669, #10b981);
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35);
    }
    .btn-danger {
      background: linear-gradient(135deg, #e11d48, #ef4444);
      box-shadow: 0 4px 15px rgba(225, 29, 72, 0.35);
    }
    .glass-card {
      background: rgba(15, 23, 42, 0.78);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.12);
    }
  </style>
</head>
<body class="p-4 flex flex-col items-center">
  <div id="app" class="w-full max-w-md"></div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const params = new URLSearchParams(window.location.search);
    let currentGame = params.get('game') || 'hub';
    const uid = tg?.initDataUnsafe?.user?.id || params.get('uid') || 0;

    function nav(game) {
      currentGame = game;
      render();
    }

    function render() {
      const root = document.getElementById('app');
      if (currentGame === 'hub') return renderHub(root);
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

    function renderHub(root) {
      root.innerHTML = `
        <div class="glass-card rounded-2xl p-5 text-center mb-4">
          <h1 class="text-2xl font-extrabold mb-1">مینی‌اپ بازی‌های راینو</h1>
          <p class="text-slate-300 text-sm">بازی مورد نظر خود را انتخاب کنید</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <button onclick="nav('2048')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">پازل 2048</button>
          <button onclick="nav('spuzzle')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">پازل کشویی</button>
          <button onclick="nav('samegame')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">جفت‌ها</button>
          <button onclick="nav('dooz')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">دوز ۲ نفره</button>
          <button onclick="nav('doz4p')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">دوز ۴ نفره</button>
          <button onclick="nav('connect4')" class="btn-success py-3 px-4 rounded-xl font-bold active:scale-95 transition">چهار در ردیف</button>
          <button onclick="nav('rps')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">سنگ کاغذ قیچی</button>
          <button onclick="nav('memory')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">بازی حافظه</button>
          <button onclick="nav('typing')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">تایپ سرعتی</button>
          <button onclick="nav('hangman')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">حدس کلمه</button>
          <button onclick="nav('guess')" class="btn-primary py-3 px-4 rounded-xl font-bold active:scale-95 transition">حدس عدد</button>
        </div>
      `;
    }

    let b2048 = null, s2048 = 0;
    function init2048() {
      b2048 = Array(4).fill(0).map(() => Array(4).fill(0));
      s2048 = 0;
      addTile2048(); addTile2048();
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
          <h2 class="text-xl font-extrabold">بازی 2048</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">امتیاز: ${s2048}</span>
        </div>
        <div class="grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="grid grid-cols-3 gap-2 mb-4">
          <div></div><button onclick="move2048('up')" class="btn-primary py-3 rounded-xl font-bold">بالا</button><div></div>
          <button onclick="move2048('right')" class="btn-primary py-3 rounded-xl font-bold">راست</button>
          <button onclick="init2048();render()" class="btn-success py-3 rounded-xl font-bold">جدید</button>
          <button onclick="move2048('left')" class="btn-primary py-3 rounded-xl font-bold">چپ</button>
          <div></div><button onclick="move2048('down')" class="btn-primary py-3 rounded-xl font-bold">پایین</button><div></div>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">بازگشت به منو</button>
      `;
    }

    let spz = null;
    function initSpz() { spz = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0].sort(() => Math.random()-0.5); }
    window.clickSpz = function(i) {
      const emp = spz.indexOf(0);
      const r1 = Math.floor(i/4), c1 = i%4, r2 = Math.floor(emp/4), c2 = emp%4;
      if (Math.abs(r1-r2)+Math.abs(c1-c2)===1) {
        [spz[i], spz[emp]] = [spz[emp], spz[i]];
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
          <h2 class="text-xl font-extrabold">پازل کشویی</h2>
          <button onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-lg font-bold text-sm">چینش مجدد</button>
        </div>
        <div class="grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">بازگشت به منو</button>
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
      if (!doozWin) doozTurn = (doozTurn + 1) % syms.length;
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
          <h2 class="text-xl font-extrabold">${mode==='doz4p'?'دوز ۴ نفره':'دوز ۲ نفره'}</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${doozWin ? 'برنده: '+doozWin : 'نوبت: '+syms[doozTurn]}</span>
        </div>
        <div class="grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initDooz('${mode}');render()" class="btn-success flex-1 py-3 rounded-xl font-bold">بازی مجدد</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
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
          if (!c4Win) c4Turn = c4Turn===1?2:1;
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
          <h2 class="text-xl font-extrabold">چهار در ردیف</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${c4Win ? 'برنده: بازیکن '+c4Win : 'نوبت بازیکن '+c4Turn}</span>
        </div>
        <div class="grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initC4();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">شروع مجدد</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
        </div>
      `;
    }

    let rpsU = 0, rpsB = 0, rpsMsg = 'یکی از گزینه‌ها را انتخاب کنید';
    window.playRPS = function(c) {
      const opts = ['rock','paper','scissors'];
      const b = opts[Math.floor(Math.random()*3)];
      const names = {rock:'سنگ', paper:'کاغذ', scissors:'قیچی'};
      if (c===b) rpsMsg = `مساوی! هر دو ${names[c]} آوردید.`;
      else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) {
        rpsU++; rpsMsg = `بردی! شما ${names[c]} و حریف ${names[b]}`;
      } else {
        rpsB++; rpsMsg = `حریف برد! حریف ${names[b]} آورد`;
      }
      renderRPS(document.getElementById('app'));
    };
    function renderRPS(root) {
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <h2 class="text-xl font-extrabold mb-2">سنگ، کاغذ، قیچی</h2>
          <p class="font-bold text-slate-300 mb-3">شما: ${rpsU} — حریف: ${rpsB}</p>
          <div class="p-3 rounded-xl bg-slate-900/90 font-bold">${rpsMsg}</div>
        </div>
        <div class="grid grid-cols-3 gap-3 mb-4">
          <button onclick="playRPS('rock')" class="btn-primary py-3 rounded-xl font-bold">سنگ</button>
          <button onclick="playRPS('paper')" class="btn-success py-3 rounded-xl font-bold">کاغذ</button>
          <button onclick="playRPS('scissors')" class="btn-danger py-3 rounded-xl font-bold">قیچی</button>
        </div>
        <button onclick="nav('hub')" class="btn-danger w-full py-3 rounded-xl font-bold">بازگشت به منو</button>
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
          <h2 class="text-xl font-extrabold">بازی حافظه</h2>
          <span class="glass-card px-3 py-1 rounded-lg font-bold">${memMatch.length/2} / 8</span>
        </div>
        <div class="grid grid-cols-4 gap-2 glass-card p-3 rounded-2xl mb-4">${cells}</div>
        <div class="flex gap-2">
          <button onclick="initMem();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">شروع مجدد</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
        </div>
      `;
    }

    const sentences = ["سرعت و دقت در تایپ نشانه مهارت است", "راینوبازی بهترین تجربه مسابقه آنلاین", "تمرکز بالا رمز پیروزی در رقابت‌هاست"];
    let targetSentence = sentences[0], typeStart = 0, typeMsg = '';
    function initTyping() {
      targetSentence = sentences[Math.floor(Math.random()*sentences.length)];
      typeStart = Date.now(); typeMsg = '';
    }
    window.checkTyping = function() {
      const val = document.getElementById('typeInput').value.trim();
      if (val === targetSentence) {
        const sec = ((Date.now() - typeStart)/1000).toFixed(1);
        typeMsg = `آفرین! در ${sec} ثانیه تایپ کردی!`;
        renderTyping(document.getElementById('app'));
      } else {
        typeMsg = 'متن وارد شده هنوز دقیق نیست!';
        renderTyping(document.getElementById('app'));
      }
    };
    function renderTyping(root) {
      if (!typeStart) initTyping();
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl mb-4">
          <h2 class="text-xl font-extrabold mb-3">مسابقه تایپ سرعتی</h2>
          <p class="p-3 rounded-xl bg-slate-900 font-bold text-emerald-400 mb-4">${targetSentence}</p>
          <input id="typeInput" type="text" placeholder="جمله بالا را اینجا تایپ کنید..." class="w-full p-3 rounded-xl bg-slate-800 text-white border border-slate-600 mb-3" />
          ${typeMsg ? `<p class="font-bold text-amber-400 mb-2">${typeMsg}</p>` : ''}
          <button onclick="checkTyping()" class="btn-success w-full py-3 rounded-xl font-bold">ثبت و بررسی</button>
        </div>
        <div class="flex gap-2">
          <button onclick="initTyping();render()" class="btn-primary flex-1 py-3 rounded-xl font-bold">جمله جدید</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
        </div>
      `;
    }

    const wordsList = ["تلگرام", "راینو", "پایتون", "امپراتور", "کهکشان"];
    let hmWord = "", hmGuessed = [], hmLives = 6;
    function initHangman() {
      hmWord = wordsList[Math.floor(Math.random()*wordsList.length)];
      hmGuessed = []; hmLives = 6;
    }
    window.guessLetter = function(ch) {
      if (hmGuessed.includes(ch) || hmLives <= 0) return;
      hmGuessed.push(ch);
      if (!hmWord.includes(ch)) hmLives--;
      renderHangman(document.getElementById('app'));
    };
    function renderHangman(root) {
      if (!hmWord) initHangman();
      const display = hmWord.split('').map(c => hmGuessed.includes(c) ? c : '_').join(' ');
      const won = hmWord.split('').every(c => hmGuessed.includes(c));
      const letters = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی".split('');
      const kbHtml = letters.map(ch => `
        <button onclick="guessLetter('${ch}')" class="py-2 rounded-lg font-bold ${hmGuessed.includes(ch) ? 'bg-slate-800 text-slate-500' : 'btn-primary'}">${ch}</button>
      `).join('');
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-extrabold">حدس کلمه</h2>
            <span class="px-3 py-1 rounded-lg bg-rose-600/30 font-bold">جان: ${hmLives}</span>
          </div>
          <div class="text-3xl font-extrabold tracking-widest my-4">${display}</div>
          ${won ? '<p class="text-emerald-400 font-bold">تبریک! درست حدس زدی!</p>' : ''}
          ${hmLives <= 0 ? `<p class="text-rose-400 font-bold">باختی! کلمه: ${hmWord}</p>` : ''}
        </div>
        <div class="grid grid-cols-7 gap-1.5 glass-card p-3 rounded-2xl mb-4">${kbHtml}</div>
        <div class="flex gap-2">
          <button onclick="initHangman();render()" class="btn-success flex-1 py-3 rounded-xl font-bold">کلمه جدید</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
        </div>
      `;
    }

    let secretNum = 0, guessHint = 'یک عدد بین ۱ تا ۱۰۰ حدس بزنید';
    function initGuess() { secretNum = Math.floor(Math.random()*100)+1; guessHint = 'یک عدد بین ۱ تا ۱۰۰ حدس بزنید'; }
    window.submitGuess = function() {
      const v = Number(document.getElementById('guessInp').value);
      if (!v) return;
      if (v === secretNum) guessHint = `آفرین! عدد ${secretNum} درست بود!`;
      else if (v < secretNum) guessHint = 'برو بالاتر!';
      else guessHint = 'بیا پایین‌تر!';
      renderGuess(document.getElementById('app'));
    };
    function renderGuess(root) {
      if (!secretNum) initGuess();
      root.innerHTML = `
        <div class="glass-card p-5 rounded-2xl text-center mb-4">
          <h2 class="text-xl font-extrabold mb-2">حدس عدد</h2>
          <p class="font-bold text-amber-400 mb-4">${guessHint}</p>
          <input id="guessInp" type="number" min="1" max="100" placeholder="عدد ۱ تا ۱۰۰" class="w-full p-3 rounded-xl bg-slate-800 text-white text-center text-xl font-bold mb-3" />
          <button onclick="submitGuess()" class="btn-success w-full py-3 rounded-xl font-bold">بررسی</button>
        </div>
        <div class="flex gap-2">
          <button onclick="initGuess();render()" class="btn-primary flex-1 py-3 rounded-xl font-bold">شروع مجدد</button>
          <button onclick="nav('hub')" class="btn-danger flex-1 py-3 rounded-xl font-bold">بازگشت</button>
        </div>
      `;
    }

    render();
  </script>
</body>
</html>
"""

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/{full_path:path}")
    async def serve_fallback(full_path: str):
        return HTMLResponse(content=FALLBACK_MINIAPP_HTML, status_code=200)
