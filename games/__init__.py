# -*- coding: utf-8 -*-
"""ثبت بازی‌های باقی‌مانده در ربات (بازی‌های مینی‌اپ حذف شدند)"""

from aiogram import Dispatcher

from .panel import router as panel_r
from .gardone import router as gardone_r
from .lobbies import router as lobby_r  # مدیریت لابی‌ها برای انتقال به مینی اپ

def register_all_games(dp: Dispatcher) -> None:
    dp.include_routers(
        panel_r,
        lobby_r,
        gardone_r,
    )
