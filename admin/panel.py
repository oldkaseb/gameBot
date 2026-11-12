# -*- coding: utf-8 -*-
"""admin/panel.py — دریافت پیام حاوی ایموجی پریمیوم در پیوی و ذخیره برای تنظیمات و ارسال نهایی از داخل مینی‌اپ"""

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
        [success(f"{E.CROWN} ورود به مینی‌اپ فرماندهی کل ربات", web_app_url=url)],
    ])


@router.message(Command("admin"))
@router.message(Command("panel"))
@router.message(F.text.in_({"پنل", "ادمین", "پنل مدیریت", "مدیریت"}))
async def cmd_admin_panel(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    await set_dt_config(f"bc_waiting_{msg.from_user.id}", "0")
    await msg.answer(
        f"{E.CROWN}{E.SPARK} <b>مینی‌اپ فرماندهی و مدیریت کل ربات راینو</b>\n\n"
        f"تمام بخش‌های مدیریتی ربات، لیست کامل کاربران، ارسال همگانی و پنل برج شیاطین در مینی‌اپ زیر قرار دارند:",
        reply_markup=_admin_miniapp_kb(msg.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:cancel_bc_capture")
async def cb_cancel_bc_capture(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        return
    await set_dt_config(f"bc_waiting_{cb.from_user.id}", "0")
    await cb.answer("لغو شد.")
    await cb.message.edit_text(
        "❌ دریافت پیام همگانی لغو شد.",
        reply_markup=_admin_miniapp_kb(cb.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.message(
    F.chat.type == "private",
    lambda m: m.from_user and m.from_user.id in OWNER_IDS,
)
async def capture_owner_broadcast_message(msg: Message):
    """اگر مالک در مینی‌اپ دکمه «ثبت پیام در پیوی» را زده باشد، پیام ارسالی او (با ایموجی پریمیوم/عکس/ویدیو) ذخیره می‌شود"""
    uid = msg.from_user.id
    waiting = await get_dt_config(f"bc_waiting_{uid}", "0")
    if waiting != "1":
        return

    if msg.text and msg.text.strip() in ("/cancel", "لغو", "انصراف"):
        await set_dt_config(f"bc_waiting_{uid}", "0")
        await msg.reply("❌ دریافت پیام لغو شد.", reply_markup=_admin_miniapp_kb(uid))
        return

    preview_txt = (msg.text or msg.caption or "[رسانه / فایل / استیکر]")[:180]
    draft_data = {
        "src_chat_id": msg.chat.id,
        "src_msg_id": msg.message_id,
        "raw_html": msg.html_text or msg.text or msg.caption or "",
        "has_shortcode": ("[E:" in (msg.text or msg.caption or "")),
        "preview": preview_txt,
        "saved_at": time.strftime("%H:%M:%S"),
    }

    await set_dt_config("bc_draft", json.dumps(draft_data))
    await set_dt_config(f"bc_waiting_{uid}", "0")

    admin_url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    await msg.reply(
        f"✅ <b>پیام شما (به همراه ایموجی‌های پریمیوم و فرمت‌ها) با موفقیت ثبت شد!</b>\n\n"
        f"📌 پیش‌نمایش متن: <i>{preview_txt}</i>\n\n"
        f"حالا روی دکمه زیر بزنید تا در مینی‌اپ مقصد، دکمه شیشه‌ای و <b>ارسال نهایی</b> را انجام دهید:",
        reply_markup=kb([
            [success("👑 بازگشت به مینی‌اپ و ارسال نهایی", web_app_url=admin_url)]
        ]),
        parse_mode=ParseMode.HTML,
    )
