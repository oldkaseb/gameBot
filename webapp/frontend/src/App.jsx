import { useEffect, useState } from 'react';
import HokmGame from './pages/HokmGame';
import ChatGame from './pages/ChatGame';

const BTN = {
  primary: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/30 active:scale-95 transition-all",
  success: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 shadow-lg shadow-emerald-600/30 active:scale-95 transition-all",
  danger: "px-4 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 shadow-lg shadow-rose-600/30 active:scale-95 transition-all",
};

async function reportWin(uid, gameType, bestTime = null) {
  if (!uid) return;
  try {
    await fetch('/api/win', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid: Number(uid), game_type: gameType, best_time: bestTime }),
    });
  } catch (e) {
    console.error(e);
  }
}

/* ═══════════ 1. بازی 2048 ═══════════ */
function Game2048({ uid, onBack }) {
  const initBoard = () => {
    const b = Array(4).fill(0).map(() => Array(4).fill(0));
    addRandom(b); addRandom(b);
    return b;
  };
  function addRandom(b) {
    const empty = [];
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) if (!b[r][c]) empty.push([r, c]);
    if (empty.length) {
      const [r, c] = empty[Math.floor(Math.random() * empty.length)];
      b[r][c] = Math.random() < 0.9 ? 2 : 4;
    }
  }
  const [board, setBoard] = useState(initBoard);
  const [score, setScore] = useState(0);

  const slide = (row) => {
    const arr = row.filter(Boolean);
    const out = [];
    let gained = 0;
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] === arr[i + 1]) {
        const v = arr[i] * 2;
        out.push(v); gained += v; i++;
      } else out.push(arr[i]);
    }
    while (out.length < 4) out.push(0);
    return [out, gained];
  };

  const move = (dir) => {
    let b = board.map(r => [...r]);
    const rot = (m) => m[0].map((_, i) => m.map(row => row[i]).reverse());
    if (dir === 'up') b = rot(rot(rot(b)));
    if (dir === 'right') b = b.map(r => r.reverse());
    if (dir === 'down') b = rot(b);

    let totalGain = 0;
    let moved = false;
    b = b.map(row => {
      const [nr, g] = slide(row);
      if (nr.join(',') !== row.join(',')) moved = true;
      totalGain += g;
      return nr;
    });

    if (dir === 'up') b = rot(b);
    if (dir === 'right') b = b.map(r => r.reverse());
    if (dir === 'down') b = rot(rot(rot(b)));

    if (moved) {
      addRandom(b);
      setBoard(b);
      setScore(s => s + totalGain);
      if (b.some(r => r.includes(2048))) reportWin(uid, '2048');
    }
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">پازل 2048</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">امتیاز: {score}</span>
      </div>
      <div className="grid grid-cols-4 gap-2 bg-slate-900/80 p-3 rounded-2xl w-full aspect-square mb-4">
        {board.flat().map((v, idx) => (
          <div key={idx} className={`flex items-center justify-center rounded-xl font-extrabold text-xl ${v ? 'bg-indigo-600 text-white' : 'bg-slate-800/70 text-transparent'}`}>
            {v || 0}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 w-48 mb-4">
        <div />
        <button className={BTN.primary} onClick={() => move('up')}>بالا</button>
        <div />
        <button className={BTN.primary} onClick={() => move('left')}>چپ</button>
        <button className={BTN.success} onClick={() => { setBoard(initBoard()); setScore(0); }}>شروع مجدد</button>
        <button className={BTN.primary} onClick={() => move('right')}>راست</button>
        <div />
        <button className={BTN.primary} onClick={() => move('down')}>پایین</button>
        <div />
      </div>
      <button className={`${BTN.danger} w-full`} onClick={onBack}>بازگشت به منوی بازی‌ها</button>
    </div>
  );
}

/* ═══════════ 2. پازل کششی ۱۵ تایی (Sliding Puzzle) ═══════════ */
function SlidingPuzzle({ uid, onBack }) {
  const createBoard = () => {
    const arr = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  };
  const [tiles, setTiles] = useState(createBoard);
  const [moves, setMoves] = useState(0);
  const solved = tiles.slice(0, 15).every((v, i) => v === i + 1);

  const clickTile = (idx) => {
    if (solved) return;
    const emptyIdx = tiles.indexOf(0);
    const r1 = Math.floor(idx / 4), c1 = idx % 4;
    const r2 = Math.floor(emptyIdx / 4), c2 = emptyIdx % 4;
    if (Math.abs(r1 - r2) + Math.abs(c1 - c2) === 1) {
      const next = [...tiles];
      [next[idx], next[emptyIdx]] = [next[emptyIdx], next[idx]];
      setTiles(next);
      setMoves(m => m + 1);
      if (next.slice(0, 15).every((v, i) => v === i + 1)) reportWin(uid, 'spuzzle');
    }
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">پازل کششی</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">حرکت: {moves}</span>
      </div>
      <div className="grid grid-cols-4 gap-2 bg-slate-900/80 p-3 rounded-2xl w-full aspect-square mb-4">
        {tiles.map((v, i) => (
          <button
            key={i}
            onClick={() => clickTile(i)}
            className={v === 0 ? "bg-slate-800/40 rounded-xl" : `${BTN.primary} text-lg`}
          >
            {v || ''}
          </button>
        ))}
      </div>
      {solved && <div className="mb-3 text-emerald-400 font-bold">تبریک! پازل حل شد!</div>}
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={() => { setTiles(createBoard()); setMoves(0); }}>چینش مجدد</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ 3. بازی جفت‌ها (SameGame) ═══════════ */
function SameGame({ uid, onBack }) {
  const colors = ['bg-rose-600', 'bg-blue-600', 'bg-emerald-600', 'bg-amber-500'];
  const createGrid = () => Array(8).fill(0).map(() => Array(8).fill(0).map(() => Math.floor(Math.random() * 4)));
  const [grid, setGrid] = useState(createGrid);
  const [score, setScore] = useState(0);

  const clickCell = (r0, c0) => {
    const target = grid[r0][c0];
    const q = [[r0, c0]];
    const visited = new Set([`${r0},${c0}`]);
    const group = [[r0, c0]];
    while (q.length) {
      const [r, c] = q.pop();
      for (const [dr, dc] of [[0,1],[0,-1],[1,0],[-1,0]]) {
        const nr = r + dr, nc = c + dc;
        const key = `${nr},${nc}`;
        if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8 && !visited.has(key) && grid[nr][nc] === target) {
          visited.add(key); group.push([nr, nc]); q.push([nr, nc]);
        }
      }
    }
    if (group.length < 2) return;
    const next = grid.map(row => [...row]);
    group.forEach(([r, c]) => { next[r][c] = Math.floor(Math.random() * 4); });
    setGrid(next);
    setScore(s => s + group.length * 10);
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">بازی جفت‌ها</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">امتیاز: {score}</span>
      </div>
      <div className="grid grid-cols-8 gap-1.5 bg-slate-900/80 p-3 rounded-2xl w-full aspect-square mb-4">
        {grid.map((row, r) => row.map((colorIdx, c) => (
          <button
            key={`${r}-${c}`}
            onClick={() => clickCell(r, c)}
            className={`${colors[colorIdx]} rounded-lg active:scale-90 transition-transform`}
          />
        )))}
      </div>
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={() => { setGrid(createGrid()); setScore(0); }}>شروع مجدد</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ 4. بازی دوز ۲ نفره و ۴ نفره (Dooz / Doz4p) ═══════════ */
function DoozGame({ mode = 'dooz', uid, onBack }) {
  const size = mode === 'doz4p' ? 5 : 3;
  const players = mode === 'doz4p' ? ['X', 'O', 'A', 'B'] : ['X', 'O'];
  const [board, setBoard] = useState(() => Array(size * size).fill(''));
  const [turnIdx, setTurnIdx] = useState(0);
  const [winner, setWinner] = useState(null);

  const checkWin = (b, sym) => {
    const need = mode === 'doz4p' ? 4 : 3;
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const dirs = [[0,1],[1,0],[1,1],[1,-1]];
        for (const [dr, dc] of dirs) {
          let ok = true;
          for (let k = 0; k < need; k++) {
            const nr = r + dr * k, nc = c + dc * k;
            if (nr < 0 || nr >= size || nc < 0 || nc >= size || b[nr * size + nc] !== sym) { ok = false; break; }
          }
          if (ok) return true;
        }
      }
    }
    return false;
  };

  const play = (idx) => {
    if (board[idx] || winner) return;
    const sym = players[turnIdx];
    const next = [...board];
    next[idx] = sym;
    setBoard(next);
    if (checkWin(next, sym)) {
      setWinner(sym);
      reportWin(uid, mode);
    } else if (next.every(Boolean)) {
      setWinner('DRAW');
    } else {
      setTurnIdx((turnIdx + 1) % players.length);
    }
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">{mode === 'doz4p' ? 'دوز ۴ نفره' : 'دوز ۲ نفره'}</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">
          {winner ? (winner === 'DRAW' ? 'مساوی!' : `برنده: ${winner}`) : `نوبت: ${players[turnIdx]}`}
        </span>
      </div>
      <div className={`grid ${size === 5 ? 'grid-cols-5' : 'grid-cols-3'} gap-2 bg-slate-900/80 p-3 rounded-2xl w-full aspect-square mb-4`}>
        {board.map((cell, i) => (
          <button
            key={i}
            onClick={() => play(i)}
            className={`${cell === 'X' ? BTN.primary : cell === 'O' ? BTN.success : cell ? BTN.danger : 'bg-slate-800/80 rounded-xl'} text-2xl font-extrabold flex items-center justify-center`}
          >
            {cell}
          </button>
        ))}
      </div>
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={() => { setBoard(Array(size * size).fill('')); setWinner(null); setTurnIdx(0); }}>بازی مجدد</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ 5. چهار در یک ردیف (Connect 4) ═══════════ */
function Connect4Game({ uid, onBack }) {
  const ROWS = 6, COLS = 7;
  const [board, setBoard] = useState(() => Array(ROWS).fill(0).map(() => Array(COLS).fill(0)));
  const [turn, setTurn] = useState(1);
  const [winner, setWinner] = useState(0);

  const drop = (col) => {
    if (winner) return;
    const next = board.map(r => [...r]);
    let placedRow = -1;
    for (let r = ROWS - 1; r >= 0; r--) {
      if (next[r][col] === 0) { next[r][col] = turn; placedRow = r; break; }
    }
    if (placedRow === -1) return;
    setBoard(next);

    const check = (p) => {
      for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
        for (const [dr, dc] of [[0,1],[1,0],[1,1],[1,-1]]) {
          let ok = true;
          for (let k = 0; k < 4; k++) {
            const nr = r + dr*k, nc = c + dc*k;
            if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS || next[nr][nc] !== p) { ok = false; break; }
          }
          if (ok) return true;
        }
      }
      return false;
    };

    if (check(turn)) { setWinner(turn); reportWin(uid, 'connect4'); }
    else setTurn(turn === 1 ? 2 : 1);
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">چهار در یک ردیف</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">
          {winner ? `برنده: بازیکن ${winner}` : `نوبت بازیکن ${turn}`}
        </span>
      </div>
      <div className="grid grid-cols-7 gap-1.5 bg-slate-900/90 p-3 rounded-2xl w-full mb-4">
        {board.map((row, r) => row.map((v, c) => (
          <button
            key={`${r}-${c}`}
            onClick={() => drop(c)}
            className={`aspect-square rounded-full ${v === 1 ? 'bg-rose-600' : v === 2 ? 'bg-emerald-500' : 'bg-slate-800'}`}
          />
        )))}
      </div>
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={() => { setBoard(Array(ROWS).fill(0).map(() => Array(COLS).fill(0))); setWinner(0); setTurn(1); }}>شروع مجدد</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ 6. سنگ کاغذ قیچی (RPS) ═══════════ */
function RPSGame({ uid, onBack }) {
  const options = [
    { id: 'rock', label: 'سنگ', style: BTN.primary },
    { id: 'paper', label: 'کاغذ', style: BTN.success },
    { id: 'scissors', label: 'قیچی', style: BTN.danger },
  ];
  const [score, setScore] = useState({ user: 0, bot: 0 });
  const [status, setStatus] = useState('یکی از گزینه‌ها را انتخاب کنید');

  const play = (choice) => {
    const botChoice = options[Math.floor(Math.random() * 3)].id;
    if (choice === botChoice) {
      setStatus(`مساوی! هر دو ${options.find(o => o.id === choice).label} آوردید.`);
    } else if (
      (choice === 'rock' && botChoice === 'scissors') ||
      (choice === 'paper' && botChoice === 'rock') ||
      (choice === 'scissors' && botChoice === 'paper')
    ) {
      const nextUser = score.user + 1;
      setScore(s => ({ ...s, user: nextUser }));
      setStatus('بردی! امتیاز برای تو ثبت شد.');
      if (nextUser === 3) reportWin(uid, 'rps');
    } else {
      setScore(s => ({ ...s, bot: s.bot + 1 }));
      setStatus('حریف این دست رو برد!');
    }
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <h2 className="text-xl font-extrabold mb-2">سنگ، کاغذ، قیچی</h2>
      <p className="mb-4 text-slate-300 font-bold">شما: {score.user} — رقیب: {score.bot}</p>
      <div className="p-4 rounded-2xl bg-slate-900/80 w-full text-center mb-4 font-bold">{status}</div>
      <div className="grid grid-cols-3 gap-3 w-full mb-4">
        {options.map(o => (
          <button key={o.id} className={o.style} onClick={() => play(o.id)}>{o.label}</button>
        ))}
      </div>
      <button className={`${BTN.danger} w-full`} onClick={onBack}>بازگشت</button>
    </div>
  );
}

/* ═══════════ 7. بازی حافظه (Memory) ═══════════ */
function MemoryGame({ uid, onBack }) {
  const symbols = ['A','B','C','D','E','F','G','H'];
  const createDeck = () => [...symbols, ...symbols].sort(() => Math.random() - 0.5);
  const [cards, setCards] = useState(createDeck);
  const [flipped, setFlipped] = useState([]);
  const [matched, setMatched] = useState([]);

  const flip = (idx) => {
    if (flipped.length === 2 || flipped.includes(idx) || matched.includes(idx)) return;
    const next = [...flipped, idx];
    setFlipped(next);
    if (next.length === 2) {
      const [i1, i2] = next;
      if (cards[i1] === cards[i2]) {
        const nm = [...matched, i1, i2];
        setMatched(nm);
        setFlipped([]);
        if (nm.length === 16) reportWin(uid, 'memory');
      } else {
        setTimeout(() => setFlipped([]), 700);
      }
    }
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <div className="w-full flex justify-between items-center mb-4">
        <span className="text-xl font-extrabold">بازی حافظه</span>
        <span className="px-3 py-1 rounded-lg bg-white/10 font-bold">جفت‌ها: {matched.length / 2} از 8</span>
      </div>
      <div className="grid grid-cols-4 gap-2 bg-slate-900/80 p-3 rounded-2xl w-full aspect-square mb-4">
        {cards.map((c, idx) => {
          const open = flipped.includes(idx) || matched.includes(idx);
          return (
            <button
              key={idx}
              onClick={() => flip(idx)}
              className={`${open ? BTN.success : BTN.primary} text-xl flex items-center justify-center`}
            >
              {open ? c : '?'}
            </button>
          );
        })}
      </div>
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={() => { setCards(createDeck()); setFlipped([]); setMatched([]); }}>شروع مجدد</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ 8. گردونه شانس (Gardone) ═══════════ */
function GardoneGame({ uid, onBack }) {
  const prizes = ['۱۰۰ امتیاز', 'شانس مجدد', '۲۵۰ امتیاز', 'پوچ', '۵۰۰ امتیاز طلایی', '۵۰ امتیاز'];
  const [result, setResult] = useState('برای چرخاندن گردونه دکمه سبز را بزنید');
  const [spinning, setSpinning] = useState(false);

  const spin = () => {
    if (spinning) return;
    setSpinning(true);
    setResult('در حال چرخش...');
    setTimeout(() => {
      const prize = prizes[Math.floor(Math.random() * prizes.length)];
      setResult(`نتیجه گردونه: ${prize}`);
      setSpinning(false);
      if (prize.includes('امتیاز')) reportWin(uid, 'gardone');
    }, 1000);
  };

  return (
    <div className="p-4 flex flex-col items-center max-w-md mx-auto">
      <h2 className="text-xl font-extrabold mb-4">گردونه شانس راینو</h2>
      <div className="p-8 rounded-2xl bg-slate-900/80 w-full text-center mb-4 font-extrabold text-lg">
        {result}
      </div>
      <div className="flex gap-2 w-full">
        <button className={`${BTN.success} flex-1`} onClick={spin} disabled={spinning}>چرخش گردونه</button>
        <button className={`${BTN.danger} flex-1`} onClick={onBack}>بازگشت</button>
      </div>
    </div>
  );
}

/* ═══════════ هاب اصلی مینی‌اپ ═══════════ */
function App() {
  const [gameData, setGameData] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const game = params.get('game') || 'hub';
    const session = params.get('session') || 'solo';
    const tg = window.Telegram?.WebApp;
    tg?.ready?.();
    tg?.expand?.();
    const uid = tg?.initDataUnsafe?.user?.id?.toString() || params.get('uid') || '0';
    setGameData({ game, session, uid });
  }, []);

  if (!gameData) {
    return <div className="glass-bg h-screen text-white flex items-center justify-center">در حال بارگذاری...</div>;
  }

  const goHub = () => setGameData(prev => ({ ...prev, game: 'hub' }));
  const openGame = (g) => setGameData(prev => ({ ...prev, game: g }));

  const isChat = ['typing', 'hangman', 'guess'].includes(gameData.game);

  return (
    <div className="glass-bg min-h-screen text-white font-sans">
      {gameData.game === 'hokm' && <HokmGame session={gameData.session} uid={gameData.uid} />}
      {isChat && <ChatGame game={gameData.game} session={gameData.session} uid={gameData.uid} />}
      {gameData.game === '2048' && <Game2048 uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'spuzzle' && <SlidingPuzzle uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'samegame' && <SameGame uid={gameData.uid} onBack={goHub} />}
      {(gameData.game === 'dooz' || gameData.game === 'doz4p') && <DoozGame mode={gameData.game} uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'connect4' && <Connect4Game uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'rps' && <RPSGame uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'memory' && <MemoryGame uid={gameData.uid} onBack={goHub} />}
      {gameData.game === 'gardone' && <GardoneGame uid={gameData.uid} onBack={goHub} />}

      {gameData.game === 'hub' && (
        <div className="p-4 max-w-md mx-auto">
          <h1 className="text-2xl font-extrabold text-center mb-2">مینی‌اپ بازی‌های راینو</h1>
          <p className="text-center text-slate-300 text-sm mb-5">بازی مورد نظر خود را انتخاب کنید</p>
          <div className="grid grid-cols-2 gap-3">
            <button className={BTN.primary} onClick={() => openGame('2048')}>پازل 2048</button>
            <button className={BTN.primary} onClick={() => openGame('spuzzle')}>پازل کششی</button>
            <button className={BTN.primary} onClick={() => openGame('samegame')}>جفت‌ها</button>
            <button className={BTN.primary} onClick={() => openGame('dooz')}>دوز ۲ نفره</button>
            <button className={BTN.primary} onClick={() => openGame('doz4p')}>دوز ۴ نفره</button>
            <button className={BTN.success} onClick={() => openGame('connect4')}>چهار در ردیف</button>
            <button className={BTN.success} onClick={() => openGame('hokm')}>حکم ۴ نفره</button>
            <button className={BTN.primary} onClick={() => openGame('rps')}>سنگ کاغذ قیچی</button>
            <button className={BTN.primary} onClick={() => openGame('memory')}>بازی حافظه</button>
            <button className={BTN.primary} onClick={() => openGame('typing')}>تایپ سرعتی</button>
            <button className={BTN.primary} onClick={() => openGame('hangman')}>حدس کلمه</button>
            <button className={BTN.primary} onClick={() => openGame('guess')}>حدس عدد</button>
            <button className={`${BTN.success} col-span-2`} onClick={() => openGame('gardone')}>گردونه شانس</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
