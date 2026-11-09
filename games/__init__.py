# -*- coding: utf-8 -*-
"""ثبت همه بازی‌ها در Dispatcher"""

from aiogram import Dispatcher

from .panel import router as panel_r
from .hangman import router as hangman_r
from .typing_game import router as typing_r
from .number_guess import router as guess_r
from .g2048 import router as g2048_r
from .samegame import router as samegame_r
from .spuzzle import router as spuzzle_r
from .dooz import router as dooz_r
from .doz4p import router as doz4p_r
from .connect4 import router as connect4_r
from .rps import router as rps_r
from .memory import router as memory_r
from .hokm import router as hokm_r
from .gardone import router as gardone_r


def register_all_games(dp: Dispatcher) -> None:
    """فقط بازی‌ها — anon, stop, lb, admin در main.py ثبت می‌شوند"""
    dp.include_routers(
        panel_r,       # پنل بازی‌ها
        hokm_r,
        doz4p_r,
        dooz_r,
        connect4_r,
        rps_r,
        memory_r,
        spuzzle_r,
        samegame_r,
        g2048_r,
        typing_r,
        guess_r,
        hangman_r,
        gardone_r,
    )
