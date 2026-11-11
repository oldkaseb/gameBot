# -*- coding: utf-8 -*-
"""گردونه شانس حرفه‌ای گروهی با مدیریت دستی اعضا و مینی‌اپ انیمیشنی"""

import asyncio
import html
import os
import random
import time
from urllib.parse import urlencode

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import primary, success, danger, kb
from database import db

router = Router(name="gardone")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

active_gardones: dict[int, dict] = {}


def _safe(name: str) -> str:
    return html.escape(name or "کاربر")


def _render_gardone_card(g: dict, lang: str) -> tuple[str, list]:
    host_id = g["host_id"]
    parts = list(g["participants"].values())
    p_lines = "\n".join(
        f"  {idx}. {E.USER} <b>{_safe(p['name'])}</b> (@{p['username']})" if p['username']
        else f"  {idx}. {E.USER} <b>{_safe(p['name'])}</b>"
        for idx, p in enumerate(parts, 1)
    ) if parts else f"  {E.INFO} هنوز کسی وارد نشده است."

    text = (
        f"{E.TARGET}{E.SPARK} <b>گردونه و قرعه‌کشی شانس راینو</b>\n\n"
        f"{E.CROWN} برگزارکننده: <b>{_safe(g['host_name'])}</b>\n"
        f"{E.PEOPLE} تعداد کل شرکت‌کنندگان: <b>{len(parts)} نفر</b>\n\n"
        f"<b>لیست اسامی:</b>\n{p_lines}\n\n"
        f"{E.INFO} <i>راهنما برای برگزارکننده:</i>\n"
        f"برای اضافه کردن دستی: <code>+username</code>\n"
        f"برای حذف کردن کاربر: <code>-username</code>"
    )

    rows = [
        [success(f"{E.PLUS} شرکت در قرعه‌کشی", "gjoin_click")],
        [
            primary(f"{E.DICE} شروع قرعه‌کشی", f"gspin_ask_{host_id}"),
            danger(f"{E.CROSS} لغو گردونه", f"gspin_cancel_{host_id}")
        ]
    ]
    return text, rows


@router.callback_query(F.data.startswith("gardone_start_"))
async def start_gardone_lobby(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    if chat_id in active_gardones:
        await cb.answer("یک گردونه فعال در گروه وجود دارد!", show_alert=True)
        return

    active_gardones[chat_id] = {
        "host_id": uid,
        "host_name": cb.from_user.first_name or "Host",
        "chat_id": chat_id,
        "msg_id": cb.message.message_id,
        "status": "collecting",
        "participants": {
            uid: {
                "id": uid,
                "name": cb.from_user.first_name or "Host",
                "username": cb.from_user.username or "",
            }
        },
        "created_at": time.time()
    }
    await cb.answer()
    txt, rows = _render_gardone_card(active_gardones[chat_id], lang)
    await cb.message.edit_text(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "gjoin_click")
async def join_gardone(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    g = active_gardones.get(chat_id)
    if not g or g["status"] != "collecting":
        await cb.answer("گردونه منقضی یا تمام شده است.", show_alert=True)
        return

    if uid in g["participants"]:
        await cb.answer("شما قبلاً ثبت شدید!", show_alert=True)
        return

    g["participants"][uid] = {
        "id": uid,
        "name": cb.from_user.first_name or f"User_{uid}",
        "username": cb.from_user.username or "",
    }
    await cb.answer("نام شما در قرعه‌کشی ثبت شد!")
    txt, rows = _render_gardone_card(g, lang)
    try:
        await cb.message.edit_text(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.message(F.text.regexp(r"^[\+\-][a-zA-Z0-9_]{3,}$"))
async def modify_gardone_members(msg: Message):
    chat_id = msg.chat.id
    g = active_gardones.get(chat_id)
    if not g or g["status"] != "collecting" or msg.from_user.id != g["host_id"]:
        return

    cmd = msg.text[0]
    username = msg.text[1:].lstrip("@").lower()

    if cmd == "+":
        uid_rand = int(time.time() * 1000) % 10000000
        g["participants"][uid_rand] = {
            "id": uid_rand,
            "name": username,
            "username": username,
        }
        await msg.reply(f"{E.CHECK} کاربر @{username} دستی اضافه شد.")
    elif cmd == "-":
        to_del = [k for k, v in g["participants"].items() if v["username"].lower() == username]
        if to_del:
            for k in to_del:
                del g["participants"][k]
            await msg.reply(f"{E.CROSS} کاربر @{username} حذف شد.")
        else:
            await msg.reply(f"{E.WARN} کاربری با این یوزرنیم پیدا نشد.")

    txt, rows = _render_gardone_card(g, "fa")
    try:
        await msg.bot.edit_message_text(
            text=txt,
            chat_id=chat_id,
            message_id=g["msg_id"],
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("gspin_ask_"))
async def ask_winner_count(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    g = active_gardones.get(chat_id)

    if not g or g["status"] != "collecting":
        await cb.answer("گردونه فعال نیست.", show_alert=True)
        return

    if uid != g["host_id"]:
        await cb.answer("فقط برگزارکننده اجازه شروع دارد!", show_alert=True)
        return

    total = len(g["participants"])
    if total < 1:
        await cb.answer("حداقل یک شرکت‌کننده نیاز است!", show_alert=True)
        return

    g["status"] = "waiting_count"
    await cb.answer()

    counts = [1, 2, 3, 5, 10]
    c_btns = [primary(f"{E.TROPHY} {c} برنده", f"gspin_go_{c}") for c in counts if c <= total]
    if not c_btns:
        c_btns = [primary(f"{E.TROPHY} 1 برنده", "gspin_go_1")]

    row1 = c_btns[:3]
    row2 = c_btns[3:]
    kb_rows = [r for r in [row1, row2] if r]
    kb_rows.append([danger(f"{E.CROSS} لغو", f"gspin_cancel_{uid}")])

    await cb.message.edit_text(
        f"{E.TROPHY} <b>تعیین تعداد برندگان</b>\n\n"
        f"شرکت‌کنندگان فعلی: <b>{total} نفر</b>\n"
        f"چند نفر در این قرعه‌کشی برنده اعلام شوند؟",
        reply_markup=kb(kb_rows),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("gspin_go_"))
async def launch_gardone_app(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    g = active_gardones.get(chat_id)

    if not g or uid != g["host_id"]:
        await cb.answer("خطای دسترسی!", show_alert=True)
        return

    count = int(cb.data.split("_")[2])
    g["winner_count"] = count
    g["status"] = "spinning"

    names = [p["name"] for p in g["participants"].values()]
    random.shuffle(names)
    winners = names[:count]
    g["winners"] = winners

    session_id = f"g_{abs(chat_id)}_{int(time.time())}"
    params = urlencode({
        "game": "gardone_anim",
        "session": session_id,
        "names": ",".join(names),
        "winners": ",".join(winners),
        "count": count
    })
    app_url = f"{MINI_APP_URL}/?{params}"

    web_btn = primary(f"{E.PLAY} ورود به سالن قرعه‌کشی زنده (انیمیشن)", web_app_url=app_url)
    finish_btn = success(f"{E.CHECK} ثبت و اعلام نتایج رسمی", f"gspin_finish_{chat_id}")

    await cb.message.edit_text(
        f"{E.SPARK}{E.PARTY} <b>قرعه‌کشی آغاز شد!</b>\n\n"
        f"{E.TROPHY} تعداد برندگان: <b>{count} نفر</b>\n"
        f"{E.HOURGLASS} با زدن دکمه زیر می‌توانید انیمیشن رنگی چرخش اسامی را در مینی‌اپ تماشا کنید.\n\n"
        f"پس از اتمام تماشا، دکمه اعلام نتایج را بزنید.",
        reply_markup=kb([[web_btn], [finish_btn]]),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("gspin_finish_"))
async def finalize_gardone(cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[2])
    g = active_gardones.get(chat_id)
    if not g:
        await cb.answer("این قرعه‌کشی به اتمام رسیده است.", show_alert=True)
        return

    winners = g.get("winners", [])
    host_id = g["host_id"]

    w_text = "\n".join(f"  🥇 نفر {i}: <b>{_safe(w)}</b>" for i, w in enumerate(winners, 1))
    summary = (
        f"{E.TROPHY}{E.PARTY} <b>نتایج نهایی قرعه‌کشی راینو</b>\n\n"
        f"<b>برندگان خوش‌شانس:</b>\n{w_text}\n\n"
        f"{E.USER} با تشکر از برگزارکننده: <b>{_safe(g['host_name'])}</b>\n"
        f"{E.PEOPLE} کل شرکت‌کنندگان: {len(g['participants'])} نفر"
    )

    await cb.message.edit_text(summary, reply_markup=None, parse_mode=ParseMode.HTML)

    # ارسال برندگان به پیوی درخواست‌کننده به ترتیب
    try:
        await cb.bot.send_message(
            host_id,
            f"{E.TROPHY} <b>لیست برندگان قرعه‌کشی گروه:</b>\n\n{w_text}",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    active_gardones.pop(chat_id, None)
    await cb.answer("نتایج با موفقیت ثبت و ارسال شد.")


@router.callback_query(F.data.startswith("gspin_cancel_"))
async def cancel_gardone(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    g = active_gardones.get(chat_id)
    if g and (uid == g["host_id"] or await db.is_admin(uid)):
        active_gardones.pop(chat_id, None)
        await cb.message.edit_text(f"{E.CROSS} گردونه لغو شد.", reply_markup=None)
    else:
        await cb.answer("شما دسترسی لغو این گردونه را ندارید.", show_alert=True)
