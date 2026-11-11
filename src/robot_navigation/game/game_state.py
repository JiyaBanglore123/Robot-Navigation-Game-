"""
Runtime game-state manager for the DFA-based Robot Navigation Game.
Author: Pavithra S (Person 3)

GameState keeps the robot's logical DFA state and its grid position in sync.
It never computes transitions itself: every move is delegated to the
DFAEngine (Person 1), and GameState only interprets the result.

Status values exposed to the frontend:
    READY    - fresh game, no moves yet
    MOVING   - last move took the robot to a new cell
    BLOCKED  - last move hit the outer wall (DFA self-loop), robot stayed put
    CRASHED  - robot hit an obstacle (DFA entered the Crash trap state)
    WON      - robot reached the goal (accepting state)
"""

from typing import Any, Optional

from .grid_config import CRASH_STATE, LevelConfig, state_to_position

# Terminal statuses: no further moves are accepted.
GAME_OVER_STATUSES = {"CRASHED", "WON"}

# Movement symbol -> (row delta, col delta); used only to report which
# obstacle cell the robot crashed into (the Crash state has no coordinates).
_SYMBOL_DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


class GameState:

    def __init__(self, level_config: LevelConfig, dfa_engine):
        """Initialize a game session for the given level."""
        # 1-2. Store level configuration and DFA engine reference.
        self.level_config = level_config
        self.dfa_engine = dfa_engine

        self.rows: int = level_config["rows"]
        self.cols: int = level_config["cols"]
        self.start_state: str = level_config["start"]
        self.goal_state: str = level_config["goal"]

        self.start_position = self._require_position(self.start_state, "start")
        self.goal_position = self._require_position(self.goal_state, "goal")
        self.obstacle_positions = [
            self._require_position(obs, "obstacle") for obs in level_config["obstacles"]
        ]

        # 3-6. Current state, counter, status, and synchronized position.
        self.reset()

    # ------------------------------------------------------------------ #
    # Public API (used by GameManager in app.py)
    # ------------------------------------------------------------------ #

    def move(self, direction: str) -> dict:
        """Coordinate one movement and return the updated game state."""
        # 1. Reject moves once the game is over.
        if self.status in GAME_OVER_STATUSES:
            self.message = f"Game over ({self.status}). Reset to play again."
            return self.get_state()

        # 2. Ask the DFA engine where this symbol leads.
        result = self.dfa_engine.process_movement(self.current_state, direction)

        # 3. Process the result.
        engine_status = str(result.get("status", "")).upper()
        next_state = self._normalize_state_name(result.get("next_state"))
        self.message = result.get("message", "")

        if engine_status == "INVALID" or next_state is None:
            # Invalid symbol: nothing changes, and it does not count as a move.
            self.message = self.message or f"Invalid movement '{direction}'."
            return self.get_state()

        previous_state = self.current_state

        # 4-5. Update state and move counter.
        self.current_state = next_state
        self.move_counter += 1
        self.input_string.append(direction)

        # 6-7. Synchronize grid position and determine status.
        if engine_status == "CRASHED" or next_state == CRASH_STATE:
            self.status = "CRASHED"
            # Robot stays drawn on its last valid cell; record the obstacle hit.
            self.crash_position = self._step(self.robot_position, direction)
        else:
            position = state_to_position(next_state)
            if position is None:
                raise ValueError(f"DFA returned unknown state '{next_state}'.")
            self.robot_position = position

            if engine_status == "WON" or next_state == self.goal_state:
                self.status = "WON"
            elif next_state == previous_state:
                self.status = "BLOCKED"
            else:
                self.status = "MOVING"

        self.path.append(list(self.robot_position))

        # 8. Return the updated state.
        return self.get_state()

    def reset(self) -> None:
        """Restore the game to its initial configuration."""
        self.current_state: str = self.start_state
        self.robot_position: tuple[int, int] = self.start_position
        self.move_counter: int = 0
        self.status: str = "READY"
        self.message: str = "Game ready."
        self.input_string: list[str] = []
        self.path: list[list[int]] = [list(self.start_position)]
        self.crash_position: Optional[tuple[int, int]] = None

    def get_state(self) -> dict:
        """Return a JSON-serializable snapshot of the current session."""
        return {
            "current_state": self.current_state,
            "robot_position": list(self.robot_position),
            "status": self.status,
            "move_count": self.move_counter,
            "goal_position": list(self.goal_position),
            "obstacles": [list(pos) for pos in self.obstacle_positions],
            "rows": self.rows,
            "cols": self.cols,
            # Extra fields (ignored safely by the frontend if unused):
            "start_position": list(self.start_position),
            "input_string": "".join(self.input_string),
            "path": [list(p) for p in self.path],
            "crash_position": list(self.crash_position) if self.crash_position else None,
            "is_game_over": self.status in GAME_OVER_STATUSES,
            "message": self.message,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _require_position(self, state: str, label: str) -> tuple[int, int]:
        position = state_to_position(state)
        if position is None:
            raise ValueError(f"Invalid {label} state '{state}' (expected 'q<row><col>').")
        return position

    def _normalize_state_name(self, state: Any) -> Optional[str]:
        """Accept either a state name ('q01') or a JFLAP node id ('1')."""
        if state is None:
            return None
        state = str(state)
        if state == CRASH_STATE or state_to_position(state) is not None:
            return state
        graph = getattr(self.dfa_engine, "graph", None)
        if graph is not None and state in graph.nodes:
            return graph.nodes[state].get("name", state)
        return state

    @staticmethod
    def _step(position: tuple[int, int], symbol: str) -> Optional[tuple[int, int]]:
        delta = _SYMBOL_DELTAS.get(symbol)
        if delta is None:
            return None
        return position[0] + delta[0], position[1] + delta[1]
