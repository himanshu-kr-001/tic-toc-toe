from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse


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
def root() -> HTMLResponse:
    html = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Tic-Tac-Toe Online Relay</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; background: #0b1220; color: #e8eefc; }
      .wrap { max-width: 820px; margin: 0 auto; padding: 28px 18px 40px; }
      .card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 16px; padding: 18px; }
      h1 { font-size: 22px; margin: 0 0 10px; }
      p { line-height: 1.55; margin: 10px 0; color: rgba(232,238,252,0.92); }
      code, pre { background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; }
      code { padding: 2px 8px; }
      pre { padding: 12px; overflow: auto; }
      .muted { color: rgba(232,238,252,0.70); }
      a { color: #9ad0ff; text-decoration: none; }
    </style>
  </head>
  <body>
    <div class=\"wrap\">
      <div class=\"card\">
        <h1>Tic-Tac-Toe Online Relay Server</h1>
        <p class=\"muted\">This server is deployed on Render. The Tkinter game runs on your computer.</p>

        <p><b>Health check:</b> <a href=\"/health\">/health</a></p>
        <p><b>WebSocket endpoint:</b> <code>/ws?room=ROOMNAME</code></p>

        <p><b>Example:</b></p>
        <pre>wss://YOUR-SERVICE.onrender.com/ws?room=demo</pre>

        <p class=\"muted\">Developed by Himanshu Kumar</p>
      </div>
    </div>
  </body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/health")
def health() -> dict:
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
