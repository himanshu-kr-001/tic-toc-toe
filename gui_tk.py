from __future__ import annotations

import colorsys
import tkinter as tk
from typing import Dict, Optional, Tuple

try:
    import winsound  # type: ignore
except Exception:  # pragma: no cover
    winsound = None  # type: ignore

from game_controller import GameController
from online_net import OnlineClient, OnlineConfig, OnlineHost


Move = Tuple[int, int]


class TicTacToeGUI:
    """Tkinter GUI wrapper around GameController."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.root.resizable(False, False)

        self.controller = GameController(x_symbol="X", o_symbol="O")
        self._win_line_id: Optional[int] = None
        self._cell_origin: Dict[Move, Tuple[float, float]] = {}
        self._cell_rect_id: Dict[Move, int] = {}
        self._cell_text_layers: Dict[Move, list[int]] = {}
        self._cell_palette: Dict[Move, Tuple[str, str, str]] = {}
        self._x_palette_idx = 0
        self._o_palette_idx = 0
        self._cell_size = 120
        self._pad = 10
        self._corner_radius = 22
        self.mode_var = tk.StringVar(value="HUMAN_HUMAN")

        self._rgb_anim_t = 0.0
        self._rgb_anim_after_id: Optional[str] = None

        self._online_mode: bool = False
        self._online_role: Optional[str] = None  # 'host' | 'client'
        self._online_host: Optional[OnlineHost] = None
        self._online_client: Optional[OnlineClient] = None
        self._local_symbol: str = "X"

        self._build_ui()
        self._sync_ui_from_state()
        self._start_rgb_border_animation()

    def _build_ui(self) -> None:
        self.top = tk.Frame(self.root, padx=10, pady=10)
        self.top.pack(fill="x")

        tk.Label(self.top, text="Mode:").pack(side="left")
        tk.Radiobutton(
            self.top,
            text="Human vs Human",
            value="HUMAN_HUMAN",
            variable=self.mode_var,
            command=self._on_change_mode,
        ).pack(side="left", padx=(6, 0))
        tk.Radiobutton(
            self.top,
            text="Human vs AI",
            value="HUMAN_AI",
            variable=self.mode_var,
            command=self._on_change_mode,
        ).pack(side="left", padx=(6, 0))

        tk.Radiobutton(
            self.top,
            text="Online",
            value="ONLINE",
            variable=self.mode_var,
            command=self._on_change_mode,
        ).pack(side="left", padx=(6, 0))

        self.restart_btn = tk.Button(self.top, text="Restart Round", command=self._on_restart_pressed)
        self.restart_btn.pack(side="right")

        self.online_frame = tk.Frame(self.root, padx=10, pady=4)
        self.online_frame.pack(fill="x")

        tk.Label(self.online_frame, text="IP:").pack(side="left")
        self.join_ip_var = tk.StringVar(value="127.0.0.1")
        self.join_ip_entry = tk.Entry(self.online_frame, textvariable=self.join_ip_var, width=16)
        self.join_ip_entry.pack(side="left", padx=(4, 8))

        tk.Label(self.online_frame, text="Port:").pack(side="left")
        self.port_var = tk.StringVar(value="5050")
        self.port_entry = tk.Entry(self.online_frame, textvariable=self.port_var, width=6)
        self.port_entry.pack(side="left", padx=(4, 8))

        self.host_btn = tk.Button(self.online_frame, text="Host", command=self._online_host_start)
        self.host_btn.pack(side="left", padx=(0, 6))

        self.join_btn = tk.Button(self.online_frame, text="Join", command=self._online_join)
        self.join_btn.pack(side="left", padx=(0, 6))

        self.disconnect_btn = tk.Button(self.online_frame, text="Disconnect", command=self._online_disconnect)
        self.disconnect_btn.pack(side="left")

        self.score_label = tk.Label(self.root, padx=10)
        self.score_label.pack(fill="x")

        self.status_label = tk.Label(self.root, padx=10, pady=6, anchor="w")
        self.status_label.pack(fill="x")

        self.board_frame = tk.Frame(self.root, padx=10, pady=10)
        self.board_frame.pack()

        # Single canvas that contains the 3x3 board and also draws the win strike-through.
        self.board_canvas = tk.Canvas(self.board_frame, highlightthickness=0, bg=self.board_frame.cget("bg"))
        self.board_canvas.pack()

        for r in range(3):
            for c in range(3):
                x = self._pad + c * (self._cell_size + self._pad)
                y = self._pad + r * (self._cell_size + self._pad)
                self._cell_origin[(r, c)] = (x, y)

                rect_id = self._create_round_rect(
                    x,
                    y,
                    x + self._cell_size,
                    y + self._cell_size,
                    radius=self._corner_radius,
                    fill="white",
                    outline="#ff0000",
                    width=3,
                )
                self._cell_rect_id[(r, c)] = rect_id
                self._cell_text_layers[(r, c)] = []

        total_w = self._pad + 3 * (self._cell_size + self._pad)
        total_h = self._pad + 3 * (self._cell_size + self._pad)
        self.board_canvas.config(width=total_w, height=total_h)

        self.board_canvas.bind("<Button-1>", self._on_canvas_click)

        self.footer_label = tk.Label(
            self.root,
            text="Developed by Himanshu Kumar",
            anchor="center",
            font=("Segoe UI", 10),
            fg="#444",
            pady=6,
        )
        self.footer_label.pack(fill="x")

        self._set_online_controls_visible(False)

    def _create_round_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        **kwargs,
    ) -> int:
        """Create a rounded rectangle on the canvas (single polygon item)."""
        r = max(0.0, min(radius, abs(x2 - x1) / 2, abs(y2 - y1) / 2))
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        return self.board_canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def _start_rgb_border_animation(self) -> None:
        if self._rgb_anim_after_id is not None:
            try:
                self.root.after_cancel(self._rgb_anim_after_id)
            except Exception:
                pass
            self._rgb_anim_after_id = None

        self._rgb_anim_t = 0.0
        self._rgb_border_tick()

    def _rgb_border_tick(self) -> None:
        # Animate outline color for each cell using a hue-shifted rainbow.
        self._rgb_anim_t = (self._rgb_anim_t + 0.01) % 1.0
        idx = 0
        for r in range(3):
            for c in range(3):
                hue = (self._rgb_anim_t + idx * 0.08) % 1.0
                rr, gg, bb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                color = f"#{int(rr * 255):02x}{int(gg * 255):02x}{int(bb * 255):02x}"
                self.board_canvas.itemconfigure(self._cell_rect_id[(r, c)], outline=color)
                idx += 1

        # Keep win line above everything.
        if self._win_line_id is not None:
            self.board_canvas.tag_raise(self._win_line_id)

        self._rgb_anim_after_id = self.root.after(40, self._rgb_border_tick)

    def _online_host_start(self) -> None:
        if not self._online_mode:
            return
        self._online_disconnect()
        try:
            port = int(self.port_var.get().strip())
        except Exception:
            port = 5050

        self._online_role = "host"
        self._local_symbol = "X"

        def on_connect() -> None:
            self.root.after(0, self._online_send_sync)

        def on_disconnect() -> None:
            self.root.after(0, self._online_disconnect)

        def on_message(msg: dict) -> None:
            if msg.get("type") == "move":
                row = msg.get("row")
                col = msg.get("col")
                if isinstance(row, int) and isinstance(col, int):
                    self.root.after(0, lambda: self._online_apply_remote_move((row, col)))
            elif msg.get("type") == "restart":
                self.root.after(0, self._online_restart_both)

        host = OnlineHost(OnlineConfig(host="0.0.0.0", port=port), on_message, on_connect, on_disconnect)
        self._online_host = host
        host.start()
        self._sync_ui_from_state()

    def _online_join(self) -> None:
        if not self._online_mode:
            return
        self._online_disconnect()
        ip = self.join_ip_var.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_var.get().strip())
        except Exception:
            port = 5050

        self._online_role = "client"
        self._local_symbol = "O"

        def on_disconnect() -> None:
            self.root.after(0, self._online_disconnect)

        def on_message(msg: dict) -> None:
            t = msg.get("type")
            if t == "sync":
                self.root.after(0, lambda: self._online_apply_sync(msg))
            elif t == "restart":
                self.root.after(0, self._restart_round)

        client = OnlineClient(ip, port, on_message=on_message, on_disconnect=on_disconnect)
        self._online_client = client
        try:
            client.connect()
        except Exception:
            self._online_disconnect()
            return

        self._sync_ui_from_state()

    def _online_disconnect(self) -> None:
        if self._online_client is not None:
            try:
                self._online_client.close()
            except Exception:
                pass
        if self._online_host is not None:
            try:
                self._online_host.stop()
            except Exception:
                pass
        self._online_client = None
        self._online_host = None
        self._online_role = None
        self._local_symbol = "X"

    def _online_apply_remote_move(self, move: Move) -> None:
        # Host only: apply joiner's move when it's O's turn.
        if self._online_role != "host":
            return
        if self.controller.state() != "IN_PROGRESS":
            return
        if self.controller.current_turn != "O":
            return
        ok = self.controller.apply_move(move)
        if not ok:
            return
        self._assign_cell_palette(move, "O")
        self._sync_ui_from_state()
        self._handle_end_if_needed()
        self._online_send_sync()

    def _online_send_sync(self) -> None:
        if self._online_role != "host" or self._online_host is None:
            return
        if not self._online_host.connected:
            return
        payload = {
            "grid": self.controller.board.grid,
            "turn": self.controller.current_turn,
        }
        try:
            self._online_host.send_sync(payload)
        except Exception:
            pass

    def _online_apply_sync(self, msg: dict) -> None:
        if self._online_role != "client":
            return
        grid = msg.get("grid")
        turn = msg.get("turn")
        if not (isinstance(grid, list) and isinstance(turn, str)):
            return

        # Replace local board state from host.
        try:
            self.controller.board.grid = [list(row) for row in grid]
            self.controller.current_turn = turn
        except Exception:
            return

        # Ensure any new symbols have palettes.
        for r in range(3):
            for c in range(3):
                sym = self.controller.board.grid[r][c]
                if sym in ("X", "O"):
                    self._assign_cell_palette((r, c), sym)

        self._sync_ui_from_state()

    def _on_restart_pressed(self) -> None:
        if self._online_mode:
            if self._online_role == "host":
                self._online_restart_both()
            elif self._online_role == "client" and self._online_client is not None:
                try:
                    self._online_client.send_restart()
                except Exception:
                    self._online_disconnect()
            return

        self._restart_round()

    def _on_change_mode(self) -> None:
        selected = self.mode_var.get()
        if selected == "ONLINE":
            self._online_mode = True
            self.controller.set_mode("HUMAN_HUMAN")
            self._local_symbol = "X"
            self._set_online_controls_visible(True)
        else:
            self._online_mode = False
            self._online_disconnect()
            self._set_online_controls_visible(False)
            self.controller.set_mode(selected)
        self._restart_round()

    def _set_online_controls_visible(self, visible: bool) -> None:
        if visible:
            self.online_frame.pack(fill="x")
        else:
            self.online_frame.pack_forget()

    def _restart_round(self) -> None:
        self._clear_win_line()
        self._cell_palette.clear()
        self._x_palette_idx = 0
        self._o_palette_idx = 0
        self.controller.reset_round(starting_turn="X")
        self._sync_ui_from_state()

        # If in AI mode and AI is set to start (future flexibility), perform AI step.
        self._maybe_ai_step()

    def _on_click(self, row: int, col: int) -> None:
        if self.controller.state() != "IN_PROGRESS":
            return

        if self._online_mode:
            if self.controller.current_turn != self._local_symbol:
                return

            # Client sends move to host; host is authoritative.
            if self._online_role == "client" and self._online_client is not None:
                try:
                    self._online_client.send_move((row, col))
                except Exception:
                    self._online_disconnect()
                return
        else:
            if not self.controller.is_human_turn():
                return

        symbol = self.controller.current_turn
        ok = self.controller.apply_move((row, col))
        if not ok:
            return

        self._assign_cell_palette((row, col), symbol)

        self._sync_ui_from_state()
        if self._handle_end_if_needed():
            return

        if self._online_mode:
            self._online_send_sync()
        else:
            self._maybe_ai_step()

    def _maybe_ai_step(self) -> None:
        if self.controller.state() != "IN_PROGRESS":
            return
        if not self.controller.is_ai_turn():
            return
        self.root.after(120, self._ai_step)

    def _ai_step(self) -> None:
        if self.controller.state() != "IN_PROGRESS":
            return
        if not self.controller.is_ai_turn():
            return

        move = self.controller.apply_ai_move()
        if move is not None:
            self._assign_cell_palette(move, self.controller.ai_symbol)

        self._sync_ui_from_state()
        self._handle_end_if_needed()

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.controller.state() != "IN_PROGRESS":
            return

        if self._online_mode:
            if self.controller.current_turn != self._local_symbol:
                return
        else:
            if not self.controller.is_human_turn():
                return

        col = int((event.x - self._pad) // (self._cell_size + self._pad))
        row = int((event.y - self._pad) // (self._cell_size + self._pad))
        if not (0 <= row < 3 and 0 <= col < 3):
            return

        x0, y0 = self._cell_origin[(row, col)]
        if not (x0 <= event.x <= x0 + self._cell_size and y0 <= event.y <= y0 + self._cell_size):
            return

        self._on_click(row, col)

    def _handle_end_if_needed(self) -> bool:
        if self.controller.finalize_if_over():
            st = self.controller.state()
            if st in ("X_WINS", "O_WINS"):
                self._draw_win_line()
            self._play_end_tone(st)
            self._vibrate_window()
            self._sync_ui_from_state()

            # Auto-restart after a short delay (score is preserved).
            if self._online_mode:
                # Host controls restart so both sides stay in sync.
                if self._online_role == "host":
                    self.root.after(2200, self._online_restart_both)
            else:
                self.root.after(2200, self._restart_round)
            return True
        return False

    def _online_restart_both(self) -> None:
        self._restart_round()
        if self._online_host is not None and self._online_host.connected:
            try:
                self._online_host.send_restart()
            except Exception:
                pass

    def _play_end_tone(self, state: str) -> None:
        # Windows tone via winsound; fallback to Tk bell.
        if winsound is not None:
            if state in ("X_WINS", "O_WINS"):
                winsound.Beep(880, 180)
                winsound.Beep(988, 180)
            else:
                winsound.Beep(440, 240)
            return

        # Fallback: short UI bell
        try:
            self.root.bell()
        except Exception:
            pass

    def _vibrate_window(self, cycles: int = 10, distance: int = 6, delay_ms: int = 25) -> None:
        """Desktop-friendly 'vibrate' effect by shaking the window briefly."""
        try:
            self.root.update_idletasks()
            x0 = self.root.winfo_x()
            y0 = self.root.winfo_y()
        except Exception:
            return

        def step(i: int) -> None:
            if i >= cycles:
                self.root.geometry(f"+{x0}+{y0}")
                return
            dx = distance if (i % 2 == 0) else -distance
            self.root.geometry(f"+{x0 + dx}+{y0}")
            self.root.after(delay_ms, lambda: step(i + 1))

        step(0)

    def _clear_win_line(self) -> None:
        if self._win_line_id is not None:
            self.board_canvas.delete(self._win_line_id)
            self._win_line_id = None

    def _clear_cell_symbol(self, cell: Move) -> None:
        for item_id in self._cell_text_layers.get(cell, []):
            self.board_canvas.delete(item_id)
        self._cell_text_layers[cell] = []

    def _assign_cell_palette(self, cell: Move, symbol: str) -> None:
        if cell in self._cell_palette:
            return

        # (dark, mid, light)
        x_palettes = [
            ("#0b3d91", "#1a73e8", "#67b7ff"),
            ("#0f4c5c", "#2a9d8f", "#9bf6ff"),
            ("#1b4332", "#2d6a4f", "#95d5b2"),
            ("#7f1d1d", "#ef4444", "#fecaca"),
        ]
        o_palettes = [
            ("#7b1fa2", "#ab47bc", "#ff6fd8"),
            ("#6d28d9", "#8b5cf6", "#ddd6fe"),
            ("#9a3412", "#f97316", "#fed7aa"),
            ("#0f766e", "#14b8a6", "#99f6e4"),
        ]

        if symbol == "X":
            palette = x_palettes[self._x_palette_idx % len(x_palettes)]
            self._x_palette_idx += 1
        else:
            palette = o_palettes[self._o_palette_idx % len(o_palettes)]
            self._o_palette_idx += 1

        self._cell_palette[cell] = palette

    def _draw_cell_symbol(self, cell: Move, symbol: str) -> None:
        self._clear_cell_symbol(cell)
        if symbol == " ":
            return

        x0, y0 = self._cell_origin[cell]
        cx = x0 + self._cell_size / 2
        cy = y0 + self._cell_size / 2

        if cell not in self._cell_palette:
            # If the board is already populated (e.g., future features), assign deterministically.
            self._assign_cell_palette(cell, symbol)

        c1, c2, c3 = self._cell_palette[cell]
        colors = [c1, c2, c3]

        # Simulated vertical gradient: multiple text layers with slight y offsets.
        offsets = [-3, 0, 3]
        for dy, color in zip(offsets, colors, strict=False):
            item_id = self.board_canvas.create_text(
                cx,
                cy + dy,
                text=symbol,
                fill=color,
                font=("Segoe UI", 40, "bold"),
            )
            self._cell_text_layers[cell].append(item_id)

    def _draw_win_line(self) -> None:
        self._clear_win_line()
        cells = self.controller.board.winning_line()
        if not cells:
            return

        # Draw from center of first cell to center of last cell.
        (r1, c1), (_, _), (r3, c3) = cells
        ox1, oy1 = self._cell_origin[(r1, c1)]
        ox2, oy2 = self._cell_origin[(r3, c3)]
        x1 = ox1 + self._cell_size / 2
        y1 = oy1 + self._cell_size / 2
        x2 = ox2 + self._cell_size / 2
        y2 = oy2 + self._cell_size / 2

        self._win_line_id = self.board_canvas.create_line(
            x1,
            y1,
            x2,
            y2,
            fill="#c00000",
            width=8,
            capstyle=tk.ROUND,
        )
        self.board_canvas.tag_raise(self._win_line_id)

    def _sync_ui_from_state(self) -> None:
        b = self.controller.board
        for r in range(3):
            for c in range(3):
                self._draw_cell_symbol((r, c), b.grid[r][c])

                if b.grid[r][c] == " ":
                    self.board_canvas.itemconfigure(self._cell_rect_id[(r, c)], fill="white")
                else:
                    self.board_canvas.itemconfigure(self._cell_rect_id[(r, c)], fill="#f3f3f3")

        if self._online_mode:
            self.score_label.config(text="Online game")
        elif self.controller.mode == "HUMAN_HUMAN":
            s = self.controller.score_hh
            self.score_label.config(text=f"Score  X: {s.x}   O: {s.o}   Draws: {s.draws}")
        else:
            s = self.controller.score_ha
            self.score_label.config(text=f"Score  You: {s.human}   AI: {s.ai}   Draws: {s.draws}")

        st = self.controller.state()
        if st == "IN_PROGRESS":
            turn = self.controller.current_turn
            if self._online_mode:
                who = "You" if turn == self._local_symbol else "Friend"
                conn = "Connected" if (self._online_role is not None) else "Not connected"
                self.status_label.config(text=f"Online ({conn})  Turn: {turn} ({who})")
            elif self.controller.mode == "HUMAN_AI":
                who = "You" if self.controller.is_human_turn() else "AI"
                self.status_label.config(text=f"Turn: {turn} ({who})")
            else:
                self.status_label.config(text=f"Turn: {turn}")
        else:
            self.status_label.config(text=f"Round finished: {st}")

        # Keep symbols above borders and win line above everything.
        for cell in self._cell_text_layers:
            for item_id in self._cell_text_layers[cell]:
                self.board_canvas.tag_raise(item_id)
        if self._win_line_id is not None:
            self.board_canvas.tag_raise(self._win_line_id)
