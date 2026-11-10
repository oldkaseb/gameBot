"""مدیریت لابی بازی‌های چندنفره برای انتقال به مینی‌اپ"""

import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode

from emojis import E
from langs import t, get_user_lang
from utils.premium import success, primary, danger, kb

router = Router(name="lobbies")
MINI_APP_URL = "https://games.rhinokaseb.abrdns.com"

# { lobby_id: {game_type, host_id, max_players, players: [{id, name}], msg_id} }
active_lobbies = {}

GAME_CONFIG = {
    "dooz":     {"max": 2, "name": "دوز ۲ نفره", "icon": "❌"},
    "doz4p":    {"max": 4, "name": "دوز ۴ نفره", "icon": "🔴"},
    "connect4": {"max": 2, "name": "چهار در ردیف", "icon": "🔴"},
    "hokm":     {"max": 4, "name": "حکم ۴ نفره", "icon": "🃏"},
    "rps":      {"max": 2, "name": "سنگ کاغذ قیچی", "icon": "🪨"},
    "memory":   {"max": 2, "name": "بازی حافظه", "icon": "🧠"},
}

@router.callback_query(F.data.startswith("lobby_"))
async def create_lobby(cb: CallbackQuery):
    parts = cb.data.split("_")
    game_type = parts[1]
    host_id = int(parts[2])
    uid = cb.from_user.id
    
    if uid != host_id:
        await cb.answer("این لابی برای شما نیست!", show_alert=True)
        return
        
    config = GAME_CONFIG.get(game_type)
    if not config:
        await cb.answer("بازی نامعتبر", show_alert=True)
        return

    lobby_id = str(uuid.uuid4())[:8]
    active_lobbies[lobby_id] = {
        "game_type": game_type,
        "host_id": host_id,
        "max_players": config["max"],
        "players": [{"id": uid, "name": cb.from_user.first_name}],
        "msg_id": cb.message.message_id,
        "chat_id": cb.message.chat.id,
    }

    await cb.answer()
    await update_lobby_message(cb, lobby_id)

async def update_lobby_message(cb_or_bot, lobby_id):
    lobby = active_lobbies.get(lobby_id)
    if not lobby: return
    
    config = GAME_CONFIG[lobby["game_type"]]
    current_p = len(lobby["players"])
    max_p = lobby["max_players"]
    
    players_list = "\n".join([f"👤 {p['name']}" for p in lobby["players"]])
    
    text = (
        f"{E.GAME} <b>لابی {config['name']}</b>\n\n"
        f"{E.PEOPLE} بازیکنان ({current_p}/{max_p}):\n{players_list}\n\n"
        f"{E.HOURGLASS} منتظر بازیکنان..."
    )
    
    rows = [[success(f"{E.PLUS} پیوستن به بازی", f"join_lobby_{lobby_id}")]]
    if lobby["host_id"] == (cb_or_bot.from_user.id if hasattr(cb_or_bot, 'from_user') else 0):
        rows.append([danger("لغو لابی", f"cancel_lobby_{lobby_id}")])
    
    try:
        await cb_or_bot.bot.edit_message_text(
            text=text, chat_id=lobby["chat_id"], message_id=lobby["msg_id"],
            reply_markup=kb(rows), parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("join_lobby_"))
async def join_lobby(cb: CallbackQuery):
    lobby_id = cb.data.replace("join_lobby_", "")
    lobby = active_lobbies.get(lobby_id)
    
    if not lobby:
        await cb.answer("لابی منقضی شده یا پر شده است.", show_alert=True)
        return
        
    if any(p["id"] == cb.from_user.id for p in lobby["players"]):
        await cb.answer("شما قبلاً در این لابی هستید!", show_alert=True)
        return
        
    if len(lobby["players"]) >= lobby["max_players"]:
        await cb.answer("لابی پر است!", show_alert=True)
        return

    lobby["players"].append({"id": cb.from_user.id, "name": cb.from_user.first_name})
    await cb.answer("✅ وارد لابی شدید!")

    # اگر لابی پر شد، بازی را استارت کن
    if len(lobby["players"]) == lobby["max_players"]:
        await start_webapp_game(cb, lobby_id)
    else:
        await update_lobby_message(cb, lobby_id)

async def start_webapp_game(cb: CallbackQuery, lobby_id: str):
    lobby = active_lobbies[lobby_id]
    game_url = f"{MINI_APP_URL}/?game={lobby['game_type']}&session={lobby_id}"
    
    text = (
        f"{E.PARTY} <b>لابی پر شد! بازی شروع می‌شود.</b>\n\n"
        f"{E.INFO} همه بازیکنان وارد میز شوند:"
    )
    markup = kb([[primary(f"{E.GAME} ورود به میز بازی", web_app_url=game_url)]])
    
    await cb.bot.edit_message_text(
        text=text, chat_id=lobby["chat_id"], message_id=lobby["msg_id"],
        reply_markup=markup, parse_mode=ParseMode.HTML
    )
    del active_lobbies[lobby_id]
