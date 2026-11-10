# -*- coding: utf-8 -*-
"""webapp/backend/main.py — سرور FastAPI و WebSocket برای تمام بازی‌های Mini App"""

import json
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from webapp.backend.game_logic.hokm import HokmGame
    from webapp.backend.auth import validate_init_data
except ImportError:
    from game_logic.hokm import HokmGame
    from auth import validate_init_data

from database import db

app = FastAPI(title="Rhino GameBot Mini App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

active_rooms = {}
connections = {}


class WinPayload(BaseModel):
    uid: int
    game_type: str
    best_time: float | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/win")
async def record_win(payload: WinPayload):
    try:
        await db.add_win(payload.uid, payload.game_type, payload.best_time)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/leaderboard/{game_type}")
async def get_leaderboard(game_type: str):
    try:
        rows = await db.top_players(None if game_type == "all" else game_type, limit=10)
        return {
            "ok": True,
            "players": [dict(r) for r in rows],
        }
    except Exception as e:
        return {"ok": False, "players": [], "error": str(e)}


@app.websocket("/ws/{game_type}/{session_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_type: str,
    session_id: str,
    user_id: int,
    init_data: str = Query(None),
):
    # اگر init_data ارسال شده بود اعتبارسنجی کن؛ اگر در مرورگر/تست یا بدون initData بود اجازه اتصال بده
    if init_data and init_data != "none":
        try:
            tg_user = validate_init_data(init_data)
            real_user_id = tg_user.get("id")
            if real_user_id and int(real_user_id) != int(user_id):
                await websocket.close(code=1008)
                return
        except Exception as e:
            print(f"Auth warning: {e}")

    await websocket.accept()

    if session_id not in connections:
        connections[session_id] = []
    connections[session_id].append({"ws": websocket, "user_id": user_id})

    if session_id not in active_rooms:
        if game_type == "hokm":
            active_rooms[session_id] = HokmGame(session_id)
        else:
            active_rooms[session_id] = {"type": game_type, "state": {}, "players": []}

    room = active_rooms[session_id]
    if isinstance(room, dict) and user_id not in room["players"]:
        room["players"].append(user_id)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if game_type == "hokm":
                game = active_rooms[session_id]
                game.handle_action(user_id, msg)
                for conn in list(connections.get(session_id, [])):
                    try:
                        await conn["ws"].send_json(game.get_state_for_player(conn["user_id"]))
                    except Exception:
                        pass
            else:
                # همگام‌سازی بلادرنگ برای تمام بازی‌های چندنفره و چتی در مینی‌اپ
                payload = {
                    "user_id": user_id,
                    "game_type": game_type,
                    **msg,
                }
                for conn in list(connections.get(session_id, [])):
                    try:
                        await conn["ws"].send_json(payload)
                    except Exception:
                        pass

    except WebSocketDisconnect:
        if session_id in connections:
            connections[session_id] = [
                c for c in connections[session_id] if c["ws"] != websocket
            ]


# سرو کردن فایل‌های بیلد شده فرانت‌اند React در Coolify
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
