# -*- coding: utf-8 -*-
"""بکاپ دیتابیس"""

import asyncio
import os
import random
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode

from emojis import E

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
CHUNK = 15 * 1024 * 1024
DATABASE_URL = os.getenv("DATABASE_URL", "")


def _short_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(random.randint(1000, 9999))


async def _run_pg_dump(out: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        "pg_dump", "--no-owner", "--no-acl", "-Fc", "-f", str(out), DATABASE_URL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"pg_dump: {err.decode()[:400]}")


def _split(src: Path, size: int) -> list:
    parts = []
    with src.open("rb") as f:
        i = 1
        while chunk := f.read(size):
            p = src.with_suffix(src.suffix + f".part{i:02d}")
            p.write_bytes(chunk)
            parts.append(p)
            i += 1
    return parts


async def create_and_send_backup(chat_id: int, bot: Bot, label: str = "manual"):
    """bot به عنوان پارامتر پاس داده می‌شود — بدون import از main"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bid = _short_id()
    dump = BACKUP_DIR / f"bk_{bid}.dump"

    status = await bot.send_message(
        chat_id, f"{E.REFRESH} در حال بکاپ ({label})...",
        parse_mode=ParseMode.HTML,
    )
    try:
        await _run_pg_dump(dump)
        size = dump.stat().st_size

        if size > CHUNK:
            parts = _split(dump, CHUNK)
            dump.unlink(missing_ok=True)
        else:
            parts = [dump]

        total = len(parts)
        for i, p in enumerate(parts, 1):
            try:
                await bot.send_document(
                    chat_id,
                    FSInputFile(p, filename=f"bk_{bid}_p{i:02d}of{total:02d}.dump"),
                    caption=f"📦 {i}/{total} | {size/1024/1024:.1f} MB",
                )
            finally:
                p.unlink(missing_ok=True)

        await status.edit_text(
            f"{E.PARTY}{E.OK2} <b>بکاپ کامل شد!</b>\n"
            f"شناسه: <code>{bid}</code>\n"
            f"حجم: {size/1024/1024:.2f} MB",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        try:
            await status.edit_text(f"{E.CROSS} خطا: {e}", parse_mode=ParseMode.HTML)
        except Exception:
            pass
