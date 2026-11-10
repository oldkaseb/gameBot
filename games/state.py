"""مدیریت متمرکز وضعیت بازی‌ها + پاکسازی خودکار"""

from __future__ import annotations
import asyncio
import logging
import time
from typing import Any
from aiogram import Bot

logger = logging.getLogger("games.state")

# ساختار: {game_type: {chat_id: {game_id: game_dict}}}
active_games: dict[str, dict[int, dict[int, dict]]] = {
    "hangman": {}, "typing": {}, "guess_number": {}, "hokm": {},
    "dooz": {}, "doz4p": {}, "connect4": {}, "rps": {},
    "memory": {}, "2048": {}, "samegame": {}, "spuzzle": {},
    "gardone": {},
}

active_gharch: dict[int, dict] = {}

# ✅ تایم‌اوت از ۳۰ دقیقه به ۲۴ ساعت افزایش یافت
GAME_TIMEOUT_SECONDS = 24 * 60 * 60


def register(game_type: str, chat_id: int, game_id: int, data: dict) -> None:
    active_games[game_type].setdefault(chat_id, {})[game_id] = data
    data["_created"] = time.time()
    logger.debug(f"🟢 register {game_type} chat={chat_id} gid={game_id}")


def unregister(game_type: str, chat_id: int, game_id: int) -> None:
    if chat_id in active_games[game_type]:
        existed = game_id in active_games[game_type][chat_id]
        active_games[game_type][chat_id].pop(game_id, None)
        if existed:
            logger.debug(f"🔴 unregister {game_type} chat={chat_id} gid={game_id}")
        if not active_games[game_type][chat_id]:
            del active_games[game_type][chat_id]


def get(game_type: str, chat_id: int, game_id: int) -> dict | None:
    return active_games[game_type].get(chat_id, {}).get(game_id)


def exists(game_type: str, chat_id: int, game_id: int) -> bool:
    return game_id in active_games[game_type].get(chat_id, {})


def user_has_game(game_type: str, chat_id: int, user_id: int) -> bool:
    for g in active_games[game_type].get(chat_id, {}).values():
        if g.get("player_id") == user_id:
            return True
        if any(p.get("id") == user_id for p in g.get("players_info", [])):
            return True
        if any(p.get("id") == user_id for p in g.get("participants", [])):
            return True
        if any(p.get("id") == user_id for p in g.get("players", [])):
            return True
    return False


def clear_chat(game_type: str, chat_id: int) -> int:
    if chat_id in active_games[game_type]:
        n = len(active_games[game_type][chat_id])
        del active_games[game_type][chat_id]
        if n:
            logger.info(f"🧹 clear_chat {game_type} chat={chat_id} n={n}")
        return n
    return 0


def cleanup_stale() -> int:
    now = time.time()
    removed = 0
    for gtype, chats in active_games.items():
        for chat_id, games in list(chats.items()):
            if not isinstance(games, dict):
                del chats[chat_id]
                removed += 1
                logger.warning(f"🗑️ removed corrupted entry {gtype}/{chat_id}")
                continue
            for gid, g in list(games.items()):
                if not isinstance(g, dict):
                    del games[gid]
                    removed += 1
                    continue
                if now - g.get("_created", now) > GAME_TIMEOUT_SECONDS:
                    del games[gid]
                    removed += 1
                    logger.info(f"⏰ timeout {gtype}/{chat_id}/{gid}")
            if not games:
                del chats[chat_id]
    return removed


async def cleanup_loop(bot: Bot) -> None:
    while True:
        await asyncio.sleep(300)
        n = cleanup_stale()
        if n:
            logger.info(f"Cleaned up {n} stale games")
