# Tic-Tac-Toe (Human vs Human)

A fully functional Tic-Tac-Toe game written in Python with a Tkinter GUI.

## Features

- 3×3 grid
- Human vs Human (two players on the same computer)
- Human vs AI
- Online multiplayer (Host/Join over LAN)
- Win/Draw detection
- Restart round
- Score tracking across rounds

## How to Run

1. Open a terminal in this folder.
2. Run:

```bash
python main.py
```

## Online Play (Host/Join)

This project includes an **Online** mode for playing with a friend on the same Wi‑Fi/LAN.

### Host (Player X)

1. Run the game.
2. Select **Mode: Online**.
3. Choose a **Port** (default: `5050`).
4. Click **Host**.

### Join (Player O)

1. Run the game on the other computer.
2. Select **Mode: Online**.
3. Enter the host PC's **IP** and the same **Port**.
4. Click **Join**.

### Finding your IP (Windows)

- Open Command Prompt and run: `ipconfig`
- Look for **IPv4 Address** (example: `192.168.1.10`)

### Notes

- Online mode is designed for LAN. Over the internet you would need port-forwarding or a tunnel.
- Host is authoritative: the host syncs moves/restarts to the joiner.

## Deploy Online Relay on Render (Internet Play)

Render cannot run a Tkinter GUI, but it can host an **online relay server**. You still run the game (`python main.py`) on both computers, and both clients connect to the same Render server.

### Files included

- `render_server.py` (FastAPI WebSocket relay)
- `requirements.txt`
- `render.yaml`

### Deploy steps

1. Push this repo to GitHub.
2. In Render:
   - New +
   - Blueprint
   - Select your GitHub repo
3. Deploy. Render will run:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn render_server:app --host 0.0.0.0 --port $PORT`

### After deploy

Your service URL will look like:

`https://<your-service>.onrender.com`

WebSocket endpoint:

`wss://<your-service>.onrender.com/ws?room=ROOMNAME`

To use this from the desktop app, the networking layer must use WebSockets (LAN TCP mode is separate).

## Notes

- `X` always starts.
- After each round finishes, you can click **Restart Round** to play again.
