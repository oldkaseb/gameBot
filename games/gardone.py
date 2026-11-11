# -*- coding: utf-8 -*-
"""گردونه شانس گروهی — عضوگیری، افزودن/حذف با یوزرنیم، انتخاب تعداد برنده و انیمیشن قرعه‌کشی"""

import html
import os
import random
import time

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode, ChatType

from emojis import E
from langs import t, get_user_lang
from utils.premium import primary, success, danger, kb
from database import db
from games.panel import make_miniapp_btn

router = Router(name="gardone")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://games.rhinokaseb.abrdns.com").rstrip("/")

active_gardones: dict[int, dict] = {}


def _safe(name: str) -> str:
    return html.escape(name or "کاربر")


def _fa_to_en(s: str) -> str:
    return (s or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


def _render_gardone_lobby(g: dict, lang: str) -> tuple[str, list]:
    host_id = g["host_id"]
    parts = list(g["participants"].values())
    if parts:
        p_lines = "\n".join(
            f"  {idx}. {E.USER} <b>{_safe(p['name'])}</b>" + (f" (@{p['username']})" if p.get("username") else "")
            for idx, p in enumerate(parts, 1)
        )
    else:
        p_lines = f"  {E.INFO} {t('gardone_nobody', lang)}"

    preview_url = f"{MINI_APP_URL}/?game=gardone_anim&chat={g['chat_id']}"
    text = (
        f"<a href='{preview_url}'>&#8205;</a>"
        f"{E.TARGET}{E.SPARK} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{E.CROWN} درخواست‌کننده: <b>{_safe(g['host_name'])}</b>\n"
        f"{E.PEOPLE} {t('gardone_participants', lang, n=len(parts))}:\n{p_lines}\n\n"
        f"{E.INFO} <i>افزودن/حذف کاربر توسط درخواست‌کننده با ارسال یوزرنیم:</i>\n"
        f"<code>+@username</code> یا <code>-@username</code>"
    )

    rows = [
        [success(f"{E.PLUS} {t('gardone_join', lang)}", "gjoin_btn")],
        [
            primary(f"{E.SPARK} شروع قرعه‌کشی", f"gspin_ask_{host_id}"),
            danger(f"{E.CROSS} {t('gardone_cancel', lang)}", f"gspin_cancel_{host_id}"),
        ],
    ]
    return text, rows


@router.callback_query(F.data.startswith("gardone_start_"))
async def gardone_start(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    parts = cb.data.split("_")
    try:
        host_id = int(parts[2])
    except (IndexError, ValueError):
        host_id = uid

    if uid != host_id:
        await cb.answer(t("not_your_panel", lang), show_alert=True)
        return

    active_gardones[chat_id] = {
        "host_id": uid,
        "host_name": cb.from_user.first_name or "Host",
        "chat_id": chat_id,
        "msg_id": cb.message.message_id,
        "is_pm": cb.message.chat.type == ChatType.PRIVATE,
        "status": "collecting",
        "winner_count": 1,
        "participants": {},
        "winners": [],
        "created_at": time.time(),
    }

    await cb.answer()
    txt, rows = _render_gardone_lobby(active_gardones[chat_id], lang)
    try:
        await cb.message.edit_text(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML, disable_web_page_preview=False)
    except Exception:
        sent = await cb.message.answer(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML, disable_web_page_preview=False)
        active_gardones[chat_id]["msg_id"] = sent.message_id


@router.callback_query(F.data == "gjoin_btn")
async def gardone_join(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)

    g = active_gardones.get(chat_id)
    if not g or g["status"] != "collecting":
        await cb.answer(t("game_not_active", lang), show_alert=True)
        return

    if str(uid) in g["participants"]:
        await cb.answer(t("gardone_already_joined", lang), show_alert=True)
        return

    g["participants"][str(uid)] = {
        "id": uid,
        "name": cb.from_user.first_name or f"User {uid}",
        "username": (cb.from_user.username or "").lstrip("@"),
    }
    await cb.answer(t("gardone_joined", lang))
    txt, rows = _render_gardone_lobby(g, get_user_lang(g["host_id"]))
    try:
        await cb.message.edit_text(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML, disable_web_page_preview=False)
    except Exception:
        pass


# افزودن یا حذف کاربر با یوزرنیم توسط درخواست‌کننده (+@user / -@user / @user)
@router.message(
    F.text,
    lambda m: (
        m.chat.id in active_gardones
        and active_gardones[m.chat.id]["status"] == "collecting"
        and active_gardones[m.chat.id]["host_id"] == m.from_user.id
        and (m.text.strip().startswith("+") or m.text.strip().startswith("-") or m.text.strip().startswith("@"))
    ),
)
async def gardone_manage_user_by_username(msg: Message):
    chat_id = msg.chat.id
    g = active_gardones.get(chat_id)
    raw = msg.text.strip()

    action = "+"
    if raw.startswith("-"):
        action = "-"
        raw = raw[1:].strip()
    elif raw.startswith("+"):
        raw = raw[1:].strip()

    uname = raw.lstrip("@").strip()
    if not uname or len(uname) < 3:
        return

    key = f"u_{uname.lower()}"
    if action == "+":
        g["participants"][key] = {
            "id": 0,
            "name": f"@{uname}",
            "username": uname,
        }
        await msg.reply(f"{E.CHECK} کاربر <b>@{_safe(uname)}</b> به گردونه اضافه شد.", parse_mode=ParseMode.HTML)
    else:
        removed = False
        for k in list(g["participants"].keys()):
            p = g["participants"][k]
            if p.get("username", "").lower() == uname.lower() or p.get("name", "").lstrip("@").lower() == uname.lower():
                del g["participants"][k]
                removed = True
        if removed:
            await msg.reply(f"{E.CROSS} کاربر <b>@{_safe(uname)}</b> از گردونه حذف شد.", parse_mode=ParseMode.HTML)
        else:
            await msg.reply(f"{E.WARN} کاربری با یوزرنیم @{_safe(uname)} در لیست نبود.", parse_mode=ParseMode.HTML)

    txt, rows = _render_gardone_lobby(g, get_user_lang(g["host_id"]))
    try:
        await msg.bot.edit_message_text(
            text=txt,
            chat_id=chat_id,
            message_id=g["msg_id"],
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("gspin_ask_"))
async def gardone_ask_winner_count(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    g = active_gardones.get(chat_id)

    if not g:
        await cb.answer(t("game_expired", lang), show_alert=True)
        return
    if uid != g["host_id"]:
        await cb.answer(t("gardone_only_starter", lang), show_alert=True)
        return
    if len(g["participants"]) < 1:
        await cb.answer(t("gardone_empty", lang), show_alert=True)
        return

    g["status"] = "asking_count"
    await cb.answer()

    max_w = min(10, len(g["participants"]))
    btns = [primary(f"{E.TROPHY} {i} نفر", f"gspin_run_{i}") for i in range(1, min(6, max_w + 1))]
    rows = [btns[:3]]
    if btns[3:]:
        rows.append(btns[3:])
    rows.append([danger(f"{E.ARROW} بازگشت به لابی", "gspin_back")])

    await cb.message.edit_text(
        f"{E.TROPHY}{E.SPARK} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{E.PEOPLE} شرکت‌کنندگان آماده: <b>{len(g['participants'])} نفر</b>\n"
        f"{E.INFO} {t('gardone_ask_count', lang)}",
        reply_markup=kb(rows),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "gspin_back")
async def gardone_back_to_lobby(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    if not g or cb.from_user.id != g["host_id"]:
        await cb.answer()
        return
    g["status"] = "collecting"
    await cb.answer()
    txt, rows = _render_gardone_lobby(g, get_user_lang(g["host_id"]))
    await cb.message.edit_text(txt, reply_markup=kb(rows), parse_mode=ParseMode.HTML, disable_web_page_preview=False)


@router.message(
    F.text,
    lambda m: (
        m.chat.id in active_gardones
        and active_gardones[m.chat.id]["status"] == "asking_count"
        and active_gardones[m.chat.id]["host_id"] == m.from_user.id
    ),
)
async def gardone_count_by_text(msg: Message):
    chat_id = msg.chat.id
    g = active_gardones.get(chat_id)
    raw = _fa_to_en(msg.text.strip())
    if not raw.isdigit():
        return
    cnt = int(raw)
    if not (1 <= cnt <= 10):
        await msg.reply(f"{E.WARN} عددی بین ۱ تا ۱۰ بفرستید.")
        return
    await _execute_gardone_draw(msg.bot, chat_id, cnt)


@router.callback_query(F.data.startswith("gspin_run_"))
async def gardone_count_by_btn(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    g = active_gardones.get(chat_id)
    if not g or cb.from_user.id != g["host_id"]:
        await cb.answer("فقط سازنده گردونه!", show_alert=True)
        return
    cnt = int(cb.data.split("_")[2])
    await cb.answer("قرعه‌کشی آغاز شد!")
    await _execute_gardone_draw(cb.bot, chat_id, cnt)


async def _execute_gardone_draw(bot, chat_id: int, count: int):
    g = active_gardones.get(chat_id)
    if not g:
        return

    players = list(g["participants"].values())
    win_count = min(count, len(players))
    winners = random.sample(players, win_count)
    g["winners"] = winners
    g["winner_count"] = win_count
    g["status"] = "finished"

    for w in winners:
        if w.get("id"):
            try:
                await db.add_win(int(w["id"]), "gardone")
            except Exception:
                pass

    start_param = f"gardone_anim__{chat_id}"
    preview_url = f"{MINI_APP_URL}/?game=gardone_anim&chat={chat_id}"

    winners_ordered = "\n".join(
        f"  {idx}. {E.TROPHY} <b>{_safe(w['name'])}</b>" + (f" (@{w['username']})" if w.get("username") else "")
        for idx, w in enumerate(winners, 1)
    )

    group_text = (
        f"<a href='{preview_url}'>&#8205;</a>"
        f"{E.PARTY}{E.TROPHY} <b>نتایج قرعه‌کشی گردونه شانس راینو</b>\n\n"
        f"{E.CROWN} برگزارکننده: <b>{_safe(g['host_name'])}</b>\n"
        f"{E.PEOPLE} کل شرکت‌کنندگان: <b>{len(players)} نفر</b>\n"
        f"{E.STAR} تعداد برندگان: <b>{win_count} نفر</b>\n\n"
        f"<b>لیست برندگان به ترتیب قرعه:</b>\n{winners_ordered}\n\n"
        f"{E.SPARK} برای تماشای انیمیشن چرخش گردونه و بیرون آمدن تک‌تک برندگان، روی دکمه زیر بزنید:"
    )

    rows = [
        [make_miniapp_btn(f"{E.PLAY} تماشای انیمیشن قرعه‌کشی در مینی‌اپ", start_param, g["is_pm"], success)],
    ]

    try:
        await bot.edit_message_text(
            text=group_text,
            chat_id=chat_id,
            message_id=g["msg_id"],
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
    except Exception:
        await bot.send_message(
            chat_id=chat_id,
            text=group_text,
            reply_markup=kb(rows),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )

    # ارسال لیست برندگان به ترتیب به پیوی درخواست‌کننده
    try:
        await bot.send_message(
            chat_id=g["host_id"],
            text=(
                f"{E.TROPHY}{E.SPARK} <b>گزارش قرعه‌کشی شما</b>\n\n"
                f"<b>برندگان به ترتیب قرعه ({win_count} نفر از {len(players)} نفر):</b>\n"
                f"{winners_ordered}"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("gspin_cancel_"))
async def gardone_cancel(cb: CallbackQuery):
    chat_id = cb.message.chat.id
    uid = cb.from_user.id
    g = active_gardones.get(chat_id)
    if not g:
        await cb.answer()
        return
    if uid != g["host_id"] and not await db.is_admin(uid):
        await cb.answer(t("gardone_only_starter", get_user_lang(uid)), show_alert=True)
        return
    active_gardones.pop(chat_id, None)
    await cb.answer()
    try:
        await cb.message.edit_text(f"{E.CROSS} گردونه شانس لغو شد.", parse_mode=ParseMode.HTML)
    except Exception:
        pass
