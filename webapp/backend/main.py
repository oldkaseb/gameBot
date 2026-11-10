from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from game_logic.hokm import HokmGame

app = FastAPI()

# برای اجازه دادن به فرانت‌اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# اتاق‌های فعال
active_rooms = {}
connections = {}

@app.websocket("/ws/{game_type}/{session_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, game_type: str, session_id: str, user_id: int):
    await websocket.accept()
    
    if session_id not in connections:
        connections[session_id] = []
    connections[session_id].append({"ws": websocket, "user_id": user_id})

    # استارت بازی
    if session_id not in active_rooms:
        if game_type == "hokm":
            active_rooms[session_id] = HokmGame(session_id)
        # بقیه بازی‌ها رو اینجا اضافه کن

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if game_type == "hokm":
                game = active_rooms[session_id]
                # پردازش حرکت
                response = game.handle_action(user_id, msg)
                
                # ارسال وضعیت جدید به همه
                for conn in connections[session_id]:
                    await conn["ws"].send_json(game.get_state_for_player(conn["user_id"]))
                    
            elif game_type in ["typing", "hangman", "guess"]:
                # بازی‌های چتی (شبیه ساز چت)
                for conn in connections[session_id]:
                    await conn["ws"].send_json({
                        "user_id": user_id,
                        "text": msg.get("text"),
                        "name": msg.get("name", "User")
                    })

    except WebSocketDisconnect:
        connections[session_id] = [c for c in connections[session_id] if c["ws"] != websocket]
