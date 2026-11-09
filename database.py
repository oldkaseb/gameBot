# -*- coding: utf-8 -*-
"""database.py — asyncpg، نسخه نهایی ربات بازی"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional, Any

import asyncpg

logger = logging.getLogger("db")
DATABASE_URL = os.getenv("DATABASE_URL", "")

OWNER_IDS = {7662192190, 6041119040}


# ═════════════════════════ SQL
SQL_TABLES = [
    """CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        is_banned BOOLEAN DEFAULT FALSE,
        language VARCHAR(5) DEFAULT 'fa',
        start_time TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS groups (
        group_id BIGINT PRIMARY KEY,
        title TEXT,
        member_count INT DEFAULT 0,
        added_time TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS start_message (
        id INT PRIMARY KEY,
        message_id BIGINT,
        chat_id BIGINT
    )""",
    """CREATE TABLE IF NOT EXISTS banned_users (user_id BIGINT PRIMARY KEY)""",
    """CREATE TABLE IF NOT EXISTS banned_groups (group_id BIGINT PRIMARY KEY)""",
    """CREATE TABLE IF NOT EXISTS admins (
        user_id BIGINT PRIMARY KEY,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS admin_logs (
        id SERIAL PRIMARY KEY,
        admin_id BIGINT NOT NULL,
        action TEXT NOT NULL,
        target_id BIGINT,
        detail TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS game_settings (
        game_type VARCHAR(50) PRIMARY KEY,
        is_enabled BOOLEAN DEFAULT TRUE,
        config JSONB DEFAULT '{}'::jsonb,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS game_wins (
        user_id BIGINT,
        game_type VARCHAR(50),
        wins INTEGER DEFAULT 0,
        best_time DOUBLE PRECISION,
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (user_id, game_type)
    )""",
    """CREATE TABLE IF NOT EXISTS forced_channels (
        id SERIAL PRIMARY KEY,
        chat_id TEXT NOT NULL UNIQUE,
        username TEXT,
        title TEXT,
        button_text TEXT DEFAULT 'عضویت',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
]

SQL_ALTERS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'fa'",
    "ALTER TABLE game_wins ADD COLUMN IF NOT EXISTS best_time DOUBLE PRECISION",
]

SQL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_game_wins_type ON game_wins(game_type)",
    "CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned)",
]


class Database:
    def __init__(self, dsn: str = ""):
        self.dsn = dsn or DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    # ══════════ اتصال
    async def connect(self):
        if self.pool:
            return
        for attempt in range(1, 11):
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.dsn, min_size=1, max_size=10, command_timeout=60
                )
                logger.info("✅ DB connected")
                return
            except Exception as e:
                logger.warning(f"DB connect {attempt}/10 failed: {e}")
                await asyncio.sleep(3)
        raise RuntimeError("Cannot connect to DB after 10 attempts")

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def init(self):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            for sql in SQL_TABLES:
                await conn.execute(sql)
            for sql in SQL_ALTERS:
                try:
                    await conn.execute(sql)
                except Exception as e:
                    logger.debug(f"alter skip: {e}")
            for sql in SQL_INDEXES:
                try:
                    await conn.execute(sql)
                except Exception as e:
                    logger.debug(f"index skip: {e}")
        logger.info("✅ DB schema ready")

    # ══════════ کاربران
    async def get_user(self, user_id: int) -> Optional[asyncpg.Record]:
        return await self.pool.fetchrow(
            "SELECT * FROM users WHERE user_id=$1", user_id
        )

    async def upsert_user(self, user_id: int, username: str, first_name: str) -> bool:
        existing = await self.get_user(user_id)
        if existing:
            await self.pool.execute(
                "UPDATE users SET username=$2, first_name=$3 WHERE user_id=$1",
                user_id, username, first_name,
            )
            return False
        await self.pool.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES ($1,$2,$3)",
            user_id, username, first_name,
        )
        return True

    async def is_banned(self, user_id: int) -> bool:
        val = await self.pool.fetchval(
            "SELECT is_banned FROM users WHERE user_id=$1", user_id
        )
        return bool(val) if val is not None else False

    async def set_banned(self, user_id: int, banned: bool):
        await self.pool.execute(
            "UPDATE users SET is_banned=$2 WHERE user_id=$1", user_id, banned
        )

    async def set_language(self, user_id: int, lang: str):
        await self.pool.execute(
            "UPDATE users SET language=$2 WHERE user_id=$1", user_id, lang
        )

    async def user_language(self, user_id: int) -> Optional[str]:
        return await self.pool.fetchval(
            "SELECT language FROM users WHERE user_id=$1", user_id
        )

    # ══════════ ادمین‌ها
    async def is_admin(self, user_id: int) -> bool:
        if user_id in OWNER_IDS:
            return True
        return await self.pool.fetchval(
            "SELECT 1 FROM admins WHERE user_id=$1", user_id
        ) is not None

    async def is_owner(self, user_id: int) -> bool:
        return user_id in OWNER_IDS

    async def list_admins(self):
        return await self.pool.fetch("SELECT * FROM admins ORDER BY created_at")

    async def add_admin(self, user_id: int):
        await self.pool.execute(
            "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
        )

    async def remove_admin(self, user_id: int):
        await self.pool.execute("DELETE FROM admins WHERE user_id=$1", user_id)

    async def log_admin(
        self, admin_id: int, action: str,
        target_id: int = None, detail: str = ""
    ):
        try:
            await self.pool.execute(
                "INSERT INTO admin_logs (admin_id, action, target_id, detail) "
                "VALUES ($1,$2,$3,$4)",
                admin_id, action, target_id, detail,
            )
        except Exception as e:
            logger.debug(f"log_admin failed: {e}")

    # ══════════ تنظیمات بازی
    async def is_game_enabled(self, game_type: str) -> bool:
        val = await self.pool.fetchval(
            "SELECT is_enabled FROM game_settings WHERE game_type=$1", game_type
        )
        return True if val is None else bool(val)

    async def toggle_game(self, game_type: str) -> bool:
        current = await self.is_game_enabled(game_type)
        new = not current
        await self.pool.execute(
            """INSERT INTO game_settings (game_type, is_enabled) VALUES ($1,$2)
               ON CONFLICT (game_type) DO UPDATE
               SET is_enabled=$2, updated_at=NOW()""",
            game_type, new,
        )
        return new

    async def all_game_settings(self) -> dict[str, bool]:
        try:
            rows = await self.pool.fetch(
                "SELECT game_type, is_enabled FROM game_settings"
            )
            return {r["game_type"]: bool(r["is_enabled"]) for r in rows}
        except Exception:
            return {}

    async def get_game_config(self, game_type: str) -> dict:
        val = await self.pool.fetchval(
            "SELECT config FROM game_settings WHERE game_type=$1", game_type
        )
        return dict(val) if val else {}

    async def set_game_config(self, game_type: str, key: str, value: Any):
        await self.pool.execute(
            """INSERT INTO game_settings (game_type, config) VALUES ($1, $2::jsonb)
               ON CONFLICT (game_type) DO UPDATE
               SET config = jsonb_set(
                   COALESCE(game_settings.config, '{}'::jsonb),
                   $3::text[], to_jsonb($4::json)
               ), updated_at=NOW()""",
            game_type, json.dumps({key: value}), f"{{{key}}}", json.dumps(value),
        )

    # ══════════ Leaderboard
    async def add_win(self, user_id: int, game_type: str, best_time: float = None):
        try:
            if best_time is not None:
                await self.pool.execute(
                    """INSERT INTO game_wins (user_id, game_type, wins, best_time)
                       VALUES ($1, $2, 1, $3)
                       ON CONFLICT (user_id, game_type) DO UPDATE
                       SET wins = game_wins.wins + 1,
                           best_time = LEAST(
                               COALESCE(game_wins.best_time, $3), $3
                           ),
                           updated_at = NOW()""",
                    user_id, game_type, best_time,
                )
            else:
                await self.pool.execute(
                    """INSERT INTO game_wins (user_id, game_type, wins)
                       VALUES ($1, $2, 1)
                       ON CONFLICT (user_id, game_type) DO UPDATE
                       SET wins = game_wins.wins + 1, updated_at = NOW()""",
                    user_id, game_type,
                )
        except Exception as e:
            logger.debug(f"add_win failed: {e}")

    async def top_players(self, game_type: str = None, limit: int = 10):
        if game_type:
            return await self.pool.fetch(
                """SELECT gw.user_id, gw.wins, gw.best_time, u.first_name
                   FROM game_wins gw
                   LEFT JOIN users u ON u.user_id = gw.user_id
                   WHERE gw.game_type = $1
                   ORDER BY gw.wins DESC, gw.best_time ASC NULLS LAST
                   LIMIT $2""",
                game_type, limit,
            )
        return await self.pool.fetch(
            """SELECT user_id, SUM(wins) as total FROM game_wins
               GROUP BY user_id ORDER BY total DESC LIMIT $1""",
            limit,
        )

    async def user_wins(self, user_id: int):
        return await self.pool.fetch(
            "SELECT game_type, wins, best_time FROM game_wins "
            "WHERE user_id=$1 ORDER BY wins DESC",
            user_id,
        )

    async def reset_user_wins(self, user_id: int):
        await self.pool.execute("DELETE FROM game_wins WHERE user_id=$1", user_id)

    # ══════════ کانال اجباری
    async def list_channels(self):
        return await self.pool.fetch("SELECT * FROM forced_channels ORDER BY id")

    async def add_channel(self, chat_id: str, username: str, title: str):
        await self.pool.execute(
            """INSERT INTO forced_channels (chat_id, username, title)
               VALUES ($1,$2,$3)
               ON CONFLICT (chat_id) DO UPDATE SET username=$2, title=$3""",
            chat_id, username, title,
        )

    async def remove_channel(self, ch_id: int):
        await self.pool.execute("DELETE FROM forced_channels WHERE id=$1", ch_id)

    # ══════════ گروه‌ها
    async def get_group(self, group_id: int):
        return await self.pool.fetchrow(
            "SELECT * FROM groups WHERE group_id=$1", group_id
        )

    async def add_group(self, group_id: int, title: str, member_count: int):
        await self.pool.execute(
            """INSERT INTO groups (group_id, title, member_count) VALUES ($1,$2,$3)
               ON CONFLICT (group_id) DO UPDATE SET title=$2, member_count=$3""",
            group_id, title, member_count,
        )

    async def remove_group(self, group_id: int):
        await self.pool.execute("DELETE FROM groups WHERE group_id=$1", group_id)

    async def list_groups(self, limit: int = 100, offset: int = 0):
        return await self.pool.fetch(
            "SELECT * FROM groups ORDER BY added_time DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )

    # ══════════ شمارش‌ها
    async def count_groups(self) -> int:
        return await self.pool.fetchval("SELECT COUNT(*) FROM groups") or 0

    async def count_users(self) -> int:
        return await self.pool.fetchval("SELECT COUNT(*) FROM users") or 0

    async def count_banned(self) -> int:
        return await self.pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE is_banned=TRUE"
        ) or 0


# ══════════ singleton
db = Database()
