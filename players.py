from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from game_board import GameBoard, Move


@dataclass
class Player:
    """Human player. In GUI mode the UI supplies the move, so this class is minimal."""

    symbol: str

    def validate_move(self, board: GameBoard, move: Optional[Move]) -> bool:
        if move is None:
            return False
        r, c = move
        return (0 <= r < board.size) and (0 <= c < board.size) and board.grid[r][c] == " "
