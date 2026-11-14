# -*- coding: utf-8 -*-
"""webapp/backend/js_core_casino.py — بخش ۲ از ۴: هسته سراسری، صفحه اصلی (Hub)، کیف پول دوگانه و ۴ بازی کازینویی"""

JS_CORE_CASINO = r"""
window.onerror = function(msg, url, line) {
  console.warn("MiniApp non-fatal warn:", msg, line);
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

window.uploadedImages = {};
window.uiAssetsMap = {};
window.recentWinsList = [];

/* آپلودر هوشمند با حفظ کامل شفافیت (Transparency) برای فایل‌های PNG توخالی */
window.handleImageUpload = function(inputEl, targetKey, previewImgId) {
  const file = inputEl.files && inputEl.files[0];
  if (!file) return;
  const isTransparentType = file.type === 'image/png' || file.type === 'image/webp' || targetKey === 'store_item_photo';
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
      const dataUrl = isTransparentType ? canvas.toDataURL('image/png') : canvas.toDataURL('image/jpeg', 0.84);
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

/* رندر ایموجی پریمیوم متحرک تلگرام یا آیکون جایگزین */
window.renderTgEmoji = function(emojiId, fallbackIcon = '✨', cls = 'w-5 h-5 inline-block object-contain align-middle') {
  if (emojiId && String(emojiId).length >= 10) {
    return `<img src="/api/tg_emoji/${emojiId}" onerror="this.outerHTML='<span>${fallbackIcon}</span>'" class="${cls}" />`;
  }
  return `<span>${fallbackIcon || ''}</span>`;
};

/* کامپوننت سراسری نمایش آواتار به همراه قاب PNG توخالی + امواج صوتی صحبت کردن در اتاق */
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
  if (window.uiAssetsMap && window.uiAssetsMap[key]) {
    return window.uiAssetsMap[key];
  }
  return fallbackUrl || ('/api/custom_bg/' + key);
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

const HERO_CUSTOM_IMG = window.RHINO_CONFIG?.HERO_CUSTOM_IMG || "";
const BOT_USERNAME = window.RHINO_CONFIG?.BOT_USERNAME || "RhinoGamesBot";
const SHORT_NAME = window.RHINO_CONFIG?.SHORT_NAME || "RhinoGamesApp";
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
    heroTitle: "گیم باکس و روم راینو",
    bigWins: "BIG WINS • برندگان کازینو",
    backMenu: "منو",
    playBtn: "ورود",
    optBot: "🤖 بازی با ربات",
    optInvite: "📩 دعوت دوستان با ربات",
    optShare: "📤 اشتراک‌گذاری لینک میز",
    sendInviteBtn: "ارسال دعوت‌نامه",
    enterTableBtn: "ورود به میز",
    notStartedWarn: "⚠️ این کاربران هنوز ربات را استارت نکرده‌اند:",
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
    games: {
      crash: "CRASH",
      bombs: "BOMBS",
      pickaxe: "HELL PICKAXE",
      slot: "ROYAL SLOT",
      hokm: "HOKM 4P",
      hokm2p: "HOKM 2P",
      dooz: "RINGS 2P",
      doz4p: "RINGS 4P",
      connect4: "CONNECT 4",
      rps: "ROCK PAPER",
      guess: "NUMBER GUESS",
      g2048: "2048 PUZZLE",
      spuzzle: "PUZZLE 15",
      samegame: "COLOR MATCH",
      memory: "MEMORY",
      typing: "SPEED TYPE",
      hangman: "WORD GUESS"
    }
  },
  en: {
    heroTitle: "Rhino Social & Casino",
    bigWins: "BIG WINS",
    backMenu: "Menu", playBtn: "Play",
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
    games: {
      crash: "CRASH",
      bombs: "BOMBS",
      pickaxe: "HELL PICKAXE",
      slot: "ROYAL SLOT",
      hokm: "HOKM 4P",
      hokm2p: "HOKM 2P",
      dooz: "RINGS 2P",
      doz4p: "RINGS 4P",
      connect4: "CONNECT 4",
      rps: "ROCK PAPER",
      guess: "NUMBER GUESS",
      g2048: "2048 PUZZLE",
      spuzzle: "PUZZLE 15",
      samegame: "COLOR MATCH",
      memory: "MEMORY",
      typing: "SPEED TYPE",
      hangman: "WORD GUESS"
    }
  }
};

function T() { return I18N[lang] || I18N.fa; }

let currentGame = parsedGame || 'hub';
let hubFilter = 'all';
const tgUser = tg?.initDataUnsafe?.user || {};
const realTgUid = tgUser.id || Number(params.get('uid')) || 0;
const uid = realTgUid || Math.floor(Math.random()*900000 + 100000);
const isOwner = OWNER_IDS.includes(Number(uid));
const myName = tgUser.first_name || 'CEORHINO';
const myUsername = tgUser.username || '';
const myPhoto = tgUser.photo_url || '';

let hokmPollTimer = null;
let guessPollTimer = null;
let vrPollTimer = null;
let pmPollTimer = null;
let isJoinVerified = false;
let lobbyState = { game: '', maxPlayers: 2, rpsTargetWins: 3, step: 'options', inviteWarning: '', inviteSuccess: '' };

/* متغیرهای سراسری پلتفرم اجتماعی، کیف پول، چت پیوی و کازینو */
let spState = null;
let activeVoiceRoom = null;
let minimizedVoiceRoom = null;
let viewedProfileData = null;
let activePmChat = null;
let activePmPeerUid = 0;
let spMsg = '';
let spErr = '';
let vrSheet = '';
let selectedSeatIdx = 1;
let selectedGiftRecs = [];
let storeTab = 'subs';
let bombsState = null;
let crashLastResult = null;
let pickaxeLastResult = null;
let slotLastResult = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecordingVoice = false;

window.cycleLang = function() {
  const codes = ['fa', 'en'];
  lang = codes[(codes.indexOf(lang) + 1) % codes.length];
  localStorage.setItem('rhino_lang', lang);
  applyDir();
  render();
};

function renderBottomNav() {
  return `
    <div class="fixed bottom-3 left-3 right-3 z-30 bottom-dock px-2.5 py-2 flex justify-around items-center">
      <button type="button" onclick="nav('hub')" class="${currentGame==='hub' ? 'text-purple-400 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black transition">
        <span class="text-lg">🏠</span><span>Home</span>
      </button>
      <button type="button" onclick="nav('voice_hub')" class="${currentGame==='voice_hub' ? 'text-amber-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black transition">
        <span class="text-lg">🎙️</span><span>Rooms</span>
      </button>
      <button type="button" onclick="nav('sp_wallet')" class="w-11 h-10 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-xl shadow-[0_0_18px_rgba(124,58,237,0.75)] border border-purple-300/40">
        🪙
      </button>
      <button type="button" onclick="nav('sp_pm_hub')" class="${currentGame==='sp_pm_hub'||currentGame==='sp_pm_chat' ? 'text-pink-400 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black transition">
        <span class="text-lg">💬</span><span>Chats</span>
      </button>
      <button type="button" onclick="nav('sp_store')" class="${currentGame==='sp_store' ? 'text-emerald-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black transition">
        <span class="text-lg">🛍️</span><span>Store</span>
      </button>
      <button type="button" onclick="openUserProfileModal(${uid})" class="${currentGame==='sp_profile' ? 'text-sky-300 scale-110' : 'text-slate-300'} flex flex-col items-center gap-0.5 text-[10px] font-black transition">
        <span class="text-lg">👤</span><span>Profile</span>
      </button>
    </div>
  `;
}

function renderTopBar(titleText = '') {
  const me = spState?.me || {};
  const langFlags = { fa: '🇮🇷 FA', en: '🇬🇧 EN' };
  return `
    <div class="glass-panel mx-3 mb-2 px-3 py-2 rounded-2xl flex justify-between items-center shrink-0">
      <div class="flex items-center gap-1.5">
        ${currentGame !== 'hub' ? `<button type="button" onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-xs font-extrabold">${T().backMenu}</button>` : `<span class="text-xs font-black text-purple-400">RHINO™</span>`}
        <span class="text-sm font-black text-white truncate max-w-[125px]">${titleText || T().heroTitle}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <button type="button" onclick="nav('sp_wallet')" class="glass-soft px-2 py-1 rounded-xl text-[11px] font-black text-amber-300 flex items-center gap-1">
          <span>🪙 ${(me.coins ?? 1000).toLocaleString()}</span>
          <span class="text-purple-300">| ⭐ ${me.stars_balance ?? 0}</span>
        </button>
        ${isOwner && currentGame !== 'tower_admin' ? `
          <button type="button" onclick="nav('tower_admin')" class="btn-primary px-2 py-1 rounded-xl text-[11px] font-black text-amber-200">👑</button>
        ` : ''}
        <button type="button" onclick="cycleLang()" class="glass-soft px-2 py-1 rounded-xl text-[10px] font-extrabold text-amber-300">
          ${langFlags[lang] || 'FA'}
        </button>
      </div>
    </div>
  `;
}

window.openChannelLink = function(url) {
  if (tg && tg.openTelegramLink && url.startsWith('https://t.me/')) tg.openTelegramLink(url);
  else window.open(url, '_blank');
};

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
        const invSeat = activeVoiceRoom.my_mic_invite;
        if (confirm('🎙️ مدیر اتاق شما را به میکروفون شماره ' + invSeat + ' دعوت کرده است. می‌پذیرید؟')) {
          return callSocialApi('room_op', { room_id: activeVoiceRoom.room_id, op: 'take_seat', seat_idx: String(invSeat) });
        }
      }
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

window.verifyJoinAndRender = async function() {
  const root = document.getElementById('app');
  await loadUiAssets();
  await callSocialApi('state');
  if (!realTgUid || isOwner) { isJoinVerified = true; return render(); }
  try {
    const res = await fetch('/api/check_join/' + realTgUid);
    const data = await res.json();
    if (data && data.joined === false && data.channels?.length > 0) {
      isJoinVerified = false;
      const chBtns = data.channels.map(c => `<button type="button" onclick="openChannelLink('${c.url}')" class="btn-primary w-full py-3 rounded-xl font-bold">${c.title}</button>`).join('');
      root.innerHTML = `
        ${renderTopBar()}
        <div class="flex-1 flex flex-col justify-center p-4">
          <div class="glass-panel p-6 rounded-3xl text-center">
            <div class="text-3xl mb-2">🔒</div>
            <div class="flex flex-col gap-2.5 my-4">${chBtns}</div>
            <button type="button" onclick="verifyJoinAndRender()" class="btn-success w-full py-3.5 rounded-xl font-black">✅ OK</button>
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
  if (vrPollTimer && g !== 'voice_room_live') { clearInterval(vrPollTimer); vrPollTimer = null; }
  if (pmPollTimer && g !== 'sp_pm_chat') { clearInterval(pmPollTimer); pmPollTimer = null; }
  spMsg = ''; spErr = '';
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
   صفحه اصلی پلتفرم راینو (کازینو + اتاق‌های صوتی + بازی‌ها + لول ثروت و جذابیت تا ۵۰)
   ═══════════════════════════════════════════════════════════════════════════ */
function renderHub(root) {
  const G = T().games;
  const me = spState?.me || {};
  const avatarUrl = me.photo || myPhoto || '';
  const displayName = me.display_name || myName;
  const wLvl = me.wealth_level || 1;
  const cLvl = me.charm_level || 1;

  const allCards = [
    { id: "crash",      title: G.crash,       mode: "PVE",  tag: "HOT",  online: 34, cat: "casino", c1: "#581c87", c2: "#ec4899", icon: "🚀" },
    { id: "bombs",      title: G.bombs,       mode: "PVE",  tag: "NEW",  online: 26, cat: "casino", c1: "#78350f", c2: "#f59e0b", icon: "💣" },
    { id: "pickaxe",    title: G.pickaxe,     mode: "PVE",  tag: "NEW",  online: 18, cat: "casino", c1: "#7f1d1d", c2: "#ef4444", icon: "⛏️" },
    { id: "slot",       title: G.slot,        mode: "SLOT", tag: "NEW",  online: 22, cat: "casino", c1: "#312e81", c2: "#8b5cf6", icon: "🎰" },
    { id: "voice_hub",  title: "VOICE ROOMS", mode: "LIVE", tag: "VIP",  online: 42, cat: "pvp",    c1: "#1e1b4b", c2: "#a855f7", icon: "🎙️" },
    { id: "hokm",       title: G.hokm,        mode: "PVP",  tag: "HOT",  online: 28, cat: "pvp",    c1: "#7f1d1d", c2: "#b91c1c", icon: "♠️" },
    { id: "hokm2p",     title: G.hokm2p,      mode: "PVP",  tag: "",     online: 12, cat: "pvp",    c1: "#500724", c2: "#db2777", icon: "👑" },
    { id: "dooz",       title: G.dooz,        mode: "PVP",  tag: "",     online: 9,  cat: "pvp",    c1: "#1e1b4b", c2: "#3b82f6", icon: "🟢" },
    { id: "doz4p",      title: G.doz4p,       mode: "PVP",  tag: "",     online: 6,  cat: "pvp",    c1: "#4a044e", c2: "#ec4899", icon: "🟣" },
    { id: "connect4",   title: G.connect4,    mode: "PVP",  tag: "",     online: 11, cat: "pvp",    c1: "#064e3b", c2: "#10b981", icon: "🔴" },
    { id: "rps",        title: G.rps,         mode: "PVP",  tag: "",     online: 7,  cat: "pvp",    c1: "#312e81", c2: "#6366f1", icon: "✂️" },
    { id: "guess",      title: G.guess,       mode: "PVP",  tag: "LIVE", online: 19, cat: "pvp",    c1: "#14532d", c2: "#22c55e", icon: "🎯" },
    { id: "2048",       title: G.g2048,       mode: "PVE",  tag: "",     online: 15, cat: "pve",    c1: "#1e3a8a", c2: "#2563eb", icon: "🧩" },
    { id: "spuzzle",    title: G.spuzzle,     mode: "PVE",  tag: "",     online: 5,  cat: "pve",    c1: "#0c4a6e", c2: "#0ea5e9", icon: "🔢" },
    { id: "samegame",   title: G.samegame,    mode: "PVE",  tag: "",     online: 8,  cat: "pve",    c1: "#581c87", c2: "#a855f7", icon: "🟦" },
    { id: "memory",     title: G.memory,      mode: "PVE",  tag: "",     online: 10, cat: "pve",    c1: "#4c1d95", c2: "#8b5cf6", icon: "🧠" },
    { id: "typing",     title: G.typing,      mode: "PVE",  tag: "",     online: 4,  cat: "pve",    c1: "#78350f", c2: "#f59e0b", icon: "⌨️" },
    { id: "hangman",    title: G.hangman,     mode: "PVE",  tag: "",     online: 9,  cat: "pve",    c1: "#881337", c2: "#e11d48", icon: "🕵️" }
  ];

  const filteredCards = allCards.filter(c => {
    if (hubFilter === 'casino') return c.cat === 'casino';
    if (hubFilter === 'pvp') return c.cat === 'pvp';
    return true;
  });

  const winsData = window.recentWinsList?.length ? window.recentWinsList : [
    { name: displayName, game: "CRASH", win: 4500, mult: "3.0x", time: "1m ago" },
    { name: "RHINO VIP", game: "BOMBS", win: 9200, mult: "4.6x", time: "2m ago" }
  ];

  const bigWinsHtml = winsData.map((w, i) => `
    <div class="glass-panel rounded-2xl px-3 py-2 flex items-center gap-2.5 shrink-0 min-w-[175px] border border-purple-500/25">
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center font-black text-xs shrink-0">
        ${(w.name || 'P')[0]}
      </div>
      <div class="leading-tight truncate">
        <div class="text-[11px] font-black text-amber-300 truncate">👑 ${w.name}</div>
        <div class="text-[9px] text-emerald-300 font-bold">+${(w.win||1200).toLocaleString()} 🪙 (${w.mult||'2x'})</div>
      </div>
      <span class="text-base ml-auto">${['🚀','💣','⛏️','🎰'][i % 4]}</span>
    </div>
  `).join('');

  const cardsHtml = filteredCards.map(g => {
    const customImg = getAssetImg(g.id, '');
    return `
      <div onclick="nav('${g.id}')" class="arcade-card cursor-pointer">
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

  root.innerHTML = `
    ${typeof renderMinimizedFloatingWidget === 'function' ? renderMinimizedFloatingWidget() : ''}
    <div class="glass-panel mx-3 mb-2 px-3 py-2.5 rounded-3xl flex items-center justify-between gap-2 shrink-0 border border-purple-500/25">
      <div onclick="openUserProfileModal(${uid})" class="flex items-center gap-3 min-w-0 flex-1 cursor-pointer py-0.5 pr-1">
        ${window.renderAvatarWithFrame(avatarUrl, displayName, 'w-11 h-11 text-base', me.ring_photo, me.ring_css, 'border-2 border-purple-400')}
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1">
            <span class="font-black text-sm text-white truncate">${displayName}</span>
            ${me.custom_badge_emoji_id ? window.renderTgEmoji(me.custom_badge_emoji_id, me.custom_badge_icon || '💎', 'w-5 h-5') : ''}
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
        <button type="button" onclick="nav('sp_wallet')" title="شارژ و تبدیل کیف پول" class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-xl font-black shadow-lg border border-purple-300/40">+</button>
        ${isOwner ? `
          <button type="button" onclick="nav('tower_admin')" title="پنل مدیریت" class="w-10 h-10 rounded-full glass-soft flex items-center justify-center text-base border border-amber-400/50">👑</button>
        ` : ''}
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col gap-3">
      <div>
        <div class="flex items-center justify-between px-1 mb-1.5">
          <div class="flex items-center gap-1 text-[11px] font-black text-orange-400 tracking-wider uppercase">
            <span>🔥</span><span>${T().bigWins}</span>
          </div>
          <div class="flex gap-1.5 text-[10px] font-black">
            <button type="button" onclick="setHubFilter('all')" class="px-2 py-0.5 rounded-lg ${hubFilter==='all'?'btn-primary':'glass-soft'}">همه</button>
            <button type="button" onclick="setHubFilter('casino')" class="px-2 py-0.5 rounded-lg ${hubFilter==='casino'?'btn-primary':'glass-soft'}">🎰 کازینو</button>
            <button type="button" onclick="setHubFilter('pvp')" class="px-2 py-0.5 rounded-lg ${hubFilter==='pvp'?'btn-primary':'glass-soft'}">🎙️ روم و گروهی</button>
          </div>
        </div>
        <div class="flex gap-2 overflow-x-auto pb-1">${bigWinsHtml}</div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        ${cardsHtml}
      </div>
    </div>

    ${renderBottomNav()}
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   کیف پول دوگانه (Wallet): شارژ با استارز و تبدیل آنی استارز به سکه
   ═══════════════════════════════════════════════════════════════════════════ */
function renderSpWallet(root) {
  if (!spState) { callSocialApi('state'); return; }
  const me = spState.me;
  const packs = spState.topup_packs || [];
  const rate = spState.rate || 100;

  const packsHtml = packs.map(pk => `
    <div class="glass-soft p-3 rounded-2xl flex items-center justify-between border border-purple-400/30">
      <div>
        <div class="font-black text-xs text-white">${pk.title}</div>
        <div class="text-[10px] text-emerald-300 font-bold">معادل ${((pk.stars + pk.bonus_stars) * rate).toLocaleString()} 🪙 سکه کازینو</div>
      </div>
      <button type="button" onclick="callSocialApi('create_topup_invoice',{pack_id:'${pk.id}'})" class="btn-primary px-3.5 py-2 rounded-xl text-xs font-black shrink-0">
        ⭐ ${pk.stars} Stars
      </button>
    </div>
  `).join('');

  root.innerHTML = `
    ${renderTopBar('🪙 کیف پول و تبدیل استارز')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3 text-xs">
      ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 font-bold text-center">${spMsg}</div>` : ''}
      ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 font-bold text-center">${spErr}</div>` : ''}

      <div class="glass-panel p-4 rounded-3xl grid grid-cols-2 gap-3 text-center border border-purple-400/40">
        <div class="glass-soft p-3 rounded-2xl">
          <div class="text-slate-400 text-[10px] font-bold">موجودی استارز کیف پول</div>
          <div class="text-2xl font-black text-amber-300 mt-1">⭐ ${(me.stars_balance||0).toLocaleString()}</div>
        </div>
        <div class="glass-soft p-3 rounded-2xl">
          <div class="text-slate-400 text-[10px] font-bold">موجودی سکه کازینو و خرید</div>
          <div class="text-2xl font-black text-emerald-300 mt-1">🪙 ${(me.coins||0).toLocaleString()}</div>
        </div>
      </div>

      <div class="glass-panel p-4 rounded-3xl space-y-2.5 border border-emerald-400/30">
        <h3 class="font-black text-sm text-emerald-300 text-center">🔄 تبدیل استارز به سکه کازینو (هر ۱ ⭐ = ${rate} 🪙)</h3>
        <div class="flex gap-2">
          <input id="conv_stars_inp" type="number" value="${me.stars_balance > 0 ? me.stars_balance : 10}" min="1" placeholder="تعداد استارز..." class="flex-1 p-3 rounded-xl glass-soft text-center font-black text-sm text-white" />
          <button type="button" onclick="callSocialApi('convert_stars_to_coins',{stars:Number(document.getElementById('conv_stars_inp').value||0)})" class="btn-success px-5 rounded-xl font-black text-xs">
            ⚡ تبدیل به سکه
          </button>
        </div>
      </div>

      <div class="glass-panel p-4 rounded-3xl space-y-2.5">
        <h3 class="font-black text-sm text-amber-300 text-center">⭐ شارژ کیف پول با استارز تلگرام</h3>
        <div class="flex flex-col gap-2">${packsHtml}</div>
      </div>
    </div>
    ${renderBottomNav()}
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۴ بازی کازینویی (CRASH, BOMBS, HELL PICKAXE, ROYAL SLOT)
   ═══════════════════════════════════════════════════════════════════════════ */
function renderCrashGame(root) {
  const r = crashLastResult;
  root.innerHTML = `
    ${renderTopBar('🚀 CRASH • انفجار موشک')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col justify-between gap-3">
      <div class="glass-panel p-6 rounded-3xl text-center relative overflow-hidden border border-pink-500/40 my-auto">
        <div class="text-6xl mb-3 ${r ? (r.won ? 'animate-bounce' : '') : ''}">${r ? (r.won ? '🚀💎' : '💥🔥') : '🚀'}</div>
        <div class="text-4xl font-black ${r ? (r.won ? 'text-emerald-400' : 'text-rose-400') : 'text-amber-300'} mb-1 ltr-grid">
          ${r ? (r.crash_point.toFixed(2) + 'x') : '1.00x'}
        </div>
        <div class="text-xs font-bold text-slate-300">
          ${spMsg || spErr || 'مبلغ شرط و ضریب خروج خودکار (Target Cashout) را مشخص کنید:'}
        </div>
      </div>

      <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
        <div class="grid grid-cols-2 gap-2.5">
          <div>
            <label class="block text-[11px] text-slate-300 font-bold mb-1">🪙 مبلغ شرط (سکه):</label>
            <input id="cr_bet" type="number" value="200" min="10" class="w-full p-3 rounded-xl glass-soft text-center font-black text-base text-amber-300" />
          </div>
          <div>
            <label class="block text-[11px] text-slate-300 font-bold mb-1">🎯 ضریب برداشت (مثلاً 2.0):</label>
            <input id="cr_mult" type="number" step="0.1" value="2.0" min="1.1" class="w-full p-3 rounded-xl glass-soft text-center font-black text-base text-emerald-300" />
          </div>
        </div>
        <div class="grid grid-cols-4 gap-1.5 text-[11px] font-black">
          <button type="button" onclick="document.getElementById('cr_mult').value='1.5'" class="glass-soft py-1.5 rounded-lg">1.5x</button>
          <button type="button" onclick="document.getElementById('cr_mult').value='2.0'" class="glass-soft py-1.5 rounded-lg">2.0x</button>
          <button type="button" onclick="document.getElementById('cr_mult').value='3.0'" class="glass-soft py-1.5 rounded-lg">3.0x</button>
          <button type="button" onclick="document.getElementById('cr_mult').value='5.0'" class="glass-soft py-1.5 rounded-lg">5.0x</button>
        </div>
        <button type="button" onclick="callSocialApi('casino_play',{game:'crash',bet:Number(document.getElementById('cr_bet').value||100),target_mult:Number(document.getElementById('cr_mult').value||2)})" class="btn-primary w-full py-4 rounded-2xl font-black text-base">
          🚀 پرتاب موشک و ثبت شرط
        </button>
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
    let content = '❓';
    let cls = 'glass-soft hover:border-amber-400';
    if (isRev && isBomb) { content = '💣'; cls = 'btn-danger'; }
    else if (isRev) { content = '🪙'; cls = 'btn-success'; }
    else if (b.game_over && isBomb) { content = '💣'; cls = 'bg-rose-950/70 border border-rose-500/40'; }

    gridHtml += `
      <button type="button" ${!b.active || isRev ? 'disabled' : ''} onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'pick',cell:${i}})"
        class="aspect-square rounded-2xl font-black text-xl flex items-center justify-center transition ${cls}">
        ${content}
      </button>
    `;
  }

  root.innerHTML = `
    ${renderTopBar('💣 BOMBS • بمب و سکه')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col justify-between gap-2.5 text-xs">
      ${spMsg ? `<div class="p-2.5 rounded-2xl bg-emerald-600/35 border border-emerald-400 font-bold text-center">${spMsg}</div>` : ''}
      ${spErr ? `<div class="p-2.5 rounded-2xl bg-rose-600/40 border border-rose-400 font-bold text-center">${spErr}</div>` : ''}

      <div class="glass-panel px-4 py-2.5 rounded-2xl flex justify-between items-center font-black">
        <span>ضریب فعلی: <b class="text-emerald-300 text-sm">${b.mult || 1.0}x</b></span>
        <span>جایزه فعلی: <b class="text-amber-300 text-sm">${(b.potential_win || 0).toLocaleString()} 🪙</b></span>
      </div>

      <div class="ltr-grid grid grid-cols-5 gap-2 glass-panel p-3 rounded-3xl">
        ${gridHtml}
      </div>

      <div class="glass-panel p-3.5 rounded-3xl space-y-2.5">
        ${b.active ? `
          <button type="button" onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'cashout'})" class="btn-success w-full py-4 rounded-2xl font-black text-sm">
            💰 برداشت جایزه (${(b.potential_win || b.bet).toLocaleString()} 🪙)
          </button>
        ` : `
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-[10px] text-slate-300 mb-1">🪙 مبلغ شرط (سکه):</label>
              <input id="bm_bet" type="number" value="${b.bet || 200}" min="10" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-amber-300" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-300 mb-1">💣 تعداد بمب‌ها (۱ تا ۱۵):</label>
              <select id="bm_mines" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-black text-center">
                ${[3, 5, 7, 10, 15].map(n => `<option value="${n}" ${(b.mines_count||5)===n?'selected':''}>${n} بمب</option>`).join('')}
              </select>
            </div>
          </div>
          <button type="button" onclick="callSocialApi('casino_play',{game:'bombs',sub_op:'start',bet:Number(document.getElementById('bm_bet').value||200),mines:Number(document.getElementById('bm_mines').value||5)})" class="btn-primary w-full py-3.5 rounded-2xl font-black text-sm">
            💣 شروع بازی و کاشت بمب‌ها
          </button>
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
    <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col justify-between gap-3">
      <div class="glass-panel p-6 rounded-3xl text-center my-auto space-y-3 border border-amber-400/40">
        <div class="text-6xl">${isPick ? '⛏️💎' : (res?.reels ? res.reels.join(' ') : '🎰 7️⃣ 💎')}</div>
        <div class="text-2xl font-black text-amber-300">${res ? (res.mult + 'x') : 'آماده شانس‌آزمایی!'}</div>
        <div class="text-xs font-bold text-slate-200">${spMsg || spErr || (isPick ? 'با کلنگ دوزخی سنگ معدن را بشکن و تا ۱۲ برابر سکه ببر!' : 'گردونه سلطنتی را بچرخان و تا ۱۵ برابر سکه برنده شو!')}</div>
      </div>

      <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
        <label class="block text-[11px] text-slate-300 font-bold text-center">🪙 مبلغ شرط (سکه):</label>
        <input id="ps_bet" type="number" value="200" min="10" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-amber-300" />
        <button type="button" onclick="callSocialApi('casino_play',{game:'${mode}',bet:Number(document.getElementById('ps_bet').value||200)})" class="btn-primary w-full py-4 rounded-2xl font-black text-base">
          ${isPick ? '⛏️ ضربه با کلنگ دوزخی' : '🎰 چرخش اسلات سلطنتی'}
        </button>
      </div>
    </div>
    ${renderBottomNav()}
  `;
}
"""
