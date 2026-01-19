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

## Notes

- `X` always starts.
- After each round finishes, you can click **Restart Round** to play again.
