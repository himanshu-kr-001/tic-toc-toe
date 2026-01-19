from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ai_player import AIPlayer
from game_board import GameBoard, Move
from players import Player


@dataclass
class ScoreHumanHuman:
    x: int = 0
    o: int = 0
    draws: int = 0


@dataclass
class ScoreHumanAI:
    human: int = 0
    ai: int = 0
    draws: int = 0


class GameController:
    """Orchestrates game state: turns, applying moves, and score tracking."""

    def __init__(
        self,
        x_symbol: str = "X",
        o_symbol: str = "O",
        human_symbol: str = "X",
        ai_symbol: str = "O",
        ai_max_depth: Optional[int] = None,
    ) -> None:
        self.board = GameBoard()
        self.player_x = Player(symbol=x_symbol)
        self.player_o = Player(symbol=o_symbol)
        self.ai = AIPlayer(symbol=ai_symbol, max_depth=ai_max_depth)
        self.human_symbol = human_symbol
        self.ai_symbol = ai_symbol
        self.mode: str = "HUMAN_HUMAN"  # or 'HUMAN_AI'
        self.score_hh = ScoreHumanHuman()
        self.score_ha = ScoreHumanAI()
        self.current_turn: str = "X"  # 'X' starts by default

    def set_mode(self, mode: str) -> None:
        if mode not in ("HUMAN_HUMAN", "HUMAN_AI"):
            raise ValueError("Invalid mode")
        self.mode = mode

    def set_ai_depth(self, max_depth: Optional[int]) -> None:
        self.ai.max_depth = max_depth

    def reset_round(self, starting_turn: str = "X") -> None:
        self.board.reset()
        self.current_turn = starting_turn

    def state(self) -> str:
        return self.board.game_state()

    def is_human_turn(self) -> bool:
        if self.mode == "HUMAN_HUMAN":
            return True
        return self.current_turn == self.human_symbol

    def is_ai_turn(self) -> bool:
        return self.mode == "HUMAN_AI" and self.current_turn == self.ai_symbol

    def apply_move(self, move: Move) -> bool:
        """Applies a move for the current player (X or O)."""
        if self.mode == "HUMAN_AI" and self.current_turn != self.human_symbol:
            return False

        player = self.player_x if self.current_turn == self.player_x.symbol else self.player_o
        if not player.validate_move(self.board, move):
            return False
        ok = self.board.place(move[0], move[1], player.symbol)
        if ok:
            self._advance_turn()
        return ok

    def apply_ai_move(self) -> Optional[Move]:
        if not self.is_ai_turn():
            return None
        move = self.ai.choose_move(self.board)
        if move is None:
            return None
        self.board.place(move[0], move[1], self.ai_symbol)
        self._advance_turn()
        return move

    def finalize_if_over(self) -> bool:
        """Updates score if round is over. Returns True if game is over."""
        st = self.state()
        if st == "IN_PROGRESS":
            return False

        if st == "DRAW":
            if self.mode == "HUMAN_HUMAN":
                self.score_hh.draws += 1
            else:
                self.score_ha.draws += 1
            return True

        winner = "X" if st == "X_WINS" else "O"
        if self.mode == "HUMAN_HUMAN":
            if winner == "X":
                self.score_hh.x += 1
            else:
                self.score_hh.o += 1
        else:
            if winner == self.human_symbol:
                self.score_ha.human += 1
            else:
                self.score_ha.ai += 1
        return True

    def _advance_turn(self) -> None:
        self.current_turn = "O" if self.current_turn == "X" else "X"
