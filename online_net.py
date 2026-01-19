from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


Move = Tuple[int, int]


def _send_json_line(sock: socket.socket, obj: dict) -> None:
    data = (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
    sock.sendall(data)


def _recv_lines(sock: socket.socket, on_line: Callable[[str], None], stop_event: threading.Event) -> None:
    buf = ""
    sock.settimeout(0.5)
    while not stop_event.is_set():
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        if not chunk:
            break
        buf += chunk.decode("utf-8", errors="replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if line:
                on_line(line)


@dataclass
class OnlineConfig:
    host: str = "0.0.0.0"
    port: int = 5050


class OnlineHost:
    """Host side of a 2-player connection (accepts one joiner)."""

    def __init__(
        self,
        config: OnlineConfig,
        on_message: Callable[[dict], None],
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self.config = config
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self._listener: Optional[socket.socket] = None
        self._sock: Optional[socket.socket] = None
        self._accept_thread: Optional[threading.Thread] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def start(self) -> None:
        if self._accept_thread is not None:
            return
        self._stop.clear()
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def stop(self) -> None:
        self._stop.set()
        for s in (self._sock, self._listener):
            try:
                if s is not None:
                    s.close()
            except Exception:
                pass
        self._sock = None
        self._listener = None
        self._accept_thread = None
        self._rx_thread = None

    def send_sync(self, payload: dict) -> None:
        if self._sock is None:
            return
        payload = dict(payload)
        payload["type"] = "sync"
        _send_json_line(self._sock, payload)

    def send_restart(self) -> None:
        if self._sock is None:
            return
        _send_json_line(self._sock, {"type": "restart"})

    def _accept_loop(self) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener = listener
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.config.host, self.config.port))
        listener.listen(1)
        listener.settimeout(0.5)

        try:
            while not self._stop.is_set():
                try:
                    client, _addr = listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                # Only allow one client.
                if self._sock is not None:
                    try:
                        client.close()
                    except Exception:
                        pass
                    continue

                self._sock = client
                try:
                    _send_json_line(client, {"type": "hello", "symbol": "O"})
                except Exception:
                    try:
                        client.close()
                    except Exception:
                        pass
                    self._sock = None
                    continue

                try:
                    self.on_connect()
                except Exception:
                    pass

                self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
                self._rx_thread.start()

        finally:
            try:
                listener.close()
            except Exception:
                pass

    def _rx_loop(self) -> None:
        assert self._sock is not None

        def on_line(line: str) -> None:
            try:
                msg = json.loads(line)
            except Exception:
                return
            self.on_message(msg)

        try:
            _recv_lines(self._sock, on_line, self._stop)
        finally:
            try:
                if self._sock is not None:
                    self._sock.close()
            except Exception:
                pass
            self._sock = None
            try:
                self.on_disconnect()
            except Exception:
                pass


class OnlineClient:
    """Client for the remote player. Sends moves, receives sync updates."""

    def __init__(
        self,
        host: str,
        port: int,
        on_message: Callable[[dict], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self.host = host
        self.port = port
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.symbol: Optional[str] = None

        self._sock: Optional[socket.socket] = None
        self._stop = threading.Event()
        self._rx_thread: Optional[threading.Thread] = None

    def connect(self, timeout: float = 5.0) -> None:
        if self._sock is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((self.host, self.port))
        s.settimeout(None)
        self._sock = s
        self._stop.clear()
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def close(self) -> None:
        self._stop.set()
        try:
            if self._sock is not None:
                self._sock.close()
        except Exception:
            pass
        self._sock = None

    def send_move(self, move: Move) -> None:
        if self._sock is None:
            return
        _send_json_line(self._sock, {"type": "move", "row": move[0], "col": move[1]})

    def send_restart(self) -> None:
        if self._sock is None:
            return
        _send_json_line(self._sock, {"type": "restart"})

    def send_sync(self, payload: dict) -> None:
        if self._sock is None:
            return
        payload = dict(payload)
        payload["type"] = "sync"
        _send_json_line(self._sock, payload)

    def _rx_loop(self) -> None:
        assert self._sock is not None

        def on_line(line: str) -> None:
            try:
                msg = json.loads(line)
            except Exception:
                return
            if msg.get("type") == "hello":
                self.symbol = msg.get("symbol")
            self.on_message(msg)

        try:
            _recv_lines(self._sock, on_line, self._stop)
        finally:
            self.close()
            try:
                self.on_disconnect()
            except Exception:
                pass
