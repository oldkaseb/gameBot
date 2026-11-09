"""پنل ادمین استایل‌دار — به سبک ربات ایموجی"""

from __future__ import annotations
import math
from typing import Union
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from emojis import E
from langs import t, get_user_lang
from utils.premium import (
    btn, primary, success, danger, back_btn, cancel_btn, kb,
)
from database import db

router = Router(name="admin_panel")

OWNER_IDS = {7662192190, 6041119040}
USERS_PAGE = 8


class AdminStates(StatesGroup):
    search_user = State()
    charge_days = State()
    broadcast = State()
    add_admin = State()
    set_trial = State()
    set_price = State()


# ─────────── بررسی سطح دسترسی
async def _is_admin(uid: int) -> bool:
    if uid in OWNER_IDS:
        return True
    return await db.pool.fetchval("SELECT 1 FROM admins WHERE user_id = $1", uid) is not None


async def _is_owner(uid: int) -> bool:
    return uid in OWNER_IDS


# ─────────── منوی اصلی ادمین
def _admin_menu_kb(lang: str = "fa") -> "InlineKeyboardMarkup":
    return kb([
        [success(f"{E.CHART} {t('admin_stats', lang)}", "adm:stats")],
        [primary(f"{E.SEARCH} {t('admin_users', lang)}", "adm:users"),
         primary(f"{E.BOX} {t('admin_defpacks', lang)}", "adm:defpacks")],
        [primary(f"{E.BLOCK} {t('admin_filters', lang)}", "adm:filters"),
         primary(f"{E.LOCK} {t('admin_locks', lang)}", "adm:locks")],
        [primary(f"{E.MEGA} {t('admin_bcast', lang)}", "adm:bcast"),
         primary(f"{E.LINK} {t('admin_refs', lang)}", "adm:refs")],
        [primary(f"{E.CAL} {t('admin_settings', lang)}", "adm:settings"),
         danger(f"{E.CROWN} {t('admin_admins', lang)}", "adm:admins")],
        [primary(f"{E.BOX} {t('admin_backup', lang)}", "adm:backup_menu")],
        [back_btn(lang, "menu")],
    ])


def _admin_text(lang: str) -> str:
    return (
        f"{E.CROWN}{E.PC} <b>{t('admin_panel', lang)}</b>\n\n"
        f"{E.FLAME} مدیریت کامل ربات از اینجاست.\n"
        f"{E.SPARK} یک بخش را انتخاب کن:"
    )


# ─────────── ورودی‌ها
async def open_panel(event: Union[Message, CallbackQuery], state: FSMContext = None):
    uid = event.from_user.id
    lang = get_user_lang(uid)

    if not await _is_admin(uid):
        if isinstance(event, CallbackQuery):
            await event.answer(t("admin_only", lang), show_alert=True)
        else:
            await event.answer(f"{E.BLOCK} {t('admin_only', lang)}")
        return

    if state:
        await state.clear()

    text = _admin_text(lang)
    markup = _admin_menu_kb(lang)

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def open_stats(event: Union[Message, CallbackQuery]):
    uid = event.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        return

    # جمع‌آوری آمار
    try:
        total_users = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
        active_users = await db.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE is_banned=FALSE AND subscription_end > NOW()"
        ) or 0
        banned_users = await db.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE is_banned=TRUE"
        ) or 0
        total_groups = await db.pool.fetchval("SELECT COUNT(*) FROM groups") or 0
        total_packs = await db.pool.fetchval("SELECT COUNT(*) FROM user_packs") or 0
        def_packs = await db.pool.fetchval("SELECT COUNT(*) FROM default_packs") or 0
    except Exception:
        # ممکن است جدول‌ها وجود نداشته باشند
        total_users = active_users = banned_users = total_groups = 0
        total_packs = def_packs = 0

    text = (
        f"{E.CHART}{E.ROCKET} <b>{t('admin_stats', lang)}</b>\n\n"
        f"{E.DISGUISE} کاربران کل: <b>{total_users:,}</b>\n"
        f"{E.OK2} فعال: <b>{active_users:,}</b>\n"
        f"{E.BLOCK} مسدود: <b>{banned_users:,}</b>\n"
        f"{E.PARTY} گروه‌ها: <b>{total_groups:,}</b>\n"
        f"{E.BOX} پک پیش‌فرض: <b>{def_packs:,}</b>\n"
        f"{E.GEM} پک کاربر: <b>{total_packs:,}</b>"
    )
    markup = kb([[back_btn(lang, "adm:panel")]])

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        await event.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════
# ═══ CALLBACK HANDLERS
# ═══════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(msg: Message, state: FSMContext):
    await open_panel(msg, state)


@router.message(F.text.in_({"ادمین", "پنل ادمین", "مدیر"}))
async def msg_admin(msg: Message, state: FSMContext):
    await open_panel(msg, state)


@router.callback_query(F.data == "adm:panel")
async def cb_panel(cb: CallbackQuery, state: FSMContext):
    await open_panel(cb, state)


@router.callback_query(F.data == "adm:stats")
async def cb_stats(cb: CallbackQuery):
    await open_stats(cb)


# ─────────── آمار (دستور /stats)
@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    await open_stats(msg)


@router.message(F.text.in_({"آمار", "امار"}))
async def msg_stats(msg: Message):
    await open_stats(msg)


# ─────────── چک کاربر
@router.callback_query(F.data == "adm:users")
async def cb_users(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    await cb.answer()
    await state.clear()

    text = f"{E.SEARCH} <b>{t('admin_users', lang)}</b>\n\n{E.INFO} یک گزینه انتخاب کنید:"
    markup = kb([
        [primary(f"{E.DISGUISE} لیست کاربران", "adm:ulist:0")],
        [success(f"{E.SEARCH} جستجوی کاربر", "adm:usearch")],
        [back_btn(lang, "adm:panel")],
    ])
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:ulist:"))
async def cb_ulist(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    await cb.answer()
    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 0

    try:
        users = await db.pool.fetch(
            "SELECT user_id, full_name, username, is_banned FROM users "
            "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            USERS_PAGE, page * USERS_PAGE,
        )
        total = await db.pool.fetchval("SELECT COUNT(*) FROM users") or 0
    except Exception:
        users = []
        total = 0

    pages = max(1, math.ceil(total / USERS_PAGE))
    rows = []
    for u in users:
        icon = E.BLOCK if u["is_banned"] else E.OK2
        name = u["full_name"] or f"user_{u['user_id']}"
        rows.append([primary(f"{icon} {name}", f"adm:up:{u['user_id']}")])

    nav = []
    if page > 0:
        nav.append(primary(f"◀️ قبلی", f"adm:ulist:{page-1}"))
    nav.append(primary(f"{page+1}/{pages}", "noop"))
    if page < pages - 1:
        nav.append(primary(f"بعدی ▶️", f"adm:ulist:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([back_btn(lang, "adm:users")])
    await cb.message.edit_text(
        f"{E.DISGUISE} <b>لیست کاربران</b> ({total:,} نفر)",
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:usearch")
async def cb_usearch(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    if not await _is_admin(uid):
        await cb.answer(t("admin_only", lang), show_alert=True)
        return

    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.search_user)
    await cb.message.edit_text(
        f"{E.SEARCH} <b>جستجوی کاربر</b>\n\n{E.INFO} آیدی عددی را بفرستید:",
        reply_markup=kb([[cancel_btn(lang, "adm:users")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.search_user, F.text)
async def msg_search_user(msg: Message, state: FSMContext):
    lang = get_user_lang(msg.from_user.id)
    try:
        target = int(msg.text.strip().replace("۰", "0").replace("۱", "1").replace("۲", "2")
                     .replace("۳", "3").replace("۴", "4").replace("۵", "5").replace("۶", "6")
                     .replace("۷", "7").replace("۸", "8").replace("۹", "9"))
    except ValueError:
        await msg.answer(f"{E.WARN} آیدی نامعتبر.", parse_mode=ParseMode.HTML)
        return

    await state.clear()
    user = await db.pool.fetchrow("SELECT * FROM users WHERE user_id = $1", target)
    if not user:
        await msg.answer(f"{E.CROSS} کاربر یافت نشد.", parse_mode=ParseMode.HTML)
        return

    await _show_user_panel(msg, target)


async def _show_user_panel(msg_or_cb, target_uid: int):
    """نمایش پنل یک کاربر"""
    user = await db.pool.fetchrow("SELECT * FROM users WHERE user_id = $1", target_uid)
    if not user:
        return

    from datetime import datetime, timezone
    end = user["subscription_end"]
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    days = max(0, (end - datetime.now(timezone.utc)).days) if end else 0

    status_icon = E.OK2 if not user["is_banned"] else E.BLOCK

    text = (
        f"{E.CROWN} <b>پنل کاربر</b>\n\n"
        f"{E.DISGUISE} نام: <b>{user['full_name'] or '—'}</b>\n"
        f"{E.PIN} یوزرنیم: @{user['username'] or '—'}\n"
        f"{E.INFO} آیدی: <code>{target_uid}</code>\n"
        f"{status_icon} وضعیت: {'فعال' if not user['is_banned'] else 'مسدود'}\n"
        f"{E.CAL} اشتراک: {days} روز"
    )

    if user["is_banned"]:
        ban_btn = success(f"{E.OK2} رفع مسدودی", f"adm:unban:{target_uid}")
    else:
        ban_btn = danger(f"{E.BLOCK} مسدود کردن", f"adm:ban:{target_uid}")

    rows = [
        [ban_btn],
        [primary(f"{E.MONEY} شارژ دستی", f"adm:ucharge:{target_uid}")],
        [primary(f"{E.BOX} پک‌های کاربر", f"adm:upacks:{target_uid}")],
        [primary(f"{E.LINK} زیرمجموعه‌ها", f"adm:urefs:{target_uid}")],
        [back_btn(get_user_lang(target_uid), "adm:users")],
    ]

    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.answer()
        await msg_or_cb.message.edit_text(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    else:
        await msg_or_cb.answer(text, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:up:"))
async def cb_up(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await _show_user_panel(cb, target)


@router.callback_query(F.data.startswith("adm:ban:"))
async def cb_ban(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await db.pool.execute("UPDATE users SET is_banned=TRUE WHERE user_id=$1", target)
    await db.log_admin(cb.from_user.id, "ban", target)
    await cb.answer("مسدود شد", show_alert=True)
    await _show_user_panel(cb, target)


@router.callback_query(F.data.startswith("adm:unban:"))
async def cb_unban(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await db.pool.execute("UPDATE users SET is_banned=FALSE WHERE user_id=$1", target)
    await db.log_admin(cb.from_user.id, "unban", target)
    await cb.answer("رفع مسدودی شد", show_alert=True)
    await _show_user_panel(cb, target)


@router.callback_query(F.data.startswith("adm:ucharge:"))
async def cb_ucharge(cb: CallbackQuery, state: FSMContext):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.charge_days)
    await state.update_data(charge_uid=target)
    lang = get_user_lang(cb.from_user.id)
    await cb.message.edit_text(
        f"{E.MONEY} <b>شارژ دستی</b>\n\n{E.INFO} چند روز شارژ شود؟ (عدد بفرستید)",
        reply_markup=kb([[cancel_btn(lang, f"adm:up:{target}")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.charge_days, F.text)
async def msg_charge_days(msg: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("charge_uid")
    if not target:
        await state.clear()
        return

    try:
        days = int(msg.text.strip().replace("۰", "0").replace("۱", "1").replace("۲", "2")
                   .replace("۳", "3").replace("۴", "4").replace("۵", "5").replace("۶", "6")
                   .replace("۷", "7").replace("۸", "8").replace("۹", "9"))
    except ValueError:
        await msg.answer(f"{E.WARN} عدد بفرستید.", parse_mode=ParseMode.HTML)
        return

    await state.clear()

    from datetime import datetime, timezone, timedelta
    new_end = datetime.now(timezone.utc) + timedelta(days=days)
    await db.pool.execute(
        "UPDATE users SET subscription_end=$2 WHERE user_id=$1", target, new_end
    )
    await db.log_admin(msg.from_user.id, "charge", target, str(days))

    await msg.answer(
        f"{E.OK2} کاربر <code>{target}</code> به مدت <b>{days}</b> روز شارژ شد.",
        parse_mode=ParseMode.HTML,
    )

    # اطلاع به کاربر
    try:
        await msg.bot.send_message(
            target,
            f"{E.PARTY}{E.MONEY} حساب شما به مدت <b>{days} روز</b> شارژ شد!",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm:upacks:"))
async def cb_upacks(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await cb.answer()

    try:
        packs = await db.pool.fetch(
            "SELECT pack_title FROM user_packs WHERE user_id=$1", target
        )
    except Exception:
        packs = []

    text = f"{E.BOX} <b>پک‌های {target}</b>\n\n"
    if packs:
        text += "\n".join(f"• {p['pack_title']}" for p in packs)
    else:
        text += "هیچ پکی ندارد."

    await cb.message.edit_text(
        text,
        reply_markup=kb([[back_btn(get_user_lang(cb.from_user.id), f"adm:up:{target}")]]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:urefs:"))
async def cb_urefs(cb: CallbackQuery):
    try:
        target = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await cb.answer()

    try:
        refs = await db.pool.fetch(
            "SELECT user_id, full_name, username FROM users WHERE referred_by=$1", target
        )
    except Exception:
        refs = []

    text = f"{E.LINK} <b>زیرمجموعه‌های {target}</b> ({len(refs)} نفر)\n\n"
    for r in refs[:20]:
        text += f"• {r['full_name'] or '—'} (<code>{r['user_id']}</code>)\n"

    await cb.message.edit_text(
        text,
        reply_markup=kb([[back_btn(get_user_lang(cb.from_user.id), f"adm:up:{target}")]]),
        parse_mode=ParseMode.HTML,
    )


# ─────────── پک‌های پیش‌فرض
@router.callback_query(F.data == "adm:defpacks")
async def cb_defpacks(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_text(
        f"{E.BOX} <b>{t('admin_defpacks', lang)}</b>\n\n{E.INFO} یک گزینه:",
        reply_markup=kb([
            [success(f"{E.PLUS} افزودن پک", "adm:defadd")],
            [primary(f"{E.EYES} لیست پک‌ها", "adm:deflist")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:deflist")
async def cb_deflist(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    try:
        packs = await db.pool.fetch("SELECT * FROM default_packs ORDER BY created_at DESC")
    except Exception:
        packs = []

    rows = []
    for p in packs:
        icon = E.OK2 if p["is_active"] else E.CROSS
        rows.append([primary(f"{icon} {p['pack_title']}", f"adm:deftog:{p['id']}")])
    rows.append([back_btn(lang, "adm:defpacks")])

    await cb.message.edit_text(
        f"{E.BOX} <b>پک‌های پیش‌فرض</b> ({len(packs)})",
        reply_markup=kb(rows) if packs else kb([[back_btn(lang, "adm:defpacks")]]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:deftog:"))
async def cb_deftog(cb: CallbackQuery):
    try:
        pid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("❌")
        return
    await db.pool.execute(
        "UPDATE default_packs SET is_active = NOT is_active WHERE id=$1", pid
    )
    await cb.answer("وضعیت تغییر کرد")
    await cb_deflist(cb)


@router.callback_query(F.data == "adm:defadd")
async def cb_defadd(cb: CallbackQuery, state: FSMContext):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await state.clear()
    await cb.message.edit_text(
        f"{E.PLUS} <b>افزودن پک پیش‌فرض</b>\n\n"
        f"{E.LINK} لینک پک را بفرستید:\n"
        f"<code>https://t.me/addemoji/PackName</code>\n\n"
        f"{E.CROSS} برای لغو: /cancel",
        parse_mode=ParseMode.HTML,
    )


# ─────────── فیلترها
@router.callback_query(F.data == "adm:filters")
async def cb_filters(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_text(
        f"{E.BLOCK} <b>{t('admin_filters', lang)}</b>",
        reply_markup=kb([
            [success(f"{E.SEARCH} مشاهده فیلترها", "adm:flist")],
            [primary(f"{E.PLUS} فیلتر پک", "adm:fpack")],
            [primary(f"{E.REFRESH} رفع فیلتر", "adm:ufilter")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:flist")
async def cb_flist(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()

    try:
        emojis = await db.pool.fetch("SELECT emoji_id FROM filtered_emojis LIMIT 20")
        packs = await db.pool.fetch("SELECT pack_name FROM filtered_packs LIMIT 20")
    except Exception:
        emojis, packs = [], []

    text = f"{E.CHART} <b>فیلترها</b>\n\n"
    text += f"{E.BLOCK} <b>پک‌های فیلتر:</b> {len(packs)}\n"
    for p in packs:
        text += f"  • {p['pack_name']}\n"
    text += f"\n{E.BLOCK} <b>ایموجی‌های فیلتر:</b> {len(emojis)}\n"
    for e in emojis:
        text += f"  • <code>{e['emoji_id']}</code>\n"

    await cb.message.edit_text(
        text,
        reply_markup=kb([[back_btn(lang, "adm:filters")]]),
        parse_mode=ParseMode.HTML,
    )


# ─────────── قفل‌ها / اسپانسری
@router.callback_query(F.data == "adm:locks")
async def cb_locks(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_text(
        f"{E.LOCK} <b>{t('admin_locks', lang)}</b>",
        reply_markup=kb([
            [primary(f"{E.PLUS} افزودن کانال اجباری", "adm:addchannel")],
            [primary(f"{E.EYES} لیست کانال‌ها", "adm:listchannels")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:listchannels")
async def cb_listchannels(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    try:
        chans = await db.pool.fetch("SELECT * FROM forced_channels")
    except Exception:
        chans = []

    text = f"{E.LOCK} <b>کانال‌های اجباری</b> ({len(chans)})\n\n"
    for c in chans:
        text += f"• {c['title'] or c['chat_id']}\n  <code>{c['chat_id']}</code>\n\n"

    await cb.message.edit_text(
        text or "هیچ کانالی ثبت نشده.",
        reply_markup=kb([[back_btn(lang, "adm:locks")]]),
        parse_mode=ParseMode.HTML,
    )


# ─────────── ارسال همگانی
@router.callback_query(F.data == "adm:bcast")
async def cb_bcast(cb: CallbackQuery, state: FSMContext):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.broadcast)
    await cb.message.edit_text(
        f"{E.MEGA} <b>{t('admin_bcast', lang)}</b>\n\n"
        f"{E.INFO} پیام خود را بفرستید (متن، عکس، ویدیو...):\n"
        f"{E.CROSS} برای لغو: /cancel",
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.broadcast)
async def msg_broadcast(msg: Message, state: FSMContext):
    await state.clear()
    lang = get_user_lang(msg.from_user.id)

    status = await msg.answer(f"{E.HOURGLASS} در حال ارسال...")

    try:
        users = await db.pool.fetch("SELECT user_id FROM users WHERE is_banned=FALSE")
    except Exception:
        users = []

    sent = failed = 0
    import asyncio
    for i, u in enumerate(users):
        try:
            await msg.copy_to(u["user_id"])
            sent += 1
        except Exception:
            failed += 1

        # rate limit
        if i % 25 == 0:
            await asyncio.sleep(0.05)

        # آپدیت وضعیت
        if i % 50 == 0:
            try:
                await status.edit_text(
                    f"{E.HOURGLASS} در حال ارسال...\n"
                    f"{E.CHECK} موفق: {sent}\n"
                    f"{E.CROSS} ناموفق: {failed}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    await status.edit_text(
        f"{E.PARTY}{E.OK2} <b>ارسال کامل شد!</b>\n\n"
        f"{E.CHECK} موفق: {sent}\n"
        f"{E.CROSS} ناموفق: {failed}",
        parse_mode=ParseMode.HTML,
    )


# ─────────── زیرمجموعه‌ها
@router.callback_query(F.data == "adm:refs")
async def cb_refs(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()

    try:
        top = await db.pool.fetch(
            """SELECT referred_by, COUNT(*) as cnt FROM users
               WHERE referred_by IS NOT NULL
               GROUP BY referred_by ORDER BY cnt DESC LIMIT 10"""
        )
    except Exception:
        top = []

    text = f"{E.CROWN} <b>برترین معرف‌ها</b>\n\n"
    for i, r in enumerate(top, 1):
        text += f"{i}. <code>{r['referred_by']}</code> — {r['cnt']} نفر\n"

    if not top:
        text += "هیچ زیرمجموعه‌ای یافت نشد."

    await cb.message.edit_text(
        text,
        reply_markup=kb([[back_btn(lang, "adm:panel")]]),
        parse_mode=ParseMode.HTML,
    )


# ─────────── تنظیمات
@router.callback_query(F.data == "adm:settings")
async def cb_settings(cb: CallbackQuery):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()

    try:
        trial = await db.pool.fetchval(
            "SELECT value FROM bot_settings WHERE key='trial_days'"
        ) or "2"
        price = await db.pool.fetchval(
            "SELECT value FROM bot_settings WHERE key='subscription_price'"
        ) or "100000"
    except Exception:
        trial, price = "2", "100000"

    await cb.message.edit_text(
        f"{E.CAL} <b>{t('admin_settings', lang)}</b>\n\n"
        f"{E.GIFT} مدت تست: <b>{trial}</b> روز\n"
        f"{E.MONEY} نرخ اشتراک: <b>{price:,}</b> تومان",
        reply_markup=kb([
            [primary(f"{E.CAL} تغییر مدت تست", "adm:set_trial")],
            [primary(f"{E.CASH} تغییر نرخ", "adm:set_price")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:set_trial")
async def cb_set_trial(cb: CallbackQuery, state: FSMContext):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.set_trial)
    await cb.message.edit_text(
        f"{E.CAL} <b>مدت تست جدید (روز):</b>",
        reply_markup=kb([[cancel_btn(lang, "adm:settings")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.set_trial, F.text)
async def msg_set_trial(msg: Message, state: FSMContext):
    try:
        days = int(msg.text.strip())
        await db.pool.execute(
            """INSERT INTO bot_settings (key, value) VALUES ('trial_days', $1)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
            str(days),
        )
        await state.clear()
        await msg.answer(f"{E.OK2} مدت تست = <b>{days}</b> روز", parse_mode=ParseMode.HTML)
    except ValueError:
        await msg.answer(f"{E.WARN} عدد بفرستید.", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:set_price")
async def cb_set_price(cb: CallbackQuery, state: FSMContext):
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.set_price)
    await cb.message.edit_text(
        f"{E.CASH} <b>نرخ جدید اشتراک (تومان):</b>",
        reply_markup=kb([[cancel_btn(lang, "adm:settings")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.set_price, F.text)
async def msg_set_price(msg: Message, state: FSMContext):
    try:
        price = int(msg.text.strip())
        await db.pool.execute(
            """INSERT INTO bot_settings (key, value) VALUES ('subscription_price', $1)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
            str(price),
        )
        await state.clear()
        await msg.answer(f"{E.OK2} نرخ = <b>{price:,}</b> تومان", parse_mode=ParseMode.HTML)
    except ValueError:
        await msg.answer(f"{E.WARN} عدد بفرستید.", parse_mode=ParseMode.HTML)


# ─────────── مدیریت ادمین‌ها
@router.callback_query(F.data == "adm:admins")
async def cb_admins(cb: CallbackQuery):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()

    try:
        admins = await db.pool.fetch("SELECT * FROM admins ORDER BY created_at")
    except Exception:
        admins = []

    text = f"{E.CROWN} <b>مدیران</b>\n\n"
    text += f"{E.STAR} سوپرادمین‌ها:\n"
    for oid in OWNER_IDS:
        text += f"  • <code>{oid}</code>\n"
    text += f"\n{E.SHIELD} ادمین‌ها ({len(admins)}):\n"
    for a in admins:
        text += f"  • <code>{a['user_id']}</code> — {a['level']}\n"

    await cb.message.edit_text(
        text,
        reply_markup=kb([
            [success(f"{E.PLUS} افزودن", "adm:aadd")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:aadd")
async def cb_aadd(cb: CallbackQuery, state: FSMContext):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()
    await state.clear()
    await state.set_state(AdminStates.add_admin)
    await cb.message.edit_text(
        f"{E.PLUS} <b>آیدی ادمین جدید:</b>",
        reply_markup=kb([[cancel_btn(lang, "adm:admins")]]),
        parse_mode=ParseMode.HTML,
    )


@router.message(AdminStates.add_admin, F.text)
async def msg_add_admin(msg: Message, state: FSMContext):
    try:
        target = int(msg.text.strip())
    except ValueError:
        await msg.answer(f"{E.WARN} آیدی نامعتبر.", parse_mode=ParseMode.HTML)
        return

    try:
        await db.pool.execute(
            """INSERT INTO admins (user_id, level) VALUES ($1, 'full')
               ON CONFLICT (user_id) DO UPDATE SET level = 'full'""",
            target,
        )
        await state.clear()
        await msg.answer(
            f"{E.OK2} ادمین <code>{target}</code> اضافه شد.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await msg.answer(f"{E.WARN} خطا: {e}")


# ─────────── بکاپ
@router.callback_query(F.data == "adm:backup_menu")
async def cb_backup_menu(cb: CallbackQuery):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    lang = get_user_lang(cb.from_user.id)
    await cb.answer()

    await cb.message.edit_text(
        f"{E.BOX} <b>{t('admin_backup', lang)}</b>\n\n"
        f"{E.INFO} عملیات مورد نظر:",
        reply_markup=kb([
            [success(f"{E.DOWN} بکاپ فوری", "adm:do_backup")],
            [primary(f"{E.REFRESH} بازسازی تامب‌ها", "adm:rebuild")],
            [back_btn(lang, "adm:panel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:do_backup")
async def cb_do_backup(cb: CallbackQuery):
    if not await _is_owner(cb.from_user.id):
        await cb.answer("فقط مالک", show_alert=True)
        return
    await cb.answer("شروع شد", show_alert=False)

    try:
        from admin.backup import create_and_send_backup
        await create_and_send_backup(cb.from_user.id, "manual")
    except Exception as e:
        await cb.message.answer(f"{E.CROSS} خطا در بکاپ: {e}")


# ─────────── noop
@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery):
    await cb.answer()
