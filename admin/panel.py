# -*- coding: utf-8 -*-
"""admin/panel.py — پنل فرماندهی مینی‌اپ + سیستم ارسال همگانی در پیوی با حفظ ۱۰۰٪ ایموجی‌های پریمیوم"""

import asyncio
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from emojis import E
from utils.premium import primary, success, danger, kb

router = Router(name="admin_panel")
OWNER_IDS = {7662192190, 6041119040}
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


class BroadcastStates(StatesGroup):
    waiting_message = State()
    waiting_button = State()
    waiting_confirm = State()


def _admin_miniapp_kb(uid: int):
    url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    return kb([
        [success(f"{E.CROWN} ورود به مینی‌اپ فرماندهی کل ربات", web_app_url=url)],
        [
            primary(f"{E.SPARK} ارسال همگانی به کاربران (با ایموجی پریمیوم)", "adm:bc_users"),
            primary(f"{E.PEOPLE} ارسال همگانی به گروه‌ها", "adm:bc_groups"),
        ],
    ])


@router.message(Command("admin"))
@router.message(Command("panel"))
@router.message(F.text.in_({"پنل", "ادمین", "پنل مدیریت", "مدیریت"}))
async def cmd_admin_panel(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return
    await state.clear()
    await msg.answer(
        f"{E.CROWN}{E.SPARK} <b>فرماندهی و مدیریت کل ربات راینو</b>\n\n"
        f"• برای مدیریت گرافیکی کاربران، طبقات برج، کانال‌ها و گروه‌ها وارد مینی‌اپ شوید.\n"
        f"• برای <b>ارسال همگانی همراه با ایموجی‌های پریمیوم تلگرام</b>، از دو دکمه زیر در همین پیوی استفاده کنید:",
        reply_markup=_admin_miniapp_kb(msg.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text.in_({"همگانی", "ارسال همگانی", "/broadcast"}))
async def cmd_quick_broadcast(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return
    await state.clear()
    await msg.answer(
        f"{E.SPARK} <b>ارسال همگانی با پشتیبانی کامل از ایموجی پریمیوم</b>\n\n"
        f"مقصد ارسال همگانی را انتخاب کنید:",
        reply_markup=kb([
            [primary(f"{E.USER} ارسال به تمام کاربران (پیوی)", "adm:bc_users")],
            [primary(f"{E.PEOPLE} ارسال به تمام گروه‌ها", "adm:bc_groups")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.in_({"adm:bc_users", "adm:bc_groups"}))
async def cb_start_broadcast_pm(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        await cb.answer("⛔ فقط مالک دسترسی دارد!", show_alert=True)
        return
    target_type = "users" if cb.data == "adm:bc_users" else "groups"
    await state.set_state(BroadcastStates.waiting_message)
    await state.update_data(target_type=target_type)
    await cb.answer()

    target_lbl = "تمام کاربران ربات" if target_type == "users" else "تمام گروه‌های ربات"
    await cb.message.answer(
        f"📝 <b>مرحله ۱ از ۳ — ارسال همگانی به ({target_lbl})</b>\n\n"
        f"لطفاً پیامی که می‌خواهید ارسال شود را همین‌جا بفرستید:\n"
        f"✅ <i>می‌تواند شامل هرگونه <b>ایموجی پریمیوم تلگرام</b>، تگ‌های <code>[E:...]</code>، عکس، ویدیو، گیف یا متن فرمت‌دار باشد.</i>",
        reply_markup=kb([[danger("❌ انصراف", "adm:bc_cancel")]]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:bc_cancel")
async def cb_cancel_broadcast(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        return
    await state.clear()
    await cb.answer("لغو شد.")
    await cb.message.edit_text(
        f"{E.CROSS} عملیات ارسال همگانی لغو شد.",
        reply_markup=_admin_miniapp_kb(cb.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.message(StateFilter(BroadcastStates.waiting_message))
async def msg_receive_broadcast_content(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return

    # ذخیره آیدی پیام و چت برای کپی دقیق (حفظ کامل custom_emoji_entities و رسانه)
    await state.update_data(
        src_chat_id=msg.chat.id,
        src_msg_id=msg.message_id,
        raw_text=msg.html_text or msg.text or msg.caption or "",
        has_shortcode=("[E:" in (msg.text or msg.caption or "")),
    )
    await state.set_state(BroadcastStates.waiting_button)
    await msg.reply(
        f"🔘 <b>مرحله ۲ از ۳ — افزودن دکمه شیشه‌ای (اختیاری)</b>\n\n"
        f"اگر می‌خواهید زیر پیام دکمه شیشه‌ای لینک‌دار قرار بگیرد، به این فرمت بفرستید:\n"
        f"<code>متن دکمه | https://t.me/...</code>\n\n"
        f"یا اگر بدون دکمه می‌خواهید ارسال شود، روی دکمه زیر بزنید:",
        reply_markup=kb([
            [success("⏭️ بدون دکمه (ادامه به پیش‌نمایش)", "adm:bc_nobtn")],
            [danger("❌ انصراف", "adm:bc_cancel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(StateFilter(BroadcastStates.waiting_button), F.data == "adm:bc_nobtn")
async def cb_broadcast_no_button(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        return
    await state.update_data(btn_text="", btn_url="")
    await state.set_state(BroadcastStates.waiting_confirm)
    await cb.answer()
    await _send_broadcast_preview(cb.message, state)


@router.message(StateFilter(BroadcastStates.waiting_button), F.text)
async def msg_broadcast_button(msg: Message, state: FSMContext):
    if msg.from_user.id not in OWNER_IDS:
        return
    parts = [p.strip() for p in msg.text.split("|", 1)]
    if len(parts) < 2 or not parts[1].startswith("http"):
        await msg.reply("⚠️ فرمت نادرست است! به صورت <code>متن | https://...</code> بفرستید یا دکمه «بدون دکمه» را بزنید.", parse_mode=ParseMode.HTML)
        return
    await state.update_data(btn_text=parts[0], btn_url=parts[1])
    await state.set_state(BroadcastStates.waiting_confirm)
    await _send_broadcast_preview(msg, state)


async def _send_broadcast_preview(msg_obj: Message, state: FSMContext):
    data = await state.get_data()
    btn_text = data.get("btn_text")
    btn_url = data.get("btn_url")
    preview_kb = kb([[primary(btn_text, url=btn_url)]]) if (btn_text and btn_url) else None

    # نمایش پیش‌نمایش دقیق پیام همراه با ایموجی پریمیوم به مالک
    try:
        if data.get("has_shortcode"):
            await msg_obj.bot.send_message(
                chat_id=msg_obj.chat.id,
                text=data["raw_text"],
                reply_markup=preview_kb,
                parse_mode=ParseMode.HTML,
            )
        else:
            await msg_obj.bot.copy_message(
                chat_id=msg_obj.chat.id,
                from_chat_id=data["src_chat_id"],
                message_id=data["src_msg_id"],
                reply_markup=preview_kb,
            )
    except Exception:
        pass

    target_lbl = "تمام کاربران (پیوی)" if data.get("target_type") == "users" else "تمام گروه‌ها"
    await msg_obj.answer(
        f"👁️ <b>پیش‌نمایش پیام همگانی بالا آماده است!</b>\n"
        f"🎯 مقصد: <b>{target_lbl}</b>\n\n"
        f"آیا ارسال همگانی آغاز شود؟",
        reply_markup=kb([
            [success("🚀 بله، ارسال همگانی شروع شود", "adm:bc_confirm")],
            [danger("❌ لغو ارسال", "adm:bc_cancel")],
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(StateFilter(BroadcastStates.waiting_confirm), F.data == "adm:bc_confirm")
async def cb_execute_broadcast(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        return
    data = await state.get_data()
    await state.clear()
    await cb.answer("ارسال همگانی آغاز شد!")

    target_type = data.get("target_type", "users")
    btn_text = data.get("btn_text")
    btn_url = data.get("btn_url")
    send_kb = kb([[primary(btn_text, url=btn_url)]]) if (btn_text and btn_url) else None

    await db.ensure_pool()
    if target_type == "groups":
        rows = await db.pool.fetch("SELECT chat_id AS id FROM groups")
    else:
        rows = await db.pool.fetch("SELECT user_id AS id FROM users")

    targets = [r["id"] for r in rows]
    status_msg = await cb.message.edit_text(
        f"⏳ در حال ارسال پیام همگانی (با ایموجی پریمیوم) به <b>{len(targets)}</b> مقصد...",
        parse_mode=ParseMode.HTML,
    )

    sent_ok, sent_fail = 0, 0
    for tid in targets:
        try:
            if data.get("has_shortcode"):
                await cb.bot.send_message(
                    chat_id=tid,
                    text=data["raw_text"],
                    reply_markup=send_kb,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await cb.bot.copy_message(
                    chat_id=tid,
                    from_chat_id=data["src_chat_id"],
                    message_id=data["src_msg_id"],
                    reply_markup=send_kb,
                )
            sent_ok += 1
        except Exception:
            sent_fail += 1
        await asyncio.sleep(0.04)

    await status_msg.edit_text(
        f"🏁 <b>ارسال همگانی با موفقیت به پایان رسید!</b>\n\n"
        f"✅ ارسال موفق: <b>{sent_ok}</b>\n"
        f"❌ ناموفق / بلاک‌شده: <b>{sent_fail}</b>",
        reply_markup=_admin_miniapp_kb(cb.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:"))
async def cb_admin_panel(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in OWNER_IDS:
        await cb.answer("⛔ فقط مالک ربات دسترسی دارد!", show_alert=True)
        return
    await state.clear()
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"{E.CROWN}{E.SPARK} <b>فرماندهی و مدیریت کل ربات راینو</b>\n\n"
            f"برای مدیریت کامل ربات یا ارسال همگانی با ایموجی پریمیوم، گزینه مورد نظر را انتخاب کنید:",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await cb.message.answer(
            f"{E.CROWN} <b>فرماندهی کل ربات:</b>",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
