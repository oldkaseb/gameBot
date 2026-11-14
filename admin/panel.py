# -*- coding: utf-8 -*-
"""admin/panel.py — هدایت مالک به مینی‌اپ فرماندهی + دریافت پیام همگانی با ایموجی پریمیوم در پیوی"""

import json
import os
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, BaseFilter

from emojis import E, render_emojis
from utils.premium import success, danger, kb
from social_platform import get_sp_config, set_sp_config

router = Router(name="admin_panel")
OWNER_IDS = {7662192190, 6041119040}
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")


class IsWaitingBroadcastFilter(BaseFilter):
    async def __call__(self, msg: Message) -> bool:
        if not msg.from_user or msg.from_user.id not in OWNER_IDS:
            return False
        if msg.chat.type != ChatType.PRIVATE:
            return False
        try:
            waiting = await get_sp_config(f"bc_waiting_{msg.from_user.id}", "0")
            return waiting == "1"
        except Exception:
            return False


def _admin_miniapp_kb(uid: int):
    url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    return kb([
        [success(f"{E.CROWN} ورود به مینی‌اپ فرماندهی کل پلتفرم", web_app_url=url)],
    ])


def _extract_html_with_custom_emojis(msg: Message) -> str:
    raw_html = getattr(msg, "html_text", None) or msg.text or msg.caption or ""
    if "[E:" in raw_html:
        try:
            raw_html = render_emojis(raw_html)
        except Exception:
            pass
    return raw_html


@router.message(IsWaitingBroadcastFilter())
async def capture_owner_broadcast_message(msg: Message):
    uid = msg.from_user.id

    if msg.text and msg.text.strip() in ("/cancel", "لغو", "انصراف"):
        await set_sp_config(f"bc_waiting_{uid}", "0")
        await msg.reply("❌ دریافت پیام همگانی لغو شد.", reply_markup=_admin_miniapp_kb(uid))
        return

    raw_plain = msg.text or msg.caption or ""
    full_html = _extract_html_with_custom_emojis(msg)
    has_shortcode = "[E:" in raw_plain

    all_ents = (msg.entities or []) + (msg.caption_entities or [])
    custom_emoji_count = sum(1 for ent in all_ents if ent.type == "custom_emoji")
    if has_shortcode:
        custom_emoji_count += raw_plain.count("[E:")

    short_summary = (raw_plain or "[رسانه / فایل / استیکر]")[:120]

    draft_data = {
        "src_chat_id": msg.chat.id,
        "src_msg_id": msg.message_id,
        "raw_html": full_html,
        "has_shortcode": has_shortcode,
        "custom_emoji_count": custom_emoji_count,
        "preview": f"{short_summary} ({custom_emoji_count} ایموجی پریمیوم)" if custom_emoji_count else short_summary,
        "saved_at": time.strftime("%H:%M:%S"),
    }

    await set_sp_config("bc_draft", json.dumps(draft_data))
    await set_sp_config(f"bc_waiting_{uid}", "0")

    try:
        if has_shortcode and msg.text:
            await msg.bot.send_message(
                chat_id=msg.chat.id,
                text=full_html,
                parse_mode=ParseMode.HTML,
            )
        else:
            await msg.bot.copy_message(
                chat_id=msg.chat.id,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id,
            )
    except Exception:
        pass

    admin_url = f"{MINI_APP_URL}/?game=tower_admin&uid={uid}"
    await msg.reply(
        f"{E.CHECK} <b>پیش‌نمایش واقعی پیام شما در بالا رندر شد!</b>\n"
        f"{E.SPARK} تعداد ایموجی پریمیوم ثبت‌شده: <b>{custom_emoji_count} عدد</b>\n\n"
        f"حالا روی دکمه زیر بزنید و از داخل مینی‌اپ ارسال نهایی را انجام دهید:",
        reply_markup=kb([
            [success("👑 بازگشت به مینی‌اپ و ارسال نهایی", web_app_url=admin_url)]
        ]),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("admin"))
@router.message(Command("panel"))
@router.message(F.text.in_({"پنل", "ادمین", "پنل مدیریت", "مدیریت"}))
async def cmd_admin_panel(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    await set_sp_config(f"bc_waiting_{msg.from_user.id}", "0")
    await msg.answer(
        f"{E.CROWN}{E.SPARK} <b>مینی‌اپ فرماندهی و مدیریت کل پلتفرم راینو</b>\n\n"
        f"تمام بخش‌های مدیریتی ربات، لیست کامل کاربران، ارسال همگانی، فروشگاه و تغییر عکس‌های مینی‌اپ در پنل زیر قرار دارند:",
        reply_markup=_admin_miniapp_kb(msg.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm:cancel_bc_capture")
async def cb_cancel_bc_capture(cb: CallbackQuery):
    if cb.from_user.id not in OWNER_IDS:
        return
    await set_sp_config(f"bc_waiting_{cb.from_user.id}", "0")
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
            f"{E.CROWN}{E.SPARK} <b>فرماندهی و مدیریت کل پلتفرم راینو</b>\n\n"
            f"برای ورود به پنل مدیریت کل روی دکمه زیر بزنید:",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await cb.message.answer(
            f"{E.CROWN} <b>فرماندهی کل ربات:</b>",
            reply_markup=_admin_miniapp_kb(cb.from_user.id),
            parse_mode=ParseMode.HTML,
        )
