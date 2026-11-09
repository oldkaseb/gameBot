"""بازی‌های ناشناس — قارچ و اعتراف"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.dispatcher.event.bases import SkipHandler

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, btn, cancel_btn, kb
from . import state
from .state import active_gharch

router = Router(name="anon")

OWNER_IDS = {7662192190, 6041119040}


class AnonStates(StatesGroup):
    ask_god = State()
    confirm_god = State()
    eteraf_custom = State()


# ══════════ قارچ
@router.callback_query(F.data.startswith("gharch_start_"))
async def gharch_start(cb: CallbackQuery, state_fsm: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except: await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    try:
        member = await cb.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await cb.answer(t("gharch_only_admin", lang), show_alert=True); return

    await cb.answer()
    await state_fsm.clear()
    await state_fsm.update_data(chat_id=chat_id, starter=uid, setup_msg=cb.message.message_id)
    await state_fsm.set_state(AnonStates.ask_god)
    await cb.message.edit_text(
        f"{E.MASK}{E.GHOST} <b>{t('gharch_choose_god', lang)}</b>",
        parse_mode=ParseMode.HTML,
    )


@router.message(AnonStates.ask_god, F.text)
async def gharch_got_god(msg: Message, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if msg.from_user.id != data.get("starter"):
        return
    uname = msg.text.strip()
    if not uname.startswith("@"):
        await msg.reply(f"{E.WARN} {t('gharch_invalid_username', get_user_lang(msg.from_user.id))}")
        return

    await state_fsm.update_data(god_username=uname.lower().lstrip("@"))
    await state_fsm.set_state(AnonStates.confirm_god)
    try: await msg.delete()
    except: pass

    lang = get_user_lang(msg.from_user.id)
    keyboard = kb([[success(f"{E.CHECK} {t('gharch_confirm_btn', lang)}", f"gharch_confirm_{data['starter']}")]])
    try:
        await msg.bot.edit_message_text(
            chat_id=data["chat_id"], message_id=data["setup_msg"],
            text=f"{E.MASK} <b>{t('gharch_confirm_god', lang, god=uname)}</b>",
            reply_markup=keyboard, parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("gharch_confirm_"))
async def gharch_confirm(cb: CallbackQuery, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    expected_uname = data.get("god_username", "")
    if not cb.from_user.username or cb.from_user.username.lower() != expected_uname:
        await cb.answer(t("gharch_not_god", get_user_lang(cb.from_user.id)), show_alert=True)
        return

    lang = get_user_lang(cb.from_user.id)
    chat_id = data["chat_id"]
    active_gharch[chat_id] = {"god_id": cb.from_user.id, "god_username": f"@{cb.from_user.username}"}
    await state_fsm.clear()

    me = await cb.bot.get_me()
    keyboard = kb([[success(f"{E.MASK} {t('gharch_send_btn', lang)}",
                             url=f"https://t.me/{me.username}?start=gharch_{chat_id}")]])
    await cb.message.edit_text(
        f"{E.PARTY}{E.MASK} <b>{t('gharch_started', lang, god=f'@{cb.from_user.username}')}</b>",
        reply_markup=keyboard, parse_mode=ParseMode.HTML,
    )
    try: await cb.bot.pin_chat_message(chat_id, cb.message.message_id)
    except: pass
    await cb.answer(t("gharch_you_are_god", lang))


# ══════════ اعتراف
@router.callback_query(F.data.startswith("eteraf_start_default_"))
async def eteraf_default(cb: CallbackQuery):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except: await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    try:
        member = await cb.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await cb.answer(t("gharch_only_admin", lang), show_alert=True); return

    await cb.answer()
    me = await cb.bot.get_me()
    starter = await cb.message.answer(f"{E.GHOST} {t('eteraf_default_text', lang)}")
    keyboard = kb([[success(f"{E.MASK} {t('eteraf_send_btn', lang)}",
                             url=f"https://t.me/{me.username}?start=eteraf_{chat_id}_{starter.message_id}")]])
    await starter.edit_reply_markup(reply_markup=keyboard)
    try: await cb.message.delete()
    except: pass


@router.callback_query(F.data.startswith("eteraf_start_custom_"))
async def eteraf_custom(cb: CallbackQuery, state_fsm: FSMContext):
    uid = cb.from_user.id
    lang = get_user_lang(uid)
    chat_id = cb.message.chat.id
    try: target = int(cb.data.rsplit("_", 1)[1])
    except: await cb.answer("❌"); return
    if uid != target:
        await cb.answer(t("not_your_panel", lang), show_alert=True); return

    try:
        member = await cb.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin:
        await cb.answer(t("gharch_only_admin", lang), show_alert=True); return

    await cb.answer()
    await state_fsm.clear()
    await state_fsm.update_data(chat_id=chat_id, starter=uid, prompt_msg=cb.message.message_id)
    await state_fsm.set_state(AnonStates.eteraf_custom)
    await cb.message.edit_text(f"{E.GHOST} <b>{t('eteraf_enter_text', lang)}</b>", parse_mode=ParseMode.HTML)


@router.message(AnonStates.eteraf_custom, F.text)
async def eteraf_got_text(msg: Message, state_fsm: FSMContext):
    data = await state_fsm.get_data()
    if msg.from_user.id != data.get("starter"):
        return
    lang = get_user_lang(msg.from_user.id)
    chat_id = data["chat_id"]
    me = await msg.bot.get_me()

    starter = await msg.bot
