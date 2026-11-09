"""بکاپ و ریستور دیتابیس"""

from __future__ import annotations
import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
import random

from aiogram import F
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode
from aiogram.filters import Command

from emojis import E
from utils.premium import kb, back_btn
from database import db
from admin.panel import router, OWNER_IDS  # ✅ استفاده از همان router

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
BACKUP_CHUNK_SIZE = 15 * 1024 * 1024
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
        raise RuntimeError(f"pg_dump failed: {err.decode()[:400]}")


def _split_file(src: Path, size: int) -> list[Path]:
    parts = []
    with src.open("rb") as f:
        i = 1
        while True:
            chunk = f.read(size)
            if not chunk:
                break
            p = src.with_suffix(src.suffix + f".part{i:02d}")
            p.write_bytes(chunk)
            parts.append(p)
            i += 1
    return parts


async def create_and_send_backup(chat_id: int, label: str = "manual") -> None:
    from main import bot  # ✅ از main

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bid = _short_id()
    dump = BACKUP_DIR / f"bk_{bid}.dump"

    status = await bot.send_message(
        chat_id,
        f"{E.REFRESH} در حال بکاپ‌گیری ({label})...",
        parse_mode=ParseMode.HTML,
    )

    try:
        await _run_pg_dump(dump)
        size = dump.stat().st_size

        if size > BACKUP_CHUNK_SIZE:
            parts = _split_file(dump, BACKUP_CHUNK_SIZE)
            dump.unlink(missing_ok=True)
        else:
            parts = [dump]

        total = len(parts)
        for i, p in enumerate(parts, 1):
            try:
                await bot.send_document(
                    chat_id,
                    FSInputFile(p, filename=f"bk_{bid}_p{i:02d}of{total:02d}.dump"),
                    caption=f"📦 قطعه {i}/{total} | {size/1024/1024:.1f} MB",
                )
            finally:
                p.unlink(missing_ok=True)

        await status.edit_text(
            f"{E.PARTY}{E.OK2} بکاپ کامل شد!\n"
            f"شناسه: <code>{bid}</code>\n"
            f"حجم: {size/1024/1024:.2f} MB",
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        try:
            await status.edit_text(f"{E.CROSS} خطا: {e}", parse_mode=ParseMode.HTML)
        except Exception:
            pass


@router.message(Command("backup"))
async def cmd_backup(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    await create_and_send_backup(msg.from_user.id, "manual")


@router.message(F.text.in_({"بکاپ", "backup"}))
async def msg_backup(msg: Message):
    if msg.from_user.id not in OWNER_IDS:
        return
    await create_and_send_backup(msg.from_user.id, "manual")
