# -*- coding: utf-8 -*-
"""games/__init__.py — ثبت روترهای بازی، پنل، لابی و گردونه شانس"""

from aiogram import Dispatcher

from games.panel import router as panel_router
from games.lobbies import router as lobbies_router
from games.gardone import router as gardone_router
from games.demon_tower import router as demon_tower_router



def register_all_games(dp: Dispatcher):
    dp.include_router(panel_router)
    dp.include_router(lobbies_router)
    dp.include_router(gardone_router)
    dp.include_router(demon_tower_router)

    # ثبت سایر روترهای احتمالی در صورت فراخوانی مستقیم
    optional_modules = [
        "leaderboard",
    ]
    for mod_name in optional_modules:
        try:
            mod = __import__(f"games.{mod_name}", fromlist=["router"])
            if hasattr(mod, "router"):
                dp.include_router(mod.router)
        except Exception:
            pass
