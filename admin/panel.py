# -*- coding: utf-8 -*-
"""admin/panel.py — دریافت پیام همگانی، دریافت خودکار ایموجی‌های پریمیوم (برای نشان VIP کاربر، گیفت، چت و روابط) و دستور ریست لول و موجودی"""

import json
import os
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, BaseFilter

from emojis import E, render_emojis
from utils.premium import success, danger, kb
from database import db
from social_platform import (
    get_sp_config,
    set_sp_config,
    reset_all_levels_and_balances,
    ensure_social_tables,
)

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


class IsWaitingEmojiCaptureFilter(BaseFilter):
    """بررسی اینکه آیا کاربر یا مالک در حال فرستادن ایموجی پریمیوم به پیوی ربات است یا خیر"""
    async def __call__(self, msg: Message) -> bool:
        if not msg.from_user or msg.chat.type != ChatType.PRIVATE:
            return False
        try:
            mode = await get_sp_config(f"user_emoji_wait_{msg.from_user.id}", "")
            return bool(mode)
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


# ─── ۱. دستور «ریست لول و موجودی» برای مالک ربات ───
@router.message(F.text.in_({"ریست لول و موجودی", "/reset_all", "ریست کل"}))
async def cmd_reset_all_platform(msg: Message):
    if not msg.from_user or msg.from_user.id not in OWNER_IDS:
        return
    await reset_all_levels_and_balances()
    await msg.reply(
        "♻️ <b>ریست کامل انجام شد!</b>\n\n"
        "✅ موجودی سکه و استارز تمام کاربران صفر شد.\n"
        "✅ لول‌های ثروت و جذابیت تمام کاربران به لول ۱ برگشت.\n"
        "✅ دیتابیس اتاق‌های صوتی و لول روم‌ها کاملاً ریست شد.",
        parse_mode=ParseMode.HTML,
    )


# ─── ۲. دریافت خودکار ایموجی پریمیوم متحرک از کاربر (برای نشان جلوی اسم) یا از مالک (برای گیفت، پک چت و خط رابط) ───
@router.message(IsWaitingEmojiCaptureFilter())
async def capture_custom_emoji_from_pm(msg: Message):
    uid = msg.from_user.id
    mode = await get_sp_config(f"user_emoji_wait_{uid}", "")
    await set_sp_config(f"user_emoji_wait_{uid}", "")

    if msg.text and msg.text.strip() in ("/cancel", "لغو", "انصراف"):
        await msg.reply("❌ عملیات لغو شد.")
        return

    await ensure_social_tables()
    raw_text = (msg.text or msg.caption or "").strip()
    ents = (msg.entities or []) + (msg.caption_entities or [])
    custom_ent = next((e for e in ents if e.type == "custom_emoji"), None)

    custom_emoji_id = ""
    unicode_char = "✨"

    if custom_ent:
        custom_emoji_id = str(custom_ent.custom_emoji_id)
        try:
            unicode_char = raw_text[custom_ent.offset : custom_ent.offset + custom_ent.length] or "✨"
        except Exception:
            unicode_char = "✨"
    elif raw_text.isdigit() and len(raw_text) >= 15:
        custom_emoji_id = raw_text
    elif raw_text:
        unicode_char = raw_text[:4]

    if mode == "badge":
        await db.pool.execute(
            "UPDATE sp_profiles SET custom_badge_emoji_id=$1, custom_badge_icon=$2 WHERE user_id=$3",
            custom_emoji_id, unicode_char, uid
        )
        await msg.reply(
            f"✅ <b>نشان اختصاصی شما ثبت شد!</b>\n"
            f"آیدی ایموجی پریمیوم: <code>{custom_emoji_id or 'ایموجی استاندارد'}</code>\n"
            f"اکنون در مینی‌اپ جلوی نام شما به صورت متحرک نمایش داده می‌شود.",
            reply_markup=kb([[success("👤 بازگشت به پروفایل در مینی‌اپ", web_app_url=f"{MINI_APP_URL}/?game=sp_profile&uid={uid}")]]),
            parse_mode=ParseMode.HTML,
        )
        return

    # حالت‌های مدیریتی مالک ربات
    if uid in OWNER_IDS:
        await set_sp_config("last_captured_emoji_id", custom_emoji_id)
        await set_sp_config("last_captured_emoji_icon", unicode_char)

        if mode == "adm_rel_marriage":
            await set_sp_config("default_marriage_emoji_id", custom_emoji_id)
            await set_sp_config("default_marriage_icon", unicode_char)
        elif mode == "adm_rel_bestie":
            await set_sp_config("default_bestie_emoji_id", custom_emoji_id)
            await set_sp_config("default_bestie_icon", unicode_char)
        elif mode == "adm_chat_pack":
            raw_packs = await get_sp_config("chat_emoji_packs", "[]")
            try:
                packs = json.loads(raw_packs)
            except Exception:
                packs = []
            for e in ents:
                if e.type == "custom_emoji":
                    packs.append({"id": str(e.custom_emoji_id), "icon": unicode_char})
            if not ents and custom_emoji_id:
                packs.append({"id": custom_emoji_id, "icon": unicode_char})
            await set_sp_config("chat_emoji_packs", json.dumps(packs[-40:]))

        await msg.reply(
            f"✅ <b>ایموجی پریمیوم با موفقیت دریافت و ذخیره شد!</b>\n"
            f"🔢 آیدی ایموجی: <code>{custom_emoji_id or 'ندارد'}</code>\n"
            f"حالا وارد پنل مدیریت مینی‌اپ شوید؛ این آیدی به طور خودکار در فیلد مربوطه قرار گرفته است:",
            reply_markup=_admin_miniapp_kb(uid),
            parse_mode=ParseMode.HTML,
        )


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
            await msg.bot.send_message(chat_id=msg.chat.id, text=full_html, parse_mode=ParseMode.HTML)
        else:
            await msg.bot.copy_message(chat_id=msg.chat.id, from_chat_id=msg.chat.id, message_id=msg.message_id)
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
        f"تمام بخش‌های مدیریتی ربات، لیست کامل کاربران، ارسال همگانی، فروشگاه، ایموجی‌های پریمیوم و تغییر عکس‌های مینی‌اپ در پنل زیر قرار دارند:",
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
