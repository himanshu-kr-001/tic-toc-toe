from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


Move = Tuple[int, int]  # (row, col)


@dataclass
class GameBoard:
    """Represents a 3x3 Tic-Tac-Toe board and encapsulates all board rules."""

    size: int = 3

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.grid: List[List[str]] = [[" " for _ in range(self.size)] for _ in range(self.size)]

    def copy(self) -> "GameBoard":
        b = GameBoard(self.size)
        b.grid = [row[:] for row in self.grid]
        return b

    def place(self, row: int, col: int, symbol: str) -> bool:
        """Place symbol at (row, col). Returns False if invalid/occupied."""
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.grid[row][col] != " ":
            return False
        self.grid[row][col] = symbol
        return True

    def available_moves(self) -> Iterable[Move]:
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == " ":
                    yield (r, c)

    def is_full(self) -> bool:
        return all(self.grid[r][c] != " " for r in range(self.size) for c in range(self.size))

    def winner(self) -> Optional[str]:
        """Returns 'X' or 'O' if there is a winner, else None."""
        lines: List[List[str]] = []

        # Rows
        lines.extend(self.grid)

        # Columns
        for c in range(self.size):
            lines.append([self.grid[r][c] for r in range(self.size)])

        # Diagonals
        lines.append([self.grid[i][i] for i in range(self.size)])
        lines.append([self.grid[i][self.size - 1 - i] for i in range(self.size)])

        for line in lines:
            if line[0] != " " and all(cell == line[0] for cell in line):
                return line[0]
        return None

    def winning_line(self) -> Optional[List[Move]]:
        """Returns the 3 (row, col) cells forming the winning line, or None."""
        # Rows
        for r in range(self.size):
            row = self.grid[r]
            if row[0] != " " and all(cell == row[0] for cell in row):
                return [(r, 0), (r, 1), (r, 2)]

        # Columns
        for c in range(self.size):
            col = [self.grid[r][c] for r in range(self.size)]
            if col[0] != " " and all(cell == col[0] for cell in col):
                return [(0, c), (1, c), (2, c)]

        # Main diagonal
        diag1 = [self.grid[i][i] for i in range(self.size)]
        if diag1[0] != " " and all(cell == diag1[0] for cell in diag1):
            return [(0, 0), (1, 1), (2, 2)]

        # Anti diagonal
        diag2 = [self.grid[i][self.size - 1 - i] for i in range(self.size)]
        if diag2[0] != " " and all(cell == diag2[0] for cell in diag2):
            return [(0, 2), (1, 1), (2, 0)]

        return None

    def game_state(self) -> str:
        """One of: 'IN_PROGRESS', 'DRAW', 'X_WINS', 'O_WINS'."""
        w = self.winner()
        if w == "X":
            return "X_WINS"
        if w == "O":
            return "O_WINS"
        if self.is_full():
            return "DRAW"
        return "IN_PROGRESS"

    def __str__(self) -> str:
        """Text display (useful for debugging or optional CLI usage)."""
        rows = []
        for r in range(self.size):
            rows.append(" | ".join(self.grid[r]))
        sep = "\n" + "-" * (self.size * 4 - 3) + "\n"
        return sep.join(rows)
