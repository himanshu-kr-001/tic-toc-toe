from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Optional, Tuple

from game_board import GameBoard, Move


@dataclass
class AIPlayer:
    """AI player using Minimax with optional depth limits for difficulty."""

    symbol: str
    max_depth: Optional[int] = None  # None means full search (optimal)

    @property
    def opponent(self) -> str:
        return "O" if self.symbol == "X" else "X"

    def choose_move(self, board: GameBoard) -> Optional[Move]:
        best_score = -inf
        best_move: Optional[Move] = None

        # Minimax searches all legal moves and chooses the one with best evaluation.
        for move in board.available_moves():
            b2 = board.copy()
            b2.place(move[0], move[1], self.symbol)
            score = self._minimax(b2, depth=1, maximizing=False, alpha=-inf, beta=inf)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _terminal_score(self, board: GameBoard, depth: int) -> Optional[int]:
        state = board.game_state()
        if state == "DRAW":
            return 0

        if state == "X_WINS" or state == "O_WINS":
            winner = "X" if state == "X_WINS" else "O"
            # Prefer faster wins and slower losses.
            if winner == self.symbol:
                return 10 - depth
            return depth - 10

        return None

    def _minimax(
        self,
        board: GameBoard,
        depth: int,
        maximizing: bool,
        alpha: float,
        beta: float,
    ) -> int:
        terminal = self._terminal_score(board, depth)
        if terminal is not None:
            return terminal

        if self.max_depth is not None and depth >= self.max_depth:
            # Depth-limited evaluation: 0 is a neutral heuristic for Tic-Tac-Toe.
            # This intentionally makes Easy/Medium imperfect.
            return 0

        if maximizing:
            best = -inf
            for move in board.available_moves():
                b2 = board.copy()
                b2.place(move[0], move[1], self.symbol)
                val = self._minimax(b2, depth + 1, False, alpha, beta)
                best = max(best, val)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return int(best)

        best = inf
        for move in board.available_moves():
            b2 = board.copy()
            b2.place(move[0], move[1], self.opponent)
            val = self._minimax(b2, depth + 1, True, alpha, beta)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return int(best)
