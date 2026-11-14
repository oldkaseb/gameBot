# -*- coding: utf-8 -*-
"""webapp/backend/js_social.py — بخش ۳ از ۴: اتاق‌های صوتی، چت پیوی با ویس، ازدواج/رفاقت، پروفایل و فروشگاه"""

JS_SOCIAL = r"""
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

window.openDirectPmChat = function(peerUid) {
  activePmPeerUid = Number(peerUid);
  currentGame = 'sp_pm_chat';
  callSocialApi('pm_op', { op: 'load', peer_uid: activePmPeerUid });
  if (pmPollTimer) clearInterval(pmPollTimer);
  pmPollTimer = setInterval(() => {
    if (currentGame === 'sp_pm_chat' && activePmPeerUid && !isUserTyping() && !isRecordingVoice) {
      callSocialApi('pm_op', { op: 'load', peer_uid: activePmPeerUid });
    }
  }, 4000);
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

function renderMinimizedFloatingWidget() {
  if (!minimizedVoiceRoom || currentGame === 'voice_room_live') return '';
  return `
    <div onclick="activeVoiceRoom=minimizedVoiceRoom;minimizedVoiceRoom=null;currentGame='voice_room_live';render()" class="fixed top-20 left-3 z-40 w-20 h-24 rounded-2xl overflow-hidden border-2 border-purple-400 shadow-2xl cursor-pointer bg-slate-950">
      <img src="${minimizedVoiceRoom.photo || '/api/banner/voice_hub.png'}" class="w-full h-16 object-cover" />
      <div class="bg-purple-900/90 text-[9px] font-black text-center py-1 truncate px-1">🎙️ ${minimizedVoiceRoom.title}</div>
    </div>
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۱. لیست اتاق‌های صوتی و مودال ساخت/ویرایش اتاق (با قفل تعداد مایک بر اساس لول روم تا ۵۰)
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
          <span class="px-2 py-0.5 rounded-full bg-black/65 backdrop-blur-md text-[10px] font-black text-amber-300 border border-amber-400/30">
            Lv.${r.level || 1}/50
          </span>
          ${r.is_locked ? `<span class="w-7 h-7 rounded-full bg-rose-600/90 flex items-center justify-center text-xs shadow">🔒</span>` : `<span class="px-2 py-0.5 rounded-full bg-emerald-500/80 text-[9px] font-black">LIVE</span>`}
        </div>
        <div>
          <div class="font-black text-sm text-white truncate drop-shadow">${r.title}</div>
          <div class="text-[10px] text-slate-300 truncate mb-1.5">${r.description || ''}</div>
          <div class="flex items-center justify-between ltr-grid">
            <span class="pill-mode-pve">${r.mic_count} Mic • ${r.category || 'Friendship'}</span>
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
    ${renderTopBar('🎙️ اتاق‌های صوتی زنده')}

    <div class="flex-1 overflow-y-auto px-3 pb-24">
      <div class="flex justify-between items-center mb-3">
        <span class="text-xs font-black text-slate-300">اتاق‌های صوتی فعال (${rooms.length})</span>
        <button type="button" onclick="vrSheet='edit_room';renderVoiceHub(document.getElementById('app'))" class="btn-primary px-3.5 py-2 rounded-xl text-xs font-black">
          ${me.room ? '⚙️ ویرایش اتاق من' : '➕ ساخت اتاق صوتی'}
        </button>
      </div>

      ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center mb-3">${spMsg}</div>` : ''}
      ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center mb-3">${spErr}</div>` : ''}

      ${me.room ? `
        <div onclick="callSocialApi('join_room',{room_id:${me.room.room_id}})" class="glass-panel p-3 rounded-3xl mb-3 flex items-center justify-between border border-purple-400/40 cursor-pointer">
          <div class="flex items-center gap-3 min-w-0">
            <img src="${me.room.photo || me.photo || '/api/banner/voice_hub.png'}" class="w-12 h-12 rounded-2xl object-cover border border-amber-400" />
            <div class="min-w-0">
              <div class="text-xs font-black text-amber-300 truncate">👑 اتاق شخصی شما: ${me.room.title}</div>
              <div class="text-[10px] text-slate-300">Lv.${me.room.level || 1}/50 • ${me.room.is_locked ? '🔒 قفل‌شده' : '🟢 عمومی'} • ${me.room.mic_count} مایک</div>
            </div>
          </div>
          <span class="btn-success px-3 py-1.5 rounded-xl text-xs font-black shrink-0">ورود ◀</span>
        </div>
      ` : ''}

      <div class="grid grid-cols-2 gap-3">
        ${roomsGridHtml || `<div class="col-span-2 glass-panel p-8 rounded-3xl text-center text-xs text-slate-300">هنوز اتاق صوتی ساخته نشده است! روی «➕ ساخت اتاق صوتی» بزنید.</div>`}
      </div>
    </div>
    ${renderBottomNav()}
  `;
}

function renderEditRoomModal(rm) {
  const me = spState?.me || {};
  const allowedMics = rm?.allowed_mic_list || [1, 2, 6, 8];
  const allMicNums = [1, 2, 6, 8, 10, 12, 15, 17, 20, 24, 30, 36];

  return `
    <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div class="glass-panel p-4 rounded-3xl w-full max-w-sm space-y-2.5 text-xs max-h-[90vh] overflow-y-auto border border-purple-400/40">
        <h3 class="text-sm font-black text-amber-300 text-center">🎙️ تنظیمات اتاق صوتی (Lv.${rm?.level || 1}/50)</h3>
        <div>
          <label class="block text-[11px] text-slate-300 mb-1">نام اتاق صوتی:</label>
          <input id="rm_title" type="text" value="${rm?.title || ('مجلس ' + myName)}" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
        </div>
        <div>
          <label class="block text-[11px] text-slate-300 mb-1">معرفی اتاق (Room Info):</label>
          <input id="rm_desc" type="text" value="${rm?.description || 'به اتاق صوتی خوش آمدید!'}" class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />
        </div>
        <div class="glass-soft p-2.5 rounded-2xl text-center">
          <label class="block text-[11px] text-amber-200 font-bold mb-1">📷 عکس پروفایل اتاق صوتی (آپلود از گالری):</label>
          <input type="file" accept="image/*" onchange="handleImageUpload(this, 'my_room_photo', 'prev_my_room_photo')" class="w-full text-[10px]" />
          <img id="prev_my_room_photo" src="${rm?.photo || ''}" class="${rm?.photo ? '' : 'hidden'} w-20 h-20 rounded-2xl object-cover mx-auto mt-2 border border-amber-400" />
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-[10px] text-slate-300 mb-1">تعداد مایک (بر اساس لول روم):</label>
            <select id="rm_mics" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
              ${allMicNums.map(n => {
                const unlocked = allowedMics.includes(n) || isOwner;
                return `<option value="${n}" ${(rm?.mic_count||8)===n?'selected':''} ${!unlocked?'disabled':''}>${n} Mic ${!unlocked?'🔒':''}</option>`;
              }).join('')}
            </select>
          </div>
          <div>
            <label class="block text-[10px] text-slate-300 mb-1">دسته‌بندی:</label>
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
          <button type="button" onclick="vrSheet='';callSocialApi('save_my_room',{title:document.getElementById('rm_title').value,description:document.getElementById('rm_desc').value,room_photo:window.uploadedImages['my_room_photo']||'',mic_count:Number(document.getElementById('rm_mics').value),category:document.getElementById('rm_cat').value,is_locked:document.getElementById('rm_lock').checked,pin_code:document.getElementById('rm_pin')?.value||''})" class="btn-success py-3 rounded-2xl font-black">💾 ذخیره و ورود</button>
          <button type="button" onclick="vrSheet='';render()" class="btn-danger py-3 rounded-2xl font-bold">انصراف</button>
        </div>
      </div>
    </div>
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۲. داخل اتاق صوتی زنده (پاپ‌آپ صندلی برای مالک/ادمین، خط رابط بدون تداخل چپ و راست، شنوندگان بدون مایک، امواج صوتی و افکت گیفت)
   ═══════════════════════════════════════════════════════════════════════════ */
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

/* وقتی مالک یا ادمین روم روی مایک کلیک می‌کند، مستقیم منتقل نمی‌شود بلکه منوی پاپ‌آپ باز می‌شود */
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

  const bgThemes = {
    lighthouse: "radial-gradient(circle at 50% 20%, #1e1b4b 0%, #090514 85%)",
    royal_stage: "radial-gradient(circle at 50% 15%, #581c87 0%, #1e1b4b 60%, #090514 95%)",
    crimson: "radial-gradient(circle at 50% 20%, #7f1d1d 0%, #111827 90%)",
    emerald: "radial-gradient(circle at 50% 20%, #065f46 0%, #090514 90%)"
  };
  const roomBgCss = bgThemes[r.bg_theme] || bgThemes.lighthouse;

  const mc = r.mic_count || 8;
  const colsCount = mc === 1 ? 1 : (mc === 2 ? 2 : (mc <= 8 ? 4 : (mc <= 15 ? 5 : 6)));
  const gridCols = colsCount === 1 ? 'grid-cols-1 max-w-[110px]' : (colsCount === 2 ? 'grid-cols-2 max-w-[220px]' : (colsCount === 4 ? 'grid-cols-4' : (colsCount === 5 ? 'grid-cols-5' : 'grid-cols-6')));
  const seatSize = mc <= 8 ? 'w-14 h-14 text-lg' : (mc <= 15 ? 'w-12 h-12 text-sm' : 'w-10 h-10 text-xs');

  let seatsHtml = '';
  for (let i = 1; i <= mc; i++) {
    const occ = (r.seats || {})[String(i)];
    const isLockedSeat = (r.locked_seats || []).includes(i);
    const occUid = occ ? Number(occ.uid) : 0;

    /* خط رابط بین دو صندلی مجاور (در چیدمان RTL، صندلی i+1 در سمت چپ صندلی i قرار می‌گیرد)
       هر پل فقط بین i و i+1 کشیده می‌شود، بنابراین اگر سمت راست کاربر رفیقش باشد (i-1 -> i)
       و سمت چپش پارتنرش باشد (i -> i+1)، هر دو پل بدون هیچ تداخلی به طور مستقل نمایش داده می‌شوند! */
    let bondBridgeHtml = '';
    if (occ && (i % colsCount !== 0)) {
      const nextOcc = (r.seats || {})[String(i + 1)];
      if (nextOcc && occ.bonds && occ.bonds[String(nextOcc.uid)]) {
        const relType = occ.bonds[String(nextOcc.uid)];
        const linkMeta = relType === 'marriage'
          ? (occ.marriage_link || { emoji_id: '', icon: '💍', color: '#ec4899' })
          : (occ.bestie_link || { emoji_id: '', icon: '⚡', color: '#06b6d4' });
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
          style="${(!occ?.ring_photo && occ?.ring_css) ? ('box-shadow:' + occ.ring_css + ';') : ''}"
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

  // بخش کاربران بدون مایک (شنوندگان پایین مایک‌ها)
  const listeners = r.unseated_listeners || [];
  const listenersHtml = listeners.map(m => `
    <div onclick="openUserProfileModal(${m.uid})" class="glass-soft px-2 py-1 rounded-full flex items-center gap-1.5 cursor-pointer shrink-0">
      ${window.renderAvatarWithFrame(m.photo, m.name, 'w-5 h-5 text-[8px]', m.ring_photo, m.ring_css)}
      <span class="text-[10px] font-bold text-slate-200 truncate max-w-[65px]">${m.name}</span>
    </div>
  `).join('');

  // افکت تمام‌صفحه گیفت با اوپاسیتی ملایم برای چند ثانیه
  const gfx = r.gift_fx;
  const giftOverlayHtml = gfx ? `
    <div class="fixed inset-0 z-40 pointer-events-none flex flex-col items-center justify-center bg-black/25 backdrop-blur-[2px] animate-pulse">
      <div class="p-6 rounded-3xl bg-purple-950/60 border border-amber-400/50 text-center shadow-2xl" style="opacity: 0.85;">
        <div class="text-6xl mb-2">
          ${gfx.custom_emoji_id ? window.renderTgEmoji(gfx.custom_emoji_id, gfx.icon, 'w-20 h-20 mx-auto') : (gfx.photo ? `<img src="${gfx.photo}" class="w-20 h-20 object-contain mx-auto" />` : gfx.icon)}
        </div>
        <div class="text-sm font-black text-amber-300">🎁 ${gfx.sender} ⬅️ ${gfx.recipients}</div>
        <div class="text-xs font-extrabold text-white mt-1">${gfx.gift_name} (${gfx.coins.toLocaleString()} 🪙)</div>
      </div>
    </div>
  ` : '';

  const membersAvatars = (r.visible_members || []).slice(0, 5).map(m => `
    <div onclick="openUserProfileModal(${m.uid})" title="${m.name}" class="cursor-pointer px-0.5">
      ${window.renderAvatarWithFrame(m.photo, m.name, 'w-7 h-7 text-[10px]', m.ring_photo, m.ring_css)}
    </div>
  `).join('');

  const chatsHtml = (r.chats || []).map(c => c.sys ? `
    <div class="px-3 py-1.5 rounded-2xl ${c.gift ? 'bg-amber-500/25 border border-amber-400/50 text-amber-200' : 'bg-teal-950/60 border border-teal-500/25 text-teal-300'} text-[11px] font-bold">
      ${c.text}
    </div>
  ` : `
    <div class="px-3 py-1.5 rounded-2xl bg-black/45 text-xs">
      <span onclick="openUserProfileModal(${c.uid})" class="font-black text-amber-300 cursor-pointer">
        ${c.badge_emoji_id ? window.renderTgEmoji(c.badge_emoji_id, '', 'w-4 h-4') : ''} ${c.badge ? c.badge + ' ' : ''}${c.name}:
      </span>
      <span class="text-white mr-1">${c.text}</span>
    </div>
  `).join('');

  const imSeated = Object.values(r.seats || {}).some(s => s && Number(s.uid) === Number(uid));

  let modalSheetHtml = '';
  if (vrSheet === 'exit_confirm') {
    modalSheetHtml = `
      <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center gap-10">
        <div class="flex flex-col items-center gap-2">
          <button type="button" onclick="event.stopPropagation();vrKeepMinimized()" class="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-3xl shadow-[0_0_25px_#10b981]">🗗</button>
          <span class="font-black text-sm">Keep</span>
        </div>
        <div class="flex flex-col items-center gap-2">
          <button type="button" onclick="event.stopPropagation();callSocialApi('room_op',{room_id:${r.room_id},op:'leave_room'})" class="w-20 h-20 rounded-full bg-gradient-to-br from-rose-500 to-red-600 flex items-center justify-center text-3xl shadow-[0_0_25px_#f43f5e]">⏻</button>
          <span class="font-black text-sm">Exit</span>
        </div>
      </div>
    `;
  } else if (vrSheet === 'seat_menu') {
    const sIdx = selectedSeatIdx;
    const isLocked = (r.locked_seats || []).includes(sIdx);
    const occ = (r.seats || {})[String(sIdx)];
    modalSheetHtml = `
      <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
        <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-2.5 text-xs border-t border-purple-400">
          <h3 class="font-black text-sm text-amber-300 text-center">🎙️ گزینه‌های میکروفون شماره ${sIdx}</h3>
          <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'take_seat',seat_idx:'${sIdx}'})" class="btn-success w-full py-3 rounded-2xl font-black">
            🪑 انتقال به این میکروفون (نشستن)
          </button>
          <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_seat_lock',seat_idx:${sIdx}})" class="btn-primary w-full py-3 rounded-2xl font-black">
            ${isLocked ? '🔓 باز کردن قفل این میکروفون' : '🔒 قفل کردن این میکروفون'}
          </button>
          ${occ ? `
            <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'kick_from_seat',seat_idx:'${sIdx}'})" class="btn-danger w-full py-3 rounded-2xl font-black">
              ⬇️ پایین آوردن ${occ.name} از روی مایک
            </button>
          ` : ''}
          <div class="pt-2 border-t border-white/10">
            <div class="text-[11px] text-slate-300 font-bold mb-1.5 text-center">📩 دعوت کاربر بدون مایک به این صندلی:</div>
            <div class="flex gap-1.5 overflow-x-auto pb-1">
              ${listeners.map(u => `
                <button type="button" onclick="vrSheet='';callSocialApi('room_op',{room_id:${r.room_id},op:'invite_to_seat',seat_idx:'${sIdx}',target_uid:${u.uid}})" class="glass-soft px-3 py-1.5 rounded-xl font-bold shrink-0">
                  ➕ دعوت ${u.name}
                </button>
              `).join('') || '<span class="text-slate-400 text-[10px] mx-auto">همه اعضای حاضر روی مایک هستند</span>'}
            </div>
          </div>
        </div>
      </div>
    `;
  } else if (vrSheet === 'manage') {
    const allowedMics = r.allowed_mic_list || [1, 2, 6, 8];
    const allMics = [1, 2, 6, 8, 10, 12, 15, 17, 20, 24, 30, 36];
    modalSheetHtml = `
      <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
        <div onclick="event.stopPropagation()" class="glass-panel rounded-t-3xl p-4 space-y-3 border-t border-purple-400/40 text-xs max-h-[82vh] overflow-y-auto">
          <div class="flex justify-between items-center border-b border-white/10 pb-2 font-black">
            <span class="text-amber-300">🎛️ مدیریت اتاق (Lv.${r.level}/50 — سقف مجاز: ${r.max_allowed_mics} مایک)</span>
            <button type="button" onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="text-slate-400">✖</button>
          </div>

          <div>
            <div class="text-[11px] font-bold text-slate-300 mb-1.5">🎙️ تغییر تعداد میکروفون‌ها (با افزایش لول روم مایک‌های بیشتر باز می‌شوند):</div>
            <div class="grid grid-cols-4 gap-1.5 text-center font-black">
              ${allMics.map(n => {
                const ok = allowedMics.includes(n) || isOwner;
                return `
                  <button type="button" ${!ok ? 'disabled' : ''} onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'change_layout',mic_count:${n}});vrSheet=''"
                    class="py-2 rounded-xl ${r.mic_count===n ? 'btn-primary' : (ok ? 'glass-soft' : 'bg-slate-900/50 opacity-40')}">
                    ${n} Mic ${!ok ? '🔒' : ''}
                  </button>
                `;
              }).join('')}
            </div>
          </div>

          <div class="grid grid-cols-4 gap-2 text-center text-[11px] font-bold pt-2 border-t border-white/10">
            <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_lock_room'});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1"><span class="text-lg">${r.is_locked ? '🔓' : '🔒'}</span><span>${r.is_locked ? 'Unlock' : 'Lock'}</span></button>
            <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_auto_lock_mics'});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1"><span class="text-lg">💺</span><span>Mic Lock</span></button>
            <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'clear_chat'});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1"><span class="text-lg">🧹</span><span>Clear Chat</span></button>
            <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'toggle_pk'});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1"><span class="text-lg">⚔️</span><span>PK Battle</span></button>
          </div>

          ${isRoomOwner ? `
            <div class="pt-2 border-t border-white/10 space-y-1.5">
              <div class="font-black text-indigo-300 text-center">🛡️ تعیین یا عزل ادمین‌های اتاق (روی نام کاربر بزنید):</div>
              <div class="flex gap-1.5 flex-wrap justify-center">
                ${(r.visible_members || []).filter(m => Number(m.uid) !== Number(r.owner_id)).map(m => {
                  const isAdm = (r.admins_list || []).includes(Number(m.uid));
                  return `
                    <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'set_room_admin',target_uid:${m.uid}})"
                      class="px-3 py-1.5 rounded-xl font-bold ${isAdm ? 'btn-success' : 'glass-soft'}">
                      ${isAdm ? '🛡️ ادمین: ' : '➕ ادمین کردن: '}${m.name}
                    </button>
                  `;
                }).join('') || '<span class="text-slate-400 text-[10px]">کاربر دیگری در اتاق حضور ندارد</span>'}
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  } else if (vrSheet === 'details') {
    modalSheetHtml = `
      <div onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))" class="fixed inset-0 z-50 bg-black/70 flex flex-col justify-end">
        <div onclick="event.stopPropagation()" class="bg-white text-slate-900 rounded-t-3xl p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          <div class="flex justify-between items-center">
            <h3 class="font-black text-base">Room Details</h3>
            <button type="button" onclick="openUserProfileModal(${r.owner_id})" class="text-xs font-bold text-purple-700">👤 مشاهده پروفایل مالک اتاق</button>
          </div>
          <div class="flex items-center justify-between bg-slate-100 p-3 rounded-2xl">
            <div class="flex items-center gap-3">
              <img src="${r.photo || '/api/banner/voice_hub.png'}" class="w-14 h-14 rounded-2xl object-cover" />
              <div>
                <div class="font-black text-sm">👑 ${r.title}</div>
                <div class="text-xs text-slate-500">ID: ${r.room_id} • مجموع گیفت: ${(r.total_gifts||0).toLocaleString()} 🪙</div>
              </div>
            </div>
            <span class="px-3 py-1 rounded-xl bg-amber-400 text-black font-black text-xs">Lv.${r.level || 1}/50</span>
          </div>
          <div class="bg-slate-100 p-3 rounded-2xl">
            <div class="font-black text-xs mb-2">Room Members (${r.online_count || 1})</div>
            <div class="flex gap-2 flex-wrap">
              ${(r.visible_members || []).map(m => `
                <div onclick="openUserProfileModal(${m.uid})" class="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-full text-xs font-bold shadow-sm cursor-pointer">
                  ${window.renderAvatarWithFrame(m.photo, m.name, 'w-5 h-5 text-[8px]', m.ring_photo, m.ring_css)}
                  <span>${m.name}</span><span class="text-[10px] text-purple-600">${m.badge||''}</span>
                </div>
              `).join('')}
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
            <span class="text-amber-300">🎁 ارسال هدیه به اشخاص مشخص (موجودی: ${(me.coins||0).toLocaleString()} 🪙)</span>
            <button type="button" onclick="vrSheet='';drawLiveVoiceRoom(document.getElementById('app'))">✖</button>
          </div>
          <div>
            <div class="text-[10px] text-slate-300 mb-1">گیرنده یا گیرندگان گیفت را انتخاب کنید:</div>
            <div class="flex gap-1.5 overflow-x-auto pb-1">
              ${allInRoom.map(m => {
                const sel = selectedGiftRecs.includes(Number(m.uid));
                return `
                  <button type="button" onclick="window.toggleGiftRecSelection(${m.uid})"
                    class="px-2.5 py-1.5 rounded-xl font-bold shrink-0 border ${sel ? 'btn-success border-white' : 'glass-soft border-white/10'}">
                    ${sel ? '✅ ' : '👤 '}${m.name}
                  </button>
                `;
              }).join('')}
            </div>
          </div>
          <div class="grid grid-cols-4 gap-2 text-center">
            ${gifts.map(g => `
              <button type="button" onclick="callSocialApi('room_op',{room_id:${r.room_id},op:'send_gift',gift_id:${g.id},recipient_uids:selectedGiftRecs});vrSheet=''" class="glass-soft p-2.5 rounded-2xl flex flex-col items-center gap-1 hover:border-amber-400">
                <div class="text-2xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-9 h-9 mx-auto') : (g.photo ? `<img src="${g.photo}" class="w-9 h-9 object-contain mx-auto" />` : g.icon)}</div>
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
    ${giftOverlayHtml}
    ${modalSheetHtml}
    <div style="background: ${roomBgCss};" class="flex-1 flex flex-col justify-between p-3 overflow-hidden relative">
      <div class="flex items-center justify-between gap-2 shrink-0">
        <div onclick="vrSheet='details';drawLiveVoiceRoom(document.getElementById('app'))" class="glass-panel px-2.5 py-1.5 rounded-2xl flex items-center gap-2 cursor-pointer">
          <img src="${r.photo || '/api/banner/voice_hub.png'}" class="w-9 h-9 rounded-xl object-cover border border-amber-400" />
          <div class="leading-tight">
            <div class="font-black text-xs text-amber-200 flex items-center gap-1">
              <span>👑 ${r.title}</span>
              ${r.is_locked ? '<span>🔒</span>' : ''}
            </div>
            <div class="text-[10px] text-emerald-300 font-bold">Lv.${r.level || 1}/50 (${r.level_pct || 0}%) • 🪙 ${(r.total_gifts || 0).toLocaleString()}</div>
          </div>
        </div>

        <div class="flex items-center gap-1.5">
          <div class="flex items-center gap-0.5">${membersAvatars}</div>
          <span class="px-2 py-1 rounded-xl glass-soft text-[11px] font-black">👥 ${r.online_count || 1}</span>
          <button type="button" onclick="vrOpenExitPrompt()" class="w-8 h-8 rounded-full glass-panel flex items-center justify-center text-sm font-black">⏻</button>
        </div>
      </div>

      ${r.pk_active ? `
        <div class="glass-panel p-2 rounded-2xl flex items-center justify-between text-xs font-black border border-rose-500/50 my-1 shrink-0">
          <span class="text-sky-400">🔵 TEAM A: ${r.pk_score_a}</span>
          <span class="px-2 py-0.5 rounded bg-rose-600 text-[10px]">PK VS</span>
          <span class="text-rose-400">🔴 TEAM B: ${r.pk_score_b}</span>
        </div>
      ` : ''}

      <!-- صندلی‌های میکروفون + خطوط رابط ازدواج و رفاقت -->
      <div class="my-auto py-2 overflow-y-auto max-h-[42vh] flex justify-center">
        <div class="grid ${gridCols} gap-3.5 justify-items-center w-full">
          ${seatsHtml}
        </div>
      </div>

      <!-- بخش کاربران بدون مایک (شنوندگان پایین مایک‌ها) -->
      <div class="glass-panel px-3 py-1.5 rounded-2xl mb-1.5 shrink-0">
        <div class="text-[9px] font-black text-slate-400 mb-1">🎧 حاضرین بدون مایک (${listeners.length} نفر):</div>
        <div class="flex gap-1.5 overflow-x-auto pb-0.5">
          ${listenersHtml || '<span class="text-[10px] text-slate-500">همه اعضای حاضر روی مایک هستند</span>'}
        </div>
      </div>

      <!-- چت زنده اتاق -->
      <div class="flex flex-col gap-1 max-h-[20vh] overflow-y-auto mb-1.5 pr-1">
        ${chatsHtml}
      </div>

      <!-- نوار ابزار پایین اتاق -->
      <div class="flex items-center gap-1.5 shrink-0 pt-1">
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

/* پلی‌لیست اختصاصی موزیک کاربر و پخش فایل‌های ارسالی به ربات */
let userMusicPlaylist = [];

async function loadUserPlaylist() {
  try {
    const res = await fetch('/api/social/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: Number(uid), action: 'get_my_playlist' })
    });
    const data = await res.json();
    if (data.playlist) userMusicPlaylist = data.playlist;
  } catch (e) {}
}

window.playUserMusicTrack = async function(fileId) {
  try {
    const tempBotToken = "__BOT_TOKEN_PLACEHOLDER__"; // یا دریافت مستقیم از فایل سرویس
    // پخش فایل صوتی از طریق Telegram File API یا تگ صوتی HTML5
    const audioEl = document.getElementById('roomAudioPlayer');
    if (audioEl) {
      audioEl.src = `/api/get_tg_file/${fileId}`;
      audioEl.play();
    }
  } catch (e) {
    alert('امکان پخش این موزیک وجود ندارد.');
  }
};

/* موتور WebRTC مایک‌های اتاق صوتی برای انتقال واقعی صدا */
let localRoomStream = null;
let roomPeerConnections = {};

async function initRoomVoiceWebRTC(isMicActive) {
  if (isMicActive) {
    try {
      localRoomStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      // ارسال استریم صوتی به سایر حاضرین روی مایک از طریق سیگنالینگ سکتور صوتی
    } catch (e) {
      alert('دسترسی به میکروفون مسدود است!');
    }
  } else {
    if (localRoomStream) {
      localRoomStream.getTracks().forEach(t => t.stop());
      localRoomStream = null;
    }
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۳. چت خصوصی (PV) داخل مینی‌اپ با ضبط ویس، بک‌گراند سفارشی، پک ایموجی پریمیوم و لول ارتباط
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
      <span>💌 درخواست <b>${p.pending_type === 'marriage' ? 'ازدواج 💍' : 'رفاقت ⚡'}</b> از طرف <b>${p.partner_name}</b></span>
      ${Number(p.requested_by) !== Number(uid) ? `
        <div class="flex gap-1.5">
          <button type="button" onclick="callSocialApi('rel_op',{op:'respond',target_uid:${p.partner_uid},accept:true})" class="btn-success px-3 py-1 rounded-xl font-black">قبول</button>
          <button type="button" onclick="callSocialApi('rel_op',{op:'respond',target_uid:${p.partner_uid},accept:false})" class="btn-danger px-3 py-1 rounded-xl font-bold">رد</button>
        </div>
      ` : `<span class="text-amber-300 font-bold">در انتظار تایید...</span>`}
    </div>
  `).join('');

  root.innerHTML = `
    ${renderTopBar('💬 چت خصوصی و درخواست‌های رابطه')}
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
            <span class="btn-primary px-3 py-1.5 rounded-xl font-black">ورود به چت ◀</span>
          </div>
        `).join('') || '<div class="glass-panel p-6 rounded-3xl text-center text-slate-400">هنوز گفتگویی ندارید! روی پروفایل هر کاربر در اتاق صوتی بزنید تا چت خصوصی باز شود.</div>'}
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

    <div class="mx-3 mt-1.5 flex items-center justify-between gap-2 text-[10px]">
      <div class="flex items-center gap-1">
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

  const visitorsHtml = isMe ? (p.visitors_log || []).map(v => `
    <div onclick="openUserProfileModal(${v.uid})" class="glass-soft p-2.5 rounded-xl flex items-center justify-between text-xs cursor-pointer">
      <div class="flex items-center gap-2.5">
        ${window.renderAvatarWithFrame(v.photo, v.name, 'w-9 h-9 text-xs', v.ring_photo, v.ring_css)}
        <span class="font-bold">${v.name} <b class="text-amber-300">${v.badge||''}</b></span>
      </div>
      <span class="text-[10px] text-slate-400">${v.time}</span>
    </div>
  `).join('') : '';

  root.innerHTML = `
    ${renderTopBar('👤 پروفایل کاربری')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3 text-xs">
      ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 font-bold text-center">${spMsg}</div>` : ''}
      ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 font-bold text-center">${spErr}</div>` : ''}

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
        <div class="text-[11px] text-white/80 font-mono mb-2">
          ID: ${p.user_id} ${p.username ? ('• @' + p.username) : ''} ${p.ring_name ? ('• ⭕ ' + p.ring_name) : ''}
        </div>
        <p class="text-xs text-white/95 bg-black/30 p-2.5 rounded-2xl max-w-xs mx-auto mb-3">${p.bio}</p>

        <!-- لول ثروت (Wealth) و لول جذابیت (Charm) تا ۵۰ -->
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
            <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${p.user_id},rel_type:'marriage'})" class="btn-danger py-2.5 rounded-xl font-black">💍 ازدواج (5K)</button>
            <button type="button" onclick="callSocialApi('rel_op',{op:'propose',target_uid:${p.user_id},rel_type:'bestie'})" class="btn-success py-2.5 rounded-xl font-black">⚡ رفاقت (2K)</button>
          </div>
        ` : ''}
      </div>

      <!-- کارت‌های روابط کاربر (۱ ازدواج + تا ۵ رفیق صمیمی) -->
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

      <!-- اتاق صوتی کاربر در پروفایل -->
      <div class="glass-panel p-4 rounded-3xl">
        <h4 class="text-xs font-black text-amber-300 mb-2">🎙️ اتاق صوتی اختصاصی ${isMe ? 'شما' : p.display_name}</h4>
        ${p.room ? `
          <div onclick="callSocialApi('join_room',{room_id:${p.room.room_id}})" class="glass-soft p-3 rounded-2xl flex items-center justify-between cursor-pointer border border-purple-400/40">
            <div class="flex items-center gap-3 min-w-0">
              <img src="${p.room.photo || p.photo || '/api/banner/voice_hub.png'}" class="w-12 h-12 rounded-2xl object-cover" />
              <div class="min-w-0">
                <div class="font-black text-xs text-white truncate">${p.room.title} ${p.room.is_locked ? '🔒' : '🟢'}</div>
                <div class="text-[10px] text-emerald-300 font-bold">👥 ${p.room.online_count || 1} نفر داخل اتاق • Lv.${p.room.level || 1}/50</div>
              </div>
            </div>
            <button type="button" class="btn-success px-3 py-2 rounded-xl text-xs font-black shrink-0">ورود ◀</button>
          </div>
        ` : `
          <div class="text-center text-xs text-slate-400 py-2">
            ${isMe ? `<button type="button" onclick="openMyVoiceRoomQuick()" class="btn-primary px-4 py-2.5 rounded-xl font-black">➕ ساخت اتاق صوتی شخصی</button>` : 'این کاربر هنوز اتاق صوتی نساخته است.'}
          </div>
        `}
      </div>

      ${isMe ? `
        <!-- انتخاب گیفت‌های دریافتی برای شناور شدن روی کارت پروفایل با هاله نئون -->
        <div class="glass-panel p-4 rounded-3xl space-y-2">
          <h4 class="font-black text-pink-300 text-center">✨ انتخاب گیفت‌های دریافتی برای شناور شدن روی کارت پروفایل (حداکثر ۶ عدد)</h4>
          <div class="grid grid-cols-4 gap-2">
            ${(p.received_gifts_inv || []).map(g => {
              const active = (p.showcased_gifts || []).map(Number).includes(Number(g.id));
              return `
                <button type="button" onclick="window.toggleShowcaseGift(${g.id})" class="p-2 rounded-2xl border ${active ? 'border-pink-400 bg-pink-950/60' : 'border-white/10 glass-soft'} flex flex-col items-center gap-1">
                  <div class="text-2xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-7 h-7') : (g.photo ? `<img src="${g.photo}" class="w-7 h-7 object-contain" />` : g.icon)}</div>
                  <span class="text-[9px] font-bold truncate w-full">${g.name} (x${g.count})</span>
                </button>
              `;
            }).join('') || '<div class="col-span-4 text-center text-slate-400 py-2">هنوز گیفتی دریافت نکرده‌اید.</div>'}
          </div>
        </div>

        <!-- ست کردن ایموجی پریمیوم جلوی اسم + رنگ‌های کارت پروفایل -->
        <div class="glass-panel p-4 rounded-3xl space-y-3">
          <h4 class="font-black text-amber-300 text-center">🌟 ست کردن ایموجی پریمیوم متحرک جلوی نام (ویژه مشترکین VIP)</h4>
          <div class="flex gap-2">
            <input id="sp_badge_eid" type="text" value="${p.custom_badge_emoji_id || ''}" placeholder="آیدی ایموجی پریمیوم تلگرام..." class="flex-1 p-2.5 rounded-xl glass-soft text-center text-white ltr-grid" />
            <button type="button" onclick="callSocialApi('arm_user_badge_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary px-3 rounded-xl font-black">📩 ارسال به ربات</button>
          </div>

          <h4 class="font-black text-sm text-indigo-300 text-center pt-2">🎨 رنگ‌ها و تم‌های کارت پروفایل (شامل تم‌های خاص ULTRA)</h4>
          <div class="grid grid-cols-2 gap-2">
            ${themes.map(t => `
              <button type="button" onclick="callSocialApi('save_profile',{card_theme:'${t.id}'})" style="background:${t.css}" class="px-2.5 py-2 rounded-xl text-[10px] font-black border ${p.card_theme===t.id ? 'border-white scale-105' : 'border-white/20 opacity-80'} flex items-center justify-between gap-1">
                <span>${t.title}</span>
                ${t.tier !== 'free' ? `<span class="px-1 rounded bg-black/50 text-amber-300 text-[8px]">${t.tier.toUpperCase()}</span>` : ''}
              </button>
            `).join('')}
          </div>

          <div class="border-t border-white/10 pt-3 space-y-2">
            <input id="sp_name_inp" type="text" value="${p.display_name}" class="w-full p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
            <input id="sp_bio_inp" type="text" value="${p.bio}" class="w-full p-2.5 rounded-xl glass-soft text-white text-center" />

            <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center">
              <span>🕵️ بازدید مخفی پروفایل دیگران (PLUS+):</span>
              <input id="sp_stealth_chk" type="checkbox" ${p.stealth_mode ? 'checked' : ''} ${!p.can_stealth_visit ? 'disabled' : ''} class="w-4 h-4" />
            </div>
            <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center">
              <span>👻 ورود روح به اتاق‌های صوتی باز (ULTRA):</span>
              <input id="sp_ghost_chk" type="checkbox" ${p.ghost_mode ? 'checked' : ''} ${!p.can_ghost_join ? 'disabled' : ''} class="w-4 h-4" />
            </div>

            <button type="button" onclick="callSocialApi('save_profile',{display_name:document.getElementById('sp_name_inp').value,bio:document.getElementById('sp_bio_inp').value,card_theme:'${p.card_theme}',custom_badge_emoji_id:document.getElementById('sp_badge_eid').value,stealth_mode:document.getElementById('sp_stealth_chk').checked,ghost_mode:document.getElementById('sp_ghost_chk').checked})" class="btn-success w-full py-3 rounded-2xl font-black">
              💾 ذخیره تغییرات پروفایل
            </button>
          </div>
        </div>

        <div class="glass-panel p-4 rounded-3xl space-y-2">
          <h4 class="font-black text-amber-300 text-center">👁️ آخرین بازدیدکنندگان پروفایل شما</h4>
          <div class="flex flex-col gap-1.5">${visitorsHtml || '<div class="text-center text-slate-400">هنوز کسی از پروفایل شما بازدید نکرده است.</div>'}</div>
        </div>
      ` : `
        <button type="button" onclick="viewedProfileData=null;renderSpProfile(document.getElementById('app'))" class="btn-primary w-full py-3 rounded-2xl font-black text-xs">🔙 بازگشت به پروفایل خودم</button>
      `}
    </div>
    ${renderBottomNav()}
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۵. فروشگاه جامع (اشتراک‌ها، کاورهای PNG دور پروفایل، خط رابط ازدواج/رفاقت و گیفت‌های متحرک)
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
    contentHtml = subs.map(s => {
      const isCurrent = me.sub_tier === s.id;
      return `
        <div class="glass-panel p-4 rounded-3xl space-y-2.5 border ${isCurrent ? 'border-emerald-400 ring-2 ring-emerald-400/30' : (s.id==='ultra' ? 'border-pink-400' : 'border-purple-400/40')}">
          <div class="flex justify-between items-center">
            <span class="text-base font-black text-white">${s.title}</span>
            <span class="px-2.5 py-1 rounded-full bg-white/10 text-amber-300 text-xs font-black">${s.badge}</span>
          </div>
          <ul class="text-xs text-slate-200 space-y-1 pr-2">
            ${s.perks.map(pk => `<li>✅ ${pk}</li>`).join('')}
          </ul>
          <div class="grid grid-cols-2 gap-2 pt-2">
            <button type="button" onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'coins'})" class="btn-success py-3 rounded-xl font-black text-xs">
              🪙 خرید با ${s.coins.toLocaleString()} سکه
            </button>
            <button type="button" onclick="callSocialApi('buy_subscription',{tier_id:'${s.id}',pay_method:'direct_stars'})" class="btn-primary py-3 rounded-xl font-black text-xs">
              ⭐ خرید با ${s.stars} استارز
            </button>
          </div>
        </div>
      `;
    }).join('');
  } else if (storeTab === 'rings') {
    contentHtml = `
      ${me.avatar_ring_id ? `<button type="button" onclick="callSocialApi('buy_or_equip_ring',{ring_id:0})" class="btn-danger w-full py-2.5 rounded-2xl text-xs font-black mb-2">❌ برداشتن کاور فعلی از دور آواتار</button>` : ''}
    ` + rings.map(r => {
      const owned = (me.owned_rings || []).includes(Number(r.id));
      const equipped = Number(me.avatar_ring_id) === Number(r.id);
      const btnText = equipped ? 'فعال ✓' : (owned ? 'پوشیدن' : ('خرید (' + r.price_coins + ' 🪙)'));
      return `
        <div class="glass-panel p-3.5 rounded-3xl flex items-center justify-between gap-3 border ${equipped ? 'border-emerald-400' : 'border-white/10'}">
          <div class="flex items-center gap-3.5">
            <div class="p-1">
              ${window.renderAvatarWithFrame(me.photo || myPhoto, me.display_name || myName, 'w-14 h-14 text-lg', r.photo, r.ring_css)}
            </div>
            <div>
              <div class="font-black text-xs text-white">${r.name}</div>
              <div class="text-[11px] text-amber-300 font-bold">${r.price_coins.toLocaleString()} 🪙</div>
            </div>
          </div>
          <button type="button" onclick="callSocialApi('buy_or_equip_ring',{ring_id:${r.id}})" class="${equipped ? 'btn-success' : (owned ? 'btn-primary' : 'btn-danger')} px-4 py-2.5 rounded-xl text-xs font-black shrink-0">
            ${btnText}
          </button>
        </div>
      `;
    }).join('');
  } else if (storeTab === 'links') {
    contentHtml = relLinks.map(r => {
      const owned = (me.owned_rel_links || []).includes(Number(r.id));
      const equipped = Number(me.active_marriage_link_id) === Number(r.id) || Number(me.active_bestie_link_id) === Number(r.id);
      return `
        <div class="glass-panel p-3.5 rounded-3xl flex items-center justify-between gap-3 border ${equipped ? 'border-pink-400' : 'border-white/10'}">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-2xl glass-soft flex items-center justify-center text-2xl">
              ${r.custom_emoji_id ? window.renderTgEmoji(r.custom_emoji_id, r.icon, 'w-8 h-8') : r.icon}
            </div>
            <div>
              <div class="font-black text-xs text-white">${r.name}</div>
              <div class="text-[10px] text-amber-300 font-bold">${r.price_coins.toLocaleString()} 🪙</div>
            </div>
          </div>
          <button type="button" onclick="callSocialApi('buy_or_equip_ring',{ring_id:${r.id}})" class="${equipped ? 'btn-success' : (owned ? 'btn-primary' : 'btn-danger')} px-4 py-2 rounded-xl text-xs font-black">
            ${equipped ? 'فعال ✓' : (owned ? 'استفاده' : 'خرید')}
          </button>
        </div>
      `;
    }).join('');
  } else {
    contentHtml = `<div class="grid grid-cols-2 gap-2.5">` + gifts.map(g => `
      <div class="glass-panel p-3.5 rounded-3xl text-center space-y-1.5">
        <div class="text-4xl">${g.custom_emoji_id ? window.renderTgEmoji(g.custom_emoji_id, g.icon, 'w-12 h-12 mx-auto') : (g.photo ? `<img src="${g.photo}" class="w-12 h-12 object-contain mx-auto" />` : g.icon)}</div>
        <div class="font-black text-xs text-white">${g.name}</div>
        <div class="text-xs text-amber-300 font-extrabold">${g.price_coins.toLocaleString()} 🪙</div>
        <div class="text-[10px] text-slate-400">قابل ارسال به اشخاص در اتاق صوتی</div>
      </div>
    `).join('') + `</div>`;
  }

  root.innerHTML = `
    ${renderTopBar('🛍️ فروشگاه VIP و کاور پروفایل')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 space-y-3">
      <div class="glass-panel p-3 rounded-2xl flex justify-between items-center text-xs font-black">
        <span>موجودی: <b class="text-amber-300">🪙 ${(me.coins||0).toLocaleString()}</b> | <b class="text-purple-300">⭐ ${me.stars_balance||0}</b></span>
        <span>اشتراک: <b class="text-emerald-300 uppercase">${me.sub_tier} ${me.sub_badge||''}</b></span>
      </div>

      <div class="grid grid-cols-4 gap-1.5 text-[11px] font-black">
        <button type="button" onclick="storeTab='subs';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='subs' ? 'btn-primary' : 'glass-soft'}">💎 اشتراک</button>
        <button type="button" onclick="storeTab='rings';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='rings' ? 'btn-primary' : 'glass-soft'}">⭕ کاورها</button>
        <button type="button" onclick="storeTab='links';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='links' ? 'btn-primary' : 'glass-soft'}">🔗 خط رابط</button>
        <button type="button" onclick="storeTab='gifts';renderSpStore(document.getElementById('app'))" class="py-2.5 rounded-xl ${storeTab==='gifts' ? 'btn-primary' : 'glass-soft'}">🎁 گیفت‌ها</button>
      </div>

      ${spMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-bold text-center">${spMsg}</div>` : ''}
      ${spErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-bold text-center">${spErr}</div>` : ''}

      <div class="space-y-3">${contentHtml}</div>
    </div>
    ${renderBottomNav()}
  `;
}
"""
