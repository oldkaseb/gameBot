"""مدیریت متمرکز وضعیت بازی‌ها + پاکسازی خودکار"""

from __future__ import annotations
import asyncio
import time
from typing import Any
from aiogram import Bot

# ساختار: {game_type: {chat_id: {game_id: game_dict}}}
active_games: dict[str, dict[int, dict[int, dict]]] = {
    "hangman": {}, "typing": {}, "guess_number": {}, "hokm": {},
    "dooz": {}, "doz4p": {}, "connect4": {}, "rps": {},
    "memory": {}, "2048": {}, "samegame": {}, "spuzzle": {},
    "gardone": {},
}

active_gharch: dict[int, dict] = {}

GAME_TIMEOUT_SECONDS = 30 * 60  # ۳۰ دقیقه


def register(game_type: str, chat_id: int, game_id: int, data: dict) -> None:
    active_games[game_type].setdefault(chat_id, {})[game_id] = data
    data["_created"] = time.time()


def unregister(game_type: str, chat_id: int, game_id: int) -> None:
    if chat_id in active_games[game_type]:
        active_games[game_type][chat_id].pop(game_id, None)
        if not active_games[game_type][chat_id]:
            del active_games[game_type][chat_id]


def get(game_type: str, chat_id: int, game_id: int) -> dict | None:
    return active_games[game_type].get(chat_id, {}).get(game_id)


def exists(game_type: str, chat_id: int, game_id: int) -> bool:
    return game_id in active_games[game_type].get(chat_id, {})


def user_has_game(game_type: str, chat_id: int, user_id: int) -> bool:
    """آیا این کاربر در این گروه یک بازی فعال دارد؟"""
    for g in active_games[game_type].get(chat_id, {}).values():
        if g.get("player_id") == user_id:
            return True
        if any(p.get("id") == user_id for p in g.get("players_info", [])):
            return True
    return False


def clear_chat(game_type: str, chat_id: int) -> int:
    """پاک کردن همه بازی‌های یک گروه — برگرداندن تعداد"""
    if chat_id in active_games[game_type]:
        n = len(active_games[game_type][chat_id])
        del active_games[game_type][chat_id]
        return n
    return 0


def cleanup_stale() -> int:
    """پاک‌سازی خودکار بازی‌های رهاشده"""
    now = time.time()
    removed = 0
    for gtype, chats in active_games.items():
        for chat_id, games in list(chats.items()):
            for gid, g in list(games.items()):
                if now - g.get("_created", now) > GAME_TIMEOUT_SECONDS:
                    del games[gid]
                    removed += 1
            if not games:
                del chats[chat_id]
    return removed


async def cleanup_loop(bot: Bot) -> None:
    """حلقه پس‌زمینه برای پاکسازی"""
    while True:
        await asyncio.sleep(300)  # هر ۵ دقیقه
        n = cleanup_stale()
        if n:
            import logging
            logging.getLogger("games").info(f"Cleaned up {n} stale games")
