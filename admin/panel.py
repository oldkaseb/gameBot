# -*- coding: utf-8 -*-
"""admin/panel.py — دریافت پیام همگانی (با ایموجی پریمیوم) در پیوی و ذخیره برای ارسال نهایی از مینی‌اپ"""

import json
import os
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from utils.premium import success, danger, kb
from games.demon_tower import get_dt_config, set_dt_config

router = Router(name="admin_panel")
OWNER_IDS = {7662192190, 6041119040}
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


def _admin_miniapp_kb(uid: int):
    url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    return kb([
        [success(f"{E.CROWN} ورود به مینی‌اپ فرماندهی کل ربات", web_app_url=url)]
    ])


@router.message(Command("admin"))
@router.message(Command("panel"))
@router.message(F.text.in_({"پنل", "ادمین", "پنل مدیریت", "مدیریت"}))
async def cmd_admin_panel(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    await msg.answer(
        f"{E.CROWN}{E.SPARK} <b>مینی‌اپ فرماندهی و مدیریت کل ربات راینو</b>\n\n"
        f"تمام بخش‌های مدیریتی ربات (آمار، ارسال همگانی، کانال‌های عضویت اجباری، مدیریت گروه‌ها، لیست کامل کاربران و پنل برج شیاطین) در مینی‌اپ زیر قرار دارند:",
        reply_markup=_admin_miniapp_kb(msg.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:cancel_bc_wait")
async def cb_cancel_bc_wait(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        return
    await set_dt_config("bc_waiting_owner", "0")
    await cb.answer("لغو شد.")
    await cb.message.edit_text(
        "❌ دریافت پیام همگانی لغو شد.",
        reply_markup=_admin_miniapp_kb(cb.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("adm:"))
async def cb_admin_panel(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        await cb.answer("⛔ فقط مالک ربات دسترسی دارد!", show_alert=True)
        return
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"{E.CROWN}{E.SPARK} <b>مینی‌اپ فرماندهی و مدیریت کل ربات راینو</b>\n\n"
            f"برای مدیریت کامل ربات روی دکمه زیر بزنید:",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await cb.message.answer(
            f"{E.CROWN} <b>مینی‌اپ فرماندهی کل ربات:</b>",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )


# هندلر دریافت پیام همگانی در پیوی مالک (وقتی از داخل مینی‌اپ دکمه ثبت متن در پیوی را زده باشد)
@router.message(F.chat.type == "private", F.from_user.id.in_(OWNER_IDS))
async def catch_owner_broadcast_draft(msg: Message):
    waiting_uid = await get_dt_config("bc_waiting_owner", "0")
    if waiting_uid != str(msg.from_user.id):
        return

    if msg.text and msg.text.strip() in ("/cancel", "لغو", "انصراف"):
        await set_dt_config("bc_waiting_owner", "0")
        await msg.reply("❌ دریافت پیام همگانی لغو شد.", reply_markup=_admin_miniapp_kb(msg.from_user.id))
        return

    preview_txt = (msg.text or msg.caption or "[رسانه / فایل / استیکر]")[:250]
    draft = {
        "src_chat_id": msg.chat.id,
        "src_msg_id": msg.message_id,
        "preview": preview_txt,
        "has_media": bool(msg.photo or msg.video or msg.animation or msg.document or msg.voice or msg.audio),
        "saved_at": time.strftime("%H:%M:%S"),
    }
    await set_dt_config("bc_draft", json.dumps(draft))
    await set_dt_config("bc_waiting_owner", "0")

    admin_url = f"{MINI_APP_URL}/?game=tower_admin&uid={msg.from_user.id}"
    await msg.reply(
        f"✅ <b>پیام همگانی شما (همراه با ایموجی‌های پریمیوم و فرمت کامل) دریافت و ذخیره شد!</b>\n\n"
        f"حالا وارد مینی‌اپ پنل مدیریت شوید تا مقصد (کاربران یا گروه‌ها) و دکمه شیشه‌ای را تنظیم کرده و <b>ارسال نهایی</b> را بزنید:",
        reply_markup=kb([
            [success("👑 بازگشت به مینی‌اپ برای تنظیمات و ارسال نهایی", web_app_url=admin_url)]
        ]),
        parse_mode=ParseMode.HTML,
    )
