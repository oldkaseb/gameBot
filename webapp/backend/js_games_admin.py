# -*- coding: utf-8 -*-
"""webapp/backend/js_games_admin.py — بخش ۴ از ۴: پنل مدیریت کل پلتفرم + موتور کامل بازی‌های کلاسیک و روتر اصلی"""

JS_GAMES_ADMIN = r"""
/* ═══════════════════════════════════════════════════════════════════════════
   ۱. پنل مدیریت کل پلتفرم راینو (همگام‌سازی آنی فروشگاه، ایموجی پریمیوم و دکمه ریست کل)
   ═══════════════════════════════════════════════════════════════════════════ */
let admState = null;
let admTab = 'store_mgr';
let admMsg = '';
let admErr = '';
let admLookedUpUser = null;

async function callTowerAdminApi(action = 'state', extra = {}) {
  try {
    const res = await fetch('/api/tower/admin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ uid: Number(uid), action: action, ...extra })
    });
    if (!res.ok) {
      const errTxt = await res.text();
      admErr = 'خطای سرور (' + res.status + '): ' + errTxt.slice(0, 120);
      if (!admState) admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
      drawTowerAdminApp(document.getElementById('app'));
      return;
    }
    const data = await res.json();
    admMsg = data.msg || '';
    admErr = data.ok === false ? (data.error || '') : '';
    if (data.looked_up) admLookedUpUser = data.looked_up;
    if (data.state) {
      spState = data.state; // همگام‌سازی فوری کاورها و آیتم‌های جدید با فروشگاه کاربران
    }
    if (data.admin_data) {
      admState = data.admin_data;
      if (admState.ui_assets) {
        window.uiAssetsMap = admState.ui_assets;
        applyDynamicCssBackgrounds();
      }
    }
    if (!admState) admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
    drawTowerAdminApp(document.getElementById('app'));
  } catch (e) {
    admErr = 'خطا در ارتباط با سرور: ' + (e.message || e);
    if (!admState) admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
    drawTowerAdminApp(document.getElementById('app'));
  }
}

window.admSwitchTab = function(t) {
  admTab = t;
  admMsg = '';
  admErr = '';
  currentGame = 'tower_admin';
  if (!admState) {
    admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
  }
  drawTowerAdminApp(document.getElementById('app'));
};

window.admSaveUiAsset = function(assetKey) {
  const dataUrl = window.uploadedImages['asset_' + assetKey];
  if (!dataUrl) {
    if (tg?.showAlert) tg.showAlert('ابتدا یک تصویر از گالری انتخاب کنید!');
    return;
  }
  callTowerAdminApi('save_ui_asset', { asset_key: assetKey, photo: dataUrl });
};

window.admDeleteUiAsset = function(assetKey) {
  callTowerAdminApi('delete_ui_asset', { asset_key: assetKey });
};

function startTowerAdminApp(root) {
  if (!isOwner) {
    root.innerHTML = `<div class="p-8 text-center"><div class="glass-panel p-6 rounded-3xl text-rose-400 font-black">⛔ دسترسی غیرمجاز (UID: ${uid})</div></div>`;
    return;
  }
  if (!admState) {
    admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
  }
  drawTowerAdminApp(root);
  callTowerAdminApi('state');
}

function drawTowerAdminApp(root) {
  if (!root) root = document.getElementById('app');
  if (!root) return;
  currentGame = 'tower_admin';
  if (!admState) {
    admState = { bot_stats: {}, ui_assets: {}, users_list: [], store_items: [], forced_channels: [], groups_list: [] };
  }

  const tabs = [
    { id: 'store_mgr',    lbl: '🛍️ کاور و گیفت' },
    { id: 'ui_assets',    lbl: '🖼️ عکس بازی‌ها' },
    { id: 'bot_stats',    lbl: '📊 آمار و همگانی' },
    { id: 'users',        lbl: '👤 کاربران و شارژ' },
    { id: 'bot_channels', lbl: '🔒 قفل کانال' },
    { id: 'bot_groups',   lbl: '👥 گروه‌ها' }
  ];

  const tabsHtml = tabs.map(t => `
    <button type="button" onclick="window.admSwitchTab('${t.id}')" class="py-2.5 px-2 rounded-xl text-[11px] font-black transition active:scale-95 ${admTab === t.id ? 'btn-primary text-white ring-2 ring-purple-300/50' : 'glass-soft text-slate-300'}">
      ${t.lbl}
    </button>
  `).join('');

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
          <label class="block text-[11px] text-amber-300 font-black">۱. آپلود فایل PNG توخالی (برای کاور پروفایل یا گیفت تصویری):</label>
          <input type="file" accept="image/png,image/webp,image/*" onchange="handleImageUpload(this, 'store_item_photo', 'prev_store_item_photo')" class="w-full text-[10px] text-slate-300" />
          <div class="relative w-16 h-16 mx-auto mt-2 flex items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold border border-white/20">👤</div>
            <img id="prev_store_item_photo" class="hidden absolute inset-0 w-full h-full object-contain pointer-events-none" style="transform: scale(1.28);" />
          </div>
        </div>

        <div class="glass-soft p-3 rounded-2xl space-y-2 border border-emerald-400/40">
          <label class="block text-[11px] text-emerald-300 font-black">۲. یا ایموجی پریمیوم متحرک تلگرام (برای گیفت / خط رابط):</label>
          <div class="flex gap-2">
            <input id="st_eid" type="text" value="${capId}" placeholder="آیدی ۱۹ رقمی ایموجی پریمیوم..." class="flex-1 p-2 rounded-xl bg-slate-900 text-white text-center ltr-grid" />
            <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'gift'});setTimeout(()=>tg?.close?.(),700)" class="btn-primary px-3 rounded-xl font-black">📩 ارسال به ربات</button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <input id="st_icon" type="text" value="${capIco}" placeholder="ایموجی جایگزین" class="p-2.5 rounded-xl glass-soft text-white text-center" />
          <input id="st_coins" type="number" value="2000" placeholder="قیمت به سکه" class="p-2.5 rounded-xl glass-soft text-white font-bold text-center" />
        </div>
        <input id="st_css" type="text" placeholder="کد رنگ خط رابط یا سایه CSS (اختیاری)" class="w-full p-2.5 rounded-xl glass-soft text-white text-center ltr-grid text-[10px]" />
        <button type="button" onclick="callTowerAdminApi('save_store_item',{category:document.getElementById('st_cat').value,name:document.getElementById('st_name').value,icon:document.getElementById('st_icon').value,custom_emoji_id:document.getElementById('st_eid').value,photo:window.uploadedImages['store_item_photo']||'',price_coins:Number(document.getElementById('st_coins').value||1500),ring_css:document.getElementById('st_css').value});window.uploadedImages['store_item_photo']='';" class="btn-success w-full py-3 rounded-2xl font-black">
          ➕ ذخیره و نمایش فوری در فروشگاه
        </button>

        <div class="border-t border-white/10 pt-3 space-y-2">
          <div class="font-black text-amber-200 text-center">🔗 تنظیم ایموجی پیش‌فرض ازدواج / رفاقت و پک ایموجی چت:</div>
          <div class="grid grid-cols-3 gap-1.5">
            <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'rel_marriage'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">💍 پیش‌فرض ازدواج</button>
            <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'rel_bestie'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">⚡ پیش‌فرض رفاقت</button>
            <button type="button" onclick="callTowerAdminApi('arm_admin_emoji_capture',{cap_mode:'chat_pack'});setTimeout(()=>tg?.close?.(),700)" class="glass-soft py-2 rounded-xl font-bold">💬 افزودن پک چت</button>
          </div>
        </div>
      </div>

      <div class="glass-panel p-3.5 rounded-3xl space-y-2 mt-3 text-xs">
        <h4 class="font-black text-center text-indigo-300">لیست آیتم‌های فعلی فروشگاه (${items.length})</h4>
        ${items.map(it => `
          <div class="glass-soft p-2.5 rounded-2xl flex justify-between items-center gap-2">
            <div class="flex items-center gap-2.5 min-w-0">
              ${it.category === 'ring' ? window.renderAvatarWithFrame('', 'U', 'w-10 h-10 text-xs', it.photo, it.ring_css) : (it.custom_emoji_id ? window.renderTgEmoji(it.custom_emoji_id, it.icon, 'w-8 h-8') : (it.photo ? `<img src="${it.photo}" class="w-8 h-8 rounded-xl object-contain" />` : `<span class="text-xl">${it.icon}</span>`))}
              <span class="truncate"><b>${it.name}</b> (${it.category}) — ${it.price_coins} 🪙</span>
            </div>
            <button type="button" onclick="callTowerAdminApi('delete_store_item',{item_id:${it.id}})" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold shrink-0">حذف</button>
          </div>
        `).join('')}
      </div>
    `;
  }

  else if (admTab === 'ui_assets') {
    const assetItems = [
      { key: 'menu_bg',     title: '🌌 پس‌زمینه کل مینی‌اپ (Menu BG)' },
      { key: 'hokm_carpet', title: '🟥 طرح فرش میز حکم (Hokm Carpet)' },
      { key: 'crash',       title: '🚀 پوستر کارت کازینو: CRASH' },
      { key: 'bombs',       title: '💣 پوستر کارت کازینو: BOMBS' },
      { key: 'pickaxe',     title: '⛏️ پوستر کارت کازینو: HELL PICKAXE' },
      { key: 'slot',        title: '🎰 پوستر کارت کازینو: ROYAL SLOT' },
      { key: 'voice_hub',   title: '🎙️ پوستر کارت: اتاق‌های صوتی' },
      { key: 'hokm',        title: '🃏 پوستر کارت بازی: حکم ۴ نفره' },
      { key: 'hokm2p',      title: '🃏 پوستر کارت بازی: حکم ۲ نفره' },
      { key: 'dooz',        title: '🃏 پوستر کارت بازی: دوز ۲ نفره' },
      { key: 'doz4p',       title: '🃏 پوستر کارت بازی: دوز ۴ نفره' },
      { key: 'connect4',    title: '🃏 پوستر کارت بازی: چهار در ردیف' },
      { key: 'rps',         title: '🃏 پوستر کارت بازی: سنگ کاغذ قیچی' },
      { key: 'guess',       title: '🃏 پوستر کارت بازی: حدس عدد' },
      { key: '2048',        title: '🃏 پوستر کارت بازی: پازل ۲۰۴۸' },
      { key: 'spuzzle',     title: '🃏 پوستر کارت بازی: پازل ۱۵' },
      { key: 'samegame',    title: '🃏 پوستر کارت بازی: جفت‌های رنگی' },
      { key: 'memory',      title: '🃏 پوستر کارت بازی: حافظه' },
      { key: 'typing',      title: '🃏 پوستر کارت بازی: تایپ سرعتی' },
      { key: 'hangman',     title: '🃏 پوستر کارت بازی: حدس کلمه' }
    ];

    const savedMap = admState.ui_assets || {};
    const cardsListHtml = assetItems.map(item => {
      const curImg = savedMap[item.key] || ('/api/custom_bg/' + item.key);
      const hasCustom = Boolean(savedMap[item.key]);
      return `
        <div class="glass-soft p-3 rounded-2xl flex flex-col gap-2 border ${hasCustom ? 'border-emerald-400/50' : 'border-white/10'}">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2.5 min-w-0">
              <img id="prev_asset_${item.key}" src="${curImg}" class="w-14 h-14 rounded-xl object-cover border border-purple-400/40 shrink-0" />
              <div class="min-w-0">
                <div class="font-black text-xs text-white truncate">${item.title}</div>
                <div class="text-[10px] ${hasCustom ? 'text-emerald-300' : 'text-slate-400'} font-bold">
                  ${hasCustom ? '✅ عکس سفارشی فعال است' : '⚪ تصویر پیش‌فرض'}
                </div>
              </div>
            </div>
            ${hasCustom ? `<button type="button" onclick="admDeleteUiAsset('${item.key}')" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold shrink-0">حذف</button>` : ''}
          </div>
          <div class="flex items-center gap-2 pt-1 border-t border-white/10">
            <input type="file" accept="image/*" onchange="handleImageUpload(this, 'asset_${item.key}', 'prev_asset_${item.key}')" class="flex-1 text-[10px] text-slate-300" />
            <button type="button" onclick="admSaveUiAsset('${item.key}')" class="btn-success px-3.5 py-1.5 rounded-xl text-[11px] font-black shrink-0">💾 ذخیره</button>
          </div>
        </div>
      `;
    }).join('');

    sectionHtml = `
      <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
        <h3 class="font-black text-sm text-amber-300 text-center">🖼️ مدیریت و تغییر تمام عکس‌های مینی‌اپ</h3>
        <div class="flex flex-col gap-2.5">${cardsListHtml}</div>
      </div>
    `;
  }

  else if (admTab === 'bot_stats') {
    const st = admState.bot_stats || {};
    const draft = admState.bc_draft || null;
    sectionHtml = `
      <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
        <h3 class="font-black text-sm text-amber-300 text-center">📊 آمار زنده کل پلتفرم راینو</h3>
        <div class="grid grid-cols-2 gap-2 text-center font-extrabold">
          <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">کل کاربران</div><div class="text-lg text-emerald-300">${st.users || 0}</div></div>
          <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">کل گروه‌ها</div><div class="text-lg text-sky-300">${st.groups || 0}</div></div>
          <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">اتاق‌های صوتی</div><div class="text-lg text-amber-300">${st.rooms || 0}</div></div>
          <div class="glass-soft p-3 rounded-2xl"><div class="text-slate-400 text-[10px]">مشترکین VIP</div><div class="text-lg text-purple-300">💎 ${st.vips || 0}</div></div>
        </div>

        <div class="border-t border-white/10 pt-3 space-y-2.5">
          <h4 class="font-black text-sm text-indigo-300 text-center">📢 ارسال پیام همگانی (با حفظ ایموجی پریمیوم)</h4>
          <div class="glass-soft p-3 rounded-2xl text-center space-y-2 border ${draft ? 'border-emerald-400/50' : 'border-amber-400/40'}">
            ${draft ? `
              <div class="text-emerald-300 font-black text-xs">✅ پیام همگانی شما در پیوی دریافت و آماده ارسال است!</div>
              <div class="p-2 rounded-xl bg-black/40 text-slate-200 text-[11px] truncate">«${draft.preview}»</div>
              <div class="grid grid-cols-2 gap-2 pt-1">
                <button type="button" onclick="callTowerAdminApi('bot_arm_bc_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary py-2 rounded-xl font-bold text-[11px]">🔄 تغییر پیام در پیوی</button>
                <button type="button" onclick="callTowerAdminApi('bot_clear_bc_draft')" class="btn-danger py-2 rounded-xl font-bold text-[11px]">🗑️ پاک کردن پیام</button>
              </div>
            ` : `
              <button type="button" onclick="callTowerAdminApi('bot_arm_bc_capture');setTimeout(()=>tg?.close?.(),700)" class="btn-primary w-full py-3.5 rounded-2xl font-black text-xs border border-amber-400/50">
                📝 ثبت پیام همگانی در پیوی ربات (با ایموجی پریمیوم)
              </button>
            `}
          </div>

          <select id="bc_target" class="w-full p-2.5 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
            <option value="users">👤 ارسال به تمام کاربران (پیوی)</option>
            <option value="groups">👥 ارسال به تمام گروه‌ها</option>
          </select>
          <div class="grid grid-cols-2 gap-2">
            <input id="bc_btxt" type="text" placeholder="متن دکمه شیشه‌ای (اختیاری)" class="p-2.5 rounded-xl glass-soft text-white text-center" />
            <input id="bc_burl" type="text" placeholder="لینک (https://...)" class="p-2.5 rounded-xl glass-soft text-white text-center" />
          </div>
          <button type="button" onclick="callTowerAdminApi('bot_broadcast',{target_type:document.getElementById('bc_target').value,btn_text:document.getElementById('bc_btxt').value,btn_url:document.getElementById('bc_burl').value})" ${!draft ? 'disabled' : ''} class="${draft ? 'btn-success' : 'bg-slate-800 opacity-50'} w-full py-4 rounded-2xl font-black text-sm">
            🚀 شروع ارسال همگانی نهایی
          </button>
        </div>

        <div class="border-t border-white/10 pt-3">
          <button type="button" onclick="if(confirm('آیا مطمئن هستید که می‌خواهید تمام موجودی‌های سکه/استارز، لول‌های ثروت و جذابیت کاربران و دیتابیس اتاق‌های صوتی صفر شوند؟'))callTowerAdminApi('reset_all_platform')" class="btn-danger w-full py-3.5 rounded-2xl font-black text-xs">
            ♻️ ریست لول و موجودی کل کاربران و روم‌ها
          </button>
        </div>
      </div>
    `;
  }

  else if (admTab === 'users') {
    const u = admLookedUpUser;
    const allUsers = admState.users_list || [];
    const usersRowsHtml = allUsers.map((usr, idx) => {
      const unamePart = usr.username ? ('(@' + usr.username + ')') : '';
      return `
        <div onclick="callTowerAdminApi('Lookup_user',{target_uid:${usr.user_id}})" class="glass-soft p-3 rounded-2xl flex items-center justify-between gap-2 text-xs cursor-pointer hover:border-amber-400/50">
          <div class="text-right space-y-0.5 min-w-0">
            <div class="font-black text-white truncate">${idx + 1}. ${usr.first_name || 'بدون نام'} ${unamePart}</div>
            <div class="text-[10px] text-slate-300 font-mono">ID: ${usr.user_id} | 💎 ${(usr.sub_tier||'free').toUpperCase()} | 🪙 ${Number(usr.coins||0).toLocaleString()} | ⭐ ${usr.stars_balance||0}</div>
          </div>
          <button type="button" class="btn-primary px-2.5 py-1.5 rounded-xl text-[10px] font-black shrink-0">مدیریت ◀</button>
        </div>
      `;
    }).join('');

    sectionHtml = `
      <div class="glass-panel p-4 rounded-3xl space-y-3 text-xs">
        <h3 class="font-black text-sm text-amber-300 text-center">🔍 جستجو، شارژ سکه/استارز و اهدای اشتراک VIP</h3>
        <div class="flex gap-2">
          <input id="au_uid" type="number" value="${u ? u.user_id : ''}" placeholder="آیدی عددی کاربر..." class="flex-1 p-2.5 rounded-xl glass-soft text-center font-black text-white" />
          <button type="button" onclick="callTowerAdminApi('Lookup_user',{target_uid:Number(document.getElementById('au_uid').value)})" class="btn-primary px-4 rounded-xl font-black">جستجو</button>
        </div>

        ${u ? `
          <div class="glass-soft p-3 rounded-2xl space-y-2 border-2 border-amber-400">
            <div class="flex justify-between"><span>کاربر:</span><b>${u.display_name} (${u.user_id})</b></div>
            <div class="flex justify-between"><span>موجودی سکه / استارز:</span><b class="text-amber-300">🪙 ${(u.coins||0).toLocaleString()} | ⭐ ${u.stars_balance||0}</b></div>
            <div class="flex justify-between"><span>لول ثروت / جذابیت:</span><b class="text-pink-300">💰 Lv.${u.wealth_level||1}/50 | 💖 Lv.${u.charm_level||1}/50</b></div>

            <div class="grid grid-cols-2 gap-2 pt-2 border-t border-white/10">
              <input id="au_addc" type="number" placeholder="افزودن سکه (+)" class="p-2 rounded-xl bg-slate-900 text-center text-white font-bold" />
              <input id="au_adds" type="number" placeholder="افزودن استارز (+)" class="p-2 rounded-xl bg-slate-900 text-center text-white font-bold" />
            </div>
            <div>
              <label class="block text-[10px] text-slate-300 mb-1">تغییر سطح اشتراک کاربر:</label>
              <select id="au_tier" class="w-full p-2 rounded-xl bg-slate-900 border border-white/20 text-white font-bold text-center">
                <option value="">بدون تغییر (${u.sub_tier.toUpperCase()})</option>
                <option value="free">FREE (عادی)</option>
                <option value="pro">🥈 PRO (پرو)</option>
                <option value="plus">🥇 PLUS (پلاس)</option>
                <option value="ultra">💎 ULTRA (الترا)</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button type="button" onclick="callTowerAdminApi('charge_user',{target_uid:${u.user_id},add_coins:Number(document.getElementById('au_addc').value||0),add_stars:Number(document.getElementById('au_adds').value||0),set_tier:document.getElementById('au_tier').value})" class="btn-success py-2.5 rounded-xl font-black">⚡ اعمال تغییرات</button>
              <button type="button" onclick="callTowerAdminApi('bot_global_ban',{target_id:${u.user_id},ban:${!u.global_banned}})" class="btn-danger py-2.5 rounded-xl font-black">${u.global_banned ? '🟢 رفع مسدودیت' : '⛔ مسدود کردن'}</button>
            </div>
          </div>
        ` : ''}
      </div>

      <div class="glass-panel p-4 rounded-3xl space-y-2 mt-3">
        <h4 class="text-xs font-black text-indigo-300 text-center">📋 لیست کل کاربران (${allUsers.length} نفر)</h4>
        <div class="flex flex-col gap-2 max-h-96 overflow-y-auto">${usersRowsHtml}</div>
      </div>
    `;
  }

  else if (admTab === 'bot_channels') {
    const chRows = (admState.forced_channels || []).map(c => `
      <div class="glass-soft p-3 rounded-2xl flex justify-between items-center text-xs">
        <div><div class="font-black text-amber-300">${c.title || c.chat_id}</div><div class="text-[10px] text-slate-300">${c.chat_id}</div></div>
        <button type="button" onclick="callTowerAdminApi('bot_del_channel',{chat_id:'${c.chat_id}'})" class="btn-danger px-3 py-1.5 rounded-xl text-[10px] font-black">حذف</button>
      </div>
    `).join('');
    sectionHtml = `
      <div class="glass-panel p-4 rounded-3xl space-y-2.5 text-xs">
        <h3 class="font-black text-sm text-amber-300 text-center">🔒 افزودن کانال به قفل اجباری</h3>
        <input id="fc_cid" type="text" placeholder="یوزرنیم کانال با @ (مثلاً @RHINOBOT_TM)" class="w-full p-2.5 rounded-xl glass-soft text-center font-black text-white" />
        <div class="grid grid-cols-2 gap-2">
          <input id="fc_title" type="text" placeholder="عنوان دکمه" class="w-full p-2.5 rounded-xl glass-soft text-center text-white" />
          <input id="fc_uname" type="text" placeholder="یوزرنیم بدون @" class="w-full p-2.5 rounded-xl glass-soft text-center text-white" />
        </div>
        <button type="button" onclick="callTowerAdminApi('bot_add_channel',{chat_id:document.getElementById('fc_cid').value,title:document.getElementById('fc_title').value,username:document.getElementById('fc_uname').value})" class="btn-success w-full py-3 rounded-2xl font-black">➕ افزودن کانال</button>
        <div class="flex flex-col gap-2 pt-2">${chRows}</div>
      </div>
    `;
  }

  else if (admTab === 'bot_groups') {
    const gRows = (admState.groups_list || []).map(g => `
      <div class="glass-soft p-3 rounded-2xl flex justify-between items-center gap-2 text-xs">
        <div class="truncate"><div class="font-black text-white truncate">${g.title || 'Group'}</div><div class="text-[10px] text-slate-400 font-mono">${g.chat_id}</div></div>
        <div class="flex gap-1 shrink-0">
          <button type="button" onclick="callTowerAdminApi('bot_group_link',{chat_id:${g.chat_id}})" class="btn-primary px-2.5 py-1.5 rounded-xl text-[10px] font-bold">🔗 لینک</button>
          <button type="button" onclick="callTowerAdminApi('bot_leave_group',{chat_id:${g.chat_id}})" class="btn-danger px-2.5 py-1.5 rounded-xl text-[10px] font-bold">🚪 خروج</button>
        </div>
      </div>
    `).join('');
    sectionHtml = `<div class="glass-panel p-4 rounded-3xl space-y-2">${gRows}</div>`;
  }

  root.innerHTML = `
    ${renderTopBar('👑 فرماندهی کل پلتفرم')}
    <div class="flex-1 overflow-y-auto px-3 pb-24 flex flex-col">
      <div class="grid grid-cols-3 gap-1.5 mb-3 shrink-0">${tabsHtml}</div>
      ${admMsg ? `<div class="p-3 rounded-2xl bg-emerald-600/35 border border-emerald-400 text-xs font-extrabold text-center mb-2.5 whitespace-pre-line">${admMsg}</div>` : ''}
      ${admErr ? `<div class="p-3 rounded-2xl bg-rose-600/40 border border-rose-400 text-xs font-extrabold text-center mb-2.5 whitespace-pre-line">${admErr}</div>` : ''}
      ${sectionHtml}
    </div>
    ${renderBottomNav()}
  `;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ۲. درگاه لابی بازی‌های چندنفره + میز حکم واقعی روی فرش ایرانی + سایر بازی‌ها
   ═══════════════════════════════════════════════════════════════════════════ */
window.setRpsTargetAndContinue = function(n) {
  lobbyState.rpsTargetWins = n;
  lobbyState.step = 'options';
  renderLobbyGate(document.getElementById('app'));
};
window.startLobbyWithBot = function() { nav(lobbyState.game, true); };
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
    lobbyState.inviteWarning = data.not_started?.length > 0 ? `${T().notStartedWarn}\n(${data.not_started.join(' , ')})` : '';
    lobbyState.inviteSuccess = data.invited?.length > 0 ? `✅ (${data.invited.join(' , ')})` : '';
    renderLobbyGate(document.getElementById('app'));
  } catch (e) {}
};

window.shareTableInline = function(gameType, extraStr = '') {
  const startParamStr = `${gameType}__${parsedChat}__${lang}`;
  const directTableUrl = `https://t.me/${BOT_USERNAME}/${SHORT_NAME}?startapp=${startParamStr}`;
  const shareText = `🎮 ${T().heroTitle} (${gameType.toUpperCase()})\n👤 ${myName}`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(directTableUrl)}&text=${encodeURIComponent(shareText)}`;
  try {
    if (tg && typeof tg.openTelegramLink === 'function') {
      tg.openTelegramLink(shareUrl);
      return;
    }
  } catch (err) {}
  window.open(shareUrl, '_blank');
};

function renderLobbyGate(root) {
  if (lobbyState.step === 'rps_count') {
    root.innerHTML = `
      ${renderTopBar(T().games.rps)}
      <div class="flex-1 flex flex-col justify-center p-4">
        <div class="glass-panel p-6 rounded-3xl text-center">
          <h2 class="text-base font-black text-amber-300 mb-4">${T().rpsAskWins}</h2>
          <div class="grid grid-cols-3 gap-3">
            <button type="button" onclick="setRpsTargetAndContinue(3)" class="btn-primary py-4 rounded-2xl font-black text-base">3 ${T().winsUnit}</button>
            <button type="button" onclick="setRpsTargetAndContinue(5)" class="btn-success py-4 rounded-2xl font-black text-base">5 ${T().winsUnit}</button>
            <button type="button" onclick="setRpsTargetAndContinue(7)" class="btn-danger py-4 rounded-2xl font-black text-base">7 ${T().winsUnit}</button>
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
      boxesHtml += `<input type="text" placeholder="@username / ID (${i + 1})" class="invite-user-input w-full p-3 rounded-xl glass-soft text-white text-sm font-bold text-center" />`;
    }
    root.innerHTML = `
      ${renderTopBar(T().optInvite)}
      <div class="flex-1 overflow-y-auto p-4 flex flex-col justify-center">
        <div class="glass-panel p-5 rounded-3xl text-center">
          <div class="flex flex-col gap-2.5 mb-4">${boxesHtml}</div>
          ${lobbyState.inviteWarning ? `<div class="p-3 rounded-xl bg-rose-600/30 border border-rose-400 text-xs font-extrabold text-rose-200 mb-3 whitespace-pre-line">${lobbyState.inviteWarning}</div>` : ''}
          ${lobbyState.inviteSuccess ? `<div class="p-3 rounded-xl bg-emerald-600/30 border border-emerald-400 text-xs font-extrabold text-emerald-200 mb-3">${lobbyState.inviteSuccess}</div>` : ''}
          <button type="button" onclick="submitBotInvites()" class="btn-success w-full py-3.5 rounded-2xl font-black mb-2">${T().sendInviteBtn}</button>
          <button type="button" onclick="nav('${lobbyState.game}', true)" class="btn-primary w-full py-3.5 rounded-2xl font-black mb-2">${T().enterTableBtn}</button>
          <button type="button" onclick="lobbyState.step='options';renderLobbyGate(document.getElementById('app'))" class="btn-danger w-full py-2.5 rounded-xl font-bold text-xs">${T().backMenu}</button>
        </div>
      </div>
    `;
    return;
  }

  root.innerHTML = `
    ${renderTopBar()}
    <div class="flex-1 flex flex-col justify-center p-4">
      <div class="glass-panel p-5 rounded-3xl text-center flex flex-col gap-3">
        <button type="button" onclick="startLobbyWithBot()" class="btn-success w-full py-4 rounded-2xl font-black text-sm">${T().optBot}</button>
        <button type="button" onclick="openInviteBoxes()" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">${T().optInvite}</button>
        <button type="button" onclick="shareTableInline('${lobbyState.game}', '${lobbyState.rpsTargetWins}');nav('${lobbyState.game}', true)" class="btn-primary w-full py-4 rounded-2xl font-black text-sm">${T().optShare}</button>
      </div>
    </div>
  `;
}

let hokmMode = '4p';
let hokmError = '';
let myMicActive = false;
let localAudioStream = null;

async function callHokmApi(action, extra = {}) {
  if (action === 'state' && isUserTyping()) return;
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
    if (data.state && !(action === 'state' && isUserTyping())) {
      drawHokmTable(data.state);
    }
  } catch (e) {}
}

window.hokmChooseSuit = function(s) { callHokmApi('choose_trump', { suit: s }); };
window.hokmPlayCard = function(code) { callHokmApi('play_card', { card: code }); };
window.hokmFillBots = function() { callHokmApi('add_bots'); };
window.hokmSwapSeats = function(i1, i2) { callHokmApi('swap_seats', { idx1: i1, idx2: i2 }); };
window.hokmSendReaction = function(txt) { callHokmApi('chat', { text: txt }); };
window.hokmSendCustomChat = function() {
  const inp = document.getElementById('hokmChatInp');
  if (inp && inp.value.trim()) {
    const msgText = inp.value.trim();
    inp.value = '';
    inp.blur();
    callHokmApi('chat', { text: msgText });
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
  root.innerHTML = `<div class="p-4 flex-1 flex items-center justify-center"><div class="glass-panel p-6 rounded-3xl font-bold">...</div></div>`;
  callHokmApi('join');
  if (hokmPollTimer) clearInterval(hokmPollTimer);
  hokmPollTimer = setInterval(() => callHokmApi('state'), 1200);
}

function renderRealFaceDownTricks(count) {
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

function renderPlayerRectCard(seat) {
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
        <div class="text-start leading-tight">
          <div class="text-[11px] font-black text-white flex items-center gap-1">
            ${seat.is_hakem ? '👑' : ''}<span class="truncate max-w-[75px]">${seat.name}</span>
            ${seat.mic_on ? '<span class="text-emerald-400">🎙️</span>' : ''}
          </div>
          <div class="text-[9px] text-amber-200/80 font-bold">
            🃏 ${seat.cards_left} ${seat.is_turn ? ('(' + seat.timer_sec + 's)') : ''}
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

  if (st.status === 'joining') {
    const rowsHtml = pList.map((p, idx) => `
      <div class="glass-soft p-2.5 rounded-xl flex justify-between items-center text-xs font-bold">
        <span>#${idx + 1}: <b class="text-amber-300">${p.name}</b></span>
        ${isHost && st.mode === '4p' && idx > 0 ? `
          <button type="button" onclick="hokmSwapSeats(2, ${idx})" class="btn-primary px-2 py-1 rounded-lg text-[10px]">${T().pickPartner}</button>
        ` : ''}
      </div>
    `).join('');

    root.innerHTML = `
      ${renderTopBar(st.mode === '2p' ? T().games.hokm2p : T().games.hokm)}
      <div class="flex-1 p-3 flex flex-col justify-between">
        <div class="persian-carpet p-4 flex flex-col justify-between">
          <div class="carpet-medallion"></div>
          <div class="z-10 glass-panel p-4 rounded-2xl text-center my-auto">
            <h2 class="text-base font-black text-amber-300 mb-3">(${pList.length}/${st.max_players})</h2>
            <div class="flex flex-col gap-2 mb-4">${rowsHtml}</div>
            <div class="flex flex-col gap-2">
              <button type="button" onclick="hokmFillBots()" class="btn-success w-full py-3 rounded-xl font-black text-xs">${T().fillBotsBtn}</button>
              <button type="button" onclick="shareTableInline('${st.mode === '2p' ? 'hokm2p' : 'hokm'}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs">${T().optShare}</button>
            </div>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const topSeat = st.seats?.top || { name: 'P2', cards_left: 0 };
  const rightSeat = st.seats?.right || null;
  const leftSeat = st.seats?.left || null;
  const bottomSeat = st.seats?.bottom || { name: myName, cards_left: (st.my_hand || []).length };
  const isMyTurn = Number(st.turn_id) === Number(uid) && st.status === 'playing';

  let centerStageHtml = '';
  if (st.status === 'hakem_choosing') {
    if (Number(st.hakem_id) === Number(uid)) {
      centerStageHtml = `
        <div class="z-20 glass-panel p-3.5 rounded-2xl border border-amber-400 text-center max-w-[260px]">
          <div class="text-amber-300 font-black text-xs mb-2">${T().chooseTrumpPrompt}</div>
          <div class="grid grid-cols-2 gap-2">
            <button type="button" onclick="hokmChooseSuit('S')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-base">♠️</button>
            <button type="button" onclick="hokmChooseSuit('H')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-base">♥️</button>
            <button type="button" onclick="hokmChooseSuit('D')" class="bg-white text-rose-600 py-2 rounded-xl font-black text-base">♦️</button>
            <button type="button" onclick="hokmChooseSuit('C')" class="bg-white text-slate-900 py-2 rounded-xl font-black text-base">♣️</button>
          </div>
        </div>
      `;
    } else {
      centerStageHtml = `<div class="z-20 glass-panel px-4 py-2.5 rounded-2xl text-xs font-extrabold text-amber-300">👑 ${st.hakem_name}: ${T().waitingHakem}</div>`;
    }
  } else if (st.status === 'finished') {
    centerStageHtml = `
      <div class="z-20 glass-panel p-5 rounded-3xl text-center border-2 border-amber-400">
        <div class="text-xl font-black text-amber-300 mb-3">🏆 ${T().winner}: ${st.winner_display}</div>
        <button type="button" onclick="nav('hub')" class="btn-success px-5 py-2.5 rounded-xl font-bold text-xs">${T().backMenu}</button>
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

  const handCards = st.my_hand || [];
  const overlapPx = handCards.length > 9 ? -15 : (handCards.length > 6 ? -10 : -4);
  const handHtml = handCards.map((c, idx) => `
    <button type="button"
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

        <div class="z-20 flex justify-between items-start gap-1">
          <div class="glass-panel px-2 py-1 rounded-xl text-[10px] font-extrabold">
            <div>${T().trump}: <span class="bg-white text-black px-1 rounded">${st.trump_icon}</span></div>
            <div class="text-amber-300">${T().sets}: ${st.our_sets} - ${st.their_sets}</div>
          </div>

          ${renderPlayerRectCard(topSeat)}

          <button type="button" onclick="nav('hub')" class="btn-danger px-2.5 py-1 rounded-xl text-[10px] font-bold">${T().backMenu}</button>
        </div>

        <div class="z-20 flex-1 flex items-center justify-between px-0.5 min-h-[150px]">
          <div class="flex flex-col items-center gap-1">
            ${rightSeat ? renderPlayerRectCard(rightSeat) : ''}
          </div>

          <div class="flex-1 flex flex-col items-center justify-center">
            <div class="mb-1 flex items-center gap-1">
              <span class="text-[10px] font-bold text-rose-200">${T().oppTricks}:</span>
              ${renderRealFaceDownTricks(st.their_tricks)}
            </div>
            ${centerStageHtml}
          </div>

          <div class="flex flex-col items-center gap-1">
            ${leftSeat ? renderPlayerRectCard(leftSeat) : ''}
          </div>
        </div>

        <div class="z-20 flex flex-col items-center gap-1">
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-extrabold text-emerald-300">${T().ourTricks} (${st.our_tricks}/7):</span>
            ${renderRealFaceDownTricks(st.our_tricks)}
          </div>

          ${hokmError ? `<div class="bg-rose-600/90 px-3 py-0.5 rounded-lg text-[11px] font-bold">${hokmError}</div>` : ''}

          <div class="ltr-grid w-full flex justify-center items-end py-1 px-1 overflow-hidden">
            ${handHtml}
          </div>

          <div class="w-full flex items-center justify-between gap-1 px-1">
            ${renderPlayerRectCard(bottomSeat)}

            <div class="flex items-center gap-1">
              <button type="button" onclick="hokmToggleMic()" class="${myMicActive ? 'btn-success' : 'glass-panel'} px-2.5 py-1.5 rounded-xl text-xs font-bold">
                ${myMicActive ? T().micOn : T().micOff}
              </button>
              <button type="button" onclick="hokmSendReaction('🔥')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">🔥</button>
              <button type="button" onclick="hokmSendReaction('😂')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">😂</button>
              <button type="button" onclick="hokmSendReaction('👏')" class="glass-panel px-2 py-1.5 rounded-xl text-xs">👏</button>
            </div>
          </div>

          <div class="w-full flex gap-1 px-1">
            <input id="hokmChatInp" type="text" maxlength="40" placeholder="${T().chatPlaceholder}" onkeydown="if(event.key==='Enter')hokmSendCustomChat()" class="flex-1 px-2.5 py-1 rounded-xl glass-soft text-white text-[11px]" />
            <button type="button" onclick="hokmSendCustomChat()" class="btn-primary px-3 py-1 rounded-xl text-[11px] font-bold">${T().sendBtn}</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

/* ═══════════ بازی‌های آرکید و فکری (2048, پازل ۱۵، دوز، ۴ در ردیف، حدس عدد، حافظه، تایپ، حدس کلمه) ═══════════ */
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
    ${renderTopBar(T().games.g2048)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="glass-panel px-4 py-2.5 rounded-2xl flex justify-between items-center">
        <span class="font-extrabold text-sm">${T().score}: <b class="text-amber-300">${s2048}</b></span>
        <button type="button" onclick="init2048();render()" class="btn-success px-3 py-1 rounded-xl text-xs font-bold">${T().restart}</button>
      </div>
      <div id="board2048" class="ltr-grid grid grid-cols-4 gap-2.5 glass-panel p-3.5 rounded-3xl touch-none">${cells}</div>
      <p class="text-center text-xs text-slate-300 font-bold">${T().swipeHint}</p>
    </div>
    ${renderBottomNav()}
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
  const cells = spz.map((v,i) => `<button type="button" onclick="clickSpz(${i})" class="aspect-square rounded-2xl font-black text-xl ${v ? 'btn-primary' : 'bg-white/5'}">${v || ''}</button>`).join('');
  root.innerHTML = `
    ${renderTopBar(T().games.spuzzle)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="flex justify-end"><button type="button" onclick="initSpz();render()" class="btn-success px-3 py-1.5 rounded-xl font-bold text-xs">${T().restart}</button></div>
      <div id="spzBoard" class="ltr-grid grid grid-cols-4 gap-2 glass-panel p-3.5 rounded-3xl touch-none">${cells}</div>
      <p class="text-center text-xs text-slate-300 font-bold">${T().swipeHint}</p>
    </div>
    ${renderBottomNav()}
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

const DOOZ_COLORS = [
  { id: 'rose',   cls: 'bg-rose-500 shadow-[0_0_12px_#f43f5e]' },
  { id: 'cyan',   cls: 'bg-cyan-400 shadow-[0_0_12px_#22d3ee]' },
  { id: 'emerald',cls: 'bg-emerald-400 shadow-[0_0_12px_#34d399]' },
  { id: 'amber',  cls: 'bg-amber-400 shadow-[0_0_12px_#fbbf24]' },
  { id: 'purple', cls: 'bg-purple-500 shadow-[0_0_12px_#a855f7]' }
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
    <button type="button" onclick="pickDoozColor(${idx})" class="w-7 h-7 rounded-full ${c.cls} border-2 ${myDoozColorIdx === idx ? 'border-white scale-110' : 'border-transparent opacity-60'}"></button>
  `).join('');
  const cells = doozB.map((v,i) => `
    <button type="button" onclick="clickDooz(${i})" class="aspect-square rounded-full glass-soft flex items-center justify-center p-2">
      ${v !== null ? `<div class="w-full h-full rounded-full ${DOOZ_COLORS[v].cls}"></div>` : ''}
    </button>
  `).join('');
  root.innerHTML = `
    ${renderTopBar(mode==='doz4p' ? T().games.doz4p : T().games.dooz)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="glass-panel p-3 rounded-2xl flex justify-between items-center">
        <span class="text-xs font-extrabold">${T().pickColor}</span>
        <div class="flex gap-2">${colorPickerHtml}</div>
      </div>
      <div class="ltr-grid grid ${sz===5?'grid-cols-5':'grid-cols-3'} gap-3 glass-panel p-4 rounded-3xl">${cells}</div>
      <button type="button" onclick="initDooz('${mode}');render()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().restart}</button>
    </div>
    ${renderBottomNav()}
  `;
}

let guessRoomData = null;
async function callGuessApi(action, extra = {}) {
  if (action === 'state' && isUserTyping()) return;
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
    if (data.room && !(action === 'state' && isUserTyping())) {
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
  guessPollTimer = setInterval(() => callGuessApi('state'), 2500);
};
window.sendGroupGuessVal = function() {
  const inp = document.getElementById('gValInp');
  const v = Number(inp?.value);
  if (inp && inp.value.trim() !== '' && !isNaN(v)) {
    inp.value = '';
    inp.blur();
    callGuessApi('guess', { guess_val: v });
  }
};
window.restartGroupGuess = function() { callGuessApi('restart'); };

function renderGuess(root) {
  if (!guessRoomData) {
    root.innerHTML = `
      ${renderTopBar(T().games.guess)}
      <div class="flex-1 flex flex-col justify-center p-4 pb-24">
        <div class="glass-panel p-5 rounded-3xl text-center">
          <div class="grid grid-cols-2 gap-3 my-4">
            <div>
              <label class="text-xs text-slate-300 font-bold block mb-1">${T().fromNum}</label>
              <input id="gMinInp" type="number" value="1" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
            </div>
            <div>
              <label class="text-xs text-slate-300 font-bold block mb-1">${T().toNum}</label>
              <input id="gMaxInp" type="number" value="1000" class="w-full p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
            </div>
          </div>
          <button type="button" onclick="createGroupGuessRange()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().createGame}</button>
        </div>
      </div>
      ${renderBottomNav()}
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
    ${renderTopBar(`${T().games.guess} (${r.min}-${r.max})`)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24 overflow-hidden">
      <div class="glass-panel p-4 rounded-3xl text-center">
        ${r.winner_id ? `
          <div class="p-4 rounded-2xl bg-emerald-600/30 border border-emerald-400 my-2">
            <div class="text-lg font-black text-emerald-300">🎉 ${T().winner}: ${r.winner_name} (${r.secret_revealed})</div>
          </div>
        ` : `
          <div class="flex gap-2 my-2">
            <input id="gValInp" type="number" placeholder="${r.min} - ${r.max}" onkeydown="if(event.key==='Enter')sendGroupGuessVal()" class="flex-1 p-3 rounded-xl glass-soft text-center font-black text-lg text-white" />
            <button type="button" onclick="sendGroupGuessVal()" class="btn-success px-5 rounded-xl font-black">${T().submitBtn}</button>
          </div>
        `}
        <button type="button" onclick="shareTableInline('guess', '${r.min}-${r.max}')" class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs mt-2">${T().optShare}</button>
      </div>

      <div class="flex-1 overflow-y-auto my-3 flex flex-col gap-1.5">${histHtml}</div>

      <div class="flex gap-2">
        ${r.winner_id && isHost ? `<button type="button" onclick="restartGroupGuess()" class="btn-success flex-1 py-3.5 rounded-2xl font-black">${T().playAgainBtn}</button>` : ''}
        <button type="button" onclick="guessRoomData=null;nav('hub')" class="btn-danger flex-1 py-3.5 rounded-2xl font-black">${T().backMenu}</button>
      </div>
    </div>
    ${renderBottomNav()}
  `;
}

let rpsU = 0, rpsB = 0, rpsMsg = '...';
window.playRPS = function(c) {
  const target = lobbyState.rpsTargetWins || 3;
  if (rpsU >= target || rpsB >= target) { rpsU = 0; rpsB = 0; }
  const b = ['rock','paper','scissors'][Math.floor(Math.random()*3)];
  if (c===b) rpsMsg = '=';
  else if ((c==='rock'&&b==='scissors')||(c==='paper'&&b==='rock')||(c==='scissors'&&b==='paper')) {
    rpsU++; rpsMsg = rpsU >= target ? `🏆 ${T().winner}!` : '+1';
  } else {
    rpsB++; rpsMsg = rpsB >= target ? '❌' : '-1';
  }
  renderRPS(document.getElementById('app'));
};
function renderRPS(root) {
  const target = lobbyState.rpsTargetWins || 3;
  root.innerHTML = `
    ${renderTopBar(`${T().games.rps} (${target})`)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24 text-center">
      <div class="glass-panel p-6 rounded-3xl">
        <p class="text-3xl font-black mb-3">${rpsU} — ${rpsB}</p>
        <div class="p-3 rounded-xl glass-soft font-bold text-sm">${rpsMsg}</div>
      </div>
      <div class="grid grid-cols-3 gap-3">
        <button type="button" onclick="playRPS('rock')" class="btn-primary py-5 rounded-2xl font-black">🪨 ${T().rock}</button>
        <button type="button" onclick="playRPS('paper')" class="btn-success py-5 rounded-2xl font-black">📄 ${T().paper}</button>
        <button type="button" onclick="playRPS('scissors')" class="btn-danger py-5 rounded-2xl font-black">✂️ ${T().scissors}</button>
      </div>
      <div></div>
    </div>
    ${renderBottomNav()}
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
  const cells = c4B.map(row=>row.map((v,c)=>`<button type="button" onclick="dropC4(${c})" class="aspect-square rounded-full ${v===1?'btn-danger':v===2?'btn-success':'glass-soft'}"></button>`).join('')).join('');
  root.innerHTML = `
    ${renderTopBar(T().games.connect4)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold text-sm">${c4Win ? `🏆 P${c4Win}` : `${T().turn}: P${c4Turn}`}</div>
      <div class="ltr-grid grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${cells}</div>
      <button type="button" onclick="initC4();render()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().restart}</button>
    </div>
    ${renderBottomNav()}
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
  const cells = sgGrid.map((row,r)=>row.map((v,c)=>`<button type="button" onclick="clickSg(${r},${c})" class="aspect-square rounded-lg ${sgCls[v]}"></button>`).join('')).join('');
  root.innerHTML = `
    ${renderTopBar(T().games.samegame)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="glass-panel px-4 py-2 rounded-xl text-center font-bold">${T().score}: ${sgScore}</div>
      <div class="ltr-grid grid grid-cols-8 gap-1.5 glass-panel p-3 rounded-3xl">${cells}</div>
      <div></div>
    </div>
    ${renderBottomNav()}
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
  const cells = memCards.map((v,i)=>{ const open = memFlip.includes(i) || memMatch.includes(i); return `<button type="button" onclick="clickMem(${i})" class="aspect-square rounded-2xl font-black text-2xl ${open?'btn-success':'glass-panel'}">${open?v:'?'}</button>`; }).join('');
  root.innerHTML = `
    ${renderTopBar(T().games.memory)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="ltr-grid grid grid-cols-4 gap-2.5 glass-panel p-3.5 rounded-3xl my-auto">${cells}</div>
    </div>
    ${renderBottomNav()}
  `;
}

const sentences = ["آب از سرچشمه گل آلود است", "به عمل کار برآید به سخندانی نیست", "نابرده رنج گنج میسر نمیشود"];
let targetSentence = sentences[0], typeStart = 0, typeMsg = '';
function initTyping() { targetSentence = sentences[Math.floor(Math.random()*sentences.length)]; typeStart = Date.now(); typeMsg = ''; }
window.checkTyping = function() {
  const val = document.getElementById('typeInput').value.trim();
  if (val === targetSentence) typeMsg = '🏆 ' + ((Date.now() - typeStart)/1000).toFixed(1) + 's'; else typeMsg = '❌';
  renderTyping(document.getElementById('app'));
};
function renderTyping(root) {
  if (!typeStart) initTyping();
  root.innerHTML = `
    ${renderTopBar(T().games.typing)}
    <div class="flex-1 flex flex-col justify-center p-4 pb-24">
      <div class="glass-panel p-5 rounded-3xl">
        <p class="p-3.5 rounded-2xl glass-soft font-bold text-emerald-300 mb-4 text-center">${targetSentence}</p>
        <input id="typeInput" type="text" class="w-full p-3.5 rounded-2xl glass-soft text-white mb-3 text-center" />
        ${typeMsg ? `<p class="font-bold text-amber-300 mb-3 text-center">${typeMsg}</p>` : ''}
        <button type="button" onclick="checkTyping()" class="btn-success w-full py-3.5 rounded-2xl font-black">${T().submitBtn}</button>
      </div>
    </div>
    ${renderBottomNav()}
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
  const kbHtml = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی".split('').map(ch => `<button type="button" onclick="guessLetter('${ch}')" class="py-2 rounded-xl font-bold ${hmGuessed.includes(ch) ? 'opacity-30 glass-soft' : 'btn-primary'}">${ch}</button>`).join('');
  root.innerHTML = `
    ${renderTopBar(T().games.hangman)}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24">
      <div class="glass-panel p-5 rounded-3xl text-center">
        <div class="text-xs text-rose-300 font-bold">❤️ ${hmLives}</div>
        <div class="text-3xl font-black tracking-widest my-3">${display}</div>
      </div>
      <div class="grid grid-cols-7 gap-1.5 glass-panel p-3 rounded-3xl">${kbHtml}</div>
    </div>
    ${renderBottomNav()}
  `;
}

async function renderGardoneAnim(root) {
  root.innerHTML = `
    ${renderTopBar()}
    <div class="flex-1 flex flex-col justify-between p-4 pb-24 text-center">
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
    if (idx >= winNames.length) { slot.innerText = "🏆"; return; }
    let elapsed = 0; const target = winNames[idx];
    const timer = setInterval(() => {
      slot.innerText = allNames[Math.floor(Math.random() * allNames.length)];
      elapsed += 70;
      if (elapsed >= 1600) {
        clearInterval(timer); idx++; slot.innerText = '🥇 ' + target;
        const row = document.createElement('div');
        row.className = "p-2 rounded-xl glass-soft font-bold text-emerald-300";
        row.innerText = '#' + idx + ' - ' + target;
        wBox.appendChild(row);
        setTimeout(nextWinner, 1200);
      }
    }, 70);
  }
  setTimeout(nextWinner, 400);
}

/* ═══════════ روتر اصلی و اجرای اولیه مینی‌اپ ═══════════ */
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

verifyJoinAndRender();
"""
