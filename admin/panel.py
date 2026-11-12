# -*- coding: utf-8 -*-
"""admin/panel.py — هدایت مستقیم مالک به مینی‌اپ جامع پنل مدیریت کل ربات و برج شیاطین"""

import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from utils.premium import success, kb

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
        f"تمام بخش‌های مدیریتی ربات (آمار، ارسال همگانی، کانال‌های عضویت اجباری، مدیریت گروه‌ها، مسدودسازی و پنل کامل برج شیاطین) به داخل مینی‌اپ اختصاصی منتقل شده‌اند:",
        reply_markup=_admin_miniapp_kb(msg.from_user.id),
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
            f"برای مدیریت کامل ربات، کانال‌های قفل اجباری، ارسال همگانی، گروه‌ها و برج شیاطین روی دکمه زیر بزنید:",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await cb.message.answer(
            f"{E.CROWN} <b>مینی‌اپ فرماندهی کل ربات:</b>",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
