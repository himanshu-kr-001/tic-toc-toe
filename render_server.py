from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()


@dataclass
class Room:
    a: Optional[WebSocket] = None
    b: Optional[WebSocket] = None

    def other(self, ws: WebSocket) -> Optional[WebSocket]:
        if ws is self.a:
            return self.b
        if ws is self.b:
            return self.a
        return None


_rooms: Dict[str, Room] = {}
_rooms_lock = asyncio.Lock()


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "tic-tac-toe-ws"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, room: str = "default") -> None:
    await websocket.accept()

    async with _rooms_lock:
        r = _rooms.get(room)
        if r is None:
            r = Room()
            _rooms[room] = r

        if r.a is None:
            r.a = websocket
            await websocket.send_json({"type": "hello", "role": "a"})
        elif r.b is None:
            r.b = websocket
            await websocket.send_json({"type": "hello", "role": "b"})
            # Notify both clients that game can start.
            try:
                await r.a.send_json({"type": "ready"})
            except Exception:
                pass
            try:
                await r.b.send_json({"type": "ready"})
            except Exception:
                pass
        else:
            await websocket.send_json({"type": "error", "message": "Room is full"})
            await websocket.close(code=1008)
            return

    try:
        while True:
            msg = await websocket.receive_text()
            async with _rooms_lock:
                r = _rooms.get(room)
                other = r.other(websocket) if r else None
            if other is not None:
                try:
                    await other.send_text(msg)
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        async with _rooms_lock:
            r = _rooms.get(room)
            if r is not None:
                if r.a is websocket:
                    r.a = None
                if r.b is websocket:
                    r.b = None
                if r.a is None and r.b is None:
                    _rooms.pop(room, None)

        try:
            await websocket.close()
        except Exception:
            pass
