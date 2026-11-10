"""گردونه شانس — انتخاب تعداد برنده با دکمه inline (بدون FSM)"""

import random
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb
from . import state

router = Router(name="gardone")


def _counts_kb(uid: int):
    rows = []
    for base in (1, 6):
        rows.append([
            primary(str(n), f"gardone_setup_{uid}_{n}")
            for n in range(base, base + 5)
        ])
    return kb(rows)


def _render(game, lang):
    gid = game["game_id"]
    starter = game["starter_admin_id"]
    parts = game["participants"]
    plist = "\n".join(f"👤 {p['name']}" for p in parts) if parts else t("gardone_nobody", lang)
    winners_n = game.get("winner_count", 1)
    text = (
        f"{E.TARGET}{E.PARTY} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{t('gardone_active', lang)}\n"
        f"{E.INFO} {t('gardone_winner_count', lang, n=winners_n)}\n\n"
        f"<b>{t('gardone_participants', lang, n=len(parts))}:</b>\n{plist}"
    )
    rows = [
        [success(f"{E.CHECK} {t('gardone_join', lang)}", f"gardone_join_{gid}")],
        [primary(f"{E.TARGET} {t('gardone_spin', lang)}", f"gardone_spin_{gid}_{starter}")],
        [danger(f"{E.CROSS} {t('gardone_cancel', lang)}", f"gardone_cancel_{gid}_{starter}")],
    ]
    return text, kb(rows)


@router.callback_query(F.data.startswith("gardone_start_"))
async def start(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try:
        target = int(cb.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("❌", show_alert=True); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    try:
        member = await cb.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await cb.answer(t("admin_only", lang), show_alert=True); return

    if state.active_games["gardone"].get(chat_id):
        await cb.answer(t("game_already_running", lang), show_alert=True); return

    await cb.answer()
    await cb.message.edit_text(
        f"{E.TARGET}{E.PARTY} <b>{t('gardone_title', lang)}</b>\n\n"
        f"{E.INFO} {t('gardone_ask_count', lang)}",
        reply_markup=_counts_kb(uid),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("gardone_setup_"))
async def setup(cb: CallbackQuery):
    import logging
    log = logging.getLogger("gardone")
    
    try:
        if not cb.message or not getattr(cb.message, "chat", None):
            await cb.answer("❌ پیام نامعتبر", show_alert=True)
            return
        
        parts = cb.data.split("_")
        try:
            uid_target = int(parts[2])
            count = int(parts[3])
        except (ValueError, IndexError):
            await cb.answer("❌", show_alert=True)
            return
        
        uid = cb.from_user.id
        lang = get_user_lang(uid)
        chat_id = cb.message.chat.id
        
        log.info(f"🎡 gardone_setup: user={uid} target={uid_target} count={count} chat={chat_id}")
        
        if uid != uid_target:
            await cb.answer(t("not_your_panel", lang), show_alert=True)
            return
        if not (1 <= count <= 10):
            await cb.answer("❌", show_alert=True)
            return
        if state.active_games["gardone"].get(chat_id):
            log.warning(f"gardone already running: chat={chat_id}")
            await cb.answer(t("game_already_running", lang), show_alert=True)
            return
        
        await cb.answer()
        gid = cb.message.message_id
        game = {
            "game_id": gid, "starter_admin_id": uid,
            "participants": [], "winner_count": count,
        }
        state.register("gardone", chat_id, gid, game)
        log.info(f"✅ gardone registered: chat={chat_id} gid={gid} count={count}")
        
        try:
            text, markup = _render(game, lang)
        except Exception as e:
            log.exception(f"gardone render fail: {e}")
            await cb.message.answer(f"⚠️ خطای رندر: {e}")
            state.unregister("gardone", chat_id, gid)
            return
        
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            log.info(f"✅ gardone setup edited: gid={gid}")
        except Exception as e:
            log.warning(f"edit_text failed: {e} — trying answer")
            try:
                await cb.message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)
                log.info(f"✅ gardone setup answered: gid={gid}")
            except Exception as e2:
                log.error(f"❌ both failed: {e2}")
                await cb.answer(f"⚠️ {e2}", show_alert=True)
    
    except Exception as e:
        log.exception(f"❌ gardone setup crash: {e}")
        try:
            await cb.answer(f"⚠️ {e}", show_alert=True)
        except Exception:
            pass


@router.callback_query(F.data.startswith("gardone_join_"))
async def join(cb: CallbackQuery):
    try:
        gid = int(cb.data.split("_")[2])
    except (ValueError, IndexError):
        await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("gardone", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if any(p["id"] == uid for p in game["participants"]):
        await cb.answer(t("gardone_already_joined", lang), show_alert=True); return
    game["participants"].append({"id": uid, "name": cb.from_user.first_name})
    await cb.answer(t("gardone_joined", lang))
    text, markup = _render(game, lang)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("gardone_spin_"))
async def spin(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, starter = int(parts[2]), int(parts[3])
    except (ValueError, IndexError):
        await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("gardone", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if uid != starter:
        await cb.answer(t("gardone_only_starter", lang), show_alert=True); return
    if not game["participants"]:
        await cb.answer(t("gardone_empty", lang), show_alert=True); return

    await cb.answer(t("gardone_spinning", lang))
    winners_n = min(game["winner_count"], len(game["participants"]))
    shuffled = random.sample(game["participants"], len(game["participants"]))
    winners = shuffled[:winners_n]

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, w in enumerate(winners):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} <b>{w['name']}</b>")
    winner_text = "\n".join(lines)

    text = (
        f"{E.PARTY}{E.TROPHY} <b>{t('gardone_winner', lang)}</b>\n\n"
        f"{winner_text}"
    )
    await cb.message.edit_text(text, reply_markup=None, parse_mode=ParseMode.HTML)
    state.unregister("gardone", chat_id, gid)


@router.callback_query(F.data.startswith("gardone_cancel_"))
async def cancel(cb: CallbackQuery):
    parts = cb.data.split("_")
    try:
        gid, starter = int(parts[2]), int(parts[3])
    except (ValueError, IndexError):
        await cb.answer("❌"); return
    chat_id, uid = cb.message.chat.id, cb.from_user.id
    lang = get_user_lang(uid)
    game = state.get("gardone", chat_id, gid)
    if not game:
        await cb.answer(t("game_expired", lang), show_alert=True); return
    if uid != starter:
        await cb.answer(t("gardone_only_starter", lang), show_alert=True); return
    state.unregister("gardone", chat_id, gid)
    await cb.answer()
    await cb.message.edit_text(f"{E.CROSS} {t('gardone_cancelled', lang)}")
